"""Vues de consultation des rejets (art. 80) — pour le greffe et l'auditeur."""
from __future__ import annotations

from rest_framework import generics

from apps.inscriptions.models import Inscription
from apps.inscriptions.serializers import InscriptionSerializer
from apps.workflow.statuts import StatutInscription


class ListeRejets(generics.ListAPIView):
    """Liste des demandes rejetées — filtrable par motif d'article 80."""

    serializer_class = InscriptionSerializer

    def get_queryset(self):
        qs = Inscription.objects.filter(statut=StatutInscription.REJETEE).order_by(
            "-instant_rejet"
        )
        motif = self.request.query_params.get("motif")
        if motif:
            qs = qs.filter(motif_rejet=motif)
        return qs
