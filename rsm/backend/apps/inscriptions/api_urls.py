"""API des inscriptions — dépôt, consultation, validation, rejet."""
from django.urls import path

from apps.inscriptions import views

urlpatterns = [
    path("", views.ListeDeposerInscription.as_view(), name="inscriptions-liste"),
    path("<uuid:reference_demande>/", views.DetailInscription.as_view(),
         name="inscription-detail"),
    path("<uuid:reference_demande>/valider/", views.ValiderInscription.as_view(),
         name="inscription-valider"),
    path("<uuid:reference_demande>/rejeter/", views.RejeterInscription.as_view(),
         name="inscription-rejeter"),
]
