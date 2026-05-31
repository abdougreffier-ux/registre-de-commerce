"""
Journal d'audit inaltérable — TDR § 5.2, articles 79 et 82 du décret.

Principes :
- Append-only : aucune suppression, aucune modification rétroactive.
- Détection d'altération : chaînage d'empreintes (hash de l'entrée n-1
  incorporé dans l'entrée n).
- Indépendance linguistique : toutes les entrées sont stockées dans une
  forme structurée, avec libellés d'action portés par un référentiel bilingue.
- Lisibilité auditeur : chaque entrée porte acteur, horodatage, action,
  objet, résultat (§ 5.2 du TDR).
- L'auditeur (§ 4.1 du TDR) dispose d'un accès en lecture seule.

Protection technique complémentaire : un trigger PostgreSQL (posé par une
migration dédiée) interdit ``UPDATE`` et ``DELETE`` sur la table, quelle
que soit l'origine de l'opération. Cette protection est indépendante du
code Python et résiste à une compromission de l'application.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class CategorieAudit(models.TextChoices):
    """Catégories d'événements listées par le TDR § 5.2."""

    CONNEXION = "connexion", _("Connexion / déconnexion / tentative")
    COMPTE = "compte", _("Création ou modification de compte / rôle")
    DEMANDE = "demande", _("Dépôt d'une demande (inscription, modification, etc.)")
    CONTROLE_FORME = "controle_forme", _("Contrôle de forme (art. 80)")
    VALIDATION = "validation", _("Validation par l'autorité de validation")
    REJET = "rejet", _("Rejet motivé (art. 80)")
    CERTIFICAT = "certificat", _("Délivrance d'un certificat")
    RECHERCHE = "recherche", _("Lancement d'une recherche publique")
    EXPORT_STAT = "export_stat", _("Export statistique (art. 82)")
    ADMIN = "admin", _("Opération d'administration")
    SYSTEME = "systeme", _("Événement système")


class ResultatAudit(models.TextChoices):
    SUCCES = "succes", _("Succès")
    ECHEC = "echec", _("Échec")
    REJET = "rejet", _("Rejet pour motif limitatif (art. 80)")
    REFUS_AUTORISATION = "refus_autorisation", _("Refus d'autorisation")


class EntreeAudit(models.Model):
    """
    Entrée immuable du journal d'audit.

    Champs cardinaux (§ 5.2) :
    - identifiant interne (``id``) ;
    - horodatage à la seconde (``instant``) ;
    - identité de l'acteur (``acteur``) ;
    - type d'action (``categorie`` + ``action_cle``) ;
    - objet concerné (``objet_type`` + ``objet_reference``) ;
    - résultat (``resultat``).

    Champs d'intégrité :
    - ``empreinte`` : hash de (données de l'entrée + ``empreinte_precedente``) ;
    - ``empreinte_precedente`` : empreinte de la dernière entrée connue.
    Le cumul forme une chaîne détectant toute rupture d'intégrité.
    """

    instant = models.DateTimeField(_("Instant"), db_index=True)
    categorie = models.CharField(
        _("Catégorie"), max_length=32, choices=CategorieAudit.choices, db_index=True,
    )
    action_cle = models.CharField(
        _("Action (clé métier)"),
        max_length=80,
        help_text=_(
            "Identifiant stable de l'action, indépendant de la langue (ex. "
            "``inscription.creer``, ``recherche.lancer``, ``rejet.prononcer``)."
        ),
    )
    acteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Acteur"),
        on_delete=models.PROTECT,
        related_name="entrees_audit",
        null=True, blank=True,
        help_text=_("Nul uniquement pour les événements système non imputables."),
    )
    acteur_role = models.CharField(
        _("Rôle applicatif"),
        max_length=48,
        blank=True,
        help_text=_("Rôle sous lequel l'action a été exécutée (§ 4.1 du TDR)."),
    )
    objet_type = models.CharField(
        _("Type d'objet"),
        max_length=64,
        blank=True,
        help_text=_("ex. ``inscription``, ``modification``, ``utilisateur``."),
    )
    objet_reference = models.CharField(
        _("Référence de l'objet"),
        max_length=120,
        blank=True,
        help_text=_(
            "Référence stable (numéro d'inscription, identifiant de demande, "
            "identifiant utilisateur, etc.)."
        ),
    )
    resultat = models.CharField(
        _("Résultat"), max_length=32, choices=ResultatAudit.choices,
    )
    details = models.JSONField(
        _("Détails"),
        default=dict, blank=True,
        help_text=_(
            "Données complémentaires structurées (diff avant/après, motifs, "
            "critères de recherche, etc.). Aucun champ libre en langue locale "
            "pour préserver la neutralité linguistique § 7.6."
        ),
    )

    # Intégrité
    empreinte_precedente = models.CharField(
        _("Empreinte précédente"), max_length=128, blank=True,
    )
    empreinte = models.CharField(
        _("Empreinte de l'entrée"), max_length=128, db_index=True,
    )

    # Contexte technique (utile à l'auditeur)
    adresse_ip = models.GenericIPAddressField(_("Adresse IP"), null=True, blank=True)
    user_agent = models.CharField(_("User-Agent"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Entrée du journal d'audit")
        verbose_name_plural = _("Journal d'audit")
        ordering = ("-instant", "-id")
        indexes = [
            models.Index(fields=["categorie", "instant"]),
            models.Index(fields=["objet_type", "objet_reference"]),
        ]

    # -- Blocages applicatifs (complétés par des triggers SQL) -------------- #
    def save(self, *args, **kwargs):  # noqa: D401
        if self.pk is not None:
            # Toute tentative de mise à jour est refusée (art. 79, § 5.2).
            raise PermissionError(
                "Le journal d'audit est append-only : toute modification "
                "d'une entrée existante est interdite."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # noqa: D401
        raise PermissionError(
            "Le journal d'audit est append-only : toute suppression est "
            "interdite (article 79 du décret 2021-033)."
        )

    def __str__(self) -> str:  # pragma: no cover
        return f"[{self.instant:%Y-%m-%d %H:%M:%S}] {self.action_cle} → {self.resultat}"
