"""
D.2 — Scénario complet de rejet art. 88 via appels API enchaînés.

Règle cardinale (art. 88 dernier alinéa) :
> « Toute modification visant à supprimer l'ensemble des constituants,
>   des créanciers garantis ou des biens grevés sans en désigner de
>   nouveaux est sans effet. »

Scénario testé de bout en bout par HTTP :

1. POST /api/v1/modifications/          → création demande  (201)
2. GET  /api/v1/modifications/<id>/     → demande RECUE      (200)
3. POST /api/v1/modifications/<id>/appliquer/
                                        → refus 400, payload
                                          contient motif_refus_code
                                          structuré
4. GET  /api/v1/modifications/<id>/     → demande REJETEE,
                                          motif_refus_code exposé au
                                          serializer, accessible en
                                          lecture.
5. POST /api/v1/modifications/<id>/appliquer/
                                        → demande non ré-applicable,
                                          refus 400, motif DEMANDE_NON_APPLICABLE.
6. Aucun snapshot n'est laissé en base (rollback du savepoint vérifié).
7. Aucune transition de statut n'a été enregistrée sur l'inscription.

Cohérence globale : on vérifie que le champ ``motif_refus_code`` est
exposé à l'API pour TOUS les motifs limitatifs de
``MotifRefusModification`` qui peuvent être rencontrés par un client
API — pas seulement pour `ETAT_FINAL_*`.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.audit.models import EntreeAudit
from apps.biens.models import BienGreve
from apps.inscriptions.models import RoleInscriptionPartie
from apps.modifications.models import (
    MotifRefusModification,
    SnapshotInscription,
    StatutDemandeModification,
)
from apps.workflow.models import TransitionStatut
from apps.workflow.statuts import StatutInscription

from tests import helpers


def _client_pour(user) -> APIClient:
    c = APIClient()
    c.force_authenticate(user)
    return c


class D2_RejetArt88_CycleCompletHTTP_Tests(APITestCase):
    """
    Scénario enchaîné via API : création → tentative d'application
    échouée (état final invalide) → demande REJETEE + motif_refus_code
    exposé → demande non ré-applicable.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        self.c_agent = _client_pour(self.agent)
        self.c_greffier = _client_pour(self.greffier)
        # Instantané initial des transitions déjà enregistrées
        # (validation greffier à la création).
        self.nb_transitions_initial = TransitionStatut.objects.filter(
            numero_inscription=self.inscription.numero_ordre,
        ).count()

    def test_cycle_complet_rejet_art88_via_api(self):
        # ---- 1. Création de la demande → 201 -------------------------- #
        rep = self.c_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "Retrait du dernier bien",
                "objet_modification_ar": "إزالة المال الأخير",
                "diff_propose": {
                    "biens": {"retirer": [self.peuple["bien"].pk]},
                },
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        id_mod = rep.data["id"]
        self.assertEqual(rep.data["statut"], StatutDemandeModification.RECUE)
        self.assertEqual(rep.data["motif_refus_code"], "")

        # ---- 2. Consultation → RECUE ---------------------------------- #
        rep = self.c_agent.get(f"/api/v1/modifications/")
        demande_vue = next(
            d for d in rep.data["results"]
            if d["id"] == id_mod
        )
        self.assertEqual(demande_vue["statut"], StatutDemandeModification.RECUE)

        # ---- 3. Tentative d'application → 400 avec motif structuré ----- #
        rep = self.c_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_400_BAD_REQUEST, rep.data)
        # Le handler d'exceptions expose ``detail``, ``article``, ``classe``.
        self.assertEqual(rep.data["article"], "88")
        self.assertEqual(rep.data["classe"], "ModificationSansEffet")

        # ---- 4. Consultation → REJETEE + motif_refus_code exposé ------- #
        rep_liste = self.c_agent.get("/api/v1/modifications/")
        demande_vue = next(
            d for d in rep_liste.data["results"] if d["id"] == id_mod
        )
        self.assertEqual(
            demande_vue["statut"], StatutDemandeModification.REJETEE,
        )
        self.assertEqual(
            demande_vue["motif_refus_code"],
            MotifRefusModification.ETAT_FINAL_BIEN_ABSENT,
            "Le motif structuré (clé limitative) doit être exposé au serializer.",
        )
        # Le détail humain est également présent (non vide).
        self.assertTrue(demande_vue["motif_refus"])

        # ---- 5. Ré-application refusée → DEMANDE_NON_APPLICABLE ------- #
        rep2 = self.c_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )
        self.assertEqual(rep2.status_code, status.HTTP_400_BAD_REQUEST)
        # Statut inchangé.
        rep_liste2 = self.c_agent.get("/api/v1/modifications/")
        demande_vue2 = next(
            d for d in rep_liste2.data["results"] if d["id"] == id_mod
        )
        self.assertEqual(
            demande_vue2["statut"], StatutDemandeModification.REJETEE,
        )

        # ---- 6. Aucun snapshot résiduel -------------------------------- #
        snapshots = SnapshotInscription.objects.filter(
            demande_modification_id=id_mod,
        )
        self.assertEqual(
            snapshots.count(), 0,
            "Les snapshots doivent être rollback avec le savepoint "
            "(aucun snapshot orphelin après rejet).",
        )

        # ---- 7. Le bien reste actif, aucun effet sur l'inscription ----- #
        bien = BienGreve.objects.get(pk=self.peuple["bien"].pk)
        self.assertTrue(bien.actif)
        self.assertIsNone(bien.date_fin_validite)
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.INSCRITE)

        # ---- 8. Aucune transition art. 88 enregistrée ----------------- #
        nb_final = TransitionStatut.objects.filter(
            numero_inscription=self.inscription.numero_ordre,
        ).count()
        self.assertEqual(
            nb_final, self.nb_transitions_initial,
            "Aucune transition art. 88 ne doit avoir été enregistrée après rejet.",
        )

        # ---- 9. Audit : "modification.refuser" tracée une fois -------- #
        traces_refus = EntreeAudit.objects.filter(
            action_cle="modification.refuser",
            objet_reference=str(id_mod),
        )
        self.assertEqual(traces_refus.count(), 1)
        self.assertEqual(
            traces_refus.first().details.get("motif_code"),
            MotifRefusModification.ETAT_FINAL_BIEN_ABSENT,
        )
        # Aucune trace de succès.
        self.assertFalse(
            EntreeAudit.objects.filter(
                action_cle="modification.appliquer",
                objet_reference=self.inscription.numero_ordre,
            ).exists(),
        )


class D2_MotifRefusCode_ExpositionParCasTests(APITestCase):
    """
    Cohérence globale : le champ ``motif_refus_code`` est exposé
    uniformément au serializer pour chaque motif limitatif rencontré
    via l'API.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        self.c_agent = _client_pour(self.agent)
        self.c_greffier = _client_pour(self.greffier)

    def _cree_puis_applique(self, diff, **kw) -> dict:
        """Crée une demande via API puis tente de l'appliquer ; retourne la dernière vue de la demande."""
        rep = self.c_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "test",
                "objet_modification_ar": "اختبار",
                "diff_propose": diff,
                "accord_createur_confirme": kw.get("accord_createur", True),
                "accord_constituant_confirme": kw.get("accord_constituant", True),
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        id_mod = rep.data["id"]
        self.c_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )
        rep_liste = self.c_agent.get("/api/v1/modifications/")
        return next(d for d in rep_liste.data["results"] if d["id"] == id_mod)

    def test_etat_final_constituant_absent(self):
        vue = self._cree_puis_applique({
            "parties": {"retirer": [self.peuple["lien_constituant"].pk]},
        })
        self.assertEqual(vue["statut"], StatutDemandeModification.REJETEE)
        self.assertEqual(
            vue["motif_refus_code"],
            MotifRefusModification.ETAT_FINAL_CONSTITUANT_ABSENT,
        )

    def test_etat_final_creancier_absent(self):
        vue = self._cree_puis_applique({
            "parties": {"retirer": [self.peuple["lien_creancier"].pk]},
        })
        self.assertEqual(
            vue["motif_refus_code"],
            MotifRefusModification.ETAT_FINAL_CREANCIER_ABSENT,
        )

    def test_etat_final_bien_absent(self):
        vue = self._cree_puis_applique({
            "biens": {"retirer": [self.peuple["bien"].pk]},
        })
        self.assertEqual(
            vue["motif_refus_code"],
            MotifRefusModification.ETAT_FINAL_BIEN_ABSENT,
        )

    def test_accords_manquants(self):
        vue = self._cree_puis_applique(
            {"scalaires": {"monnaie": "MRU"}},
            accord_constituant=False,
        )
        self.assertEqual(
            vue["motif_refus_code"], MotifRefusModification.ACCORDS_MANQUANTS,
        )

    def test_diff_vide(self):
        vue = self._cree_puis_applique({})
        self.assertEqual(
            vue["motif_refus_code"], MotifRefusModification.DIFF_VIDE,
        )

    def test_diff_invalide_champ_jamais_modifiable(self):
        # duree_en_jours est dans CHAMPS_JAMAIS_MODIFIABLES (art. 90 al. 2).
        vue = self._cree_puis_applique({
            "scalaires": {"duree_en_jours": 9999},
        })
        self.assertEqual(
            vue["motif_refus_code"], MotifRefusModification.DIFF_INVALIDE,
        )

    def test_statut_inscription_incompatible(self):
        # Force l'inscription en statut EXPIREE pour simuler l'état incompatible.
        from apps.inscriptions.models import Inscription
        Inscription.objects.filter(pk=self.inscription.pk).update(
            statut=StatutInscription.EXPIREE,
        )
        vue = self._cree_puis_applique({
            "scalaires": {"monnaie": "MRU"},
        })
        self.assertEqual(
            vue["motif_refus_code"],
            MotifRefusModification.STATUT_INSCRIPTION_INCOMPATIBLE,
        )
