"""Admin — demandes de radiation (consultation seule, § 4.1)."""
from django.contrib import admin

from apps.core.admin_base import ConsultationMetierAdmin
from apps.radiations.models import DemandeRadiation


@admin.register(DemandeRadiation)
class DemandeRadiationAdmin(ConsultationMetierAdmin):
    list_display = (
        "id", "inscription", "fondement", "statut",
        "applique_le", "cree_le",
    )
    list_filter = ("fondement", "statut")
    search_fields = (
        "inscription__numero_ordre",
        "nom_constituant", "denomination_constituant",
    )
