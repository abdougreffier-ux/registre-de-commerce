"""Vues d'audit — lecture seule, destinées à l'auditeur."""
from __future__ import annotations

from rest_framework import filters, generics, permissions
from rest_framework.response import Response

from apps.audit.models import EntreeAudit
from apps.audit.services import verifier_chaine
from apps.core.serializers import StrictModelSerializer


class _PermissionLectureAudit(permissions.BasePermission):
    """
    Placeholder — le rôle Auditeur n'est pas encore formellement attribué
    (cf. app. ``utilisateurs``). Pour l'instant, ``is_staff`` suffit à
    représenter un profil habilité en développement. À remplacer par la
    vérification du rôle « auditeur » lorsque la matrice sera opérationnelle.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class EntreeAuditSerializer(StrictModelSerializer):
    class Meta:
        model = EntreeAudit
        fields = [
            "id",
            "instant",
            "categorie",
            "action_cle",
            "acteur",
            "acteur_role",
            "objet_type",
            "objet_reference",
            "resultat",
            "details",
            "adresse_ip",
            "user_agent",
            "empreinte_precedente",
            "empreinte",
        ]
        read_only_fields = fields


class ListeEntreesAudit(generics.ListAPIView):
    queryset = EntreeAudit.objects.all()
    serializer_class = EntreeAuditSerializer
    permission_classes = [_PermissionLectureAudit]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["instant", "categorie", "resultat"]
    ordering = ["-instant"]


class VerificationChaineAudit(generics.GenericAPIView):
    permission_classes = [_PermissionLectureAudit]

    def get(self, request):
        ok, premier_id_altere = verifier_chaine()
        return Response(
            {"integre": ok, "premiere_entree_alteree": premier_id_altere}
        )
