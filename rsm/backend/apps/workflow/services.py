"""
Moteur d'exécution des transitions — TDR § 4.3.

Interface unique : ``appliquer_transition(...)``. Toute transition de statut
passe obligatoirement par ce service, qui :

1. Vérifie la transition dans la matrice (autorisée ET non interdite).
2. Instancie l'horodatage (stub, ZONE GELÉE § 5.1).
3. Ecrit une ligne d'historique non modifiable.
4. Ecrit une entrée au journal d'audit.
5. Met à jour le statut courant de l'inscription (côté appelant).

Le service NE persiste PAS l'inscription (responsabilité de l'appelant),
mais il renvoie le nouveau statut et la ligne d'historique créée.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from django.db import transaction
from django.utils import timezone

from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.core.exceptions import TransitionInterdite
from apps.workflow.models import TransitionStatut
from apps.workflow.statuts import (
    Transition,
    est_explicitement_interdite,
    transition_requise,
)


@dataclass(frozen=True)
class ResultatTransition:
    transition: Transition
    trace: TransitionStatut


@transaction.atomic
def appliquer_transition(
    *,
    numero_inscription: str,
    statut_actuel: str,
    statut_cible: str,
    evenement: str,
    acteur=None,
    acteur_role: str = "",
    motif: str = "",
    details_audit: Mapping[str, Any] | None = None,
) -> ResultatTransition:
    """Applique la transition demandée, dans une transaction atomique."""
    # 1. Interdiction explicite (§ 4.3).
    interdiction = est_explicitement_interdite(statut_actuel, statut_cible)
    if interdiction:
        raise TransitionInterdite(interdiction)

    # 2. Conformité à la matrice.
    try:
        t = transition_requise(statut_actuel, statut_cible, evenement)
    except LookupError as exc:
        raise TransitionInterdite(str(exc)) from exc

    # 3. Horodatage (stub — cf. apps.core.horodatage).
    instant = timezone.now()

    # 4. Historique (append-only).
    trace = TransitionStatut(
        numero_inscription=numero_inscription,
        statut_avant=statut_actuel,
        statut_apres=statut_cible,
        evenement=t.evenement,
        articles_fondateurs=", ".join(f"art. {a}" for a in t.articles),
        motif=motif or t.motif,
        instant=instant,
        acteur=acteur,
        acteur_role=acteur_role,
        automatique=t.automatique,
    )
    # save direct via Django (le modèle bloque les updates/deletes).
    super(TransitionStatut, trace).save()

    # 5. Journal d'audit.
    from apps.audit.middleware import contexte_courant

    contexte = contexte_courant()
    tracer(
        categorie=CategorieAudit.VALIDATION if evenement.startswith("validation")
        else CategorieAudit.DEMANDE,
        action_cle=f"transition.{evenement}",
        resultat=ResultatAudit.SUCCES,
        objet_type="inscription",
        objet_reference=numero_inscription,
        details={
            "statut_avant": statut_actuel,
            "statut_apres": statut_cible,
            "articles": list(t.articles),
            "motif": motif or t.motif,
            "complements": dict(details_audit or {}),
        },
        contexte=contexte,
    )

    return ResultatTransition(transition=t, trace=trace)
