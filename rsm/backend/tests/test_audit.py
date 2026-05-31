"""
Tests du journal d'audit — TDR § 5.2, articles 79 et 82.

Points vérifiés :
- chaînage cryptographique (empreinte incluant la précédente) ;
- immuabilité : toute modification ou suppression est rejetée ;
- indépendance linguistique (seuls les codes d'action sont stockés) ;
- cohérence du ``ResultatAudit`` et de la ``CategorieAudit`` avec les
  énumérations.
"""
from __future__ import annotations

from django.test import TestCase

from apps.audit.models import (
    CategorieAudit,
    EntreeAudit,
    ResultatAudit,
)
from apps.audit.services import ContexteAudit, tracer, verifier_chaine


class JournalAuditTests(TestCase):
    def test_ajout_et_chainage(self):
        e1 = tracer(
            categorie=CategorieAudit.SYSTEME, action_cle="systeme.demarrage",
            resultat=ResultatAudit.SUCCES,
        )
        e2 = tracer(
            categorie=CategorieAudit.DEMANDE, action_cle="inscription.deposer",
            resultat=ResultatAudit.SUCCES,
            contexte=ContexteAudit(adresse_ip="127.0.0.1"),
        )
        # L'empreinte précédente de e2 est l'empreinte de e1.
        self.assertEqual(e2.empreinte_precedente, e1.empreinte)
        self.assertNotEqual(e1.empreinte, e2.empreinte)

    def test_immuabilite_update(self):
        e = tracer(
            categorie=CategorieAudit.SYSTEME, action_cle="systeme.test",
            resultat=ResultatAudit.SUCCES,
        )
        with self.assertRaises(PermissionError):
            e.action_cle = "altere"
            e.save()

    def test_immuabilite_delete(self):
        e = tracer(
            categorie=CategorieAudit.SYSTEME, action_cle="systeme.test",
            resultat=ResultatAudit.SUCCES,
        )
        with self.assertRaises(PermissionError):
            e.delete()

    def test_categories_valides_uniquement(self):
        with self.assertRaises(ValueError):
            tracer(
                categorie="inexistante", action_cle="x",
                resultat=ResultatAudit.SUCCES,
            )

    def test_resultats_valides_uniquement(self):
        with self.assertRaises(ValueError):
            tracer(
                categorie=CategorieAudit.SYSTEME, action_cle="x",
                resultat="xyz",
            )

    def test_verifier_chaine_detecte_absence_alteration(self):
        for i in range(5):
            tracer(
                categorie=CategorieAudit.SYSTEME,
                action_cle=f"systeme.{i}",
                resultat=ResultatAudit.SUCCES,
            )
        ok, premier_altere = verifier_chaine()
        self.assertTrue(ok)
        self.assertIsNone(premier_altere)

    def test_independance_linguistique_stockage(self):
        """
        § 7.6 — le journal conserve des clés neutres (``action_cle``),
        indépendamment de la langue d'interface utilisée.
        """
        tracer(
            categorie=CategorieAudit.RECHERCHE,
            action_cle="recherche.lancer",
            resultat=ResultatAudit.SUCCES,
        )
        e = EntreeAudit.objects.order_by("-id").first()
        # La clé d'action est stable, lisible dans les deux langues.
        self.assertEqual(e.action_cle, "recherche.lancer")
