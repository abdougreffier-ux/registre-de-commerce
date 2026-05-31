"""API des inscriptions — dépôt, consultation, validation, rejet, PJ."""
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
    path("<uuid:reference_demande>/pieces-jointes/",
         views.PieceJointeUploadView.as_view(),
         name="inscription-piece-jointe"),
]
