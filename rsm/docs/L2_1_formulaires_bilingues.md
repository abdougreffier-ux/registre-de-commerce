# L2.1 — Formulaires bilingues

**Livrable** : L2.1 — partie du livrable L2 (§ 8 du TDR).
**Objet** : spécification fonctionnelle des bordereaux et formulaires
prévus par le décret 2021-033. **Pas d'interface utilisateur** —
description du contenu opposable uniquement.
**Fondement** : articles 80, 85, 88, 91, 92, 96, 97 du décret ; TDR § 7
(bilinguisme).
**État** : spécifications consolidant l'existant. **Aucune règle nouvelle.**

---

## 1. Principes communs aux six formulaires

### 1.1 Bilinguisme par formulaire (§ 7)

| Type de champ | Présentation | Stockage |
|---------------|--------------|----------|
| Neutre linguistiquement | Saisi une seule fois, restitué à l'identique FR/AR | Colonne unique |
| Bilingue | Paire FR + AR saisie côte à côte | Colonnes `*_fr` + `*_ar` + `langue_faisant_foi` |
| Choisi dans une liste limitative | Affichage du libellé résolu selon la langue active | Clé neutre en base |

**Règle** : aucun formulaire ne demande à l'utilisateur de choisir une
langue pour saisir un champ juridiquement neutre. La langue d'interface
est indépendante de la langue des données stockées.

### 1.2 Canaux d'arrivée (art. 78)

Tout formulaire est admis par l'un des **deux canaux limitatifs** :

- **Guichet papier** — `canal_saisie = "guichet_papier"` — bordereau
  papier remis au greffe, saisi par un agent.
- **Portail électronique** — `canal_saisie = "portail_electronique"` —
  soumission en ligne par un déclarant authentifié. ⚠️ Zone GELÉE
  `L11/MFA` pour l'authentification forte.

### 1.3 Régime déclaratif (art. 86)

Aucun formulaire n'impose un contrôle de fond. Les contrôles admis
sont **exclusivement de forme** et se limitent à :
- présence / absence d'un champ obligatoire ;
- lisibilité / compréhensibilité au sens de l'art. 80 ;
- appartenance à une liste limitative (natures, motifs, critères…) ;
- cohérence de format (date, montant, adresse électronique).

Le système ne vérifie **jamais** :
- l'identité réelle des parties ;
- l'existence effective d'un bien ;
- la validité d'un accord entre parties (signature cryptographique : zone GELÉE `L11/A2`) ;
- l'existence d'un numéro RC auprès du RCCM (zone GELÉE `L11/interconnexions`).

### 1.4 Contrôles automatiques applicables à TOUS les formulaires

| Contrôle | Fondement | Mise en œuvre | Message |
|----------|-----------|---------------|---------|
| Canal autorisé | art. 78, 80 | Enum `CanalSaisie` | `RejetForme` art. 80 |
| Clés inconnues dans le payload | TDR cohérence globale | `StrictInputMixin` (L3.5 § 4.2) | HTTP 400 + champ `non_autorises` |
| Authentification (hors recherche publique) | § 5.1 | `IsAuthenticated` DRF | HTTP 403 |
| Séparation stricte saisie / validation | § 4.1 | `peut_valider_demande` (L3.5 § 4.3) | HTTP 403 |

---

## 2. Formulaire d'inscription initiale (art. 85)

**Fondement** : articles 78, 85, 86, 87.
**Endpoint** : `POST /api/v1/inscriptions/` (L3.4 § 3.1).
**Modèle ORM** : `Inscription` + `Partie` + `BienGreve` + `RoleInscriptionPartie` (L3.1 § 2.8).
**Rôle habilité** : `AGENT_SAISIE` (guichet) OU `DECLARANT_EXTERNE` (portail).

### 2.1 Contenu du formulaire

**Bloc 1 — Canal et nature**

| Champ | Type | Obligatoire | Bilinguisme | Contrôle | Référence |
|-------|------|:-----------:|-------------|----------|-----------|
| `canal_saisie` | Choix limitatif `CanalSaisie` | ✅ | Neutre | Art. 80 : doit appartenir à la liste | art. 78 al. 1 |
| `nature_droit` | Choix limitatif `NaturesDroitInscrit` (12 valeurs) | ✅ | Neutre | Art. 80 + art. 76 : liste limitative | art. 76, 85 |

**Bloc 2 — Sûreté (art. 85)**

| Champ | Type | Obligatoire | Bilinguisme | Contrôle | Référence |
|-------|------|:-----------:|-------------|----------|-----------|
| `somme_garantie` | Décimal positif ou nul | ✅ | Neutre | Format Decimal(18,2) | art. 85 |
| `monnaie` | Code ISO 4217 (ex. `MRU`) | ✅ | Neutre | Code à 3 caractères | art. 85 |
| `duree_en_jours` | Entier strictement positif | ✅ | Neutre | ≥ 1 ; aucune borne supérieure à ce jour (zone A3) | art. 85 |
| `adresse_electronique_notifications` | Email | ❌ | Neutre | Format email | art. 85 avant-dernier alinéa |

**Bloc 3 — Parties (art. 85)** — un lien par rôle via `RoleInscriptionPartie`

Pour chaque **créancier garanti** (au moins 1) :

| Champ | Type | Obligatoire | Bilinguisme | Contrôle |
|-------|------|:-----------:|-------------|----------|
| `type_partie` | Choix `pp` / `pm` | ✅ | Neutre | Enum `TypePartie` |
| `nom` (PP) OU `denomination_sociale` (PM) | Texte libre | ✅ | Neutre (identité propre) | Non vide |
| `prenom` (PP) | Texte libre | ✅ si PP | Neutre | Non vide |
| `date_naissance` (PP) | Date | ✅ si PP | Neutre | Format ISO-8601 |
| `lieu_naissance` (PP) | Texte libre | ✅ si PP | Neutre | Non vide |
| `numero_rc` (PM) | Texte | ✅ si PM | Neutre | Pas de vérification d'existence (art. 86) |
| `adresse` | Texte libre | ✅ | Neutre | Non vide |
| `adresse_electronique` | Email | ❌ | Neutre | Format email |
| `telephone` | Texte | ❌ | Neutre | — |

Règle identique pour chaque **constituant** (au moins 1) et chaque
**débiteur** (au moins 1). Une même personne peut être désignée sous
plusieurs rôles simultanés.

**Bloc 4 — Biens grevés (art. 85, 93)** — au moins un bien

Pour chaque bien :

| Champ | Type | Obligatoire | Bilinguisme | Contrôle | Référence |
|-------|------|:-----------:|-------------|----------|-----------|
| `description_fr` | Texte libre | ⚠️ au moins une langue | Bilingue | — | art. 85 |
| `description_ar` | Texte libre | ⚠️ au moins une langue | Bilingue | — | art. 85 |
| `langue_faisant_foi_description` | Choix `fr` / `ar` / `equ` | ✅ si une seule version | Neutre | Enum `LangueFaisantFoi` | § 7.4 |
| `marque` | Texte | ❌ | Neutre | Non bloquant | art. 85 al. 3 |
| `modele` | Texte | ❌ | Neutre | Non bloquant | art. 85 al. 3 |
| `annee` | Entier | ❌ | Neutre | Non bloquant | art. 85 al. 3 |
| `numero_serie` | Texte | ❌ | Neutre | Non bloquant (indexé art. 93) | art. 85 al. 3, 93 |

**Règle art. 85 alinéa 3** : l'omission de `numero_serie`, `marque`,
`modele` ou `annee` ne prive pas l'inscription d'effet dès lors que
les biens sont décrits par ailleurs de manière suffisamment précise.
Le système **N'IMPOSE PAS** la saisie de ces champs. Vérifié par le
test [tests/test_regles_metier.py::test_champs_bien_grevé_optionnels_non_bloquants](../backend/tests/test_regles_metier.py).

**Bloc 5 — Identité du requérant (art. 85)**

| Champ | Type | Obligatoire | Bilinguisme | Contrôle |
|-------|------|:-----------:|-------------|----------|
| `requerant` | FK vers `Partie` | ✅ | Neutre | Structure identique au Bloc 3 |

### 2.2 Effets de la soumission

1. Enregistrement en base avec `statut = RECUE`.
2. `instant_arrivee` posé à l'horloge serveur (⚠️ **STUB** — cf. L3.3 § 2 et 3.2).
3. Transition automatique → `EN_CONTROLE_FORME` (§ 4.3, cf. L2.3).
4. Audit `inscription.deposer` tracé.
5. Aucun numéro d'ordre attribué à ce stade (attribution à la validation — cf. § 3.1 ci-dessous pour la référence à la validation ultérieure).

### 2.3 Zones gelées applicables

| Zone | Rappel |
|------|--------|
| `L11/MFA` | Authentification forte du déclarant externe sur le portail. |
| `L11/A7` | Prépaiement des émoluments (art. 85) — non exigé tant que non arbitré. |
| `L11/A2` | Signature électronique des parties — les accords du créancier et du constituant sont captés à la validation, pas au dépôt initial. |

---

## 3. Formulaire de modification (art. 88)

**Fondement** : articles 88, 90, 93.
**Endpoint** : `POST /api/v1/modifications/` (L3.4 § 4.1).
**Modèle ORM** : `DemandeModification` + `DiffModification` (L3.1 § 2.9).
**Rôle habilité pour créer** : `AGENT_SAISIE` OU `DECLARANT_EXTERNE`.
**Rôle habilité pour appliquer** : `AUTORITE_VALIDATION` (séparation stricte § 4.1).

### 3.1 Contenu du formulaire

**Bloc 1 — Identification de la modification**

| Champ | Type | Obligatoire | Bilinguisme | Contrôle | Référence |
|-------|------|:-----------:|-------------|----------|-----------|
| `inscription` | Référence à l'inscription initiale | ✅ | Neutre | Doit être en cours de validité (§ 4.3) | art. 88, 93 |
| `objet_modification_fr` | Texte libre | ⚠️ bilingue | Multilingue | Non vide | art. 88 |
| `objet_modification_ar` | Texte libre | ⚠️ bilingue | Multilingue | Non vide | art. 88 |

**Bloc 2 — Différentiel proposé (`diff_propose`)**

Schéma STRICT — toute clé hors schéma = refus (L3.1 § 2.9 + L3.4 § 4.1) :

```
{
  "parties": {
    "ajouter": [ <liste de parties à créer> ],
    "retirer": [ <ids de liens RoleInscriptionPartie à désactiver> ]
  },
  "biens": {
    "ajouter": [ <liste de biens à créer> ],
    "retirer": [ <ids de biens à désactiver> ]
  },
  "scalaires": {
    "nature_droit":                        <clé NaturesDroitInscrit>,
    "somme_garantie":                      <décimal ≥ 0>,
    "monnaie":                             <code ISO>,
    "adresse_electronique_notifications":  <email>
  }
}
```

**Champs NON modifiables par ce formulaire** (art. 78, 90 al. 2) :
numéro d'ordre, instants (arrivée, saisie opposable), durée en jours,
date d'expiration, statut, mention radiée, motif de rejet. Toute
tentative → refus `DIFF_INVALIDE`.

**Bloc 3 — Accords des parties (art. 88)**

| Champ | Type | Obligatoire | Bilinguisme | Contrôle | Référence |
|-------|------|:-----------:|-------------|----------|-----------|
| `accord_createur_confirme` | Booléen | ✅ | Neutre | Doit être `true` pour appliquer | art. 88 |
| `accord_constituant_confirme` | Booléen | ✅ | Neutre | Doit être `true` pour appliquer | art. 88 |

⚠️ **Zone gelée `L11/A2`** : le contrôle **cryptographique** de ces
signatures électroniques n'est PAS câblé. Seul le flag booléen est
vérifié à l'application. Une bascule vers la vérification effective
passera par un adaptateur sans changement du formulaire.

### 3.2 Contrôles au dépôt (création de la demande)

- Schéma strict du diff (rejet des clés inconnues).
- Clés scalaires limitées à `CHAMPS_SCALAIRES_MODIFIABLES`.
- `nature_droit` ∈ `NaturesDroitInscrit` (liste limitative art. 76).
- `somme_garantie` ≥ 0 si fournie.

### 3.3 Contrôles à l'application (art. 88 dernier alinéa)

Au moment de l'application, après mutation dans un savepoint
(L3.2 § 4.2), l'**état final** de l'inscription est vérifié :

| Contrôle | Motif de refus (clé limitative) | Effet |
|----------|--------------------------------|-------|
| ≥ 1 constituant actif | `ETAT_FINAL_CONSTITUANT_ABSENT` | Rollback + REJETEE + audit |
| ≥ 1 créancier garanti actif | `ETAT_FINAL_CREANCIER_ABSENT` | Rollback + REJETEE + audit |
| ≥ 1 bien grevé actif | `ETAT_FINAL_BIEN_ABSENT` | Rollback + REJETEE + audit |
| Accords art. 88 confirmés | `ACCORDS_MANQUANTS` | REJETEE + audit |
| Statut compatible | `STATUT_INSCRIPTION_INCOMPATIBLE` | REJETEE + audit |
| Schéma respecté | `DIFF_INVALIDE` | REJETEE + audit |
| Diff non vide | `DIFF_VIDE` | REJETEE + audit |
| Première application | `DEMANDE_NON_APPLICABLE` | Refus sans nouveau rejet |

Référence : L3.1 § 2.9, L3.4 § 4.3, tests
[test_modifications_cas_limites.py](../backend/tests/test_modifications_cas_limites.py)
et [test_api_d2_rejet_art88.py](../backend/tests/test_api_d2_rejet_art88.py).

### 3.4 Effets de l'application réussie

- Transition → `MODIFIEE` (§ 4.3).
- Snapshot `MODIFICATION_AVANT` + `MODIFICATION_APRES` (art. 79).
- Audit `modification.appliquer`.
- Numéro d'ordre INCHANGÉ (immutable — art. 78).
- Durée et date d'expiration INCHANGÉES (art. 90 al. 2).

### 3.5 Zones gelées applicables

| Zone | Rappel |
|------|--------|
| `L11/A2` | Signature électronique des parties : flag booléen uniquement. |
| `L11/horodatage` | `applique_le` non opposable tant que la source de temps n'est pas arbitrée. |
| `L11/parties_reutilisation` | Chaque ajout de partie crée une NOUVELLE `Partie` — pas de référencement d'une partie existante. |

---

## 4. Formulaire de renouvellement (art. 91)

**Fondement** : article 91.
**Endpoint** : `POST /api/v1/renouvellements/` (L3.4 § 5.1).
**Modèle ORM** : `DemandeRenouvellement` (L3.1 § 2.10).
**Rôle créateur** : `AGENT_SAISIE` OU `DECLARANT_EXTERNE`.
**Rôle applicateur** : `AUTORITE_VALIDATION` (séparation stricte § 4.1).

### 4.1 Contenu du formulaire

| Champ | Type | Obligatoire | Bilinguisme | Contrôle | Référence |
|-------|------|:-----------:|-------------|----------|-----------|
| `inscription` | Référence | ✅ | Neutre | En cours de validité (STATUTS_EN_COURS_DE_VALIDITE) | art. 91, § 4.3 |

**Aucun autre champ.** Le renouvellement n'exige pas de nouveau
bordereau détaillé : il prolonge mécaniquement la durée initiale.

### 4.2 Contrôles à l'application

| Contrôle | Fondement | Exception levée |
|----------|-----------|-----------------|
| Inscription en cours de validité | § 4.3 | `RenouvellementHorsDelai` |
| `date_expiration` future (non atteinte) | art. 91 | `RenouvellementHorsDelai` |
| Séparation stricte (acteur ≠ créateur demande) | § 4.1 | `AutorisationRefusee` |

### 4.3 Effets

Prorogation mécanique :

```
ancienne_date_expiration = inscription.date_expiration
nouvelle_date_expiration = ancienne_date_expiration + inscription.duree_en_jours
```

⚠️ **Hypothèse A3** : « durée initiale » s'entend comme la durée
fixée à l'inscription initiale, **non pas** comme une durée résultant
d'un renouvellement antérieur. Décision adoptée par défaut, en
attente d'arbitrage MO.

Transition → `RENOUVELEE` (§ 4.3). Audit `renouvellement.appliquer`.
Numéro d'ordre inchangé.

---

## 5. Formulaire de radiation (art. 92)

**Fondement** : article 92.
**Endpoint** : `POST /api/v1/radiations/` (L3.4 § 6.1).
**Modèle ORM** : `DemandeRadiation` (L3.1 § 2.11).
**Rôle créateur** : `AGENT_SAISIE`, `DECLARANT_EXTERNE`.
**Rôle applicateur** : `AUTORITE_VALIDATION` (séparation stricte § 4.1).

### 5.1 Contenu du formulaire (art. 92 alinéa 1)

| Champ | Type | Obligatoire | Bilinguisme | Contrôle | Référence |
|-------|------|:-----------:|-------------|----------|-----------|
| `inscription` | Référence à l'inscription initiale | ✅ | Neutre | En cours de validité | art. 92 |
| `fondement` | Choix limitatif `FondementRadiation` | ✅ | Neutre | `consentement`, `jugement`, `requerant_original` | art. 92 |
| `nom_constituant` (PP) | Texte | ✅ si PP | Neutre | Non vide | art. 92 al. 1 |
| `prenom_constituant` (PP) | Texte | ✅ si PP | Neutre | Non vide | art. 92 al. 1 |
| `denomination_constituant` (PM) | Texte | ✅ si PM | Neutre | Non vide | art. 92 al. 1 |
| `adresse_constituant` | Texte | ✅ | Neutre | Non vide | art. 92 al. 1 |
| `numero_rc_constituant` | Texte | ⚠️ si PM | Neutre | Pas de vérification d'existence | art. 92 al. 1 |

### 5.2 Pièces jointes admises (art. 92 alinéa 1 in fine)

| Fondement | Pièce attendue | Format |
|-----------|----------------|--------|
| `consentement` | Acte authentique OU sous seing privé portant consentement à la radiation | Document joint (ex. PDF) |
| `jugement` | Copie de la décision judiciaire reconnaissant l'intérêt légitime du demandeur | Document joint |
| `requerant_original` | Aucune pièce requise (radiation par la personne ayant procédé à l'inscription) | — |

Les pièces sont attachées via `PieceJointe` (cf. L3.1 § 2.8).
⚠️ **Zone gelée `L11/A5` partielle** : le scellement opposable des
pièces jointes (empreinte `sceau_empreinte`) reste en STUB.

### 5.3 Effets de l'application réussie

- Transition → `RADIEE` (§ 4.3).
- `mention_radiee = True` (art. 92 al. 2).
- L'inscription reste au **fichier public** jusqu'à sa date
  d'expiration avec la mention « radiée ».
- À expiration : transition automatique → `EXPIREE` puis `ARCHIVEE` +
  `fichier_actuel = "general"` (art. 92 al. 3).

---

## 6. Formulaire de recherche publique (art. 94-97)

**Fondement** : articles 94, 95, 96, 97.
**Endpoint** : `POST /api/v1/recherche/` (L3.4 § 8.1).
**Permission** : `AllowAny` (art. 94 — « ouverture à tout intéressé »).

### 6.1 Contenu du formulaire

Liste **LIMITATIVE** de quatre critères (art. 96) :

| Champ | Type | Obligatoire | Bilinguisme | Référence |
|-------|------|:-----------:|-------------|-----------|
| `nom_constituant` | Texte | ⚠️ au moins 2 des 4 | Neutre | art. 96 |
| `numero_rc` | Texte | ⚠️ au moins 2 des 4 | Neutre | art. 96 |
| `numero_serie_bien` | Texte | ⚠️ au moins 2 des 4 | Neutre | art. 96 |
| `numero_inscription` | Texte | ⚠️ au moins 2 des 4 | Neutre | art. 96 |

**Règle cardinale** : AU MOINS 2 des 4 critères doivent être
renseignés. Toute soumission avec < 2 critères → `RechercheCriteresInsuffisants` (HTTP 400, article 96).

**Clés hors liste refusées** par `StrictInputSerializer`. Vérifié par
[tests/test_api_d3_accept_language.py::test_recherche_critere_hors_liste_refuse_par_l_api](../backend/tests/test_api_s4_recherche_coherence.py).

### 6.2 Traitement

1. Filtrage sur `STATUTS_FICHIER_PUBLIC` (art. 77 : inscriptions en
   cours de validité uniquement).
2. Pour chaque critère renseigné, jointure métier (rôle constituant,
   RC, numéro de série, numéro d'ordre).
3. Persistance de la requête dans `RequeteRecherche` (append-only).
4. Audit `recherche.lancer`.

### 6.3 Structure de la réponse

- `instant` : horodatage de la recherche à la seconde (⚠️ STUB — L3.3).
- `requete_id` : identifiant de la trace de recherche.
- `criteres_utilises` : liste des clés effectivement renseignées.
- `nombre_resultats` : entier.
- `inscriptions` : liste des `Inscription` du fichier public correspondant.
- `homonymes_par_inscription` : si `nom_constituant` utilisé,
  **résultat EXHAUSTIF des homonymes** avec nom, prénom, dénomination,
  adresse, date de naissance (art. 97 alinéa 2).
- `avertissement` : mention « Aperçu non opposable — certificat
  probant art. 97 GELÉ » (`L11/A5`).

### 6.4 Certificat de recherche associé (art. 97 alinéa 3)

Le TDR § 4.2.5 prévoit qu'à l'issue de toute recherche, un certificat
est délivré. Structure du certificat (L3.1 § 2.12) :

| Champ | Contenu |
|-------|---------|
| `type_certificat` | `"recherche"` |
| `requete_recherche` | FK vers la trace de recherche |
| `langue_generation` | `fr`, `ar` ou `fr-ar` |
| `probant` | **Toujours `False`** tant que l'arbitrage scellement + horodatage n'est pas rendu |
| `empreinte` | SHA-256 STUB |
| `contenu_json` | Sérialisation canonique bilingue |

⚠️ **Zones gelées applicables** : `L11/A5` (certificat probant) et
`L11/horodatage` (horodatage opposable).

---

## 7. Bordereau de rejet (art. 80)

**Fondement** : article 80.
**Endpoint** : `POST /api/v1/inscriptions/<uuid>/rejeter/` (L3.4 § 3.5).
**Rôle habilité** : `AUTORITE_VALIDATION` (séparation stricte).

⚠️ Le rejet n'est pas un formulaire de saisie initiale mais une
décision structurée. Il est tout de même spécifié ici, conformément
au périmètre.

### 7.1 Contenu

| Champ | Type | Obligatoire | Bilinguisme | Contrôle | Référence |
|-------|------|:-----------:|-------------|----------|-----------|
| `motif` | Choix **LIMITATIF** `MotifRejet` | ✅ | Neutre | 3 motifs uniquement : `canal_non_autorise`, `informations_illisibles`, `informations_incomprehensibles` | art. 80 |
| `commentaire_fr` | Texte libre | ❌ | Multilingue | — | — |
| `commentaire_ar` | Texte libre | ❌ | Multilingue | — | — |

**Règle cardinale art. 80** : seuls les trois motifs listés sont
admissibles. Tout autre motif → HTTP 400 + `RejetForme`. Vérifié par
[test_api_s2_rejet_art80.py::test_rejet_motif_hors_liste_refuse](../backend/tests/test_api_s2_rejet_art80.py).

**Règle cardinale art. 86** : le rejet est un contrôle **de forme
uniquement**. Aucun motif fondé sur la véracité des énonciations n'est
admissible.

### 7.2 Effets

- Transition `EN_CONTROLE_FORME → REJETEE` (§ 4.3).
- `motif_rejet` figé (immuable).
- `instant_rejet` posé.
- Commentaires bilingues préservés.
- Audit `inscription.rejeter` + `transition.rejet_art80`.
- L'inscription rejetée **n'apparaît jamais au fichier public**.

---

## 8. Formulaire de validation (art. 87)

⚠️ Distinction : la validation **n'est pas un bordereau de l'article
85** mais une décision de l'autorité de validation qui fait suite au
contrôle de forme art. 80.

**Fondement** : articles 78 al. 4, 85, 86, 87.
**Endpoint** : `POST /api/v1/inscriptions/<uuid>/valider/` (L3.4 § 3.4).
**Rôle habilité** : `AUTORITE_VALIDATION` (séparation stricte § 4.1).

### 8.1 Contenu

Aucun payload — action déclenchée sur une inscription déjà reçue et
peuplée (parties, biens) à l'état `EN_CONTROLE_FORME`.

### 8.2 Effets

1. `attribuer_numero_ordre()` : verrou pessimiste sur `SequenceNumeroOrdre`, incrémentation, horodatage.
2. `numero_ordre = format(ordre, instant)` → `NNNNNN-AAAAMMJJHHMMSS` (art. 78 al. 4).
3. `instant_saisie_opposable` posé (⚠️ STUB, `L11/horodatage`).
4. `date_expiration = instant.date() + duree_en_jours`.
5. Transition → `INSCRITE` (§ 4.3).
6. Audit `inscription.valider` + `transition.validation_greffier`.
7. ⚠️ **Délivrance du certificat d'inscription** (art. 78 alinéa 3,
   art. 86 in fine) — STRUCTUREL : `Certificat(type_certificat="inscription", probant=False)`. Activation
   probante conditionnée à `L11/A5` et `L11/horodatage`.

---

## 9. Matrice récapitulative des formulaires

| Formulaire | Article | Endpoint | Rôle créateur | Rôle applicateur | Zones gelées | Test de référence |
|------------|:-------:|----------|---------------|------------------|--------------|-------------------|
| Inscription initiale | 85 | `POST /inscriptions/` | AGENT_SAISIE, DECLARANT_EXTERNE | AUTORITE_VALIDATION | MFA, A2, A7, horodatage | S1 ; D.3 |
| Validation | 87 | `POST /inscriptions/<uuid>/valider/` | — | AUTORITE_VALIDATION | A5, horodatage | S1 ; D.1 |
| Rejet | 80 | `POST /inscriptions/<uuid>/rejeter/` | — | AUTORITE_VALIDATION | — | S2 ; D.1 ; D.3 |
| Modification | 88 | `POST /modifications/` + `/appliquer/` | AGENT_SAISIE, DECLARANT_EXTERNE | AUTORITE_VALIDATION | A2, horodatage, parties_reutilisation | D.2 |
| Renouvellement | 91 | `POST /renouvellements/` + `/appliquer/` | AGENT_SAISIE, DECLARANT_EXTERNE | AUTORITE_VALIDATION | horodatage | S3 |
| Radiation | 92 | `POST /radiations/` + `/appliquer/` | AGENT_SAISIE, DECLARANT_EXTERNE | AUTORITE_VALIDATION | A5 (pièces jointes scellées) | S4 |
| Recherche publique | 96, 97 | `POST /recherche/` | — (public art. 94) | — | A5, horodatage | S4 ; D.3 |

---

## 10. Renvois croisés

- Modèle de données : [L3.1](L3_1_modele_donnees.md).
- Dictionnaire API (endpoints, codes HTTP) : [L3.4](L3_4_dictionnaire_api.md).
- Architecture et flux : [L3.2](L3_2_architecture_modulaire.md) § 4.
- Bilinguisme et taxonomie des champs : [L3.6](L3_6_matrice_bilingue.md).
- Règles de validation consolidées : [L2.2](L2_2_regles_validation.md).
- Statuts, transitions et messages système : [L2.3](L2_3_matrice_statuts_transitions.md).
- Traçabilité article par article : [L11](L11_tracabilite_articles_76_97.md).
