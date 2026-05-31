"""
Traces des recherches effectuées au RSM — articles 94 à 97.

Chaque recherche est tracée, même anonyme, afin :
- d'auditer la cohérence fichier public ↔ certificat de recherche à l'instant T
  (§ 4.2.5, point critique) ;
- d'alimenter les statistiques d'usage (uniquement pour le greffe, art. 82).

Les critères soumis sont conservés (JSON) ; l'instant de la recherche,
à la seconde, détermine la photographie du fichier public restituée.
"""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class RequeteRecherche(models.Model):
    instant = models.DateTimeField(_("Instant de la recherche"), db_index=True)
    criteres_soumis = models.JSONField(_("Critères soumis"), default=dict)
    nombre_resultats = models.PositiveIntegerField(_("Nombre de résultats"), default=0)
    adresse_ip = models.GenericIPAddressField(_("Adresse IP"), null=True, blank=True)
    user_agent = models.CharField(_("User-Agent"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Requête de recherche")
        verbose_name_plural = _("Requêtes de recherche")
        ordering = ("-instant",)

    def save(self, *args, **kwargs):  # noqa: D401
        if self.pk is not None:
            raise PermissionError(
                "Une requête de recherche est immuable une fois enregistrée."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError(
            "Suppression d'une trace de recherche interdite (art. 79)."
        )
