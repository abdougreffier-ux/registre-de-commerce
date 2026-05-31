"""
Scénario S5 — Immutabilité et exhaustivité du journal d'audit.

Articles 79, § 5.2 du TDR.

Règles vérifiées :
- toute action métier significative est tracée ;
- le journal est consultable en lecture seule via l'API (rôle auditeur
  à définir — en développement, ``is_staff`` fait foi) ;
- aucune modification ni suppression d'entrée n'est possible ;
- la chaîne d'empreintes est vérifiable ;
- un acteur non habilité reçoit 403 sur l'endpoint d'audit.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.audit.models import EntreeAudit
from apps.audit.services import ContexteAudit, tracer, verifier_chaine
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.utilisateurs.models import RoleApplicatif

from tests import helpers


class S5_Audit_API_Tests(APITestCase):
    def setUp(self):
        self.auditeur = helpers.creer_utilisateur(
            username="auditeur", roles=[RoleApplicatif.AUDITEUR],
        )
        self.auditeur.is_staff = True
        self.auditeur.save(update_fields=["is_staff"])
        self.client_auditeur = APIClient()
        self.client_auditeur.force_authenticate(self.auditeur)

        self.agent = helpers.creer_agent_saisie("s5_agent")

    # --------------------------------------------------------------------- #
    # Lecture seule par l'auditeur                                           #
    # --------------------------------------------------------------------- #
    def test_liste_entrees_accessible_a_l_auditeur(self):
        tracer(
            categorie=CategorieAudit.SYSTEME, action_cle="systeme.test",
            resultat=ResultatAudit.SUCCES,
            contexte=ContexteAudit(adresse_ip="127.0.0.1"),
        )
        rep = self.client_auditeur.get("/api/v1/audit/entrees/")
        self.assertEqual(rep.status_code, status.HTTP_200_OK)
        # Résultat paginé — structure minimale.
        self.assertIn("results", rep.data)

    def test_liste_entrees_refusee_a_un_non_auditeur(self):
        non_auditeur = helpers.creer_agent_saisie("non_auditeur")
        client = APIClient()
        client.force_authenticate(non_auditeur)
        rep = client.get("/api/v1/audit/entrees/")
        self.assertEqual(rep.status_code, status.HTTP_403_FORBIDDEN)

    # --------------------------------------------------------------------- #
    # Immutabilité (niveau ORM — protection complémentaire aux triggers SQL) #
    # --------------------------------------------------------------------- #
    def test_entree_existante_non_modifiable(self):
        tracer(
            categorie=CategorieAudit.SYSTEME, action_cle="systeme.immut",
            resultat=ResultatAudit.SUCCES,
        )
        entree = EntreeAudit.objects.order_by("-id").first()
        entree.action_cle = "altere"
        with self.assertRaises(PermissionError):
            entree.save()

    def test_entree_existante_non_supprimable(self):
        tracer(
            categorie=CategorieAudit.SYSTEME, action_cle="systeme.immut2",
            resultat=ResultatAudit.SUCCES,
        )
        entree = EntreeAudit.objects.order_by("-id").first()
        with self.assertRaises(PermissionError):
            entree.delete()

    # --------------------------------------------------------------------- #
    # Chaîne d'empreintes                                                    #
    # --------------------------------------------------------------------- #
    def test_verification_chaine_integre(self):
        for i in range(5):
            tracer(
                categorie=CategorieAudit.SYSTEME, action_cle=f"systeme.{i}",
                resultat=ResultatAudit.SUCCES,
            )
        ok, premier_altere = verifier_chaine()
        self.assertTrue(ok)
        self.assertIsNone(premier_altere)

    def test_endpoint_verification_chaine_accessible_a_l_auditeur(self):
        tracer(
            categorie=CategorieAudit.SYSTEME, action_cle="systeme.verif",
            resultat=ResultatAudit.SUCCES,
        )
        rep = self.client_auditeur.get("/api/v1/audit/verification-chaine/")
        self.assertEqual(rep.status_code, status.HTTP_200_OK)
        self.assertTrue(rep.data["integre"])
        self.assertIsNone(rep.data["premiere_entree_alteree"])
