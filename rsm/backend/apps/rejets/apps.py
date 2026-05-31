from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RejetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rejets"
    verbose_name = _("Rejets (art. 80)")
