"""
Admin — utilisateurs et affectations de rôle.

§ 4.1 TDR — l'administrateur fonctionnel gère les utilisateurs et les
rôles. Toute affectation et toute révocation doit être tracée
(signal ``_tracer_affectation_role`` → journal d'audit, catégorie
``compte``).

Règles :
- La suppression d'un utilisateur est interdite : la désactivation
  passe par le flag ``compte_actif``. Conservation au sens de l'art. 79
  et lisibilité des traces d'audit.
- La suppression d'une ``AffectationRole`` est interdite : la révocation
  passe par ``actif=False`` + ``fin_le``. Préserve la chronologie
  d'habilitation (§ 5.2).
- Les actions de masse sont désactivées (principe général RSM — voir
  ``apps.core.admin_base._BaseAdminRSM``).
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.core.admin_base import EditionRestreinteAdmin
from apps.utilisateurs.models import AffectationRole, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """
    Admin des utilisateurs — basé sur ``UserAdmin`` de Django pour
    préserver les écrans standard (mot de passe, groupes, permissions).

    Renforcements RSM :
    - ``has_delete_permission`` toujours False ;
    - ``actions = None`` / ``get_actions`` vide : aucune action de masse ;
    - champ ``compte_actif`` pour la désactivation logique.
    """

    list_display = (
        "username", "identifiant_officiel", "nom_affichage",
        "is_staff", "compte_actif",
    )
    search_fields = (
        "username", "identifiant_officiel", "nom_affichage", "email",
    )
    fieldsets = UserAdmin.fieldsets + (
        ("RSM", {"fields": (
            "identifiant_officiel", "nom_affichage",
            "telephone", "compte_actif",
        )}),
    )
    actions = None

    def get_actions(self, request):  # noqa: D401
        return {}

    def has_delete_permission(self, request, obj=None):  # noqa: D401
        return False


@admin.register(AffectationRole)
class AffectationRoleAdmin(EditionRestreinteAdmin):
    list_display = ("utilisateur", "role", "actif", "debut_le", "fin_le")
    list_filter = ("role", "actif")
    search_fields = (
        "utilisateur__username", "utilisateur__identifiant_officiel",
    )
    readonly_fields = ("debut_le",)
