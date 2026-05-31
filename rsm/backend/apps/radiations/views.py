from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import TransitionInterdite
from apps.radiations.models import DemandeRadiation
from apps.radiations.serializers import DemandeRadiationSerializer
from apps.radiations.services import appliquer_radiation


class ListeCreerRadiation(generics.ListCreateAPIView):
    queryset = DemandeRadiation.objects.order_by("-cree_le")
    serializer_class = DemandeRadiationSerializer

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user, modifie_par=self.request.user)


class AppliquerRadiation(APIView):
    def post(self, request, pk):
        demande = DemandeRadiation.objects.get(pk=pk)
        try:
            appliquer_radiation(demande=demande, acteur=request.user)
        except TransitionInterdite as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(DemandeRadiationSerializer(demande).data)
