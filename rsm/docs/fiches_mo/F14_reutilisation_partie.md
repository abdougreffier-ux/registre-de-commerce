# Fiche MO — F14 — Réutilisation d'une Partie existante (art. 88)

**Référence L11** : `L11/parties_reutilisation`
**Articles fondateurs** : article 88 (modification — contenu du
diff) ; article 86 (régime déclaratif) ; article 93 (indexation).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/parties_reutilisation` — Référencement d'une `Partie` existante dans le diff d'une modification |
| Articles fondateurs | Art. 88 (contenu du diff), art. 86 (régime déclaratif), art. 93 (indexation) |
| Statut actuel | **Conservatisme strict** — le diff de modification (cf. L3.1 § 2.9) **crée systématiquement** une nouvelle `Partie` à chaque ajout ; pas de référencement d'une partie existante |
| Dépendances | F13 (si identité nationale retenue, elle peut intervenir dans l'identification des parties) |
| Impact transverse | Uniquement le diff de modification art. 88 — ne touche ni les inscriptions initiales ni les radiations. |

---

## 2. Contexte juridique

### 2.1 Contenu du diff d'une modification (art. 88)

Le diff de modification (cf. L2.1 § 3 + L3.1 § 2.9) accepte trois
blocs :
- `parties` : ajouter / retirer des parties ;
- `biens` : ajouter / retirer des biens ;
- `scalaires` : modifier nature, somme, monnaie, adresse email.

Pour l'**ajout** d'une partie, le schéma actuel (`DiffModification`)
accepte uniquement un objet `donnees` qui contient les informations
d'identité (nom, prénom, dénomination, etc.). Le système CRÉE alors
une nouvelle ligne `Partie` avec ces données.

Il n'existe **aucune clé `partie_id`** qui permettrait de référencer
une partie déjà connue du système.

### 2.2 Enjeu fonctionnel

Dans la pratique, une même personne (physique ou morale) peut figurer
dans plusieurs inscriptions :
- une banque créancière de plusieurs sûretés sur plusieurs clients ;
- une société constituant simultanément des sûretés sur plusieurs
  éléments de son patrimoine ;
- un notaire mandataire récurrent.

Deux approches sont possibles :
- **Conservatisme** : chaque inscription a ses propres lignes
  `Partie`, jamais partagées — chaque modification qui ajoute une
  partie crée une nouvelle ligne, même si la personne existe déjà.
- **Réutilisation** : la modification peut référencer par `partie_id`
  une ligne `Partie` existante.

### 2.3 Articulation avec l'article 86 (régime déclaratif)

L'option de réutilisation pourrait introduire un **contrôle de
cohérence** implicite : si le déposant référence une `Partie`
existante dont les énonciations sont erronées, le système reproduit
l'erreur. À l'inverse, si le déposant fournit des données
nouvelles, elles peuvent diverger de celles déjà présentes dans le
système pour la même personne — ce qui pose un problème de cohérence
sans pour autant être une irrégularité juridique (l'art. 86 autorise
chaque déposant à énoncer ce qu'il veut).

### 2.4 Articulation avec l'article 93 (indexation)

L'art. 93 impose une indexation par nom du constituant. Si deux
inscriptions désignent « le même » constituant via deux `Partie`
différentes :
- **Conservatisme** : les deux inscriptions apparaissent séparément
  dans la recherche ; les homonymes (art. 97 al. 2) peuvent être le
  même individu, sans que le système ne le devine.
- **Réutilisation** : les deux inscriptions partagent la `Partie` ;
  la recherche consolidée est plus précise.

### 2.5 Risques juridiques selon l'option retenue

**Risques du conservatisme strict** :
- Duplication d'identités dans le système (plusieurs lignes `Partie`
  pour une même personne) ;
- Difficulté à agréger les inscriptions relatives à une même personne ;
- Charge supplémentaire pour les déposants qui doivent re-saisir
  l'identité à chaque ajout.

**Risques de la réutilisation** :
- **Risque cardinal** : une partie référencée peut avoir été
  désactivée (`actif=False`), créée par un autre déposant (problème
  de confidentialité), ou avoir été modifiée après sa création —
  chacun de ces cas nécessite une règle explicite.
- Risque d'appariement erroné (homonymes) si le déposant sélectionne
  mal.
- Question de responsabilité : si deux inscriptions partagent une
  `Partie` et que l'une d'elles s'avère frauduleuse, la qualité de
  l'identification dans l'autre est également affectée.

---

## 3. Situation actuelle dans le système

### 3.1 Mécanisme actuel

| Élément | État |
|---------|------|
| Schéma du diff (`DiffModification`) | Accepte `parties.ajouter` avec `donnees` seulement — pas de `partie_id` |
| Clé racine `partie_id` | Refusée (clé hors schéma — `StrictInputMixin`) |
| `_creer_partie()` dans le service | Crée systématiquement une nouvelle ligne `Partie` |
| Tests désactivés liés | `test_api_zones_gelees.py::test_reutilisation_partie_existante_via_diff` |
| Documentation | L3.1 § 2.6 (conservation conservatrice mentionnée) ; L2.1 § 3.5 (mention dans le formulaire) |

### 3.2 Points d'extension

L'interface actuelle est **conservatrice** par choix explicite. Pour
activer la réutilisation, il faudrait :
- ajouter une clé optionnelle `partie_id` dans le diff ;
- faire évoluer le service `_creer_partie()` pour accepter soit
  des données, soit un identifiant ;
- définir les règles d'accessibilité (qui peut référencer quelle
  partie).

---

## 4. Options d'arbitrage

### 4.1 Option a — Conservatisme strict (statu quo)

**Description** : chaque ajout de partie dans un diff de modification
CRÉE une nouvelle ligne `Partie`. Aucun référencement d'une partie
existante n'est permis.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟢 Stricte (aucun contrôle d'identité) |
| Simplicité technique | 🟢 Maximale |
| Cohérence des données | 🔴 Faible (duplications possibles) |
| Charge pour le déposant | 🟠 Re-saisie systématique |
| Risque juridique | 🟢 Nul (conforme à l'état actuel) |

**Avantages** : simplicité, conformité stricte.
**Inconvénients** : duplication de données.

### 4.2 Option b — Réutilisation libre de toute partie active

**Description** : le diff accepte une clé `partie_id` référençant
toute `Partie.actif=True` du système. Aucune restriction d'accès.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟠 Tension — le déposant peut référencer une partie énoncée par un autre déposant |
| Simplicité technique | 🟢 Modérée |
| Cohérence des données | 🟢 Élevée |
| Confidentialité | 🔴 **Faible** — toute partie est visible de tout déposant |
| Risque RGPD | 🔴 Élevé |

**Avantages** : cohérence maximale.
**Inconvénients** : problèmes de confidentialité des données
personnelles d'un déposant à l'autre.

### 4.3 Option c — Réutilisation limitée à ses propres parties

**Description** : le diff accepte `partie_id` uniquement si la partie
référencée a été **créée par le même déposant** (ou sur son
inscription). Un déposant ne peut référencer que des parties qu'il a
lui-même introduites.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟢 Préservée |
| Confidentialité | 🟢 Respectée |
| Cohérence intra-déposant | 🟢 Élevée |
| Cohérence globale | 🟠 Modérée (toujours des duplications inter-déposants) |
| Complexité | 🟠 Modérée (contrôle d'appartenance) |

**Avantages** : équilibre confidentialité / cohérence.
**Inconvénients** : ne résout pas la duplication inter-déposants.

### 4.4 Option d — Matching automatique assisté (suggestion)

**Description** : lors de la saisie d'une nouvelle partie, le système
détecte une **correspondance probable** avec une partie existante
(matching sur nom + RC ou nom + date de naissance). Il **suggère**
au déposant de réutiliser la partie existante. La décision finale
revient au déposant.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟢 Préservée (suggestion, pas de contrainte) |
| UX | 🟢 Améliorée |
| Cohérence | 🟢 Progressive |
| Risque de faux positifs / négatifs | 🟠 Modéré |
| Complexité | 🔴 Élevée (algorithme de matching) |

**Avantages** : combine confidentialité et qualité des données.
**Inconvénients** : algorithme de matching à calibrer ; exige
également de définir une politique de confidentialité (quelles
parties existent-elles dans le corpus de matching ?).

### 4.5 Option e — Réutilisation avec consentement explicite de la partie

**Description** : pour référencer une partie existante créée par un
autre déposant, un **consentement explicite** de la partie concernée
est requis (ex. code de confirmation envoyé par e-mail ou SMS). Le
consentement est tracé au journal d'audit.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟢 Préservée |
| Confidentialité | 🟢 Stricte |
| UX | 🔴 Lourde |
| Complexité | 🔴 Élevée |
| Dépendance F13 | 🟠 (canaux de notification à activer) |

**Avantages** : respect maximal de la confidentialité et du
consentement.
**Inconvénients** : procédure lourde, dépendance à des canaux
externes.

### 4.6 Option f — Identification par identifiant national (si F13 d activée)

**Description** : si une identité numérique nationale est retenue
(F13 option d / F2 option c), les parties identifiées par leur
numéro national sont automatiquement réutilisées — une seule ligne
`Partie` par numéro national unique. Les parties sans numéro national
restent en conservatisme strict.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟢 Préservée (identité vérifiée par le fournisseur national) |
| Dépendance | 🔴 Identité nationale active |
| Cohérence | 🟢 Maximale pour les parties identifiées |
| UX | 🟢 Transparente |

**Avantages** : conforme, moderne, cohérent.
**Inconvénients** : dépend de F13/F2 arbitrées.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Modifications |
|--------|---------------|
| a | Aucune |
| b | Ajout de la clé `partie_id` + validation simple |
| c | Ajout de la clé + contrôle d'appartenance (liens historiques) |
| d | Module de matching + interface de suggestion |
| e | Flux de consentement + module de notification |
| f | Connecteur identité + table de correspondance `id_national → Partie` |

### 5.2 Impacts sur les tests

- Activation de `test_reutilisation_partie_existante_via_diff`.
- Nouveaux tests selon option : confidentialité, matching,
  consentement, intégration identité.

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 § 3 (diff modification) | Schéma mis à jour si réutilisation activée |
| L3.1 § 2.6 (`Partie`) | Documentation de la politique retenue |
| L3.1 § 2.9 (`DiffModification`) | Évolution du schéma |
| L11 | Passage de `L11/parties_reutilisation` à IMPLÉMENTÉ |

### 5.4 Dépendances transversales

- **F2 / F13 (identité numérique)** : si retenues, mutualisation
  avec F14 option f.
- **F13 (notifications)** : si retenues, activation possible
  d'option e.
- **Régime déclaratif art. 86** (F1, F13) : la lecture retenue de
  l'art. 86 conditionne l'admissibilité des options b à f.

### 5.5 Impacts sur l'exploitation

- **Fusion / déduplication** : politique de traitement des doublons
  existants si bascule d'option a vers b, c, d, e ou f.
- **Audit** : traçabilité des références à une partie existante
  (qui a référencé quoi, quand).
- **Conservation art. 79** : une partie désactivée mais encore
  référencée par des inscriptions historiques doit rester
  consultable.

---

## 6. Tradeoffs synthétiques

| Critère | a (Conservatisme) | b (Libre) | c (Propre déposant) | d (Matching) | e (Consentement) | f (Identité nationale) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| Conformité art. 86 | Maximale | Tension | Préservée | Préservée | Préservée | Préservée |
| Confidentialité | N/A | Faible | Élevée | Modérée | Maximale | Élevée |
| Cohérence des données | Faible | Élevée | Modérée | Progressive | Élevée | Maximale (sous-ensemble) |
| Charge déposant | Modérée | Faible | Faible | Faible | Élevée | Très faible |
| Complexité technique | Nulle | Faible | Modérée | Élevée | Élevée | Modérée (avec F13/F2) |
| Dépendance externe | Aucune | Aucune | Aucune | Aucune | Canaux notif. | Identité nationale |
| Mise en service | Immédiate | Court | Court | Moyen | Long | Dépend F13/F2 |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Lecture de l'art. 86** : stricte (option a) ou souple
   (options b à f) ?
2. **Cadre légal / RGPD / protection des données personnelles** :
   quelles règles locales s'appliquent aux données des parties ?
3. **Politique en cas de doublon détecté** (option d) : fusion
   automatique, manuelle, ou conservation ?
4. **Ergonomie souhaitée** : importance d'une expérience fluide
   pour les déposants institutionnels récurrents ?
5. **Articulation avec F2 / F13** : arbitrage conjoint ?
6. **Sort des parties historiques** lors d'un changement de
   politique (migration) ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ autre : ______ |
| Schéma du diff à adapter | _(à renseigner)_ |
| Règle de confidentialité | _(à renseigner)_ |
| Politique de doublons | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Modèle `Partie` : [L3.1 § 2.6](../L3_1_modele_donnees.md).
- Modèle `DiffModification` + schéma : [L3.1 § 2.9](../L3_1_modele_donnees.md).
- Formulaire de modification : [L2.1 § 3](../L2_1_formulaires_bilingues.md).
- Régime déclaratif art. 86 : [L2.2 § 2.7](../L2_2_regles_validation.md).
- Fiche F2 (identité) : [F2_authentification_forte.md](F2_authentification_forte.md).
- Fiche F13 (interconnexions) : [F13_interconnexions_externes.md](F13_interconnexions_externes.md).
- Registre : [L11](../L11_tracabilite_articles_76_97.md).
