"""URLs d'authentification applicative."""
from django.urls import path

from apps.utilisateurs.api_views import (
    ChangerMotDePasseView, LoginView, LogoutView, WhoamiView,
)

urlpatterns = [
    path("whoami/", WhoamiView.as_view(), name="auth-whoami"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path(
        "changer-mot-de-passe/",
        ChangerMotDePasseView.as_view(),
        name="auth-changer-mot-de-passe",
    ),
]
