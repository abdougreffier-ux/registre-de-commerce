from django.urls import path

from apps.modifications import views

urlpatterns = [
    path("", views.ListeCreerModification.as_view(), name="modifications-liste"),
    path("<int:pk>/appliquer/", views.AppliquerModification.as_view(),
         name="modification-appliquer"),
]
