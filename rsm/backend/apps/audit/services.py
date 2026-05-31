"""
Service d'écriture du journal d'audit.

Interface unique : ``tracer(...)``. Tous les modules métier passent par cette
fonction ; aucun ``EntreeAudit.objects.create`` direct n'est autorisé.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit.models import CategorieAudit, EntreeAudit, ResultatAudit


@dataclass(frozen=True)
class ContexteAudit:
    """Éléments non métier liés à l'acte (IP, user-agent, rôle actif)."""

    acteur_id: int | None = None
    acteur_role: str = ""
    adresse_ip: str | None = None
    user_agent: str = ""


def _canonicaliser(payload: Mapping[str, Any]) -> bytes:
    """Sérialisation déterministe (clés triées) pour le calcul d'empreinte."""
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _derniere_empreinte() -> str:
    dernier = EntreeAudit.objects.order_by("-id").only("empreinte").first()
    return dernier.empreinte if dernier else ""


def _calculer_empreinte(entree_donnees: Mapping[str, Any], precedente: str) -> str:
    """
    Chaînage d'empreintes : l'empreinte de l'entrée n englobe l'empreinte de
    l'entrée n-1, de sorte que toute altération rétroactive soit détectable.

    Algorithme : SHA-256. La valeur produite n'est pas juridiquement
    opposable tant que la politique cryptographique globale (§ 5.1, zone
    gelée) n'a pas été arbitrée par le MO.
    """
    corps = {"precedente": precedente, "entree": entree_donnees}
    return hashlib.sha256(_canonicaliser(corps)).hexdigest()


@transaction.atomic
def tracer(
    *,
    categorie: str,
    action_cle: str,
    resultat: str = ResultatAudit.SUCCES,
    objet_type: str = "",
    objet_reference: str = "",
    details: Mapping[str, Any] | None = None,
    contexte: ContexteAudit | None = None,
) -> EntreeAudit:
    """
    Ajoute une entrée au journal d'audit.

    L'ensemble est exécuté dans une transaction ; en cas d'échec, aucune
    trace n'est enregistrée (cohérence).
    """
    if categorie not in dict(CategorieAudit.choices):
        raise ValueError(f"Catégorie d'audit invalide : {categorie!r}")
    if resultat not in dict(ResultatAudit.choices):
        raise ValueError(f"Résultat d'audit invalide : {resultat!r}")

    contexte = contexte or ContexteAudit()
    details_ = dict(details or {})
    instant = timezone.now()

    precedente = _derniere_empreinte()
    payload = {
        "instant": instant.isoformat(timespec="seconds"),
        "categorie": categorie,
        "action_cle": action_cle,
        "resultat": resultat,
        "acteur_id": contexte.acteur_id,
        "acteur_role": contexte.acteur_role,
        "objet_type": objet_type,
        "objet_reference": objet_reference,
        "details": details_,
    }
    empreinte = _calculer_empreinte(payload, precedente)

    # On contourne .save() pour la toute première écriture (autrement bloquée
    # par l'override de save), via un manager `create` interne.
    entree = EntreeAudit(
        instant=instant,
        categorie=categorie,
        action_cle=action_cle,
        resultat=resultat,
        acteur_id=contexte.acteur_id,
        acteur_role=contexte.acteur_role,
        adresse_ip=contexte.adresse_ip,
        user_agent=contexte.user_agent,
        objet_type=objet_type,
        objet_reference=objet_reference,
        details=details_,
        empreinte_precedente=precedente,
        empreinte=empreinte,
    )
    # .save() normal : pk is None → création acceptée, une fois créée,
    # toute nouvelle save() est interdite par l'override.
    models_save = type(entree).__mro__[1].save  # django.db.models.Model.save
    models_save(entree)
    return entree


def verifier_chaine() -> tuple[bool, int | None]:
    """
    Recalcule la chaîne d'empreintes de bout en bout.

    Retourne ``(True, None)`` si la chaîne est intègre, ``(False, id)`` avec
    l'identifiant de la première entrée altérée sinon.

    Usage :
    - ``management command`` de vérification périodique ;
    - outil mis à disposition de l'auditeur (§ 4.1, § 5.2).
    """
    precedente = ""
    for entree in EntreeAudit.objects.order_by("id").iterator():
        payload = {
            "instant": entree.instant.isoformat(timespec="seconds"),
            "categorie": entree.categorie,
            "action_cle": entree.action_cle,
            "resultat": entree.resultat,
            "acteur_id": entree.acteur_id,
            "acteur_role": entree.acteur_role,
            "objet_type": entree.objet_type,
            "objet_reference": entree.objet_reference,
            "details": entree.details,
        }
        attendue = _calculer_empreinte(payload, precedente)
        if attendue != entree.empreinte or entree.empreinte_precedente != precedente:
            return False, entree.id
        precedente = entree.empreinte
    return True, None
