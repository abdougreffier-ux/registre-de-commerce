"""Admin — extractions statistiques (monopole du greffe, art. 82, art. 79)."""
from django.contrib import admin

from apps.core.admin_base import LectureSeuleAdmin
from apps.statistiques.models import ExtractionStatistique


@admin.register(ExtractionStatistique)
class ExtractionStatistiqueAdmin(LectureSeuleAdmin):
    list_display = ("instant", "producteur")
    date_hierarchy = "instant"
