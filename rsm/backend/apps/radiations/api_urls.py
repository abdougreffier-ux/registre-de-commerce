from django.urls import path

from apps.radiations import views

urlpatterns = [
    path("", views.ListeCreerRadiation.as_view(), name="radiations-liste"),
    path("<int:pk>/appliquer/", views.AppliquerRadiation.as_view(),
         name="radiation-appliquer"),
]
