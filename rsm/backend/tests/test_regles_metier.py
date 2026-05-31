"""
Tests des règles métier — articles 80, 85, 88 al. 4, 91, 92, 96, 97 al. 2.

Ces tests sont l'expression exécutable de la matrice de conformité L11.
Chaque assertion cite l'article dont elle garantit le respect.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.core.enums import (
    CanalSaisie,
    MotifRejet,
    NaturesDroitInscrit,
)
from apps.core.exceptions import (
    RechercheCriteresInsuffisants,
    RejetForme,
    RenouvellementHorsDelai,
)
from apps.inscriptions.models import Inscription, RoleInscriptionPartie
from apps.inscriptions.services import (
    DonneesDemandeInscription,
    creer_demande,
    prononcer_rejet,
)
from apps.parties.models import RolePartie
from apps.recherche.services import CriteresRecherche, rechercher
from apps.renouvellements.models import DemandeRenouvellement
from apps.renouvellements.services import appliquer_renouvellement
from apps.radiations.models import (
    DemandeRadiation,
    FondementRadiation,
)
from apps.radiations.services import appliquer_radiation
from apps.workflow.statuts import StatutInscription

from tests import helpers


class Article80_RejetsLimitatifsTests(TestCase):
    """Article 80 — motifs limitatifs de rejet."""

    def test_canal_invalide_est_rejete_au_depot(self):
        agent = helpers.creer_agent_saisie()
        with self.assertRaises(RejetForme):
            creer_demande(
                donnees=DonneesDemandeInscription(
                    canal_saisie="postal",  # hors liste limitative
                    nature_droit=NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                    somme_garantie=Decimal("1000"),
                    monnaie="MRU",
                    duree_en_jours=365,
                ),
                acteur=agent,
            )

    def test_motif_rejet_hors_liste_refuse(self):
        agent = helpers.creer_agent_saisie()
        greffier = helpers.creer_greffier()
        demande = helpers.deposer_demande_standard(acteur=agent)
        with self.assertRaises(RejetForme):
            prononcer_rejet(
                inscription=demande,
                motif="motif_invente",  # hors liste limitative art. 80
                acteur=greffier,
            )

    def test_rejet_motif_art80_accepte_et_trace(self):
        agent = helpers.creer_agent_saisie()
        greffier = helpers.creer_greffier()
        demande = helpers.deposer_demande_standard(acteur=agent)
        demande = prononcer_rejet(
            inscription=demande,
            motif=MotifRejet.INFORMATIONS_ILLISIBLES,
            commentaire_fr="Scanner illisible",
            commentaire_ar="الوثيقة غير مقروءة",
            acteur=greffier,
        )
        self.assertEqual(demande.statut, StatutInscription.REJETEE)
        self.assertEqual(demande.motif_rejet, MotifRejet.INFORMATIONS_ILLISIBLES)


class Article85_ContenuInscriptionTests(TestCase):
    """Article 85 — champs obligatoires, régime déclaratif (art. 86)."""

    def test_nature_droit_hors_liste_rejetee(self):
        """Art. 76 — liste LIMITATIVE des natures."""
        agent = helpers.creer_agent_saisie()
        with self.assertRaises(RejetForme):
            creer_demande(
                donnees=DonneesDemandeInscription(
                    canal_saisie=CanalSaisie.GUICHET_PAPIER,
                    nature_droit="nantissement_inexistant",
                    somme_garantie=Decimal("1"),
                    monnaie="MRU",
                    duree_en_jours=1,
                ),
                acteur=agent,
            )

    def test_demande_valide_statut_en_controle_forme(self):
        agent = helpers.creer_agent_saisie()
        demande = helpers.deposer_demande_standard(acteur=agent)
        # Le service passe automatiquement Reçue → En contrôle de forme.
        self.assertEqual(demande.statut, StatutInscription.EN_CONTROLE_FORME)

    def test_champs_bien_grevé_optionnels_non_bloquants(self):
        """
        Article 85 alinéa 3 — l'omission du numéro de série, du fabricant,
        du modèle ou de l'année ne prive pas l'inscription d'effet.
        """
        from apps.biens.models import BienGreve

        agent = helpers.creer_agent_saisie()
        inscription = helpers.deposer_demande_standard(acteur=agent)
        bien = BienGreve.objects.create(
            inscription=inscription,
            description_fr="Outillage industriel (pas de n° série disponible)",
            description_ar="معدات صناعية (لا يتوفر رقم تسلسلي)",
            # aucun champ technique renseigné — doit être accepté
        )
        self.assertIsNotNone(bien.pk)
        self.assertEqual(bien.numero_serie, "")


# Les tests relatifs à l'article 88 dernier alinéa (modification sans effet,
# contrôle d'état final, anti-contournement par modifications successives)
# sont portés par ``tests/test_modifications.py``.


class Article91_RenouvellementAvantExpirationTests(TestCase):
    """Article 91 — renouvellement possible uniquement avant expiration."""

    def test_renouvellement_apres_expiration_refuse(self):
        agent = helpers.creer_agent_saisie()
        greffier = helpers.creer_greffier()
        d = helpers.deposer_demande_standard(acteur=agent, duree_jours=1)
        inscription = helpers.valider_avec_greffier(d, greffier)
        # Force l'expiration en reculant la date.
        Inscription.objects.filter(pk=inscription.pk).update(
            date_expiration=timezone.localdate() - timedelta(days=1)
        )
        inscription.refresh_from_db()

        demande = DemandeRenouvellement.objects.create(
            inscription=inscription,
            cree_par=agent, modifie_par=agent,
        )
        with self.assertRaises(RenouvellementHorsDelai):
            appliquer_renouvellement(demande=demande, acteur=greffier)

    def test_renouvellement_proroge_de_duree_initiale(self):
        """
        Art. 91 — prorogation = durée initiale, décomptée à partir de la
        date à laquelle la période en cours aurait expiré.
        Hypothèse TDR § 9.3 : « durée initiale » = durée fixée lors de
        l'inscription initiale.
        """
        agent = helpers.creer_agent_saisie()
        greffier = helpers.creer_greffier()
        d = helpers.deposer_demande_standard(acteur=agent, duree_jours=365)
        inscription = helpers.valider_avec_greffier(d, greffier)
        ancienne = inscription.date_expiration
        demande = DemandeRenouvellement.objects.create(
            inscription=inscription, cree_par=agent, modifie_par=agent,
        )
        appliquer_renouvellement(demande=demande, acteur=greffier)
        demande.refresh_from_db()
        self.assertEqual(demande.ancienne_date_expiration, ancienne)
        self.assertEqual(
            demande.nouvelle_date_expiration,
            ancienne + timedelta(days=365),
        )


class Article92_RadiationTests(TestCase):
    """Article 92 — mention « radiée » au fichier public jusqu'à expiration."""

    def test_radiation_active_mention_et_statut(self):
        agent = helpers.creer_agent_saisie()
        greffier = helpers.creer_greffier()
        d = helpers.deposer_demande_standard(acteur=agent)
        inscription = helpers.valider_avec_greffier(d, greffier)

        demande = DemandeRadiation.objects.create(
            inscription=inscription,
            fondement=FondementRadiation.CONSENTEMENT,
            cree_par=agent, modifie_par=agent,
        )
        appliquer_radiation(demande=demande, acteur=greffier)
        inscription.refresh_from_db()
        self.assertTrue(inscription.mention_radiee)
        self.assertEqual(inscription.statut, StatutInscription.RADIEE)


class Article96_DeuxCriteresMinimumTests(TestCase):
    """Article 96 — recherche à au moins deux critères parmi quatre."""

    def test_recherche_un_seul_critere_refusee(self):
        with self.assertRaises(RechercheCriteresInsuffisants):
            rechercher(CriteresRecherche(nom_constituant="Ould"))

    def test_recherche_deux_criteres_acceptee(self):
        resultat = rechercher(CriteresRecherche(
            nom_constituant="Ould", numero_rc="RC/NKT/2024/0001",
        ))
        self.assertGreaterEqual(len(resultat.criteres_utilises), 2)
        self.assertEqual(resultat.nombre_resultats, len(resultat.inscriptions))
        self.assertEqual(len(resultat.inscriptions), 0)

    def test_recherche_critere_hors_liste_ignore(self):
        """Seuls les 4 critères limitatifs de l'art. 96 sont exploités."""
        # Le service n'expose aucun paramètre hors liste — garanti par la
        # dataclass ``CriteresRecherche``. On ne peut pas soumettre autre chose.
        self.assertFalse(hasattr(CriteresRecherche, "nom_creancier"))


class Article97_HomonymesTests(TestCase):
    """Article 97 alinéa 2 — résultat exhaustif des homonymes."""

    def test_homonymes_inclus_quand_recherche_par_nom(self):
        agent = helpers.creer_agent_saisie()
        greffier = helpers.creer_greffier()
        inscription = helpers.valider_avec_greffier(
            helpers.deposer_demande_standard(acteur=agent), greffier,
        )
        homonyme1 = helpers.creer_partie_pp(nom="DUPONT", prenom="Pierre")
        homonyme2 = helpers.creer_partie_pp(nom="DUPONT", prenom="Paul")
        RoleInscriptionPartie.objects.create(
            inscription=inscription, partie=homonyme1, role=RolePartie.CONSTITUANT,
        )
        RoleInscriptionPartie.objects.create(
            inscription=inscription, partie=homonyme2, role=RolePartie.CONSTITUANT,
        )
        # Recherche par nom + numéro d'inscription (2 critères minimum).
        resultat = rechercher(CriteresRecherche(
            nom_constituant="DUPONT",
            numero_inscription=inscription.numero_ordre,
        ))
        self.assertEqual(len(resultat.inscriptions), 1)
        homonymes = resultat.homonymes_par_inscription.get(inscription.pk, [])
        noms = {h["prenom"] for h in homonymes}
        self.assertEqual(noms, {"Pierre", "Paul"})
