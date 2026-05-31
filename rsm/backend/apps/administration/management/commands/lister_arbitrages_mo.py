"""
Génère le registre des tests désactivés en attente d'arbitrage MO.

    python manage.py lister_arbitrages_mo

Charge l'ensemble des modules de tests pour peupler le registre, puis
écrit ``tests/arbitrages_mo_en_attente.txt``. Ce fichier est un livrable
de suivi MO ; il doit être commité et annexé à L11.
"""
from __future__ import annotations

import importlib
import pkgutil

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Produit le registre des tests en attente d'arbitrage MO."

    def handle(self, *args, **options):
        # Charger tous les modules de tests pour déclencher les décorateurs.
        import tests  # noqa: F401

        for finder, name, is_pkg in pkgutil.walk_packages(
            tests.__path__, prefix="tests.",
        ):
            importlib.import_module(name)

        from tests.marqueurs import REGISTRE_EN_MEMOIRE, ecrire_registre

        ecrire_registre()
        self.stdout.write(self.style.SUCCESS(
            f"Registre écrit : {len(REGISTRE_EN_MEMOIRE)} arbitrage(s) en attente."
        ))
        for cle, m in REGISTRE_EN_MEMOIRE:
            self.stdout.write(f"  [{m.reference}] {m.titre} → {cle}")
