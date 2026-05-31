"""
Journal d'audit sous concurrence — § 5.2 TDR.

Écritures simultanées depuis plusieurs threads : la chaîne d'empreintes
doit rester intègre (aucun doublon d'empreinte_précédente, aucune
rupture détectable, aucun trou d'id).

Notes techniques :
- ``TransactionTestCase`` obligatoire pour que chaque thread dispose
  de sa propre connexion + transaction.
- Le service ``tracer()`` entre dans une transaction atomique qui
  verrouille implicitement la lecture ``SELECT … ORDER BY id DESC
  LIMIT 1`` lors du calcul de l'empreinte précédente ; PostgreSQL
  sérialise ces opérations au besoin via le contrôle de concurrence.
"""
from __future__ import annotations

import threading

from django.db import connections
from django.test import TransactionTestCase

from apps.audit.models import CategorieAudit, EntreeAudit, ResultatAudit
from apps.audit.services import tracer, verifier_chaine


class AuditConcurrent_Tests(TransactionTestCase):
    def _ecrire_n(self, n: int, prefixe: str, erreurs: list, barriere):
        try:
            barriere.wait(timeout=5)
            for i in range(n):
                tracer(
                    categorie=CategorieAudit.SYSTEME,
                    action_cle=f"concurrent.{prefixe}.{i}",
                    resultat=ResultatAudit.SUCCES,
                )
        except Exception as exc:  # pragma: no cover
            erreurs.append(exc)
        finally:
            connections.close_all()

    def test_chaine_integre_apres_ecritures_concurrentes(self):
        nb_threads = 8
        par_thread = 25
        barriere = threading.Barrier(nb_threads)
        erreurs: list[Exception] = []

        threads = [
            threading.Thread(
                target=self._ecrire_n,
                args=(par_thread, f"t{idx}", erreurs, barriere),
            )
            for idx in range(nb_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=20)

        self.assertEqual(erreurs, [], f"Erreurs concurrentes : {erreurs}")

        # Chaque thread a écrit son lot : au total nb_threads * par_thread.
        self.assertEqual(
            EntreeAudit.objects.filter(action_cle__startswith="concurrent.").count(),
            nb_threads * par_thread,
        )

        # La chaîne d'empreintes doit rester intègre.
        ok, premier_altere = verifier_chaine()
        self.assertTrue(ok)
        self.assertIsNone(premier_altere)

        # Aucune empreinte dupliquée.
        empreintes = list(EntreeAudit.objects.values_list("empreinte", flat=True))
        self.assertEqual(len(set(empreintes)), len(empreintes))
