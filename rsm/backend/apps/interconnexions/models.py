"""
Modèles de prévision — interopérabilité bancaire (fiche F15).

⚠️ AUCUNE LOGIQUE D'EXPOSITION : ces modèles définissent uniquement la
structure de données nécessaire à l'agrément des partenaires, à la
collecte du consentement des constituants et au journal des accès.
Aucun endpoint HTTP n'est câblé à ces modèles tant que la fiche F15 n'a
pas été instruite par décision MO.

Articles du décret 2021-033 servant de fondement :
- art. 79  : conservation, journal append-only ;
- art. 82  : monopole statistique du greffe ;
- art. 83  : réversibilité ;
- art. 94  : recherche ouverte à tout intéressé ;
- art. 96  : critères limitatifs (deux minimum) ;
- art. 97  : certificat probant.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import ActeurTrace, Horodatage


# --------------------------------------------------------------------------- #
# A. Statut d'un partenaire                                                    #
# --------------------------------------------------------------------------- #
class StatutPartenaire(models.TextChoices):
    """États possibles d'un partenaire dans son cycle d'agrément."""

    EN_INSTRUCTION = "en_instruction", _("En instruction")
    AGREE = "agree", _("Agréé")
    SUSPENDU = "suspendu", _("Suspendu")
    REVOQUE = "revoque", _("Révoqué")


class TypePartenaire(models.TextChoices):
    """
    Catégorie de partenaire — liste limitative à arbitrer en F15
    (décision n° 2 de la fiche). Les valeurs ci-dessous reflètent les
    catégories institutionnelles habituelles ; aucune n'est activée
    sans décision MO.
    """

    BANQUE = "banque", _("Banque agréée par la BCM")
    MICROFINANCE = "microfinance", _("Institution de microfinance")
    SOCIETE_FINANCIERE = "societe_financiere", _("Société financière")
    IFI = "ifi", _("Institution financière internationale")


class PartenaireBancaire(Horodatage, ActeurTrace):
    """
    Établissement habilité à interagir avec le RSM par API.

    L'inscription dans cette table est une formalité administrative (art. 83 —
    cahier des charges), distincte de toute opération métier.
    """

    code = models.CharField(
        _("Code partenaire (unique)"),
        max_length=32, unique=True, db_index=True,
        help_text=_(
            "Identifiant stable à choisir par le MO (ex. code BCM)."
        ),
    )
    raison_sociale = models.CharField(_("Raison sociale"), max_length=255)
    type_partenaire = models.CharField(
        _("Type de partenaire"),
        max_length=24, choices=TypePartenaire.choices,
    )
    statut = models.CharField(
        _("Statut d'agrément"), max_length=24,
        choices=StatutPartenaire.choices,
        default=StatutPartenaire.EN_INSTRUCTION,
    )

    contact_technique_email = models.EmailField(
        _("Contact technique (e-mail)"), blank=True,
    )
    contact_technique_telephone = models.CharField(
        _("Contact technique (téléphone)"), max_length=32, blank=True,
    )
    autorite_agrement = models.CharField(
        _("Autorité d'agrément"), max_length=128, blank=True,
        help_text=_("Ex. : BCM, Ministère des Finances, …"),
    )
    reference_agrement = models.CharField(
        _("Référence de l'acte d'agrément"), max_length=128, blank=True,
    )
    valide_du = models.DateField(_("Valide du"), null=True, blank=True)
    valide_au = models.DateField(_("Valide au"), null=True, blank=True)

    note_interne = models.TextField(_("Note interne"), blank=True)

    class Meta:
        verbose_name = _("Partenaire externe (F15)")
        verbose_name_plural = _("Partenaires externes (F15)")
        ordering = ("raison_sociale",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code} — {self.raison_sociale}"


# --------------------------------------------------------------------------- #
# B. Accréditation (convention signée + plafonds)                              #
# --------------------------------------------------------------------------- #
class AccreditationPartenaire(Horodatage, ActeurTrace):
    """
    Convention concrète — plafond de requêtes, périmètre, dates.

    Plusieurs accréditations peuvent se succéder dans le temps pour un
    même partenaire (renouvellements, modifications de plafond).
    """

    partenaire = models.ForeignKey(
        PartenaireBancaire,
        verbose_name=_("Partenaire"),
        on_delete=models.PROTECT,
        related_name="accreditations",
    )
    reference_convention = models.CharField(
        _("Référence de la convention"), max_length=128, db_index=True,
    )
    debut_le = models.DateField(_("Début"))
    fin_le = models.DateField(_("Fin"), null=True, blank=True)
    plafond_requetes_par_jour = models.PositiveIntegerField(
        _("Plafond de requêtes par jour"), default=0,
        help_text=_("0 = illimité (à éviter — décision F15 #7)."),
    )
    perimetre = models.JSONField(
        _("Périmètre de données autorisées"), default=dict,
        help_text=_(
            "Décrit les champs accessibles au partenaire. Tant que la "
            "fiche F15 #4 n'est pas tranchée, ce champ reste vide ; "
            "aucune ouverture par défaut."
        ),
    )
    actif = models.BooleanField(_("Accréditation active"), default=False)

    class Meta:
        verbose_name = _("Accréditation partenaire (F15)")
        verbose_name_plural = _("Accréditations partenaires (F15)")
        ordering = ("-debut_le",)


# --------------------------------------------------------------------------- #
# C. Clés publiques (mTLS / JWS)                                               #
# --------------------------------------------------------------------------- #
class ClePubliquePartenaire(Horodatage, ActeurTrace):
    """
    Empreinte de la clé publique X.509 d'un partenaire pour la
    vérification des appels API. La clé brute (PEM) n'est pas stockée
    par défaut : seule l'empreinte SHA-256 est conservée, suffisante
    pour identifier le certificat. La clé peut être collectée par voie
    hors-bande (cahier des charges art. 83).
    """

    partenaire = models.ForeignKey(
        PartenaireBancaire,
        verbose_name=_("Partenaire"),
        on_delete=models.PROTECT,
        related_name="cles",
    )
    empreinte_sha256 = models.CharField(
        _("Empreinte SHA-256 (hex)"), max_length=64, unique=True, db_index=True,
    )
    sujet_x509 = models.CharField(_("Sujet X.509"), max_length=255, blank=True)
    emetteur_x509 = models.CharField(_("Émetteur X.509"), max_length=255, blank=True)
    valide_du = models.DateField(_("Valide du"))
    valide_au = models.DateField(_("Valide au"))
    revoquee = models.BooleanField(_("Révoquée"), default=False)
    motif_revocation = models.CharField(
        _("Motif de révocation"), max_length=255, blank=True,
    )

    class Meta:
        verbose_name = _("Clé publique partenaire (F15)")
        verbose_name_plural = _("Clés publiques partenaires (F15)")


# --------------------------------------------------------------------------- #
# D. Consentement du constituant                                               #
# --------------------------------------------------------------------------- #
class ConsentementInterconnexion(Horodatage, ActeurTrace):
    """
    Consentement explicite d'un constituant à la consultation
    périodique d'inscriptions le concernant par un partenaire donné
    (cas d'usage 2 — surveillance de portefeuille).

    La nature de ce consentement (implicite art. 94 vs explicite vs
    annuel renouvelable) est à arbitrer en F15 #5. Tant que F15 n'est
    pas tranchée, aucun consentement n'est exploité par un service —
    cette table existe pour l'enregistrement futur.
    """

    constituant = models.ForeignKey(
        "parties.Partie",
        verbose_name=_("Constituant"),
        on_delete=models.PROTECT,
        related_name="consentements_interconnexion",
    )
    partenaire = models.ForeignKey(
        PartenaireBancaire,
        verbose_name=_("Partenaire"),
        on_delete=models.PROTECT,
        related_name="consentements",
    )
    accorde_le = models.DateTimeField(_("Accordé le"))
    valide_jusquau = models.DateTimeField(_("Valide jusqu'au"), null=True, blank=True)
    revoque_le = models.DateTimeField(_("Révoqué le"), null=True, blank=True)
    motif_revocation = models.CharField(
        _("Motif de révocation"), max_length=255, blank=True,
    )
    preuve_documentaire = models.CharField(
        _("Référence de la preuve"), max_length=255, blank=True,
        help_text=_(
            "Chemin / hash du document de consentement. La nature du "
            "document est à arbitrer en F15 (signature électronique = F3)."
        ),
    )

    class Meta:
        verbose_name = _("Consentement d'interconnexion (F15)")
        verbose_name_plural = _("Consentements d'interconnexion (F15)")
        constraints = [
            models.UniqueConstraint(
                fields=["constituant", "partenaire"],
                condition=models.Q(revoque_le__isnull=True),
                name="unique_consentement_actif",
            ),
        ]


# --------------------------------------------------------------------------- #
# E. Journal d'accès API — append-only (art. 79)                               #
# --------------------------------------------------------------------------- #
class JournalAccesAPI(models.Model):
    """
    Journal append-only de chaque appel API d'un partenaire.

    Une entrée est créée à chaque appel, qu'il aboutisse ou échoue.
    Aucune modification ni suppression n'est admise (art. 79).

    Tant que la fiche F15 n'est pas tranchée, **aucune vue n'écrit dans
    cette table** ; elle est créée pour que les futurs services puissent
    s'y appuyer immédiatement après activation.
    """

    instant = models.DateTimeField(_("Instant"), auto_now_add=True, db_index=True)
    partenaire = models.ForeignKey(
        PartenaireBancaire,
        verbose_name=_("Partenaire"),
        on_delete=models.PROTECT,
        related_name="journal_acces",
        null=True, blank=True,
    )
    cle_utilisee = models.ForeignKey(
        ClePubliquePartenaire,
        verbose_name=_("Clé utilisée"),
        on_delete=models.PROTECT,
        related_name="journal_acces",
        null=True, blank=True,
    )
    methode = models.CharField(_("Méthode HTTP"), max_length=8)
    chemin = models.CharField(_("Chemin"), max_length=255)
    parametres = models.JSONField(
        _("Paramètres envoyés"), default=dict,
        help_text=_(
            "Critères de recherche art. 96 ou payload résumé. Aucune "
            "donnée personnelle hors article 96 n'est journalisée."
        ),
    )
    code_retour = models.PositiveSmallIntegerField(_("Code HTTP retour"))
    certificat_emis = models.CharField(
        _("Identifiant de certificat émis (art. 97)"),
        max_length=128, blank=True,
    )
    duree_ms = models.PositiveIntegerField(_("Durée (ms)"), default=0)
    ip_origine = models.GenericIPAddressField(_("IP d'origine"), null=True, blank=True)
    user_agent = models.CharField(_("User-Agent"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Entrée du journal d'accès API (F15)")
        verbose_name_plural = _("Entrées du journal d'accès API (F15)")
        ordering = ("-instant",)
        indexes = [
            models.Index(fields=["partenaire", "instant"]),
        ]

    def save(self, *args, **kwargs):  # noqa: D401
        if self.pk is not None:
            raise PermissionError(
                "Le journal d'accès API est append-only (art. 79)."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError(
            "Suppression interdite — journal append-only (art. 79)."
        )
