"""
Calcul d'agrégats statistiques pour le greffe (article 82).

Principes cardinaux :
- AUCUNE invention de donnée : si un axe n'est pas modélisé dans le
  Registre (wilaya, moughataa, type de créancier, secteur d'activité),
  l'API expose explicitement ``disponible: false`` avec la raison
  juridique / technique. Aucune estimation, aucune extrapolation.
- Les agrégats sont reproductibles : ils dépendent uniquement du
  périmètre passé en paramètre et de l'état du Registre à l'instant T.
- Les libellés sont neutres (clés stables) ; la traduction est
  effectuée côté frontend via le référentiel i18n. Les valeurs
  numériques sont strictement identiques en FR et en AR.
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
from decimal import Decimal
from typing import Mapping

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.biens.models import BienGreve
from apps.inscriptions.models import Inscription
from apps.modifications.models import DemandeModification
from apps.parties.models import Partie, RolePartie, TypePartie
from apps.radiations.models import DemandeRadiation
from apps.renouvellements.models import DemandeRenouvellement
from apps.statistiques.models import ExtractionStatistique
from apps.utilisateurs.habilitations import (
    AutorisationRefusee,
    peut_produire_statistiques,
)


# Familles de biens — déduites de la liste limitative de l'article 76,
# cf. ``apps.core.enums.NaturesDroitInscrit``. Aucune donnée nouvelle
# n'est créée : on regroupe simplement les natures déjà saisies.
FAMILLES_BIENS = {
    "fonds_commerce": ("nant_fonds_commerce", "priv_vendeur_fonds"),
    "equipements_outillage": ("nant_outillage",),
    "stocks": ("nant_stocks",),
    "creances_comptes": ("nant_creance", "nant_compte_bancaire"),
    "valeurs_titres": ("nant_droits_associes",),
    "propriete_intellectuelle": ("nant_pi",),
    "privileges_publics": (
        "priv_tresor", "priv_fiscal", "priv_douanes", "priv_prevoyance",
    ),
}


# Tranches de durée en jours (bornes incluses à gauche, exclues à droite).
TRANCHES_DUREE_JOURS = [
    ("court_lt_180", 0, 180),
    ("moyen_180_365", 180, 366),
    ("long_1_2_ans", 366, 731),
    ("long_2_5_ans", 731, 1826),
    ("tres_long_5_ans_plus", 1826, 10**9),
]


def _appliquer_perimetre(qs, perimetre):
    d = dict(perimetre or {})
    if d.get("date_debut"):
        qs = qs.filter(cree_le__date__gte=d["date_debut"])
    if d.get("date_fin"):
        qs = qs.filter(cree_le__date__lte=d["date_fin"])
    if d.get("nature_droit"):
        qs = qs.filter(nature_droit=d["nature_droit"])
    if d.get("canal_saisie"):
        qs = qs.filter(canal_saisie=d["canal_saisie"])
    if d.get("statut"):
        qs = qs.filter(statut=d["statut"])
    return qs


def _famille_pour_nature(nature_droit: str) -> str:
    for famille, natures in FAMILLES_BIENS.items():
        if nature_droit in natures:
            return famille
    return "autre"


def _tranche_pour_duree(duree_jours: int | None) -> str | None:
    if duree_jours is None:
        return None
    for cle, mn, mx in TRANCHES_DUREE_JOURS:
        if mn <= duree_jours < mx:
            return cle
    return None


# --------------------------------------------------------------------------- #
# Indicateurs principaux                                                       #
# --------------------------------------------------------------------------- #
def calculer_indicateurs(perimetre: Mapping | None = None) -> dict:
    """
    Calcule l'ensemble des indicateurs statistiques exposables.

    Retourne un dictionnaire structuré par axe. Chaque axe est self-describing
    via la clé ``disponible`` : ``true`` lorsqu'il s'appuie sur des données
    modélisées, ``false`` accompagné d'une ``raison_indisponibilite``
    lorsqu'il dépend de données absentes du modèle actuel.
    """
    qs = _appliquer_perimetre(Inscription.objects.all(), perimetre)

    total = qs.count()

    # ----- A. Répartition territoriale ----------------------------------- #
    territorial = {
        "disponible": False,
        "raison_indisponibilite": "wilaya_moughataa_non_modelise",
        "note": (
            "Le décret 2021-033 (art. 85) ne prévoit que l'adresse "
            "non structurée du constituant ; aucune wilaya ni moughataa "
            "normalisée n'est collectée. Évolution éventuelle à arbitrer "
            "par décision MO."
        ),
    }

    # ----- B. Créanciers ------------------------------------------------- #
    # Table de rôles : ``apps.inscriptions.models.RoleInscriptionPartie``
    # (related_name côté Partie : ``roles_dans_inscriptions``).
    creanciers_qs = Partie.objects.filter(
        roles_dans_inscriptions__role=RolePartie.CREANCIER,
        roles_dans_inscriptions__actif=True,
        roles_dans_inscriptions__inscription__in=qs,
    )
    creanciers = {
        "disponible": True,
        "par_type_personne": dict(
            creanciers_qs.values_list("type_partie")
            .annotate(n=Count("id", distinct=True))
        ),
        "nombre_creanciers_distincts": creanciers_qs.distinct().count(),
        "raison_indisponibilite_typologie": "type_creancier_non_modelise",
        "note_typologie": (
            "Le modèle Partie ne distingue pas banque / microfinance / "
            "établissement financier. Une typologie sectorielle "
            "nécessiterait une extension du modèle (décision MO)."
        ),
    }

    # ----- C. Constituants / débiteurs ----------------------------------- #
    constituants_qs = Partie.objects.filter(
        roles_dans_inscriptions__role=RolePartie.CONSTITUANT,
        roles_dans_inscriptions__actif=True,
        roles_dans_inscriptions__inscription__in=qs,
    )
    constituants = {
        "disponible": True,
        "par_type_personne": dict(
            constituants_qs.values_list("type_partie")
            .annotate(n=Count("id", distinct=True))
        ),
        "nombre_constituants_distincts": constituants_qs.distinct().count(),
        "raison_indisponibilite_secteur": "secteur_non_modelise",
        "note_secteur": (
            "Le secteur d'activité du constituant n'est pas collecté "
            "par le décret. La typologie PME / non PME requiert une "
            "interconnexion (interconnexion : zone d'arbitrage MO)."
        ),
    }

    # ----- D. Biens grevés (par famille déduite de la nature) ----------- #
    par_nature = dict(
        qs.values_list("nature_droit").annotate(n=Count("*"))
    )
    par_famille = Counter()
    for nature, n in par_nature.items():
        par_famille[_famille_pour_nature(nature)] += n
    biens = {
        "disponible": True,
        "par_nature_droit": par_nature,
        "par_famille_bien": dict(par_famille),
        "biens_avec_numero_serie": BienGreve.objects.filter(
            inscription__in=qs,
        ).exclude(numero_serie="").count(),
        "biens_total": BienGreve.objects.filter(inscription__in=qs).count(),
        "note": (
            "Famille de biens déduite de la nature du droit (art. 76 — "
            "liste limitative). Aucun champ catégorie distinct n'est "
            "ajouté au modèle ; la déduction est documentée dans "
            "``services.FAMILLES_BIENS``."
        ),
    }

    # ----- E. Dynamique des inscriptions -------------------------------- #
    par_statut = dict(qs.values_list("statut").annotate(n=Count("*")))
    par_canal = dict(qs.values_list("canal_saisie").annotate(n=Count("*")))
    dynamique = {
        "disponible": True,
        "inscriptions_total": total,
        "par_statut": par_statut,
        "par_canal_saisie": par_canal,
        "demandes_modification": _filtrer_par_perimetre(
            DemandeModification, perimetre,
        ).count(),
        "demandes_renouvellement": _filtrer_par_perimetre(
            DemandeRenouvellement, perimetre,
        ).count(),
        "demandes_radiation": _filtrer_par_perimetre(
            DemandeRadiation, perimetre,
        ).count(),
    }

    # ----- F. Durée et montants ----------------------------------------- #
    par_tranche = Counter()
    for d in qs.values_list("duree_en_jours", flat=True):
        cle = _tranche_pour_duree(d)
        if cle:
            par_tranche[cle] += 1
    agreg_montants = qs.aggregate(
        somme_totale=Sum("somme_garantie"),
        somme_moyenne=Avg("somme_garantie"),
        duree_moyenne_jours=Avg("duree_en_jours"),
    )
    par_monnaie = {}
    for monnaie, n in qs.values_list("monnaie").annotate(n=Count("*")):
        par_monnaie[monnaie or "non_renseignee"] = n
    duree_montants = {
        "disponible": True,
        "duree_moyenne_jours": _to_float(agreg_montants["duree_moyenne_jours"]),
        "par_tranche_duree": dict(par_tranche),
        "somme_garantie_totale": _to_float(agreg_montants["somme_totale"]),
        "somme_garantie_moyenne": _to_float(agreg_montants["somme_moyenne"]),
        "par_monnaie": par_monnaie,
        "note_monnaie": (
            "Les sommes sont restituées telles que déclarées ; aucune "
            "conversion n'est opérée car les taux ne sont pas modélisés "
            "dans le Registre (ce qui serait une donnée externe)."
        ),
    }

    return {
        "instant_calcul": timezone.now().isoformat(timespec="seconds"),
        "perimetre": dict(perimetre or {}),
        "totaux": {
            "inscriptions": total,
            "biens_grevés": biens["biens_total"],
            "demandes_modification": dynamique["demandes_modification"],
            "demandes_renouvellement": dynamique["demandes_renouvellement"],
            "demandes_radiation": dynamique["demandes_radiation"],
        },
        "axes": {
            "territorial": territorial,
            "creanciers": creanciers,
            "constituants": constituants,
            "biens": biens,
            "dynamique": dynamique,
            "duree_montants": duree_montants,
        },
    }


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _filtrer_par_perimetre(modele, perimetre):
    """Filtre par instant de création, pour les modèles annexes."""
    qs = modele.objects.all()
    d = dict(perimetre or {})
    if d.get("date_debut"):
        qs = qs.filter(cree_le__date__gte=d["date_debut"])
    if d.get("date_fin"):
        qs = qs.filter(cree_le__date__lte=d["date_fin"])
    return qs


def _to_float(v):
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    return v


# --------------------------------------------------------------------------- #
# Indicateurs orientés « accès au financement des PME »                        #
# --------------------------------------------------------------------------- #
#
# ⚠️ Le décret 2021-033 ne définit pas la PME et le modèle de données ne
# collecte ni l'effectif, ni le chiffre d'affaires, ni le secteur. Les
# indicateurs ci-dessous sont donc des PROXIES :
#
#   - Constituants personne morale = entreprises (PME possibles, non
#     identifiées comme telles) ;
#   - Sûretés sur fonds de commerce / équipements / stocks =
#     « familles productives » couramment associées au financement
#     d'exploitation ;
#   - Tranches de montants servent d'estimation indicative.
#
# Chaque indicateur expose explicitement son statut « proxy » et la
# limitation correspondante. La typologie PME stricte requiert un
# enrichissement modèle (à arbitrer en F13/F15 par le MO).

# Familles « productives » — utilisées comme proxy d'usage entreprise.
FAMILLES_PRODUCTIVES_PME = (
    "fonds_commerce",
    "equipements_outillage",
    "stocks",
    "creances_comptes",
)


def calculer_indicateurs_financement_pme(perimetre=None) -> dict:
    """
    Indicateurs ciblés sur l'accès au financement des entreprises.

    Retourne :
      - ``totaux``     : compteurs absolus (ex. inscriptions productives)
      - ``ratios``     : pourcentages (ex. % productives)
      - ``familles``   : ventilation par famille productive
      - ``parties``    : profil PP/PM des constituants
      - ``meta``       : étiquetage explicite « proxy » + limitation
    """
    qs = _appliquer_perimetre(Inscription.objects.all(), perimetre)
    total = qs.count()

    # Inscriptions productives (sûretés sur fonds, équipements, stocks,
    # créances/comptes) — proxy de financement d'exploitation.
    natures_productives = []
    for famille in FAMILLES_PRODUCTIVES_PME:
        natures_productives.extend(FAMILLES_BIENS.get(famille, ()))
    qs_productives = qs.filter(nature_droit__in=natures_productives)
    n_productives = qs_productives.count()

    # Constituants personnes morales rattachés à des sûretés productives.
    constituants_pm_qs = Partie.objects.filter(
        roles_dans_inscriptions__role=RolePartie.CONSTITUANT,
        roles_dans_inscriptions__actif=True,
        roles_dans_inscriptions__inscription__in=qs_productives,
        type_partie=TypePartie.PERSONNE_MORALE,
    ).distinct()
    constituants_pm = constituants_pm_qs.count()

    constituants_total_qs = Partie.objects.filter(
        roles_dans_inscriptions__role=RolePartie.CONSTITUANT,
        roles_dans_inscriptions__actif=True,
        roles_dans_inscriptions__inscription__in=qs,
    ).distinct()
    constituants_total = constituants_total_qs.count()

    # Ventilation par famille productive (chiffres absolus).
    par_famille = {}
    for famille in FAMILLES_PRODUCTIVES_PME:
        natures = FAMILLES_BIENS.get(famille, ())
        par_famille[famille] = qs.filter(nature_droit__in=natures).count()

    # Maturité du registre : taux de radiation, % d'inscriptions actives.
    n_inscrites = qs.filter(statut="inscrite").count()
    n_radiees = qs.filter(statut="radiee").count()
    n_expirees = qs.filter(statut="expiree").count()

    # Échéances proches : inscriptions actives expirant dans 90 jours.
    seuil_90j = (timezone.now() + timedelta(days=90)).date()

    n_echeance_90j = qs.filter(
        statut="inscrite",
        date_expiration__isnull=False,
        date_expiration__lte=seuil_90j,
    ).count()

    # Agrégats financiers.
    montants = qs_productives.aggregate(
        somme_totale=Sum("somme_garantie"),
        somme_moyenne=Avg("somme_garantie"),
        duree_moyenne_jours=Avg("duree_en_jours"),
    )

    return {
        "instant_calcul": timezone.now().isoformat(timespec="seconds"),
        "perimetre": dict(perimetre or {}),
        "totaux": {
            "inscriptions": total,
            "inscriptions_productives": n_productives,
            "constituants_total": constituants_total,
            "constituants_pm_productifs": constituants_pm,
            "inscrites_actives": n_inscrites,
            "radiees": n_radiees,
            "expirees": n_expirees,
            "echeances_90_jours": n_echeance_90j,
        },
        "ratios": {
            "part_productives_pct": _pct(n_productives, total),
            "part_constituants_pm_pct": _pct(constituants_pm, constituants_total),
            "taux_radiation_pct": _pct(n_radiees, total),
            "taux_actif_pct": _pct(n_inscrites, total),
        },
        "familles_productives": par_famille,
        "montants_productifs": {
            "somme_totale": _to_float(montants["somme_totale"]),
            "somme_moyenne": _to_float(montants["somme_moyenne"]),
            "duree_moyenne_jours": _to_float(montants["duree_moyenne_jours"]),
        },
        "meta": {
            "type": "proxy",
            "limitation": (
                "Le modèle de données ne collecte ni la qualification "
                "PME, ni le secteur, ni l'effectif. Les indicateurs "
                "ci-dessus sont des proxies fondés sur les familles de "
                "biens productives et sur le type de personne (PM). "
                "Une typologie PME stricte requiert l'enrichissement "
                "des modèles (à arbitrer par le MO — fiches F13/F15)."
            ),
            "familles_productives": list(FAMILLES_PRODUCTIVES_PME),
        },
    }


def _pct(n, total):
    if not total:
        return 0.0
    return round(100.0 * float(n) / float(total), 2)


# --------------------------------------------------------------------------- #
# Conservation des extractions traçables (art. 82)                             #
# --------------------------------------------------------------------------- #
def produire_extraction(
    *,
    acteur,
    perimetre: Mapping | None = None,
) -> ExtractionStatistique:
    """
    Calcule les indicateurs ET enregistre une extraction immutable
    associée au producteur (monopole du greffe — art. 82). Tracée au
    journal d'audit (catégorie ``EXPORT_STAT``).
    """
    if not peut_produire_statistiques(acteur):
        raise AutorisationRefusee(
            "Production statistique refusée : monopole du greffe (art. 82)."
        )

    resultat = calculer_indicateurs(perimetre)
    extraction = ExtractionStatistique(
        producteur=acteur, perimetre=dict(perimetre or {}),
        resultat=resultat,
    )
    extraction.save()

    tracer(
        categorie=CategorieAudit.EXPORT_STAT,
        action_cle="statistiques.extraire",
        resultat=ResultatAudit.SUCCES,
        objet_type="extraction_statistique",
        objet_reference=str(extraction.pk),
        details={
            "perimetre": dict(perimetre or {}),
            "total_inscriptions": resultat["totaux"]["inscriptions"],
        },
        contexte=contexte_courant(),
    )
    return extraction
