"""
Scénario S4 — Recherche publique et cohérence du fichier public.

Articles 77, 94 à 97 du décret.

Règles vérifiées :
- ouverture à tout intéressé (anonyme), art. 94 ;
- deux critères minimum parmi les QUATRE critères limitatifs art. 96 ;
- critère hors liste non exploité ;
- résultat exhaustif des homonymes (art. 97 al. 2) ;
- une inscription RADIÉE reste visible au fichier public avec la
  mention, jusqu'à sa date d'expiration (art. 92 al. 2) ;
- une inscription ARCHIVÉE n'apparaît plus au fichier public
  (art. 92 al. 3).
"""
from __future__ import annotations

from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.inscriptions.models import Inscription, RoleInscriptionPartie
from apps.parties.models import RolePartie
from apps.workflow.statuts import StatutInscription

from tests import helpers


class S4_Recherche_API_Tests(TestCase):
    def setUp(self):
        self.client_public = APIClient()  # pas d'authentification → art. 94
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier(duree_jours=365)
        )

    # --------------------------------------------------------------------- #
    # Art. 96 — deux critères minimum                                        #
    # --------------------------------------------------------------------- #
    def test_recherche_un_seul_critere_refusee(self):
        rep = self.client_public.post(
            "/api/v1/recherche/",
            data={"nom_constituant": "Constituant SARL"},
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rep.data.get("article"), "96")

    def test_recherche_deux_criteres_ouverte_sans_auth(self):
        rep = self.client_public.post(
            "/api/v1/recherche/",
            data={
                "nom_constituant": "Constituant SARL",
                "numero_rc": "RC/NKT/2024/1001",
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK)
        self.assertEqual(rep.data["nombre_resultats"], 1)

    def test_critere_hors_liste_refuse_par_l_api(self):
        """
        Art. 96 — liste limitative. Avec le durcissement global des
        serializers (``StrictInputSerializer``), toute clé hors liste
        est REFUSÉE explicitement par l'API, uniformément à travers
        toute l'application (principe de cohérence globale du TDR).
        """
        rep = self.client_public.post(
            "/api/v1/recherche/",
            data={
                "nom_constituant": "Constituant SARL",
                "numero_rc": "RC/NKT/2024/1001",
                "nom_creancier": "Banque Créancière",  # hors liste art. 96
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_autorises", rep.data)

    # --------------------------------------------------------------------- #
    # Art. 97 al. 2 — homonymes                                              #
    # --------------------------------------------------------------------- #
    def test_homonymes_constituants_retournes_en_totalite(self):
        # Ajoute deux constituants PP homonymes.
        h1 = helpers.creer_partie_pp(nom="DUPONT", prenom="Pierre")
        h2 = helpers.creer_partie_pp(nom="DUPONT", prenom="Paul")
        RoleInscriptionPartie.objects.create(
            inscription=self.inscription, partie=h1, role=RolePartie.CONSTITUANT,
        )
        RoleInscriptionPartie.objects.create(
            inscription=self.inscription, partie=h2, role=RolePartie.CONSTITUANT,
        )
        rep = self.client_public.post(
            "/api/v1/recherche/",
            data={
                "nom_constituant": "DUPONT",
                "numero_inscription": self.inscription.numero_ordre,
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK)
        homonymes = rep.data["homonymes_par_inscription"].get(
            str(self.inscription.pk), []
        )
        noms = {h["prenom"] for h in homonymes if h["prenom"]}
        self.assertIn("Pierre", noms)
        self.assertIn("Paul", noms)

    # --------------------------------------------------------------------- #
    # Art. 92 al. 2 — mention « radiée » au fichier public                   #
    # --------------------------------------------------------------------- #
    def test_inscription_radiee_visible_au_fichier_public(self):
        client_agent = APIClient()
        client_agent.force_authenticate(self.agent)
        client_greffier = APIClient()
        client_greffier.force_authenticate(self.greffier)

        rep_rad = client_agent.post(
            "/api/v1/radiations/",
            data={"inscription": self.inscription.pk, "fondement": "consentement"},
            format="json",
        )
        id_rad = rep_rad.data["id"]
        client_greffier.post(
            f"/api/v1/radiations/{id_rad}/appliquer/", format="json",
        )
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.RADIEE)
        self.assertTrue(self.inscription.mention_radiee)

        # Une recherche valide doit toujours retrouver l'inscription
        # (art. 92 al. 2 — conservation au fichier public jusqu'à expiration).
        rep = self.client_public.post(
            "/api/v1/recherche/",
            data={
                "numero_inscription": self.inscription.numero_ordre,
                "numero_rc": "RC/NKT/2024/1001",
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK)
        self.assertEqual(rep.data["nombre_resultats"], 1)
        self.assertTrue(rep.data["inscriptions"][0]["mention_radiee"])

    # --------------------------------------------------------------------- #
    # Art. 92 al. 3 — après expiration, sortie du fichier public             #
    # --------------------------------------------------------------------- #
    def test_inscription_archivee_invisible_au_fichier_public(self):
        Inscription.objects.filter(pk=self.inscription.pk).update(
            date_expiration=timezone.localdate() - timedelta(days=1),
        )
        call_command("expirer_inscriptions")
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, StatutInscription.ARCHIVEE)
        self.assertEqual(self.inscription.fichier_actuel, "general")

        rep = self.client_public.post(
            "/api/v1/recherche/",
            data={
                "numero_inscription": self.inscription.numero_ordre,
                "numero_rc": "RC/NKT/2024/1001",
            },
            format="json",
        )
        self.assertEqual(rep.status_code, status.HTTP_200_OK)
        # L'inscription n'apparaît plus au fichier public (art. 77 + 92 al. 3).
        self.assertEqual(rep.data["nombre_resultats"], 0)
