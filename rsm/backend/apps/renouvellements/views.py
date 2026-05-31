from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import RenouvellementHorsDelai
from apps.renouvellements.models import DemandeRenouvellement
from apps.renouvellements.serializers import DemandeRenouvellementSerializer
from apps.renouvellements.services import appliquer_renouvellement


class ListeCreerRenouvellement(generics.ListCreateAPIView):
    queryset = DemandeRenouvellement.objects.order_by("-cree_le")
    serializer_class = DemandeRenouvellementSerializer

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user, modifie_par=self.request.user)


class AppliquerRenouvellement(APIView):
    def post(self, request, pk):
        demande = DemandeRenouvellement.objects.get(pk=pk)
        try:
            appliquer_renouvellement(demande=demande, acteur=request.user)
        except RenouvellementHorsDelai as exc:
            return Response(
                {"detail": str(exc), "article": exc.article},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(DemandeRenouvellementSerializer(demande).data)
