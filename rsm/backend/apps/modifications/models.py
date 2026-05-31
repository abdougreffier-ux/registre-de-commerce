"""
Demandes de modification — articles 88, 89, 90.

Règles cardinales (art. 88) :
- le formulaire vise obligatoirement : champ concerné, numéro de
  l'inscription initiale, objet de la modification, informations ajoutées /
  modifiées / supprimées, signatures du créancier et du constituant ;
- une modification visant à supprimer l'ensemble des constituants, des
  créanciers garantis ou des biens grevés sans en désigner de nouveaux est
  sans effet (art. 88 dernier alinéa) : le système REFUSE et motive le refus.

Art. 90 : prise d'effet à la date et à l'heure de saisie ; aucun effet sur
la durée de l'inscription initiale sauf prorogation expresse — cas traité
par le module ``renouvellements``.

Art. 93 : la modification est systématiquement associée au numéro de
l'inscription initiale (champ ``inscription``).
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import ActeurTrace, DescriptionBilingue, Horodatage


class StatutDemandeModification(models.TextChoices):
    RECUE = "recue", _("Reçue")
    REJETEE = "rejetee", _("Rejetée (art. 80 ou effet utile art. 88)")
    APPLIQUEE = "appliquee", _("Appliquée")


class MotifRefusModification(models.TextChoices):
    """
    Motifs LIMITATIFS de refus d'application d'une modification.

    Toute valeur ici correspond à un fondement exprès du décret ou du TDR.
    Aucun motif « divers » ni « fourre-tout » n'est admis. Les libellés
    sont bilingues (FR ici, AR fourni par le référentiel de traductions
    Django — même traitement que toute autre énumération du système).
    """

    # Art. 88 dernier alinéa + § 4.3 TDR — état final vidant les parties,
    # les créanciers garantis ou les biens grevés sans remplacement.
    ETAT_FINAL_CONSTITUANT_ABSENT = (
        "etat_final_constituant_absent",
        _("État final sans constituant actif (art. 88 dernier al.)"),
    )
    ETAT_FINAL_CREANCIER_ABSENT = (
        "etat_final_creancier_absent",
        _("État final sans créancier garanti actif (art. 88 dernier al.)"),
    )
    ETAT_FINAL_BIEN_ABSENT = (
        "etat_final_bien_absent",
        _("État final sans bien grevé actif (art. 88 dernier al.)"),
    )
    # Art. 88 — accord du créancier et du constituant obligatoire.
    ACCORDS_MANQUANTS = (
        "accords_manquants",
        _("Accords du créancier et/ou du constituant non confirmés (art. 88)"),
    )
    # § 4.3 TDR — une modification ne peut s'appliquer qu'à une
    # inscription en cours de validité.
    STATUT_INSCRIPTION_INCOMPATIBLE = (
        "statut_inscription_incompatible",
        _("Inscription non en cours de validité (§ 4.3 TDR)"),
    )
    # Schéma strict du diff (art. 78 al. 4, art. 88, art. 90 al. 2) :
    # clés hors schéma, champs jamais modifiables, nature hors liste, etc.
    DIFF_INVALIDE = (
        "diff_invalide",
        _("Diff non conforme au schéma strict (art. 78 / 88 / 90 al. 2)"),
    )
    # Pas de diff = pas d'objet de modification.
    DIFF_VIDE = (
        "diff_vide",
        _("Aucune modification effective proposée"),
    )
    # Une demande déjà appliquée ou déjà rejetée n'est pas ré-applicable.
    DEMANDE_NON_APPLICABLE = (
        "demande_non_applicable",
        _("Demande déjà traitée (appliquée ou rejetée)"),
    )


class DemandeModification(Horodatage, ActeurTrace, DescriptionBilingue):
    """
    Demande de modification d'une inscription en cours.

    Le contenu de la modification est exprimé sous forme d'un « diff »
    structuré (``diff_propose``) que le service d'application interprète
    pour mettre à jour l'inscription concernée.

    Schéma strict du diff — voir ``apps.modifications.diff.DiffModification``.
    Toute clé non prévue provoque le rejet immédiat de la demande.
    """

    inscription = models.ForeignKey(
        "inscriptions.Inscription",
        verbose_name=_("Inscription initiale"),
        on_delete=models.PROTECT,
        related_name="demandes_modification",
        help_text=_(
            "Article 93 — la modification est rattachée au numéro de "
            "l'inscription initiale."
        ),
    )
    objet_modification_fr = models.TextField(_("Objet de la modification (FR)"))
    objet_modification_ar = models.TextField(_("Objet de la modification (AR)"))

    #: Structure JSON STRICTE décrivant les champs ajoutés / modifiés /
    #: retirés. Seules les clés ``parties``, ``biens`` et ``scalaires``
    #: sont autorisées. Voir ``apps.modifications.diff``.
    diff_propose = models.JSONField(_("Différentiel proposé"), default=dict)

    statut = models.CharField(
        _("Statut"), max_length=16,
        choices=StatutDemandeModification.choices,
        default=StatutDemandeModification.RECUE,
    )
    #: Motif structuré (clé limitative), dépendant de l'énumération
    #: ``MotifRefusModification``. Un seul motif cardinal par rejet.
    motif_refus_code = models.CharField(
        _("Motif de refus (clé limitative)"),
        max_length=48, blank=True,
        choices=[(m.value, m.label) for m in MotifRefusModification],
    )
    motif_refus = models.CharField(
        _("Motif de refus — détail"), max_length=255, blank=True,
        help_text=_(
            "Précision humaine, facultative. La référence juridique "
            "opposable est portée par ``motif_refus_code``."
        ),
    )
    applique_le = models.DateTimeField(_("Appliquée le"), null=True, blank=True)

    # Accord des parties — ZONE GELÉE pour la signature électronique.
    accord_createur_confirme = models.BooleanField(
        _("Accord du créancier confirmé"), default=False,
        help_text=_("Signature électronique GELÉE (§ 5.1, art. 88)."),
    )
    accord_constituant_confirme = models.BooleanField(
        _("Accord du constituant confirmé"), default=False,
    )

    class Meta:
        verbose_name = _("Demande de modification")
        verbose_name_plural = _("Demandes de modification")
        ordering = ("-cree_le",)

    def __str__(self) -> str:  # pragma: no cover
        return f"Modification de {self.inscription}"


class SnapshotInscription(models.Model):
    """
    Photographie canonique d'une inscription à un instant donné.

    Article 79 — conservation intégrale. Un snapshot est créé AVANT et
    APRÈS chaque modification, renouvellement et radiation, de sorte que
    toute la trajectoire de l'inscription soit reconstituable.

    ⚠️ Append-only : toute modification ou suppression est refusée.

    ``empreinte`` : scellement de la charge utile (mode STUB actuel —
    zone gelée § 5.1 TDR). Permet de détecter toute altération future,
    sans être opposable en l'état.
    """

    class Evenement(models.TextChoices):
        DEMANDE_RECUE = "demande_recue", _("Demande reçue (avant application)")
        VALIDATION_INSCRIPTION = "validation_inscription", _("Après validation de l'inscription")
        MODIFICATION_AVANT = "modification_avant", _("Avant modification (art. 88)")
        MODIFICATION_APRES = "modification_apres", _("Après modification (art. 88)")
        RENOUVELLEMENT_AVANT = "renouvellement_avant", _("Avant renouvellement (art. 91)")
        RENOUVELLEMENT_APRES = "renouvellement_apres", _("Après renouvellement (art. 91)")
        RADIATION_AVANT = "radiation_avant", _("Avant radiation (art. 92)")
        RADIATION_APRES = "radiation_apres", _("Après radiation (art. 92)")

    inscription = models.ForeignKey(
        "inscriptions.Inscription",
        verbose_name=_("Inscription"),
        on_delete=models.PROTECT,
        related_name="snapshots",
    )
    evenement = models.CharField(
        _("Événement déclencheur"),
        max_length=48, choices=Evenement.choices, db_index=True,
    )
    demande_modification = models.ForeignKey(
        DemandeModification,
        verbose_name=_("Demande de modification rattachée"),
        on_delete=models.PROTECT,
        related_name="snapshots",
        null=True, blank=True,
    )
    instant = models.DateTimeField(_("Instant"), db_index=True)
    contenu = models.JSONField(_("Contenu canonique"))
    empreinte = models.CharField(
        _("Empreinte de scellement"),
        max_length=128,
        help_text=_("SHA-256 du contenu canonique. Mode STUB — § 5.1 TDR."),
    )
    acteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Acteur"),
        on_delete=models.PROTECT,
        related_name="+",
        null=True, blank=True,
    )

    class Meta:
        verbose_name = _("Snapshot d'inscription")
        verbose_name_plural = _("Snapshots d'inscription")
        ordering = ("inscription_id", "instant", "id")
        indexes = [
            models.Index(fields=["inscription", "evenement"]),
        ]

    def save(self, *args, **kwargs):  # noqa: D401
        if self.pk is not None:
            raise PermissionError(
                "Les snapshots sont append-only (art. 79)."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError(
            "Suppression d'un snapshot interdite (art. 79)."
        )
