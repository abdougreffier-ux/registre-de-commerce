"""
Extractions statistiques — article 82.

Le greffe détient le monopole de la production et de la diffusion des
statistiques relatives aux sûretés mobilières. Ce modèle enregistre
chaque extraction, avec l'acteur, l'instant, le périmètre et le résultat,
afin que l'auditeur puisse s'assurer qu'aucune production n'a eu lieu en
dehors de ce monopole.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ExtractionStatistique(models.Model):
    instant = models.DateTimeField(_("Instant de l'extraction"), auto_now_add=True)
    producteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Producteur (rôle Greffe)"),
        on_delete=models.PROTECT, related_name="+",
    )
    perimetre = models.JSONField(
        _("Périmètre demandé"), default=dict,
        help_text=_(
            "Critères d'agrégation (période, nature de droit, canal, etc.)."
        ),
    )
    resultat = models.JSONField(_("Résultat"), default=dict)

    class Meta:
        verbose_name = _("Extraction statistique (art. 82)")
        verbose_name_plural = _("Extractions statistiques (art. 82)")
        ordering = ("-instant",)

    def save(self, *args, **kwargs):  # noqa: D401
        if self.pk is not None:
            raise PermissionError(
                "Les extractions statistiques sont immuables (art. 79, 82)."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError("Suppression interdite.")
