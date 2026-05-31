from django.urls import path

from apps.certificats import views

urlpatterns = [
    path("", views.ListeCertificats.as_view(), name="certificats-liste"),
    path("<int:pk>/", views.DetailCertificat.as_view(), name="certificat-detail"),
]
