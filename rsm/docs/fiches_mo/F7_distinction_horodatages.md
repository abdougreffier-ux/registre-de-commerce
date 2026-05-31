# Fiche MO — F7 — Distinction horodatage d'arrivée / horodatage de saisie

**Référence L11** : `A9`
**Articles fondateurs** : article 78 alinéas 2 et 3 ; TDR § 4.2.1,
§ 9.3 (zone d'ambiguïté signalée).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `A9` — Distinction entre horodatage d'arrivée et horodatage de saisie |
| Articles fondateurs | Art. 78 al. 2 (ordre d'arrivée), al. 3 (prise d'effet à la saisie), al. 4 (composition du numéro d'ordre) |
| Statut actuel | **Deux horodatages distincts** implémentés : `Inscription.instant_arrivee` (posé à la réception) et `Inscription.instant_saisie_opposable` (posé à la validation). Lien logique non formellement arbitré. |
| Dépendances | F5 (source de temps commune), F8 (politique d'indisponibilité) |
| Impact transverse | Toutes les inscriptions ; rang chronologique (art. 78 al. 2) ; prise d'effet (art. 78 al. 3). |

---

## 2. Contexte juridique

### 2.1 Double exigence de l'article 78

| Alinéa | Exigence |
|:------:|----------|
| **al. 2** | « Les demandes sont enregistrées dans l'ordre de leur **date d'arrivée**. » |
| **al. 3** | « L'inscription **prend effet à la date et à l'heure auxquelles les informations sont saisies dans le fichier du Registre** de façon à être accessibles aux personnes effectuant une recherche. » |

Ces deux alinéas pointent vers **deux instants distincts** :
- l'instant où la demande arrive physiquement au greffe ou au
  portail (al. 2 — fonde l'ordre entre déposants concurrents) ;
- l'instant où l'inscription devient accessible à la recherche
  publique (al. 3 — fonde l'opposabilité aux tiers).

### 2.2 Ambiguïté signalée au TDR § 9.3

> *« Article 78, alinéa 2 : l'ordre d'arrivée est-il déterminé par la
>   réception physique au guichet, par la soumission électronique,
>   ou par la saisie effective dans la base ? Les présents TDR
>   retiennent l'horodatage de réception au point d'entrée choisi,
>   distinct, le cas échéant, de l'horodatage de saisie effective
>   dans la base. »*

Le TDR **signale** cette ambiguïté comme hypothèse à arbitrer par le
MO (zone A9).

### 2.3 Enjeu juridique cardinal

Dans un contentieux entre deux déposants dont les demandes se
chevauchent, la question est :
- qui a la **priorité d'inscription** ? ;
- à partir de quand l'inscription est-elle **opposable aux tiers** ?

La réponse dépend de la définition retenue pour « date d'arrivée » et
« instant de saisie ».

### 2.4 Cas de figure potentiels

| Cas | Instant d'arrivée | Instant de saisie opposable | Délai typique |
|-----|-------------------|------------------------------|:-------------:|
| Bordereau papier déposé le matin, saisi par l'agent l'après-midi | Dépôt physique (matin) | Validation greffier (après-midi) | Quelques heures |
| Dépôt électronique automatique | Réception par le portail | Validation greffier (potentiellement immédiate ou différée) | Minutes à heures |
| Dépôt papier le vendredi soir, saisi le lundi | Dépôt physique (vendredi) | Validation (lundi) | 3 jours |
| Indisponibilité du système (cf. F8) | File d'attente (horodatage de réception) | Saisie à rétablissement | Variable |

### 2.5 Risques juridiques en l'absence d'arbitrage

- **Risque de contestation du rang** entre deux déposants si les deux
  horodatages ne coïncident pas et si la règle de priorité n'est pas
  formellement arbitrée.
- **Risque d'incertitude** sur l'opposabilité aux tiers en cas
  d'incident entre réception et saisie (ex. recherche effectuée
  pendant cet intervalle).
- **Risque pour la valeur probante du certificat de recherche**
  (art. 97) : si un tiers a effectué une recherche à T0, entre
  réception de la demande X (à T-1) et sa saisie (à T+1), le
  certificat délivré à T0 ne la reflètera pas — nuance juridiquement
  sensible.

---

## 3. Situation actuelle dans le système

### 3.1 Deux horodatages existants

```
┌───────────────────────────────────────────────────────────┐
│ Inscription                                               │
│                                                           │
│   instant_arrivee        ← posé à la CRÉATION            │
│   (art. 78 al. 2)          (réception, automatique)      │
│                                                           │
│   instant_saisie_opposable ← posé à la VALIDATION        │
│   (art. 78 al. 3)           (service valider_inscription)│
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### 3.2 Règles actuelles

- `instant_arrivee` est posé par `creer_demande()` à
  `timezone.now()` — indexé en base (ordre de tri).
- `instant_saisie_opposable` est posé par `valider_inscription()` à
  l'instant où le numéro d'ordre est attribué — indexé.
- Le numéro d'ordre `NNNNNN-AAAAMMJJHHMMSS` embarque la composante
  temporelle de `instant_saisie_opposable` (art. 78 al. 4).

### 3.3 Ce qui n'est pas formellement arbitré

- La **règle de priorité juridique** : lequel des deux horodatages
  détermine la priorité entre deux déposants en cas de litige ?
- La **politique de tolérance** : quel délai maximal est acceptable
  entre `instant_arrivee` et `instant_saisie_opposable` ? Au-delà,
  quelle procédure ?
- L'**affichage** au public : le certificat de recherche mentionne-t-il
  les deux instants ou un seul ?

---

## 4. Options d'arbitrage

### 4.1 Option a — Horodatage unique (rapprochement des deux)

**Description** : l'ordre d'arrivée et la prise d'effet sont réputés
coïncider. Techniquement, `instant_saisie_opposable` est posé dès la
réception (validation automatisée ou validation considérée comme
instantanée). Un seul horodatage juridique est opposable.

| Dimension | Évaluation |
|-----------|------------|
| Simplicité juridique | 🟢 **Maximale** |
| Compatibilité avec le canal papier | 🔴 **Faible** — un bordereau papier déposé à T-1 mais saisi par l'agent à T+1 aurait une prise d'effet à T+1, alors que l'art. 78 al. 2 semble imposer T-1 |
| Compatibilité avec le canal électronique | 🟢 Bonne (saisie et arrivée quasi-simultanées) |
| Respect de l'art. 78 al. 2 | 🟠 Dégradé pour le canal papier |
| Respect de l'art. 78 al. 3 | 🟢 Sans ambiguïté |
| Impact sur le modèle | 🟠 Fusion des deux champs, ou l'un devient alias de l'autre |
| Risque juridique | 🔴 Incompatibilité possible avec l'art. 78 al. 2 pour le papier |

**Avantages** : simplicité maximale.
**Inconvénients** : **tension avec l'art. 78 al. 2** pour le canal
papier, où l'ordre d'arrivée doit refléter la réception effective,
non la saisie ultérieure.

### 4.2 Option b — Horodatage d'arrivée prime pour la chronologie ; horodatage de saisie pour la prise d'effet

**Description** : conserver les deux horodatages, mais **trancher la
règle de priorité** en faveur de l'arrivée pour la chronologie
(art. 78 al. 2) et en faveur de la saisie pour la prise d'effet
(art. 78 al. 3). Le numéro d'ordre porte la composante temporelle
de la saisie (art. 78 al. 4).

En pratique :
- deux déposants A et B dont les demandes arrivent respectivement à
  T-1 et T+1 : A a la **priorité** indépendamment de l'ordre de saisie ;
- A et B sont opposables aux tiers **chacun à leur instant de saisie
  respectif**.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 al. 2 | 🟢 Stricte |
| Conformité art. 78 al. 3 | 🟢 Stricte |
| Conformité art. 78 al. 4 (numéro d'ordre horodaté) | 🟢 La composante temporelle reste celle de la saisie |
| Complexité juridique | 🟠 Deux horodatages à expliquer |
| Complexité technique | 🟢 Déjà implémentée |
| Situation actuelle du code | 🟢 Compatible sans modification |

**Avantages** : concilie les deux alinéas de l'art. 78 ; reflète la
réalité opérationnelle (délai entre dépôt papier et saisie).
**Inconvénients** : deux horodatages à documenter et à expliquer
aux déposants.

### 4.3 Option c — Horodatage d'arrivée = horodatage de saisie opposable (canal unique strict)

**Description** : variante d'option a, mais applicable **uniquement
au canal électronique**. Pour le canal papier, on ajoute une étape
intermédiaire de saisie automatique à la réception (numérisation OCR
ou acceptation provisoire) qui pose simultanément les deux
horodatages. La saisie par l'agent ne modifie pas l'instant
d'arrivée, ce qui maintient la cohérence.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 al. 2, 3 | 🟢 Stricte si le processus automatique est infaillible |
| Dépendance technique | 🔴 Requiert un dispositif de saisie automatique fiable |
| Compatibilité guichet actuel | 🟠 Nécessite OCR ou queue électronique au guichet |
| Coût | 🟠 Modéré |

**Avantages** : simplicité juridique comme option a.
**Inconvénients** : dépendance à une automatisation rigoureuse ;
risque en cas de défaillance de la saisie automatique.

### 4.4 Option d — Trois horodatages distincts (réception / contrôle / validation)

**Description** : introduire un troisième horodatage formalisant
l'étape de contrôle de forme :
- `instant_arrivee` — réception physique ou électronique (art. 78 al. 2) ;
- `instant_controle_forme` — début du contrôle par le greffier ;
- `instant_saisie_opposable` — validation et saisie effective (art. 78
  al. 3).

La priorité chronologique reste fondée sur `instant_arrivee` ; la
prise d'effet sur `instant_saisie_opposable` ; l'horodatage
intermédiaire alimente l'audit et permet de mesurer les délais de
traitement.

| Dimension | Évaluation |
|-----------|------------|
| Granularité de traçabilité | 🟢 Maximale |
| Conformité art. 78 | 🟢 Stricte |
| Complexité | 🟠 Modérée — nouveau champ à ajouter au modèle |
| Valeur ajoutée | 🟠 Essentiellement statistique (mesurer les délais) |

**Avantages** : transparence totale sur le cycle de traitement.
**Inconvénients** : ajoute un horodatage supplémentaire sans valeur
juridique directe ; peut compliquer la présentation publique.

### 4.5 Option e — Horodatage d'arrivée déterminant la priorité, avec période de tolérance

**Description** : option b **plus** une règle de tolérance : si
`instant_saisie_opposable - instant_arrivee > seuil` (ex. 72 heures
ouvrables), la demande est signalée à l'autorité de validation et
nécessite une justification. Au-delà d'un seuil absolu (ex. 7 jours),
la demande est automatiquement rejetée ou réinitialisée.

Cette option vise à éviter les abus où une demande « dormante »
garderait indûment la priorité chronologique.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 | 🟢 Stricte |
| Robustesse opérationnelle | 🟢 **Élevée** — limite les effets de bord |
| Complexité juridique | 🟠 Introduit une notion de délai qui n'est pas expressément prévue par le décret |
| Risque | 🟠 Si le seuil est mal calibré, des demandes légitimes pourraient être rejetées |

**Avantages** : réduit le risque d'abus.
**Inconvénients** : la notion de « tolérance » ou « délai maximum »
n'est pas explicitement prévue par l'art. 78 — introduit une règle
qui mériterait une base réglementaire.

### 4.6 Option f — Règle de la soumission électronique prime ; canal papier converti

**Description** : si le portail électronique devient le canal de
référence, les demandes papier au guichet sont systématiquement
converties en soumission électronique par l'agent de saisie, qui les
enregistre **en temps réel**. Les deux horodatages coïncident pour
toute demande, quelle que soit l'origine.

Implique un changement opérationnel du guichet (saisie immédiate par
l'agent, avec accusé de dépôt horodaté remis au déposant).

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 | 🟢 Stricte |
| Compatibilité avec la pratique traditionnelle | 🔴 Bouleversement |
| Dépendance F2 (MFA agent) | 🟢 L'agent est authentifié fortement |
| Coût opérationnel | 🟠 Formation + équipement des guichets |
| Risque d'erreur humaine | 🔴 Si l'agent ne saisit pas immédiatement, le délai subsiste |

**Avantages** : élégance juridique.
**Inconvénients** : transformation des habitudes de travail ; risque
de désynchronisation en cas d'affluence.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Modifications |
|--------|---------------|
| a | Fusion des deux champs ou suppression de `instant_arrivee` |
| b | **Aucune** — le code actuel est déjà conforme |
| c | Processus de saisie automatique à implémenter |
| d | Ajout d'un champ `instant_controle_forme` |
| e | Ajout d'un contrôle de délai + logique de signalement |
| f | Modification du workflow guichet (saisie en temps réel) |

### 5.2 Impacts sur les tests

- Nouveau test : scénario de demandes simultanées reçues à des
  instants différents — vérification de la règle de priorité
  retenue.
- Nouveau test (option e) : dépassement de seuil → signalement ou
  rejet automatique.
- Compatibilité avec les tests existants : la séquence
  dépôt → contrôle → validation est déjà testée dans S1.

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 § 2.2 (formulaire inscription) | Explicitation de la règle de priorité |
| L2.2 Règles G-78.3, E-78.4 | Précision selon l'option retenue |
| L2.3 § 2.2 (matrice transitions) | Aucun impact sur la matrice |
| L2.6 scénarios A, B | Précision des deux horodatages dans la postcondition |
| L3.1 § 2.8 (Inscription) | Éventuel ajout / retrait de champs |
| L3.3 § 2 | Section « Distinction des deux horodatages » à consolider |
| L11 | Passage de `A9` à IMPLÉMENTÉ (arbitrée) |

### 5.4 Dépendances transversales

- **F5 (source de temps)** : les deux horodatages utilisent la même
  source. Si la source est fiable (F5 option a à f), les deux
  horodatages sont tous deux opposables.
- **F8 (politique d'indisponibilité)** : en cas d'indisponibilité
  entre arrivée et saisie, la règle de priorité arbitrée ici est
  déterminante pour le traitement des demandes en attente.

### 5.5 Impacts sur la recherche publique (art. 97)

Le certificat de recherche délivré à un instant T :
- reflète les inscriptions dont `instant_saisie_opposable ≤ T` et
  `statut ∈ STATUTS_FICHIER_PUBLIC` ;
- **n'affiche pas** les demandes dont `instant_arrivee ≤ T` mais
  `instant_saisie_opposable > T` (elles existent en base mais ne
  sont pas encore au fichier public).

Conséquence : un tiers peut faire une recherche à T0, recevoir un
certificat « négatif », et découvrir ensuite qu'une demande X
antérieure (en termes d'arrivée) a été saisie à T+1 et est devenue
opposable. **L'art. 78 al. 2 donne alors priorité à X** sur une
inscription que le tiers aurait faite à T+0, même si le certificat
à T0 ne mentionnait pas X.

Ce point doit être explicitement arbitré par le MO.

---

## 6. Tradeoffs synthétiques

| Critère | a (Unique) | b (Deux distincts) | c (Coïncidence forcée) | d (Trois horodatages) | e (Tolérance) | f (Saisie immédiate) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| Conformité art. 78 al. 2 (ordre d'arrivée) | Dégradée (papier) | Stricte | Stricte | Stricte | Stricte | Stricte |
| Conformité art. 78 al. 3 (prise d'effet) | Stricte | Stricte | Stricte | Stricte | Stricte | Stricte |
| Simplicité juridique | Maximale | Modérée | Élevée | Faible | Modérée | Élevée |
| Compatibilité canal papier | Faible | Élevée | Modérée | Élevée | Élevée | Modérée |
| Code actuel compatible | Non | **Oui** | Non | Non | Presque | Non |
| Valeur ajoutée d'audit | Faible | Moyenne | Faible | Élevée | Moyenne | Faible |
| Risque d'abus | Faible | Modéré | Faible | Modéré | **Faible** | Faible |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Règle de priorité** : en cas de litige entre deux déposants,
   quel horodatage détermine la priorité ? (`instant_arrivee` ou
   `instant_saisie_opposable` ?)
2. **Politique pour le canal papier** : l'agent de saisie dispose-t-il
   d'un délai maximum pour saisir un bordereau papier dans la base ?
3. **Politique pour le canal électronique** : la saisie est-elle
   automatique à la soumission, ou exige-t-elle une étape de
   validation manuelle ?
4. **Mention sur le certificat de recherche** : les deux horodatages
   sont-ils affichés, ou seulement celui de saisie opposable ?
5. **Traitement des demandes en cours** au moment d'une recherche :
   doit-on les mentionner au certificat sous une forme particulière
   (ex. « demande en cours de contrôle de forme, non opposable à ce
   jour ») ? (Risque d'interférence avec art. 86 — régime déclaratif.)
6. **Seuil de tolérance** (option e) : durée acceptable, procédure
   au-delà.
7. **Communication au déposant** : l'accusé de dépôt mentionne-t-il
   uniquement l'horodatage d'arrivée, ou précise-t-il que la prise
   d'effet aura lieu ultérieurement ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ autre : ______ |
| Horodatage déterminant la priorité | ☐ arrivée  ☐ saisie opposable  ☐ autre |
| Horodatage déterminant la prise d'effet | ☐ arrivée  ☐ saisie opposable  ☐ autre |
| Délai de tolérance (si option e) | _(à renseigner)_ |
| Affichage sur certificat de recherche | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Modèle `Inscription` : [L3.1 § 2.8](../L3_1_modele_donnees.md).
- Règles G-78.3 et C-78.2 : [L2.2 § 2.2](../L2_2_regles_validation.md).
- Flux de dépôt et validation : [L3.2 § 4.1](../L3_2_architecture_modulaire.md).
- Matrice statuts × transitions : [L2.3](../L2_3_matrice_statuts_transitions.md).
- Scénarios A et B : [L2.6 § 2 et § 3](../L2_6_scenarios_fonctionnels.md).
- Politique d'horodatage : [L3.3 § 2](../L3_3_horodatage_scellement.md).
- Fiche F5 (source de temps) : [F5_source_de_temps.md](F5_source_de_temps.md) — complémentaire.
- Fiche F8 (indisponibilité) : [F8_politique_indisponibilite.md](F8_politique_indisponibilite.md) — complémentaire.
- Ambiguïté TDR § 9.3 : [L11 — registre des hypothèses, zone A9](../L11_tracabilite_articles_76_97.md).
