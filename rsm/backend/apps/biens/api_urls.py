"""URLs des catégories de biens."""
from django.urls import path

from apps.biens import views

urlpatterns = [
    path(
        "",
        views.ListeCategoriesBien.as_view(),
        name="categories-biens-liste",
    ),
    path(
        "publier/",
        views.PublierCategorieBien.as_view(),
        name="categories-biens-publier",
    ),
    path(
        "<int:pk>/",
        views.DetailCategorieBien.as_view(),
        name="categories-biens-detail",
    ),
    path(
        "<int:pk>/modifier/",
        views.ModifierCategorieBien.as_view(),
        name="categories-biens-modifier",
    ),
]
