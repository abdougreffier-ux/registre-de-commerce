"""
Classes d'authentification spécifiques au RSM.

Mode TEST :
- ``RSM_MODE_TEST=true`` (défaut en environnement de test) :
  l'authentification de session reste **active** (cookie ``sessionid``
  obligatoire pour les endpoints protégés), mais la **vérification CSRF
  est désactivée** pour les appels API afin d'éviter les blocages liés
  au proxy de développement (Create React App réécrit l'``Origin`` à
  l'origine du backend, ce qui crée un mismatch fastidieux à diagnostiquer
  pour les testeurs fonctionnels).

Mode PRODUCTION :
- ``RSM_MODE_TEST=false`` : comportement strictement identique à celui
  de DRF : ``SessionAuthentication`` avec vérification CSRF complète.

Ce dispositif n'introduit AUCUNE règle métier ; il est purement
technique. Il est documenté comme tel dans la note L11 du mode TEST.
"""
from __future__ import annotations

from django.conf import settings
from rest_framework.authentication import SessionAuthentication


class SessionAuthSansCSRFEnTest(SessionAuthentication):
    """
    Variante de ``SessionAuthentication`` qui n'applique pas le
    contrôle CSRF lorsque ``settings.RSM_MODE_TEST`` vaut ``True``.

    Le contrôle de session (cookie ``sessionid``) reste pleinement
    appliqué. Aucune autorisation n'est ouverte aux requêtes anonymes.
    """

    def enforce_csrf(self, request):
        if bool(getattr(settings, "RSM_MODE_TEST", False)):
            # Mode TEST : on n'enforce pas le CSRF. La session reste
            # exigée par ``IsAuthenticated`` ; le cookie sessionid doit
            # être présent.
            return
        return super().enforce_csrf(request)
