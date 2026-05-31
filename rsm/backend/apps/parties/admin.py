"""Admin — parties (consultation seule, art. 79, § 4.1)."""
from django.contrib import admin

from apps.core.admin_base import ConsultationMetierAdmin
from apps.parties.models import Partie


@admin.register(Partie)
class PartieAdmin(ConsultationMetierAdmin):
    list_display = (
        "id", "type_partie", "nom", "prenom",
        "denomination_sociale", "numero_rc",
    )
    list_filter = ("type_partie",)
    search_fields = ("nom", "prenom", "denomination_sociale", "numero_rc")
