"""
Endpoints d'authentification par session — TDR § 4.1, § 5.1.

Ces endpoints ne constituent pas le mécanisme d'authentification forte
(F2) qui demeure en attente des paramètres techniques désignés par le
maître d'ouvrage. Ils fournissent une voie de connexion minimale
s'appuyant sur l'authentification Django / DRF session pour permettre
le test des parcours applicatifs (TDR § 4.1 — rôles Agent de saisie,
Autorité de validation, Déclarant externe, Auditeur, etc.).

Aucune règle métier, aucun flux juridique n'est altéré : ces endpoints
se limitent à ouvrir et fermer une session authentifiée et à exposer
l'identité et les rôles de l'utilisateur courant, de la même manière que
le ferait le portail d'admin Django.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import (
    validate_password, ValidationError as PasswordValidationError,
)
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


def _info_systeme():
    """Métadonnées système exposées à toute réponse d'auth."""
    return {
        "mode_test": bool(getattr(settings, "RSM_MODE_TEST", False)),
        "timesource_mode": getattr(settings, "RSM_TIMESOURCE_MODE", "local_stub"),
        "seal_mode": getattr(settings, "RSM_SEAL_MODE", "disabled"),
        "esign_mode": getattr(settings, "RSM_ESIGN_MODE", "disabled"),
        "mfa_mode": getattr(settings, "RSM_MFA_MODE", "disabled"),
        "interop_banques_mode": getattr(
            settings, "RSM_INTEROP_BANQUES_MODE", "disabled",
        ),
    }


def _serialiser_utilisateur(utilisateur):
    """Représentation minimale et non sensible de l'utilisateur courant."""
    base = {"systeme": _info_systeme()}
    if not utilisateur or not utilisateur.is_authenticated:
        return {**base, "authentifie": False, "roles": []}
    return {
        **base,
        "authentifie": True,
        "id": utilisateur.id,
        "username": utilisateur.username,
        "nom_affichage": getattr(utilisateur, "nom_affichage", "")
        or utilisateur.get_full_name()
        or utilisateur.username,
        "identifiant_officiel": getattr(utilisateur, "identifiant_officiel", ""),
        "roles": sorted(list(utilisateur.roles_actifs()))
        if hasattr(utilisateur, "roles_actifs")
        else [],
        "is_staff": bool(utilisateur.is_staff),
        "mot_de_passe_initial": bool(
            getattr(utilisateur, "mot_de_passe_initial", False)
        ),
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class WhoamiView(APIView):
    """
    GET /api/v1/auth/whoami/

    Permission : ``AllowAny``. Pose le cookie ``csrftoken`` (requis pour
    tout POST ultérieur via ``SessionAuthentication``) et renvoie les
    informations minimales de l'utilisateur courant (ou l'état anonyme).
    La ``SessionAuthentication`` par défaut de DRF suffit : elle n'exige
    pas de jeton CSRF en GET et renseigne ``request.user`` à partir de
    la session Django si elle existe.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(_serialiser_utilisateur(request.user))


class LoginView(APIView):
    """
    POST /api/v1/auth/login/

    Corps attendu : ``{"username": "...", "password": "..."}``.
    Retourne la représentation de l'utilisateur courant sur succès,
    ou ``401`` sur échec. Aucune information métier exposée.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        if not username or not password:
            return Response(
                {"detail": "Identifiants manquants."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        utilisateur = authenticate(request, username=username, password=password)
        if utilisateur is None:
            return Response(
                {"detail": "Identifiants invalides."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not getattr(utilisateur, "compte_actif", True):
            return Response(
                {"detail": "Compte désactivé. Contactez l'administrateur."},
                status=status.HTTP_403_FORBIDDEN,
            )
        login(request, utilisateur)
        # Rafraîchit le jeton CSRF de session pour le client.
        get_token(request)
        return Response(_serialiser_utilisateur(utilisateur))


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(_serialiser_utilisateur(None))


class ChangerMotDePasseView(APIView):
    """
    POST /api/v1/auth/changer-mot-de-passe/

    Corps attendu :
      ``{"ancien": "...", "nouveau": "...", "confirmation": "..."}``

    Comportement :
    - vérifie l'ancien mot de passe ;
    - vérifie que ``nouveau == confirmation`` et que ``nouveau != ancien`` ;
    - applique les validateurs Django (longueur, similarité, communs) ;
    - persiste le nouveau mot de passe + ``mot_de_passe_initial = False`` ;
    - rafraîchit le hash de session pour ne pas déconnecter l'utilisateur.

    ⚠️ Cette opération est strictement technique :
    - aucune entrée n'est écrite dans le journal d'audit métier (art. 79) ;
    - aucun effet juridique n'est attaché au changement ;
    - la responsabilité du compte demeure pleinement celle de
      l'utilisateur dès lors qu'il prend la main sur son mot de passe.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        utilisateur = request.user
        ancien = request.data.get("ancien") or ""
        nouveau = request.data.get("nouveau") or ""
        confirmation = request.data.get("confirmation") or ""

        if not utilisateur.check_password(ancien):
            return Response(
                {"detail": "Ancien mot de passe incorrect.",
                 "code": "ancien_invalide"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if nouveau != confirmation:
            return Response(
                {"detail": "Le nouveau mot de passe et sa confirmation diffèrent.",
                 "code": "confirmation_differente"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if nouveau == ancien:
            return Response(
                {"detail": "Le nouveau mot de passe doit être différent de l'ancien.",
                 "code": "identique_a_ancien"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(nouveau, user=utilisateur)
        except PasswordValidationError as e:
            return Response(
                {"detail": " ".join(e.messages),
                 "code": "validation_echouee"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        utilisateur.set_password(nouveau)
        utilisateur.mot_de_passe_initial = False
        utilisateur.save(update_fields=["password", "mot_de_passe_initial"])
        # Empêche la déconnexion immédiate après changement de hash.
        update_session_auth_hash(request, utilisateur)

        return Response(_serialiser_utilisateur(utilisateur))
