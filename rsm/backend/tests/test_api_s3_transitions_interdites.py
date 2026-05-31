"""
Scénario S3 — Transitions explicitement interdites (§ 4.3 du TDR).

Trois interdictions formellement décrites par le TDR :
1. Pas de retour d'une inscription RADIÉE vers INSCRITE.
2. Pas de modification d'une inscription EXPIRÉE (art. 90).
3. Pas de renouvellement après expiration (art. 91).
4. Pas de retour du fichier général vers le fichier public.

Les tests vérifient que ces interdictions sont respectées au niveau API
et que l'état avant/après n'est pas altéré.
"""
from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.biens.models import BienGreve
from apps.inscriptions.models import Inscription, RoleInscriptionPartie
from apps.workflow.statuts import StatutInscription

from tests import helpers


class S3_TransitionsInterdites_API_Tests(TestCase):
    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier(duree_jours=365)
        )
        self.client_agent = APIClient()
        self.client_agent.force_authenticate(self.agent)
        self.client_greffier = APIClient()
        self.client_greffier.force_authenticate(self.greffier)

    # --------------------------------------------------------------------- #
    # Interdiction 1 — modification d'une inscription EXPIRÉE                #
    # --------------------------------------------------------------------- #
    def test_modification_d_inscription_expiree_refusee(self):
        Inscription.objects.filter(pk=self.inscription.pk).update(
            statut=StatutInscription.EXPIREE,
        )
        rep = self.client_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "Tentative sur inscription expirée",
                "objet_modification_ar": "محاولة على تسجيل منتهي",
                "diff_propose": {"scalaires": {"monnaie": "MRU"}},
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED)
        id_mod = rep.data["id"]
        # L'application doit être refusée.
        rep_applique = self.client_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/",
            format="json",
        )
        self.assertEqual(rep_applique.status_code, status.HTTP_400_BAD_REQUEST)

        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.EXPIREE)

    # --------------------------------------------------------------------- #
    # Interdiction 2 — renouvellement après expiration                       #
    # --------------------------------------------------------------------- #
    def test_renouvellement_apres_expiration_refuse(self):
        # On recule la date d'expiration.
        Inscription.objects.filter(pk=self.inscription.pk).update(
            date_expiration=timezone.localdate() - timedelta(days=1),
        )
        rep = self.client_agent.post(
            "/api/v1/renouvellements/",
            data={"inscription": self.inscription.pk},
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_201_CREATED)
        id_renouv = rep.data["id"]
        rep_applique = self.client_greffier.post(
            f"/api/v1/renouvellements/{id_renouv}/appliquer/",
            format="json",
        )
        self.assertEqual(rep_applique.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rep_applique.data.get("article"), "91")

    # --------------------------------------------------------------------- #
    # Interdiction 3 — pas de retour d'une radiation vers une inscription    #
    # --------------------------------------------------------------------- #
    def test_radiation_puis_modification_refusee(self):
        # On radie.
        rep_rad = self.client_agent.post(
            "/api/v1/radiations/",
            data={
                "inscription": self.inscription.pk,
                "fondement": "consentement",
            },
            format="json",
        )
        id_rad = rep_rad.data["id"]
        self.client_greffier.post(
            f"/api/v1/radiations/{id_rad}/appliquer/", format="json",
        )
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.RADIEE)

        # Tentative de modification après radiation → refusée, car le
        # statut RADIEE n'est pas dans STATUTS_EN_COURS_DE_VALIDITE.
        rep = self.client_agent.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "Tentative après radiation",
                "objet_modification_ar": "محاولة بعد الشطب",
                "diff_propose": {"scalaires": {"monnaie": "MRU"}},
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        id_mod = rep.data["id"]
        rep_applique = self.client_greffier.post(
            f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
        )
        self.assertEqual(rep_applique.status_code, status.HTTP_400_BAD_REQUEST)
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.RADIEE)

    # --------------------------------------------------------------------- #
    # Interdiction 4 — pas de modification de la durée via une modification  #
    # --------------------------------------------------------------------- #
    def test_modification_durée_ou_date_expiration_refusee(self):
        """
        Art. 90 al. 2 — la modification n'a aucun effet sur la durée de
        l'inscription initiale sauf prorogation expresse (renouvellement).
        Le schéma strict du diff exclut ces champs.
        """
        for champ_interdit in ("duree_en_jours", "date_expiration"):
            rep = self.client_agent.post(
                "/api/v1/modifications/",
                data={
                    "inscription": self.inscription.pk,
                    "objet_modification_fr": f"Tentative sur {champ_interdit}",
                    "objet_modification_ar": f"محاولة على {champ_interdit}",
                    "diff_propose": {"scalaires": {champ_interdit: 999}},
                    "accord_createur_confirme": True,
                    "accord_constituant_confirme": True,
                },
                format="json",
            )
            id_mod = rep.data["id"]
            rep_applique = self.client_greffier.post(
                f"/api/v1/modifications/{id_mod}/appliquer/", format="json",
            )
            self.assertEqual(
                rep_applique.status_code, status.HTTP_400_BAD_REQUEST,
                f"Modification du champ {champ_interdit} acceptée à tort.",
            )
