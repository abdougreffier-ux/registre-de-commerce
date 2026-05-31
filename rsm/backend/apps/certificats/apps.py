from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CertificatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.certificats"
    verbose_name = _("Certificats (stub — production probante GELÉE)")
