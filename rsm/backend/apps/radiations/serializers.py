from apps.core.serializers import StrictModelSerializer
from apps.radiations.models import DemandeRadiation


class DemandeRadiationSerializer(StrictModelSerializer):
    class Meta:
        model = DemandeRadiation
        fields = [
            "id", "inscription", "fondement", "statut", "motif_refus",
            "nom_constituant", "prenom_constituant", "denomination_constituant",
            "adresse_constituant", "numero_rc_constituant",
            "applique_le", "cree_le", "modifie_le",
        ]
        read_only_fields = ["statut", "motif_refus", "applique_le", "cree_le", "modifie_le"]
