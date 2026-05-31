"""
API d'audit — lecture seule.

Seul le rôle « Auditeur / Contrôleur » (§ 4.1 du TDR) peut accéder à ces
endpoints. Le contrôle d'accès final sera câblé lorsque l'app
``utilisateurs`` exposera sa matrice d'habilitations.
"""
from django.urls import path

from apps.audit import views

urlpatterns = [
    path("entrees/", views.ListeEntreesAudit.as_view(), name="audit-liste"),
    path(
        "verification-chaine/",
        views.VerificationChaineAudit.as_view(),
        name="audit-verification-chaine",
    ),
]
