"""
Tests de la machine d'états et de la matrice des transitions (§ 4.3 TDR).

Chaque test cite l'article ou la règle du TDR qu'il matérialise.
"""
from __future__ import annotations

from django.test import TestCase

from apps.core.exceptions import TransitionInterdite
from apps.workflow.services import appliquer_transition
from apps.workflow.statuts import (
    INTERDICTIONS_EXPLICITES,
    TRANSITIONS,
    StatutInscription,
    est_autorisee,
    est_explicitement_interdite,
    transition_requise,
)


class MatriceTransitionsTests(TestCase):
    """Conformité de la matrice aux règles du § 4.3."""

    def test_transitions_listees_toutes_presentes(self):
        # Reçue → En contrôle de forme est automatique.
        self.assertTrue(est_autorisee(
            StatutInscription.RECUE,
            StatutInscription.EN_CONTROLE_FORME,
            "prise_en_charge",
        ))
        # En contrôle de forme → Inscrite sur validation greffier.
        self.assertTrue(est_autorisee(
            StatutInscription.EN_CONTROLE_FORME,
            StatutInscription.INSCRITE,
            "validation_greffier",
        ))
        # En contrôle de forme → Rejetée par motif art. 80.
        self.assertTrue(est_autorisee(
            StatutInscription.EN_CONTROLE_FORME,
            StatutInscription.REJETEE,
            "rejet_art80",
        ))

    def test_interdictions_explicites_enregistrees(self):
        """§ 4.3 — transitions explicitement interdites."""
        # Radiée → Inscrite : interdit (pas de retour en arrière).
        self.assertIsNotNone(est_explicitement_interdite(
            StatutInscription.RADIEE, StatutInscription.INSCRITE,
        ))
        # Expirée → Modifiée : interdit.
        self.assertIsNotNone(est_explicitement_interdite(
            StatutInscription.EXPIREE, StatutInscription.MODIFIEE,
        ))
        # Expirée → Renouvelée : interdit (art. 91).
        self.assertIsNotNone(est_explicitement_interdite(
            StatutInscription.EXPIREE, StatutInscription.RENOUVELEE,
        ))

    def test_matrice_et_interdictions_disjointes(self):
        """Une transition autorisée ne peut pas figurer en interdiction."""
        tuples_autorises = {(t.depuis, t.vers) for t in TRANSITIONS}
        tuples_interdits = {(d, v) for d, v, _ in INTERDICTIONS_EXPLICITES}
        self.assertEqual(tuples_autorises & tuples_interdits, set())

    def test_transition_inconnue_leve_erreur(self):
        with self.assertRaises(LookupError):
            transition_requise(
                StatutInscription.INSCRITE,
                StatutInscription.RECUE,
                "evenement_inexistant",
            )


class ApplicationTransitionsTests(TestCase):
    """Effet de ``appliquer_transition`` et historisation."""

    def test_transition_interdite_leve_exception(self):
        with self.assertRaises(TransitionInterdite):
            appliquer_transition(
                numero_inscription="000001-20261021120000",
                statut_actuel=StatutInscription.RADIEE,
                statut_cible=StatutInscription.INSCRITE,
                evenement="retour_arriere",
                acteur=None,
            )

    def test_transition_autorisee_enregistre_historique(self):
        from apps.workflow.models import TransitionStatut

        resultat = appliquer_transition(
            numero_inscription="000002-20261021120000",
            statut_actuel=StatutInscription.RECUE,
            statut_cible=StatutInscription.EN_CONTROLE_FORME,
            evenement="prise_en_charge",
            acteur=None,
        )
        self.assertEqual(resultat.transition.evenement, "prise_en_charge")
        self.assertTrue(
            TransitionStatut.objects.filter(
                numero_inscription="000002-20261021120000",
                statut_apres=StatutInscription.EN_CONTROLE_FORME,
            ).exists()
        )

    def test_historique_immuable(self):
        """§ 4.3 + art. 79 — pas de modification ni suppression d'historique."""
        from apps.workflow.models import TransitionStatut

        resultat = appliquer_transition(
            numero_inscription="000003-20261021120000",
            statut_actuel=StatutInscription.RECUE,
            statut_cible=StatutInscription.EN_CONTROLE_FORME,
            evenement="prise_en_charge",
            acteur=None,
        )
        trace: TransitionStatut = resultat.trace

        with self.assertRaises(PermissionError):
            trace.motif = "altération"
            trace.save()

        with self.assertRaises(PermissionError):
            trace.delete()
