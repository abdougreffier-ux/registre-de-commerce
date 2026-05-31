# Procédure de déploiement RCCM — Règles de gouvernance

## Règle fondamentale — MIGRATIONS_OK obligatoire

> **Aucune recette, aucune démonstration, aucune mise en production ne peut être
> autorisée tant que le système ne signale pas MIGRATIONS_OK.**

Cette règle est non négociable. Elle découle du fait qu'un schéma de base de données
désynchronisé avec les modèles Django peut provoquer :

- Des données invisibles (HTTP 500 masqué en « Aucune donnée »)
- Des erreurs silencieuses de lecture ou d'écriture
- Des documents PDF incorrects ou partiels
- Des risques juridiques pour les immatriculations RCCM

---

## Procédure obligatoire avant toute session de recette ou démonstration

### Étape 1 — Vérification de l'état du schéma

```bash
python manage.py check_deploy
```

**Résultat attendu :**
```
✅  RCCM — Système prêt pour le déploiement.
```

Si des migrations sont en attente, le système affiche :
```
⛔  RCCM — Des problèmes bloquants ont été détectés.
```
→ **La session doit être reportée jusqu'à correction.**

### Étape 2 — Application des migrations si nécessaire

```bash
python manage.py check_deploy --apply
```

Ou directement :
```bash
python manage.py migrate
python manage.py check_deploy   # vérification post-migration
```

### Étape 3 — Démarrage du serveur (uniquement après MIGRATIONS_OK)

```bash
python manage.py runserver
```

---

## Garanties techniques en place

| Mécanisme | Déclencheur | Effet |
|-----------|-------------|-------|
| `CoreConfig.ready()` | Démarrage Django | Log CRITICAL + flag `_MIGRATIONS_OK=False` |
| System Check `rccm.E001` | `runserver` / `check` | Bloque le démarrage |
| `MigrationGuardMiddleware` | Requête `GET /api/*` | HTTP 503 JSON bilingue |
| Intercepteur Axios 503 | Réponse frontend | Bandeau rouge bloquant non dismissible |
| `check_deploy` | Appel manuel / script CI | Rapport pass/fail avec exit code |

---

## Règles de création de migrations

### Ce qui est autorisé

| Opération | Sûreté |
|-----------|--------|
| `AddField(blank=True)` | ✅ Sûre — colonne optionnelle, aucune donnée existante touchée |
| `AddField(default=valeur)` | ✅ Sûre — valeur par défaut appliquée aux lignes existantes |
| `CreateModel` | ✅ Sûre — nouvelle table, aucune table existante touchée |
| `AddIndex` | ✅ Sûre — performance uniquement |

### Ce qui requiert une revue explicite

| Opération | Risque | Précaution |
|-----------|--------|------------|
| `RemoveField` | Perte de données | Vérifier que la colonne est bien vide / inutilisée |
| `AlterField` (type) | Conversion de données | Tester sur dump de données réelles |
| `RenameField` | Rupture de compatibilité | Vérifier tous les accès directs au champ |
| `RunPython` | Arbitraire | Relecture obligatoire du code |
| `DeleteModel` | Perte de table | Vérifier FK et données |

### Ce qui est interdit sans backup préalable

- `RunPython` modifiant des données sans possibilité de rollback
- `AlterField` réduisant la taille d'un `CharField` sur des données existantes
- Toute migration combinant `RemoveField` + `CreateModel` sur les mêmes données

---

## Gestion de la civilité pour les personnes physiques existantes

Voir section dédiée → [`CIVILITE_EXISTANTS.md`](./CIVILITE_EXISTANTS.md)

---

## Contacts en cas de blocage

En cas de blocage `MIGRATIONS_PENDING` sur un environnement de production :

1. **Ne pas redémarrer** le serveur en boucle — le blocage est intentionnel
2. Contacter l'administrateur système pour appliquer `python manage.py migrate`
3. Vérifier l'intégrité des données après correction avec `check_deploy`
4. Consigner l'incident dans le journal d'audit RCCM
