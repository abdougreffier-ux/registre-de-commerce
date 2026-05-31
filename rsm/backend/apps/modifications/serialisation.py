"""
Sérialisation canonique d'une inscription pour les snapshots.

Principes :
- Rendu **déterministe** (clés triées, types normalisés) afin que deux
  sérialisations de la même inscription donnent rigoureusement le même
  contenu → prérequis pour un scellement fiable (§ 6.3 TDR).
- Portée FICHIER PUBLIC : on n'inclut que les rôles et biens ``actifs``,
  reflétant l'état opposable à l'instant de la sérialisation.
- Historique COMPLET : une vue miroir inclut également les éléments
  inactifs pour l'auditeur (cf. ``serialiser_inscription_integrale``).
- Neutralité linguistique (§ 6.3) : aucun texte rendu dans une seule
  langue ne dépend de la langue d'interface ; les champs bilingues sont
  rendus sous forme de paire ``{"fr": "...", "ar": "..."}``.
"""
from __future__ import annotations

from typing import Any

from django.core.serializers.json import DjangoJSONEncoder

from apps.biens.models import BienGreve
from apps.inscriptions.models import Inscription, RoleInscriptionPartie
from apps.parties.models import Partie, TypePartie


def _partie_a_dict(partie: Partie) -> dict[str, Any]:
    """Rend une partie sous forme de dict neutre linguistiquement."""
    if partie.type_partie == TypePartie.PERSONNE_PHYSIQUE:
        return {
            "type_partie": partie.type_partie,
            "nom": partie.nom,
            "prenom": partie.prenom,
            "date_naissance": (
                partie.date_naissance.isoformat() if partie.date_naissance else None
            ),
            "lieu_naissance": partie.lieu_naissance,
            "adresse": partie.adresse,
            "adresse_electronique": partie.adresse_electronique,
            "telephone": partie.telephone,
        }
    return {
        "type_partie": partie.type_partie,
        "denomination_sociale": partie.denomination_sociale,
        "numero_rc": partie.numero_rc,
        "adresse": partie.adresse,
        "adresse_electronique": partie.adresse_electronique,
        "telephone": partie.telephone,
    }


def _bien_a_dict(bien: BienGreve) -> dict[str, Any]:
    return {
        "id": bien.id,
        "actif": bien.actif,
        "marque": bien.marque,
        "modele": bien.modele,
        "annee": bien.annee,
        "numero_serie": bien.numero_serie,
        "description": {
            "fr": bien.description_fr,
            "ar": bien.description_ar,
            "langue_faisant_foi": bien.langue_faisant_foi_description,
        },
    }


def _role_a_dict(lien: RoleInscriptionPartie) -> dict[str, Any]:
    return {
        "id": lien.id,
        "actif": lien.actif,
        "role": lien.role,
        "ordre": lien.ordre,
        "partie_id": lien.partie_id,
        "partie": _partie_a_dict(lien.partie),
    }


def _scalaires(inscription: Inscription) -> dict[str, Any]:
    return {
        "nature_droit": inscription.nature_droit,
        "somme_garantie": (
            str(inscription.somme_garantie)
            if inscription.somme_garantie is not None else None
        ),
        "monnaie": inscription.monnaie,
        "duree_en_jours": inscription.duree_en_jours,
        "date_expiration": (
            inscription.date_expiration.isoformat()
            if inscription.date_expiration else None
        ),
        "adresse_electronique_notifications":
            inscription.adresse_electronique_notifications,
        "statut": inscription.statut,
        "fichier_actuel": inscription.fichier_actuel,
        "mention_radiee": inscription.mention_radiee,
    }


def serialiser_inscription(inscription: Inscription) -> dict[str, Any]:
    """
    Sérialise l'inscription dans son état OPPOSABLE à l'instant T
    (rôles et biens actifs uniquement).
    """
    roles = list(
        inscription.roles_parties.filter(actif=True)
        .select_related("partie")
        .order_by("role", "ordre", "id")
    )
    biens = list(
        inscription.biens.filter(actif=True).order_by("id")
    )
    return {
        "reference_demande": str(inscription.reference_demande),
        "numero_ordre": inscription.numero_ordre,
        "scalaires": _scalaires(inscription),
        "roles_parties": [_role_a_dict(r) for r in roles],
        "biens_greves": [_bien_a_dict(b) for b in biens],
    }


def serialiser_inscription_integrale(inscription: Inscription) -> dict[str, Any]:
    """
    Sérialise l'inscription AVEC son historique (actifs + inactifs).

    Destiné à l'auditeur (§ 5.2 TDR) : permet de constater à la fois
    l'état courant et l'ensemble des éléments qui en sont sortis.
    """
    roles = list(
        inscription.roles_parties.all()
        .select_related("partie")
        .order_by("role", "ordre", "id")
    )
    biens = list(inscription.biens.all().order_by("id"))
    return {
        "reference_demande": str(inscription.reference_demande),
        "numero_ordre": inscription.numero_ordre,
        "scalaires": _scalaires(inscription),
        "roles_parties": [_role_a_dict(r) for r in roles],
        "biens_greves": [_bien_a_dict(b) for b in biens],
    }


def encoder_canonique(payload: dict[str, Any]) -> bytes:
    """
    Encode un payload sous forme d'octets déterministes (UTF-8, clés triées).
    """
    import json
    return json.dumps(
        payload, cls=DjangoJSONEncoder,
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
