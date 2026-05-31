from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ModificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.modifications"
    verbose_name = _("Modifications (art. 88-90)")
