"""
Scénario S2 — Rejets motivés au sens de l'article 80.

Règle cardinale : les motifs de rejet sont LIMITATIVEMENT énumérés par
l'article 80. L'article 86 interdit au greffier tout contrôle au fond :
la forme seule est contrôlée.

Assertions :
- canal non autorisé au dépôt → 400 + référence article ;
- motif hors liste au moment du rejet → 400 ;
- rejet par motif limitatif → statut REJETEE, pas au fichier public,
  tracé au journal d'audit.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.audit.models import EntreeAudit
from apps.core.enums import CanalSaisie, MotifRejet, NaturesDroitInscrit
from apps.inscriptions.models import Inscription
from apps.workflow.statuts import (
    STATUTS_FICHIER_PUBLIC,
    StatutInscription,
)

from tests import helpers


class S2_RejetArt80_API_Tests(APITestCase):
    def setUp(self):
        self.agent = helpers.creer_agent_saisie("s2_agent")
        self.greffier = helpers.creer_greffier("s2_greffier")
        self.client_agent = APIClient()
        self.client_agent.force_authenticate(self.agent)
        self.client_greffier = APIClient()
        self.client_greffier.force_authenticate(self.greffier)

    def test_canal_hors_liste_refuse_au_depot(self):
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data={
                "canal_saisie": "canal_inexistant",  # hors liste art. 78
                "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                "somme_garantie": "1000",
                "monnaie": "MRU",
                "duree_en_jours": 30,
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rep.data.get("article"), "80")

    def test_nature_droit_hors_liste_refusee(self):
        """Art. 76 — liste limitative."""
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data={
                "canal_saisie": CanalSaisie.GUICHET_PAPIER,
                "nature_droit": "nature_inventee",
                "somme_garantie": "1000",
                "monnaie": "MRU",
                "duree_en_jours": 30,
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rep.data.get("article"), "80")

    def test_rejet_motif_hors_liste_refuse(self):
        # Dépôt valide.
        depot = self.client_agent.post(
            "/api/v1/inscriptions/",
            data={
                "canal_saisie": CanalSaisie.GUICHET_PAPIER,
                "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                "somme_garantie": "1000",
                "monnaie": "MRU",
                "duree_en_jours": 30,
            },
            format="json",
        )
        ref = depot.data["reference_demande"]

        # Tentative de rejet avec motif inventé.
        rep = self.client_greffier.post(
            f"/api/v1/inscriptions/{ref}/rejeter/",
            data={"motif": "motif_non_limitatif"},
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejet_motif_limitatif_accepte(self):
        depot = self.client_agent.post(
            "/api/v1/inscriptions/",
            data={
                "canal_saisie": CanalSaisie.GUICHET_PAPIER,
                "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                "somme_garantie": "1000",
                "monnaie": "MRU",
                "duree_en_jours": 30,
            },
            format="json",
        )
        ref = depot.data["reference_demande"]

        rep = self.client_greffier.post(
            f"/api/v1/inscriptions/{ref}/rejeter/",
            data={
                "motif": MotifRejet.INFORMATIONS_ILLISIBLES,
                "commentaire_fr": "Document scanné illisible",
                "commentaire_ar": "الوثيقة الممسوحة غير مقروءة",
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK, rep.data)
        self.assertEqual(rep.data["statut"], StatutInscription.REJETEE)
        self.assertEqual(
            rep.data["motif_rejet"], MotifRejet.INFORMATIONS_ILLISIBLES,
        )
        # Commentaires bilingues préservés.
        self.assertEqual(rep.data["commentaire_rejet_fr"], "Document scanné illisible")
        self.assertEqual(rep.data["commentaire_rejet_ar"], "الوثيقة الممسوحة غير مقروءة")

        # Une inscription rejetée n'est PAS au fichier public.
        inscription = Inscription.objects.get(reference_demande=ref)
        self.assertNotIn(inscription.statut, STATUTS_FICHIER_PUBLIC)

        # Trace du rejet au journal d'audit.
        traces = EntreeAudit.objects.filter(
            action_cle="inscription.rejeter",
            objet_reference=str(ref),
        )
        self.assertEqual(traces.count(), 1)
        trace = traces.first()
        self.assertEqual(trace.resultat, "rejet")
        self.assertEqual(
            trace.details.get("motif"), MotifRejet.INFORMATIONS_ILLISIBLES,
        )
