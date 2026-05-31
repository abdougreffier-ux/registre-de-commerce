"""Admin — biens grevés (consultation seule, art. 79, § 4.1)."""
from django.contrib import admin

from apps.biens.models import BienGreve
from apps.core.admin_base import ConsultationMetierAdmin


@admin.register(BienGreve)
class BienGreveAdmin(ConsultationMetierAdmin):
    list_display = (
        "id", "inscription", "marque", "modele", "numero_serie",
        "annee", "actif", "date_fin_validite",
    )
    list_filter = ("marque", "actif")
    search_fields = (
        "numero_serie", "marque", "modele",
        "description_fr", "description_ar",
    )
