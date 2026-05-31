"""
Admin — inscriptions, rôles des parties, pièces jointes, séquence.

Les inscriptions et leurs objets rattachés sont créés / mutés
EXCLUSIVEMENT par les services applicatifs (``apps.inscriptions.services``
et suivants). L'admin Django n'offre qu'un accès en consultation
(§ 4.1 TDR — aucun administrateur n'a de pouvoir d'écriture sur le métier ;
article 79 — conservation pérenne).
"""
from django.contrib import admin

from apps.core.admin_base import ConsultationMetierAdmin, LectureSeuleAdmin
from apps.inscriptions.models import (
    Inscription,
    PieceJointe,
    RoleInscriptionPartie,
    SequenceNumeroOrdre,
)


class RoleInline(admin.TabularInline):
    model = RoleInscriptionPartie
    extra = 0
    can_delete = False
    readonly_fields = (
        "partie", "role", "ordre",
        "actif", "date_fin_validite", "raison_fin",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class PieceJointeInline(admin.TabularInline):
    model = PieceJointe
    extra = 0
    can_delete = False
    readonly_fields = (
        "nom_original", "fichier", "type_mime",
        "taille_octets", "sceau_empreinte",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Inscription)
class InscriptionAdmin(ConsultationMetierAdmin):
    list_display = (
        "numero_ordre", "reference_demande", "statut",
        "canal_saisie", "nature_droit", "instant_arrivee",
        "instant_saisie_opposable", "date_expiration",
    )
    list_filter = ("statut", "fichier_actuel", "canal_saisie", "nature_droit")
    search_fields = ("numero_ordre", "reference_demande")
    date_hierarchy = "instant_arrivee"
    inlines = [RoleInline, PieceJointeInline]


@admin.register(RoleInscriptionPartie)
class RoleInscriptionPartieAdmin(ConsultationMetierAdmin):
    list_display = ("inscription", "partie", "role", "ordre",
                    "actif", "date_fin_validite")
    list_filter = ("role", "actif")


@admin.register(PieceJointe)
class PieceJointeAdmin(ConsultationMetierAdmin):
    list_display = ("inscription", "nom_original", "type_mime", "taille_octets")


@admin.register(SequenceNumeroOrdre)
class SequenceNumeroOrdreAdmin(LectureSeuleAdmin):
    """
    Article 78 — le compteur est géré EXCLUSIVEMENT par le service
    ``attribuer_numero_ordre``. Aucune édition via l'admin n'est admise,
    sous peine de rompre l'unicité et la chronologie.
    """

    list_display = ("pk", "prochaine_valeur")
