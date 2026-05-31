# L3.1 — Modèle de données consolidé

**Livrable** : L3.1 — partie du livrable L3 (§ 8 du TDR).
**Objet** : description complète et opposable du modèle de données du système RSM.
**Fondement** : chapitre IV (articles 76 à 97) du décret 2021-033 et TDR § 6.
**État** : spécifications techniques consolidant l'existant. **Aucune règle nouvelle**.

---

## Conventions

- **Clé neutre linguistiquement** (§ 6.3 TDR) : valeur stockée sans variation FR/AR. Ex. : numéros, dates, montants, identités propres, énumérations limitatives du décret.
- **Champ bilingue** (§ 6.3 TDR) : paire de colonnes `*_fr` + `*_ar` avec mention explicite de la langue faisant foi lorsqu'une seule version est renseignée.
- **Append-only** (art. 79) : entité dont la suppression physique est interdite au niveau ORM (override `delete()` → `PermissionError`) et, pour le journal d'audit, également au niveau PostgreSQL (triggers).
- **Validité temporelle** : entité disposant des champs `actif` + `date_fin_validite` + `raison_fin`. La « désactivation » remplace toute suppression.
- **Créé par service** : entité dont la création et la mutation passent exclusivement par un service applicatif (`apps.*.services`). L'admin Django ne les mute jamais.

---

## 1. Cartographie des entités

```
                                RSM — vue consolidée
┌──────────────────────────────────────────────────────────────────────────┐
│ TRANSVERSES                                                              │
│  ┌───────────────────┐   ┌──────────────────────┐                        │
│  │ Utilisateur       │   │ EntreeAudit          │ append-only + chaînée │
│  │ AffectationRole   │   │ (apps.audit)         │                       │
│  │ (apps.utilisateurs│   └──────────────────────┘                        │
│  └───────────────────┘   ┌──────────────────────┐                        │
│  ┌───────────────────┐   │ TransitionStatut     │ append-only             │
│  │ LibelleNatureDroit│   │ (apps.workflow)      │                         │
│  │ LibelleMotifRejet │   └──────────────────────┘                        │
│  │ LibelleCanalSaisie│   ┌──────────────────────┐                        │
│  │ LibelleCritRech.  │   │ RequeteRecherche     │ append-only             │
│  │ LibelleTypeCert.  │   │ (apps.recherche)     │                         │
│  │ (apps.referentiels│   └──────────────────────┘                        │
│  └───────────────────┘                                                   │
└──────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────┐
│ NOYAU MÉTIER                                                             │
│                                                                          │
│   Partie ─────┐                                                          │
│   (PP/PM)     │                                                          │
│               ▼                                                          │
│     RoleInscriptionPartie ─(N)─►  Inscription ◄──(N)─ BienGreve          │
│       (validité                    (append-only,                          │
│        temporelle)                  statut § 4.3,                         │
│                                     numéro d'ordre)                       │
│                                      ▲                                    │
│                                      │                                    │
│     ┌────────────────────────────────┼───────────────────────────────┐   │
│     │                                │                               │   │
│     │   DemandeModification          │                               │   │
│     │   DemandeRenouvellement        │                               │   │
│     │   DemandeRadiation             │                               │   │
│     │   PieceJointe                  │                               │   │
│     │     (toutes rattachées à l'inscription initiale, art. 93)      │   │
│     └────────────────────────────────┼───────────────────────────────┘   │
│                                      │                                    │
│              SnapshotInscription ────┘                                    │
│                (append-only, avant/après modifications)                   │
│                                                                          │
│     Certificat  ──► Inscription / RequeteRecherche (GELÉ pour probant)   │
│     ExtractionStatistique (append-only, art. 82)                         │
│     SequenceNumeroOrdre (singleton, verrou SELECT FOR UPDATE)            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Entités par module

### 2.1 `apps.audit` — Journal inaltérable

#### `EntreeAudit` (append-only, chaînée)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `id` | BigAuto | PK | — |
| `instant` | DateTime | NOT NULL, indexé | § 5.2 |
| `categorie` | Char(32) | Enum `CategorieAudit` (11 valeurs limitatives) | § 5.2 |
| `action_cle` | Char(80) | clé neutre linguistiquement | § 7.6 |
| `acteur` | FK → Utilisateur | PROTECT, nullable (événements système) | § 5.2 |
| `acteur_role` | Char(48) | rôle applicatif actif lors de l'action | § 4.1 |
| `objet_type` | Char(64) | — | § 5.2 |
| `objet_reference` | Char(120) | — | § 5.2 |
| `resultat` | Char(32) | Enum `ResultatAudit` | § 5.2 |
| `details` | JSON | payload structuré neutre linguistiquement | § 7.6 |
| `empreinte_precedente` | Char(128) | chaînage | § 5.2 |
| `empreinte` | Char(128) | SHA-256 du payload canonicalisé + empreinte_precedente | § 5.2 |
| `adresse_ip` | INET | null | § 5.2 |
| `user_agent` | Char(255) | — | § 5.2 |

**Invariants** :
- `save()` refusé si `self.pk is not None` → création uniquement.
- `delete()` refusé → append-only au niveau ORM.
- Triggers PostgreSQL `rsm_audit_pas_update` / `rsm_audit_pas_delete` → append-only au niveau base (migration `0002_append_only_triggers`).
- L'empreinte se calcule sur `{instant, catégorie, action_cle, résultat, acteur_id, acteur_role, objet_type, objet_reference, details, empreinte_precedente}` (JSON canonique, clés triées).

**Relations sortantes** : aucune (journal autonome).

---

### 2.2 `apps.workflow` — Matrice des transitions

#### `TransitionStatut` (append-only)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `id` | BigAuto | PK | — |
| `numero_inscription` | Char(64) | clé naturelle, indexé | art. 78, 93 |
| `statut_avant` | Char(32) | Enum `StatutInscription`, vide pour la création | § 4.3 |
| `statut_apres` | Char(32) | Enum `StatutInscription` | § 4.3 |
| `evenement` | Char(64) | identifiant stable (ex. `validation_greffier`, `rejet_art80`) | § 4.3 |
| `articles_fondateurs` | Char(64) | ex. `"art. 85, 86"` | — |
| `motif` | Char(255) | — | § 4.3 |
| `instant` | DateTime | indexé | art. 78, § 5.2 |
| `acteur` | FK → Utilisateur | PROTECT, nullable (transitions auto) | § 4.1 |
| `acteur_role` | Char(48) | — | § 4.1 |
| `automatique` | Bool | True pour transitions système | § 4.3 |

**Invariants** :
- Même règle append-only qu'`EntreeAudit`.
- Table complémentaire au journal d'audit : historise spécifiquement les états juridiques d'une inscription.

**Statuts limitatifs (9)** — `apps.workflow.statuts.StatutInscription` :
`RECUE` · `EN_CONTROLE_FORME` · `REJETEE` · `INSCRITE` · `MODIFIEE` · `RENOUVELEE` · `RADIEE` · `EXPIREE` · `ARCHIVEE`.

**Matrice autorisée** — [apps/workflow/statuts.py::TRANSITIONS](../backend/apps/workflow/statuts.py) : 15 transitions formalisées.

**Interdictions explicites** — [apps/workflow/statuts.py::INTERDICTIONS_EXPLICITES](../backend/apps/workflow/statuts.py) : 4 paires refusées au niveau matrice (contrôle croisé par test `test_matrice_et_interdictions_disjointes`).

---

### 2.3 `apps.recherche` — Traces des recherches

#### `RequeteRecherche` (append-only)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `id` | BigAuto | PK | — |
| `instant` | DateTime | indexé | art. 97 al. 3 |
| `criteres_soumis` | JSON | clés limitatives art. 96 | art. 96 |
| `nombre_resultats` | PositiveInt | — | — |
| `adresse_ip` | INET | null | § 5.2 |
| `user_agent` | Char(255) | — | § 5.2 |

**Invariants** : append-only. Trace indispensable à la valeur probante du certificat de recherche (art. 97 al. 4, ZONE GELÉE).

---

### 2.4 `apps.utilisateurs` — Comptes et rôles

#### `Utilisateur` (hérité de `AbstractUser`)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `username`, `email`, `password`, … | — | Django standard | — |
| `identifiant_officiel` | Char(64) | neutre linguistiquement, indexé | — |
| `nom_affichage` | Char(200) | — | — |
| `telephone` | Char(32) | — | — |
| `compte_actif` | Bool | désactivation logique (pas de delete) | art. 79 |

#### `AffectationRole`

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `utilisateur` | FK → Utilisateur | PROTECT | § 4.1 |
| `role` | Char(32) | Enum `RoleApplicatif` (7 rôles limitatifs) | § 4.1 |
| `actif` | Bool | — | § 4.1 |
| `debut_le` | DateTime | auto_now_add | § 5.2 |
| `fin_le` | DateTime | nullable | § 5.2 |
| `motif_affectation` | Char(255) | — | § 5.2 |

**Contrainte unique** : `(utilisateur, role) WHERE actif=True` → un utilisateur ne peut avoir deux affectations actives du même rôle. La réactivation après révocation reste possible (trace historique préservée).

**Signal `post_save`** : chaque création / modification d'affectation est tracée au journal d'audit avec `action_cle="affectation.creer"` ou `"affectation.mettre_a_jour"`.

**Rôles applicatifs limitatifs** (§ 4.1 TDR) :
`AGENT_SAISIE`, `AUTORITE_VALIDATION`, `ADMIN_FONCTIONNEL`, `ADMIN_TECHNIQUE`, `AUDITEUR`, `PROD_STATS`, `DECLARANT_EXTERNE`.

**Cumuls incompatibles** — `ROLES_INCOMPATIBLES` : `(AGENT_SAISIE, AUTORITE_VALIDATION)`. La règle § 4.1 opère au niveau de la DEMANDE (un utilisateur ne peut valider une demande qu'il a lui-même saisie), pas au niveau du compte.

---

### 2.5 `apps.referentiels` — Libellés bilingues

Cinq modèles — `LibelleNatureDroit`, `LibelleMotifRejet`, `LibelleCanalSaisie`, `LibelleCritereRecherche`, `LibelleTypeCertificat` — partageant la même structure.

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `cle` | Char(64) | **unique**, correspond EXACTEMENT à une valeur de l'enum limitative du décret | art. 76, 78, 80, 96 |
| `libelle_fr` | Char(255) | non vide au moins dans une des langues | § 6.3, 7.4 |
| `libelle_ar` | Char(255) | non vide au moins dans une des langues | § 6.3, 7.4 |
| `langue_faisant_foi` | Char(3) | Enum `LangueFaisantFoi` (fr, ar, equ) | § 7.4 |
| `description_fr` | Text | — | § 7.3 |
| `description_ar` | Text | — | § 7.3 |
| `actif` | Bool | désactivation logique possible | — |
| `ordre` | PositiveInt | ordre d'affichage | — |

**Invariant cardinal** : pour chaque modèle, l'ensemble des `cle` en base doit correspondre EXACTEMENT à l'énumération du décret. Vérifié par la commande `seed_referentiels` et par le test `test_couverture_exacte_des_enums`.

**Admin** : `EditionRestreinteAdmin` — libellés et descriptions modifiables par l'administrateur fonctionnel, `cle` en readonly, pas d'ajout ni de suppression.

---

### 2.6 `apps.parties` — Parties (PP / PM)

#### `Partie`

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `type_partie` | Char(2) | Enum `TypePartie` (`pp`, `pm`) | art. 85 |
| `nom` | Char(150) | — | art. 85 |
| `prenom` | Char(150) | — | art. 85 |
| `date_naissance` | Date | PP seulement | art. 85 |
| `lieu_naissance` | Char(150) | PP seulement | art. 85 |
| `denomination_sociale` | Char(255) | PM seulement | art. 85 |
| `numero_rc` | Char(64) | PM seulement, indexé (critère art. 96) | art. 85, 96 |
| `adresse` | Text | — | art. 85 |
| `adresse_electronique` | Email | facultative (art. 85 avant-dernier al.) | art. 85 |
| `telephone` | Char(32) | — | — |
| `cree_par`, `modifie_par` | FK → Utilisateur | PROTECT, non éditable | § 5.2 |
| `cree_le`, `modifie_le` | DateTime | auto | § 5.2 |

**Contraintes** :
- `pp_sans_denomination` (CheckConstraint SQL) : une personne physique ne peut porter `denomination_sociale`.
- Index sur `(nom, prenom)`, `(denomination_sociale)`, `(numero_rc)` — conformément à l'indexation requise par l'art. 93 et aux critères de recherche art. 96.

**Régime déclaratif** (art. 86) : aucun contrôle automatisé ne vérifie l'identité ou l'existence réelle des parties. Les champs sont stockés tels qu'énoncés.

**Zone d'arbitrage MO** : `L11/parties_reutilisation` — le modèle courant CRÉE une nouvelle `Partie` à chaque ajout via un diff de modification. L'option de référencer une partie existante est en attente d'arbitrage.

---

### 2.7 `apps.biens` — Biens grevés

#### `BienGreve` (validité temporelle)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `inscription` | FK → Inscription | PROTECT, related_name=`biens` | art. 85, 93 |
| `marque` | Char(128) | non bloquant (art. 85 al. 3) | art. 85 |
| `modele` | Char(128) | non bloquant | art. 85 |
| `annee` | PositiveInt | non bloquant | art. 85 |
| `numero_serie` | Char(128) | indexé (art. 93) | art. 93 |
| `description_fr` / `description_ar` | Text | bilingues | § 6.3 |
| `langue_faisant_foi_description` | Char(3) | § 7.4 | § 7.4 |
| `actif` | Bool | validité temporelle | art. 79 |
| `date_fin_validite` | DateTime | null | art. 79 |
| `raison_fin` | Char(255) | ex. `modification.demande#N` | art. 79 |
| `cree_par`, `modifie_par`, `cree_le`, `modifie_le` | — | audit technique | § 5.2 |

**Invariants** :
- `delete()` refusé (override ORM).
- Désactivation logique via modification contrôlée (cf. L3.2, flux de modification).
- Manager `actifs` expose uniquement `actif=True` — utilisé par la sérialisation canonique du fichier public.
- Manager `objects` expose l'historique complet — destiné à l'auditeur.

**Indexation** (art. 93) : sur `numero_serie`, sur `(marque, modele)`, sur `(inscription, actif)`.

---

### 2.8 `apps.inscriptions` — Cœur métier

#### `Inscription` (statuts § 4.3)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `id` | BigAuto | PK | — |
| `reference_demande` | UUID | unique, non éditable, visible dès la réception | art. 78 |
| `numero_ordre` | Char(64) | unique, nullable jusqu'à validation, format `NNNNNN-AAAAMMJJHHMMSS` | art. 78 al. 4 |
| `canal_saisie` | Char(32) | Enum `CanalSaisie` | art. 78 al. 1 |
| `instant_arrivee` | DateTime | indexé, ordre chronologique art. 78 al. 2 | art. 78 |
| `instant_saisie_opposable` | DateTime | nullable, indexé, prise d'effet art. 87 | art. 78 al. 3 / 87 |
| `statut` | Char(32) | Enum `StatutInscription`, indexé | § 4.3 |
| `mention_radiee` | Bool | — | art. 92 al. 2 |
| `fichier_actuel` | Char(16) | Enum `FichierRegistre` (`public`, `general`) | art. 77 |
| `nature_droit` | Char(48) | Enum `NaturesDroitInscrit` (12 valeurs art. 76) | art. 76, 85 |
| `somme_garantie` | Decimal(18,2) | nullable | art. 85 |
| `monnaie` | Char(8) | ISO 4217 | art. 85 |
| `duree_en_jours` | PositiveInt | non modifiable par une modification (art. 90 al. 2) | art. 85 |
| `date_expiration` | Date | nullable | art. 85, 91 |
| `requerant` | FK → Partie | PROTECT, nullable | art. 85 |
| `adresse_electronique_notifications` | Email | facultative | art. 85 |
| `motif_rejet` | Char(48) | Enum `MotifRejet`, seulement si REJETEE | art. 80 |
| `commentaire_rejet_fr` / `_ar` | Text | bilingues | § 7 |
| `instant_rejet` | DateTime | nullable | art. 80 |
| `cree_par`, `modifie_par` | FK → Utilisateur | PROTECT | § 5.2 |

**Invariants** :
- `numero_ordre` attribué UNE seule fois (transition `EN_CONTROLE_FORME → INSCRITE`). Jamais réutilisé (art. 78 al. 4, critère § 10.1).
- `instant_saisie_opposable` fixé à la validation (art. 87). Modifications ultérieures ne changent pas ce champ.
- `duree_en_jours` et `date_expiration` : non modifiables par `DemandeModification` (contrainte du schéma de diff, art. 90 al. 2). Modifiables uniquement par renouvellement (art. 91).
- `statut` : transitions limitées à la matrice `TRANSITIONS` + interdictions `INTERDICTIONS_EXPLICITES` (§ 4.3).

**Index** : sur `(statut, fichier_actuel)`, `instant_saisie_opposable`, `numero_ordre`, `date_expiration`.

#### `RoleInscriptionPartie` (validité temporelle)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `inscription` | FK → Inscription | PROTECT | art. 85 |
| `partie` | FK → Partie | PROTECT | art. 85 |
| `role` | Char(16) | Enum `RolePartie` (CONSTITUANT, CREANCIER, DEBITEUR, REQUERANT) | art. 85, 93 |
| `ordre` | PositiveInt | — | — |
| `actif` | Bool | — | art. 79 |
| `date_fin_validite`, `raison_fin` | — | validité temporelle | art. 79 |

**Contrainte unique conditionnée** : `(inscription, partie, role) WHERE actif=True` → permet la ré-attribution d'un rôle à une partie précédemment retirée lors d'une modification ultérieure.

**Invariant** : `delete()` refusé. Toute révocation passe par `actif=False` + `raison_fin`.

#### `PieceJointe`

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `inscription` | FK → Inscription | PROTECT | § 3.2 TDR |
| `nom_original` | Char(255) | — | — |
| `fichier` | File | stockage local, chemin `pieces_jointes/%Y/%m/` | — |
| `type_mime` | Char(128) | — | — |
| `taille_octets` | PositiveBigInt | — | — |
| `sceau_empreinte` | Char(128) | SHA-256 du contenu — **ZONE GELÉE** pour opposabilité | § 6.3 |

#### `SequenceNumeroOrdre` (singleton)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `pk` | AutoInt | forcé à 1 (ligne unique) | art. 78 |
| `prochaine_valeur` | PositiveBigInt | modifié uniquement via `attribuer_numero_ordre` | art. 78 |

**Invariants** :
- `save()` applicatif refusé sauf par le service d'attribution (flag interne `_force=True`).
- Accès sérialisé par `SELECT … FOR UPDATE` dans `attribuer_numero_ordre` (test de concurrence : 20 threads parallèles → 20 numéros contigus).
- `prochaine_valeur` ne décroît JAMAIS.

---

### 2.9 `apps.modifications` — Art. 88, 90, 93

#### `DemandeModification`

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `inscription` | FK → Inscription | PROTECT, rattachement art. 93 | art. 88, 93 |
| `objet_modification_fr` / `_ar` | Text | bilingues | § 7 |
| `diff_propose` | JSON | **schéma strict** `DiffModification` | art. 88 |
| `statut` | Char(16) | Enum `StatutDemandeModification` (RECUE, REJETEE, APPLIQUEE) | § 4.3 |
| `motif_refus_code` | Char(48) | Enum `MotifRefusModification` (8 motifs limitatifs) | art. 88, 80 |
| `motif_refus` | Char(255) | détail humain | — |
| `applique_le` | DateTime | nullable | art. 90 al. 1 |
| `accord_createur_confirme` / `accord_constituant_confirme` | Bool | art. 88, signatures GELÉES | art. 88 |

**Schéma strict du diff** — `apps.modifications.diff.DiffModification` :
```
{
  "parties": {
    "ajouter": [{"role": <RolePartie>, "type_partie": <TypePartie>,
                 "donnees": {... clés limitatives ...}}],
    "retirer": [<id RoleInscriptionPartie>, ...]
  },
  "biens": {
    "ajouter": [{... clés limitatives ...}],
    "retirer": [<id BienGreve>, ...]
  },
  "scalaires": {
    "nature_droit" | "somme_garantie" | "monnaie"
      | "adresse_electronique_notifications": <valeur>
  }
}
```

**Contrôle du diff (art. 88, 90 al. 2)** :
- Toute clé racine hors `{parties, biens, scalaires}` → refusée (`DIFF_INVALIDE`).
- Tout champ des scalaires hors `CHAMPS_SCALAIRES_MODIFIABLES` → refusé.
- Tout champ de `CHAMPS_JAMAIS_MODIFIABLES` (numéro d'ordre, horodatages, durée, date d'expiration, statut, etc.) → refusé.

**Contrôle d'état final (art. 88 dernier al.)** : après application dans le savepoint, vérification de ≥1 constituant, ≥1 créancier, ≥1 bien actifs. Échec → rollback du savepoint + marquage `REJETEE` avec `motif_refus_code`.

#### `SnapshotInscription` (append-only)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `inscription` | FK → Inscription | PROTECT | art. 79 |
| `evenement` | Char(48) | Enum `Evenement` (8 événements : validation, modification avant/après, renouvellement avant/après, radiation avant/après, demande reçue) | art. 79 |
| `demande_modification` | FK → DemandeModification | PROTECT, nullable | — |
| `instant` | DateTime | indexé | § 5.2 |
| `contenu` | JSON | sérialisation canonique (clés triées, champs bilingues en paire fr/ar) | § 6.3 |
| `empreinte` | Char(128) | SHA-256 canonique — **STUB** pour opposabilité (§ 5.1 zone gelée) | § 6.3 |
| `acteur` | FK → Utilisateur | PROTECT, nullable | § 5.2 |

**Invariants** : `save()` si `pk`, `delete()` refusés.

---

### 2.10 `apps.renouvellements` — Art. 91

#### `DemandeRenouvellement`

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `inscription` | FK → Inscription | PROTECT | art. 91 |
| `statut` | Char(16) | Enum (RECUE, REJETEE, APPLIQUEE) | art. 91 |
| `motif_refus` | Char(255) | — | — |
| `ancienne_date_expiration` / `nouvelle_date_expiration` | Date | nullable | art. 91 |
| `applique_le` | DateTime | nullable | — |

**Règle art. 91** (hypothèse A3 — durée initiale = durée fixée à l'inscription, non pas à un renouvellement antérieur) : `nouvelle_date_expiration = ancienne_date_expiration + inscription.duree_en_jours`.

---

### 2.11 `apps.radiations` — Art. 92

#### `DemandeRadiation`

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `inscription` | FK → Inscription | PROTECT | art. 92 |
| `fondement` | Char(32) | Enum `FondementRadiation` (consentement, jugement, requérant initial) | art. 92 |
| `statut` | Char(16) | Enum | — |
| `nom_constituant`, `prenom_constituant`, `denomination_constituant`, `adresse_constituant`, `numero_rc_constituant` | — | contenu art. 92 al. 1 | art. 92 |

**Effet** : transition `INSCRITE/MODIFIEE/RENOUVELEE → RADIEE` + activation de `Inscription.mention_radiee`.
**Transfert au fichier général** : déclenché par `python manage.py expirer_inscriptions` à l'échéance (art. 92 al. 3).

---

### 2.12 `apps.certificats` — **ZONE GELÉE pour probant**

#### `Certificat`

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `type_certificat` | Char(32) | Enum `TypeCertificat` (5 valeurs) | art. 78, 86, 88-92, 97 |
| `inscription` | FK → Inscription | PROTECT, nullable | — |
| `requete_recherche` | FK → RequeteRecherche | PROTECT, nullable | art. 97 |
| `langue_generation` | Char(4) | `fr`, `ar`, `fr-ar` | § 7.5 |
| `probant` | Bool | **toujours False** tant que scellement et horodatage ne sont pas arbitrés | art. 97 dernier al. |
| `empreinte` | Char(128) | SHA-256 STUB | § 6.3 |
| `contenu_json` | JSON | source canonique bilingue | § 6.3 |
| `fichier_pdf` | File | GELÉ — pas de génération PDF/A à ce stade | § 7.5 |

---

### 2.13 `apps.statistiques` — Art. 82

#### `ExtractionStatistique` (append-only)

| Champ | Type | Contraintes | Article |
|-------|------|-------------|---------|
| `instant` | DateTime | auto_now_add | § 5.2 |
| `producteur` | FK → Utilisateur | PROTECT — doit avoir le rôle `PROD_STATS` | art. 82 |
| `perimetre` | JSON | critères d'agrégation | — |
| `resultat` | JSON | agrégats | — |

**Monopole art. 82** : vérifié par `apps.utilisateurs.habilitations.peut_produire_statistiques`.

---

## 3. Règles transverses d'intégrité

### 3.1 Immutabilité horodatage et numéro d'ordre (art. 78)

- `Inscription.numero_ordre` : une fois attribué, immuable (ne figure pas dans `CHAMPS_SCALAIRES_MODIFIABLES`).
- `Inscription.instant_saisie_opposable`, `instant_arrivee` : immuables.
- `SequenceNumeroOrdre.prochaine_valeur` : uniquement incrémentée par le service d'attribution, jamais décrémentée.

### 3.2 Conservation (art. 79)

- Toutes les entités append-only : override `delete()` + (pour le journal) triggers PostgreSQL.
- Toutes les entités à validité temporelle : override `delete()` + révocation logique `actif=False`.
- Aucune migration ne doit supprimer de donnée métier.

### 3.3 Bilinguisme (§ 6.3, § 7)

- Tout champ descriptif multilingue : paire `*_fr` / `*_ar` + `langue_faisant_foi`.
- Tout champ neutre linguistiquement : une seule colonne.
- Aucun libellé de référentiel n'existe dans une seule langue sans mention explicite de la langue faisant foi.
- Les énumérations limitatives du décret (natures art. 76, motifs art. 80, canaux art. 78, critères art. 96, types de certificats) sont stockées par CLÉ NEUTRE dans la base ; les libellés FR/AR sont résolus au moment de l'affichage via les référentiels.

### 3.4 Défense en profondeur

Quatre couches garantissant les invariants :

1. **PostgreSQL** — triggers `rsm_audit_interdire_mutation` sur le journal d'audit.
2. **ORM** — overrides `save()` / `delete()` sur entités append-only et à validité temporelle.
3. **DRF** — handler d'exceptions `rsm_exception_handler` traduisant `ErreurMetierRSM` en 400, `AutorisationRefusee` et `PermissionError` en 403.
4. **Admin Django** — classes de base `LectureSeuleAdmin`, `ConsultationMetierAdmin`, `EditionRestreinteAdmin` (cf. L3.2).

---

## 4. Renvois croisés

- Traçabilité article par article : [L11](L11_tracabilite_articles_76_97.md).
- Architecture modulaire : [L3.2](L3_2_architecture_modulaire.md).
- Politique d'horodatage et de scellement : [L3.3](L3_3_horodatage_scellement.md).
- Code source :
  - Énumérations : [apps/core/enums.py](../backend/apps/core/enums.py).
  - Statuts et matrice : [apps/workflow/statuts.py](../backend/apps/workflow/statuts.py).
  - Mixins bilingues et validité temporelle : [apps/core/models.py](../backend/apps/core/models.py), [apps/core/mixins.py](../backend/apps/core/mixins.py).
  - Schéma strict des diffs : [apps/modifications/diff.py](../backend/apps/modifications/diff.py).
