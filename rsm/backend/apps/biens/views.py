"""
Vues API des catégories de biens.

Lecture libre (toute personne authentifiée).
Écriture restreinte aux rôles ``admin_fonctionnel`` et ``autorite_validation``
(le greffier dispose donc de la possibilité d'ajouter/modifier des
catégories, conformément à la directive MO).

Audit : toute publication / modification de catégorie écrit une entrée
``CategorieAudit.COMPTE`` (catégorie reliée à la gestion du référentiel),
distincte de l'audit métier (art. 79 § 5.2).
"""
from __future__ import annotations

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.biens.models import CategorieBien
from apps.biens.serializers import (
    CategorieBienLectureSerializer, PublierCategorieSerializer,
)
from apps.biens.services import (
    SchemaCategorieInvalide, modifier_version, publier_nouvelle_version,
)
from apps.utilisateurs.models import RoleApplicatif


def _est_gestionnaire(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if not hasattr(user, "roles_actifs"):
        return False
    roles = set(user.roles_actifs())
    return bool(roles & {
        RoleApplicatif.AUTORITE_VALIDATION,
        RoleApplicatif.ADMIN_FONCTIONNEL,
    })


class ListeCategoriesBien(generics.ListAPIView):
    """GET /api/v1/categories-biens/ — liste des catégories actives."""

    permission_classes = [IsAuthenticated]
    serializer_class = CategorieBienLectureSerializer

    def get_queryset(self):
        actif = self.request.query_params.get("actif")
        qs = CategorieBien.objects.all().order_by("libelle_fr", "version")
        if actif in (None, "1", "true", "True"):
            qs = qs.filter(actif=True)
        elif actif in ("0", "false", "False"):
            qs = qs.filter(actif=False)
        return qs


class DetailCategorieBien(generics.RetrieveAPIView):
    """GET /api/v1/categories-biens/<id>/ — détail d'une version."""

    permission_classes = [IsAuthenticated]
    serializer_class = CategorieBienLectureSerializer
    queryset = CategorieBien.objects.all()


class PublierCategorieBien(APIView):
    """
    POST /api/v1/categories-biens/publier/ — publie une nouvelle version
    d'une catégorie (incrémente ``version``, désactive l'ancienne).

    Réservé aux gestionnaires.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _est_gestionnaire(request.user):
            raise PermissionDenied(
                "Réservé aux rôles « Autorité de validation » ou "
                "« Administrateur fonctionnel »."
            )
        payload = PublierCategorieSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        d = payload.validated_data
        try:
            cat = publier_nouvelle_version(
                cle=d["cle"],
                libelle_fr=d["libelle_fr"], libelle_ar=d["libelle_ar"],
                description_fr=d.get("description_fr", ""),
                description_ar=d.get("description_ar", ""),
                schema_champs=d["schema_champs"],
                affichage_observations=d.get("affichage_observations", True),
                acteur=request.user,
            )
        except SchemaCategorieInvalide as e:
            return Response(
                {"detail": str(e), "code": "schema_invalide"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tracer(
            categorie=CategorieAudit.COMPTE,  # catégorie « gestion du référentiel »
            action_cle="categorie_bien.publier",
            resultat=ResultatAudit.SUCCES,
            objet_type="categorie_bien",
            objet_reference=f"{cat.cle}@v{cat.version}",
            details={"cle": cat.cle, "version": cat.version,
                     "champs": [c["cle"] for c in cat.schema_champs]},
            contexte=contexte_courant(),
        )
        return Response(
            CategorieBienLectureSerializer(cat).data,
            status=status.HTTP_201_CREATED,
        )


class ModifierCategorieBien(APIView):
    """
    PATCH /api/v1/categories-biens/<id>/ — modifie une version NON UTILISÉE.

    Si la version est déjà référencée par un BienGreve, la modification
    est refusée (HTTP 409). Le gestionnaire doit alors publier une
    nouvelle version.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk: int):
        if not _est_gestionnaire(request.user):
            raise PermissionDenied(
                "Réservé aux rôles « Autorité de validation » ou "
                "« Administrateur fonctionnel »."
            )
        try:
            cat = CategorieBien.objects.get(pk=pk)
        except CategorieBien.DoesNotExist:
            return Response(
                {"detail": "Catégorie introuvable.", "code": "introuvable"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            cat = modifier_version(
                categorie=cat,
                libelle_fr=request.data.get("libelle_fr"),
                libelle_ar=request.data.get("libelle_ar"),
                description_fr=request.data.get("description_fr"),
                description_ar=request.data.get("description_ar"),
                schema_champs=request.data.get("schema_champs"),
                affichage_observations=request.data.get("affichage_observations"),
                acteur=request.user,
            )
        except ValueError as e:
            return Response(
                {"detail": str(e), "code": "deja_utilisee"},
                status=status.HTTP_409_CONFLICT,
            )
        except SchemaCategorieInvalide as e:
            return Response(
                {"detail": str(e), "code": "schema_invalide"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tracer(
            categorie=CategorieAudit.COMPTE,
            action_cle="categorie_bien.modifier",
            resultat=ResultatAudit.SUCCES,
            objet_type="categorie_bien",
            objet_reference=f"{cat.cle}@v{cat.version}",
            details={"cle": cat.cle, "version": cat.version},
            contexte=contexte_courant(),
        )
        return Response(CategorieBienLectureSerializer(cat).data)
