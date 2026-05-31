"""Routeur racine de l'API v1 (REST) — agrégation des sous-routes des apps."""
from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.utilisateurs.api_urls")),
    path("categories-biens/", include("apps.biens.api_urls")),
    path("recherche/", include("apps.recherche.api_urls")),
    path("inscriptions/", include("apps.inscriptions.api_urls")),
    path("modifications/", include("apps.modifications.api_urls")),
    path("renouvellements/", include("apps.renouvellements.api_urls")),
    path("radiations/", include("apps.radiations.api_urls")),
    path("rejets/", include("apps.rejets.api_urls")),
    path("certificats/", include("apps.certificats.api_urls")),
    path("statistiques/", include("apps.statistiques.api_urls")),
    path("referentiels/", include("apps.referentiels.api_urls")),
    path("audit/", include("apps.audit.api_urls")),
]
