"""
Signaux de l'app ``utilisateurs``.

Toute création, activation ou désactivation d'une affectation de rôle est
tracée au journal d'audit (§ 5.2 TDR, catégorie « compte »). Aucune
logique d'autorisation ne se trouve ici ; elle réside dans
``apps.utilisateurs.habilitations``.

⚠️ Important : le TDR § 4.1 prohibe le cumul des rôles agent de saisie et
autorité de validation *sur la même demande*, pas au niveau du compte.
Le compte peut donc porter simultanément les deux rôles pour des raisons
d'exploitation (remplacement, polyvalence), à condition que la
séparation soit respectée au moment de la saisie / validation d'UNE
demande donnée (voir ``habilitations.peut_valider_demande``).
"""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.utilisateurs.models import AffectationRole


@receiver(post_save, sender=AffectationRole)
def _tracer_affectation_role(sender, instance: AffectationRole, created, **kwargs):
    tracer(
        categorie=CategorieAudit.COMPTE,
        action_cle=(
            "affectation.creer" if created else "affectation.mettre_a_jour"
        ),
        resultat=ResultatAudit.SUCCES,
        objet_type="affectation_role",
        objet_reference=str(instance.pk),
        details={
            "utilisateur_id": instance.utilisateur_id,
            "role": instance.role,
            "actif": instance.actif,
            "motif": instance.motif_affectation,
        },
    )
