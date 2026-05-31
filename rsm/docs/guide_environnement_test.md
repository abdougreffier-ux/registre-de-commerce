# Guide d'environnement de TEST fonctionnel — RSM

**Objet** : accès et manipulation du système RSM en environnement de
test pour démonstration fonctionnelle.
**Portée** : environnement **local** ou **staging**, non opposable.
**État** : toutes les zones gelées (horodatage, scellement, signature,
MFA, certificats probants) sont en mode STUB — aucune donnée produite
n'a de valeur juridique.

---

## 1. Environnement de test

### 1.1 Type d'environnement

- **Local** (développement sur poste du testeur) : recommandé pour
  itérations rapides et isolation.
- **Staging** (serveur de test dédié) : possible, en appliquant les
  mêmes procédures, avec un nom d'hôte et un certificat TLS interne.

Les deux utilisent la même stack avec la même configuration `.env.test`.

### 1.2 Prérequis techniques

**Option A — Docker (recommandée)** :
- Docker ≥ 24
- Docker Compose v2 (plugin intégré)
- 4 Go de RAM disponibles
- Ports 8000 et 5433 libres sur l'hôte

**Option B — Installation native** :
- Python 3.11+
- PostgreSQL 14+ (pas de SQLite en test — les triggers append-only
  exigent PostgreSQL)
- Git
- (optionnel) Node 18+ si vous souhaitez lancer le squelette frontend
- `pip`, `virtualenv`, `psql`

### 1.3 Instructions pas-à-pas

#### Option A — Docker Compose (le plus simple)

```bash
# 1. Se placer à la racine du projet rsm/
cd rsm/

# 2. Démarrer les services (PostgreSQL + backend)
docker compose -f docker-compose.test.yml up --build

# À l'issue, le backend applique automatiquement :
#   - les migrations Django
#   - le chargement des référentiels bilingues FR/AR
#   - le peuplement des comptes et données de test
#   - le démarrage du serveur Django sur le port 8000
```

Accès :

- Backend API : http://localhost:8000/api/v1/
- Admin Django : http://localhost:8000/fr/administration/ (ou `/ar/`)
- Sonde santé : http://localhost:8000/fr/sante/

Pour arrêter :

```bash
docker compose -f docker-compose.test.yml down
# Pour tout purger (données BD incluses) :
docker compose -f docker-compose.test.yml down -v
```

#### Option B — Installation native

```bash
# 1. Cloner / se placer dans rsm/backend
cd rsm/backend/

# 2. Créer un virtualenv Python 3.11
python -m venv venv
source venv/bin/activate         # Linux / macOS
venv\Scripts\activate            # Windows PowerShell

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Préparer l'environnement
cp .env.test .env

# 5. Créer la base PostgreSQL (nécessite PostgreSQL installé)
createdb rsm_test
createuser rsm_test --pwprompt        # utiliser "rsm_test_password"
psql -c "ALTER USER rsm_test WITH SUPERUSER;" postgres   # pour les triggers

# 6. Migrations + seed
python manage.py migrate
python manage.py seed_referentiels
python manage.py seed_demo_test

# 7. Lancer le serveur
python manage.py runserver 8000
```

#### (Optionnel) — Frontend React squelette

Le frontend livré est un **squelette minimal** (accueil, liste
d'inscriptions, audit, formulaire de recherche). Il **ne contient
pas** les formulaires de dépôt, modification, radiation (Option B
GELÉE). Lancement :

```bash
cd rsm/frontend/
npm install
npm start
```

Accès : http://localhost:3000/ — proxy vers le backend `http://localhost:8000/api/v1`.

---

## 2. Accès au système

### 2.1 URL d'accès

| Surface | URL |
|---------|-----|
| API REST racine | `http://localhost:8000/api/v1/` |
| Admin Django (FR) | `http://localhost:8000/fr/administration/` |
| Admin Django (AR) | `http://localhost:8000/ar/administration/` |
| Sonde santé (FR) | `http://localhost:8000/fr/sante/` |
| Sonde santé (AR) | `http://localhost:8000/ar/sante/` |
| Accueil bilingue | `http://localhost:8000/fr/` ou `/ar/` |
| Frontend React (squelette) | `http://localhost:3000/` |

### 2.2 Comptes de test

⚠️ **Comptes et mots de passe de TEST** — fixes pour démo, **à ne
jamais utiliser en production**. Créés automatiquement par
`python manage.py seed_demo_test`.

| Utilisateur | Mot de passe | Rôle applicatif | Usage principal |
|-------------|:-:|-----------------|-----------------|
| `admin_technique` | `test-rsm-admin-2026` | `admin_technique` + superuser Django | Admin Django, diagnostics |
| `admin_fonctionnel` | `test-rsm-admin-2026` | `admin_fonctionnel` | Gestion utilisateurs, référentiels, libellés |
| `greffier` | `test-rsm-greffier-2026` | `autorite_validation` | Valider / rejeter / appliquer M/R/Rad |
| `agent_saisie` | `test-rsm-agent-2026` | `agent_saisie` | Déposer des demandes au guichet |
| `declarant_externe` | `test-rsm-declarant-2026` | `declarant_externe` | Déposer via portail (simulation) |
| `auditeur` | `test-rsm-auditeur-2026` | `auditeur` + is_staff | Consultation du journal d'audit |
| `prod_stats` | `test-rsm-stats-2026` | `prod_stats` | Production de statistiques (art. 82) |

### 2.3 Usager public

Pour la recherche publique (art. 94), aucune authentification n'est
requise. Exemple :

```bash
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -d '{"nom_constituant":"Ould Ahmed","numero_rc":"RC/NKT/2024/0001"}'
```

### 2.4 Création de comptes supplémentaires

En admin Django (via compte `admin_technique`), sous « Utilisateurs »
et « Affectations de rôle ». Cf. L2.4 pour la matrice rôles × opérations.

---

## 3. Données de test

### 3.1 Données chargées par `seed_demo_test`

| Catégorie | Volume | Commande |
|-----------|:------:|----------|
| Référentiels bilingues (12 natures, 3 motifs, 2 canaux, 4 critères, 5 types certificats) | ~26 entrées | `seed_referentiels` |
| Comptes de test | 7 utilisateurs | `seed_demo_test` |
| Parties (PP et PM) | 6 entités, dont 2 homonymes « DUPONT » | `seed_demo_test` |
| Inscriptions à différents statuts | 6 inscriptions + 1 demande de modification rejetée art. 88 | `seed_demo_test` |

### 3.2 Inscriptions exemples produites

| # | Statut | Nature | Description |
|:-:|:------:|--------|-------------|
| 1 | `INSCRITE` | Nantissement d'outillage | Inscription simple, bien avec n° série, durée 365 j |
| 2 | `MODIFIEE` | Nantissement de fonds de commerce | Modification art. 88 appliquée (augmentation somme garantie) |
| 3 | `RENOUVELEE` | Nantissement de stocks | Renouvellement appliqué, durée prorogée |
| 4 | `RADIEE` | Nantissement de créance | Radiation par consentement, mention « radiée » |
| 5 | `REJETEE` | Nantissement de compte bancaire | Rejet motif art. 80 (informations illisibles) |
| 6 | `EN_CONTROLE_FORME` | Nantissement de droits d'associés | En attente de validation greffier |

Plus une **demande de modification REJETEE art. 88 al. 4** (tentative
de retrait du dernier constituant de l'inscription 1) — visible en
consultation API + admin Django.

### 3.3 Commande de (re)chargement

```bash
# Charge ou met à jour (idempotent)
python manage.py seed_demo_test

# Purge + rechargement (⚠️ test uniquement)
python manage.py seed_demo_test --reset
```

---

## 4. Scénarios de test recommandés

**Note importante** : faute de formulaires frontend, les scénarios
s'exécutent via **API REST** (curl, HTTPie, Postman, Insomnia) ou
partiellement via **admin Django** (consultation). Un fichier de
commandes curl prêtes à copier est fourni :
[exemples_curl.md](exemples_curl.md).

### 4.1 Scénario A — Cycle complet d'une inscription

Enchaîne les 6 étapes d'une inscription :
1. Dépôt d'une demande (agent de saisie)
2. Contrôle de forme (automatique)
3. Ajout des parties et biens (admin Django ou endpoints futurs)
4. Validation par le greffier → attribution n° d'ordre
5. Consultation au fichier public via `/recherche/`
6. (Fin de vie) radiation ou expiration automatique

Acteurs : `agent_saisie` + `greffier`. **ACTIF** en environnement de test.

### 4.2 Scénario B — Rejet motivé art. 80

1. Dépôt d'une demande.
2. Le greffier soumet un motif hors liste → **400 + article 80**.
3. Le greffier soumet un motif limitatif (`informations_illisibles`)
   → **200, statut REJETEE, motif tracé, audit écrit**.

Acteurs : `agent_saisie` + `greffier`. **ACTIF**.

### 4.3 Scénario C — Modification contrôlée

1. Inscription INSCRITE (cf. scénario A).
2. Agent crée une `DemandeModification` (payload JSON via API).
3. Greffier applique → transition vers MODIFIEE, snapshots avant/après.

Acteurs : `agent_saisie` + `greffier`. **ACTIF**.

### 4.4 Scénario D — Refus art. 88 dernier alinéa

1. Tentative de retrait du dernier constituant.
2. Contrôle d'état final → refus + marquage REJETEE + motif
   `etat_final_constituant_absent` + audit `modification.refuser`.

Acteurs : `agent_saisie` + `greffier`. **ACTIF**. La demande de
modification rejetée produite par `seed_demo_test` illustre ce cas.

### 4.5 Scénario E — Renouvellement

1. Inscription INSCRITE (ou MODIFIEE) en cours de validité.
2. Agent crée une `DemandeRenouvellement`.
3. Greffier applique → date d'expiration prorogée de la durée initiale.
4. Tentative de renouvellement après expiration → refus art. 91.

Acteurs : `agent_saisie` + `greffier`. **ACTIF**.

### 4.6 Scénario F — Radiation

1. Inscription en cours de validité.
2. Agent crée une `DemandeRadiation` (fondement `consentement`).
3. Greffier applique → mention « radiée » + l'inscription reste au
   fichier public jusqu'à expiration.

Acteurs : `agent_saisie` + `greffier`. **ACTIF**.

### 4.7 Scénario G — Recherche publique + homonymes

1. Anonyme lance une recherche avec au moins 2 critères.
2. Si `nom_constituant` renseigné, le résultat inclut **tous les
   homonymes** (art. 97 al. 2). Les deux « DUPONT » sont produits
   par `seed_demo_test` pour illustrer.

Acteur : **non authentifié**. **ACTIF**.

### 4.8 Scénario H — Consultation audit + vérification chaîne

1. `auditeur` consulte `/api/v1/audit/entrees/` — liste paginée.
2. `auditeur` vérifie l'intégrité via
   `/api/v1/audit/verification-chaine/` → `{integre: true}`.

Acteur : `auditeur`. **ACTIF**.

### 4.9 Scénario I — Expiration automatique

1. Forcer une date d'expiration atteinte (mettre à jour une ligne en
   admin Django).
2. Lancer `python manage.py expirer_inscriptions`.
3. Inscriptions passent EXPIREE → ARCHIVEE, sortie du fichier public.

Acteur : automatique. **ACTIF**.

### 4.10 Ce qui reste SIMULÉ / STUB

| Mécanisme | État | Impact |
|-----------|:----:|--------|
| Horodatage opposable (F5) | STUB | Les `instant_saisie_opposable` sont produits par l'horloge locale — **non opposables juridiquement** |
| Scellement cryptographique (F6) | STUB | Les `empreinte` sont des SHA-256 non signés — **non probants** |
| Signature électronique art. 88 (F3) | Flags booléens | Les `accord_*_confirme` ne sont PAS cryptographiquement vérifiés |
| Certificats probants art. 97 (F4) | STUB | Tout `Certificat` a `probant=False`, pas de génération PDF/A bilingue |
| Authentification forte MFA (F2) | Session Django | Pas de second facteur |
| Paiement (F11) | Non implémenté | Les émoluments ne sont pas perçus |
| Notifications externes (F13) | Non câblé | Aucun email, SMS, ou webhook n'est envoyé |
| Interconnexion RCCM (F13) | Non câblée | Le n° RC est une pure énonciation (art. 86) |
| Frontend formulaires (Option B) | Non produit | Manipulation via API REST uniquement |

---

## 5. Points de vigilance

### 5.1 Ce qui ne doit PAS être interprété comme juridiquement opposable

- **Aucune inscription produite** dans l'environnement de test n'a
  de valeur juridique opposable aux tiers.
- **Aucun certificat émis** par le système n'est probant au sens de
  l'art. 97 dernier alinéa.
- **Aucun horodatage** n'a d'opposabilité au sens de l'art. 78.
- **Aucun journal d'audit** produit en test n'a force probante devant
  une juridiction — c'est un journal technique de démonstration.

Tout élément visible dans l'environnement de test doit être lu comme
un **aperçu fonctionnel**. Cette lecture est rappelée par la sonde
santé (`/fr/sante/`) qui expose publiquement l'état des zones gelées.

### 5.2 Paramétrages transitoires utilisés

| Paramètre | Valeur test | Décision MO attendue | Fiche |
|-----------|-------------|----------------------|-------|
| `DJANGO_SECRET_KEY` | Valeur de dev | À régénérer avant mise en production | — |
| `DJANGO_DEBUG` | `True` | `False` en production | — |
| `RSM_TIMESOURCE_MODE` | `local_stub` | À arbitrer | F5 |
| `RSM_SEAL_MODE` | `disabled` | À arbitrer | F6 |
| `RSM_ESIGN_MODE` | `disabled` | À arbitrer | F3 |
| `RSM_MFA_MODE` | `disabled` | À arbitrer | F2 |
| Mots de passe des comptes test | Fixes documentés | À rotater | — |
| Libellés bilingues des référentiels | Amorces | À valider par le comité § 7.3 | F1 |

### 5.3 Limites techniques connues de l'environnement de test

- **Pas de frontend complet** — la démonstration passe principalement
  par l'API REST.
- **Triggers PostgreSQL** : fonctionnent sur PostgreSQL 14+ ; non
  testés avec d'autres SGBD.
- **Concurrence** : le serveur de développement Django (`runserver`)
  est mono-threadé ; les tests de concurrence (art. 78) sont plus
  pertinents avec gunicorn multi-workers — non activé en mode test.
- **Performance** : non représentative d'un déploiement en production
  (pas de cache, pas d'optimisation base, index non tunés).
- **Frontend React** : le squelette fourni reste fonctionnel pour la
  **consultation** (liste inscriptions, liste audit, recherche) mais
  pas pour la **création/modification** de demandes.

### 5.4 Procédure de bascule vers une version de production

La bascule vers un environnement de production opposable **EXIGE** :

1. Décisions MO écrites sur F1, F5, F3, F4 au minimum (nœud cardinal
   d'opposabilité — cf. [comparatif_F1_F3_F4_F5.md](fiches_mo/comparatif_F1_F3_F4_F5.md)).
2. Régénération de `DJANGO_SECRET_KEY` avec une valeur forte.
3. Passage à `DJANGO_DEBUG=False`.
4. Configuration des modes non-STUB (`RSM_TIMESOURCE_MODE`,
   `RSM_SEAL_MODE`, `RSM_ESIGN_MODE`, `RSM_MFA_MODE`).
5. Réinitialisation complète de la base (les données test ne doivent
   **jamais** coexister avec des données opposables).
6. Rotation de tous les mots de passe de comptes test (ou mieux :
   suppression — cf. L2.4 `has_delete_permission=False`, à adapter
   par désactivation `compte_actif=False`).
7. Déploiement avec gunicorn + nginx / Apache, TLS obligatoire.
8. Activation de la supervision (métriques, alertes, logs
   centralisés).

Ce plan de bascule est le sujet d'un chantier distinct (non engagé
tant que les arbitrages MO ne sont pas rendus).

---

## 6. Arrêt et nettoyage

### 6.1 Arrêt normal

```bash
# Docker
docker compose -f docker-compose.test.yml down

# Native
# Ctrl+C sur le runserver
```

### 6.2 Purge complète

```bash
# Docker : supprime aussi les volumes (données BD)
docker compose -f docker-compose.test.yml down -v

# Native : supprime la BD
dropdb rsm_test
```

### 6.3 Diagnostic

```bash
# Vérifier l'intégrité du journal d'audit
curl -u auditeur:test-rsm-auditeur-2026 \
  http://localhost:8000/api/v1/audit/verification-chaine/

# Consulter les fiches d'arbitrage en attente
python manage.py lister_arbitrages_mo

# Exécuter la suite de tests automatisés
python manage.py test tests
```

---

## 7. Renvois croisés

- Exemples curl/HTTPie détaillés : [exemples_curl.md](exemples_curl.md).
- Dictionnaire complet des endpoints : [L3.4](L3_4_dictionnaire_api.md).
- Scénarios fonctionnels opposables : [L2.6](L2_6_scenarios_fonctionnels.md).
- Matrice des habilitations : [L2.4](L2_4_roles_operations.md).
- Zones gelées et comparatif : [fiches_mo/](fiches_mo/).
- Registre des risques et hypothèses : [L11](L11_tracabilite_articles_76_97.md).

---

## 8. Support

Pour un problème technique en environnement de test, la procédure
est :

1. Vérifier l'état via `GET /fr/sante/`.
2. Consulter les logs Docker : `docker compose -f docker-compose.test.yml logs backend`.
3. Relancer les tests automatisés : `python manage.py test tests`.
4. Vérifier les décisions MO rendues : elles peuvent modifier le
   comportement attendu.

Si le problème persiste, le registre `backend/tests/arbitrages_mo_en_attente.txt`
(produit par `python manage.py lister_arbitrages_mo`) liste les
comportements non encore activés — peut-être que ce qui semble « manquer » relève
d'une zone gelée en attente de décision MO.
