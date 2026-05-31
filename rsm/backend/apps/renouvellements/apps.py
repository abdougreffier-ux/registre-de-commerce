from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RenouvellementsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.renouvellements"
    verbose_name = _("Renouvellements (art. 91)")
