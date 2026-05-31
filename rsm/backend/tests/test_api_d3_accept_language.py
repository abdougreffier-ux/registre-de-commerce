"""
D.3 — Équivalence juridique stricte FR/AR démontrée par HTTP.

Règle cardinale TDR § 7.3 :
> « Les versions française et arabe produisent les mêmes effets
>   juridiques, sans interprétation divergente possible. »

Démonstration par construction (L3.6 § 13) :
- un seul modèle de données ;
- un seul moteur de règles ;
- clés neutres en base ; libellés résolus à la présentation.

Ce fichier vérifie la démonstration **au niveau HTTP** :

1. Deux requêtes GET, l'une avec ``Accept-Language: fr``, l'autre avec
   ``Accept-Language: ar``, produisent des réponses dont **toutes les
   clés juridiques neutres sont strictement identiques**.
2. Deux requêtes POST de recherche publique avec Accept-Language
   différent produisent les **mêmes résultats** (mêmes inscriptions,
   mêmes homonymes, même horodatage).
3. Les référentiels retournent les mêmes clés + les mêmes structures,
   les libellés FR et AR étant tous deux présents côté payload.
4. Une tentative de rejet avec motif hors liste produit le même code
   d'erreur et la même référence d'article quelle que soit la langue
   (art. 80).

Portée bilinguisme :
- Les libellés (`*_libelle`) peuvent légitimement différer (Django
  résout ``get_*_display()`` avec la langue active). Ce n'est PAS une
  violation de la règle juridique puisqu'il s'agit d'une
  représentation d'affichage.
- Les clés neutres (`statut`, `canal_saisie`, `nature_droit`, `motif_rejet`,
  `fichier_actuel`, horodatages, numéros, montants, références) sont
  strictement égales — chaque inégalité serait une non-conformité.
"""
from __future__ import annotations

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.enums import CanalSaisie, MotifRejet, NaturesDroitInscrit
from apps.inscriptions.models import RoleInscriptionPartie
from apps.parties.models import RolePartie
from apps.workflow.statuts import StatutInscription

from tests import helpers


#: Clés juridiquement neutres qui doivent être strictement égales entre
#: deux réponses d'une même inscription, quelle que soit la langue.
CLES_NEUTRES_INSCRIPTION = [
    "reference_demande", "numero_ordre",
    "canal_saisie", "instant_arrivee", "instant_saisie_opposable",
    "statut", "mention_radiee", "fichier_actuel",
    "nature_droit", "somme_garantie", "monnaie",
    "duree_en_jours", "date_expiration",
    "adresse_electronique_notifications",
    "motif_rejet", "commentaire_rejet_fr", "commentaire_rejet_ar",
    "instant_rejet", "cree_le", "modifie_le",
]


def _client() -> APIClient:
    """Client public non authentifié (pour la recherche art. 94)."""
    return APIClient()


def _client_pour(user) -> APIClient:
    c = APIClient()
    c.force_authenticate(user)
    return c


def _paire_reponses(url, *, methode="get", auth=None, payload=None):
    """
    Envoie la même requête deux fois, une avec Accept-Language: fr,
    une avec Accept-Language: ar. Retourne le couple (rep_fr, rep_ar).
    """
    def _une(lang):
        c = _client_pour(auth) if auth else _client()
        fn = getattr(c, methode)
        kwargs = {"HTTP_ACCEPT_LANGUAGE": lang}
        if payload is not None:
            return fn(url, data=payload, format="json", **kwargs)
        return fn(url, **kwargs)
    return _une("fr"), _une("ar")


# --------------------------------------------------------------------------- #
# 1. Inscription — équivalence stricte des clés neutres                       #
# --------------------------------------------------------------------------- #
class D3_InscriptionClesNeutres_FR_AR_Tests(APITestCase):
    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )
        self.ref = str(self.inscription.reference_demande)

    def test_consultation_inscription_meme_cles_neutres(self):
        rep_fr, rep_ar = _paire_reponses(
            f"/api/v1/inscriptions/{self.ref}/",
            auth=self.agent,
        )
        self.assertEqual(rep_fr.status_code, status.HTTP_200_OK)
        self.assertEqual(rep_ar.status_code, status.HTTP_200_OK)

        for cle in CLES_NEUTRES_INSCRIPTION:
            self.assertEqual(
                rep_fr.data.get(cle), rep_ar.data.get(cle),
                f"Clé neutre « {cle} » divergente entre FR et AR : "
                f"{rep_fr.data.get(cle)!r} vs {rep_ar.data.get(cle)!r}.",
            )

    def test_liste_inscriptions_memes_cles_neutres(self):
        rep_fr, rep_ar = _paire_reponses(
            "/api/v1/inscriptions/", auth=self.agent,
        )
        # Même nombre de résultats.
        self.assertEqual(
            rep_fr.data.get("count"), rep_ar.data.get("count"),
        )
        # Pour chaque ligne, mêmes clés neutres.
        for ligne_fr, ligne_ar in zip(rep_fr.data["results"], rep_ar.data["results"]):
            for cle in CLES_NEUTRES_INSCRIPTION:
                self.assertEqual(
                    ligne_fr.get(cle), ligne_ar.get(cle),
                    f"Liste inscriptions — clé « {cle} » divergente.",
                )


# --------------------------------------------------------------------------- #
# 2. Recherche publique — résultat identique indépendant de la langue          #
# --------------------------------------------------------------------------- #
class D3_RecherchePublique_FR_AR_Tests(APITestCase):
    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_recherche_meme_resultats_identiques(self):
        payload = {
            "nom_constituant": "Constituant SARL",
            "numero_rc": "RC/NKT/2024/1001",
        }
        rep_fr, rep_ar = _paire_reponses(
            "/api/v1/recherche/",
            methode="post", payload=payload,
        )
        self.assertEqual(rep_fr.status_code, status.HTTP_200_OK)
        self.assertEqual(rep_ar.status_code, status.HTTP_200_OK)

        # Clés structurelles identiques.
        self.assertEqual(
            rep_fr.data["nombre_resultats"], rep_ar.data["nombre_resultats"],
        )
        self.assertEqual(
            rep_fr.data["criteres_utilises"],
            rep_ar.data["criteres_utilises"],
        )
        # Clés neutres des inscriptions trouvées.
        ins_fr = rep_fr.data["inscriptions"]
        ins_ar = rep_ar.data["inscriptions"]
        self.assertEqual(len(ins_fr), len(ins_ar))
        for a, b in zip(ins_fr, ins_ar):
            for cle in ("reference_demande", "numero_ordre", "statut",
                        "canal_saisie", "nature_droit", "date_expiration"):
                self.assertEqual(
                    a.get(cle), b.get(cle),
                    f"Recherche — clé « {cle} » divergente.",
                )
        # Les homonymes (art. 97 al. 2) doivent être identiques.
        self.assertEqual(
            rep_fr.data["homonymes_par_inscription"],
            rep_ar.data["homonymes_par_inscription"],
            "Les homonymes (art. 97 al. 2) doivent être strictement "
            "identiques — aucune divergence bilingue n'est acceptable.",
        )

    def test_recherche_critere_hors_liste_meme_refus(self):
        payload = {
            "nom_constituant": "X",
            "numero_rc": "Y",
            "champ_fantaisiste": "Z",  # hors liste art. 96
        }
        rep_fr, rep_ar = _paire_reponses(
            "/api/v1/recherche/", methode="post", payload=payload,
        )
        # Les deux refusent avec 400.
        self.assertEqual(rep_fr.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rep_ar.status_code, status.HTTP_400_BAD_REQUEST)
        # Les clés structurelles de l'erreur sont les mêmes.
        self.assertIn("non_autorises", rep_fr.data)
        self.assertIn("non_autorises", rep_ar.data)


# --------------------------------------------------------------------------- #
# 3. Rejet motivé — même article, même code HTTP, même classe                  #
# --------------------------------------------------------------------------- #
class D3_RejetMotive_FR_AR_Tests(APITestCase):
    def setUp(self):
        self.agent = helpers.creer_agent_saisie("d3_agent")
        self.greffier = helpers.creer_greffier("d3_greffier")

    def _deposer(self) -> str:
        c = _client_pour(self.agent)
        rep = c.post(
            "/api/v1/inscriptions/",
            data={
                "canal_saisie": CanalSaisie.GUICHET_PAPIER,
                "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                "somme_garantie": "1",
                "monnaie": "MRU",
                "duree_en_jours": 1,
            },
            format="json",
        )
        return rep.data["reference_demande"]

    def test_rejet_motif_hors_liste_meme_refus_FR_et_AR(self):
        ref_fr = self._deposer()
        ref_ar = self._deposer()

        rep_fr, _ = _paire_reponses(
            f"/api/v1/inscriptions/{ref_fr}/rejeter/",
            methode="post",
            auth=self.greffier,
            payload={"motif": "motif_invente"},
        )
        _, rep_ar = _paire_reponses(
            f"/api/v1/inscriptions/{ref_ar}/rejeter/",
            methode="post",
            auth=self.greffier,
            payload={"motif": "motif_invente"},
        )
        self.assertEqual(rep_fr.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rep_ar.status_code, status.HTTP_400_BAD_REQUEST)
        # Article fondateur et classe d'exception identiques.
        self.assertEqual(rep_fr.data.get("article"), rep_ar.data.get("article"))
        self.assertEqual(rep_fr.data.get("classe"), rep_ar.data.get("classe"))

    def test_rejet_motif_limitatif_meme_cles_FR_AR(self):
        ref_fr = self._deposer()
        ref_ar = self._deposer()

        rep_fr, _ = _paire_reponses(
            f"/api/v1/inscriptions/{ref_fr}/rejeter/",
            methode="post", auth=self.greffier,
            payload={
                "motif": MotifRejet.INFORMATIONS_ILLISIBLES,
                "commentaire_fr": "Document illisible",
                "commentaire_ar": "الوثيقة غير مقروءة",
            },
        )
        _, rep_ar = _paire_reponses(
            f"/api/v1/inscriptions/{ref_ar}/rejeter/",
            methode="post", auth=self.greffier,
            payload={
                "motif": MotifRejet.INFORMATIONS_ILLISIBLES,
                "commentaire_fr": "Document illisible",
                "commentaire_ar": "الوثيقة غير مقروءة",
            },
        )
        self.assertEqual(rep_fr.status_code, status.HTTP_200_OK, rep_fr.data)
        self.assertEqual(rep_ar.status_code, status.HTTP_200_OK, rep_ar.data)
        # Mêmes clés neutres : statut, motif, commentaires bilingues.
        for cle in (
            "statut", "motif_rejet",
            "commentaire_rejet_fr", "commentaire_rejet_ar",
        ):
            self.assertEqual(
                rep_fr.data[cle], rep_ar.data[cle],
                f"Rejet — clé « {cle} » divergente FR/AR.",
            )


# --------------------------------------------------------------------------- #
# 4. Référentiels — clés identiques, libellés bilingues présents               #
# --------------------------------------------------------------------------- #
class D3_Referentiels_FR_AR_Tests(APITestCase):
    def setUp(self):
        from django.core.management import call_command
        call_command("seed_referentiels")

    def test_referentiel_natures_droit_cles_identiques(self):
        """
        La liste des clés retournées par le référentiel doit être
        strictement identique quelle que soit la langue d'accès.
        Les libellés FR et AR, eux, sont tous deux exposés dans la
        structure (pas de filtrage par langue à ce niveau de l'API).
        """
        rep_fr, rep_ar = _paire_reponses(
            "/api/v1/referentiels/natures-droit/",
        )
        self.assertEqual(rep_fr.status_code, status.HTTP_200_OK)
        self.assertEqual(rep_ar.status_code, status.HTTP_200_OK)

        # On extrait l'ensemble des clés retournées, triées.
        cles_fr = sorted(item["cle"] for item in rep_fr.data["results"])
        cles_ar = sorted(item["cle"] for item in rep_ar.data["results"])
        self.assertEqual(
            cles_fr, cles_ar,
            "Le référentiel doit exposer exactement les mêmes clés FR/AR.",
        )

        # Pour chaque clé, libellés FR et AR tous deux renseignés.
        for item in rep_fr.data["results"]:
            self.assertTrue(item["libelle_fr"].strip())
            self.assertTrue(item["libelle_ar"].strip())

    def test_les_cinq_referentiels_bilingues(self):
        """Garantie de cohérence globale : s'applique aux 5 référentiels."""
        routes = [
            "/api/v1/referentiels/natures-droit/",
            "/api/v1/referentiels/motifs-rejet/",
            "/api/v1/referentiels/canaux-saisie/",
            "/api/v1/referentiels/criteres-recherche/",
            "/api/v1/referentiels/types-certificats/",
        ]
        for route in routes:
            rep_fr, rep_ar = _paire_reponses(route)
            self.assertEqual(rep_fr.status_code, status.HTTP_200_OK)
            self.assertEqual(rep_ar.status_code, status.HTTP_200_OK)

            cles_fr = sorted(i["cle"] for i in rep_fr.data["results"])
            cles_ar = sorted(i["cle"] for i in rep_ar.data["results"])
            self.assertEqual(cles_fr, cles_ar, f"Divergence sur {route}.")


# --------------------------------------------------------------------------- #
# 5. Dépôt d'inscription — payload strict, résultats neutres identiques        #
# --------------------------------------------------------------------------- #
class D3_DepotInscription_FR_AR_Tests(APITestCase):
    def setUp(self):
        self.agent_fr = helpers.creer_agent_saisie("d3_depot_agent_fr")
        self.agent_ar = helpers.creer_agent_saisie("d3_depot_agent_ar")

    def test_depot_identique_via_accept_language(self):
        payload = {
            "canal_saisie": CanalSaisie.GUICHET_PAPIER,
            "nature_droit": NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
            "somme_garantie": "1000.00",
            "monnaie": "MRU",
            "duree_en_jours": 30,
        }
        c_fr = _client_pour(self.agent_fr)
        c_ar = _client_pour(self.agent_ar)
        rep_fr = c_fr.post(
            "/api/v1/inscriptions/", data=payload, format="json",
            HTTP_ACCEPT_LANGUAGE="fr",
        )
        rep_ar = c_ar.post(
            "/api/v1/inscriptions/", data=payload, format="json",
            HTTP_ACCEPT_LANGUAGE="ar",
        )
        self.assertEqual(rep_fr.status_code, status.HTTP_201_CREATED)
        self.assertEqual(rep_ar.status_code, status.HTTP_201_CREATED)

        # Chaque dépôt crée une inscription distincte (reference_demande
        # différente) MAIS les clés juridiques neutres qui dépendent du
        # payload sont strictement égales.
        for cle in (
            "canal_saisie", "nature_droit", "statut",
            "somme_garantie", "monnaie", "duree_en_jours",
            "mention_radiee", "fichier_actuel",
        ):
            self.assertEqual(
                rep_fr.data[cle], rep_ar.data[cle],
                f"Dépôt — clé neutre « {cle} » divergente FR/AR.",
            )

        # Les deux sont passées à EN_CONTROLE_FORME (transition automatique).
        self.assertEqual(
            rep_fr.data["statut"], StatutInscription.EN_CONTROLE_FORME,
        )
        self.assertEqual(
            rep_ar.data["statut"], StatutInscription.EN_CONTROLE_FORME,
        )


# --------------------------------------------------------------------------- #
# 6. Cohérence globale : aucune réponse ne doit contenir de chaîne FR en dur   #
#    discriminant la langue active pour un champ neutre                        #
# --------------------------------------------------------------------------- #
class D3_NonDiscriminationLangue_Tests(APITestCase):
    """
    Un résultat juridique (statut, motif, article, classe) ne doit
    JAMAIS varier selon la langue. Si un champ neutre diverge FR/AR,
    c'est une non-conformité au TDR § 7.3.
    """

    def setUp(self):
        self.inscription, self.peuple, self.agent, self.greffier = (
            helpers.preparer_inscription_prete_a_modifier()
        )

    def test_aucune_divergence_sur_refus_art88(self):
        # Demande dont l'application doit échouer art. 88.
        c_a = _client_pour(self.agent)
        c_g = _client_pour(self.greffier)
        rep_creer = c_a.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "retrait bien",
                "objet_modification_ar": "إزالة المال",
                "diff_propose": {
                    "biens": {"retirer": [self.peuple["bien"].pk]},
                },
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        id_mod = rep_creer.data["id"]

        # L'application est tentée en FR et AR sur DEUX demandes distinctes
        # (car la première application échouée marque la demande REJETEE).
        # On crée une seconde demande identique pour tester AR.
        rep_creer2 = c_a.post(
            "/api/v1/modifications/",
            data={
                "inscription": self.inscription.pk,
                "objet_modification_fr": "retrait bien",
                "objet_modification_ar": "إزالة المال",
                "diff_propose": {
                    "biens": {"retirer": [self.peuple["bien"].pk]},
                },
                "accord_createur_confirme": True,
                "accord_constituant_confirme": True,
            },
            format="json",
        )
        id_mod2 = rep_creer2.data["id"]

        rep_fr = c_g.post(
            f"/api/v1/modifications/{id_mod}/appliquer/",
            format="json", HTTP_ACCEPT_LANGUAGE="fr",
        )
        rep_ar = c_g.post(
            f"/api/v1/modifications/{id_mod2}/appliquer/",
            format="json", HTTP_ACCEPT_LANGUAGE="ar",
        )
        # Les DEUX retournent 400 avec la même structure juridique.
        self.assertEqual(rep_fr.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rep_ar.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rep_fr.data["article"], rep_ar.data["article"])
        self.assertEqual(rep_fr.data["classe"], rep_ar.data["classe"])
        # Les deux demandes ont le même motif structuré en base.
        rep_liste_fr = c_a.get("/api/v1/modifications/", HTTP_ACCEPT_LANGUAGE="fr")
        rep_liste_ar = c_a.get("/api/v1/modifications/", HTTP_ACCEPT_LANGUAGE="ar")
        dem_fr = next(d for d in rep_liste_fr.data["results"] if d["id"] == id_mod)
        dem_ar = next(d for d in rep_liste_ar.data["results"] if d["id"] == id_mod2)
        self.assertEqual(dem_fr["motif_refus_code"], dem_ar["motif_refus_code"])
        self.assertEqual(dem_fr["statut"], dem_ar["statut"])
