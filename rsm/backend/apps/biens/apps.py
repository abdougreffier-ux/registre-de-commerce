from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BiensConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.biens"
    verbose_name = _("Biens grevés")
