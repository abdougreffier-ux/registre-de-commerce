"""Sérialisations JSON des inscriptions — refonte fonctionnelle art. 85.

Le payload de dépôt accepte désormais l'ensemble des informations exigées
par l'article 85 : nature du droit, somme garantie, durée, titre
constitutif, constituants, débiteurs, créanciers, biens grevés. La
création atomique est orchestrée par ``inscriptions.services.creer_demande``.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.core.serializers import StrictInputSerializer, StrictModelSerializer
from apps.inscriptions.models import Inscription
from apps.referentiels.models import LibelleNatureDroit


class InscriptionSerializer(StrictModelSerializer):
    """Lecture d'une inscription — libellés bilingues résolus à la volée."""

    statut_libelle = serializers.CharField(source="get_statut_display", read_only=True)
    canal_saisie_libelle = serializers.CharField(
        source="get_canal_saisie_display", read_only=True,
    )
    nature_droit_libelle = serializers.SerializerMethodField()
    motif_rejet_libelle = serializers.CharField(
        source="get_motif_rejet_display", read_only=True, allow_null=True,
    )
    nature_convention_libelle = serializers.CharField(
        source="get_nature_convention_display", read_only=True, allow_null=True,
    )

    def get_nature_droit_libelle(self, obj):
        """Résolution via le référentiel paramétrable (langue FR par défaut)."""
        if not obj.nature_droit:
            return ""
        ref = LibelleNatureDroit.objects.filter(cle=obj.nature_droit).first()
        if ref is None:
            # Donnée historique sans entrée référentielle correspondante :
            # on retourne la clé technique pour préserver l'affichage.
            return obj.nature_droit
        return ref.libelle_fr

    class Meta:
        model = Inscription
        fields = [
            "reference_demande",
            "numero_ordre",
            "canal_saisie", "canal_saisie_libelle",
            "instant_arrivee", "instant_saisie_opposable",
            "statut", "statut_libelle",
            "mention_radiee", "fichier_actuel",
            "nature_droit", "nature_droit_libelle",
            "somme_garantie", "monnaie", "duree_en_jours", "date_expiration",
            "montant_en_lettres_fr", "montant_en_lettres_ar",
            "nature_convention", "nature_convention_libelle", "date_convention",
            "debiteur_est_constituant",
            "adresse_electronique_notifications",
            "motif_rejet", "motif_rejet_libelle",
            "commentaire_rejet_fr", "commentaire_rejet_ar",
            "instant_rejet",
            "cree_le", "modifie_le",
        ]
        read_only_fields = [
            "reference_demande", "numero_ordre",
            "instant_arrivee", "instant_saisie_opposable",
            "statut", "mention_radiee", "fichier_actuel",
            "motif_rejet", "commentaire_rejet_fr", "commentaire_rejet_ar",
            "instant_rejet", "cree_le", "modifie_le",
        ]


# --------------------------------------------------------------------------- #
#  Payload de dépôt — refonte fonctionnelle complète (art. 85)                #
# --------------------------------------------------------------------------- #
class PartieDeposeeSerializer(StrictInputSerializer):
    """
    Partie déposée en input : personne physique ou personne morale.

    Champs adaptés au type : PP → nom, prénom, date/lieu de naissance ;
    PM → dénomination, RC, siège. Adresse et NNI/téléphone communs.
    Régime déclaratif (art. 86) : aucun contrôle d'identité ni d'existence.
    """

    type_partie = serializers.ChoiceField(choices=["pp", "pm"])
    # Personne physique
    nom = serializers.CharField(required=False, allow_blank=True, max_length=150)
    prenom = serializers.CharField(required=False, allow_blank=True, max_length=150)
    date_naissance = serializers.DateField(required=False, allow_null=True)
    lieu_naissance = serializers.CharField(
        required=False, allow_blank=True, max_length=150,
    )
    nni = serializers.CharField(required=False, allow_blank=True, max_length=64)
    # Personne morale
    denomination_sociale = serializers.CharField(
        required=False, allow_blank=True, max_length=255,
    )
    numero_rc = serializers.CharField(
        required=False, allow_blank=True, max_length=64,
    )
    siege_social = serializers.CharField(
        required=False, allow_blank=True, max_length=255,
    )
    representant_legal = serializers.CharField(
        required=False, allow_blank=True, max_length=255,
    )
    # Commun
    adresse = serializers.CharField(required=False, allow_blank=True)
    telephone = serializers.CharField(
        required=False, allow_blank=True, max_length=32,
    )
    adresse_electronique = serializers.EmailField(
        required=False, allow_blank=True,
    )

    def validate(self, attrs):
        t = attrs.get("type_partie")
        if t == "pp":
            if not attrs.get("nom") and not attrs.get("prenom"):
                raise serializers.ValidationError(
                    "Personne physique : nom ou prénom requis."
                )
        elif t == "pm":
            if not attrs.get("denomination_sociale"):
                raise serializers.ValidationError(
                    "Personne morale : dénomination sociale requise."
                )
        return attrs


class BienDeposeSerializer(StrictInputSerializer):
    """Bien grevé déposé en input — aligné sur ``apps.biens.BienGreve``."""

    categorie_cle = serializers.CharField(max_length=64)
    description_fr = serializers.CharField(required=False, allow_blank=True)
    description_ar = serializers.CharField(required=False, allow_blank=True)
    marque = serializers.CharField(
        required=False, allow_blank=True, max_length=128,
    )
    modele = serializers.CharField(
        required=False, allow_blank=True, max_length=128,
    )
    annee = serializers.IntegerField(required=False, allow_null=True)
    numero_serie = serializers.CharField(
        required=False, allow_blank=True, max_length=128,
    )
    attributs_specifiques = serializers.DictField(
        required=False, default=dict,
    )
    observations = serializers.CharField(required=False, allow_blank=True)


class DeposerInscriptionSerializer(StrictInputSerializer):
    """Payload de dépôt d'une nouvelle demande — art. 85 intégral."""

    canal_saisie = serializers.CharField()
    nature_droit = serializers.CharField()
    somme_garantie = serializers.DecimalField(
        max_digits=18, decimal_places=2, required=False, allow_null=True,
    )
    monnaie = serializers.CharField(required=False, allow_blank=True)
    duree_en_jours = serializers.IntegerField(min_value=1)
    adresse_electronique_notifications = serializers.EmailField(
        required=False, allow_blank=True,
    )

    # Montant en lettres (calculé côté front pour le rendu temps réel,
    # re-vérifié et re-calculé côté back avant persistance).
    montant_en_lettres_fr = serializers.CharField(
        required=False, allow_blank=True, max_length=512,
    )
    montant_en_lettres_ar = serializers.CharField(
        required=False, allow_blank=True, max_length=512,
    )

    # Titre constitutif
    nature_convention = serializers.ChoiceField(
        choices=["notariee", "sous_seing_prive"],
        required=False, allow_blank=True,
    )
    date_convention = serializers.DateField(required=False, allow_null=True)

    # Parties (au moins 1 constituant, au moins 1 créancier ; débiteurs
    # facultatifs si debiteur_est_constituant=True)
    debiteur_est_constituant = serializers.BooleanField(default=False)
    constituants = PartieDeposeeSerializer(many=True, required=False, default=list)
    debiteurs = PartieDeposeeSerializer(many=True, required=False, default=list)
    creanciers = PartieDeposeeSerializer(many=True, required=False, default=list)

    # Biens grevés
    biens = BienDeposeSerializer(many=True, required=False, default=list)


class RejeterInscriptionSerializer(StrictInputSerializer):
    motif = serializers.CharField()
    commentaire_fr = serializers.CharField(required=False, allow_blank=True)
    commentaire_ar = serializers.CharField(required=False, allow_blank=True)
