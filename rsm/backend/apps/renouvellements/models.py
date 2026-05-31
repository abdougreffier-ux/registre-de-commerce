"""
Demandes de renouvellement — article 91.

Règle impérative :
- « le renouvellement est possible à tout moment avant l'expiration de la
  période d'effet en cours » (art. 91).
- l'effet est une prorogation pour une durée égale à la durée initiale,
  décomptée à partir de la date à laquelle la période en cours aurait expiré.
- toute demande reçue APRÈS l'expiration est refusée et motivée (§ 4.2.3).

Hypothèse signalée TDR § 9.3 :
- « durée initiale » s'entend comme la durée fixée lors de l'inscription
  initiale et NON comme la durée résultant d'un renouvellement antérieur.
"""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import ActeurTrace, Horodatage


class StatutDemandeRenouvellement(models.TextChoices):
    RECUE = "recue", _("Reçue")
    REJETEE = "rejetee", _("Rejetée (hors délai — art. 91)")
    APPLIQUEE = "appliquee", _("Appliquée")


class DemandeRenouvellement(Horodatage, ActeurTrace):
    inscription = models.ForeignKey(
        "inscriptions.Inscription",
        verbose_name=_("Inscription"),
        on_delete=models.PROTECT,
        related_name="demandes_renouvellement",
    )
    statut = models.CharField(
        _("Statut"), max_length=16,
        choices=StatutDemandeRenouvellement.choices,
        default=StatutDemandeRenouvellement.RECUE,
    )
    motif_refus = models.CharField(_("Motif de refus"), max_length=255, blank=True)

    ancienne_date_expiration = models.DateField(
        _("Ancienne date d'expiration"), null=True, blank=True,
    )
    nouvelle_date_expiration = models.DateField(
        _("Nouvelle date d'expiration"), null=True, blank=True,
    )
    applique_le = models.DateTimeField(_("Appliquée le"), null=True, blank=True)

    class Meta:
        verbose_name = _("Demande de renouvellement")
        verbose_name_plural = _("Demandes de renouvellement")
        ordering = ("-cree_le",)
