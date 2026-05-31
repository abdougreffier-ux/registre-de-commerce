"""
Fabrique de certificats — STRUCTURE UNIQUEMENT.

Le service ``preparer_certificat`` produit un enregistrement ``Certificat``
en base avec ``probant=False`` et un contenu structuré prêt à être rendu
bilingue lorsque les modalités officielles seront validées.

⚠️ La génération PDF/A signée et le scellement opposable (art. 97) sont
GELÉS. Le service n'écrit pas encore de fichier PDF ; il expose ses données
canoniques (``contenu_json``) pour un rendu ultérieur.
"""
from __future__ import annotations

import warnings
from typing import Any, Mapping

from django.db import transaction

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.core.enums import TypeCertificat
from apps.certificats.models import Certificat
from apps.core.scellement import sceller


@transaction.atomic
def preparer_certificat(
    *,
    type_certificat: str,
    contenu: Mapping[str, Any],
    inscription=None,
    requete_recherche=None,
    acteur=None,
    langue: str = "fr-ar",
) -> Certificat:
    if type_certificat not in dict(TypeCertificat.choices):
        raise ValueError(f"Type de certificat inconnu : {type_certificat!r}")

    warnings.warn(
        "Certificat en mode aperçu non opposable (scellement et horodatage gelés).",
        stacklevel=2,
    )
    import json as _json
    empreinte_stub = sceller(
        _json.dumps(contenu, sort_keys=True, ensure_ascii=False).encode("utf-8")
    )

    cert = Certificat(
        type_certificat=type_certificat,
        inscription=inscription,
        requete_recherche=requete_recherche,
        langue_generation=langue,
        probant=False,
        empreinte=empreinte_stub.empreinte_hex,
        contenu_json=dict(contenu),
        cree_par=acteur,
        modifie_par=acteur,
    )
    cert.save()

    tracer(
        categorie=CategorieAudit.CERTIFICAT,
        action_cle="certificat.preparer",
        resultat=ResultatAudit.SUCCES,
        objet_type="certificat",
        objet_reference=str(cert.pk),
        details={
            "type": type_certificat, "probant": False,
            "langue": langue,
        },
        contexte=contexte_courant(),
    )
    return cert
