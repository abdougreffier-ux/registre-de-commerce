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
    # Workflow demande ⇄ inscription (directive MO 2026-05-31)
    path("<uuid:reference_demande>/retourner/",
         views.RetournerDemande.as_view(),
         name="inscription-retourner"),
    path("<uuid:reference_demande>/resoumettre/",
         views.ResoumettreDemande.as_view(),
         name="inscription-resoumettre"),
    path("<uuid:reference_demande>/pieces-jointes/",
         views.PieceJointeUploadView.as_view(),
         name="inscription-piece-jointe"),
]
