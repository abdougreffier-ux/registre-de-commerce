"""Admin — présentation lecture seule du journal d'audit (art. 79, § 5.2)."""
from django.contrib import admin

from apps.audit.models import EntreeAudit
from apps.core.admin_base import LectureSeuleAdmin


@admin.register(EntreeAudit)
class EntreeAuditAdmin(LectureSeuleAdmin):
    list_display = (
        "instant", "categorie", "action_cle",
        "acteur", "acteur_role", "objet_type", "objet_reference", "resultat",
    )
    list_filter = ("categorie", "resultat", "acteur_role")
    search_fields = ("action_cle", "objet_reference", "acteur__username")
    date_hierarchy = "instant"
    ordering = ("-instant",)
