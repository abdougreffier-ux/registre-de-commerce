"""
Admin — demandes de modification et snapshots.

Les demandes sont créées par les services (agent / déclarant externe) et
leur application passe EXCLUSIVEMENT par
``apps.modifications.services.appliquer_modification``. L'admin Django
ne doit jamais offrir un chemin d'écriture alternatif (§ 4.1 TDR).

Les snapshots sont append-only (art. 79).
"""
from django.contrib import admin

from apps.core.admin_base import ConsultationMetierAdmin, LectureSeuleAdmin
from apps.modifications.models import DemandeModification, SnapshotInscription


@admin.register(DemandeModification)
class DemandeModificationAdmin(ConsultationMetierAdmin):
    list_display = (
        "id", "inscription", "statut",
        "motif_refus_code", "applique_le", "cree_le",
    )
    list_filter = ("statut", "motif_refus_code")
    search_fields = (
        "inscription__numero_ordre",
        "objet_modification_fr", "objet_modification_ar",
    )


@admin.register(SnapshotInscription)
class SnapshotInscriptionAdmin(LectureSeuleAdmin):
    list_display = ("id", "inscription", "evenement", "instant", "acteur")
    list_filter = ("evenement",)
    search_fields = ("inscription__numero_ordre",)
    date_hierarchy = "instant"
    readonly_fields = ("contenu", "empreinte")
