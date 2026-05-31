"""
Tests du workflow Demande ⇄ Inscription (directive MO 2026-05-31).

Couvre :
  1. Cycle nominal : creer_demande → retourner → resoumettre → valider.
  2. Observation FR/AR obligatoire (rejet si l'une est vide).
  3. Séparation stricte : un agent de saisie ne peut pas retourner sa
     propre demande.
  4. Resoumission réservée au déclarant initial.
  5. Verrou : une demande RETOURNEE ne peut pas être validée directement.
  6. Historique : plusieurs cycles retour/resoumission conservés.
"""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from apps.core.enums import CanalSaisie, NaturesDroitInscrit
from apps.core.exceptions import RejetForme
from apps.inscriptions.models import Inscription, ObservationRetour
from apps.inscriptions.services import (
    DonneesDemandeInscription,
    creer_demande,
    resoumettre_demande,
    retourner_demande,
    valider_inscription,
)
from apps.utilisateurs.habilitations import AutorisationRefusee
from apps.workflow.statuts import StatutInscription
from tests import helpers


class WorkflowRetourResoumissionTests(TestCase):
    """Workflow Greffier ⇄ Déclarant — retour avec observation et resoumission."""

    def setUp(self):
        self.agent = helpers.creer_agent_saisie("agent_retour")
        self.greffier = helpers.creer_greffier("greffier_retour")

    def _deposer(self):
        return creer_demande(
            donnees=DonneesDemandeInscription(
                canal_saisie=CanalSaisie.GUICHET_PAPIER,
                nature_droit=NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                somme_garantie=Decimal("1000000.00"),
                monnaie="MRU",
                duree_en_jours=365,
            ),
            acteur=self.agent,
        )

    def test_cycle_nominal_retour_resoumission_validation(self):
        """Une demande peut être retournée, corrigée, resoumise et validée."""
        ins = self._deposer()
        self.assertEqual(ins.statut, StatutInscription.EN_CONTROLE_FORME)

        # 1) Retour avec observation obligatoire FR + AR
        obs = retourner_demande(
            inscription=ins,
            observation_fr="Pièce manquante : contrat de vente.",
            observation_ar="وثيقة ناقصة: عقد البيع.",
            acteur=self.greffier,
        )
        ins.refresh_from_db()
        self.assertEqual(ins.statut, StatutInscription.RETOURNEE)
        self.assertIsNone(obs.instant_resoumission)
        self.assertEqual(obs.cree_par_id, self.greffier.pk)

        # 2) Resoumission par le déclarant
        ins = resoumettre_demande(inscription=ins, acteur=self.agent)
        self.assertEqual(ins.statut, StatutInscription.EN_CONTROLE_FORME)
        obs.refresh_from_db()
        self.assertIsNotNone(obs.instant_resoumission)
        self.assertEqual(obs.resoumis_par_id, self.agent.pk)

        # 3) Validation finale par le greffier
        ins = valider_inscription(inscription=ins, acteur=self.greffier)
        self.assertEqual(ins.statut, StatutInscription.INSCRITE)
        self.assertIsNotNone(ins.numero_ordre)

    def test_observation_fr_ar_obligatoires(self):
        """Une observation vide en FR ou AR est refusée."""
        ins = self._deposer()
        with self.assertRaises(RejetForme):
            retourner_demande(
                inscription=ins,
                observation_fr="",
                observation_ar="ملاحظة عربية فقط.",
                acteur=self.greffier,
            )
        with self.assertRaises(RejetForme):
            retourner_demande(
                inscription=ins,
                observation_fr="Observation française seulement.",
                observation_ar="   ",
                acteur=self.greffier,
            )
        ins.refresh_from_db()
        self.assertEqual(ins.statut, StatutInscription.EN_CONTROLE_FORME)

    def test_separation_stricte_retour(self):
        """L'agent qui a saisi la demande ne peut pas la retourner lui-même."""
        ins = self._deposer()
        # Tentative de retour par l'agent (créateur) : refusé.
        with self.assertRaises(AutorisationRefusee):
            retourner_demande(
                inscription=ins,
                observation_fr="Observation FR",
                observation_ar="ملاحظة عربية",
                acteur=self.agent,
            )

    def test_resoumission_reservee_au_declarant_initial(self):
        """Seul le créateur initial peut resoumettre la demande retournée."""
        ins = self._deposer()
        retourner_demande(
            inscription=ins,
            observation_fr="À corriger.",
            observation_ar="للتصحيح.",
            acteur=self.greffier,
        )
        autre_agent = helpers.creer_agent_saisie("autre_agent")
        with self.assertRaises(AutorisationRefusee):
            resoumettre_demande(inscription=ins, acteur=autre_agent)

    def test_validation_directe_dune_retournee_interdite(self):
        """Une demande RETOURNEE ne peut pas être validée sans passer par
        EN_CONTROLE_FORME (verrou workflow)."""
        ins = self._deposer()
        retourner_demande(
            inscription=ins,
            observation_fr="À corriger.",
            observation_ar="للتصحيح.",
            acteur=self.greffier,
        )
        ins.refresh_from_db()
        self.assertEqual(ins.statut, StatutInscription.RETOURNEE)
        with self.assertRaises(RejetForme):
            valider_inscription(inscription=ins, acteur=self.greffier)

    def test_cycles_multiples_historises(self):
        """Plusieurs retours/resoumissions conservent un historique complet."""
        ins = self._deposer()
        # 1er cycle
        retourner_demande(
            inscription=ins,
            observation_fr="Cycle 1 — FR",
            observation_ar="الدورة 1 — AR",
            acteur=self.greffier,
        )
        ins.refresh_from_db()
        resoumettre_demande(inscription=ins, acteur=self.agent)
        # 2e cycle
        ins.refresh_from_db()
        retourner_demande(
            inscription=ins,
            observation_fr="Cycle 2 — FR",
            observation_ar="الدورة 2 — AR",
            acteur=self.greffier,
        )
        ins.refresh_from_db()
        resoumettre_demande(inscription=ins, acteur=self.agent)

        observations = list(
            ObservationRetour.objects
            .filter(inscription=ins)
            .order_by("cree_le")
        )
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0].observation_fr, "Cycle 1 — FR")
        self.assertEqual(observations[1].observation_fr, "Cycle 2 — FR")
        # Toutes les observations sont marquées résolues.
        for obs in observations:
            self.assertIsNotNone(obs.instant_resoumission)
            self.assertEqual(obs.resoumis_par_id, self.agent.pk)

    def test_observation_immuable_apres_creation(self):
        """Une observation ne peut être modifiée après création."""
        ins = self._deposer()
        obs = retourner_demande(
            inscription=ins,
            observation_fr="Original FR",
            observation_ar="الأصلي AR",
            acteur=self.greffier,
        )
        obs.observation_fr = "Modifié"
        with self.assertRaises(PermissionError):
            obs.save()
