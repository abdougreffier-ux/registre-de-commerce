# L3.2 — Architecture modulaire

**Livrable** : L3.2 — partie du livrable L3 (§ 8 du TDR).
**Objet** : description des couches, modules, flux et dépendances du système.
**Fondement** : TDR § 6 (architecture fonctionnelle).
**État** : consolidation de l'existant. **Aucune règle nouvelle introduite.**

---

## 1. Principes directeurs

L'architecture matérialise cinq principes du TDR :

1. **Unicité de la base** (§ 6.3) — une seule base PostgreSQL, deux fichiers logiques (public, général).
2. **Unicité du moteur de règles** (§ 6.3) — toutes les règles de validation et de transition s'expriment dans les services, pas dans la présentation.
3. **Indépendance linguistique du stockage** (§ 6.3) — clés neutres, libellés bilingues séparés.
4. **Séparation stricte public / général** (§ 6.3, art. 77) — distinction logique par statut et champ `fichier_actuel`.
5. **Réversibilité** (art. 83) — absence de captivité technologique, code intégralement cessible.

---

## 2. Couches applicatives

```
┌────────────────────────────────────────────────────────────────────┐
│ PRÉSENTATION                                                       │
│  - Frontend React bilingue (rsm/frontend/) — AperÇu ; formulaires  │
│    reportés (Option B GELÉE en attente d'arbitrages MO).           │
│  - Templates Django bilingues (base, accueil).                     │
│  - Admin Django (verrouillée — cf. § 6 ci-dessous).                │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│ API REST (rest_framework)                                          │
│  - Routeur racine /api/v1/ (apps.core.api_urls).                   │
│  - Handler d'exceptions uniforme (apps.core.exception_handler).    │
│  - Serializers stricts (apps.core.serializers.StrictInput*).       │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│ SERVICES MÉTIER (moteur de règles unique)                          │
│  - apps.inscriptions.services  (art. 78, 80, 85, 86, 87)          │
│  - apps.modifications.services (art. 88, 90, 93)                   │
│  - apps.renouvellements.services (art. 91)                         │
│  - apps.radiations.services (art. 92)                              │
│  - apps.recherche.services (art. 94-97)                            │
│  - apps.statistiques.services (art. 82)                            │
│  - apps.workflow.services (moteur de transitions § 4.3)            │
│  - apps.audit.services (tracer, chaînage, vérification)            │
│  - apps.utilisateurs.habilitations (rôles § 4.1)                   │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│ DOMAINE (modèles ORM)                                              │
│  Mixins transverses : Horodatage, ActeurTrace, Bilingue,           │
│  DescriptionBilingue, ProtectionSuppression, ValiditeTemporelle    │
│  (apps.core.models, apps.core.mixins)                              │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│ PERSISTANCE (PostgreSQL 14+)                                       │
│  - Contraintes d'intégrité (CheckConstraints, UniqueConstraints).  │
│  - Index (art. 93, recherche art. 96).                             │
│  - Triggers d'immutabilité (journal d'audit).                      │
│  - Verrous pessimistes (SELECT … FOR UPDATE sur séquence n° d'ordre│
│    art. 78).                                                       │
└────────────────────────────────────────────────────────────────────┘
```

**Règle de dépendance** : une couche ne dépend que des couches situées en dessous d'elle. Aucun modèle ORM n'appelle un serializer. Aucune vue n'écrit directement en base.

---

## 3. Cartographie des applications Django

### 3.1 Applications transverses

| App | Rôle | Dépendances |
|-----|------|-------------|
| `apps.core` | Mixins, enums limitatives, exceptions typées, handler DRF, serializers stricts, admin bases, helpers horodatage / scellement (STUB). | — |
| `apps.audit` | Journal inaltérable chaîné, middleware acteur courant, API lecture seule auditeur. | core |
| `apps.referentiels` | Libellés bilingues FR/AR + commande `seed_referentiels`. | core |
| `apps.utilisateurs` | Modèles User + AffectationRole, habilitations § 4.1, signaux de traçabilité. | core, audit |
| `apps.workflow` | Statuts + matrice § 4.3 + service `appliquer_transition` + historique append-only. | core, audit, utilisateurs |

### 3.2 Applications métier

| App | Rôle | Dépendances |
|-----|------|-------------|
| `apps.parties` | Personnes physiques / morales. | core |
| `apps.biens` | Biens grevés (validité temporelle). | core, inscriptions (FK) |
| `apps.inscriptions` | Inscription, `RoleInscriptionPartie`, `PieceJointe`, `SequenceNumeroOrdre`. Services clés : `creer_demande`, `prononcer_rejet`, `valider_inscription`, `attribuer_numero_ordre`. | core, audit, workflow, utilisateurs, parties, biens, referentiels (via enums) |
| `apps.modifications` | `DemandeModification`, `SnapshotInscription`, `DiffModification` (schéma strict), `appliquer_modification`. | core, audit, workflow, utilisateurs, inscriptions, parties, biens |
| `apps.renouvellements` | `DemandeRenouvellement`, `appliquer_renouvellement`. | core, audit, workflow, utilisateurs, inscriptions |
| `apps.radiations` | `DemandeRadiation`, `appliquer_radiation`. | core, audit, workflow, utilisateurs, inscriptions |
| `apps.rejets` | Pas de modèle propre ; vue de consultation des rejets (statut REJETEE). | core, inscriptions |
| `apps.recherche` | Moteur de recherche publique art. 94-97, `RequeteRecherche` append-only. | core, audit, inscriptions, parties, biens |
| `apps.certificats` | `Certificat` (GELÉ pour probant), service `preparer_certificat`. | core, audit, inscriptions, recherche |
| `apps.statistiques` | `ExtractionStatistique` append-only, service `produire_extraction` (monopole art. 82). | core, audit, inscriptions, utilisateurs |
| `apps.administration` | Réservée aux paramètres fonctionnels ; commande `lister_arbitrages_mo`. | — |

**Règle** : aucune dépendance circulaire. Le graphe est un DAG dont les racines sont `core`, `audit` et `referentiels`.

---

## 4. Flux métier de référence

### 4.1 Dépôt d'une inscription initiale (art. 78, 85, 86, 87)

```
    Client (agent de saisie OU déclarant externe)
         │
         ▼
    POST /api/v1/inscriptions/
         │  payload : DeposerInscriptionSerializer
         │          (strict — clés inconnues refusées)
         ▼
    ListeDeposerInscription.create()
         │
         ▼
    apps.inscriptions.services.creer_demande()
         │
         │  1. peut_enregistrer_demande(acteur)          [§ 4.1]
         │  2. canal_saisie ∈ CanalSaisie                [art. 78]
         │  3. nature_droit ∈ NaturesDroitInscrit        [art. 76]
         │  4. Inscription(statut=RECUE, instant_arrivee=now)
         │  5. apps.audit.services.tracer(DEMANDE, "inscription.deposer")
         │  6. appliquer_transition RECUE → EN_CONTROLE_FORME  [§ 4.3]
         │
         ▼
    Réponse 201 : InscriptionSerializer
         (numero_ordre nul, statut=EN_CONTROLE_FORME)
```

**Puis** : `POST /api/v1/inscriptions/<uuid>/valider/` → `valider_inscription()` :

1. `peut_valider_demande(acteur, saisie_par=inscription.cree_par)` — séparation stricte § 4.1.
2. `attribuer_numero_ordre()` → verrou `SELECT … FOR UPDATE`, incrémentation, horodatage (STUB).
3. `numero_ordre = format(ordre, instant)` → `NNNNNN-AAAAMMJJHHMMSS` (art. 78 al. 4).
4. `date_expiration = instant.date() + duree_en_jours`.
5. Transition `EN_CONTROLE_FORME → INSCRITE`.
6. Audit `inscription.valider`.

### 4.2 Modification contrôlée (art. 88, 90, 93)

```
POST /api/v1/modifications/
     │
     ▼  DemandeModificationSerializer (strict)
     │
POST /api/v1/modifications/<id>/appliquer/
     │
     ▼
apps.modifications.services.appliquer_modification()
     │
     ├─ 1. Recevabilité : statut RECUE, inscription en cours,
     │     habilitations, accords des parties (art. 88)
     │
     ├─ 2. DiffModification.depuis_dict(diff_propose)
     │     - clés racine ∈ {parties, biens, scalaires}
     │     - CHAMPS_JAMAIS_MODIFIABLES refusés (art. 78, 90 al. 2)
     │     - Valeurs de nature_droit ∈ NaturesDroitInscrit
     │
     ├─ 3. Marquage REJETEE (motif_refus_code) + audit
     │     si échec étape 1 ou 2 → RETURN
     │
     ├─ 4. savepoint = transaction.savepoint()
     │
     ├─ 5. Snapshot AVANT (serialiser_inscription + sceller STUB)
     │
     ├─ 6. Application du diff :
     │     - désactivation des rôles retirés (actif=False)
     │     - désactivation des biens retirés (actif=False)
     │     - création des rôles / biens ajoutés
     │     - mise à jour des scalaires
     │
     ├─ 7. inscription.refresh_from_db()
     │
     ├─ 8. _verifier_etat_final(inscription) [art. 88 dernier al.]
     │     - ≥1 constituant actif
     │     - ≥1 créancier garanti actif
     │     - ≥1 bien grevé actif
     │     Si échec : savepoint_rollback → marquage REJETEE → RAISE
     │
     ├─ 9. Snapshot APRÈS
     │
     ├─10. appliquer_transition → MODIFIEE [§ 4.3]
     │
     ├─11. savepoint_commit + demande.statut=APPLIQUEE + audit
     │
     ▼
Réponse 200 OK
```

### 4.3 Recherche publique (art. 94-97)

```
    Client (anonyme ou authentifié)
         │
         ▼
    POST /api/v1/recherche/
         │  _CriteresSerializer (strict — 4 critères art. 96 max)
         ▼
    RecherchePublique.post()
         │
         ▼
    apps.recherche.services.rechercher(CriteresRecherche)
         │
         │  1. Comptage des critères renseignés ≥ 2  [art. 96]
         │  2. QuerySet = Inscription ∈ STATUTS_FICHIER_PUBLIC
         │  3. Jointure par rôles (constituant), RC, numéro de série, n° d'ordre
         │  4. Si nom : agrégation EXHAUSTIVE des homonymes [art. 97 al. 2]
         │  5. Persistance RequeteRecherche (append-only)
         │  6. Audit RECHERCHE "recherche.lancer"
         │
         ▼
    Réponse 200 : résultats + homonymes + avertissement
                  "aperçu non opposable — certificat probant GELÉ"
```

### 4.4 Expiration automatique (art. 85, 92 al. 3)

```
    Cron quotidien : python manage.py expirer_inscriptions
         │
         ▼
    Pour chaque Inscription ∈ STATUTS_FICHIER_PUBLIC
    avec date_expiration ≤ aujourd'hui :
         │
         ├─ Transition → EXPIREE (automatique)
         ├─ Transition → ARCHIVEE + fichier_actuel=GENERAL
         └─ Audit SYSTEME "inscription.expirer_archiver"
```

---

## 5. Règles d'intégration inter-apps

### 5.1 Sens des appels

- Les vues (DRF) appellent les services.
- Les services appellent les modèles ORM + `tracer()` + `appliquer_transition()`.
- `appliquer_transition()` appelle `tracer()` et crée une ligne `TransitionStatut`.
- Aucun service métier n'appelle une vue.
- Aucun modèle ORM n'appelle un service.

### 5.2 Points de mutation

**Mutation autorisée sur une inscription** : exclusivement via un service.

| Opération | Service autorisé | Autorisation |
|-----------|------------------|--------------|
| Création (demande reçue) | `inscriptions.services.creer_demande` | rôles `AGENT_SAISIE` ou `DECLARANT_EXTERNE` |
| Rejet art. 80 | `inscriptions.services.prononcer_rejet` | rôle `AUTORITE_VALIDATION`, séparation stricte sur la demande |
| Validation art. 87 | `inscriptions.services.valider_inscription` | idem |
| Modification art. 88 | `modifications.services.appliquer_modification` | idem + accords art. 88 confirmés |
| Renouvellement art. 91 | `renouvellements.services.appliquer_renouvellement` | idem + avant expiration |
| Radiation art. 92 | `radiations.services.appliquer_radiation` | idem |
| Expiration / archivage auto | commande `expirer_inscriptions` | sans acteur humain, transitions automatiques |

**Aucune autre voie** ne peut muter une inscription : ni l'admin Django (classes verrouillées), ni un ORM direct (overrides `delete()`), ni l'injection de clés hors schéma (serializers stricts).

### 5.3 Événements tracés

Catégories (enum `CategorieAudit`, 11 valeurs limitatives) :

`connexion`, `compte`, `demande`, `controle_forme`, `validation`, `rejet`, `certificat`, `recherche`, `export_stat`, `admin`, `systeme`.

Chaque service métier écrit au moins une entrée par opération significative.

---

## 6. Défense en profondeur

Le système met en œuvre **quatre remparts indépendants** contre toute
altération non prévue par le décret. Aucune voie unique ne peut les
contourner tous.

### Rempart 1 — PostgreSQL

- Triggers `rsm_audit_pas_update` et `rsm_audit_pas_delete` sur `audit_entreeaudit` (migration `apps/audit/migrations/0002_append_only_triggers`).
- CheckConstraints (ex. `pp_sans_denomination` sur `Partie`).
- UniqueConstraints conditionnelles (ex. `unique_partie_role_actif_par_inscription`).
- Transactions atomiques et verrous pessimistes.

### Rempart 2 — ORM Django

Overrides `save()` / `delete()` refusant les opérations interdites :

| Modèle | `save()` (update) | `delete()` |
|--------|:-:|:-:|
| `EntreeAudit` | ❌ | ❌ |
| `TransitionStatut` | ❌ | ❌ |
| `RequeteRecherche` | ❌ | ❌ |
| `SnapshotInscription` | ❌ | ❌ |
| `ExtractionStatistique` | ❌ | ❌ |
| `SequenceNumeroOrdre` | ❌ (sauf flag `_force` interne) | ❌ |
| `BienGreve` | ✅ (désactivation) | ❌ |
| `RoleInscriptionPartie` | ✅ (désactivation) | ❌ |

### Rempart 3 — DRF (API)

- `rsm_exception_handler` (cf. `apps.core.exception_handler`) traduit :
  - `ErreurMetierRSM` (et filles `RejetForme`, `ModificationSansEffet`, `RenouvellementHorsDelai`, `TransitionInterdite`, etc.) → HTTP 400 avec `detail`, `article`, `classe` ;
  - `AutorisationRefusee` → HTTP 403 ;
  - `PermissionError` → HTTP 403 avec `article=79`.
- Serializers stricts : toute clé inconnue → 400 avec champ `non_autorises`.

### Rempart 4 — Admin Django

Cf. L3.1 § 3.4 et la matrice d'habilitation intégrée à L11.

- `LectureSeuleAdmin` pour les append-only : aucune permission.
- `ConsultationMetierAdmin` pour les entités métier : aucune permission (service only).
- `EditionRestreinteAdmin` pour les référentiels et affectations : add/delete refusés.
- Actions de masse désactivées uniformément.

---

## 7. Bilinguisme architectural (§ 6.3, § 7)

### 7.1 Unicité

- **Un seul modèle de données** utilisé par les deux langues.
- **Un seul moteur de règles** — les services sont strictement identiques quelle que soit la langue active.
- **Un seul journal d'audit** — les `action_cle` sont neutres linguistiquement (ex. `inscription.deposer`, `modification.refuser`).

### 7.2 Résolution des libellés

| Niveau | Mécanisme |
|--------|-----------|
| Interface utilisateur (templates, React) | `gettext` / `i18next` avec fichiers `.po` / `.json` |
| Référentiels métier | Modèles `Libelle*` avec `libelle_fr`, `libelle_ar`, `langue_faisant_foi` |
| Champs descriptifs saisis | Paires `description_fr` / `description_ar` + `langue_faisant_foi_description` |
| Journal d'audit | Clés stables neutres (lecture dans les deux langues sans transformation) |
| API | Expose à la fois la clé neutre (`nature_droit="nant_outillage"`) et un libellé résolu (`nature_droit_libelle`) selon `Accept-Language` |

### 7.3 Équivalence juridique

Toute règle du décret produit **exactement les mêmes effets** quelle que soit la langue d'accès :

- mêmes statuts (clés neutres) ;
- mêmes transitions (matrice unique) ;
- mêmes motifs de rejet (enum neutre + libellés bilingues) ;
- mêmes horodatages, mêmes numéros, mêmes scellements ;
- mêmes certificats en contenu (rendus `fr`, `ar` ou `fr-ar` mais contenu canonique identique).

Ce principe est testé par `tests/test_referentiels.py::BilinguismePairesTests` et implicitement par toute la suite d'intégration API.

### 7.4 Direction d'écriture

- Templates Django : `dir="rtl"` posé sur `<html>` selon la langue active (`{% get_current_language %}`).
- Frontend React : `i18n.appliquerDirection()` pose `dir` dynamiquement.
- Aucune règle de mise en page n'utilise `left` / `right` codés en dur — toutes les règles CSS logiques (`margin-inline-start`, etc.).

---

## 8. Zones gelées implantées

Les zones gelées sont explicitement matérialisées dans le code pour être
reconnaissables à la revue et activables par configuration, sans
réécriture, dès qu'un arbitrage MO est rendu.

| Zone | Matérialisation |
|------|-----------------|
| Horodatage opposable (art. 78, § 5.1) | `apps.core.horodatage` — interface `maintenant_opposable()` ; mode `local_stub` en settings. |
| Scellement cryptographique (§ 6.3) | `apps.core.scellement` — interface `sceller()` / `verifier()` ; mode `disabled` en settings. |
| Signature électronique (art. 88) | Flags applicatifs `accord_createur_confirme` / `accord_constituant_confirme` ; vérification cryptographique non câblée. |
| Certificats probants (art. 97) | `apps.certificats.services.preparer_certificat` — produit un certificat `probant=False` avec avertissement. |
| Paiement électronique (art. 85) | Non implémenté. Aucun champ ni service. |
| Interconnexions externes (RCCM, etc.) | Non implémentées. Le n° RC est une pure énonciation (art. 86). |
| Authentification forte / MFA (§ 5.1) | Non implémentée. Auth Django session seulement en développement. |

Toute tentative d'usage d'une zone gelée émet un `warnings.warn` explicite (Python) et conduit à un certificat / horodatage non opposable.

**Consolidation MO** : `python manage.py lister_arbitrages_mo` produit le registre `backend/tests/arbitrages_mo_en_attente.txt` (11 tests désactivés).

---

## 9. Déploiement et exploitation

### 9.1 Environnements

- Dev : SQLite accepté à défaut — tests couvrant les triggers PostgreSQL uniquement dans un environnement PostgreSQL.
- Pré-production / production : PostgreSQL 14+ OBLIGATOIRE (triggers, contraintes conditionnelles).

### 9.2 Variables de configuration (`.env`)

| Variable | Rôle | Valeur STUB |
|----------|------|-------------|
| `RSM_TIMESOURCE_MODE` | Source de temps | `local_stub` |
| `RSM_SEAL_MODE` | Scellement | `disabled` |
| `RSM_ESIGN_MODE` | Signature électronique | `disabled` |
| `RSM_MFA_MODE` | Authentification forte | `disabled` |
| `DB_*` | PostgreSQL | à fournir |
| `DJANGO_*` | secret, hosts, debug | à fournir |

### 9.3 Commandes opérationnelles

- `python manage.py migrate` — applique les migrations, pose les triggers.
- `python manage.py seed_referentiels` — charge les libellés bilingues FR/AR.
- `python manage.py expirer_inscriptions` — quotidien, expiration et archivage (art. 92 al. 3).
- `python manage.py lister_arbitrages_mo` — registre des zones gelées.
- `python manage.py test tests` — suite complète (60+ tests).

---

## 10. Réversibilité (art. 83)

L'article 83 autorise le transfert de la tenue du RSM à un autre
organisme. L'architecture doit permettre ce transfert **sans perte
d'information ni dépendance captive**.

| Élément | Mode de cession |
|---------|-----------------|
| Code source | Licence ouverte interne ; versionné sous Git ; cessible intégralement. |
| Base de données | Export PostgreSQL `pg_dump` + triggers. Import complet possible sur tout PostgreSQL 14+. |
| Référentiels bilingues | Fixtures `apps/referentiels/fixtures/*.json` versionnées. |
| Journal d'audit | Exporté tel quel ; la chaîne d'empreintes se vérifie sur le nouveau système via `verifier_chaine()`. |
| Snapshots | Exportés ; contenu canonique lisible sans dépendance. |
| Documentation | L1, L3 (sous-livrables), L11, README. |
| Configuration | `.env.example` + procédure documentée. |
| Clés cryptographiques | GELÉES (arbitrage MO) ; la politique de conservation et de cession devra être fixée avec le choix d'infrastructure. |

---

## 11. Renvois croisés

- Modèle de données détaillé : [L3.1](L3_1_modele_donnees.md).
- Politique d'horodatage et de scellement : [L3.3](L3_3_horodatage_scellement.md).
- Traçabilité article par article + matrice admin : [L11](L11_tracabilite_articles_76_97.md).
- Note de cadrage initiale : [L1](L1_note_de_cadrage.md).
