"""
Middleware exposant l'acteur courant et son contexte aux services d'audit.

Les services d'écriture du journal doivent pouvoir retrouver l'acteur
authentifié sans que les vues aient à le passer explicitement à chaque
appel. Ce middleware stocke le contexte dans une variable de contexte
(``contextvars``), compatible avec l'asynchrone.
"""
from __future__ import annotations

import contextvars
from typing import Optional

from apps.audit.services import ContexteAudit

_contexte_actuel: contextvars.ContextVar[Optional[ContexteAudit]] = contextvars.ContextVar(
    "rsm_contexte_audit", default=None
)


def contexte_courant() -> ContexteAudit:
    """Retourne le contexte d'audit résolu pour la requête en cours."""
    return _contexte_actuel.get() or ContexteAudit()


class CurrentActorMiddleware:
    """Peuple le contexte d'audit pour toute requête HTTP."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        acteur_id = user.pk if (user is not None and user.is_authenticated) else None
        role = ""
        # Le rôle applicatif (§ 4.1) sera résolu par l'app utilisateurs
        # lorsqu'elle exposera une API stable ; pour l'instant, on laisse vide.
        token = _contexte_actuel.set(
            ContexteAudit(
                acteur_id=acteur_id,
                acteur_role=role,
                adresse_ip=_resoudre_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
            )
        )
        try:
            return self.get_response(request)
        finally:
            _contexte_actuel.reset(token)


def _resoudre_ip(request) -> str | None:
    # X-Forwarded-For uniquement si le reverse proxy est contrôlé ;
    # à raffiner lors de l'arbitrage infrastructure.
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None
