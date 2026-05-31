"""Admin — demandes de renouvellement (consultation seule, § 4.1)."""
from django.contrib import admin

from apps.core.admin_base import ConsultationMetierAdmin
from apps.renouvellements.models import DemandeRenouvellement


@admin.register(DemandeRenouvellement)
class DemandeRenouvellementAdmin(ConsultationMetierAdmin):
    list_display = (
        "id", "inscription", "statut",
        "ancienne_date_expiration", "nouvelle_date_expiration",
        "applique_le", "cree_le",
    )
    list_filter = ("statut",)
    search_fields = ("inscription__numero_ordre",)
