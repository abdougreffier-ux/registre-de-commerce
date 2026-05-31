from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RadiationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.radiations"
    verbose_name = _("Radiations (art. 92)")
