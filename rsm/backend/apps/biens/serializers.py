"""Sérialiseurs des catégories de biens."""
from rest_framework import serializers

from apps.biens.models import CategorieBien


class CategorieBienLectureSerializer(serializers.ModelSerializer):
    """Sortie publique : pas d'utilisateur cree_par/modifie_par exposé."""

    est_utilisee = serializers.BooleanField(read_only=True)

    class Meta:
        model = CategorieBien
        fields = [
            "id", "cle", "version",
            "libelle_fr", "libelle_ar",
            "description_fr", "description_ar",
            "schema_champs",
            "affichage_observations",
            "actif", "est_utilisee",
            "cree_le", "modifie_le",
        ]
        read_only_fields = fields


class PublierCategorieSerializer(serializers.Serializer):
    """Payload pour publier une nouvelle version d'une catégorie."""

    cle = serializers.RegexField(r"^[a-z0-9_]+$", max_length=64)
    libelle_fr = serializers.CharField(max_length=255)
    libelle_ar = serializers.CharField(max_length=255)
    description_fr = serializers.CharField(allow_blank=True, required=False, default="")
    description_ar = serializers.CharField(allow_blank=True, required=False, default="")
    schema_champs = serializers.ListField(child=serializers.DictField())
    affichage_observations = serializers.BooleanField(default=True)
