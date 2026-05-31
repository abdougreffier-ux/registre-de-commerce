"""Vues API des inscriptions."""
from __future__ import annotations

from decimal import Decimal

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import RejetForme
from apps.inscriptions.models import Inscription
from apps.inscriptions.serializers import (
    DeposerInscriptionSerializer,
    InscriptionSerializer,
    RejeterInscriptionSerializer,
)
from apps.inscriptions.services import (
    DonneesDemandeInscription,
    creer_demande,
    prononcer_rejet,
    valider_inscription,
)


class ListeDeposerInscription(generics.ListCreateAPIView):
    """
    GET : liste paginée des inscriptions (visible par les agents internes).
    POST : dépôt d'une nouvelle demande (§ 4.2.1).
    """

    queryset = Inscription.objects.order_by("-instant_arrivee")
    serializer_class = InscriptionSerializer

    def create(self, request, *args, **kwargs):
        payload = DeposerInscriptionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        d = payload.validated_data
        try:
            inscription = creer_demande(
                donnees=DonneesDemandeInscription(
                    canal_saisie=d["canal_saisie"],
                    nature_droit=d["nature_droit"],
                    somme_garantie=d.get("somme_garantie") or Decimal("0"),
                    monnaie=d.get("monnaie", ""),
                    duree_en_jours=d["duree_en_jours"],
                    adresse_electronique_notifications=d.get(
                        "adresse_electronique_notifications", ""
                    ),
                    montant_en_lettres_fr=d.get("montant_en_lettres_fr", ""),
                    montant_en_lettres_ar=d.get("montant_en_lettres_ar", ""),
                    nature_convention=d.get("nature_convention", ""),
                    date_convention=d.get("date_convention"),
                    debiteur_est_constituant=d.get(
                        "debiteur_est_constituant", False
                    ),
                    constituants=tuple(d.get("constituants") or []),
                    debiteurs=tuple(d.get("debiteurs") or []),
                    creanciers=tuple(d.get("creanciers") or []),
                    biens=tuple(d.get("biens") or []),
                ),
                acteur=request.user,
            )
        except RejetForme as exc:
            return Response(
                {"detail": str(exc), "article": exc.article},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            InscriptionSerializer(inscription).data,
            status=status.HTTP_201_CREATED,
        )


class DetailInscription(generics.RetrieveAPIView):
    queryset = Inscription.objects.all()
    serializer_class = InscriptionSerializer
    lookup_field = "reference_demande"


class ValiderInscription(APIView):
    def post(self, request, reference_demande):
        inscription = Inscription.objects.get(reference_demande=reference_demande)
        inscription = valider_inscription(
            inscription=inscription, acteur=request.user,
        )
        return Response(InscriptionSerializer(inscription).data)


class RejeterInscription(APIView):
    def post(self, request, reference_demande):
        payload = RejeterInscriptionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        inscription = Inscription.objects.get(reference_demande=reference_demande)
        inscription = prononcer_rejet(
            inscription=inscription,
            motif=payload.validated_data["motif"],
            commentaire_fr=payload.validated_data.get("commentaire_fr", ""),
            commentaire_ar=payload.validated_data.get("commentaire_ar", ""),
            acteur=request.user,
        )
        return Response(InscriptionSerializer(inscription).data)
