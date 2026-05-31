"""
Robustesse transactionnelle du service appliquer_modification.

Principe : en cas de défaillance en cours d'application, aucun
changement partiel ne doit subsister (§ 4.3, art. 79).

Vérifications :
- défaillance après snapshot AVANT mais avant contrôle état final →
  rollback du savepoint : pas de snapshot orphelin, pas de désactivation,
  inscription inchangée ;
- défaillance après snapshot APRÈS (hypothétique — simulée par patching
  de la transition) → rollback : inscription dans l'état antérieur,
  demande non marquée APPLIQUEE ;
- consistance du journal d'audit : la trace ``modification.appliquer``
  n'apparaît QUE si l'application a abouti.

Les défaillances sont simulées via ``unittest.mock.patch`` sur des
points ciblés du service.
"""
from __future__ import annotations

from unittest import mock

from django.test import TestCase

from apps.audit.models import EntreeAudit
from apps.biens.models import BienGreve
from apps.inscriptions.models import RoleInscriptionPartie
from apps.modifications.models import (
    SnapshotInscription,
    StatutDemandeModification,
)
from apps.modifications.services import appliquer_modification
from apps.workflow.statuts import StatutInscription

from tests import helpers


class DefaillanceApresSnapshotAvantTests(TestCase):
    """
    Défaillance injectée APRÈS le snapshot AVANT mais avant le contrôle
    d'état final. Le rollback doit annuler le snapshot AVANT.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_rollback_complet_si_defaillance_au_milieu(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"somme_garantie": "2000000.00"}},
            acteur=self.agent,
        )
        # On remplace ``_appliquer_scalaires`` par une fonction qui
        # lève — ce qui déclenche une remontée d'exception AVANT le
        # contrôle d'état final.
        chemin = "apps.modifications.services._appliquer_scalaires"
        with mock.patch(chemin, side_effect=RuntimeError("panne simulée")):
            with self.assertRaises(RuntimeError):
                appliquer_modification(demande=demande, acteur=self.greffier)

        # Aucun snapshot associé à la demande : le savepoint a rollback.
        self.assertEqual(
            SnapshotInscription.objects.filter(
                demande_modification=demande,
            ).count(),
            0,
        )
        # La demande n'est ni APPLIQUEE ni REJETEE (défaillance technique,
        # non un refus métier) : elle reste RECUE pour que le greffier
        # puisse re-tenter ou diagnostiquer.
        demande.refresh_from_db()
        self.assertEqual(demande.statut, StatutDemandeModification.RECUE)
        # L'inscription reste INSCRITE.
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.INSCRITE)

    def test_rollback_n_a_pas_laisse_de_role_desactive(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "parties": {
                    "retirer": [self.peuple["lien_debiteur"].pk],
                },
                "scalaires": {"somme_garantie": "2000000.00"},
            },
            acteur=self.agent,
        )
        chemin = "apps.modifications.services._appliquer_scalaires"
        with mock.patch(chemin, side_effect=RuntimeError("panne")):
            with self.assertRaises(RuntimeError):
                appliquer_modification(demande=demande, acteur=self.greffier)

        # Le débiteur n'a PAS été désactivé (rollback du savepoint).
        lien = RoleInscriptionPartie.objects.get(
            pk=self.peuple["lien_debiteur"].pk,
        )
        self.assertTrue(lien.actif)
        self.assertIsNone(lien.date_fin_validite)

    def test_aucune_trace_modification_appliquer_si_echec(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"monnaie": "MRU"}},
            acteur=self.agent,
        )
        chemin = "apps.modifications.services._appliquer_scalaires"
        with mock.patch(chemin, side_effect=RuntimeError("panne")):
            with self.assertRaises(RuntimeError):
                appliquer_modification(demande=demande, acteur=self.greffier)

        self.assertFalse(
            EntreeAudit.objects.filter(
                action_cle="modification.appliquer",
                objet_reference=self.inscription.numero_ordre,
            ).exists(),
            "L'audit `modification.appliquer` ne doit être écrit "
            "que lorsque l'application a abouti.",
        )


class DefaillanceApresControleEtatFinalTests(TestCase):
    """
    Défaillance injectée APRÈS le contrôle d'état final réussi mais
    AVANT la transition de statut. Le rollback doit annuler les
    mutations et les snapshots.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_rollback_si_transition_echoue(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"monnaie": "MRU"}},
            acteur=self.agent,
        )
        chemin = "apps.modifications.services.appliquer_transition"
        with mock.patch(chemin, side_effect=RuntimeError("panne transition")):
            with self.assertRaises(RuntimeError):
                appliquer_modification(demande=demande, acteur=self.greffier)

        # Aucun snapshot, statut inchangé.
        self.assertEqual(
            SnapshotInscription.objects.filter(
                demande_modification=demande,
            ).count(),
            0,
        )
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.INSCRITE)
