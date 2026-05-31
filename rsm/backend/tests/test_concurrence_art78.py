"""
Concurrence d'attribution du numéro d'ordre — article 78.

Règles :
- « les demandes sont enregistrées dans l'ordre de leur date d'arrivée »
  (art. 78 alinéa 2) ;
- le numéro d'ordre est unique (critère § 10.1 du TDR) ;
- aucun numéro n'est réutilisé.

Le service ``attribuer_numero_ordre`` pose un ``SELECT … FOR UPDATE``
sur la ligne unique de ``SequenceNumeroOrdre`` afin de sérialiser les
attributions concurrentes. Ce test vérifie le comportement sous
concurrence réelle.

⚠️ ``TransactionTestCase`` est utilisé au lieu de ``TestCase`` : avec
``TestCase``, toutes les actions sont isolées dans une transaction unique
et ne peuvent être partagées entre threads. Avec ``TransactionTestCase``,
chaque thread ouvre sa propre connexion et sa propre transaction — ce
qui est la seule façon de tester des verrous pessimistes PostgreSQL.
"""
from __future__ import annotations

import threading

from django.db import connection, connections, transaction
from django.test import TransactionTestCase

from apps.inscriptions.models import SequenceNumeroOrdre
from apps.inscriptions.services import attribuer_numero_ordre


class AttributionNumeroOrdreConcurrente_Tests(TransactionTestCase):
    """
    N threads tentent simultanément d'obtenir un numéro d'ordre.
    Les invariants à vérifier :
    - N numéros distincts rendus (pas de doublon) ;
    - chaque numéro est un entier strictement croissant ;
    - la séquence finale en base = le plus grand numéro + 1.
    """

    def setUp(self):
        # On démarre avec un compteur à 1 (déjà garanti par la migration).
        SequenceNumeroOrdre.objects.get_or_create(pk=1)

    def _obtenir_numero(self, resultats: list, erreurs: list, barriere):
        try:
            barriere.wait(timeout=5)
            with transaction.atomic():
                numero, _horodatage = attribuer_numero_ordre()
            resultats.append(numero)
        except Exception as exc:  # pragma: no cover - visibilité test
            erreurs.append(exc)
        finally:
            # Ferme la connexion propre au thread (pool Django).
            connections.close_all()

    def test_attributions_concurrentes_toutes_uniques(self):
        n_threads = 20
        barriere = threading.Barrier(n_threads)
        resultats: list[str] = []
        erreurs: list[Exception] = []

        threads = [
            threading.Thread(
                target=self._obtenir_numero,
                args=(resultats, erreurs, barriere),
            )
            for _ in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(
            erreurs, [],
            f"Des erreurs sont survenues lors de l'attribution : {erreurs}",
        )
        self.assertEqual(len(resultats), n_threads)
        # Extraction des parties séquentielles du format NNNNNN-AAAAMMJJHHMMSS.
        parties_seq = [int(r.split("-")[0]) for r in resultats]
        # 1. Aucun doublon.
        self.assertEqual(
            len(set(parties_seq)), n_threads,
            f"Doublons dans l'attribution : {parties_seq}",
        )
        # 2. Ensemble contigu : {1, 2, ..., N} sans trou.
        self.assertEqual(
            sorted(parties_seq), list(range(1, n_threads + 1)),
            "La séquence d'attribution doit être contiguë (art. 78).",
        )
        # 3. La séquence en base reflète bien le prochain numéro attendu.
        seq = SequenceNumeroOrdre.objects.get(pk=1)
        self.assertEqual(seq.prochaine_valeur, n_threads + 1)

    def test_chronologie_coherente_avec_le_numero(self):
        """
        L'horodatage à la seconde embarqué dans le format
        ``NNNNNN-AAAAMMJJHHMMSS`` doit croître (ou stagner) avec le
        numéro séquentiel — jamais l'inverse.
        """
        n = 10
        numeros: list[str] = []
        for _ in range(n):
            with transaction.atomic():
                numero, _ = attribuer_numero_ordre()
            numeros.append(numero)

        sequences = [int(x.split("-")[0]) for x in numeros]
        horodatages = [x.split("-")[1] for x in numeros]

        self.assertEqual(sequences, sorted(sequences))
        # Les horodatages sont monotones non décroissants (à la seconde près).
        self.assertEqual(horodatages, sorted(horodatages))
