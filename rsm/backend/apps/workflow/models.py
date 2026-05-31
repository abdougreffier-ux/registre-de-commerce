"""
Traces d'historique des transitions de statut.

⚠️ Distinct du journal d'audit (``apps.audit``) : le journal d'audit consigne
TOUTES les actions (technique + métier), tandis que l'historique de statut
est spécifiquement attaché à une inscription et expose, pour le greffier et
l'auditeur, la trajectoire complète de chaque dossier.

Principes :
- Historisation sans écrasement (§ 4.3, art. 79).
- Chaque transition conserve : état avant, état après, acteur, horodatage,
  événement déclencheur, articles fondateurs.
- Aucune modification ni suppression d'une ligne n'est autorisée.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.workflow.statuts import StatutInscription


class TransitionStatut(models.Model):
    """
    Ligne d'historique d'une transition de statut sur une inscription.

    Chaque inscription (``apps.inscriptions.Inscription``) est référencée
    via une clé naturelle (``numero_inscription``) afin de préserver
    l'indépendance du module workflow vis-à-vis des tables métier.
    """

    numero_inscription = models.CharField(
        _("Numéro d'inscription concerné"),
        max_length=64, db_index=True,
    )
    statut_avant = models.CharField(
        _("Statut avant"),
        max_length=32, choices=StatutInscription.choices,
        blank=True,
        help_text=_(
            "Vide pour la première transition (création de la demande)."
        ),
    )
    statut_apres = models.CharField(
        _("Statut après"),
        max_length=32, choices=StatutInscription.choices,
    )
    evenement = models.CharField(_("Événement déclencheur"), max_length=64)
    articles_fondateurs = models.CharField(
        _("Articles fondateurs"), max_length=64,
        help_text=_("Ex. ``art. 85, 86``."),
    )
    motif = models.CharField(_("Motif / justification"), max_length=255, blank=True)
    instant = models.DateTimeField(_("Instant"), db_index=True)
    acteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Acteur"),
        on_delete=models.PROTECT,
        related_name="+",
        null=True, blank=True,
        help_text=_(
            "Nul pour les transitions automatiques (ex. expiration)."
        ),
    )
    acteur_role = models.CharField(
        _("Rôle applicatif actif"), max_length=48, blank=True,
    )
    automatique = models.BooleanField(_("Transition automatique"), default=False)

    class Meta:
        verbose_name = _("Transition de statut")
        verbose_name_plural = _("Historique des transitions")
        ordering = ("-instant", "-id")
        indexes = [
            models.Index(fields=["numero_inscription", "instant"]),
        ]

    def save(self, *args, **kwargs):  # noqa: D401
        if self.pk is not None:
            raise PermissionError(
                "L'historique des transitions est append-only (art. 79)."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError(
            "Suppression d'une transition interdite (art. 79)."
        )

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"[{self.instant:%Y-%m-%d %H:%M:%S}] "
            f"{self.numero_inscription} : {self.statut_avant} → {self.statut_apres}"
        )
