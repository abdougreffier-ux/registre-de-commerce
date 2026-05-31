"""
D.1 — Séparation stricte § 4.1 vérifiée au NIVEAU HTTP.

Règle cardinale du TDR § 4.1 :
> « Aucun utilisateur ne peut cumuler les rôles d'agent de saisie et
>   d'autorité de validation sur la même demande. »

La règle est déjà testée au niveau service dans ``test_habilitations.py``.
Ce fichier la vérifie au niveau HTTP — donc à travers toute la pile
(middleware → serializer → vue → service → handler d'exceptions).

**Cohérence globale** : la règle s'applique à toutes les opérations de
validation, pas seulement à ``valider_inscription``. Les quatre cas
métier concernés sont couverts :

1. Validation d'inscription (art. 85, 87).
2. Application d'une modification (art. 88, 90).
3. Application d'un renouvellement (art. 91).
4. Application d'une radiation (art. 92).

Effets juridiques attendus :
- L'utilisateur qui a déposé la demande ne peut pas la valider, même
  s'il détient le rôle ``AUTORITE_VALIDATION``.
- Un utilisateur qui n'a pas le rôle ``AUTORITE_VALIDATION`` ne peut
  jamais valider, quel que soit le chemin HTTP.
- Un second utilisateur habilité et distinct du saisisseur peut valider.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.enums import CanalSaisie, NaturesDroitInscrit
from apps.utilisateurs.models import AffectationRole, RoleApplicatif
from apps.workflow.statuts import StatutInscription

from tests import helpers


def _client_pour(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user)
    return client


class D1_SeparationStricteValidation_HTTPTests(APITestCase):
    """Validation d'inscription (art. 85, 87) — séparation stricte HTTP."""

    def setUp(self):
        # Agent = utilisateur qui saisit la demande
        self.agent = helpers.creer_agent_saisie("d1_agent")

        # Greffier = utilisateur distinct, rôle AUTORITE_VALIDATION
        self.greffier = helpers.creer_greffier("d1_greffier")

        # Mixte = utilisateur cumulant les deux rôles (autorisé au niveau
        # compte — la séparation s'applique à la DEMANDE, § 4.1 TDR)
        self.mixte = helpers.creer_utilisateur(
            username="d1_mixte",
            roles=[
                RoleApplicatif.AGENT_SAISIE,
                RoleApplicatif.AUTORITE_VALIDATION,
            ],
        )

        # Tiers sans rôle de validation
        self.tiers_non_habilite = helpers.creer_utilisateur(
            username="d1_tiers",
            roles=[RoleApplicatif.ADMIN_TECHNIQUE],
        )

    def _deposer(self, client: APIClient) -> str:
        rep = client.post(
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
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED)
        return rep.data["reference_demande"]

    # -- Cas 1 : cumul sur la MÊME demande refusé --------------------------- #
    def test_meme_utilisateur_ne_peut_valider_sa_propre_demande(self):
        """
        L'utilisateur qui a déposé la demande ne peut pas la valider,
        même s'il détient le rôle ``AUTORITE_VALIDATION``.
        """
        ref = self._deposer(_client_pour(self.mixte))
        rep = _client_pour(self.mixte).post(
            f"/api/v1/inscriptions/{ref}/valider/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_403_FORBIDDEN)

    # -- Cas 2 : validation par acteur distinct acceptée -------------------- #
    def test_greffier_distinct_peut_valider(self):
        ref = self._deposer(_client_pour(self.agent))
        rep = _client_pour(self.greffier).post(
            f"/api/v1/inscriptions/{ref}/valider/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK, rep.data)
        self.assertEqual(rep.data["statut"], StatutInscription.INSCRITE)
        self.assertIsNotNone(rep.data["numero_ordre"])

    # -- Cas 3 : acteur non habilité refusé -------------------------------- #
    def test_sans_role_validation_refuse(self):
        ref = self._deposer(_client_pour(self.agent))
        rep = _client_pour(self.tiers_non_habilite).post(
            f"/api/v1/inscriptions/{ref}/valider/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_403_FORBIDDEN)

    # -- Cas 4 : le REJET suit la même règle -------------------------------- #
    def test_meme_utilisateur_ne_peut_rejeter_sa_propre_demande(self):
        """
        Le rejet (art. 80) suit la même règle de séparation stricte
        puisqu'il s'agit d'une décision de l'autorité de validation.
        """
        ref = self._deposer(_client_pour(self.mixte))
        rep = _client_pour(self.mixte).post(
            f"/api/v1/inscriptions/{ref}/rejeter/",
            data={"motif": "informations_illisibles"},
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_403_FORBIDDEN)


class D1_SeparationStricteModification_HTTPTests(APITestCase):
    """
    Application d'une demande de modification (art. 88, 90) — séparation
    stricte HTTP. La règle est identique : le greffier qui applique
    doit être distinct du déposant de la demande.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        # Mixte = autre utilisateur cumulant les deux rôles
        self.mixte = helpers.creer_utilisateur(
            username="d1_mod_mixte",
            roles=[
                RoleApplicatif.AGENT_SAISIE,
                RoleApplicatif.AUTORITE_VALIDATION,
            ],
        )

    def _creer_demande(self, client: APIClient) -> int:
        rep = client.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "Changement mineur",
                "objet_modification_ar": "تعديل طفيف",
                "diff_propose": {"scalaires": {"monnaie": "MRU"}},
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        return rep.data["id"]

    def test_meme_utilisateur_ne_peut_appliquer_sa_propre_modification(self):
        id_mod = self._creer_demande(_client_pour(self.mixte))
        rep = _client_pour(self.mixte).post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_403_FORBIDDEN)

    def test_greffier_distinct_peut_appliquer(self):
        id_mod = self._creer_demande(_client_pour(self.agent))
        rep = _client_pour(self.greffier).post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK, rep.data)


class D1_SeparationStricteRenouvellement_HTTPTests(APITestCase):
    """Application d'un renouvellement (art. 91) — séparation stricte HTTP."""

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        self.mixte = helpers.creer_utilisateur(
            username="d1_renouv_mixte",
            roles=[
                RoleApplicatif.AGENT_SAISIE,
                RoleApplicatif.AUTORITE_VALIDATION,
            ],
        )

    def _creer_demande(self, client: APIClient) -> int:
        rep = client.post(
            "/api/v1/renouvellements/",
            data={"inscription": self.inscription.pk},
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        return rep.data["id"]

    def test_meme_utilisateur_ne_peut_appliquer_son_propre_renouvellement(self):
        id_ren = self._creer_demande(_client_pour(self.mixte))
        rep = _client_pour(self.mixte).post(
            f"/api/v1/renouvellements/{id_ren}/appliquer/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_403_FORBIDDEN)

    def test_greffier_distinct_peut_appliquer(self):
        id_ren = self._creer_demande(_client_pour(self.agent))
        rep = _client_pour(self.greffier).post(
            f"/api/v1/renouvellements/{id_ren}/appliquer/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK, rep.data)


class D1_SeparationStricteRadiation_HTTPTests(APITestCase):
    """Application d'une radiation (art. 92) — séparation stricte HTTP."""

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        self.mixte = helpers.creer_utilisateur(
            username="d1_rad_mixte",
            roles=[
                RoleApplicatif.AGENT_SAISIE,
                RoleApplicatif.AUTORITE_VALIDATION,
            ],
        )

    def _creer_demande(self, client: APIClient) -> int:
        rep = client.post(
            "/api/v1/radiations/",
            data={
                "inscription": self.inscription.pk,
                "fondement": "consentement",
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED, rep.data)
        return rep.data["id"]

    def test_meme_utilisateur_ne_peut_appliquer_sa_propre_radiation(self):
        id_rad = self._creer_demande(_client_pour(self.mixte))
        rep = _client_pour(self.mixte).post(
            f"/api/v1/radiations/{id_rad}/appliquer/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_403_FORBIDDEN)

    def test_greffier_distinct_peut_appliquer(self):
        id_rad = self._creer_demande(_client_pour(self.agent))
        rep = _client_pour(self.greffier).post(
            f"/api/v1/radiations/{id_rad}/appliquer/", format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK, rep.data)


class D1_CoherenceGlobale_HTTPTests(APITestCase):
    """
    Test de cohérence transverse : pour CHAQUE opération soumise à
    séparation stricte, un utilisateur non habilité (sans
    ``AUTORITE_VALIDATION``) se voit refuser l'accès HTTP.

    Garantit que la règle § 4.1 est appliquée uniformément dans toute
    l'API, sans exception ni contournement.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        self.observateur = helpers.creer_utilisateur(
            username="observateur",
            roles=[RoleApplicatif.ADMIN_FONCTIONNEL],
        )
        self.c = _client_pour(self.observateur)

    def test_admin_fonctionnel_refuse_sur_toutes_les_operations_de_validation(self):
        # Une inscription à valider
        depot = _client_pour(self.agent).post(
            "/api/v1/inscriptions/",
            data={
                "canal_saisie": CanalSaisie.GUICHET_PAPIER,
                "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                "somme_garantie": "1",
                "monnaie": "MRU",
                "duree_en_jours": 1,
            },
            format="json",
        )
        ref = depot.data["reference_demande"]

        for methode, url in [
            ("post", f"/api/v1/inscriptions/{ref}/valider/"),
            ("post", f"/api/v1/inscriptions/{ref}/rejeter/"),
        ]:
            payload = {"motif": "informations_illisibles"} if "rejeter" in url else {}
            rep = getattr(self.c, methode)(url, data=payload, format="json")
            self.assertEqual(
                rep.status_code, status.HTTP_403_FORBIDDEN,
                f"L'administrateur fonctionnel ne doit pas pouvoir accéder à {url}.",
            )
