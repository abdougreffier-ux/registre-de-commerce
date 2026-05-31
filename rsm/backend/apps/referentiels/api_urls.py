"""
API des référentiels.

- Lecture publique : ``GET /natures-droit/`` (actives uniquement).
- Administration paramétrable des natures de droit : endpoints sous
  ``/admin/natures-droit/``, restreints aux rôles ``autorite_validation``
  et ``admin_fonctionnel``.
"""
from django.urls import path

from apps.referentiels import views

urlpatterns = [
    # Lecture publique
    path("natures-droit/", views.LibellesNatureDroitView.as_view()),
    path("motifs-rejet/", views.LibellesMotifRejetView.as_view()),
    path("canaux-saisie/", views.LibellesCanalSaisieView.as_view()),
    path("criteres-recherche/", views.LibellesCritereRechercheView.as_view()),
    path("types-certificats/", views.LibellesTypeCertificatView.as_view()),
    # Administration paramétrable
    path(
        "admin/natures-droit/",
        views.NatureDroitAdminListCreateView.as_view(),
        name="admin-natures-droit-liste",
    ),
    path(
        "admin/natures-droit/<int:pk>/",
        views.NatureDroitAdminDetailView.as_view(),
        name="admin-natures-droit-detail",
    ),
]
