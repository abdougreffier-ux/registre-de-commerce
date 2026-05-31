"""Admin — certificats (consultation seule, § 4.1, art. 79)."""
from django.contrib import admin

from apps.certificats.models import Certificat
from apps.core.admin_base import ConsultationMetierAdmin


@admin.register(Certificat)
class CertificatAdmin(ConsultationMetierAdmin):
    list_display = (
        "id", "type_certificat", "inscription", "requete_recherche",
        "langue_generation", "probant", "cree_le",
    )
    list_filter = ("type_certificat", "langue_generation", "probant")
    readonly_fields = ("empreinte", "contenu_json")
