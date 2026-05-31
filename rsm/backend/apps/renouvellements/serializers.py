from apps.core.serializers import StrictModelSerializer
from apps.renouvellements.models import DemandeRenouvellement


class DemandeRenouvellementSerializer(StrictModelSerializer):
    class Meta:
        model = DemandeRenouvellement
        fields = [
            "id", "inscription", "statut", "motif_refus",
            "ancienne_date_expiration", "nouvelle_date_expiration",
            "applique_le", "cree_le", "modifie_le",
        ]
        read_only_fields = [
            "statut", "motif_refus",
            "ancienne_date_expiration", "nouvelle_date_expiration",
            "applique_le", "cree_le", "modifie_le",
        ]
