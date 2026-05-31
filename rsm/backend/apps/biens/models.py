"""
Biens grevés — article 85 et article 93.

Règles directement issues du texte :
- Art. 85 alinéa 3 : l'omission du numéro de série, du fabricant, du modèle
  ou de l'année d'un bien individualisé ne prive pas l'inscription d'effet
  dès lors que les biens sont décrits par ailleurs de manière suffisamment
  précise. → Ces champs NE SONT PAS bloquants à la saisie.
- Art. 93 : pour les biens porteurs de numéros de série, indexation
  additionnelle par numéro de série.
- Art. 79 : un bien « retiré » par une modification reste conservé en base
  (désactivation logique avec date de fin et raison — voir
  ``apps.core.mixins.ValiditeTemporelle``). Aucune suppression physique.

Catégories et champs spécifiques :
- Le document MO « Liste des catégories de biens et éléments de description »
  fixe une typologie de 18 catégories, chacune avec ses champs propres.
- Cette typologie est matérialisée par ``CategorieBien`` (versionnée) et
  les attributs spécifiques sont stockés dans ``BienGreve.attributs_specifiques``
  (JSON validé STRICTEMENT contre le schéma de la catégorie + version).
- Chaque inscription conserve la version exacte du schéma utilisé au dépôt
  (champ ``categorie_version_snapshot``) — non rétroactif.

Principe de langue :
- La description structurée (marque, modèle, numéro de série, année) est
  juridiquement neutre : elle est stockée dans un champ neutre unique.
- Les libellés des catégories et de leurs champs sont bilingues FR/AR.
"""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import ValiditeTemporelle
from apps.core.models import ActeurTrace, DescriptionBilingue, Horodatage


# --------------------------------------------------------------------------- #
# Catégories et schémas de champs                                             #
# --------------------------------------------------------------------------- #
class TypeChamp(models.TextChoices):
    """
    Types de champs admis dans le schéma d'une catégorie. Liste limitative.
    Tout type non listé est refusé par la validation.
    """

    TEXTE = "texte", _("Texte court")
    TEXTE_LONG = "texte_long", _("Texte long")
    NOMBRE = "nombre", _("Nombre")
    MONTANT = "montant", _("Montant")
    DATE = "date", _("Date")
    BOOLEEN = "booleen", _("Booléen (oui/non)")


class CategorieBien(Horodatage, ActeurTrace):
    """
    Catégorie de bien grevable, telle que définie par le MO.

    Versionnage :
    - L'identifiant ``cle`` reste stable d'une version à l'autre
      (ex. ``vehicules``, ``stocks_marchandises``).
    - Chaque modification du schéma de champs incrémente ``version`` et
      crée une **nouvelle ligne** ; les anciennes versions sont conservées.
    - Une nouvelle version ne s'applique pas rétroactivement : les biens
      déjà inscrits conservent la référence à la version utilisée au dépôt
      (``BienGreve.categorie_version_snapshot``).
    - Une version qui a déjà été utilisée (référencée par au moins un
      ``BienGreve``) est **immuable** et ne peut plus être modifiée.

    Schéma de champs :
    - ``schema_champs`` est une liste ordonnée de descripteurs de champs.
    - Chaque descripteur :
        {
          "cle": "numero_chassis",
          "type": "texte" | "texte_long" | "nombre" | "montant" | "date" | "booleen",
          "obligatoire": true | false,
          "libelle_fr": "Numéro de châssis",
          "libelle_ar": "رقم الهيكل"
        }
    - Validation des données : voir ``apps.biens.services.valider_attributs``.
    """

    cle = models.CharField(
        _("Clé technique stable"),
        max_length=64, db_index=True,
        help_text=_(
            "Identifiant slug stable d'une version à l'autre "
            "(ex. ``vehicules``, ``stocks_marchandises``)."
        ),
    )
    version = models.PositiveIntegerField(
        _("Version"), default=1,
        help_text=_(
            "Incrémentée à chaque modification du schéma. Versions "
            "antérieures conservées (non rétroactivité)."
        ),
    )
    libelle_fr = models.CharField(_("Libellé (FR)"), max_length=255)
    libelle_ar = models.CharField(_("Libellé (AR)"), max_length=255)
    description_fr = models.TextField(_("Description (FR)"), blank=True)
    description_ar = models.TextField(_("Description (AR)"), blank=True)

    schema_champs = models.JSONField(
        _("Schéma des champs spécifiques"), default=list,
        help_text=_(
            "Liste ordonnée de descripteurs de champs. Chaque descripteur "
            "porte cle, type, obligatoire, libelle_fr, libelle_ar."
        ),
    )

    affichage_observations = models.BooleanField(
        _("Champ « Observations » affiché"), default=True,
        help_text=_(
            "Le document MO précise les catégories pour lesquelles le "
            "champ Observations doit être affiché. Lorsque False, le "
            "champ n'est pas exposé à la saisie."
        ),
    )

    actif = models.BooleanField(
        _("Version active"), default=True,
        help_text=_(
            "Une seule version peut être active à la fois pour une cle "
            "donnée. Les versions précédentes restent disponibles pour "
            "lecture des anciens biens."
        ),
    )

    class Meta:
        verbose_name = _("Catégorie de bien")
        verbose_name_plural = _("Catégories de biens")
        ordering = ("libelle_fr", "version")
        constraints = [
            models.UniqueConstraint(
                fields=["cle", "version"], name="unique_categorie_cle_version",
            ),
            models.UniqueConstraint(
                fields=["cle"], condition=models.Q(actif=True),
                name="unique_categorie_active_par_cle",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.libelle_fr} (v{self.version})"

    @property
    def est_utilisee(self) -> bool:
        """Vrai si au moins un BienGreve référence cette version."""
        return BienGreve.objects.filter(
            categorie_cle=self.cle,
            categorie_version_snapshot=self.version,
        ).exists()


# --------------------------------------------------------------------------- #
# Bien grevé                                                                  #
# --------------------------------------------------------------------------- #
class BienActifManager(models.Manager):
    """Ne retourne que les biens actuellement actifs (fichier public)."""

    def get_queryset(self):
        return super().get_queryset().filter(actif=True)


class BienGreve(Horodatage, ActeurTrace, DescriptionBilingue, ValiditeTemporelle):
    """
    Bien grevé par une sûreté.

    Champs neutres linguistiquement (art. 85 al. 3) — non bloquants :
    ``marque``, ``modele``, ``numero_serie``, ``annee``.

    Catégorie + attributs spécifiques :
    - ``categorie_cle`` : clé stable de la catégorie choisie (ex.
      ``vehicules``).
    - ``categorie_version_snapshot`` : version du schéma utilisée à la
      saisie. Les inscriptions futures peuvent utiliser une version
      ultérieure ; cette inscription-ci reste figée sur sa version.
    - ``attributs_specifiques`` : dictionnaire JSON dont les clés sont
      strictement celles déclarées par le schéma de la catégorie+version
      ci-dessus. Toute clé non prévue est rejetée par la validation
      (``apps.biens.services.valider_attributs``).

    Un bien « retiré » par une modification garde ``actif=False`` et
    demeure en base — conformément à l'article 79.
    """

    # Champs structurés neutres linguistiquement (art. 85 al. 3).
    marque = models.CharField(_("Marque / fabricant"), max_length=128, blank=True)
    modele = models.CharField(_("Modèle"), max_length=128, blank=True)
    annee = models.PositiveIntegerField(_("Année"), null=True, blank=True)
    numero_serie = models.CharField(
        _("Numéro de série"),
        max_length=128, blank=True, db_index=True,
        help_text=_(
            "Article 93 — indexation additionnelle pour les biens porteurs d'un "
            "numéro de série."
        ),
    )

    # Catégorie + version (snapshot pour non-rétroactivité)
    categorie_cle = models.CharField(
        _("Catégorie (clé)"), max_length=64, blank=True, db_index=True,
    )
    categorie_version_snapshot = models.PositiveIntegerField(
        _("Version du schéma au dépôt"), default=0,
        help_text=_(
            "Version de la catégorie utilisée à la saisie. Garantit la "
            "non-rétroactivité : aucune mise à jour de schéma ne modifie "
            "les biens déjà inscrits."
        ),
    )
    attributs_specifiques = models.JSONField(
        _("Attributs spécifiques"), default=dict, blank=True,
        help_text=_(
            "Dictionnaire {cle: valeur} validé contre le schéma de la "
            "catégorie+version ci-dessus. Toute clé non prévue est rejetée."
        ),
    )
    observations = models.TextField(
        _("Observations"), blank=True,
        help_text=_(
            "Champ libre, présent uniquement pour les catégories dont "
            "``CategorieBien.affichage_observations`` vaut True."
        ),
    )

    # Liens métier
    inscription = models.ForeignKey(
        "inscriptions.Inscription",
        verbose_name=_("Inscription rattachée"),
        on_delete=models.PROTECT,
        related_name="biens",
    )

    objects = models.Manager()     # Accès intégral (historique compris).
    actifs = BienActifManager()    # Vue « biens actuellement grevés ».

    class Meta:
        verbose_name = _("Bien grevé")
        verbose_name_plural = _("Biens grevés")
        indexes = [
            models.Index(fields=["numero_serie"]),
            models.Index(fields=["marque", "modele"]),
            models.Index(fields=["inscription", "actif"]),
            models.Index(fields=["categorie_cle", "categorie_version_snapshot"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        base = self.description_fr or self.description_ar or self.modele or ""
        if self.numero_serie:
            return f"{base} [{self.numero_serie}]".strip()
        return base or f"Bien grevé #{self.pk}"
