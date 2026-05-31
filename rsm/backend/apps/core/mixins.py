"""
Mixin de validité temporelle — art. 79, TDR § 4.3.

Aucune entité métier couverte par l'article 79 ne peut être supprimée.
Les actes de modification ou de radiation n'éteignent pas les
enregistrements : ils les **désactivent** avec date de fin et raison.

Ce mixin est utilisé par :
- ``apps.biens.BienGreve`` (pour « retirer » un bien grevé) ;
- ``apps.inscriptions.RoleInscriptionPartie`` (pour « retirer » une
  partie d'un rôle donné sur une inscription).

Le champ ``actif=True`` correspond à l'état « en cours de validité » ;
``actif=False`` désigne un enregistrement désactivé (mais jamais
supprimé). La paire ``date_fin_validite`` / ``raison_fin`` permet à
l'auditeur de retracer la chronologie complète.
"""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class ValiditeTemporelle(models.Model):
    """Durée de vie logique d'une entité métier (pas de suppression physique)."""

    actif = models.BooleanField(
        _("Actif"), default=True, db_index=True,
        help_text=_(
            "Un enregistrement inactif reste conservé (art. 79) mais "
            "n'apparaît plus au fichier public comme faisant partie de "
            "l'inscription en cours."
        ),
    )
    date_fin_validite = models.DateTimeField(
        _("Fin de validité"), null=True, blank=True,
    )
    raison_fin = models.CharField(
        _("Raison de fin de validité"),
        max_length=255, blank=True,
        help_text=_(
            "Référence métier (ex. ``modification.N°``, ``radiation.N°``) "
            "à rapprocher du journal d'audit."
        ),
    )

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError(
            "Suppression interdite (art. 79). Utilisez la désactivation "
            "via un acte métier tracé (modification / radiation)."
        )
