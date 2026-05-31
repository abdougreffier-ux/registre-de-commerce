"""
Scénario S6 — Conservation intégrale de l'historique (article 79).

Couvre :
- production d'un snapshot AVANT et APRÈS chaque modification,
  avec empreintes distinctes et référence à la demande ;
- interdiction de suppression physique d'un bien grevé, d'un rôle ou
  d'un snapshot ;
- consultation des éléments désactivés à travers le manager par défaut
  (pas de perte d'information).
"""
from __future__ import annotations

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.biens.models import BienGreve
from apps.inscriptions.models import RoleInscriptionPartie
from apps.modifications.models import SnapshotInscription
from apps.parties.models import RolePartie, TypePartie

from tests import helpers


class S6_Conservation_API_Tests(TestCase):
    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        self.client_agent = APIClient()
        self.client_agent.force_authenticate(self.agent)
        self.client_greffier = APIClient()
        self.client_greffier.force_authenticate(self.greffier)

    # --------------------------------------------------------------------- #
    # Snapshots avant / après modification                                    #
    # --------------------------------------------------------------------- #
    def test_snapshots_produits_par_modification(self):
        rep_mod = self.client_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "Ajout d'un bien",
                "objet_modification_ar": "إضافة مال",
                "diff_propose": {
                    "biens": {"ajouter": [{
                        "description_fr": "Bien ajouté",
                        "description_ar": "مال مضاف",
                    }]},
                },
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        id_mod = rep_mod.data["id"]
        self.client_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )

        snapshots = list(SnapshotInscription.objects.filter(
            inscription=self.inscription,
            demande_modification_id=id_mod,
        ).order_by("instant"))
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(
            snapshots[0].evenement,
            SnapshotInscription.Evenement.MODIFICATION_AVANT,
        )
        self.assertEqual(
            snapshots[1].evenement,
            SnapshotInscription.Evenement.MODIFICATION_APRES,
        )
        self.assertNotEqual(snapshots[0].empreinte, snapshots[1].empreinte)
        # Le snapshot APRÈS contient le bien nouvellement ajouté.
        descriptions_apres = [
            b["description"]["fr"]
            for b in snapshots[1].contenu["biens_greves"]
            if b["actif"]
        ]
        self.assertIn("Bien ajouté", descriptions_apres)

    # --------------------------------------------------------------------- #
    # Interdiction de suppression physique                                    #
    # --------------------------------------------------------------------- #
    def test_bien_desactive_n_est_pas_supprime(self):
        bien_initial = self.peuple["bien"]
        # Remplacement : retrait + ajout (pour respecter l'état final valide).
        rep_mod = self.client_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "Remplacement du bien",
                "objet_modification_ar": "استبدال المال",
                "diff_propose": {
                    "biens": {
                        "retirer": [bien_initial.pk],
                        "ajouter": [{"description_fr": "Bien neuf",
                                     "description_ar": "مال جديد"}],
                    },
                },
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        id_mod = rep_mod.data["id"]
        self.client_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )

        # Le bien initial reste en base (art. 79) mais désactivé.
        bien = BienGreve.objects.get(pk=bien_initial.pk)
        self.assertFalse(bien.actif)
        self.assertIsNotNone(bien.date_fin_validite)
        self.assertIn("modification.demande#", bien.raison_fin)

        # La suppression physique reste interdite au niveau ORM.
        with self.assertRaises(PermissionError):
            bien.delete()

    def test_role_desactive_n_est_pas_supprime(self):
        # Remplacement d'un constituant par un nouveau.
        rep_mod = self.client_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "Changement de constituant",
                "objet_modification_ar": "تغيير المنشئ",
                "diff_propose": {
                    "parties": {
                        "retirer": [self.peuple["lien_constituant"].pk],
                        "ajouter": [{
                            "role": RolePartie.CONSTITUANT,
                            "type_partie": TypePartie.PERSONNE_MORALE,
                            "donnees": {
                                "denomination_sociale": "Nouveau SA",
                                "numero_rc": "RC/NKT/2024/9999",
                            },
                        }],
                    },
                },
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        id_mod = rep_mod.data["id"]
        self.client_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )

        lien_initial = RoleInscriptionPartie.objects.get(
            pk=self.peuple["lien_constituant"].pk
        )
        self.assertFalse(lien_initial.actif)
        self.assertIsNotNone(lien_initial.date_fin_validite)
        with self.assertRaises(PermissionError):
            lien_initial.delete()

    # --------------------------------------------------------------------- #
    # Snapshots immuables                                                     #
    # --------------------------------------------------------------------- #
    def test_snapshot_non_modifiable_ni_supprimable(self):
        # Crée un snapshot via une modification minimale.
        rep_mod = self.client_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "Modification minime",
                "objet_modification_ar": "تعديل طفيف",
                "diff_propose": {"scalaires": {"monnaie": "MRU"}},
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        id_mod = rep_mod.data["id"]
        self.client_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )

        snapshot = SnapshotInscription.objects.filter(
            demande_modification_id=id_mod,
        ).first()
        self.assertIsNotNone(snapshot)

        with self.assertRaises(PermissionError):
            snapshot.save()
        with self.assertRaises(PermissionError):
            snapshot.delete()
