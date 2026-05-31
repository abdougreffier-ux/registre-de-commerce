from django.urls import path

from apps.renouvellements import views

urlpatterns = [
    path("", views.ListeCreerRenouvellement.as_view(), name="renouvellements-liste"),
    path("<int:pk>/appliquer/", views.AppliquerRenouvellement.as_view(),
         name="renouvellement-appliquer"),
]
