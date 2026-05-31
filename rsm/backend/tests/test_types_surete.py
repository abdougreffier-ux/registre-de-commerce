"""
Tests des 4 parcours d'inscription distingués par ``type_surete``.

Vérifie que :
  1. depot_surete (parcours historique) reste fonctionnel.
  2. privilege_vendeur accepte le payload et persiste donnees_specifiques.
  3. reserve_propriete idem.
  4. credit_bail idem.
  5. Un type_surete inconnu est refusé (article 80 par analogie).
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase

from apps.core.enums import CanalSaisie, NaturesDroitInscrit
from apps.inscriptions.models import Inscription
from tests import helpers


class TypeSurete_API_Tests(TestCase):
    """Couvre les 4 valeurs de TypeSurete + un cas d'erreur."""

    def setUp(self):
        self.agent = helpers.creer_agent_saisie("api_agent_types")
        self.client_agent = APIClient()
        self.client_agent.force_authenticate(self.agent)

    def _payload_minimal(self, type_surete: str, donnees_specifiques: dict | None = None):
        return {
            "canal_saisie": CanalSaisie.GUICHET_PAPIER,
            "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
            "somme_garantie": "500000.00",
            "monnaie": "MRU",
            "duree_en_jours": 365,
            "type_surete": type_surete,
            "donnees_specifiques": donnees_specifiques or {},
        }

    def test_depot_surete_inchange(self):
        """Le parcours historique reste fonctionnel sans donnees_specifiques."""
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data=self._payload_minimal("depot_surete"),
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        ins = Inscription.objects.get(reference_demande=rep.data["reference_demande"])
        self.assertEqual(ins.type_surete, "depot_surete")
        self.assertEqual(ins.donnees_specifiques, {})

    def test_privilege_vendeur_persiste_donnees_specifiques(self):
        donnees = {
            "date_contrat_vente": "2026-01-15",
            "reference_contrat_vente": "VENT-2026-001",
            "prix_total_vente": 1500000,
            "montant_paye": 500000,
            "montant_restant_du": 1000000,
            "bien_livre": True,
            "acheteur_en_possession": True,
            "clause_privilege": "Le vendeur conserve un privilège jusqu'au paiement intégral.",
        }
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data=self._payload_minimal("privilege_vendeur", donnees),
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        ins = Inscription.objects.get(reference_demande=rep.data["reference_demande"])
        self.assertEqual(ins.type_surete, "privilege_vendeur")
        self.assertEqual(ins.donnees_specifiques["reference_contrat_vente"], "VENT-2026-001")
        self.assertEqual(ins.donnees_specifiques["prix_total_vente"], 1500000)
        self.assertTrue(ins.donnees_specifiques["bien_livre"])

    def test_reserve_propriete_persiste_donnees_specifiques(self):
        donnees = {
            "date_contrat": "2026-02-01",
            "reference_contrat": "RP-2026-007",
            "prix_total": 2000000,
            "clause_reserve_propriete": True,
            "texte_clause_reserve": "La propriété est réservée jusqu'au paiement intégral.",
            "propriete_conservee_par_vendeur": True,
            "modalites_paiement": "Paiement en 12 mensualités",
        }
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data=self._payload_minimal("reserve_propriete", donnees),
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        ins = Inscription.objects.get(reference_demande=rep.data["reference_demande"])
        self.assertEqual(ins.type_surete, "reserve_propriete")
        self.assertTrue(ins.donnees_specifiques["clause_reserve_propriete"])
        self.assertTrue(ins.donnees_specifiques["propriete_conservee_par_vendeur"])

    def test_credit_bail_persiste_donnees_specifiques(self):
        donnees = {
            "date_contrat": "2026-03-01",
            "reference_contrat": "CB-2026-042",
            "duree_contrat": "36 mois",
            "valeur_bien_finance": 5000000,
            "montant_total_loyers": 6000000,
            "periodicite_loyers": "mensuelle",
            "montant_loyer": 166667,
            "option_achat": True,
            "prix_levee_option": 100000,
            "bien_remis_preneur": True,
        }
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data=self._payload_minimal("credit_bail", donnees),
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        ins = Inscription.objects.get(reference_demande=rep.data["reference_demande"])
        self.assertEqual(ins.type_surete, "credit_bail")
        self.assertEqual(ins.donnees_specifiques["periodicite_loyers"], "mensuelle")
        self.assertTrue(ins.donnees_specifiques["option_achat"])

    def test_type_surete_inconnu_refuse(self):
        """Un type_surete hors énumération est refusé par le serializer."""
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data=self._payload_minimal("autre_chose"),
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_400_BAD_REQUEST)
