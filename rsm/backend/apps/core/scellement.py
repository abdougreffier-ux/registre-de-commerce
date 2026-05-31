"""
Service de scellement cryptographique — interface stable.

⚖️ Régime juridique : les zones F1 à F14 ont été levées par la décision
d'arbitrage n° 0001/2026 du 22 avril 2026. Voir
``docs/L11_decisions_mo/decision_0001_2026.md``.

🔧 Régime technique : les paramètres du scellement désignés par le MO
(algorithmes, politique de rotation, gestion des clés, présence HSM)
doivent être communiqués pour implémenter l'adaptateur correspondant,
sans invention. Tant qu'ils ne sont pas transmis, le service produit
une empreinte SHA-256 non signée, utile à la détection d'altération
mais non constitutive d'une signature opposable.

Toute intégration métier passe par ``sceller()`` / ``verifier()`` sans
connaître le détail cryptographique.
"""
from __future__ import annotations

import hashlib
import warnings
from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class Sceau:
    empreinte_hex: str
    algorithme: str
    opposable: bool

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.algorithme}:{self.empreinte_hex}"


def sceller(contenu: bytes) -> Sceau:
    """
    Calcule un sceau sur un contenu binaire canonique.

    En mode ``disabled``, l'algorithme utilisé est SHA-256 (empreinte non
    signée). Il permet de détecter toute altération ultérieure mais ne
    constitue pas une signature juridiquement opposable. Les modes
    actifs nécessitent la réception des paramètres techniques désignés
    par le MO (décision n° 0001/2026, article 2 § 6).
    """
    mode = getattr(settings, "RSM_SEAL_MODE", "disabled")
    if mode != "disabled":
        raise NotImplementedError(
            f"Mode de scellement '{mode}' non implémenté : paramètres "
            "techniques à communiquer par le MO (TDR § 6.3)."
        )
    warnings.warn(
        "Scellement en mode disabled (RSM_SEAL_MODE). Les paramètres "
        "cryptographiques désignés par le MO (décision n° 0001/2026) "
        "ne sont pas encore configurés : les sceaux produits sont des "
        "empreintes SHA-256 non signées.",
        stacklevel=2,
    )
    empreinte = hashlib.sha256(contenu).hexdigest()
    return Sceau(empreinte_hex=empreinte, algorithme="sha256-stub", opposable=False)


def verifier(contenu: bytes, sceau: Sceau) -> bool:
    """Vérifie qu'un contenu produit bien le sceau fourni."""
    return hashlib.sha256(contenu).hexdigest() == sceau.empreinte_hex
