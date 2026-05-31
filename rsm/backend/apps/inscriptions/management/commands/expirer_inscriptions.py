"""
Tâche d'expiration automatique — articles 78 al. 3, 85, 92 al. 3.

Exécution journalière (via cron / scheduler d'exploitation) :

    python manage.py expirer_inscriptions

Effets :
1. Détecte les inscriptions en cours de validité (INSCRITE, MODIFIEE,
   RENOUVELEE, RADIEE) dont la date d'expiration est atteinte ou
   dépassée.
2. Pour chacune : transition vers EXPIREE.
3. Transition enchaînée : EXPIREE → ARCHIVEE, avec bascule du champ
   ``fichier_actuel`` vers le fichier général (art. 77, 79, 92 al. 3).

⚠️ La détection s'appuie sur la source de temps locale ; tant que la
source de temps officielle n'est pas arbitrée (ZONE GELÉE § 5.1), les
transitions produites ne sont pas juridiquement opposables.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.audit.services import tracer
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.core.enums import FichierRegistre
from apps.inscriptions.models import Inscription
from apps.workflow.services import appliquer_transition
from apps.workflow.statuts import (
    STATUTS_FICHIER_PUBLIC,
    StatutInscription,
)


class Command(BaseCommand):
    help = "Expire et archive les inscriptions dont la durée est écoulée."

    def handle(self, *args, **options):
        aujourdhui = timezone.localdate()
        candidats = Inscription.objects.filter(
            statut__in=list(STATUTS_FICHIER_PUBLIC),
            date_expiration__lte=aujourdhui,
        )
        n = 0
        for inscription in candidats:
            self._expirer_puis_archiver(inscription)
            n += 1
        self.stdout.write(self.style.SUCCESS(
            f"Expirées et archivées : {n} inscription(s)."
        ))

    @transaction.atomic
    def _expirer_puis_archiver(self, inscription: Inscription) -> None:
        # 1. Transition EXPIREE.
        appliquer_transition(
            numero_inscription=inscription.numero_ordre,
            statut_actuel=inscription.statut,
            statut_cible=StatutInscription.EXPIREE,
            evenement="expiration_automatique",
            acteur=None,
            motif="Date d'expiration atteinte.",
        )
        inscription.statut = StatutInscription.EXPIREE
        super(Inscription, inscription).save(update_fields=["statut"])

        # 2. Transition ARCHIVEE + bascule fichier.
        appliquer_transition(
            numero_inscription=inscription.numero_ordre,
            statut_actuel=StatutInscription.EXPIREE,
            statut_cible=StatutInscription.ARCHIVEE,
            evenement="transfert_fichier_general",
            acteur=None,
            motif="Transfert au fichier général (art. 92 al. 3).",
        )
        inscription.statut = StatutInscription.ARCHIVEE
        inscription.fichier_actuel = FichierRegistre.GENERAL
        super(Inscription, inscription).save(
            update_fields=["statut", "fichier_actuel"]
        )

        tracer(
            categorie=CategorieAudit.SYSTEME,
            action_cle="inscription.expirer_archiver",
            resultat=ResultatAudit.SUCCES,
            objet_type="inscription",
            objet_reference=inscription.numero_ordre or "",
            details={"motif": "expiration automatique", "fichier_cible": "general"},
        )
