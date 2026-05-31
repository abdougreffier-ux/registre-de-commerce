"""Admin — traces des recherches publiques (art. 94-97, § 5.2)."""
from django.contrib import admin

from apps.core.admin_base import LectureSeuleAdmin
from apps.recherche.models import RequeteRecherche


@admin.register(RequeteRecherche)
class RequeteRechercheAdmin(LectureSeuleAdmin):
    list_display = ("instant", "nombre_resultats", "adresse_ip")
    date_hierarchy = "instant"
