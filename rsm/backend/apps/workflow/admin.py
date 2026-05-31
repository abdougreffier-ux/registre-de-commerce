"""Admin — présentation lecture seule des transitions de statut (§ 4.3, art. 79)."""
from django.contrib import admin

from apps.core.admin_base import LectureSeuleAdmin
from apps.workflow.models import TransitionStatut


@admin.register(TransitionStatut)
class TransitionStatutAdmin(LectureSeuleAdmin):
    list_display = (
        "instant", "numero_inscription",
        "statut_avant", "statut_apres", "evenement",
        "acteur", "automatique",
    )
    list_filter = ("statut_apres", "evenement", "automatique")
    search_fields = ("numero_inscription",)
    date_hierarchy = "instant"
