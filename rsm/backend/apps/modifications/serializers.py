from rest_framework import serializers

from apps.core.serializers import StrictModelSerializer
from apps.modifications.models import DemandeModification


class DemandeModificationSerializer(StrictModelSerializer):
    class Meta:
        model = DemandeModification
        fields = [
            "id", "inscription", "objet_modification_fr", "objet_modification_ar",
            "diff_propose", "statut",
            "motif_refus_code", "motif_refus",
            "accord_createur_confirme", "accord_constituant_confirme",
            "applique_le", "cree_le", "modifie_le",
        ]
        read_only_fields = [
            "statut", "motif_refus_code", "motif_refus",
            "applique_le", "cree_le", "modifie_le",
        ]
