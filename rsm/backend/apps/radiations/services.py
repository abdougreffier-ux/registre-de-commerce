"""
Application d'une radiation — article 92.

Effets :
1. Transition de l'inscription vers le statut « Radiée ».
2. Mention « radiée » activée au fichier public, conservation jusqu'à la
   date d'expiration.
3. Après la date d'expiration (transition automatique → EXPIREE → ARCHIVEE,
   gérée par le planificateur d'expiration), l'inscription sort du fichier
   public et est transférée au fichier général.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.core.exceptions import TransitionInterdite
from apps.inscriptions.models import Inscription
from apps.radiations.models import DemandeRadiation, StatutDemandeRadiation
from apps.utilisateurs.habilitations import peut_valider_demande
from apps.workflow.services import appliquer_transition
from apps.workflow.statuts import (
    STATUTS_EN_COURS_DE_VALIDITE,
    StatutInscription,
)


@transaction.atomic
def appliquer_radiation(
    *, demande: DemandeRadiation, acteur,
) -> DemandeRadiation:
    inscription: Inscription = demande.inscription
    if inscription.statut not in STATUTS_EN_COURS_DE_VALIDITE:
        raise TransitionInterdite(
            "Radiation impossible : inscription non en cours de validité."
        )
    if not peut_valider_demande(acteur, saisie_par=demande.cree_par):
        from apps.utilisateurs.habilitations import AutorisationRefusee
        raise AutorisationRefusee(
            "Validation refusée (séparation stricte, § 4.1)."
        )

    appliquer_transition(
        numero_inscription=inscription.numero_ordre,
        statut_actuel=inscription.statut,
        statut_cible=StatutInscription.RADIEE,
        evenement="radiation_art92",
        acteur=acteur,
        motif=f"Radiation fondée sur {demande.fondement}.",
    )
    inscription.statut = StatutInscription.RADIEE
    inscription.mention_radiee = True
    inscription.modifie_par = acteur
    super(Inscription, inscription).save(
        update_fields=["statut", "mention_radiee", "modifie_par"]
    )

    demande.statut = StatutDemandeRadiation.APPLIQUEE
    demande.applique_le = timezone.now()
    super(DemandeRadiation, demande).save(
        update_fields=["statut", "applique_le"]
    )

    tracer(
        categorie=CategorieAudit.DEMANDE,
        action_cle="radiation.appliquer",
        resultat=ResultatAudit.SUCCES,
        objet_type="inscription",
        objet_reference=inscription.numero_ordre or "",
        details={
            "fondement": demande.fondement,
            "mention_radiee_activee": True,
        },
        contexte=contexte_courant(),
    )
    return demande
