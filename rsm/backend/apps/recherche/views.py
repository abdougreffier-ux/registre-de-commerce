"""Endpoint public de recherche — art. 94-97."""
from __future__ import annotations

from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import RechercheCriteresInsuffisants
from apps.core.serializers import StrictInputSerializer
from apps.inscriptions.serializers import InscriptionSerializer
from apps.recherche.services import CriteresRecherche, rechercher


class _CriteresSerializer(StrictInputSerializer):
    """
    Article 96 — seuls les QUATRE critères limitatifs sont admis.
    Toute clé hors liste est rejetée explicitement par le mixin strict.
    """
    nom_constituant = serializers.CharField(required=False, allow_blank=True)
    numero_rc = serializers.CharField(required=False, allow_blank=True)
    numero_serie_bien = serializers.CharField(required=False, allow_blank=True)
    numero_inscription = serializers.CharField(required=False, allow_blank=True)


class RecherchePublique(APIView):
    """
    POST : lance une recherche publique (anonyme ou authentifiée).

    La réponse comprend :
    - l'instant de la recherche, à la seconde ;
    - les critères retenus ;
    - la liste des inscriptions du fichier public qui correspondent ;
    - pour chaque inscription, la liste EXHAUSTIVE des constituants
      homonymes (article 97 al. 2), lorsque le nom a été utilisé ;
    - un identifiant de requête pour le « certificat de recherche ».

    ⚠️ Le certificat de recherche probant (article 97 dernier alinéa) est
    GELÉ à ce stade. La présente réponse tient lieu d'aperçu non opposable.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = _CriteresSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            resultat = rechercher(
                CriteresRecherche(
                    nom_constituant=d.get("nom_constituant", ""),
                    numero_rc=d.get("numero_rc", ""),
                    numero_serie_bien=d.get("numero_serie_bien", ""),
                    numero_inscription=d.get("numero_inscription", ""),
                )
            )
        except RechercheCriteresInsuffisants as exc:
            return Response(
                {"detail": str(exc), "article": exc.article},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "instant": resultat.instant.isoformat(timespec="seconds"),
            "requete_id": resultat.requete_id,
            "criteres_utilises": resultat.criteres_utilises,
            "nombre_resultats": len(resultat.inscriptions),
            "inscriptions": InscriptionSerializer(resultat.inscriptions, many=True).data,
            "homonymes_par_inscription": {
                str(pk): homonymes
                for pk, homonymes in resultat.homonymes_par_inscription.items()
            },
            "avertissement": (
                "Aperçu non opposable — le certificat de recherche probant "
                "(art. 97) est GELÉ en attente d'arbitrage (scellement et "
                "source de temps)."
            ),
        })
