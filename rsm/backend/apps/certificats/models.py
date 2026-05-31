"""
Certificats — STRUCTURE SEULEMENT. Production probante GELÉE.

⚠️ ZONE GELÉE — TDR § 3.1, § 6.2, art. 78, 86, 97.

Les cinq types de certificats prévus par le TDR sont modélisés ici
pour permettre la construction progressive de la chaîne ; leur **émission
comme documents officiels opposables** reste conditionnée à :
- l'arbitrage de la politique cryptographique (scellement, signature) ;
- l'arbitrage de la source de temps (horodatage opposable) ;
- l'arbitrage de la charte graphique bilingue des documents officiels ;
- la validation du glossaire juridique bilingue (§ 7.3 du TDR).

Tant que ces arbitrages ne sont pas tranchés, tout certificat émis est
étiqueté ``probant=False`` et porte la mention « aperçu non opposable ».
"""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import TypeCertificat
from apps.core.models import ActeurTrace, Horodatage


class Certificat(Horodatage, ActeurTrace):
    type_certificat = models.CharField(
        _("Type de certificat"),
        max_length=32, choices=TypeCertificat.choices,
    )
    inscription = models.ForeignKey(
        "inscriptions.Inscription",
        verbose_name=_("Inscription associée"),
        on_delete=models.PROTECT,
        related_name="certificats",
        null=True, blank=True,
        help_text=_(
            "Facultatif pour les certificats de recherche, qui se rattachent "
            "à une requête de recherche."
        ),
    )
    requete_recherche = models.ForeignKey(
        "recherche.RequeteRecherche",
        verbose_name=_("Requête de recherche"),
        on_delete=models.PROTECT,
        related_name="certificats",
        null=True, blank=True,
    )
    langue_generation = models.CharField(
        _("Langue de génération"), max_length=8,
        choices=[("fr", "Français"), ("ar", "Arabe"), ("fr-ar", "Bilingue")],
        default="fr-ar",
    )
    probant = models.BooleanField(
        _("Probant (art. 97)"),
        default=False,
        help_text=_(
            "Vaut ``True`` UNIQUEMENT si les conditions de scellement, "
            "d'horodatage et de signature sont réunies (zones gelées)."
        ),
    )
    empreinte = models.CharField(
        _("Empreinte de scellement"),
        max_length=128, blank=True,
    )
    contenu_json = models.JSONField(
        _("Contenu structuré"), default=dict,
        help_text=_(
            "Données du certificat au format neutre (§ 6.3) — sert de source "
            "canonique pour la génération PDF/A bilingue."
        ),
    )
    fichier_pdf = models.FileField(
        _("Fichier PDF"), upload_to="certificats/%Y/%m/", blank=True,
    )

    class Meta:
        verbose_name = _("Certificat")
        verbose_name_plural = _("Certificats")
        ordering = ("-cree_le",)
