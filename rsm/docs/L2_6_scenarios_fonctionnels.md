# L2.6 — Scénarios fonctionnels de bout en bout

**Livrable** : L2.6 — partie du livrable L2 (§ 8 du TDR).
**Objet** : huit scénarios de référence déroulés pas à pas, opposables
au MO et au greffe, montrant l'application concrète des règles du
décret et du TDR.
**Fondement** : articles 76 à 97 ; TDR § 4.
**État** : consolidation. **Aucune règle nouvelle.**

---

## 1. Conventions de lecture

Chaque scénario est décrit selon la structure suivante :

- **Acteurs** — rôles applicatifs et comptes utilisés.
- **Préconditions** — état initial du système.
- **Étapes** — actions séquentielles numérotées.
- **Contrôles** — règles appliquées à chaque étape (référence L2.2).
- **Postconditions** — état final observable.
- **Audit** — entrées significatives enregistrées.
- **Zones gelées applicables** — rappels L11.

Les identifiants d'événement, clés neutres, codes HTTP et messages
référencés renvoient aux catalogues L2.2, L2.3, L2.5.

---

## 2. Scénario A — Dépôt guichet papier et validation complète

**Fondement** : articles 78, 85, 86, 87.
**Résultat** : inscription publiée au fichier public.

### 2.1 Acteurs

- **Aïssata — Agent de saisie** (`agent_saisie`)
- **Mohamed — Autorité de validation / Greffier** (`autorite_validation`)
- **Société commerciale SARL Alpha** (constituant, personne morale)
- **Banque Bravo** (créancier garanti)
- **M. Cheikh** (débiteur, personne physique)

### 2.2 Préconditions

- Aïssata et Mohamed ont des comptes actifs avec leurs rôles respectifs.
- Les référentiels bilingues FR/AR sont chargés (`seed_referentiels`).
- Le bordereau papier est reçu au guichet ; il est complet au regard de l'article 85.

### 2.3 Étapes

| # | Acteur | Action | Endpoint | Règle | Effet |
|:-:|--------|--------|----------|-------|-------|
| 1 | Aïssata | Saisie du bordereau au guichet | `POST /api/v1/inscriptions/` | A-78.1 (canal), A-76.1 (nature), B-85.* | `Inscription` créée, statut `RECUE` |
| 2 | Système | Transition automatique | — | § 4.3 T1 | Statut → `EN_CONTROLE_FORME` ; audit `transition.prise_en_charge` |
| 3 | Aïssata | Peuplement des parties (constituant, créancier, débiteur) et des biens | Services + ORM (UI à câbler — Option B GELÉE) | B-85.* | 3 `RoleInscriptionPartie` + au moins 1 `BienGreve` (actifs) |
| 4 | Mohamed | Décision de validation | `POST /api/v1/inscriptions/<uuid>/valider/` | F-4.1.1 (saisie ≠ validation) ; A-78.1 ; B-85.* | Numéro d'ordre attribué ; `instant_saisie_opposable` posé ; `date_expiration = instant + duree_en_jours` ; statut → `INSCRITE` ; audit `inscription.valider` + `transition.validation_greffier` |
| 5 | Système | Ajout au fichier public | — | Art. 77 | `fichier_actuel = "public"` |
| 6 | Système | Préparation d'un certificat d'inscription (structurel) | `preparer_certificat(type="inscription", probant=False)` | Art. 78 al. 3 + L11/A5 | `Certificat` créé avec `probant=False` + avertissement `zone_gelee.certificat_probant.inactif` |

### 2.4 Messages système émis

| Étape | Clé neutre | Émetteur |
|:-----:|------------|----------|
| 1 | `inscription.depot.succes` | API |
| 4 | `inscription.validation.succes` | API |
| 4 | `workflow.transition.validation_greffier` | Journal + UI |
| 6 | `zone_gelee.certificat_probant.inactif` | Warning système |

### 2.5 Postconditions

- Inscription visible au fichier public avec numéro d'ordre stable.
- `Partie` + `BienGreve` + `RoleInscriptionPartie` persistés (actifs).
- Journal d'audit complet : 4 à 6 entrées selon les actions (cf. L3.5 § 9).
- Une notification externe au déposant EST ATTENDUE mais **non émise**
  (zone `L11/interconnexions`).

### 2.6 Zones gelées applicables

- `L11/horodatage` — `instant_saisie_opposable` non opposable en STUB.
- `L11/A5` — certificat d'inscription non probant.
- `L11/A7` — aucun contrôle de paiement des émoluments.
- `L11/interconnexions` — aucune notification externe.

---

## 3. Scénario B — Dépôt électronique avec rejet art. 80

**Fondement** : articles 78, 80, 86.
**Résultat** : inscription `REJETEE` avec motif limitatif, tracée au journal.

### 3.1 Acteurs

- **Déclarant externe** (`declarant_externe`) : société Delta SA.
- **Mohamed — Greffier** (`autorite_validation`).

### 3.2 Préconditions

- Le déclarant est authentifié sur le portail (⚠️ `L11/MFA` en mode
  session Django pour le moment).
- Le document soumis est partiellement illisible suite à une mauvaise
  numérisation.

### 3.3 Étapes

| # | Acteur | Action | Endpoint | Règle | Effet |
|:-:|--------|--------|----------|-------|-------|
| 1 | Déclarant | Soumission du bordereau | `POST /api/v1/inscriptions/` | A-78.1 (`portail_electronique`) ; A-76.1 | `Inscription` créée, statut `RECUE` |
| 2 | Système | Transition automatique | — | § 4.3 T1 | Statut → `EN_CONTROLE_FORME` |
| 3 | Mohamed | Contrôle de forme : document illisible | — | Art. 80 (motif `informations_illisibles`) | Préparation du rejet |
| 4 | Mohamed | Prononcé du rejet | `POST /api/v1/inscriptions/<uuid>/rejeter/` avec `motif="informations_illisibles"` | A-80.1 ; F-4.1.1 ; art. 86 (contrôle de forme uniquement) | Statut → `REJETEE` ; `motif_rejet` figé ; `instant_rejet` posé ; commentaires FR/AR conservés ; audit `inscription.rejeter` + `transition.rejet_art80` |
| 5 | Système | L'inscription **n'est pas** publiée au fichier public | — | Art. 77 + § 4.3 | `REJETEE ∉ STATUTS_FICHIER_PUBLIC` |

### 3.4 Variante — Motif hors liste

Si Mohamed tente de soumettre un motif hors `MotifRejet` :
- Réponse HTTP 400 avec `article="80"`, `classe="RejetForme"`, clé
  `rejet.art80.motif_hors_liste`.
- Aucune modification de l'inscription.
- L'inscription reste à `EN_CONTROLE_FORME`.

### 3.5 Variante — Canal de soumission invalide

Si le payload contient `canal_saisie="postal"` (hors liste) au dépôt :
- Refus dès l'étape 1 avec clé `rejet.art80.canal_non_autorise`.
- Aucune inscription créée.

### 3.6 Postconditions

- `Inscription` conservée en base (art. 79) avec `statut=REJETEE`.
- Journal d'audit contient `inscription.deposer` + `transition.prise_en_charge`
  + `inscription.rejeter` + `transition.rejet_art80`.
- Notification du rejet **GELÉE** (`L11/interconnexions`).

---

## 4. Scénario C — Modification contrôlée réussie

**Fondement** : articles 88, 90 al. 2, 93.
**Résultat** : inscription mutée vers `MODIFIEE` avec snapshots avant/après.

### 4.1 Acteurs

- **Aïssata** (agent de saisie) soumet la demande de modification.
- **Mohamed** (greffier) applique la modification.

### 4.2 Préconditions

- Inscription active (issue du scénario A), statut `INSCRITE`.
- Un nouveau bien doit être ajouté.
- Les accords du créancier et du constituant sont confirmés (art. 88).

### 4.3 Étapes

| # | Acteur | Action | Endpoint | Règle | Effet |
|:-:|--------|--------|----------|-------|-------|
| 1 | Aïssata | Création de la demande | `POST /api/v1/modifications/` avec diff `{"biens": {"ajouter": [{...}]}}` et `accord_*=true` | A-88.1 (schéma strict) | `DemandeModification` statut `RECUE` |
| 2 | Mohamed | Application | `POST /api/v1/modifications/<id>/appliquer/` | F-4.1.1 ; B-88.2 ; A-88.1 ; E-88.3 | Séquence en 9 étapes : voir ci-dessous |

**Détail de l'application (service `appliquer_modification`)** :

1. Recevabilité : statut demande `RECUE`, inscription en cours, accords confirmés, séparation stricte.
2. Validation du diff : schéma strict, nature ∈ liste limitative, scalaires autorisés.
3. Ouverture d'un savepoint.
4. Snapshot `MODIFICATION_AVANT` produit.
5. Application des mutations (retraits, ajouts, scalaires).
6. Refresh BD.
7. Contrôle d'état final (`_verifier_etat_final`) : ≥ 1 constituant actif, ≥ 1 créancier actif, ≥ 1 bien actif → OK.
8. Snapshot `MODIFICATION_APRES` produit.
9. Transition `INSCRITE → MODIFIEE` ; demande `APPLIQUEE` ; audit `modification.appliquer` + `transition.modification_art88`.

### 4.4 Postconditions

- Inscription : statut `MODIFIEE` ; nouveau bien actif ; **durée inchangée** (art. 90 al. 2) ; **numéro d'ordre inchangé** (art. 78).
- 2 `SnapshotInscription` produits (AVANT + APRÈS) avec empreintes
  SHA-256 distinctes (en STUB tant que `L11/A5` non arbitré).
- Demande `APPLIQUEE` immuable.

### 4.5 Messages système

| Étape | Clé neutre |
|:-----:|------------|
| 1 | `modification.depot.succes` |
| 2 | `modification.application.succes` |
| 2 | `workflow.transition.modification_art88` |

### 4.6 Zones gelées applicables

- `L11/A2` — signature électronique : les flags `accord_*_confirme`
  sont contrôlés mais la vérification cryptographique est GELÉE.
- `L11/A5` — snapshots scellés en STUB.
- `L11/horodatage` — `applique_le` non opposable.
- `L11/parties_reutilisation` — s'il s'agissait d'ajouter une partie
  existante, celle-ci serait **recréée** (conservatisme).

---

## 5. Scénario D — Modification refusée art. 88 dernier alinéa

**Fondement** : article 88 dernier alinéa, § 4.3 TDR.
**Résultat** : demande `REJETEE` avec motif structuré, rollback complet, aucune altération de l'inscription.

### 5.1 Acteurs

- **Aïssata** crée une demande qui retirerait l'unique constituant sans en ajouter.
- **Mohamed** tente l'application.

### 5.2 Préconditions

- Inscription `INSCRITE` avec exactement 1 constituant actif.
- Accords des parties confirmés.

### 5.3 Étapes

| # | Acteur | Action | Endpoint | Règle | Effet |
|:-:|--------|--------|----------|-------|-------|
| 1 | Aïssata | Création de la demande | `POST /api/v1/modifications/` avec diff `{"parties": {"retirer": [<id_lien>]}}` | A-88.1 (schéma strict OK — le diff est syntaxiquement valide) | `DemandeModification` `RECUE` |
| 2 | Mohamed | Tentative d'application | `POST /api/v1/modifications/<id>/appliquer/` | E-88.3 | Rejet structuré |

**Détail de l'application** :

1. Recevabilité OK, schéma OK.
2. Savepoint ouvert.
3. Snapshot `MODIFICATION_AVANT` produit.
4. Retrait du rôle de constituant (désactivation).
5. Refresh BD.
6. `_verifier_etat_final` détecte 0 constituant actif → lève `EtatFinalInvalide(motif_code=ETAT_FINAL_CONSTITUANT_ABSENT)`.
7. `savepoint_rollback(sid)` — snapshot et désactivation annulés.
8. `_marquer_rejet()` : demande `REJETEE` + `motif_refus_code` + audit `modification.refuser`.
9. Exception `ModificationSansEffet` → HTTP 400, `article="88"`, `classe="ModificationSansEffet"`.

### 5.4 Postconditions

- **Inscription strictement inchangée** : constituant toujours actif,
  statut toujours `INSCRITE`.
- Demande `REJETEE` avec `motif_refus_code="etat_final_constituant_absent"`.
- **Zéro snapshot orphelin** en base (testé par `test_api_d2_rejet_art88.py`).
- Audit : `modification.refuser` avec `motif_code` structuré.
- **Tentative de ré-application** : refusée avec motif `DEMANDE_NON_APPLICABLE`.

### 5.5 Garantie anti-contournement

Une succession de demandes retirant progressivement des parties ou
des biens ne peut **jamais** aboutir à un état invalide : le contrôle
est appliqué sur l'ÉTAT FINAL, pas sur le diff isolé (L2.2 règle E-88.3).

**Testé** : [test_modifications_cas_limites.py::AntiContournementParSuccessionTests](../backend/tests/test_modifications_cas_limites.py).

### 5.6 Messages système

| Clé neutre | Contexte |
|------------|----------|
| `etat_final_constituant_absent` | Corps de la réponse HTTP 400 |
| `zone_gelee.scellement.stub` | Warning de rollback du scellement des snapshots |

---

## 6. Scénario E — Renouvellement avant et après expiration

**Fondement** : article 91, hypothèse A3.

### 6.1 Variante E.1 — Renouvellement valide

| Préconditions | Inscription active, `date_expiration > aujourd'hui`, durée initiale 365 jours. |
|---------------|------|

| # | Acteur | Action | Endpoint | Règle | Effet |
|:-:|--------|--------|----------|-------|-------|
| 1 | Aïssata | Création demande | `POST /api/v1/renouvellements/` | — | `DemandeRenouvellement` `RECUE` |
| 2 | Mohamed | Application | `POST /api/v1/renouvellements/<id>/appliquer/` | D-91.1 ; D-91.2 ; F-4.1.1 | `nouvelle_date_expiration = ancienne + duree_en_jours` ; statut → `RENOUVELEE` ; audit |

### 6.2 Variante E.2 — Renouvellement hors délai

| Préconditions | Inscription à `date_expiration ≤ aujourd'hui` (par ex. rétrodatée dans un scénario de test). |

| # | Acteur | Action | Règle | Effet |
|:-:|--------|--------|-------|-------|
| 1 | Aïssata | Création demande | — | `DemandeRenouvellement` `RECUE` |
| 2 | Mohamed | Tentative d'application | D-91.1 | HTTP 400 ; `classe="RenouvellementHorsDelai"` ; `article="91"` ; clé `renouvellement.refus.hors_delai` |

Dans la variante E.2, l'inscription reste **inchangée**. Si sa date
d'expiration est atteinte, une commande `expirer_inscriptions`
ultérieure la fera passer à `EXPIREE` puis `ARCHIVEE` — cf. scénario H.

### 6.3 Hypothèse A3

« Durée initiale » s'entend comme la durée fixée à l'inscription
initiale, NON comme la durée résultant d'un renouvellement antérieur.
Décision adoptée par défaut, en attente d'arbitrage MO formel. Un
deuxième renouvellement appliqué produirait donc :

```
nouvelle_expiration_2 = expiration_apres_1er_renouv + duree_en_jours_initiale
```

---

## 7. Scénario F — Radiation

### 7.1 Variante F.1 — Radiation par consentement

**Fondement** : article 92 alinéa 1 (consentement), alinéa 2 (mention
« radiée »), alinéa 3 (transfert futur au fichier général).

| Acteurs | Aïssata (agent), Mohamed (greffier), constituant SARL Alpha (consent). |
|---------|------|

| # | Acteur | Action | Endpoint | Règle | Effet |
|:-:|--------|--------|----------|-------|-------|
| 1 | Aïssata | Création demande avec `fondement="consentement"` et pièce jointe (acte sous seing privé) | `POST /api/v1/radiations/` | A-92.2 ; B-92.1 | `DemandeRadiation` + `PieceJointe` |
| 2 | Mohamed | Application | `POST /api/v1/radiations/<id>/appliquer/` | F-4.1.1 | Transition `INSCRITE → RADIEE` ; `mention_radiee=True` ; audit |
| 3 | Système | L'inscription reste au fichier public avec la mention | — | E-92.3 (art. 92 al. 2) | `fichier_actuel="public"` conservé, `mention_radiee=True` |

### 7.2 Variante F.2 — Radiation par jugement

Identique à F.1 mais :
- `fondement="jugement"` ;
- Pièce jointe : copie du jugement reconnaissant l'intérêt légitime.
- ⚠️ Zone gelée `L11/A5` partielle : le scellement opposable de la
  pièce jointe reste en STUB.

### 7.3 Postconditions communes

- Inscription `RADIEE`, visible au fichier public jusqu'à expiration.
- Une recherche par numéro d'inscription retrouve l'inscription avec
  `mention_radiee=True` (art. 92 al. 2).
- Tests : [tests/test_api_s4_recherche_coherence.py::test_inscription_radiee_visible_au_fichier_public](../backend/tests/test_api_s4_recherche_coherence.py).

---

## 8. Scénario G — Recherche publique avec homonymes (art. 97 al. 2)

**Fondement** : articles 94, 95, 96, 97 al. 2.

### 8.1 Acteurs

- **Khadija — Usager public anonyme**. Pas d'authentification requise
  (art. 94 — « ouverture à tout intéressé »).

### 8.2 Préconditions

- Plusieurs inscriptions au fichier public mentionnent un constituant
  au nom « DUPONT » (un Pierre DUPONT, un Paul DUPONT — homonymes).

### 8.3 Étapes

| # | Acteur | Action | Endpoint | Règle | Effet |
|:-:|--------|--------|----------|-------|-------|
| 1 | Khadija | Recherche par `nom_constituant="DUPONT"` et `numero_rc="RC/NKT/2024/X"` | `POST /api/v1/recherche/` | A-96.1 ; B-96.2 (2 critères) ; F-94.1 (public) | Deux inscriptions rattachables |
| 2 | Système | Filtrage fichier public | — | Art. 77 | Inscriptions `STATUTS_FICHIER_PUBLIC` uniquement |
| 3 | Système | Collecte des homonymes | — | B-97.1 (art. 97 al. 2) | Pour chaque inscription, tous les constituants portant le nom « DUPONT » sont retournés avec prénom, adresse, date de naissance |
| 4 | Système | Persistance `RequeteRecherche` | — | § 5.2 | Append-only + audit `recherche.lancer` |
| 5 | Système | Préparation d'un certificat de recherche | — | Art. 97 al. 3 + L11/A5 | `Certificat(type="recherche", probant=False)` + avertissement |

### 8.4 Variante G.2 — Un seul critère

Si Khadija renseigne un seul critère :
- HTTP 400, `classe="RechercheCriteresInsuffisants"`, `article="96"`.
- Clé `recherche.refus.criteres_insuffisants`.

### 8.5 Variante G.3 — Clé hors liste

Si Khadija ajoute un critère `nom_creancier` (hors liste limitative
art. 96) :
- HTTP 400, champ `non_autorises` dans la réponse.
- Clé `recherche.refus.critere_hors_liste`.

### 8.6 Postconditions

- Résultat délivré avec `avertissement` « aperçu non opposable »
  (certificat probant GELÉ — `L11/A5`).
- Requête tracée au journal.
- Les inscriptions radiées mais non encore expirées apparaissent avec
  `mention_radiee=True` (art. 92 al. 2).
- Les inscriptions archivées (fichier général) **n'apparaissent pas**
  (art. 92 al. 3).

### 8.7 Zones gelées applicables

- `L11/A5` — certificat de recherche probant.
- `L11/horodatage` — instant de la recherche en STUB.

---

## 9. Scénario H — Expiration automatique et archivage

**Fondement** : articles 77, 79, 85, 92 al. 3, § 4.3 TDR.

### 9.1 Acteurs

- **Système** (acteur `null`).
- Les transitions sont automatiques, déclenchées par la commande
  `python manage.py expirer_inscriptions` planifiée quotidiennement.

### 9.2 Préconditions

- Ensemble d'inscriptions aux statuts `INSCRITE`, `MODIFIEE`,
  `RENOUVELEE`, ou `RADIEE` dont la `date_expiration ≤ aujourd'hui`.

### 9.3 Étapes (pour chaque inscription concernée)

| # | Acteur | Action | Règle | Effet |
|:-:|--------|--------|-------|-------|
| 1 | Système | Détection (date d'expiration atteinte) | D-92.4 | Sélection |
| 2 | Système | Transition `T12/13/14/15` | § 4.3 (automatique) | Statut → `EXPIREE` ; audit `transition.expiration_automatique` |
| 3 | Système | Transition `T16` | § 4.3 (automatique) ; art. 79, 92 al. 3 | Statut → `ARCHIVEE` ; `fichier_actuel="general"` ; audit `transition.transfert_fichier_general` |
| 4 | Système | Audit de synthèse | § 5.2 | `inscription.expirer_archiver` |

### 9.4 Postconditions

- Inscription conservée pérenne (art. 79).
- **Sortie du fichier public** : les recherches art. 94-97
  n'identifient plus cette inscription (filtrage sur
  `STATUTS_FICHIER_PUBLIC`).
- Disponible à l'auditeur (lecture seule) via `/api/v1/audit/entrees/`
  et (à câbler) la consultation des snapshots.
- Historique complet préservé :
  - `TransitionStatut` pour chaque transition ;
  - `SnapshotInscription` (si produits) conservés ;
  - `BienGreve` et `RoleInscriptionPartie` toujours présents avec
    leur état `actif` / `date_fin_validite`.

### 9.5 Tests

- [tests/test_api_s4_recherche_coherence.py::test_inscription_archivee_invisible_au_fichier_public](../backend/tests/test_api_s4_recherche_coherence.py).
- [tests/test_api_s1_cycle_nominal.py](../backend/tests/test_api_s1_cycle_nominal.py) — la 7e étape du cycle nominal teste l'expiration + archivage.

### 9.6 Zones gelées applicables

- `L11/horodatage` — la détection de « date atteinte » s'appuie sur
  l'horloge locale ; non opposable en STUB.

---

## 10. Matrice des 8 scénarios × règles appliquées

| Règle (L2.2) | A | B | C | D | E.1 | E.2 | F | G | H |
|--------------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| A-76.1 Nature limitative | ✅ | ✅ | — | — | — | — | — | — | — |
| A-78.1 Canal limitatif | ✅ | ✅ | — | — | — | — | — | — | — |
| C-78.2 Format n° d'ordre | ✅ | — | — | — | — | — | — | — | — |
| E-78.4 Immutabilité n° / horodatage | — | — | ✅ | ✅ | — | — | — | — | — |
| G-79.1 Conservation pérenne | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A-80.1 Motifs limitatifs rejet | — | ✅ | — | — | — | — | — | — | — |
| F-82.1 Monopole statistiques | — | — | — | — | — | — | — | — | — |
| B-85.* Contenu obligatoire | ✅ | ✅ | — | — | — | — | — | — | — |
| art. 86 Régime déclaratif | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| G-87.1 Prise d'effet à la saisie | ✅ | — | — | — | — | — | — | — | — |
| A-88.1 Schéma strict diff | — | — | ✅ | ✅ | — | — | — | — | — |
| B-88.2 Accords art. 88 | — | — | ✅ | ✅ | — | — | — | — | — |
| E-88.3 État final | — | — | ✅ | ✅ | — | — | — | — | — |
| E-90.1 Durée non modifiable | — | — | ✅ | — | — | — | — | — | — |
| D-91.1 Avant expiration | — | — | — | — | ✅ | ✅ | — | — | — |
| D-91.2 Durée initiale | — | — | — | — | ✅ | — | — | — | — |
| A-92.2 Fondement radiation | — | — | — | — | — | — | ✅ | — | — |
| E-92.3 Mention radiée | — | — | — | — | — | — | ✅ | — | — |
| D-92.4 Transfert fichier général | — | — | — | — | — | — | — | — | ✅ |
| G-93.* Indexation | — | — | — | — | — | — | — | ✅ | — |
| F-94.1 Ouverture publique | — | — | — | — | — | — | — | ✅ | — |
| B-96.2 Deux critères | — | — | — | — | — | — | — | ✅ | — |
| B-97.1 Homonymes | — | — | — | — | — | — | — | ✅ | — |
| F-4.1.1 Séparation stricte | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| A-global.1 Serializers stricts | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |

---

## 11. Matrice des zones gelées par scénario

| Zone gelée (L11) | A | B | C | D | E | F | G | H |
|------------------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `L11/horodatage` | ✅ | — | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| `L11/A2` (signature) | — | — | ✅ | ✅ | — | — | — | — |
| `L11/A5` (certificat probant, scellement) | ✅ | — | ✅ | ✅ | — | ✅ | ✅ | — |
| `L11/A7` (paiement) | ✅ | ✅ | — | — | — | — | — | — |
| `L11/MFA` | — | ✅ | — | — | — | — | — | — |
| `L11/interconnexions` (notifications) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | — |
| `L11/parties_reutilisation` | — | — | ✅ | ✅ | — | — | — | — |
| `L11/A6` (glossaire § 7.3) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 12. Correspondance scénarios × tests existants

| Scénario | Test(s) d'intégration de référence |
|----------|------------------------------------|
| A | [test_api_s1_cycle_nominal.py](../backend/tests/test_api_s1_cycle_nominal.py) |
| B | [test_api_s2_rejet_art80.py](../backend/tests/test_api_s2_rejet_art80.py) |
| C | [test_modifications.py::AppliquerModificationTests](../backend/tests/test_modifications.py) + scénarios S1 |
| D | [test_api_d2_rejet_art88.py](../backend/tests/test_api_d2_rejet_art88.py) + [test_modifications_cas_limites.py](../backend/tests/test_modifications_cas_limites.py) |
| E.1 | [test_regles_metier.py::test_renouvellement_proroge_de_duree_initiale](../backend/tests/test_regles_metier.py) |
| E.2 | [test_api_s3_transitions_interdites.py::test_renouvellement_apres_expiration_refuse](../backend/tests/test_api_s3_transitions_interdites.py) |
| F | [test_api_s4_recherche_coherence.py::test_inscription_radiee_visible_au_fichier_public](../backend/tests/test_api_s4_recherche_coherence.py) |
| G | [test_api_s4_recherche_coherence.py](../backend/tests/test_api_s4_recherche_coherence.py) (toute la classe) |
| H | [test_api_s4_recherche_coherence.py::test_inscription_archivee_invisible_au_fichier_public](../backend/tests/test_api_s4_recherche_coherence.py) |

Transversal :
- Séparation stricte HTTP sur tous les scénarios avec validation :
  [test_api_d1_separation_stricte.py](../backend/tests/test_api_d1_separation_stricte.py).
- Équivalence FR/AR sur tous les scénarios :
  [test_api_d3_accept_language.py](../backend/tests/test_api_d3_accept_language.py).

---

## 13. Principes opposables résultant des 8 scénarios

Des 8 scénarios ci-dessus, se dégagent les principes opposables du
système RSM, cohérents avec le décret et le TDR :

1. **L'ordre d'arrivée est opposable** : l'`instant_arrivee` est posé dès la réception, inchangé (art. 78 al. 2).
2. **Le numéro d'ordre est immuable** : attribué à la validation et jamais modifié (art. 78 al. 4).
3. **Le régime déclaratif est préservé** : aucun scénario n'introduit de contrôle au fond (art. 86).
4. **La séparation des pouvoirs est garantie** : aucun scénario ne permet à un même acteur de saisir et valider la même demande (§ 4.1).
5. **Toute action est tracée** : les 8 scénarios produisent au moins une entrée au journal d'audit (§ 5.2).
6. **Les refus sont structurés** : chaque rejet ou refus porte un motif appartenant à une enum limitative (art. 80, art. 88 dernier al., § 4.3).
7. **Le fichier public reflète la réalité juridique** : une inscription radiée y demeure jusqu'à expiration, puis en sort (art. 92 al. 2 et al. 3).
8. **Toute donnée est conservée** : aucun scénario ne supprime quoi que ce soit ; les désactivations conservent la trace (art. 79).
9. **Le bilinguisme produit les mêmes effets** : quel que soit le scénario, les clés neutres opposables sont identiques FR/AR (§ 7.3).

---

## 14. Renvois croisés

- Formulaires : [L2.1](L2_1_formulaires_bilingues.md).
- Règles de validation : [L2.2](L2_2_regles_validation.md).
- Statuts × transitions : [L2.3](L2_3_matrice_statuts_transitions.md).
- Rôles × opérations : [L2.4](L2_4_roles_operations.md).
- Messages système : [L2.5](L2_5_messages_systeme.md).
- Architecture et flux : [L3.2](L3_2_architecture_modulaire.md) § 4.
- Sécurité et intégrité : [L3.5](L3_5_securite_integrite.md).
- Bilinguisme : [L3.6](L3_6_matrice_bilingue.md).
- Traçabilité article par article : [L11](L11_tracabilite_articles_76_97.md).
