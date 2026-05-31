from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RechercheConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.recherche"
    verbose_name = _("Recherches (art. 94-97)")
