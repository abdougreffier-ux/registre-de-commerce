"""
Service d'horodatage — interface stable.

⚖️ Régime juridique : les zones F1 à F14 ont été levées par la décision
d'arbitrage n° 0001/2026 du 22 avril 2026 (Chargé du suivi du projet RSM).
Voir ``docs/L11_decisions_mo/decision_0001_2026.md``.

🔧 Régime technique : la source de temps officielle désignée par le MO
(TSA RFC 3161 / NTP stratum certifié / PTP / horloge HSM) doit être
communiquée pour permettre l'implémentation de l'adaptateur
correspondant, sans invention. Tant qu'elle n'est pas transmise, ce
service fonctionne en mode ``local_stub`` — ``timezone.now()`` sans
horodatage opposable côté TSA.

Toute bascule se fait par configuration (``RSM_TIMESOURCE_MODE``), sans
modification du code métier.
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultatHorodatage:
    """
    Structure retournée par le service d'horodatage.

    ``instant`` : datetime à la seconde près (cf. art. 78 alinéa 4).
    ``source`` : identifiant de la source de temps utilisée.
    ``opposable`` : ``True`` uniquement si l'adaptateur TSA désigné par
    le MO est effectivement configuré. ``False`` tant que les paramètres
    techniques (décision n° 0001/2026) n'ont pas été transmis.
    """

    instant: datetime
    source: str
    opposable: bool


def maintenant_opposable() -> ResultatHorodatage:
    """Retourne l'horodatage courant et son statut d'opposabilité."""
    mode = getattr(settings, "RSM_TIMESOURCE_MODE", "local_stub")

    if mode == "local_stub":
        warnings.warn(
            "Horodatage en mode local_stub (RSM_TIMESOURCE_MODE). Les "
            "paramètres de la source de temps officielle désignée par le "
            "MO (décision n° 0001/2026) ne sont pas encore configurés : "
            "l'horodatage produit est horloge locale, non contre-signé "
            "par la TSA (art. 78).",
            stacklevel=2,
        )
        return ResultatHorodatage(
            instant=timezone.now(),
            source="local_stub",
            opposable=False,
        )

    # Les autres modes (ntp_stratum_X, ptp, hsm_trusted_clock) seront
    # implémentés par des adaptateurs dédiés dès communication des
    # paramètres techniques par le MO (décision n° 0001/2026, article 2
    # § 5). Aucune implémentation par défaut n'est inventée.
    raise NotImplementedError(
        f"Source de temps '{mode}' non implémentée : paramètres "
        "techniques à communiquer par le MO (TDR § 5.1, art. 78)."
    )


def format_numero_ordre(instant: datetime, numero_sequence: int) -> str:
    """
    Forme le numéro de série prescrit par l'article 78 alinéa 4.

    Format : ``<numero_sequence>-AAAAMMJJHHMMSS``.

    Exemple : ``000123-20261021143512``.

    ⚠️ Ne préjuge pas du caractère opposable : voir ``maintenant_opposable``.
    """
    if numero_sequence <= 0:
        raise ValueError("Le numéro d'ordre doit être strictement positif.")
    partie_temporelle = instant.strftime("%Y%m%d%H%M%S")
    return f"{numero_sequence:06d}-{partie_temporelle}"
