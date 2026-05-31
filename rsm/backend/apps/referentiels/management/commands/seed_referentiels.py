"""
Chargement / mise à jour idempotente des référentiels bilingues FR/AR.

    python manage.py seed_referentiels [--reset]

Principes :
- Les CLÉS (cle) sont neutres linguistiquement et correspondent EXACTEMENT
  aux valeurs des énumérations du décret (cf. ``apps.core.enums``) ;
- Les libellés FR/AR sont chargés depuis les fixtures ``fixtures/*.json`` ;
- L'exécution est idempotente : un enregistrement existant voit ses
  libellés mis à jour SANS perdre son identifiant technique (les FK
  métier pointant sur lui restent valides) ;
- Toute exécution est tracée au journal d'audit (catégorie ``admin``).

⚠️ Les libellés FR/AR des fixtures sont une AMORCE technique ; ils
doivent être relus et validés par le comité de terminologie juridique
(§ 7.3 du TDR) avant mise en production.
"""
from __future__ import annotations

import json
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.audit.services import tracer
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.core.enums import (
    CanalSaisie,
    CritereRecherche,
    MotifRejet,
    NaturesDroitInscrit,
    TypeCertificat,
)


FIXTURES = [
    ("natures_droit.json", "referentiels.LibelleNatureDroit", NaturesDroitInscrit),
    ("motifs_rejet.json", "referentiels.LibelleMotifRejet", MotifRejet),
    ("canaux_saisie.json", "referentiels.LibelleCanalSaisie", CanalSaisie),
    ("criteres_recherche.json", "referentiels.LibelleCritereRecherche", CritereRecherche),
    ("types_certificats.json", "referentiels.LibelleTypeCertificat", TypeCertificat),
]


class Command(BaseCommand):
    help = "Charge ou met à jour les référentiels bilingues FR/AR (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help=(
                "Remet à zéro le contenu des référentiels avant chargement. "
                "⚠️ Ne doit pas être utilisé en production (casse les liens)."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        base = Path(__file__).resolve().parent.parent.parent / "fixtures"
        totaux = {"crees": 0, "mis_a_jour": 0}

        # ``LibelleNatureDroit`` est désormais PARAMÉTRABLE par le MO :
        # l'invariant strict d'égalité avec l'énumération du décret est
        # remplacé par une couverture MINIMALE (les 12 clés du décret sont
        # toujours présentes, mais des entrées supplémentaires créées par
        # le greffier sont admises). De plus, ``LibelleNatureDroit`` n'est
        # pas écrasé si une entrée existe déjà (préserve les libellés
        # ajustés par le greffier).
        PARAMETRABLES = {"referentiels.LibelleNatureDroit"}

        for nom_fichier, label_modele, enum in FIXTURES:
            modele = apps.get_model(label_modele)
            if options.get("reset"):
                modele.objects.all().delete()

            chemin = base / nom_fichier
            with chemin.open(encoding="utf-8") as fh:
                donnees = json.load(fh)

            cles_fixtures = {d["fields"]["cle"] for d in donnees}
            cles_enum = {v for v, _ in enum.choices}

            if label_modele in PARAMETRABLES:
                # Couverture minimale uniquement : les clés du décret doivent
                # être au moins présentes en fixture (sinon dépendance cassée).
                manquants = cles_enum - cles_fixtures
                if manquants:
                    raise ValueError(
                        f"Référentiel paramétrable {label_modele} : clés "
                        f"décret manquantes={sorted(manquants)}"
                    )
            else:
                # Référentiels figés (motifs de rejet, canaux, critères,
                # types de certificats) — couverture exacte exigée.
                if cles_fixtures != cles_enum:
                    manquants = cles_enum - cles_fixtures
                    en_trop = cles_fixtures - cles_enum
                    raise ValueError(
                        f"Incohérence référentiel {label_modele} : "
                        f"manquants={sorted(manquants)} en_trop={sorted(en_trop)}"
                    )

            for enregistrement in donnees:
                champs = enregistrement["fields"]
                if label_modele in PARAMETRABLES:
                    # Ne PAS écraser : préserve les libellés modifiés par le greffier.
                    obj, cree = modele.objects.get_or_create(
                        cle=champs["cle"],
                        defaults={k: v for k, v in champs.items() if k != "cle"},
                    )
                else:
                    obj, cree = modele.objects.update_or_create(
                        cle=champs["cle"],
                        defaults={k: v for k, v in champs.items() if k != "cle"},
                    )
                totaux["crees" if cree else "mis_a_jour"] += 1

            self.stdout.write(self.style.SUCCESS(
                f"{label_modele} : {len(donnees)} entrées traitées."
            ))

        tracer(
            categorie=CategorieAudit.ADMIN,
            action_cle="referentiels.seed",
            resultat=ResultatAudit.SUCCES,
            objet_type="referentiels",
            details=totaux,
        )
        self.stdout.write(self.style.SUCCESS(
            f"Total : {totaux['crees']} créé(s), {totaux['mis_a_jour']} mis à jour."
        ))
