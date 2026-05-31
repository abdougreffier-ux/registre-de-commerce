"""
Référentiels bilingues du RSM.

Les énumérations « hard-codées » (app ``core.enums``) définissent la liste
limitative des valeurs admises par le décret. Les référentiels ci-dessous
permettent à l'Administrateur fonctionnel (§ 4.1) de maintenir les libellés,
les explications et les modèles d'intitulés, sans jamais modifier ni étendre
les listes limitatives.

Principes :
- Chaque libellé est bilingue FR/AR (mixin ``Bilingue``).
- Aucune valeur fourre-tout (« autre ») n'est admise.
- Les clés (``cle``) correspondent exactement aux valeurs des énumérations
  du code ; toute divergence empêche l'affichage.
"""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import (
    CanalSaisie,
    CritereRecherche,
    MotifRejet,
    NaturesDroitInscrit,
    TypeCertificat,
)
from apps.core.models import Bilingue, Horodatage


class LibelleReferentiel(Horodatage, Bilingue):
    """Base abstraite pour tout référentiel (FR, AR, descriptions)."""

    cle = models.CharField(_("Clé technique"), max_length=64, unique=True)
    description_fr = models.TextField(_("Description (FR)"), blank=True)
    description_ar = models.TextField(_("Description (AR)"), blank=True)
    actif = models.BooleanField(_("Actif"), default=True)
    ordre = models.PositiveIntegerField(_("Ordre d'affichage"), default=0)

    class Meta:
        abstract = True
        ordering = ("ordre", "cle")


class LibelleNatureDroit(LibelleReferentiel):
    """
    Natures de sûretés et droits inscrits (art. 76).
    La clé correspond à une valeur de :class:`NaturesDroitInscrit`.
    """

    class Meta(LibelleReferentiel.Meta):
        verbose_name = _("Libellé — nature de droit inscrit")
        verbose_name_plural = _("Libellés — natures de droits inscrits")


class LibelleMotifRejet(LibelleReferentiel):
    """Motifs limitatifs de rejet (art. 80) — clé liée à :class:`MotifRejet`."""

    class Meta(LibelleReferentiel.Meta):
        verbose_name = _("Libellé — motif de rejet (art. 80)")
        verbose_name_plural = _("Libellés — motifs de rejet (art. 80)")


class LibelleCanalSaisie(LibelleReferentiel):
    """Libellés des canaux d'entrée (art. 78)."""

    class Meta(LibelleReferentiel.Meta):
        verbose_name = _("Libellé — canal de saisie")
        verbose_name_plural = _("Libellés — canaux de saisie")


class LibelleCritereRecherche(LibelleReferentiel):
    """Libellés des critères de recherche (art. 96)."""

    class Meta(LibelleReferentiel.Meta):
        verbose_name = _("Libellé — critère de recherche (art. 96)")
        verbose_name_plural = _("Libellés — critères de recherche (art. 96)")


class LibelleTypeCertificat(LibelleReferentiel):
    """Libellés des types de certificats."""

    class Meta(LibelleReferentiel.Meta):
        verbose_name = _("Libellé — type de certificat")
        verbose_name_plural = _("Libellés — types de certificats")


# --------------------------------------------------------------------------- #
# Invariants                                                                   #
# --------------------------------------------------------------------------- #
LIBELLES_ATTENDUS = {
    LibelleNatureDroit: {v for v, _ in NaturesDroitInscrit.choices},
    LibelleMotifRejet: {v for v, _ in MotifRejet.choices},
    LibelleCanalSaisie: {v for v, _ in CanalSaisie.choices},
    LibelleCritereRecherche: {v for v, _ in CritereRecherche.choices},
    LibelleTypeCertificat: {v for v, _ in TypeCertificat.choices},
}
