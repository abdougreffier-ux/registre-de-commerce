from django.urls import path

from apps.statistiques import views

urlpatterns = [
    path("", views.ListeExtractions.as_view(), name="statistiques-liste"),
    path(
        "indicateurs/",
        views.IndicateursStatistiques.as_view(),
        name="statistiques-indicateurs",
    ),
    path(
        "financement-pme/",
        views.IndicateursFinancementPME.as_view(),
        name="statistiques-financement-pme",
    ),
    path("produire/", views.ProduireExtraction.as_view(), name="statistiques-produire"),
]
