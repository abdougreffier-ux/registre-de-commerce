"""
Marqueur de tests dépendant d'un arbitrage institutionnel.

Principe :
- Un test portant sur un comportement non explicitement tranché par le
  décret 2021-033 ou par le TDR ne doit JAMAIS passer en « PASS »
  silencieusement : cela reviendrait à figer un comportement non
  stabilisé.
- Le décorateur ``arbitrage_mo`` positionne le test à l'état ``SKIP``
  avec un message explicite, référence L11, et enregistre le test dans
  un registre en vue d'un rapport MO.

Usage :

    @arbitrage_mo(
        reference="L11/A2",
        titre="Signature électronique des parties (art. 88)",
        comportement_attendu=(
            "Vérifie que la signature électronique est cryptographiquement "
            "valide et rejette les contenus altérés."
        ),
    )
    def test_quelque_chose(self):
        ...

Règle cardinale : un test marqué ``arbitrage_mo`` n'est PAS une règle
juridique stabilisée. Il ne peut servir de référence pour une décision
métier tant que la zone n'a pas été tranchée par le maître d'ouvrage.
"""
from __future__ import annotations

import json
import os
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


RACINE_TESTS = Path(__file__).resolve().parent
FICHIER_REGISTRE = RACINE_TESTS / "arbitrages_mo_en_attente.txt"


@dataclass(frozen=True)
class MarqueurArbitrage:
    reference: str
    titre: str
    comportement_attendu: str


#: Registre en mémoire — accumulé au chargement des modules de tests.
REGISTRE_EN_MEMOIRE: list[tuple[str, MarqueurArbitrage]] = []


def arbitrage_mo(
    *, reference: str, titre: str, comportement_attendu: str,
) -> Callable:
    """
    Désactive le test et l'enregistre au registre des arbitrages en attente.

    - ``reference`` : identifiant stable dans le livrable L11 (ex.
      ``"L11/A2"``).
    - ``titre`` : formulation synthétique du sujet.
    - ``comportement_attendu`` : description du comportement que le
      test mettra en œuvre une fois l'arbitrage rendu.
    """
    marqueur = MarqueurArbitrage(
        reference=reference, titre=titre,
        comportement_attendu=comportement_attendu,
    )
    raison = (
        f"[ARBITRAGE MO EN ATTENTE — {reference}] {titre}. "
        f"Comportement attendu : {comportement_attendu} "
        f"Ce test n'est pas une règle stabilisée."
    )

    def _wrap(fonction_ou_classe):
        cle = f"{fonction_ou_classe.__module__}.{fonction_ou_classe.__qualname__}"
        REGISTRE_EN_MEMOIRE.append((cle, marqueur))
        return unittest.skip(raison)(fonction_ou_classe)

    return _wrap


def ecrire_registre() -> None:
    """
    Écrit le registre des tests marqués dans
    ``tests/arbitrages_mo_en_attente.txt``. Appelé par une commande
    ``python manage.py lister_arbitrages_mo``.
    """
    if not REGISTRE_EN_MEMOIRE:
        if FICHIER_REGISTRE.exists():
            FICHIER_REGISTRE.unlink()
        return

    lignes = [
        "# Registre des tests désactivés en attente d'arbitrage MO",
        "# Généré automatiquement — ne pas éditer à la main.",
        "#",
        "# Chaque entrée représente un comportement non tranché par le",
        "# décret 2021-033 ou par le TDR. Le test correspondant est",
        "# désactivé jusqu'à décision du maître d'ouvrage.",
        "",
    ]
    for cle, m in REGISTRE_EN_MEMOIRE:
        lignes.append(f"- [{m.reference}] {m.titre}")
        lignes.append(f"  Test        : {cle}")
        lignes.append(f"  Comportement: {m.comportement_attendu}")
        lignes.append("")
    FICHIER_REGISTRE.write_text("\n".join(lignes), encoding="utf-8")


def registre_json() -> str:
    """Retourne le registre sous forme JSON (usage diagnostic)."""
    return json.dumps(
        [
            {
                "test": cle,
                "reference": m.reference,
                "titre": m.titre,
                "comportement_attendu": m.comportement_attendu,
            }
            for cle, m in REGISTRE_EN_MEMOIRE
        ],
        ensure_ascii=False, indent=2, sort_keys=True,
    )
