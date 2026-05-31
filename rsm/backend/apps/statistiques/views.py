from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.serializers import StrictModelSerializer
from apps.statistiques.models import ExtractionStatistique
from apps.statistiques.services import (
    calculer_indicateurs,
    calculer_indicateurs_financement_pme,
    produire_extraction,
)


class ExtractionStatistiqueSerializer(StrictModelSerializer):
    class Meta:
        model = ExtractionStatistique
        fields = ["id", "instant", "producteur", "perimetre", "resultat"]


class ListeExtractions(generics.ListAPIView):
    """Historique des extractions traçables (art. 82)."""

    queryset = ExtractionStatistique.objects.order_by("-instant")
    serializer_class = ExtractionStatistiqueSerializer


class IndicateursStatistiques(APIView):
    """
    Lecture des indicateurs agrégés.

    Accessible à tout utilisateur authentifié — la lecture des
    statistiques publiques relève de la consultation. La PRODUCTION
    formelle d'une extraction (avec écriture en journal d'audit et
    enregistrement traçable) reste réservée au greffe via l'endpoint
    ``/statistiques/produire/`` (monopole art. 82).

    Filtres acceptés (querystring) :
      - ``date_debut`` (YYYY-MM-DD)
      - ``date_fin`` (YYYY-MM-DD)
      - ``nature_droit`` (clé limitative art. 76)
      - ``canal_saisie`` (guichet_papier | portail_electronique)
      - ``statut`` (clé du workflow)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        perimetre = {
            cle: request.query_params.get(cle)
            for cle in ("date_debut", "date_fin", "nature_droit",
                        "canal_saisie", "statut")
            if request.query_params.get(cle)
        }
        return Response(calculer_indicateurs(perimetre))


class IndicateursFinancementPME(APIView):
    """
    Indicateurs ciblés sur l'accès au financement des PME.

    ⚠️ Indicateurs de PROXY — voir le champ ``meta.limitation`` dans la
    réponse pour la portée exacte (le décret 2021-033 ne définit pas la
    PME et le modèle de données ne collecte ni l'effectif, ni le
    secteur, ni le chiffre d'affaires).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        perimetre = {
            cle: request.query_params.get(cle)
            for cle in ("date_debut", "date_fin", "nature_droit",
                        "canal_saisie", "statut")
            if request.query_params.get(cle)
        }
        return Response(calculer_indicateurs_financement_pme(perimetre))


class ProduireExtraction(APIView):
    """Production formelle (greffe) — trace une extraction immuable."""

    def post(self, request):
        extraction = produire_extraction(
            acteur=request.user, perimetre=request.data.get("perimetre"),
        )
        return Response({
            "id": extraction.pk,
            "instant": extraction.instant.isoformat(timespec="seconds"),
            "resultat": extraction.resultat,
        })
