from django.urls import path

from apps.rejets import views

urlpatterns = [
    path("", views.ListeRejets.as_view(), name="rejets-liste"),
]
