"""
Modèles abstraits transverses du système RSM.

Principes imposés par le TDR :
- § 6.3 : stockage neutre de la langue pour les données à valeur juridique ;
  stockage explicite (fr, ar) pour les champs descriptifs reconnus multilingues.
- Art. 79 : aucune information régulièrement enregistrée ne peut être supprimée.
- § 5.2 : toute modification est tracée, datée et attribuée.

Les mixins de ce module expriment ces invariants au niveau ORM.
"""
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class LangueFaisantFoi(models.TextChoices):
    """
    Lorsqu'un texte multilingue n'est renseigné que dans une seule langue,
    la langue faisant foi doit être mentionnée explicitement (§ 7.4 du TDR).
    """

    FR = "fr", _("Français")
    AR = "ar", _("Arabe")
    EQUIVALENT = "equ", _("Équivalent établi FR et AR")


class Horodatage(models.Model):
    """
    Horodatage technique (création, modification).

    ⚠️ ATTENTION — Ce champ NE constitue PAS l'horodatage opposable au sens
    de l'article 78. L'horodatage opposable, fondant la prise d'effet juridique,
    est produit par le Moteur d'horodatage (cf. app. ``workflow`` /
    app. ``inscriptions``), reposant sur une source de temps certifiée à
    arbitrer par le maître d'ouvrage.  [ZONE GELÉE § 5.1 TDR]
    """

    cree_le = models.DateTimeField(
        _("Créé le"), default=timezone.now, editable=False, db_index=True,
    )
    modifie_le = models.DateTimeField(_("Modifié le"), auto_now=True)

    class Meta:
        abstract = True


class ActeurTrace(models.Model):
    """Acteur technique ayant créé ou dernier modifié l'entité (§ 5.2)."""

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Créé par"),
        on_delete=models.PROTECT,
        related_name="+",
        null=True, blank=True, editable=False,
    )
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Modifié par"),
        on_delete=models.PROTECT,
        related_name="+",
        null=True, blank=True, editable=False,
    )

    class Meta:
        abstract = True


class Bilingue(models.Model):
    """
    Mixin des entités dont le libellé est intrinsèquement bilingue (§ 7.4).

    Les deux colonnes ``libelle_fr`` et ``libelle_ar`` existent systématiquement.
    Une au moins doit être renseignée. Lorsqu'une seule l'est, le champ
    ``langue_faisant_foi`` précise laquelle prévaut.

    Cette règle vaut pour TOUS les référentiels : types de sûretés, motifs de
    rejet, libellés de statuts, types de biens, intitulés de formulaires, etc.
    """

    libelle_fr = models.CharField(_("Libellé français"), max_length=255, blank=True)
    libelle_ar = models.CharField(_("Libellé arabe"), max_length=255, blank=True)
    langue_faisant_foi = models.CharField(
        _("Langue faisant foi"),
        max_length=3,
        choices=LangueFaisantFoi.choices,
        default=LangueFaisantFoi.EQUIVALENT,
        help_text=_(
            "Langue de référence lorsque les deux versions ne sont pas "
            "strictement équivalentes (§ 7.4 des TDR)."
        ),
    )

    class Meta:
        abstract = True

    def clean(self) -> None:
        super().clean()
        if not (self.libelle_fr or self.libelle_ar):
            raise ValidationError(
                _("Au moins une des versions (français ou arabe) doit être renseignée.")
            )
        if (
            self.libelle_fr
            and self.libelle_ar
            and self.langue_faisant_foi not in {LangueFaisantFoi.EQUIVALENT,
                                                LangueFaisantFoi.FR,
                                                LangueFaisantFoi.AR}
        ):
            raise ValidationError(_("Langue faisant foi invalide."))

    def libelle(self, langue: str | None = None) -> str:
        """Rend le libellé dans la langue demandée, avec repli documenté."""
        from django.utils.translation import get_language

        langue = (langue or get_language() or "fr").split("-")[0]
        if langue == "ar" and self.libelle_ar:
            return self.libelle_ar
        if langue == "fr" and self.libelle_fr:
            return self.libelle_fr
        # Repli explicite : on affiche la seule version disponible, jamais une
        # traduction inventée (§ 7.4).
        return self.libelle_fr or self.libelle_ar

    def __str__(self) -> str:  # pragma: no cover - affichage admin
        return self.libelle()


class DescriptionBilingue(models.Model):
    """
    Mixin pour un texte descriptif long bilingue (ex : description des biens
    grevés, motif d'une modification).

    Contrairement à :class:`Bilingue`, les deux colonnes peuvent rester vides
    initialement ; elles sont néanmoins présentées côte à côte à la saisie.
    """

    description_fr = models.TextField(_("Description (français)"), blank=True)
    description_ar = models.TextField(_("Description (arabe)"), blank=True)
    langue_faisant_foi_description = models.CharField(
        _("Langue faisant foi (description)"),
        max_length=3,
        choices=LangueFaisantFoi.choices,
        default=LangueFaisantFoi.EQUIVALENT,
    )

    class Meta:
        abstract = True


class ProtectionSuppression(models.Model):
    """
    Interdit la suppression physique au niveau ORM (art. 79).

    La suppression logique (flag) N'EST PAS prévue pour les entités métier
    couvertes par l'article 79. Elle peut exister, de manière très encadrée,
    pour les objets administratifs (ex : paramètre désactivé), mais jamais
    pour une inscription, modification, radiation ou trace d'audit.
    """

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):  # noqa: D401 - override explicite
        raise PermissionError(
            _(
                "Suppression interdite (article 79 du décret 2021-033). "
                "Seule une opération métier tracée peut modifier l'état."
            )
        )
