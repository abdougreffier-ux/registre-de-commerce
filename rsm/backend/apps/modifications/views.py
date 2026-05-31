from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import ModificationSansEffet
from apps.modifications.models import DemandeModification
from apps.modifications.serializers import DemandeModificationSerializer
from apps.modifications.services import appliquer_modification


class ListeCreerModification(generics.ListCreateAPIView):
    queryset = DemandeModification.objects.order_by("-cree_le")
    serializer_class = DemandeModificationSerializer

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user, modifie_par=self.request.user)


class AppliquerModification(APIView):
    def post(self, request, pk):
        demande = DemandeModification.objects.get(pk=pk)
        try:
            appliquer_modification(demande=demande, acteur=request.user)
        except ModificationSansEffet as exc:
            return Response(
                {"detail": str(exc), "article": exc.article},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(DemandeModificationSerializer(demande).data)
