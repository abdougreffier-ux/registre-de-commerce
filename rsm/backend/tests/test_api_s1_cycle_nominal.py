"""
Scénario S1 — Cycle nominal complet via API.

Fondements : articles 77, 78, 85, 86, 88, 90, 91, 92 du décret 2021-033 ;
§ 4.2.1 à 4.2.5 et § 4.3 du TDR.

Trajectoire :
    Dépôt → En contrôle de forme → Inscrite → Modifiée → Renouvelée
    → Radiée → Expirée → Archivée

À chaque étape, les assertions portent SEULEMENT sur des règles
explicitement tranchées par le décret ou par le TDR. Aucun comportement
interprétatif n'est affirmé ici.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import EntreeAudit
from apps.biens.models import BienGreve
from apps.core.enums import CanalSaisie, NaturesDroitInscrit
from apps.inscriptions.models import Inscription
from apps.modifications.models import SnapshotInscription
from apps.parties.models import RolePartie, TypePartie
from apps.workflow.models import TransitionStatut
from apps.workflow.statuts import StatutInscription

from tests import helpers


class S1_CycleNominal_API_Tests(TestCase):
    """Cycle complet orchestré via les endpoints DRF."""

    def setUp(self):
        self.agent = helpers.creer_agent_saisie("api_agent")
        self.greffier = helpers.creer_greffier("api_greffier")

        self.client_agent = APIClient()
        self.client_agent.force_authenticate(self.agent)
        self.client_greffier = APIClient()
        self.client_greffier.force_authenticate(self.greffier)

    # --------------------------------------------------------------------- #
    # Helpers internes                                                       #
    # --------------------------------------------------------------------- #
    def _deposer(self, duree_jours: int = 365):
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data={
                "canal_saisie": CanalSaisie.GUICHET_PAPIER,
                "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                "somme_garantie": "1000000.00",
                "monnaie": "MRU",
                "duree_en_jours": duree_jours,
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        return rep.data

    def _peupler_inscription(self, reference_demande):
        """
        Peuple via ORM direct : l'API de gestion des parties et biens
        n'est pas dans le périmètre de ce tour (report au module
        « formulaires bilingues »).
        """
        inscription = Inscription.objects.get(reference_demande=reference_demande)
        helpers.peupler_inscription_complete(inscription, acteur=self.agent)
        return inscription

    def _valider(self, reference_demande):
        rep = self.client_greffier.post(
            f"/api/v1/inscriptions/{reference_demande}/valider/",
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK, rep.data)
        return rep.data

    # --------------------------------------------------------------------- #
    # Étapes du cycle                                                        #
    # --------------------------------------------------------------------- #
    def test_cycle_nominal_complet(self):
        # ---- 1. Dépôt — art. 78, 85 ------------------------------------- #
        depot = self._deposer(duree_jours=365)
        reference = depot["reference_demande"]

        # Statut attendu après dépôt (transition automatique).
        self.assertEqual(
            depot["statut"], StatutInscription.EN_CONTROLE_FORME,
            "Le dépôt doit déclencher la transition automatique § 4.3.",
        )
        self.assertIsNone(
            depot["numero_ordre"],
            "Le numéro d'ordre (art. 78) n'est attribué qu'à la validation.",
        )

        # ---- 2. Peuplement parties + biens (art. 85) -------------------- #
        inscription = self._peupler_inscription(reference)

        # ---- 3. Validation — art. 78 al. 4, 85, 87 ---------------------- #
        valide = self._valider(reference)
        self.assertEqual(valide["statut"], StatutInscription.INSCRITE)
        # Numéro d'ordre attribué, format NNNNNN-AAAAMMJJHHMMSS.
        self.assertIsNotNone(valide["numero_ordre"])
        self.assertRegex(valide["numero_ordre"], r"^\d{6}-\d{14}$")
        numero_ordre_attribue = valide["numero_ordre"]

        inscription.refresh_from_db()
        # Date d'expiration = instant d'opposabilité + durée.
        date_exp_attendue = (
            inscription.instant_saisie_opposable.date() + timedelta(days=365)
        )
        self.assertEqual(inscription.date_expiration, date_exp_attendue)

        # ---- 4. Modification — art. 88, 90 al. 2 ------------------------ #
        # On ajoute un bien, via l'API des modifications, avec accords
        # des parties positionnés à true (signature cryptographique GELÉE).
        rep_mod = self.client_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": inscription.pk,
                "objet_modification_fr": "Ajout d'un bien complémentaire",
                "objet_modification_ar": "إضافة مال تكميلي",
                "diff_propose": {
                    "biens": {
                        "ajouter": [{
                            "description_fr": "Machine secondaire",
                            "description_ar": "آلة ثانوية",
                        }],
                    },
                },
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        self.assertEqual(rep_mod.status_code, status.HTTP_201_CREATED, rep_mod.data)
        id_modification = rep_mod.data["id"]

        rep_applique = self.client_greffier.post(
            f"/api/v1/modifications/{id_modification}/appliquer/",
            format="json",
        )
        self.assertEqual(rep_applique.status_code, status.HTTP_200_OK, rep_applique.data)

        inscription.refresh_from_db()
        self.assertEqual(inscription.statut, StatutInscription.MODIFIEE)
        # Numéro d'ordre INCHANGÉ — immutabilité art. 78.
        self.assertEqual(inscription.numero_ordre, numero_ordre_attribue)
        # Durée et date d'expiration INCHANGÉES — art. 90 al. 2.
        self.assertEqual(inscription.duree_en_jours, 365)
        self.assertEqual(inscription.date_expiration, date_exp_attendue)

        # Snapshots avant / après modification — art. 79.
        snapshots_mod = SnapshotInscription.objects.filter(
            inscription=inscription,
            demande_modification_id=id_modification,
        ).order_by("instant")
        self.assertEqual(snapshots_mod.count(), 2)
        self.assertEqual(
            snapshots_mod.first().evenement,
            SnapshotInscription.Evenement.MODIFICATION_AVANT,
        )
        self.assertEqual(
            snapshots_mod.last().evenement,
            SnapshotInscription.Evenement.MODIFICATION_APRES,
        )
        self.assertNotEqual(
            snapshots_mod.first().empreinte,
            snapshots_mod.last().empreinte,
        )

        # Deux biens actifs après ajout (1 initial + 1 ajouté).
        self.assertEqual(BienGreve.actifs.filter(inscription=inscription).count(), 2)

        # ---- 5. Renouvellement — art. 91 -------------------------------- #
        rep_renouv = self.client_agent.post(
            "/api/v1/renouvellements/",
            data={"inscription": inscription.pk},
            format="json",
        )
        self.assertEqual(rep_renouv.status_code, status.HTTP_201_CREATED, rep_renouv.data)
        id_renouv = rep_renouv.data["id"]

        rep_applique_renouv = self.client_greffier.post(
            f"/api/v1/renouvellements/{id_renouv}/appliquer/",
            format="json",
        )
        self.assertEqual(rep_applique_renouv.status_code, status.HTTP_200_OK)

        inscription.refresh_from_db()
        self.assertEqual(inscription.statut, StatutInscription.RENOUVELEE)
        # Prorogation d'une durée égale à la durée INITIALE (hypothèse A3
        # acceptée au livrable L11 : la durée initiale = celle fixée à
        # l'inscription, non une durée postérieure).
        self.assertEqual(
            inscription.date_expiration,
            date_exp_attendue + timedelta(days=365),
        )

        # ---- 6. Radiation — art. 92 ------------------------------------- #
        rep_radiation = self.client_agent.post(
            "/api/v1/radiations/",
            data={
                "inscription": inscription.pk,
                "fondement": "consentement",
                "nom_constituant": "Constituant SARL",
                "denomination_constituant": "Constituant SARL",
                "adresse_constituant": "Nouakchott",
                "numero_rc_constituant": "RC/NKT/2024/1001",
            },
            format="json",
        )
        self.assertEqual(rep_radiation.status_code, status.HTTP_201_CREATED, rep_radiation.data)
        id_radiation = rep_radiation.data["id"]

        rep_applique_rad = self.client_greffier.post(
            f"/api/v1/radiations/{id_radiation}/appliquer/",
            format="json",
        )
        self.assertEqual(rep_applique_rad.status_code, status.HTTP_200_OK)

        inscription.refresh_from_db()
        self.assertEqual(inscription.statut, StatutInscription.RADIEE)
        # Mention « radiée » activée, fichier actuel reste public jusqu'à
        # expiration (art. 92 al. 2).
        self.assertTrue(inscription.mention_radiee)
        self.assertEqual(inscription.fichier_actuel, "public")

        # ---- 7. Expiration + transfert au fichier général (art. 92 al. 3) -- #
        # On force l'échéance à aujourd'hui, puis on lance la tâche.
        nouvelle_exp = timezone.localdate() - timedelta(days=1)
        Inscription.objects.filter(pk=inscription.pk).update(
            date_expiration=nouvelle_exp,
        )
        call_command("expirer_inscriptions")

        inscription.refresh_from_db()
        self.assertEqual(inscription.statut, StatutInscription.ARCHIVEE)
        self.assertEqual(inscription.fichier_actuel, "general")

        # ---- 8. Historique de transitions : trace complète § 4.3 -------- #
        transitions = list(
            TransitionStatut.objects.filter(
                numero_inscription=numero_ordre_attribue,
            ).order_by("instant")
        )
        evenements = [t.evenement for t in transitions]
        # Ordre attendu des événements déclencheurs.
        self.assertEqual(
            evenements,
            [
                "validation_greffier",
                "modification_art88",
                "renouvellement_art91",
                "radiation_art92",
                "expiration_automatique",
                "transfert_fichier_general",
            ],
        )

        # ---- 9. Journal d'audit : chaque action tracée (§ 5.2) ---------- #
        actions = set(
            EntreeAudit.objects.values_list("action_cle", flat=True)
        )
        for cle_attendue in {
            "inscription.deposer",
            "transition.prise_en_charge",
            "inscription.valider",
            "transition.validation_greffier",
            "modification.appliquer",
            "transition.modification_art88",
            "renouvellement.appliquer",
            "transition.renouvellement_art91",
            "radiation.appliquer",
            "transition.radiation_art92",
            "inscription.expirer_archiver",
            "transition.expiration_automatique",
            "transition.transfert_fichier_general",
        }:
            self.assertIn(cle_attendue, actions, f"Action non tracée : {cle_attendue}")
