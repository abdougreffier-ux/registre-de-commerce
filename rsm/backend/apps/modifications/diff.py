"""
Schéma strict du différentiel (diff) d'une demande de modification.

Règles imposées :
- Schéma ``strict`` (``extra="forbid"``) : toute clé hors schéma provoque
  le rejet immédiat de la demande, afin d'empêcher l'injection de champs
  non prévus par l'article 88.
- La durée (``duree_en_jours``) n'est PAS modifiable par ce canal :
  l'article 90 alinéa 2 impose que seule une prorogation expresse
  (art. 91 — renouvellement) modifie la durée de l'inscription initiale.
- La date d'expiration n'est pas modifiable par ce canal (cf. ci-dessus).
- L'instant de saisie opposable et le numéro d'ordre ne sont JAMAIS
  modifiables (art. 78 — immutabilité des horodatages et du n° d'ordre).

Champs effectivement modifiables par l'article 88 :
- identification des parties (constituants, créanciers garantis,
  débiteurs, requérant) ;
- description des biens grevés ;
- nature du droit (dans la liste limitative de l'art. 76) ;
- somme garantie et monnaie ;
- adresse électronique pour notifications.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal

from apps.core.enums import NaturesDroitInscrit
from apps.parties.models import RolePartie, TypePartie


# ZONE D'ARBITRAGE MO — ``L11/parties_reutilisation``
# --------------------------------------------------
# À ce jour, un ajout de partie dans le diff CRÉE systématiquement une
# nouvelle ligne ``Partie`` à partir des clés ci-dessous. Le schéma du
# diff n'expose PAS de clé ``partie_id`` qui permettrait de référencer
# une partie déjà connue du système. Deux options sont en attente
# d'arbitrage MO :
#
#   (a) conservatisme — chaque inscription possède ses propres lignes de
#       parties, sans rapprochement automatique. Confirme strictement le
#       régime déclaratif de l'article 86 et évite tout contrôle au fond.
#       Inconvénient : duplication possible de mêmes personnes entre
#       plusieurs inscriptions.
#
#   (b) réutilisation — une nouvelle clé ``partie_id`` autoriserait le
#       dépositaire à référencer une partie existante. Impose de définir
#       le périmètre d'accessibilité (toutes parties du registre ? parties
#       dont le dépositaire est l'auteur de la création initiale ?) et
#       les conséquences d'une désactivation ultérieure.
#
# Tant que l'arbitrage n'est pas rendu, seul (a) est implémenté. Un test
# placeholder ``@arbitrage_mo(reference="L11/parties_reutilisation")`` est
# posé dans ``tests/test_api_zones_gelees.py`` pour activer la couverture
# (b) à décision du MO.
CLES_PARTIES_PP = {"type_partie", "nom", "prenom", "date_naissance",
                   "lieu_naissance", "adresse", "adresse_electronique",
                   "telephone"}
CLES_PARTIES_PM = {"type_partie", "denomination_sociale", "numero_rc",
                   "adresse", "adresse_electronique", "telephone"}
CLES_BIEN = {"marque", "modele", "annee", "numero_serie",
             "description_fr", "description_ar"}

CHAMPS_SCALAIRES_MODIFIABLES = {
    "nature_droit",
    "somme_garantie",
    "monnaie",
    "adresse_electronique_notifications",
}

CHAMPS_JAMAIS_MODIFIABLES = frozenset({
    # Art. 78 — immuabilité du numéro d'ordre et de l'horodatage.
    "numero_ordre",
    "instant_saisie_opposable",
    "instant_arrivee",
    "reference_demande",
    # Art. 90 al. 2 — durée non modifiable par modification.
    "duree_en_jours",
    "date_expiration",
    # Champs internes.
    "statut",
    "fichier_actuel",
    "mention_radiee",
    "motif_rejet",
})


@dataclass(frozen=True)
class AjouterPartie:
    """Ajout d'une partie à un rôle donné."""

    role: str
    type_partie: str
    donnees: dict  # sous-ensemble des champs de ``Partie``

    def valider(self) -> None:
        if self.role not in dict(RolePartie.choices):
            raise ValueError(f"Rôle de partie inconnu : {self.role!r}")
        if self.type_partie not in dict(TypePartie.choices):
            raise ValueError(f"Type de partie inconnu : {self.type_partie!r}")
        cles_autorisees = (
            CLES_PARTIES_PP if self.type_partie == TypePartie.PERSONNE_PHYSIQUE
            else CLES_PARTIES_PM
        )
        extras = set(self.donnees) - cles_autorisees - {"type_partie"}
        if extras:
            raise ValueError(
                f"Clés non autorisées dans l'ajout de partie : {sorted(extras)}"
            )


@dataclass(frozen=True)
class AjouterBien:
    """Ajout d'un bien grevé."""

    donnees: dict

    def valider(self) -> None:
        extras = set(self.donnees) - CLES_BIEN
        if extras:
            raise ValueError(
                f"Clés non autorisées dans l'ajout de bien : {sorted(extras)}"
            )


@dataclass(frozen=True)
class DiffModification:
    """
    Structure complète et validée d'une modification.

    Règles :
    - ``parties_retirer`` et ``biens_retirer`` contiennent des identifiants
      de liens / biens ACTIFS au moment de l'application ; un
      identifiant inactif ou inconnu provoque un échec.
    - ``scalaires`` ne peut contenir que les clés listées dans
      ``CHAMPS_SCALAIRES_MODIFIABLES``.
    - Si un champ ``CHAMPS_JAMAIS_MODIFIABLES`` apparaît, la demande est
      refusée.
    """

    parties_ajouter: list[AjouterPartie] = field(default_factory=list)
    parties_retirer: list[int] = field(default_factory=list)  # ids de RoleInscriptionPartie
    biens_ajouter: list[AjouterBien] = field(default_factory=list)
    biens_retirer: list[int] = field(default_factory=list)  # ids de BienGreve
    scalaires: dict[str, Any] = field(default_factory=dict)

    # -------- Construction à partir d'un dict JSON -------- #
    @classmethod
    def depuis_dict(cls, brut: dict | None) -> "DiffModification":
        brut = dict(brut or {})
        cles_racine_autorisees = {"parties", "biens", "scalaires"}
        extras = set(brut) - cles_racine_autorisees
        if extras:
            raise ValueError(
                f"Clés de diff non autorisées : {sorted(extras)}. "
                f"Seules {sorted(cles_racine_autorisees)} sont admises."
            )

        parties = brut.get("parties") or {}
        biens = brut.get("biens") or {}
        scalaires = brut.get("scalaires") or {}

        diff = cls(
            parties_ajouter=[
                AjouterPartie(
                    role=p["role"],
                    type_partie=p.get("type_partie") or p["donnees"].get("type_partie"),
                    donnees={k: v for k, v in p["donnees"].items() if k != "type_partie"},
                )
                for p in (parties.get("ajouter") or [])
            ],
            parties_retirer=list(parties.get("retirer") or []),
            biens_ajouter=[AjouterBien(donnees=dict(b)) for b in (biens.get("ajouter") or [])],
            biens_retirer=list(biens.get("retirer") or []),
            scalaires=dict(scalaires),
        )
        diff.valider()
        return diff

    # -------- Validation -------- #
    def valider(self) -> None:
        # Scalaires — champs jamais modifiables.
        jamais = set(self.scalaires) & CHAMPS_JAMAIS_MODIFIABLES
        if jamais:
            raise ValueError(
                f"Champs non modifiables par une modification "
                f"(art. 78 / 90 al. 2) : {sorted(jamais)}."
            )
        # Scalaires — clés inconnues.
        extras = set(self.scalaires) - CHAMPS_SCALAIRES_MODIFIABLES
        if extras:
            raise ValueError(
                f"Clés scalaires non prévues par l'article 88 : {sorted(extras)}. "
                f"Seules {sorted(CHAMPS_SCALAIRES_MODIFIABLES)} sont admises."
            )
        # Nature de droit : liste limitative (art. 76).
        if "nature_droit" in self.scalaires:
            val = self.scalaires["nature_droit"]
            if val not in dict(NaturesDroitInscrit.choices):
                raise ValueError(
                    f"Nature de droit hors liste limitative art. 76 : {val!r}."
                )
        # Somme garantie : convertible en Decimal positif ou nul.
        if "somme_garantie" in self.scalaires:
            val = self.scalaires["somme_garantie"]
            if val is not None:
                try:
                    d = Decimal(str(val))
                except (ArithmeticError, ValueError) as e:
                    raise ValueError("Somme garantie invalide.") from e
                if d < 0:
                    raise ValueError("Somme garantie négative refusée.")
        # Sous-structures.
        for p in self.parties_ajouter:
            p.valider()
        for b in self.biens_ajouter:
            b.valider()

    @property
    def est_vide(self) -> bool:
        return not any((
            self.parties_ajouter, self.parties_retirer,
            self.biens_ajouter, self.biens_retirer, self.scalaires,
        ))
