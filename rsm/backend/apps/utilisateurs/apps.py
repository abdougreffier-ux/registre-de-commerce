from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UtilisateursConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.utilisateurs"
    verbose_name = _("Utilisateurs et rôles")

    def ready(self) -> None:
        # Import des signaux au démarrage (traçabilité des affectations de rôle).
        from apps.utilisateurs import signals  # noqa: F401
