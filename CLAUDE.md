# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Langue de travail

Tout le code, les commentaires, la documentation et les échanges sont en **français**, avec terminologie juridique stricte. Le maître d'ouvrage (MO) est le Tribunal de commerce de Nouakchott. Ne pas traduire les identifiants métier, les noms d'apps Django, ni les libellés.

## Contenu du dépôt

Ce dossier regroupe plusieurs livrables distincts pour le RCCM mauritanien. Bien identifier lequel on touche :

- **`rsm/`** — **Projet actif.** Registre des Sûretés Mobilières (RSM). Django 4.2 + DRF (backend) et React 18 + Ant Design (frontend), bilingue FR/AR. C'est ici que se concentre le travail.
- **`web/`** — Système d'immatriculation du Registre du Commerce (RCCM). Backend Django (`web/backend_django/`), frontend React, déployé sur Railway. Gouverné par la règle **MIGRATIONS_OK** (voir `web/DEPLOIEMENT.md`).
- **`ccrcsm-site/`** — Site institutionnel statique du CCRCSM, généré avec Eleventy (11ty).
- **Racine** (`*.wde`, `*.wdc`, `ETAT_*`, `*.png/.gif`) — Application RCCM desktop historique en WinDev/WebDev. Ne pas modifier sauf demande explicite.

---

## Projet RSM (`rsm/`)

### Commandes

Backend (`rsm/backend/`, venv déjà présent) :

```bash
python manage.py migrate
python manage.py seed_referentiels          # données de référence obligatoires
python manage.py seed_demo_test             # jeu de démonstration (mode test)
python manage.py runserver
python manage.py test                       # toute la suite
python manage.py test tests.test_workflow   # un seul module
python manage.py test tests.test_workflow.NomDeLaClasse.test_methode  # un seul test
python manage.py expirer_inscriptions       # tâche quotidienne d'expiration (prod)
python manage.py lister_arbitrages_mo       # liste des tests gelés faute d'arbitrage MO
```

**Les tests exigent PostgreSQL**, jamais SQLite : les triggers append-only du journal d'audit et les index full-text FR/AR en dépendent. La variable `RSM_MODE_TEST` (défaut `true`) active les stubs probants et désactive le contrôle CSRF.

Environnement de test complet via Docker : `docker compose -f rsm/docker-compose.test.yml up --build` (Postgres sur le port hôte 5433, backend sur 8000).

Frontend (`rsm/frontend/`) : `npm install`, puis `npm start` (proxy vers `http://localhost:8000`), `npm run build`, `npm test`.

### Architecture

Backend organisé en apps Django sous `rsm/backend/apps/`, séparées en **transverses** (`core`, `audit`, `referentiels`, `utilisateurs`, `workflow`) et **métier** (`parties`, `biens`, `inscriptions`, `modifications`, `renouvellements`, `radiations`, `rejets`, `recherche`, `certificats`, `statistiques`, `administration`, `interconnexions`). Chaque opération métier suit le cycle de vie d'une *demande* géré par `workflow` (statuts + transitions dans `apps/workflow/statuts.py` et `services.py`).

Conventions structurelles à respecter dans toute app :
- La logique métier vit dans `services.py` (fonctions, ex. `creer_demande`, `valider_inscription`), pas dans les vues ni les serializers.
- Les exceptions métier sont typées (`apps/core/exceptions.py`) et converties en réponses HTTP par `apps.core.exception_handler.rsm_exception_handler`.
- Les énumérations partagées sont dans `apps/core/enums.py`.
- `AUTH_USER_MODEL = "utilisateurs.Utilisateur"` ; les rôles applicatifs sont des `AffectationRole` (voir `RoleApplicatif`), pas les permissions Django natives.

**Journal d'audit (inviolable).** Toute action passe par l'unique fonction `apps.audit.services.tracer(...)` — aucun `EntreeAudit.objects.create` direct n'est autorisé. Les entrées sont chaînées par empreinte SHA-256 (chaque entrée englobe l'empreinte de la précédente). Le journal est append-only : `AUDIT_ALLOW_DELETE = False`, `AUDIT_ALLOW_UPDATE = False`, renforcé par triggers SQL. Le middleware `apps.audit.middleware.CurrentActorMiddleware` capte l'acteur courant.

### Règles non négociables (verrous MO)

Ces invariants priment sur toute considération de simplicité ou d'UX :

1. **Intégrité du registre** : aucune opération ne contourne le workflow ni n'altère un acte scellé.
2. **Traçabilité totale** : toute action est consignée au journal d'audit chaîné append-only.
3. **Parité juridique FR/AR stricte** : toute divergence entre les versions française et arabe est une non-conformité majeure. Le système est bilingue FR/AR **uniquement** ; n'ajouter aucune langue.
4. **Séparation stricte saisie/validation** : un même acteur ne peut ni saisir ni valider la même demande.
5. **Pas d'invention fonctionnelle ni de simplification juridique** : ne pas ajouter de fonction non prévue, ne pas assouplir une règle du décret.

### Zones gelées (en attente d'arbitrage MO)

Sept dispositifs probants ne sont **pas** implémentés en attendant les arbitrages institutionnels (PKI nationale, identité numérique) : horodatage opposable (art. 78), scellement cryptographique (art. 97), signature électronique des parties (art. 88), certificats probants (art. 97), paiement électronique (art. 85), interconnexions externes (RCCM / identité), authentification forte MFA. Ils tournent en mode STUB piloté par les variables `RSM_TIMESOURCE_MODE`, `RSM_SEAL_MODE`, `RSM_ESIGN_MODE`, `RSM_MFA_MODE`, `RSM_INTEROP_BANQUES_MODE`. Chaque zone gelée est signalée dans le code par un commentaire `ZONE GELÉE`. **Ne pas lever une zone gelée sans décision MO explicite** — les fiches de décision sont dans `rsm/docs/fiches_mo/`.

### Référentiel documentaire

Le fondement juridique est le **chapitre IV (art. 76-97) du décret 2021-033**. Le TDR v1.0 (Nouakchott 2026) est la base de référence. Les livrables fonctionnels (L2) et techniques (L3), la traçabilité article par article (L11) et les fiches d'arbitrage MO sont dans `rsm/docs/`. Consulter ces documents avant toute décision de conception touchant une règle métier.

---

## Projet web/ (RCCM)

Avant toute recette, démonstration ou mise en production : le schéma doit signaler **MIGRATIONS_OK** (modèles Django synchronisés avec la base). Règle non négociable détaillée dans `web/DEPLOIEMENT.md`. Lancement dev local : `web/start-dev.bat` (backend Django port 8000 + frontend React).

## Projet ccrcsm-site/

Site statique Eleventy bilingue. `npm run dev` (serve + watch sur le port 8080), `npm run build` (sortie `_site/`).

---

## État d'avancement (au 2026-05-30)

> **Note sur la source.** Cet état est dérivé du **contenu de l'arbre de travail**, et non de l'historique Git ou des pull requests : ceux-ci ne fournissent aucun signal exploitable (voir « Mise sous version » ci-dessous). À réviser à chaque évolution notable.

### Mise sous version — point d'attention prioritaire

L'unique commit du dépôt (`first commit`, 2026-04-04) ne contient que **l'application desktop WinDev/WebDev historique** (fichiers `.wde`, `.wdc`, `ETAT_*`, images) à la racine. Les **trois projets actifs `rsm/`, `web/`, `ccrcsm-site/` ne sont pas suivis par Git** (entièrement non trackés). Conséquences :

- Aucun historique de modifications, aucune PR, aucune branche de travail avec diff : le dépôt distant (`registre-de-commerce`) a une seule branche `main` et **zéro pull request**.
- Il n'existe **pas de `.gitignore`** : avant tout premier commit des projets, en ajouter un (exclure au minimum `**/venv/`, `**/node_modules/`, `_site/`, `**/__pycache__/`, `*.env*`).
- Premier vrai versionnage des projets applicatifs = travail à faire, non encore engagé.

### `rsm/` (projet actif) — substantiellement développé

- **Backend** : architecture complète et mature — 16 apps Django (transverses + métier), couche `services.py`, workflow statuts/transitions, journal d'audit chaîné append-only, gestion d'exceptions typées, 4 commandes de management (`seed_referentiels`, `seed_demo_test`, `expirer_inscriptions`, `lister_arbitrages_mo`). Suite de tests fournie : **22 modules** couvrant les scénarios S1–S6, la séparation stricte, les rejets (art. 80/88), la concurrence (art. 78), les habilitations, les zones gelées et la robustesse transactionnelle.
- **Frontend** : interface React FR/AR conséquente (~35 fichiers source) — pages de bout en bout (connexion, accueil, inscriptions, formulaires inscription/modification/radiation/renouvellement, détail, audit, gestion des catégories de biens), composants officiels (en-tête, pied de page, sceau, bandeau mode test), i18n FR/AR et contexte d'authentification. Au-delà d'un simple squelette.
- **Documentation** : livrables aboutis — L1 (cadrage), L2 (fonctionnel complet), L3 (technique complet), L11 (traçabilité art. 76–97) et fiches MO F1–F15.
- **En cours / en attente** : les **7 zones gelées** tournent en mode STUB dans l'attente des arbitrages MO (PKI, identité numérique). L'interopérabilité bancaire (fiche F15) existe en modèles seulement, sans endpoint exposé (`RSM_INTEROP_BANQUES_MODE=disabled`). Le système est en **mode test/recette** (`RSM_MODE_TEST=true` par défaut) — non opposable.

### `web/` (RCCM immatriculation)

Backend Django (`web/backend_django/`) + frontend React, configurés pour un déploiement Railway (`railway.json`, `nixpacks.toml`). Gouverné par la règle **MIGRATIONS_OK** avant toute recette/démo/production (`web/DEPLOIEMENT.md`).

### `ccrcsm-site/` (site institutionnel)

Site statique Eleventy bilingue ; build déjà généré (`_site/` présent dans l'arbre de travail).
