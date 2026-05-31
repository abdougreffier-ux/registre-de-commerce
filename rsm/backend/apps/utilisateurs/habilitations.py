"""
Règles d'habilitation — TDR § 4.1, § 5.1.

Ce module centralise les autorisations applicatives. Toute décision (qui
peut faire quoi) passe par une de ces fonctions. Aucune vue, aucun service
métier ne contient de logique d'autorisation en dur.

Séparation stricte des fonctions :
- Aucun utilisateur ne peut cumuler ``agent_saisie`` et
  ``autorite_validation`` sur la même demande.
- Les administrateurs ne peuvent pas créer / modifier / supprimer d'objet
  métier (inscription, modification, radiation).
- L'auditeur a un accès en lecture seule à tout.
"""
from __future__ import annotations

from apps.utilisateurs.models import (
    ROLES_ADMINISTRATION,
    ROLES_INCOMPATIBLES,
    RoleApplicatif,
    Utilisateur,
)


class AutorisationRefusee(PermissionError):
    """Levée lorsqu'un acte est refusé au regard des rôles de l'acteur."""


def _roles(utilisateur: Utilisateur) -> set[str]:
    return set(utilisateur.roles_actifs())


# --------------------------------------------------------------------------- #
# Écriture métier                                                              #
# --------------------------------------------------------------------------- #
def peut_enregistrer_demande(utilisateur: Utilisateur) -> bool:
    """Droit de créer une demande (agent de saisie ou déclarant externe)."""
    r = _roles(utilisateur)
    return bool(
        r & {RoleApplicatif.AGENT_SAISIE, RoleApplicatif.DECLARANT_EXTERNE}
    )


def peut_valider_demande(
    utilisateur: Utilisateur, *, saisie_par: Utilisateur | None
) -> bool:
    """
    Droit de valider (ou rejeter) une demande.

    Refuse si l'acteur cumulerait saisie et validation sur CETTE demande
    (séparation stricte).
    """
    if not utilisateur.a_role(RoleApplicatif.AUTORITE_VALIDATION):
        return False
    if saisie_par is not None and saisie_par.pk == utilisateur.pk:
        return False
    return True


def verifier_non_cumul(utilisateur: Utilisateur) -> None:
    """
    Bloque la présence simultanée de rôles incompatibles (§ 4.1).
    """
    roles = _roles(utilisateur)
    for a, b in ROLES_INCOMPATIBLES:
        if a in roles and b in roles:
            raise AutorisationRefusee(
                f"Cumul interdit : {a} + {b} sur le même utilisateur."
            )


def ecriture_metier_autorisee(utilisateur: Utilisateur) -> bool:
    """Les administrateurs n'ont jamais d'accès utile aux contenus métier."""
    return not (_roles(utilisateur) & ROLES_ADMINISTRATION)


# --------------------------------------------------------------------------- #
# Lecture / audit                                                              #
# --------------------------------------------------------------------------- #
def peut_lire_audit(utilisateur: Utilisateur) -> bool:
    return utilisateur.a_role(RoleApplicatif.AUDITEUR)


def peut_produire_statistiques(utilisateur: Utilisateur) -> bool:
    """Monopole du greffe — article 82."""
    return utilisateur.a_role(RoleApplicatif.PROD_STATS)
