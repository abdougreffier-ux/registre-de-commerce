from rest_framework import generics

from apps.certificats.models import Certificat
from apps.core.serializers import StrictModelSerializer


class CertificatSerializer(StrictModelSerializer):
    class Meta:
        model = Certificat
        fields = [
            "id", "type_certificat", "inscription", "requete_recherche",
            "langue_generation", "probant", "empreinte", "contenu_json",
            "fichier_pdf", "cree_le", "modifie_le",
        ]


class ListeCertificats(generics.ListAPIView):
    queryset = Certificat.objects.order_by("-cree_le")
    serializer_class = CertificatSerializer


class DetailCertificat(generics.RetrieveAPIView):
    queryset = Certificat.objects.all()
    serializer_class = CertificatSerializer
