"""
Gestionnaire d'exceptions REST — uniforme et traçable.

Toute exception métier du système RSM est traduite en réponse HTTP
structurée :
- ``detail`` : message destiné au déposant ;
- ``article`` : article du décret 2021-033 fondant le refus (vide si
  aucun article précis n'est invoqué) ;
- ``classe`` : identifiant technique (utile au support).

Codes HTTP retenus :
- 400 pour les erreurs métier (``ErreurMetierRSM`` et filles) ;
- 403 pour les refus d'habilitation (``AutorisationRefusee``,
  ``PermissionError`` hors journal d'audit).

Les exceptions d'altération du journal d'audit (``PermissionError``
lancé par l'override de ``save`` / ``delete``) sont également traduites
en 403 : la demande émane d'un acteur qui tente une opération qu'aucun
rôle n'autorise.
"""
from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler


def rsm_exception_handler(exc, context):
    # 1. Exceptions métier typées.
    from apps.core.exceptions import ErreurMetierRSM
    from apps.utilisateurs.habilitations import AutorisationRefusee

    if isinstance(exc, AutorisationRefusee):
        return Response(
            {
                "detail": str(exc) or "Autorisation refusée.",
                "article": "",
                "classe": "AutorisationRefusee",
            },
            status=403,
        )

    if isinstance(exc, ErreurMetierRSM):
        return Response(
            {
                "detail": str(exc),
                "article": exc.article,
                "classe": exc.__class__.__name__,
            },
            status=400,
        )

    # 2. PermissionError (protection append-only, etc.).
    if isinstance(exc, PermissionError):
        return Response(
            {
                "detail": str(exc),
                "article": "79",
                "classe": "PermissionError",
            },
            status=403,
        )

    # 3. Comportement DRF par défaut (404, 400 pour ValidationError, etc.).
    return drf_default_handler(exc, context)
