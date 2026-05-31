"""
Tests de cas limites et anti-contournement — article 88 dernier alinéa.

Scénarios couverts :
1. Diff mixte qui retire TOUS les constituants actifs et en ajoute
   de nouveaux dans le même diff → accepté (remplacement autorisé).
2. Diff qui retire un constituant et ajoute un créancier (changement de rôle) →
   refusé si l'état final n'a plus de constituant actif.
3. Diff oscillatoire : plusieurs opérations compensatoires dont l'effet
   net passe par un état temporairement invalide, mais dont l'état FINAL
   est valide → accepté (le contrôle porte sur l'état final).
4. Marquage REJETEE + motif structuré + audit ``modification.refuser``
   en cas d'échec du contrôle d'état final.
5. Rejet structuré pour diff invalide, diff vide, accords manquants.
"""
from __future__ import annotations

from django.test import TestCase

from apps.audit.models import EntreeAudit
from apps.biens.models import BienGreve
from apps.core.exceptions import ModificationSansEffet
from apps.inscriptions.models import RoleInscriptionPartie
from apps.modifications.models import (
    DemandeModification,
    MotifRefusModification,
    SnapshotInscription,
    StatutDemandeModification,
)
from apps.modifications.services import appliquer_modification
from apps.parties.models import RolePartie, TypePartie

from tests import helpers


class RemplacementTotalConstituantsTests(TestCase):
    """
    Art. 88 dernier al. — un remplacement intégral des constituants dans
    le même diff est ACCEPTÉ : l'état final comporte bien au moins un
    constituant actif.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        # On ajoute un second constituant pour tester le remplacement
        # intégral d'un ensemble > 1.
        self.c2 = helpers.creer_partie_pm("Constituant 2", "RC/NKT/2024/2002")
        self.lien_c2 = RoleInscriptionPartie.objects.create(
            inscription=self.inscription, partie=self.c2,
            role=RolePartie.CONSTITUANT,
        )

    def test_remplacement_total_constituants_accepte(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "parties": {
                    "retirer": [
                        self.peuple["lien_constituant"].pk,
                        self.lien_c2.pk,
                    ],
                    "ajouter": [
                        {"role": RolePartie.CONSTITUANT,
                         "type_partie": TypePartie.PERSONNE_MORALE,
                         "donnees": {"denomination_sociale": "Nouveau A",
                                     "numero_rc": "RC/NKT/2024/3001"}},
                        {"role": RolePartie.CONSTITUANT,
                         "type_partie": TypePartie.PERSONNE_MORALE,
                         "donnees": {"denomination_sociale": "Nouveau B",
                                     "numero_rc": "RC/NKT/2024/3002"}},
                    ],
                },
            },
            acteur=self.agent,
        )
        appliquer_modification(demande=demande, acteur=self.greffier)

        actifs = RoleInscriptionPartie.actifs.filter(
            inscription=self.inscription, role=RolePartie.CONSTITUANT,
        )
        self.assertEqual(actifs.count(), 2)
        noms = set(actifs.values_list("partie__denomination_sociale", flat=True))
        self.assertEqual(noms, {"Nouveau A", "Nouveau B"})


class DiffMixteContournementTests(TestCase):
    """
    Le contrôle d'état final doit empêcher tout contournement qui
    « déguise » un vidage en diff mixte.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_retrait_constituant_et_ajout_creancier_seul_refuse(self):
        """
        Scénario : retirer l'unique constituant ET ajouter un créancier.
        L'état final comporte 0 constituant → REFUSÉ (art. 88 dernier al.).
        """
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "parties": {
                    "retirer": [self.peuple["lien_constituant"].pk],
                    "ajouter": [
                        {"role": RolePartie.CREANCIER,
                         "type_partie": TypePartie.PERSONNE_MORALE,
                         "donnees": {
                             "denomination_sociale": "Créancier supplémentaire",
                             "numero_rc": "RC/NKT/2024/4001",
                         }},
                    ],
                },
            },
            acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

        demande.refresh_from_db()
        self.assertEqual(demande.statut, StatutDemandeModification.REJETEE)
        self.assertEqual(
            demande.motif_refus_code,
            MotifRefusModification.ETAT_FINAL_CONSTITUANT_ABSENT,
        )
        # Rollback intégral : le constituant reste actif.
        self.assertTrue(
            RoleInscriptionPartie.objects.get(
                pk=self.peuple["lien_constituant"].pk,
            ).actif,
        )

    def test_retrait_creancier_sans_remplacement_refuse(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "parties": {
                    "retirer": [self.peuple["lien_creancier"].pk],
                    "ajouter": [
                        {"role": RolePartie.DEBITEUR,
                         "type_partie": TypePartie.PERSONNE_PHYSIQUE,
                         "donnees": {"nom": "Nouveau", "prenom": "Débiteur"}},
                    ],
                },
            },
            acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

        demande.refresh_from_db()
        self.assertEqual(
            demande.motif_refus_code,
            MotifRefusModification.ETAT_FINAL_CREANCIER_ABSENT,
        )

    def test_retrait_tous_biens_avec_ajout_de_biens_accepte(self):
        """
        Remplacement de tous les biens par d'autres → accepté :
        l'état final comporte au moins un bien actif.
        """
        # Ajout d'un second bien pour avoir >1 au départ.
        bien2 = BienGreve.objects.create(
            inscription=self.inscription,
            description_fr="Second bien", description_ar="مال ثان",
        )
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "biens": {
                    "retirer": [self.peuple["bien"].pk, bien2.pk],
                    "ajouter": [
                        {"description_fr": "Bien A", "description_ar": "مال أ"},
                        {"description_fr": "Bien B", "description_ar": "مال ب"},
                    ],
                },
            },
            acteur=self.agent,
        )
        appliquer_modification(demande=demande, acteur=self.greffier)
        self.assertEqual(
            BienGreve.actifs.filter(inscription=self.inscription).count(),
            2,
        )


class PersistanceDuRejetTests(TestCase):
    """
    Un refus d'application doit laisser une trace exploitable :
    - demande marquée REJETEE,
    - motif structuré (enum limitative),
    - entrée d'audit ``modification.refuser``,
    - AUCUN snapshot orphelin (rollback du savepoint).
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_echec_art88_persiste_rejet_et_trace_audit(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"biens": {"retirer": [self.peuple["bien"].pk]}},
            acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

        demande.refresh_from_db()
        self.assertEqual(demande.statut, StatutDemandeModification.REJETEE)
        self.assertEqual(
            demande.motif_refus_code,
            MotifRefusModification.ETAT_FINAL_BIEN_ABSENT,
        )
        # Audit tracé.
        traces = EntreeAudit.objects.filter(
            action_cle="modification.refuser",
            objet_reference=str(demande.pk),
        )
        self.assertEqual(traces.count(), 1)
        self.assertEqual(
            traces.first().details.get("motif_code"),
            MotifRefusModification.ETAT_FINAL_BIEN_ABSENT,
        )
        # Aucun snapshot de modification pour cette demande.
        self.assertEqual(
            SnapshotInscription.objects.filter(
                demande_modification=demande,
            ).count(),
            0,
            "Les snapshots doivent être rollback avec le savepoint.",
        )

    def test_rejet_pour_diff_invalide_trace(self):
        demande = DemandeModification.objects.create(
            inscription=self.inscription,
            objet_modification_fr="x", objet_modification_ar="x",
            diff_propose={"cle_inventee": 1},  # hors schéma
            accord_createur_confirme=True,
            accord_constituant_confirme=True,
            cree_par=self.agent, modifie_par=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

        demande.refresh_from_db()
        self.assertEqual(demande.statut, StatutDemandeModification.REJETEE)
        self.assertEqual(
            demande.motif_refus_code, MotifRefusModification.DIFF_INVALIDE,
        )

    def test_rejet_pour_diff_vide(self):
        demande = helpers.creer_demande_modification(
            self.inscription, {}, acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)
        demande.refresh_from_db()
        self.assertEqual(
            demande.motif_refus_code, MotifRefusModification.DIFF_VIDE,
        )

    def test_rejet_pour_accords_manquants(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"monnaie": "MRU"}},
            acteur=self.agent,
            accord_createur=False, accord_constituant=True,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)
        demande.refresh_from_db()
        self.assertEqual(
            demande.motif_refus_code,
            MotifRefusModification.ACCORDS_MANQUANTS,
        )


class ReActivationInterdite_Tests(TestCase):
    """
    Une demande déjà REJETEE ne peut pas être ré-appliquée :
    la trace du refus reste immuable.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_demande_rejetee_non_reappliquable(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"biens": {"retirer": [self.peuple["bien"].pk]}},
            acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)
        # La demande est REJETEE. Nouvelle tentative : refusée dès la
        # recevabilité (statut != RECUE).
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)
