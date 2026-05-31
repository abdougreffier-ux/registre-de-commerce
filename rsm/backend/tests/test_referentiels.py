"""
Tests des référentiels bilingues — conformité et bilinguisme strict.

Règles TDR § 7 :
- mêmes libellés présents côté FR et côté AR ;
- clés neutres linguistiquement correspondant exactement aux
  énumérations limitatives du décret.
"""
from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase

from apps.core.enums import (
    CanalSaisie,
    CritereRecherche,
    MotifRejet,
    NaturesDroitInscrit,
    TypeCertificat,
)
from apps.referentiels.models import (
    LIBELLES_ATTENDUS,
    LibelleCanalSaisie,
    LibelleCritereRecherche,
    LibelleMotifRejet,
    LibelleNatureDroit,
    LibelleTypeCertificat,
)


class SeedReferentielsTests(TestCase):
    """La commande charge les fixtures sans perte ni doublon."""

    def test_seed_est_idempotent(self):
        call_command("seed_referentiels")
        premier_total = sum(m.objects.count() for m in LIBELLES_ATTENDUS)
        call_command("seed_referentiels")
        second_total = sum(m.objects.count() for m in LIBELLES_ATTENDUS)
        self.assertEqual(premier_total, second_total)

    def test_couverture_exacte_des_enums(self):
        """
        Pour les référentiels figés (motifs de rejet, canaux, critères,
        types de certificats), la couverture doit être strictement
        exacte. Pour ``LibelleNatureDroit``, désormais paramétrable
        (directive MO 2026-05-30), la couverture exigée est une
        couverture MINIMALE : les valeurs du décret sont présentes,
        mais des entrées supplémentaires (créées par le greffier ou
        par data migration) sont admises.
        """
        from apps.referentiels.models import LibelleNatureDroit
        call_command("seed_referentiels")
        for modele, valeurs_attendues in LIBELLES_ATTENDUS.items():
            cles = set(modele.objects.values_list("cle", flat=True))
            if modele is LibelleNatureDroit:
                # Couverture minimale : enum ⊆ table.
                manquants = valeurs_attendues - cles
                self.assertFalse(
                    manquants,
                    f"Référentiel {modele.__name__} : "
                    f"clés du décret manquantes={sorted(manquants)}",
                )
            else:
                self.assertEqual(
                    cles, valeurs_attendues,
                    f"Référentiel {modele.__name__} non couvrant.",
                )

    def test_libelles_fr_et_ar_toujours_renseignes(self):
        call_command("seed_referentiels")
        for modele in LIBELLES_ATTENDUS:
            for obj in modele.objects.all():
                self.assertTrue(
                    obj.libelle_fr.strip(),
                    f"Libellé FR manquant sur {modele.__name__}/{obj.cle}",
                )
                self.assertTrue(
                    obj.libelle_ar.strip(),
                    f"Libellé AR manquant sur {modele.__name__}/{obj.cle}",
                )


class BilinguismePairesTests(TestCase):
    """Chaque libellé doit rester présentable en FR ou en AR selon la langue."""

    def setUp(self):
        call_command("seed_referentiels")

    def test_libelle_par_langue(self):
        nature = LibelleNatureDroit.objects.get(
            cle=NaturesDroitInscrit.NANTISSEMENT_STOCKS
        )
        self.assertIn("stocks", nature.libelle("fr").lower())
        # La version AR est non vide et différente de FR.
        self.assertTrue(nature.libelle("ar"))
        self.assertNotEqual(nature.libelle("fr"), nature.libelle("ar"))
