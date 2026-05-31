"""
Utilisateurs, rôles applicatifs et habilitations — TDR § 4.1.

⚠️ L'AUTHENTIFICATION FORTE (MFA, PKI, identité numérique nationale) est
ZONE GELÉE — TDR § 5.1. Seul le squelette de modélisation est posé ici.
Aucun mécanisme ``login()`` n'est câblé pour les déclarants externes.

Matrice des rôles (§ 4.1 du TDR — liste limitative) :
- Agent de saisie (Greffe)
- Autorité de validation (Greffier)
- Administrateur fonctionnel
- Administrateur technique
- Auditeur / Contrôleur
- Producteur de statistiques (Greffe)
- Déclarant externe authentifié
- Usager public (non authentifié) — pas un compte, accès anonyme

Règles cardinales :
- Un utilisateur peut cumuler plusieurs rôles mais PAS agent de saisie ET
  autorité de validation sur la même demande (séparation stricte).
- Aucun administrateur (fonctionnel ou technique) ne peut créer, modifier
  ou supprimer une inscription dans le fichier du Registre.
"""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class RoleApplicatif(models.TextChoices):
    AGENT_SAISIE = "agent_saisie", _("Agent de saisie (Greffe)")
    AUTORITE_VALIDATION = "autorite_validation", _("Autorité de validation (Greffier)")
    ADMIN_FONCTIONNEL = "admin_fonctionnel", _("Administrateur fonctionnel")
    ADMIN_TECHNIQUE = "admin_technique", _("Administrateur technique")
    AUDITEUR = "auditeur", _("Auditeur / Contrôleur")
    PROD_STATS = "prod_stats", _("Producteur de statistiques (Greffe)")
    DECLARANT_EXTERNE = "declarant_externe", _("Déclarant externe authentifié")


#: Couples de rôles INCOMPATIBLES sur une même demande.
ROLES_INCOMPATIBLES = [
    (RoleApplicatif.AGENT_SAISIE, RoleApplicatif.AUTORITE_VALIDATION),
]

#: Rôles disposant de privilèges d'écriture sur les entités métier.
ROLES_ECRITURE_METIER = {
    RoleApplicatif.AGENT_SAISIE,
    RoleApplicatif.AUTORITE_VALIDATION,
    RoleApplicatif.DECLARANT_EXTERNE,
}

#: Rôles techniques — aucun accès utile aux contenus métier.
ROLES_ADMINISTRATION = {
    RoleApplicatif.ADMIN_FONCTIONNEL,
    RoleApplicatif.ADMIN_TECHNIQUE,
}


class Utilisateur(AbstractUser):
    """
    Utilisateur du système.

    Les déclarants externes, les agents du greffe et les auditeurs partagent
    la même table, distingués par leurs rôles applicatifs affectés.
    Les données d'identification sensibles ne font pas l'objet de
    duplication linguistique : le nom d'une personne physique est une donnée
    juridiquement neutre (§ 6.3).
    """

    #: Identifiant numérique officiel du compte (ex. : matricule fonctionnaire,
    #: identifiant national pour un déclarant). Zone d'arbitrage MO.
    identifiant_officiel = models.CharField(
        _("Identifiant officiel"), max_length=64, blank=True, db_index=True,
    )
    nom_affichage = models.CharField(
        _("Nom d'affichage"), max_length=200, blank=True,
    )
    telephone = models.CharField(_("Téléphone"), max_length=32, blank=True)
    compte_actif = models.BooleanField(_("Compte actif"), default=True)

    #: Marque un mot de passe « initial / temporaire » fixé par
    #: l'administrateur. Tant que ce drapeau vaut ``True``, l'utilisateur
    #: est forcé de changer son mot de passe à la première connexion ;
    #: l'accès aux fonctionnalités du système est bloqué côté client. Le
    #: changement effectif passe le drapeau à ``False`` (cf. endpoint
    #: ``POST /api/v1/auth/changer-mot-de-passe/``).
    #:
    #: Cette mécanique est purement technique : aucune écriture ne se
    #: fait dans le journal d'audit métier (art. 79) ; seuls les logs
    #: applicatifs ``compte`` éventuels reflètent le changement.
    mot_de_passe_initial = models.BooleanField(
        _("Mot de passe initial à changer"), default=False,
    )

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")

    def roles_actifs(self):
        """Itère sur les rôles actuellement affectés à l'utilisateur."""
        return self.affectations_role.filter(actif=True).values_list(
            "role", flat=True
        )

    def a_role(self, role: str) -> bool:
        return self.affectations_role.filter(role=role, actif=True).exists()


class AffectationRole(models.Model):
    """
    Lien utilisateur ↔ rôle applicatif, avec période de validité.

    Toute affectation ou révocation est tracée au journal d'audit
    (catégorie ``compte``, § 5.2 du TDR).
    """

    utilisateur = models.ForeignKey(
        Utilisateur,
        verbose_name=_("Utilisateur"),
        on_delete=models.PROTECT,
        related_name="affectations_role",
    )
    role = models.CharField(_("Rôle"), max_length=32, choices=RoleApplicatif.choices)
    actif = models.BooleanField(_("Affectation active"), default=True)
    debut_le = models.DateTimeField(_("Début d'affectation"), auto_now_add=True)
    fin_le = models.DateTimeField(_("Fin d'affectation"), null=True, blank=True)
    motif_affectation = models.CharField(
        _("Motif d'affectation ou de révocation"), max_length=255, blank=True,
    )

    class Meta:
        verbose_name = _("Affectation de rôle")
        verbose_name_plural = _("Affectations de rôles")
        constraints = [
            models.UniqueConstraint(
                fields=["utilisateur", "role"],
                condition=models.Q(actif=True),
                name="unique_role_actif_par_utilisateur",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.utilisateur} → {self.get_role_display()}"
