"""
Uniformité du durcissement des serializers — toute clé inconnue REFUSÉE.

Principe de « cohérence globale » (TDR) : la règle de rejet des clés
inconnues doit s'appliquer de façon identique à tous les points d'entrée
en écriture de l'API.

Ce fichier parcourt les endpoints d'écriture et vérifie, pour chacun,
qu'une clé inconnue provoque un 400 avec le champ ``non_autorises`` dans
la réponse.
"""
from __future__ import annotations

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.enums import CanalSaisie, NaturesDroitInscrit

from tests import helpers


class ClesInconnuesRefusees_Uniformite_Tests(TestCase):
    """
    Couvre un échantillon représentatif d'endpoints d'écriture.
    Chaque test soumet une clé fantaisiste et exige un 400 + le champ
    ``non_autorises`` dans la réponse.
    """

    def setUp(self):
        self.agent = helpers.creer_agent_saisie("u_agent")
        self.greffier = helpers.creer_greffier("u_greffier")
        self.client_agent = APIClient()
        self.client_agent.force_authenticate(self.agent)
        self.client_greffier = APIClient()
        self.client_greffier.force_authenticate(self.greffier)

    def _assert_cle_inconnue_refusee(self, rep):
        self.assertEqual(
            rep.status_code, status.HTTP_400_BAD_REQUEST,
            f"Clé inconnue acceptée à tort. Body : {rep.data}",
        )
        self.assertIn(
            "non_autorises", rep.data,
            f"Clé 'non_autorises' attendue dans la réponse. Body : {rep.data}",
        )

    # --------------------------------------------------------------------- #
    # Dépôt d'inscription                                                    #
    # --------------------------------------------------------------------- #
    def test_depot_inscription_cle_inconnue_refusee(self):
        rep = self.client_agent.post(
            "/api/v1/inscriptions/",
            data={
                "canal_saisie": CanalSaisie.GUICHET_PAPIER,
                "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                "somme_garantie": "1000",
                "monnaie": "MRU",
                "duree_en_jours": 30,
                "champ_fantaisiste": "valeur",  # hors schéma
            },
            format="json",
        )
        self._assert_cle_inconnue_refusee(rep)

    # --------------------------------------------------------------------- #
    # Rejet d'inscription                                                    #
    # --------------------------------------------------------------------- #
    def test_rejet_inscription_cle_inconnue_refusee(self):
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
            data={"motif": "informations_illisibles", "champ_fantaisiste": 1},
            format="json",
        )
        self._assert_cle_inconnue_refusee(rep)

    # --------------------------------------------------------------------- #
    # Création de demande de modification                                    #
    # --------------------------------------------------------------------- #
    def test_creation_modification_cle_inconnue_refusee(self):
        inscription, _peuple, _agent, _greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        rep = self.client_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": inscription.pk,
                "objet_modification_fr": "x",
                "objet_modification_ar": "x",
                "diff_propose": {"scalaires": {"monnaie": "MRU"}},
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
                "champ_fantaisiste": True,
            },
            format="json",
        )
        self._assert_cle_inconnue_refusee(rep)

    # --------------------------------------------------------------------- #
    # Création de demande de renouvellement                                  #
    # --------------------------------------------------------------------- #
    def test_creation_renouvellement_cle_inconnue_refusee(self):
        inscription, _peuple, _agent, _greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        rep = self.client_agent.post(
            "/api/v1/renouvellements/",
            data={
                "inscription": inscription.pk,
                "champ_fantaisiste": 1,
            },
            format="json",
        )
        self._assert_cle_inconnue_refusee(rep)

    # --------------------------------------------------------------------- #
    # Création de demande de radiation                                       #
    # --------------------------------------------------------------------- #
    def test_creation_radiation_cle_inconnue_refusee(self):
        inscription, _peuple, _agent, _greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        rep = self.client_agent.post(
            "/api/v1/radiations/",
            data={
                "inscription": inscription.pk,
                "fondement": "consentement",
                "champ_fantaisiste": 1,
            },
            format="json",
        )
        self._assert_cle_inconnue_refusee(rep)

    # --------------------------------------------------------------------- #
    # Recherche publique                                                     #
    # --------------------------------------------------------------------- #
    def test_recherche_cle_inconnue_refusee(self):
        client_public = APIClient()
        rep = client_public.post(
            "/api/v1/recherche/",
            data={
                "nom_constituant": "X",
                "numero_rc": "Y",
                "champ_fantaisiste": "Z",
            },
            format="json",
        )
        self._assert_cle_inconnue_refusee(rep)
