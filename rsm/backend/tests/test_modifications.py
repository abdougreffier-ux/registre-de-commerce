"""
Tests dédiés au service ``appliquer_modification`` — articles 88, 90, 93.

Invariants couverts :
- contrôle d'état final (art. 88 dernier alinéa) sur ≥ 1 constituant /
  ≥ 1 créancier / ≥ 1 bien ;
- impossibilité de contournement par modifications successives ;
- conservation intégrale de l'historique (art. 79) — aucune suppression
  physique, snapshots avant/après conservés ;
- schéma strict du diff — rejet de toute clé hors périmètre art. 88 ;
- interdiction de toucher à la durée (art. 90 al. 2) ou au numéro
  d'ordre (art. 78) via une modification.
"""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from apps.biens.models import BienGreve
from apps.core.exceptions import ModificationSansEffet
from apps.inscriptions.models import Inscription, RoleInscriptionPartie
from apps.modifications.diff import DiffModification
from apps.modifications.models import (
    SnapshotInscription,
    StatutDemandeModification,
)
from apps.modifications.services import appliquer_modification
from apps.parties.models import RolePartie, TypePartie
from apps.workflow.statuts import StatutInscription

from tests import helpers


# --------------------------------------------------------------------------- #
# Schéma strict du diff                                                        #
# --------------------------------------------------------------------------- #
class SchemaDiffStrictTests(TestCase):
    def test_cles_racine_hors_schema_refusees(self):
        with self.assertRaises(ValueError):
            DiffModification.depuis_dict({"inconnu": 1})

    def test_champs_jamais_modifiables_refuses(self):
        for champ in ("duree_en_jours", "date_expiration", "numero_ordre",
                      "instant_saisie_opposable", "statut"):
            with self.assertRaises(ValueError):
                DiffModification.depuis_dict({"scalaires": {champ: "x"}})

    def test_nature_droit_hors_liste_refusee(self):
        with self.assertRaises(ValueError):
            DiffModification.depuis_dict({
                "scalaires": {"nature_droit": "nant_inexistant"},
            })

    def test_somme_garantie_negative_refusee(self):
        with self.assertRaises(ValueError):
            DiffModification.depuis_dict({
                "scalaires": {"somme_garantie": "-1"},
            })

    def test_diff_scalaires_valides_accepte(self):
        diff = DiffModification.depuis_dict({
            "scalaires": {
                "somme_garantie": "1500000.00",
                "monnaie": "MRU",
                "adresse_electronique_notifications": "test@exemple.mr",
            },
        })
        self.assertFalse(diff.est_vide)


# --------------------------------------------------------------------------- #
# Application d'une modification valide                                        #
# --------------------------------------------------------------------------- #
class AppliquerModificationTests(TestCase):
    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_modification_scalaires_simples_acceptee(self):
        """Montant et adresse e-mail modifiables (art. 88)."""
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"somme_garantie": "2000000.00", "monnaie": "MRU"}},
            acteur=self.agent,
        )
        resultat = appliquer_modification(demande=demande, acteur=self.greffier)

        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.somme_garantie, Decimal("2000000.00"))
        self.assertEqual(self.inscription.statut, StatutInscription.MODIFIEE)
        self.assertIsNotNone(resultat.snapshot_avant)
        self.assertIsNotNone(resultat.snapshot_apres)

    def test_ajout_bien_accepte(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "biens": {
                    "ajouter": [
                        {"description_fr": "Matériel additionnel",
                         "description_ar": "معدات إضافية",
                         "numero_serie": "SN-002"},
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

    def test_remplacement_bien_sans_coupure(self):
        """
        Art. 88 — retrait du bien existant ET ajout d'un nouveau dans le
        même diff : accepté (l'état final reste valide).
        """
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "biens": {
                    "retirer": [self.peuple["bien"].pk],
                    "ajouter": [
                        {"description_fr": "Nouveau bien",
                         "description_ar": "مال جديد"},
                    ],
                },
            },
            acteur=self.agent,
        )
        appliquer_modification(demande=demande, acteur=self.greffier)

        # Le bien initial reste en base mais désactivé.
        bien_originel = BienGreve.objects.get(pk=self.peuple["bien"].pk)
        self.assertFalse(bien_originel.actif)
        self.assertIsNotNone(bien_originel.date_fin_validite)
        # Un bien actif le remplace.
        self.assertEqual(
            BienGreve.actifs.filter(inscription=self.inscription).count(), 1
        )


# --------------------------------------------------------------------------- #
# Art. 88 dernier alinéa — contrôle d'ÉTAT FINAL                               #
# --------------------------------------------------------------------------- #
class ControleEtatFinalTests(TestCase):
    """
    L'état après application doit respecter :
    - ≥ 1 constituant actif, ≥ 1 créancier actif, ≥ 1 bien actif.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_retrait_du_dernier_constituant_refuse(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"parties": {"retirer": [self.peuple["lien_constituant"].pk]}},
            acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

        # Rollback total : le constituant reste actif, aucun snapshot
        # résiduel, statut inchangé.
        self.assertTrue(
            RoleInscriptionPartie.objects.get(
                pk=self.peuple["lien_constituant"].pk,
            ).actif,
        )
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.INSCRITE)
        self.assertEqual(
            SnapshotInscription.objects.filter(
                inscription=self.inscription,
                evenement=SnapshotInscription.Evenement.MODIFICATION_AVANT,
            ).count(),
            0,
            "Aucun snapshot ne doit subsister après rollback.",
        )

    def test_retrait_du_dernier_creancier_refuse(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"parties": {"retirer": [self.peuple["lien_creancier"].pk]}},
            acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

    def test_retrait_du_dernier_bien_refuse(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"biens": {"retirer": [self.peuple["bien"].pk]}},
            acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

    def test_remplacement_constituant_par_un_nouveau_accepte(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "parties": {
                    "retirer": [self.peuple["lien_constituant"].pk],
                    "ajouter": [{
                        "role": RolePartie.CONSTITUANT,
                        "type_partie": TypePartie.PERSONNE_MORALE,
                        "donnees": {
                            "denomination_sociale": "Nouveau Constituant SA",
                            "numero_rc": "RC/NKT/2024/9999",
                        },
                    }],
                },
            },
            acteur=self.agent,
        )
        appliquer_modification(demande=demande, acteur=self.greffier)
        actifs = RoleInscriptionPartie.actifs.filter(
            inscription=self.inscription, role=RolePartie.CONSTITUANT,
        )
        self.assertEqual(actifs.count(), 1)
        self.assertEqual(
            actifs.first().partie.denomination_sociale,
            "Nouveau Constituant SA",
        )


# --------------------------------------------------------------------------- #
# Contournement par modifications successives                                  #
# --------------------------------------------------------------------------- #
class AntiContournementParSuccessionTests(TestCase):
    """
    Scénario : trois constituants → retirer un à un → au moment où il
    n'en reste qu'UN et où on tente de le retirer, l'état final invalide
    provoque le rollback. Aucun chemin n'amène l'inscription à 0 constituant.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        # Ajout de deux constituants supplémentaires (on passe de 1 à 3).
        self.c2 = helpers.creer_partie_pm("Constituant 2", "RC/NKT/2024/2002")
        self.c3 = helpers.creer_partie_pm("Constituant 3", "RC/NKT/2024/2003")
        self.lien_c2 = RoleInscriptionPartie.objects.create(
            inscription=self.inscription, partie=self.c2,
            role=RolePartie.CONSTITUANT,
        )
        self.lien_c3 = RoleInscriptionPartie.objects.create(
            inscription=self.inscription, partie=self.c3,
            role=RolePartie.CONSTITUANT,
        )

    def _retirer(self, lien_id: int):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"parties": {"retirer": [lien_id]}},
            acteur=self.agent,
        )
        return appliquer_modification(demande=demande, acteur=self.greffier)

    def test_impossibilite_contournement_par_retraits_successifs(self):
        # Mod 1 : 3 → 2 constituants. Valide.
        self._retirer(self.peuple["lien_constituant"].pk)
        self.assertEqual(
            RoleInscriptionPartie.actifs.filter(
                inscription=self.inscription, role=RolePartie.CONSTITUANT,
            ).count(),
            2,
        )

        # Mod 2 : 2 → 1 constituant. Valide.
        self._retirer(self.lien_c2.pk)
        self.assertEqual(
            RoleInscriptionPartie.actifs.filter(
                inscription=self.inscription, role=RolePartie.CONSTITUANT,
            ).count(),
            1,
        )

        # Mod 3 : tentative de passer à 0. Refusée → rollback complet.
        with self.assertRaises(ModificationSansEffet):
            self._retirer(self.lien_c3.pk)

        # L'état final reste à 1 constituant actif : aucun contournement.
        self.assertEqual(
            RoleInscriptionPartie.actifs.filter(
                inscription=self.inscription, role=RolePartie.CONSTITUANT,
            ).count(),
            1,
        )


# --------------------------------------------------------------------------- #
# Conservation intégrale de l'historique (art. 79)                             #
# --------------------------------------------------------------------------- #
class ConservationIntegraleTests(TestCase):
    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_suppression_physique_interdite_sur_bien(self):
        with self.assertRaises(PermissionError):
            self.peuple["bien"].delete()

    def test_suppression_physique_interdite_sur_role(self):
        with self.assertRaises(PermissionError):
            self.peuple["lien_debiteur"].delete()

    def test_suppression_physique_interdite_sur_snapshot(self):
        # Créer un snapshot via une modification valide.
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"monnaie": "MRU"}},
            acteur=self.agent,
        )
        resultat = appliquer_modification(demande=demande, acteur=self.greffier)
        with self.assertRaises(PermissionError):
            resultat.snapshot_avant.delete()

    def test_element_desactive_reste_consultable(self):
        bien_id = self.peuple["bien"].pk
        # Remplacement → désactivation du bien initial.
        demande = helpers.creer_demande_modification(
            self.inscription,
            {
                "biens": {
                    "retirer": [bien_id],
                    "ajouter": [{"description_fr": "Bien neuf",
                                 "description_ar": "مال جديد"}],
                },
            },
            acteur=self.agent,
        )
        appliquer_modification(demande=demande, acteur=self.greffier)

        bien = BienGreve.objects.get(pk=bien_id)
        self.assertFalse(bien.actif)
        self.assertIsNotNone(bien.date_fin_validite)
        self.assertIn("modification.demande#", bien.raison_fin)

    def test_snapshots_avant_et_apres_distincts(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"somme_garantie": "1500000.00"}},
            acteur=self.agent,
        )
        resultat = appliquer_modification(demande=demande, acteur=self.greffier)
        self.assertNotEqual(
            resultat.snapshot_avant.empreinte,
            resultat.snapshot_apres.empreinte,
        )
        # Les deux snapshots sont rattachés à la même demande.
        self.assertEqual(
            resultat.snapshot_avant.demande_modification_id, demande.pk,
        )
        self.assertEqual(
            resultat.snapshot_apres.demande_modification_id, demande.pk,
        )


# --------------------------------------------------------------------------- #
# Recevabilité : statut, accords des parties, unicité d'application            #
# --------------------------------------------------------------------------- #
class RecevabiliteTests(TestCase):
    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_accords_manquants_refuses(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"monnaie": "MRU"}},
            acteur=self.agent,
            accord_createur=True, accord_constituant=False,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

    def test_application_unique(self):
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"monnaie": "MRU"}},
            acteur=self.agent,
        )
        appliquer_modification(demande=demande, acteur=self.greffier)
        # Deuxième application refusée — la demande est déjà APPLIQUEE.
        demande.refresh_from_db()
        self.assertEqual(demande.statut, StatutDemandeModification.APPLIQUEE)
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

    def test_modification_d_inscription_expiree_refusee(self):
        # Force le statut expiré.
        Inscription.objects.filter(pk=self.inscription.pk).update(
            statut=StatutInscription.EXPIREE
        )
        self.inscription.refresh_from_db()
        demande = helpers.creer_demande_modification(
            self.inscription,
            {"scalaires": {"monnaie": "MRU"}},
            acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)

    def test_diff_vide_refuse(self):
        demande = helpers.creer_demande_modification(
            self.inscription, {}, acteur=self.agent,
        )
        with self.assertRaises(ModificationSansEffet):
            appliquer_modification(demande=demande, acteur=self.greffier)
