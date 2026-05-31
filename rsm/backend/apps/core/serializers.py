"""
Serializers de base RSM — durcissement strict des entrées.

Principe imposé : aucune clé inconnue dans une requête d'écriture.

Rationale :
- Une clé non prévue signale soit une tentative d'injection, soit une
  incompréhension du schéma par un client ; dans les deux cas, le
  système doit refuser explicitement plutôt qu'ignorer silencieusement.
- Cette règle s'applique UNIFORMÉMENT à toute l'API (§ « cohérence
  globale » du TDR). Chaque serializer d'entrée hérite de
  ``StrictInputMixin`` ou des classes qui l'incluent.

Usage :

    class MonSerializer(StrictInputSerializer):
        champ = serializers.CharField()

    class MonModelSerializer(StrictModelSerializer):
        class Meta:
            model = MonModele
            fields = [...]
"""
from __future__ import annotations

from rest_framework import serializers


class StrictInputMixin:
    """
    Rejette toute clé inconnue en entrée.

    La validation s'exécute AVANT le ``to_internal_value`` DRF classique,
    afin de produire un message explicite avec la liste des clés invalides.

    Comportement : si ``data`` est un ``dict`` et contient une clé qui
    n'est déclarée ni comme champ ni comme champ en écriture, on lève
    une ``ValidationError`` portée par le champ fictif ``non_autorises``
    avec la liste des clés refusées et la liste des clés admises.
    """

    def to_internal_value(self, data):
        if isinstance(data, dict):
            admises = set(self.fields.keys())
            recues = set(data.keys())
            inconnues = recues - admises
            if inconnues:
                raise serializers.ValidationError({
                    "non_autorises": [
                        f"Clé(s) non autorisée(s) : {sorted(inconnues)}. "
                        f"Admises : {sorted(admises)}."
                    ],
                })
        return super().to_internal_value(data)


class StrictInputSerializer(StrictInputMixin, serializers.Serializer):
    """Serializer d'entrée sans modèle, rejetant les clés inconnues."""


class StrictModelSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer modèle, rejetant les clés inconnues."""
