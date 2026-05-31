from django.urls import path

from apps.recherche import views

urlpatterns = [
    path("", views.RecherchePublique.as_view(), name="recherche-publique"),
]
