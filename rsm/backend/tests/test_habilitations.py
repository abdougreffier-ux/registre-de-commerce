"""
Tests des rôles et de la séparation stricte — TDR § 4.1.

Règle cardinale : « Aucun utilisateur ne peut cumuler les rôles d'agent
de saisie et d'autorité de validation sur la même demande. »
"""
from __future__ import annotations

from django.test import TestCase

from apps.inscriptions.services import valider_inscription
from apps.utilisateurs.habilitations import (
    AutorisationRefusee,
    ecriture_metier_autorisee,
    peut_enregistrer_demande,
    peut_lire_audit,
    peut_produire_statistiques,
    peut_valider_demande,
    verifier_non_cumul,
)
from apps.utilisateurs.models import AffectationRole, RoleApplicatif

from tests import helpers


class SeparationStricteTests(TestCase):
    """Un même acteur ne peut saisir ET valider la même demande."""

    def test_meme_utilisateur_ne_peut_valider_sa_propre_demande(self):
        # Agent de saisie ET autorité de validation — accumule les deux rôles
        # sur un même compte (autorisé tant que la séparation se fait au niveau
        # de la demande).
        mixte = helpers.creer_utilisateur(
            username="mixte",
            roles=[
                RoleApplicatif.AGENT_SAISIE,
                RoleApplicatif.AUTORITE_VALIDATION,
            ],
        )
        demande = helpers.deposer_demande_standard(acteur=mixte)
        # L'utilisateur ayant saisi NE PEUT PAS valider la même demande.
        with self.assertRaises(AutorisationRefusee):
            valider_inscription(inscription=demande, acteur=mixte)

    def test_agent_peut_saisir_et_autre_peut_valider(self):
        agent = helpers.creer_agent_saisie()
        greffier = helpers.creer_greffier()
        demande = helpers.deposer_demande_standard(acteur=agent)
        inscription = valider_inscription(inscription=demande, acteur=greffier)
        self.assertIsNotNone(inscription.numero_ordre)

    def test_declarant_externe_ne_peut_pas_valider(self):
        declarant = helpers.creer_utilisateur(
            username="decl",
            roles=[RoleApplicatif.DECLARANT_EXTERNE],
        )
        self.assertFalse(peut_valider_demande(declarant, saisie_par=None))


class HabilitationsParRoleTests(TestCase):
    """Mise en correspondance rôles ↔ actes (§ 4.1)."""

    def test_agent_saisie_peut_enregistrer(self):
        u = helpers.creer_agent_saisie()
        self.assertTrue(peut_enregistrer_demande(u))

    def test_declarant_externe_peut_enregistrer(self):
        u = helpers.creer_utilisateur(
            username="decl2",
            roles=[RoleApplicatif.DECLARANT_EXTERNE],
        )
        self.assertTrue(peut_enregistrer_demande(u))

    def test_auditeur_ne_peut_pas_ecrire_metier(self):
        u = helpers.creer_utilisateur(
            username="aud", roles=[RoleApplicatif.AUDITEUR]
        )
        self.assertFalse(peut_enregistrer_demande(u))
        self.assertFalse(peut_valider_demande(u, saisie_par=None))
        self.assertTrue(peut_lire_audit(u))

    def test_administrateur_fonctionnel_pas_d_ecriture_metier(self):
        u = helpers.creer_utilisateur(
            username="af", roles=[RoleApplicatif.ADMIN_FONCTIONNEL]
        )
        # Les administrateurs n'ont pas d'accès utile aux contenus métier.
        self.assertFalse(ecriture_metier_autorisee(u))

    def test_administrateur_technique_pas_d_ecriture_metier(self):
        u = helpers.creer_utilisateur(
            username="at", roles=[RoleApplicatif.ADMIN_TECHNIQUE]
        )
        self.assertFalse(ecriture_metier_autorisee(u))

    def test_monopole_statistiques(self):
        """Article 82 — seul le greffe (rôle dédié) produit des statistiques."""
        lambda_user = helpers.creer_agent_saisie("lambda")
        self.assertFalse(peut_produire_statistiques(lambda_user))
        producteur = helpers.creer_utilisateur(
            username="prod", roles=[RoleApplicatif.PROD_STATS]
        )
        self.assertTrue(peut_produire_statistiques(producteur))


class NonCumulTests(TestCase):
    """
    Règle § 4.1 — cumul agent de saisie + autorité de validation interdit.

    Le non-cumul est contrôlé au moment des actes métier (via
    ``peut_valider_demande``) mais un modèle peut également refuser
    structurellement les deux rôles actifs simultanément via
    ``verifier_non_cumul``.
    """

    def test_detection_cumul_roles_incompatibles(self):
        u = helpers.creer_utilisateur(
            username="cumul",
            roles=[
                RoleApplicatif.AGENT_SAISIE,
                RoleApplicatif.AUTORITE_VALIDATION,
            ],
        )
        with self.assertRaises(AutorisationRefusee):
            verifier_non_cumul(u)
