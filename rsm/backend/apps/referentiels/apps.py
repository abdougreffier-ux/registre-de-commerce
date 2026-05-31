from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReferentielsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.referentiels"
    verbose_name = _("Référentiels bilingues")
