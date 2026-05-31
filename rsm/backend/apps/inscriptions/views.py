"""Vues API des inscriptions."""
from __future__ import annotations

import hashlib
from decimal import Decimal

from rest_framework import generics, parsers, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.core.exceptions import RejetForme
from apps.inscriptions.models import Inscription, PieceJointe
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


# Contraintes pièces jointes
PJ_TAILLE_MAX = 10 * 1024 * 1024  # 10 Mo
PJ_TYPES_MIME_AUTORISES = {"application/pdf"}
PJ_EXTENSIONS_AUTORISEES = {".pdf"}


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
                    type_surete=d.get("type_surete", "depot_surete"),
                    donnees_specifiques=d.get("donnees_specifiques") or {},
                    debiteur_est_constituant=d.get(
                        "debiteur_est_constituant", False
                    ),
                    constituants=tuple(d.get("constituants") or []),
                    debiteurs=tuple(d.get("debiteurs") or []),
                    creanciers=tuple(d.get("creanciers") or []),
                    agents_surete=tuple(d.get("agents_surete") or []),
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


# --------------------------------------------------------------------------- #
#  Pièces jointes — upload PDF (multipart)                                    #
# --------------------------------------------------------------------------- #
class PieceJointeUploadView(APIView):
    """
    Upload d'une pièce jointe PDF associée à une demande d'inscription.

    Contraintes (refonte MO 2026-05-30) :
      - format : PDF uniquement (MIME application/pdf, extension .pdf) ;
      - taille : 10 Mo maximum par fichier ;
      - nombre : plusieurs uploads séquentiels autorisés ;
      - empreinte SHA-256 calculée et conservée pour intégrité ;
      - traçage audit obligatoire.

    Régime de stockage : ``MEDIA_ROOT/pieces_jointes/AAAA/MM/`` (cf.
    modèle ``PieceJointe.fichier``).
    """

    parser_classes = [parsers.MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, reference_demande):
        try:
            inscription = Inscription.objects.get(reference_demande=reference_demande)
        except Inscription.DoesNotExist:
            return Response(
                {"detail": "Demande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Habilitation : seul le déposant de la demande (ou un agent
        # interne autorisé) peut ajouter des pièces.
        if inscription.cree_par_id and inscription.cree_par_id != request.user.pk:
            roles = set(request.user.roles_actifs())
            from apps.utilisateurs.models import RoleApplicatif
            if not (roles & {RoleApplicatif.AGENT_SAISIE,
                             RoleApplicatif.AUTORITE_VALIDATION}):
                raise PermissionDenied(
                    "Vous ne pouvez pas ajouter de pièce à cette demande."
                )

        fichier = request.FILES.get("fichier")
        if fichier is None:
            return Response(
                {"detail": "Champ 'fichier' manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validation type MIME + extension
        nom = (fichier.name or "").lower()
        extension_ok = any(nom.endswith(ext) for ext in PJ_EXTENSIONS_AUTORISEES)
        mime_ok = (fichier.content_type or "").lower() in PJ_TYPES_MIME_AUTORISES
        if not (extension_ok and mime_ok):
            return Response(
                {"detail": "Format non autorisé. Seul PDF est accepté."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validation taille
        if fichier.size > PJ_TAILLE_MAX:
            return Response(
                {
                    "detail": (
                        f"Fichier trop volumineux : {fichier.size} octets. "
                        f"Taille maximale autorisée : {PJ_TAILLE_MAX} octets."
                    ),
                },
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # Calcul de l'empreinte SHA-256 (intégrité, pas un sceau probant)
        sha = hashlib.sha256()
        for chunk in fichier.chunks():
            sha.update(chunk)
        empreinte = sha.hexdigest()
        # Repositionner le curseur de lecture pour la persistance Django
        fichier.seek(0)

        pj = PieceJointe.objects.create(
            inscription=inscription,
            nom_original=fichier.name,
            fichier=fichier,
            type_mime=fichier.content_type or "application/pdf",
            taille_octets=fichier.size,
            sceau_empreinte=empreinte,
            cree_par=request.user,
            modifie_par=request.user,
        )

        tracer(
            categorie=CategorieAudit.DEMANDE,
            action_cle="piece_jointe.ajouter",
            resultat=ResultatAudit.SUCCES,
            objet_type="piece_jointe",
            objet_reference=str(pj.pk),
            details={
                "inscription_ref": str(inscription.reference_demande),
                "nom_original": pj.nom_original,
                "taille_octets": pj.taille_octets,
                "empreinte_sha256": empreinte,
            },
            contexte=contexte_courant(),
        )

        return Response(
            {
                "id": pj.pk,
                "nom_original": pj.nom_original,
                "taille_octets": pj.taille_octets,
                "type_mime": pj.type_mime,
                "empreinte_sha256": empreinte,
                "cree_le": pj.cree_le.isoformat() if pj.cree_le else None,
            },
            status=status.HTTP_201_CREATED,
        )
