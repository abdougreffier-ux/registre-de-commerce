"""
Matrice des statuts et des transitions — TDR § 4.3.

Les valeurs et les transitions sont DIRECTEMENT issues du TDR et du décret.
Toute modification de ce fichier doit être justifiée par une évolution
du cadre juridique et tracée au registre des hypothèses (livrable L11).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db import models
from django.utils.translation import gettext_lazy as _


class StatutInscription(models.TextChoices):
    BROUILLON = "brouillon", _(
        "Brouillon (non encore soumis au greffe)"
    )
    RECUE = "recue", _("Reçue / Soumise au greffe")
    EN_CONTROLE_FORME = "en_controle_forme", _(
        "En contrôle de forme — en attente de validation"
    )
    RETOURNEE = "retournee", _(
        "Retournée au déclarant pour correction (workflow Greffier ⇄ Déclarant)"
    )
    REJETEE = "rejetee", _("Rejetée")
    INSCRITE = "inscrite", _("Inscrite (en cours de validité)")
    MODIFIEE = "modifiee", _("Modifiée")
    RENOUVELEE = "renouvelee", _("Renouvelée")
    RADIEE = "radiee", _("Radiée (en cours de validité)")
    EXPIREE = "expiree", _("Expirée")
    ARCHIVEE = "archivee", _("Archivée (fichier général)")


# Regroupements utilitaires — fondés sur l'article 77 et le § 4.3 du TDR.
# Note : ``BROUILLON`` et ``RETOURNEE`` sont des états de demande
# pré-validation, jamais publiés au fichier public.
STATUTS_PRE_VALIDATION = frozenset({
    StatutInscription.BROUILLON,
    StatutInscription.RECUE,
    StatutInscription.EN_CONTROLE_FORME,
    StatutInscription.RETOURNEE,
})

STATUTS_FICHIER_PUBLIC = frozenset({
    StatutInscription.INSCRITE,
    StatutInscription.MODIFIEE,
    StatutInscription.RENOUVELEE,
    StatutInscription.RADIEE,  # conservées avec mention "radiée" jusqu'à expiration
})

STATUTS_EN_COURS_DE_VALIDITE = frozenset({
    StatutInscription.INSCRITE,
    StatutInscription.MODIFIEE,
    StatutInscription.RENOUVELEE,
})

STATUTS_FICHIER_GENERAL = frozenset({
    StatutInscription.ARCHIVEE,
})

STATUTS_TERMINAUX = frozenset({
    StatutInscription.EXPIREE,
    StatutInscription.ARCHIVEE,
    StatutInscription.REJETEE,
})


@dataclass(frozen=True)
class Transition:
    depuis: str
    vers: str
    #: Identifiant stable de l'événement métier déclenchant la transition.
    evenement: str
    #: Référence des articles du décret fondant la transition.
    articles: tuple[str, ...]
    #: Motif résumé, extrait du TDR.
    motif: str
    #: ``True`` si la transition est systématique (automatique), ``False`` si
    #: elle nécessite un acte humain explicite.
    automatique: bool = False


#: MATRICE DES TRANSITIONS AUTORISÉES — § 4.3 du TDR (§ "Matrice des
#: transitions autorisées"). La lecture doit se faire article-par-article.
TRANSITIONS: tuple[Transition, ...] = (
    # ── Workflow Demande ⇄ Inscription (directive MO 2026-05-31) ──
    Transition(
        depuis=StatutInscription.BROUILLON,
        vers=StatutInscription.RECUE,
        evenement="soumission_declarant",
        articles=("78", "85"),
        motif="Soumission d'un brouillon par le déclarant.",
    ),
    Transition(
        depuis=StatutInscription.EN_CONTROLE_FORME,
        vers=StatutInscription.RETOURNEE,
        evenement="retour_observation",
        articles=("85", "86"),
        motif="Retour au déclarant avec observation obligatoire FR/AR.",
    ),
    Transition(
        depuis=StatutInscription.RETOURNEE,
        vers=StatutInscription.EN_CONTROLE_FORME,
        evenement="resoumission_declarant",
        articles=("78", "85"),
        motif="Resoumission après correction par le déclarant.",
    ),
    Transition(
        depuis=StatutInscription.RECUE,
        vers=StatutInscription.EN_CONTROLE_FORME,
        evenement="prise_en_charge",
        articles=("78",),
        motif="Automatique dès la prise en charge.",
        automatique=True,
    ),
    Transition(
        depuis=StatutInscription.EN_CONTROLE_FORME,
        vers=StatutInscription.REJETEE,
        evenement="rejet_art80",
        articles=("80",),
        motif="Non-respect des motifs limitatifs de l'article 80.",
    ),
    Transition(
        depuis=StatutInscription.EN_CONTROLE_FORME,
        vers=StatutInscription.INSCRITE,
        evenement="validation_greffier",
        articles=("85", "86", "78"),
        motif="Respect des conditions art. 85 ; validation du greffier.",
    ),
    Transition(
        depuis=StatutInscription.INSCRITE,
        vers=StatutInscription.MODIFIEE,
        evenement="modification_art88",
        articles=("88",),
        motif="Formulaire de modification conforme à l'article 88.",
    ),
    Transition(
        depuis=StatutInscription.MODIFIEE,
        vers=StatutInscription.MODIFIEE,
        evenement="modification_art88",
        articles=("88",),
        motif="Nouvelle modification sur une inscription déjà modifiée.",
    ),
    Transition(
        depuis=StatutInscription.RENOUVELEE,
        vers=StatutInscription.MODIFIEE,
        evenement="modification_art88",
        articles=("88",),
        motif="Modification après renouvellement.",
    ),
    Transition(
        depuis=StatutInscription.INSCRITE,
        vers=StatutInscription.RENOUVELEE,
        evenement="renouvellement_art91",
        articles=("91",),
        motif="Renouvellement avant expiration (art. 91).",
    ),
    Transition(
        depuis=StatutInscription.MODIFIEE,
        vers=StatutInscription.RENOUVELEE,
        evenement="renouvellement_art91",
        articles=("91",),
        motif="Renouvellement avant expiration (art. 91).",
    ),
    Transition(
        depuis=StatutInscription.INSCRITE,
        vers=StatutInscription.RADIEE,
        evenement="radiation_art92",
        articles=("92",),
        motif="Radiation d'une inscription en cours.",
    ),
    Transition(
        depuis=StatutInscription.MODIFIEE,
        vers=StatutInscription.RADIEE,
        evenement="radiation_art92",
        articles=("92",),
        motif="Radiation d'une inscription modifiée.",
    ),
    Transition(
        depuis=StatutInscription.RENOUVELEE,
        vers=StatutInscription.RADIEE,
        evenement="radiation_art92",
        articles=("92",),
        motif="Radiation d'une inscription renouvelée.",
    ),
    Transition(
        depuis=StatutInscription.INSCRITE,
        vers=StatutInscription.EXPIREE,
        evenement="expiration_automatique",
        articles=("85", "92"),
        motif="Atteinte de la date d'expiration.",
        automatique=True,
    ),
    Transition(
        depuis=StatutInscription.MODIFIEE,
        vers=StatutInscription.EXPIREE,
        evenement="expiration_automatique",
        articles=("85", "92"),
        motif="Atteinte de la date d'expiration.",
        automatique=True,
    ),
    Transition(
        depuis=StatutInscription.RENOUVELEE,
        vers=StatutInscription.EXPIREE,
        evenement="expiration_automatique",
        articles=("91",),
        motif="Atteinte de la date d'expiration (renouvellement inclus).",
        automatique=True,
    ),
    Transition(
        depuis=StatutInscription.RADIEE,
        vers=StatutInscription.EXPIREE,
        evenement="expiration_automatique",
        articles=("92",),
        motif="Expiration d'une inscription radiée non encore expirée.",
        automatique=True,
    ),
    Transition(
        depuis=StatutInscription.EXPIREE,
        vers=StatutInscription.ARCHIVEE,
        evenement="transfert_fichier_general",
        articles=("79", "92"),
        motif="Transfert automatique au fichier général (art. 92 al. 3).",
        automatique=True,
    ),
)


#: TRANSITIONS EXPLICITEMENT INTERDITES — § 4.3 "Transitions explicitement
#: interdites" du TDR. Elles sont listées ici afin que toute modification de
#: la matrice principale provoque un conflit détectable en revue.
INTERDICTIONS_EXPLICITES: tuple[tuple[str, str, str], ...] = (
    (StatutInscription.RADIEE, StatutInscription.INSCRITE,
     "Pas de retour en arrière d'une radiation (§ 4.3 TDR)."),
    (StatutInscription.EXPIREE, StatutInscription.MODIFIEE,
     "Pas de modification après expiration (§ 4.3 TDR)."),
    (StatutInscription.EXPIREE, StatutInscription.RENOUVELEE,
     "Pas de renouvellement après expiration (art. 91)."),
    (StatutInscription.ARCHIVEE, StatutInscription.INSCRITE,
     "Pas de sortie du fichier général vers le fichier public."),
    # ── Verrous workflow demande-inscription (directive MO 2026-05-31) ──
    (StatutInscription.RETOURNEE, StatutInscription.INSCRITE,
     "Une demande retournée ne peut être validée directement : "
     "elle doit repasser par le contrôle de forme après resoumission."),
    (StatutInscription.INSCRITE, StatutInscription.RETOURNEE,
     "Une inscription validée ne peut être retournée au déclarant : "
     "la correction ne passe que par une modification art. 88."),
)


def transitions_depuis(statut: str) -> Iterable[Transition]:
    """Liste les transitions autorisées depuis un statut donné."""
    return tuple(t for t in TRANSITIONS if t.depuis == statut)


def est_autorisee(depuis: str, vers: str, evenement: str) -> bool:
    return any(
        t.depuis == depuis and t.vers == vers and t.evenement == evenement
        for t in TRANSITIONS
    )


def transition_requise(
    depuis: str, vers: str, evenement: str,
) -> Transition:
    for t in TRANSITIONS:
        if t.depuis == depuis and t.vers == vers and t.evenement == evenement:
            return t
    raise LookupError(
        f"Transition {depuis!r} → {vers!r} ({evenement}) non définie "
        "dans la matrice § 4.3 du TDR."
    )


def est_explicitement_interdite(depuis: str, vers: str) -> str | None:
    """Retourne le motif d'interdiction s'il existe, ``None`` sinon."""
    for d, v, raison in INTERDICTIONS_EXPLICITES:
        if d == depuis and v == vers:
            return raison
    return None
