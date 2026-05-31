"""
Vues des référentiels.

- Lecture publique pour les listes (anonyme, AllowAny).
- Mutation de ``LibelleNatureDroit`` réservée aux rôles
  ``admin_fonctionnel`` et ``autorite_validation`` (le greffier doit
  pouvoir paramétrer la liste — directive MO post-bascule, 2026-05-30).

Toutes les mutations sont tracées au journal d'audit.
"""
from __future__ import annotations

from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.core.serializers import StrictModelSerializer
from apps.referentiels import models as M
from apps.utilisateurs.models import RoleApplicatif


class _LibelleSerializer(StrictModelSerializer):
    """Serializer générique — rend clé + libellés FR/AR + langue faisant foi."""

    class Meta:
        fields = [
            "cle", "libelle_fr", "libelle_ar", "langue_faisant_foi",
            "description_fr", "description_ar", "ordre", "actif",
        ]


def _factory(modele):
    """Fabrique une vue liste pour un modèle de libellé donné."""

    serializer_meta = type(
        f"_{modele.__name__}SerializerMeta",
        (_LibelleSerializer.Meta,),
        {"model": modele},
    )
    serializer_cls = type(
        f"_{modele.__name__}Serializer",
        (_LibelleSerializer,),
        {"Meta": serializer_meta},
    )

    class _View(generics.ListAPIView):
        queryset = modele.objects.filter(actif=True).order_by("ordre", "cle")
        serializer_class = serializer_cls
        permission_classes = [permissions.AllowAny]

    _View.__name__ = f"{modele.__name__}ListView"
    return _View


LibellesNatureDroitView = _factory(M.LibelleNatureDroit)
LibellesMotifRejetView = _factory(M.LibelleMotifRejet)
LibellesCanalSaisieView = _factory(M.LibelleCanalSaisie)
LibellesCritereRechercheView = _factory(M.LibelleCritereRecherche)
LibellesTypeCertificatView = _factory(M.LibelleTypeCertificat)


# --------------------------------------------------------------------------- #
#  Administration paramétrable de LibelleNatureDroit                          #
# --------------------------------------------------------------------------- #
ROLES_ADMIN_NATURES = {
    RoleApplicatif.ADMIN_FONCTIONNEL,
    RoleApplicatif.AUTORITE_VALIDATION,
}


def _verifier_role_admin_natures(utilisateur):
    if not utilisateur or not utilisateur.is_authenticated:
        raise PermissionDenied("Authentification requise.")
    roles = set(utilisateur.roles_actifs())
    if not (roles & ROLES_ADMIN_NATURES):
        raise PermissionDenied(
            "Seuls le greffier (autorité de validation) et "
            "l'administrateur fonctionnel peuvent paramétrer les natures "
            "de droit."
        )


class _NatureDroitAdminSerializer(StrictModelSerializer):
    """Serializer d'écriture — la ``cle`` ne peut pas être modifiée après création."""

    class Meta:
        model = M.LibelleNatureDroit
        fields = [
            "id", "cle", "libelle_fr", "libelle_ar",
            "description_fr", "description_ar", "ordre", "actif",
            "langue_faisant_foi",
        ]
        read_only_fields = ["id"]


class NatureDroitAdminListCreateView(generics.ListCreateAPIView):
    """
    GET : liste complète (actives + inactives) — utile au paramétrage.
    POST : création d'une nouvelle nature paramétrable.
    """

    queryset = M.LibelleNatureDroit.objects.all().order_by("ordre", "cle")
    serializer_class = _NatureDroitAdminSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        _verifier_role_admin_natures(request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        tracer(
            categorie=CategorieAudit.ADMIN,
            action_cle="referentiels.nature_droit.creer",
            resultat=ResultatAudit.SUCCES,
            objet_type="LibelleNatureDroit",
            objet_reference=instance.cle,
            details={
                "libelle_fr": instance.libelle_fr,
                "libelle_ar": instance.libelle_ar,
                "actif": instance.actif,
            },
            contexte=contexte_courant(),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NatureDroitAdminDetailView(generics.RetrieveUpdateAPIView):
    """
    GET : détail d'une nature.
    PATCH/PUT : mise à jour des libellés / ordre / actif.
    La ``cle`` ne peut pas être modifiée après création (préserve les
    références dans les inscriptions historiques — art. 79).
    """

    queryset = M.LibelleNatureDroit.objects.all()
    serializer_class = _NatureDroitAdminSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def update(self, request, *args, **kwargs):
        _verifier_role_admin_natures(request.user)
        instance = self.get_object()
        partial = kwargs.pop("partial", False)
        # Interdire la mutation de ``cle`` : un changement de clé orphaniserait
        # les inscriptions déjà déposées (rétroactivité — interdite).
        data = {k: v for k, v in request.data.items() if k != "cle"}
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        avant = {
            "libelle_fr": instance.libelle_fr,
            "libelle_ar": instance.libelle_ar,
            "actif": instance.actif,
            "ordre": instance.ordre,
        }
        instance = serializer.save()
        tracer(
            categorie=CategorieAudit.ADMIN,
            action_cle="referentiels.nature_droit.modifier",
            resultat=ResultatAudit.SUCCES,
            objet_type="LibelleNatureDroit",
            objet_reference=instance.cle,
            details={
                "avant": avant,
                "apres": {
                    "libelle_fr": instance.libelle_fr,
                    "libelle_ar": instance.libelle_ar,
                    "actif": instance.actif,
                    "ordre": instance.ordre,
                },
            },
            contexte=contexte_courant(),
        )
        return Response(serializer.data)
