"""
Demandes de radiation — article 92.

Contenu obligatoire du bordereau (art. 92 alinéa 1) :
- numéro de l'inscription initiale ;
- nom, prénom, adresse du domicile ;
- le cas échéant, numéro d'immatriculation au RC du constituant.

Pièces jointes possibles (art. 92 alinéa 1 in fine) :
- acte authentique ou sous seing privé portant consentement à la radiation ;
- copie du jugement reconnaissant l'intérêt légitime du demandeur.

Après enregistrement de la radiation, les informations sont conservées au
fichier public jusqu'à la date d'expiration de l'inscription avec mention
« radiée ». Après expiration, elles sont transférées au fichier général.
"""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import ActeurTrace, Horodatage


class FondementRadiation(models.TextChoices):
    CONSENTEMENT = "consentement", _("Consentement à la radiation (acte authentique ou sous seing privé)")
    JUGEMENT = "jugement", _("Décision judiciaire (art. 92)")
    REQUERANT_ORIGINAL = "requerant_original", _(
        "Radiation par la personne ayant procédé à l'inscription"
    )


class StatutDemandeRadiation(models.TextChoices):
    RECUE = "recue", _("Reçue")
    REJETEE = "rejetee", _("Rejetée")
    APPLIQUEE = "appliquee", _("Appliquée")


class DemandeRadiation(Horodatage, ActeurTrace):
    inscription = models.ForeignKey(
        "inscriptions.Inscription",
        verbose_name=_("Inscription"),
        on_delete=models.PROTECT,
        related_name="demandes_radiation",
    )
    fondement = models.CharField(
        _("Fondement (art. 92)"),
        max_length=32, choices=FondementRadiation.choices,
    )
    statut = models.CharField(
        _("Statut"), max_length=16,
        choices=StatutDemandeRadiation.choices,
        default=StatutDemandeRadiation.RECUE,
    )
    motif_refus = models.CharField(_("Motif de refus"), max_length=255, blank=True)
    applique_le = models.DateTimeField(_("Appliquée le"), null=True, blank=True)

    # Champs recopiant les énonciations du bordereau de radiation (art. 92).
    nom_constituant = models.CharField(_("Nom du constituant"), max_length=150, blank=True)
    prenom_constituant = models.CharField(_("Prénom du constituant"), max_length=150, blank=True)
    denomination_constituant = models.CharField(
        _("Dénomination sociale du constituant"), max_length=255, blank=True,
    )
    adresse_constituant = models.TextField(_("Adresse du constituant"), blank=True)
    numero_rc_constituant = models.CharField(
        _("N° RC du constituant (si applicable)"), max_length=64, blank=True,
    )

    class Meta:
        verbose_name = _("Demande de radiation")
        verbose_name_plural = _("Demandes de radiation")
        ordering = ("-cree_le",)
