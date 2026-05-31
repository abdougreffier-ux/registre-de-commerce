"""URLs traduites exposées par l'app core (accueil public bilingue)."""
from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.AccueilView.as_view(), name="accueil"),
    path("sante/", views.SanteView.as_view(), name="sante"),
]
