"""
Application d'un renouvellement — article 91.

Règles mises en œuvre :
- refus strict si la date d'expiration est déjà atteinte ;
- prorogation = durée initiale de l'inscription, à partir de l'ancienne
  date d'expiration ;
- trace au journal d'audit et à l'historique de statut.
"""
from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.core.exceptions import RenouvellementHorsDelai
from apps.inscriptions.models import Inscription
from apps.renouvellements.models import (
    DemandeRenouvellement,
    StatutDemandeRenouvellement,
)
from apps.utilisateurs.habilitations import peut_valider_demande
from apps.workflow.services import appliquer_transition
from apps.workflow.statuts import StatutInscription, STATUTS_EN_COURS_DE_VALIDITE


@transaction.atomic
def appliquer_renouvellement(
    *, demande: DemandeRenouvellement, acteur,
) -> DemandeRenouvellement:
    inscription: Inscription = demande.inscription

    if inscription.statut not in STATUTS_EN_COURS_DE_VALIDITE:
        raise RenouvellementHorsDelai(
            "Renouvellement impossible : inscription non en cours (art. 91)."
        )
    aujourd_hui = timezone.localdate()
    if inscription.date_expiration is None or inscription.date_expiration < aujourd_hui:
        raise RenouvellementHorsDelai(
            "Renouvellement postérieur à l'expiration : refusé (art. 91)."
        )
    if not peut_valider_demande(acteur, saisie_par=demande.cree_par):
        from apps.utilisateurs.habilitations import AutorisationRefusee
        raise AutorisationRefusee(
            "Validation refusée (séparation stricte, § 4.1)."
        )

    duree_initiale = inscription.duree_en_jours
    ancienne_date = inscription.date_expiration
    nouvelle_date = ancienne_date + timedelta(days=duree_initiale)

    appliquer_transition(
        numero_inscription=inscription.numero_ordre,
        statut_actuel=inscription.statut,
        statut_cible=StatutInscription.RENOUVELEE,
        evenement="renouvellement_art91",
        acteur=acteur,
        motif=f"Prorogation de {duree_initiale} jours (art. 91).",
    )
    inscription.statut = StatutInscription.RENOUVELEE
    inscription.date_expiration = nouvelle_date
    inscription.modifie_par = acteur
    super(Inscription, inscription).save(
        update_fields=["statut", "date_expiration", "modifie_par"]
    )

    demande.statut = StatutDemandeRenouvellement.APPLIQUEE
    demande.ancienne_date_expiration = ancienne_date
    demande.nouvelle_date_expiration = nouvelle_date
    demande.applique_le = timezone.now()
    super(DemandeRenouvellement, demande).save(
        update_fields=[
            "statut", "ancienne_date_expiration",
            "nouvelle_date_expiration", "applique_le",
        ]
    )

    tracer(
        categorie=CategorieAudit.DEMANDE,
        action_cle="renouvellement.appliquer",
        resultat=ResultatAudit.SUCCES,
        objet_type="inscription",
        objet_reference=inscription.numero_ordre or "",
        details={
            "duree_en_jours": duree_initiale,
            "ancienne_expiration": ancienne_date.isoformat(),
            "nouvelle_expiration": nouvelle_date.isoformat(),
        },
        contexte=contexte_courant(),
    )
    return demande
