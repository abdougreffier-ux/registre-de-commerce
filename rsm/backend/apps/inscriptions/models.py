"""
Modèle d'inscription — cœur du RSM.

Fondements juridiques :
- Art. 78 : canaux de saisie, ordre d'arrivée, horodatage à la seconde,
  numéro d'ordre et prise d'effet.
- Art. 79 : conservation pérenne.
- Art. 80 : motifs limitatifs de rejet.
- Art. 85 : contenu obligatoire du formulaire d'inscription.
- Art. 86 : régime déclaratif (pas de vérification des énonciations).
- Art. 87 : prise d'effet à la saisie.
- Art. 93 : indexation par nom du constituant et par numéro de série.

Principe architectural retenu (TDR § 6.3) : un seul objet ``Inscription``
porte l'ensemble des statuts (Reçue → En contrôle de forme → Inscrite ou
Rejetée → …). Le numéro d'ordre (art. 78 alinéa 4) n'est attribué que lors
de la transition vers « Inscrite ». Les rejets sont conservés en base et
tracés au journal d'audit (§ 4.2.1).
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import (
    CanalSaisie,
    FichierRegistre,
    MotifRejet,
    NatureConvention,
    TypeSurete,
)
from apps.core.models import ActeurTrace, DescriptionBilingue, Horodatage
from apps.workflow.statuts import (
    STATUTS_FICHIER_PUBLIC,
    STATUTS_PRE_VALIDATION,
    StatutInscription,
)


class SequenceNumeroOrdre(models.Model):
    """
    Compteur monotone servant à produire le numéro d'ordre séquentiel de
    l'article 78 alinéa 4.

    Garanties :
    - Une seule ligne en base (``pk=1``), accédée en ``SELECT … FOR UPDATE``
      par le service d'attribution afin de sérialiser les requêtes.
    - Le compteur ne décroît jamais ; un numéro d'ordre n'est jamais
      réutilisé (cf. critère § 10.1 du TDR).
    """

    prochaine_valeur = models.PositiveBigIntegerField(
        _("Prochaine valeur"), default=1,
    )

    class Meta:
        verbose_name = _("Séquence du numéro d'ordre (art. 78)")
        verbose_name_plural = _("Séquence du numéro d'ordre (art. 78)")

    def save(self, *args, **kwargs):  # noqa: D401
        # Interdiction de modifier manuellement une séquence existante :
        # la mise à jour passe par le service
        # ``inscriptions.services.attribuer_numero_ordre``. Le premier
        # ``INSERT`` (création de la ligne pk=1) reste autorisé,
        # indépendamment du ``pk`` fourni en kwargs.
        if (
            kwargs.pop("_force", False) is not True
            and not self._state.adding
        ):
            raise PermissionError(
                "La séquence d'ordre ne peut être modifiée que par le service "
                "d'attribution (art. 78)."
            )
        super().save(*args, **kwargs)


class Inscription(Horodatage, ActeurTrace):
    """
    Inscription au RSM.

    Une Inscription peut représenter :
    - une demande initialement reçue (statut ``RECUE``) ;
    - une inscription en cours (``INSCRITE``, ``MODIFIEE``, ``RENOUVELEE``,
      ``RADIEE``) ;
    - une inscription expirée ou archivée (``EXPIREE``, ``ARCHIVEE``) ;
    - un rejet (``REJETEE``) — conservé en base pour traçabilité même si
      non publié au fichier public (§ 4.3).
    """

    # --- Identification ---------------------------------------------------- #
    reference_demande = models.UUIDField(
        _("Référence de la demande"),
        default=uuid.uuid4, unique=True, editable=False,
        help_text=_(
            "Identifiant opaque attribué à la réception, visible du "
            "déposant avant l'attribution du numéro d'ordre."
        ),
    )
    numero_ordre = models.CharField(
        _("Numéro d'ordre (art. 78)"),
        max_length=64, unique=True, null=True, blank=True,
        help_text=_(
            "Attribué à la transition vers « Inscrite ». Format : "
            "``NNNNNN-AAAAMMJJHHMMSS``. Une fois attribué, immuable."
        ),
    )

    # --- Canal et horodatages --------------------------------------------- #
    canal_saisie = models.CharField(
        _("Canal de saisie (art. 78)"),
        max_length=32, choices=CanalSaisie.choices,
    )
    instant_arrivee = models.DateTimeField(
        _("Instant d'arrivée (art. 78 al. 2)"),
        db_index=True,
        help_text=_(
            "Date et heure d'arrivée au point d'entrée retenu ; elle "
            "détermine l'ordre d'arrivée. NE SE CONFOND PAS avec l'instant "
            "de saisie opposable (art. 78 al. 3)."
        ),
    )
    instant_saisie_opposable = models.DateTimeField(
        _("Instant de saisie dans le fichier public (art. 78, 87)"),
        null=True, blank=True, db_index=True,
        help_text=_(
            "Prise d'effet juridique. ⚠️ ZONE GELÉE § 5.1 — l'horodatage "
            "opposable définitif dépend de la source de temps arbitrée."
        ),
    )

    # --- Statut ------------------------------------------------------------ #
    statut = models.CharField(
        _("Statut"),
        max_length=32, choices=StatutInscription.choices,
        default=StatutInscription.RECUE, db_index=True,
    )
    mention_radiee = models.BooleanField(
        _("Mention « radiée » au fichier public"),
        default=False,
        help_text=_(
            "Article 92 alinéa 2 : après radiation, les informations sont "
            "conservées au fichier public jusqu'à la date d'expiration avec "
            "mention « radiée »."
        ),
    )
    fichier_actuel = models.CharField(
        _("Fichier de rattachement (art. 77)"),
        max_length=16, choices=FichierRegistre.choices,
        default=FichierRegistre.PUBLIC, db_index=True,
    )

    # --- Contenu de l'inscription (art. 85) ------------------------------- #
    type_surete = models.CharField(
        _("Type de sûreté objet de l'inscription"),
        max_length=32, choices=TypeSurete.choices,
        default=TypeSurete.DEPOT_SURETE, db_index=True,
        help_text=_(
            "Distinction métier entre les 4 parcours de dépôt : sûreté "
            "générique (art. 76), privilège du vendeur, vente avec "
            "réserve de propriété, crédit-bail. Les éventuelles données "
            "spécifiques au type sont conservées dans "
            "``donnees_specifiques``."
        ),
    )
    donnees_specifiques = models.JSONField(
        _("Données spécifiques au type de sûreté"),
        default=dict, blank=True,
        help_text=_(
            "Dictionnaire des champs spécifiques au type_surete déposé "
            "(ex. date du contrat de vente, prix total, durée, etc.). "
            "Forme libre côté backend (régime déclaratif art. 86) ; "
            "validé en amont par les formulaires."
        ),
    )
    nature_droit = models.CharField(
        _("Nature du droit / sûreté (art. 85)"),
        max_length=48,
        help_text=_(
            "Référence à une clé de ``referentiels.LibelleNatureDroit`` "
            "active au moment du dépôt. Liste paramétrable par le greffier "
            "(non rétroactif : les inscriptions existantes restent valides "
            "même si une nature est ultérieurement désactivée)."
        ),
    )
    somme_garantie = models.DecimalField(
        _("Somme garantie (art. 85)"),
        max_digits=18, decimal_places=2, null=True, blank=True,
    )
    montant_en_lettres_fr = models.CharField(
        _("Montant en lettres (FR)"),
        max_length=512, blank=True,
        help_text=_(
            "Conversion en lettres du montant garanti, langue française. "
            "Calculée par le système ; conservée pour les certificats."
        ),
    )
    montant_en_lettres_ar = models.CharField(
        _("Montant en lettres (AR)"),
        max_length=512, blank=True,
        help_text=_("Idem en langue arabe."),
    )
    monnaie = models.CharField(
        _("Monnaie"),
        max_length=8, blank=True,
        help_text=_(
            "Code ISO 4217 (ex. ``MRU``). Le code choisi est documenté par "
            "le maître d'ouvrage."
        ),
    )
    duree_en_jours = models.PositiveIntegerField(
        _("Durée de l'inscription en jours (art. 85)"),
        help_text=_(
            "Durée de l'inscription exprimée en jours. Le texte ne fixe pas "
            "de borne (risque signalé TDR § 9.2) ; une limite paramétrable "
            "pourra être mise en œuvre après arbitrage du MO."
        ),
    )
    date_expiration = models.DateField(
        _("Date d'expiration"),
        help_text=_(
            "Date calculée à partir de l'instant de saisie opposable et de "
            "la durée déclarée ; prorogée en cas de renouvellement (art. 91)."
        ),
        null=True, blank=True,
    )

    # --- Titre constitutif (convention de sûreté) ------------------------- #
    nature_convention = models.CharField(
        _("Nature de la convention"),
        max_length=24, choices=NatureConvention.choices, blank=True,
        help_text=_(
            "Notariée ou sous seing privé. Information déclarative (art. 86) ; "
            "le greffe ne vérifie pas l'acte sous-jacent (TDR § 3.2)."
        ),
    )
    date_convention = models.DateField(
        _("Date de la convention"), null=True, blank=True,
    )

    # --- Parties (art. 85) ------------------------------------------------- #
    requerant = models.ForeignKey(
        "parties.Partie",
        verbose_name=_("Requérant (art. 85)"),
        on_delete=models.PROTECT,
        related_name="inscriptions_deposees",
        null=True, blank=True,
    )
    debiteur_est_constituant = models.BooleanField(
        _("Le débiteur est le constituant"),
        default=False,
        help_text=_(
            "Quand vrai, le système réplique les constituants comme "
            "débiteurs (cas fréquent : sûreté constituée pour garantir "
            "sa propre dette). Évite la double saisie côté frontend."
        ),
    )
    # Les liens N-N typés sont portés par ``RoleInscriptionPartie`` ci-dessous.

    # --- Notifications ----------------------------------------------------- #
    adresse_electronique_notifications = models.EmailField(
        _("Adresse électronique pour notifications"),
        blank=True,
        help_text=_("Facultative (art. 85 avant-dernier alinéa)."),
    )

    # --- Rejet ------------------------------------------------------------- #
    motif_rejet = models.CharField(
        _("Motif de rejet (art. 80)"),
        max_length=48, choices=MotifRejet.choices, blank=True,
    )
    commentaire_rejet_fr = models.TextField(
        _("Commentaire de rejet (FR)"), blank=True,
    )
    commentaire_rejet_ar = models.TextField(
        _("Commentaire de rejet (AR)"), blank=True,
    )
    instant_rejet = models.DateTimeField(_("Instant du rejet"), null=True, blank=True)

    # --- Référence à l'inscription initiale (pour traces de modif/radiation)
    # Non utilisé à ce stade : les demandes de modification / renouvellement /
    # radiation référencent directement l'inscription concernée (app dédiée).

    class Meta:
        verbose_name = _("Inscription")
        verbose_name_plural = _("Inscriptions")
        indexes = [
            models.Index(fields=["statut", "fichier_actuel"]),
            models.Index(fields=["instant_saisie_opposable"]),
            models.Index(fields=["numero_ordre"]),
            models.Index(fields=["date_expiration"]),
        ]

    # -- Helpers de lecture ------------------------------------------------- #
    @property
    def est_au_fichier_public(self) -> bool:
        return self.statut in STATUTS_FICHIER_PUBLIC

    @property
    def est_pre_validation(self) -> bool:
        return self.statut in STATUTS_PRE_VALIDATION

    def __str__(self) -> str:  # pragma: no cover
        return self.numero_ordre or f"Demande {self.reference_demande}"


class RoleInscriptionPartieActifManager(models.Manager):
    """Ne retourne que les rôles actuellement actifs."""

    def get_queryset(self):
        return super().get_queryset().filter(actif=True)


class RoleInscriptionPartie(models.Model):
    """
    Lien typé entre une inscription et une partie (constituant, créancier
    garanti, débiteur).

    Cf. article 85 : « identification du ou des créanciers, du ou des
    constituants et débiteurs ». Une même partie peut apparaître sous
    plusieurs rôles (ex. débiteur et constituant) ; chaque rôle fait
    l'objet d'une ligne distincte.

    Une partie « retirée » par une modification garde ``actif=False`` et
    reste conservée en base — conformément à l'article 79. Les
    ``UniqueConstraint`` sont conditionnés à ``actif=True`` pour
    permettre la réintroduction ultérieure d'une partie précédemment
    retirée si l'acte de modification l'exige.
    """

    from apps.parties.models import RolePartie  # noqa: E402

    inscription = models.ForeignKey(
        Inscription,
        verbose_name=_("Inscription"),
        on_delete=models.PROTECT,
        related_name="roles_parties",
    )
    partie = models.ForeignKey(
        "parties.Partie",
        verbose_name=_("Partie"),
        on_delete=models.PROTECT,
        related_name="roles_dans_inscriptions",
    )
    role = models.CharField(_("Rôle"), max_length=16, choices=RolePartie.choices)
    ordre = models.PositiveIntegerField(_("Ordre"), default=0)

    # Validité temporelle (cf. apps.core.mixins.ValiditeTemporelle — inlined
    # ici plutôt qu'hérité, afin d'appliquer la contrainte unique conditionnée
    # à ``actif=True`` sans risquer les conflits de ``Meta.constraints``.)
    actif = models.BooleanField(_("Actif"), default=True, db_index=True)
    date_fin_validite = models.DateTimeField(
        _("Fin de validité"), null=True, blank=True,
    )
    raison_fin = models.CharField(
        _("Raison de fin de validité"), max_length=255, blank=True,
    )

    objects = models.Manager()
    actifs = RoleInscriptionPartieActifManager()

    class Meta:
        verbose_name = _("Rôle d'une partie dans une inscription")
        verbose_name_plural = _("Rôles des parties")
        constraints = [
            # L'unicité ne vaut que pour les rôles ACTIFS : un rôle peut être
            # désactivé puis ré-attribué à la même partie lors d'une
            # modification ultérieure, conformément à l'article 79
            # (conservation intégrale de l'historique).
            models.UniqueConstraint(
                fields=["inscription", "partie", "role"],
                condition=models.Q(actif=True),
                name="unique_partie_role_actif_par_inscription",
            ),
        ]
        ordering = ("role", "ordre", "id")
        indexes = [
            models.Index(fields=["inscription", "role", "actif"]),
        ]

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError(
            "Suppression interdite (art. 79). Utilisez la désactivation "
            "via un acte de modification tracé."
        )


class PieceJointe(Horodatage, ActeurTrace):
    """
    Pièce jointe à une demande — article 92 pour la radiation notamment.

    Le système reçoit et conserve la pièce, sans se substituer à l'acte
    (§ 3.2 du TDR). Le scellement de la pièce (empreinte) est prévu au
    § 6.3 ; il est GELÉ à ce stade et signalé par ``sceau_empreinte``.
    """

    inscription = models.ForeignKey(
        Inscription,
        verbose_name=_("Inscription"),
        on_delete=models.PROTECT,
        related_name="pieces_jointes",
    )
    nom_original = models.CharField(_("Nom du fichier"), max_length=255)
    fichier = models.FileField(_("Contenu"), upload_to="pieces_jointes/%Y/%m/")
    type_mime = models.CharField(_("Type MIME"), max_length=128, blank=True)
    taille_octets = models.PositiveBigIntegerField(_("Taille (octets)"))
    sceau_empreinte = models.CharField(
        _("Empreinte de scellement"),
        max_length=128, blank=True,
        help_text=_(
            "Empreinte SHA-256 du fichier à des fins d'intégrité. ⚠️ Le "
            "scellement opposable reste GELÉ (TDR § 5.1)."
        ),
    )

    class Meta:
        verbose_name = _("Pièce jointe")
        verbose_name_plural = _("Pièces jointes")


# --------------------------------------------------------------------------- #
#  Observations de retour pour correction (workflow Greffier ⇄ Déclarant)     #
# --------------------------------------------------------------------------- #
class ObservationRetour(Horodatage):
    """
    Observation formulée par le greffier lors d'un retour d'une demande
    au déclarant pour correction (directive MO 2026-05-31).

    Distinction métier (TDR § 4.3 + arbitrage MO) :
      - **Rejet (art. 80)** : terminal, motifs limitatifs, demande clôturée.
        Porté par ``Inscription.motif_rejet`` + ``commentaire_rejet_fr/_ar``.
      - **Retour pour correction** : réversible, observation libre FR + AR,
        demande conservée en statut ``RETOURNEE`` jusqu'à resoumission.
        Porté par ce modèle, en plusieurs exemplaires si plusieurs cycles.

    Garde-fous (TDR § garde-fous inviolables) :
      - intégrité : append-only applicatif — une observation ne peut être
        modifiée ni supprimée après création ; seul l'instant_resoumission
        et l'acteur de resoumission peuvent être renseignés une seule
        fois lorsque le déclarant resoumet ;
      - parité FR/AR : les deux textes sont obligatoires et non vides ;
      - traçabilité : chaque retour et chaque resoumission sont audités
        séparément (cf. CategorieAudit.RETOUR_CORRECTION).
    """

    inscription = models.ForeignKey(
        Inscription,
        verbose_name=_("Inscription concernée"),
        on_delete=models.PROTECT,
        related_name="observations_retour",
    )
    observation_fr = models.TextField(
        _("Observation du greffier (FR)"),
        help_text=_(
            "Observation détaillée motivant le retour. Obligatoire et "
            "non vide. Visible du déclarant."
        ),
    )
    observation_ar = models.TextField(
        _("Observation du greffier (AR)"),
        help_text=_(
            "Observation détaillée motivant le retour, version arabe. "
            "Obligatoire et non vide. Parité juridique avec FR."
        ),
    )
    cree_par = models.ForeignKey(
        "utilisateurs.Utilisateur",
        verbose_name=_("Greffier ayant retourné la demande"),
        on_delete=models.PROTECT,
        related_name="retours_emis",
    )
    statut_au_moment = models.CharField(
        _("Statut de l'inscription au moment du retour"),
        max_length=32,
    )
    instant_resoumission = models.DateTimeField(
        _("Instant de la resoumission par le déclarant"),
        null=True, blank=True,
        help_text=_(
            "Renseigné une seule fois lorsque le déclarant resoumet la "
            "demande après correction. Immuable ensuite."
        ),
    )
    resoumis_par = models.ForeignKey(
        "utilisateurs.Utilisateur",
        verbose_name=_("Déclarant ayant resoumis la demande"),
        on_delete=models.PROTECT,
        related_name="resoumissions_effectuees",
        null=True, blank=True,
    )

    class Meta:
        verbose_name = _("Observation de retour")
        verbose_name_plural = _("Observations de retour")
        ordering = ("cree_le",)
        indexes = [
            models.Index(fields=["inscription", "cree_le"]),
        ]

    def clean(self):
        """Validation FR/AR non vides (parité juridique)."""
        from django.core.exceptions import ValidationError
        if not (self.observation_fr or "").strip():
            raise ValidationError({
                "observation_fr": _(
                    "L'observation française est obligatoire et non vide."
                ),
            })
        if not (self.observation_ar or "").strip():
            raise ValidationError({
                "observation_ar": _(
                    "L'observation arabe est obligatoire et non vide."
                ),
            })

    def save(self, *args, **kwargs):
        # Append-only : interdire la modification du texte ou de l'auteur
        # après création. Seuls instant_resoumission et resoumis_par peuvent
        # être renseignés une fois.
        if self.pk:
            ancien = type(self).objects.get(pk=self.pk)
            for champ in ("observation_fr", "observation_ar",
                          "cree_par_id", "inscription_id",
                          "statut_au_moment"):
                if getattr(ancien, champ) != getattr(self, champ):
                    raise PermissionError(
                        f"Champ '{champ}' immuable après création "
                        "(append-only — art. 79 + intégrité)."
                    )
            # instant_resoumission et resoumis_par : une seule fois
            if (ancien.instant_resoumission is not None
                    and ancien.instant_resoumission != self.instant_resoumission):
                raise PermissionError(
                    "Instant de resoumission déjà figé — immuable."
                )
            if (ancien.resoumis_par_id is not None
                    and ancien.resoumis_par_id != self.resoumis_par_id):
                raise PermissionError(
                    "Acteur de resoumission déjà figé — immuable."
                )
        else:
            self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError(
            "Suppression interdite (art. 79 — conservation pérenne)."
        )
