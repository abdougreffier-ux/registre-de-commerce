"""
Services métier — catégories de biens et validation des attributs.

⚠️ Toute clé d'attribut hors schéma déclaré par la catégorie est REJETÉE.
La validation est strictement structurelle :
- types limités à ceux de ``TypeChamp`` ;
- champs obligatoires : doivent être présents et non vides.

Aucune règle juridique n'est inventée : la liste des catégories et leurs
champs proviennent du document MO « Liste des catégories de biens et
éléments de description » (référencé en L11 / livraison MO).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.utils.translation import gettext_lazy as _

from apps.biens.models import CategorieBien, TypeChamp


class SchemaCategorieInvalide(ValueError):
    """Levée lorsque le ``schema_champs`` lui-même est mal formé."""


class AttributsInvalides(ValueError):
    """Levée lorsqu'un payload d'attributs est non conforme au schéma."""

    def __init__(self, message: str, *, code: str = "attributs_invalides",
                 champ: str | None = None):
        super().__init__(message)
        self.code = code
        self.champ = champ


# --------------------------------------------------------------------------- #
# Validation du schéma                                                        #
# --------------------------------------------------------------------------- #
def valider_schema_champs(schema: list) -> None:
    """
    Vérifie qu'un descripteur de schéma est bien formé.

    Format attendu (pour chaque entrée) :
      { "cle": str, "type": str, "obligatoire": bool,
        "libelle_fr": str, "libelle_ar": str }
    """
    if not isinstance(schema, list):
        raise SchemaCategorieInvalide(
            "Le schéma de champs doit être une liste."
        )
    cles = set()
    types_admis = {t.value for t in TypeChamp}
    for index, descripteur in enumerate(schema):
        if not isinstance(descripteur, dict):
            raise SchemaCategorieInvalide(
                f"Champ #{index} : descripteur invalide (objet attendu)."
            )
        for attendu in ("cle", "type", "obligatoire", "libelle_fr", "libelle_ar"):
            if attendu not in descripteur:
                raise SchemaCategorieInvalide(
                    f"Champ #{index} : attribut « {attendu} » manquant."
                )
        cle = descripteur["cle"]
        if not isinstance(cle, str) or not cle.replace("_", "").isalnum():
            raise SchemaCategorieInvalide(
                f"Champ #{index} : clé invalide (alphanumérique avec _ requise)."
            )
        if cle in cles:
            raise SchemaCategorieInvalide(
                f"Champ #{index} : clé en doublon (« {cle} »)."
            )
        cles.add(cle)
        if descripteur["type"] not in types_admis:
            raise SchemaCategorieInvalide(
                f"Champ « {cle} » : type « {descripteur['type']} » non admis. "
                f"Types acceptés : {sorted(types_admis)}."
            )
        if not isinstance(descripteur["obligatoire"], bool):
            raise SchemaCategorieInvalide(
                f"Champ « {cle} » : ``obligatoire`` doit être booléen."
            )
        for libelle_attr in ("libelle_fr", "libelle_ar"):
            if not isinstance(descripteur[libelle_attr], str) or not descripteur[libelle_attr].strip():
                raise SchemaCategorieInvalide(
                    f"Champ « {cle} » : ``{libelle_attr}`` requis."
                )


# --------------------------------------------------------------------------- #
# Validation d'un payload d'attributs contre une catégorie+version            #
# --------------------------------------------------------------------------- #
def valider_attributs(
    *,
    categorie: CategorieBien,
    payload: dict,
) -> dict:
    """
    Valide ``payload`` contre le schéma de ``categorie``.

    Retourne un nouveau dict ne contenant **que** les clés du schéma,
    avec les valeurs canonicalisées (Decimal pour montant, date pour
    date, etc.). Toute clé inconnue déclenche une exception.
    """
    if not isinstance(payload, dict):
        raise AttributsInvalides(
            "Les attributs spécifiques doivent être un objet (dict).",
            code="format_attendu_dict",
        )

    valider_schema_champs(categorie.schema_champs)
    schema_par_cle = {c["cle"]: c for c in categorie.schema_champs}

    cles_inconnues = set(payload.keys()) - set(schema_par_cle.keys())
    if cles_inconnues:
        raise AttributsInvalides(
            f"Clés non prévues par la catégorie : "
            f"{sorted(cles_inconnues)}.",
            code="cles_hors_schema",
        )

    canonique = {}
    for cle, descripteur in schema_par_cle.items():
        if cle not in payload or _est_vide(payload[cle]):
            if descripteur["obligatoire"]:
                raise AttributsInvalides(
                    f"Le champ « {descripteur['libelle_fr']} » "
                    f"(clé {cle}) est obligatoire.",
                    code="champ_obligatoire_manquant",
                    champ=cle,
                )
            continue
        canonique[cle] = _canonicaliser(
            valeur=payload[cle], type_champ=descripteur["type"], cle=cle,
            libelle=descripteur["libelle_fr"],
        )
    return canonique


def _est_vide(v):
    if v is None: return True
    if isinstance(v, str) and not v.strip(): return True
    return False


def _canonicaliser(*, valeur, type_champ: str, cle: str, libelle: str):
    if type_champ == TypeChamp.TEXTE or type_champ == TypeChamp.TEXTE_LONG:
        if not isinstance(valeur, str):
            raise AttributsInvalides(
                f"« {libelle} » doit être un texte.",
                code="type_attendu_texte", champ=cle,
            )
        return valeur.strip()

    if type_champ == TypeChamp.NOMBRE:
        try:
            return int(valeur) if isinstance(valeur, (bool,)) is False and \
                float(valeur) == int(valeur) else float(valeur)
        except (TypeError, ValueError):
            raise AttributsInvalides(
                f"« {libelle} » doit être un nombre.",
                code="type_attendu_nombre", champ=cle,
            )

    if type_champ == TypeChamp.MONTANT:
        try:
            d = Decimal(str(valeur))
            return float(d)
        except (InvalidOperation, TypeError):
            raise AttributsInvalides(
                f"« {libelle} » doit être un montant numérique.",
                code="type_attendu_montant", champ=cle,
            )

    if type_champ == TypeChamp.DATE:
        if isinstance(valeur, date):
            return valeur.isoformat()
        if not isinstance(valeur, str):
            raise AttributsInvalides(
                f"« {libelle} » doit être une date au format AAAA-MM-JJ.",
                code="type_attendu_date", champ=cle,
            )
        try:
            return date.fromisoformat(valeur).isoformat()
        except ValueError:
            raise AttributsInvalides(
                f"« {libelle} » : format de date invalide (attendu AAAA-MM-JJ).",
                code="format_date_invalide", champ=cle,
            )

    if type_champ == TypeChamp.BOOLEEN:
        if isinstance(valeur, bool):
            return valeur
        if isinstance(valeur, str) and valeur.lower() in ("true", "false", "oui", "non"):
            return valeur.lower() in ("true", "oui")
        raise AttributsInvalides(
            f"« {libelle} » doit être un booléen.",
            code="type_attendu_booleen", champ=cle,
        )

    raise AttributsInvalides(
        f"Type « {type_champ} » non reconnu pour le champ « {libelle} ».",
        code="type_inconnu", champ=cle,
    )


# --------------------------------------------------------------------------- #
# Versionnage : création d'une nouvelle version d'une catégorie              #
# --------------------------------------------------------------------------- #
def publier_nouvelle_version(
    *,
    cle: str,
    libelle_fr: str,
    libelle_ar: str,
    schema_champs: list,
    affichage_observations: bool = True,
    description_fr: str = "",
    description_ar: str = "",
    acteur=None,
) -> CategorieBien:
    """
    Publie une nouvelle version d'une catégorie identifiée par ``cle``.

    - La version active précédente passe à ``actif=False``.
    - La nouvelle version reçoit ``actif=True`` et un numéro incrémenté.
    - Si une version active existe et n'a pas été utilisée, elle est
      désactivée mais conservée (non rétroactivité de toute façon).
    """
    valider_schema_champs(schema_champs)
    derniere = (
        CategorieBien.objects.filter(cle=cle).order_by("-version").first()
    )
    nouvelle_version = (derniere.version + 1) if derniere else 1

    if derniere and derniere.actif:
        derniere.actif = False
        super(CategorieBien, derniere).save(update_fields=["actif"])

    return CategorieBien.objects.create(
        cle=cle, version=nouvelle_version,
        libelle_fr=libelle_fr, libelle_ar=libelle_ar,
        description_fr=description_fr, description_ar=description_ar,
        schema_champs=schema_champs,
        affichage_observations=affichage_observations,
        actif=True,
        cree_par=acteur, modifie_par=acteur,
    )


def modifier_version(
    *,
    categorie: CategorieBien,
    libelle_fr: str | None = None,
    libelle_ar: str | None = None,
    schema_champs: list | None = None,
    affichage_observations: bool | None = None,
    description_fr: str | None = None,
    description_ar: str | None = None,
    acteur=None,
) -> CategorieBien:
    """
    Modifie une version DE CATÉGORIE — autorisé uniquement si elle n'a
    pas encore été utilisée par un BienGreve. Sinon, ``ValueError`` :
    il faut publier une nouvelle version (non rétroactivité).
    """
    if categorie.est_utilisee:
        raise ValueError(
            "Cette version de catégorie est déjà utilisée. "
            "Publier une nouvelle version pour appliquer les changements."
        )
    if libelle_fr is not None: categorie.libelle_fr = libelle_fr
    if libelle_ar is not None: categorie.libelle_ar = libelle_ar
    if description_fr is not None: categorie.description_fr = description_fr
    if description_ar is not None: categorie.description_ar = description_ar
    if affichage_observations is not None:
        categorie.affichage_observations = bool(affichage_observations)
    if schema_champs is not None:
        valider_schema_champs(schema_champs)
        categorie.schema_champs = schema_champs
    categorie.modifie_par = acteur
    categorie.save()
    return categorie
