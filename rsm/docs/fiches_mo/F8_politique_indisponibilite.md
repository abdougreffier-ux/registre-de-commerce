# Fiche MO — F8 — Politique d'indisponibilité du système

**Référence L11** : `A4`
**Articles fondateurs** : article 78 alinéa 2 (ordre d'arrivée) ;
TDR § 5.3 (disponibilité et continuité), § 9.2 (risque R4 identifié).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `A4` — Politique d'indisponibilité (cf. risque R4) |
| Articles fondateurs | Art. 78 al. 2 (ordre d'arrivée) ; TDR § 5.3 ; risque R4 du L11 (« Indisponibilité et ordre d'arrivée ») |
| Statut actuel | **Non arbitrée.** Aucun mécanisme spécifique en cas d'indisponibilité. La tâche `expirer_inscriptions` reste exécutable manuellement après rétablissement. |
| Dépendances | F5 (source de temps) ; F7 (distinction horodatages) ; fortement liée à la cohérence de l'art. 78 al. 2 en cas d'interruption. |
| Impact transverse | Toutes les opérations d'écriture : dépôt, validation, rejet, modification, renouvellement, radiation, recherche publique. |

---

## 2. Contexte juridique

### 2.1 Exigence de l'article 78 alinéa 2

> *« Les demandes sont enregistrées dans l'ordre de leur date
>   d'arrivée. »*

Cet impératif ne souffre **aucune exception** liée à un incident
technique. En cas d'indisponibilité du système, l'ordre d'arrivée doit
néanmoins être préservé.

### 2.2 Exigence du TDR § 5.3

> *« Disponibilité cible 99,5 % par an en dehors des interruptions
>   programmées, compte tenu du rôle juridique du Registre. Plan de
>   continuité documenté ; procédure de bascule en cas de défaillance
>   majeure. Objectifs indicatifs : RPO ≤ 1 heure, RTO ≤ 4 heures,
>   au regard de la valeur juridique des horodatages. Procédure
>   spécifique en cas d'indisponibilité : les demandes reçues pendant
>   la période d'indisponibilité sont horodatées à leur date d'arrivée
>   effective et non à la date de rétablissement du service. »*

### 2.3 Risque signalé au TDR § 9.2 (R4)

> *« Indisponibilité du système : peut affecter le rang chronologique
>   d'une inscription et créer du contentieux. »*

### 2.4 Cas de figure en cause

| Situation | Exemple | Durée typique |
|-----------|---------|:-------------:|
| Indisponibilité programmée | Maintenance planifiée, mises à jour | Quelques heures |
| Indisponibilité partielle | Service API en panne, guichet papier disponible | Minutes à heures |
| Indisponibilité totale | Panne majeure, coupure réseau, incident serveur | Minutes à jours |
| Indisponibilité partielle inverse | Serveur OK, portail externe down | Minutes à heures |

### 2.5 Risques juridiques en l'absence d'arbitrage

- **Risque cardinal** : en cas d'incident, les demandes reçues
  pendant l'indisponibilité peuvent être saisies à la reprise avec
  l'horodatage de reprise, et non celui d'arrivée effective →
  **contentieux de priorité** selon art. 78 al. 2.
- **Risque de perte de données** : pour le canal électronique, si les
  soumissions ne sont pas mises en file d'attente ou archivées, elles
  peuvent être **perdues** sans trace de leur arrivée.
- **Risque de contestation de la validité** des inscriptions passées
  si l'horodatage n'est pas fiable sur l'intervalle d'indisponibilité.
- **Risque de non-conformité au TDR § 5.3** si aucune procédure
  documentée n'est en place.

---

## 3. Situation actuelle dans le système

### 3.1 Mécanismes existants

| Mécanisme | État |
|-----------|------|
| Disponibilité cible (99,5 %) | Objectif documenté en L1, non instrumenté |
| RPO / RTO | Objectifs indicatifs (≤ 1 h / ≤ 4 h) documentés, non instrumentés |
| Sauvegardes automatisées | Prévues par déploiement, à câbler selon infra |
| Procédure de bascule | Non documentée |
| File d'attente en cas d'indisponibilité du portail | Inexistante |
| Horodatage rétrospectif à la reprise | Absent |
| Journal de disponibilité | Absent |
| Notification aux déposants | Absente |

### 3.2 Ce qui fonctionne déjà partiellement

- L'**horloge serveur** reste fiable tant que le serveur fonctionne ;
  seule une panne logicielle ou matérielle peut affecter les
  horodatages internes.
- Les **transactions atomiques** (L3.5 § 3.2) garantissent qu'une
  opération interrompue est entièrement rollback — pas d'état partiel.
- Le **chaînage du journal d'audit** reste intègre après un incident
  (testé par `verifier_chaine()`).

### 3.3 Ce qui manque

- Dispositif de **mise en attente** des demandes soumises
  électroniquement pendant l'indisponibilité du service central.
- Procédure de **reprise horodatée** (chaque demande reçue pendant
  l'interruption doit être ré-injectée avec son horodatage d'arrivée
  effectif).
- Journal d'**incidents de service** (début / fin, type, impact
  estimé).
- **Accusé de dépôt alternatif** (papier au guichet, email
  automatique côté portail) portant horodatage indépendant.

### 3.4 Périmètre impacté

| Canal | Sensibilité à l'indisponibilité |
|-------|:-------------------------------:|
| Guichet papier | 🟠 Dépôts physiques acceptés mais saisie différée |
| Portail électronique | 🔴 Aucune soumission possible sans file d'attente |
| Recherche publique | 🟠 Inaccessible pendant l'incident |
| Expiration automatique | 🟢 Tâche programmée, rattrapage au réveil |

---

## 4. Options d'arbitrage

### 4.1 Option a — File d'attente électronique avec horodatage de réception externe

**Description** : en amont du système central, un **dispositif de
collecte** (ex. reverse proxy, service mail, gateway API) accepte les
soumissions électroniques et leur attribue un **horodatage de
réception** indépendant du système central. Les demandes sont mises
en file d'attente persistante (SQLite / fichier / file AMQP). À la
reprise, le système central les ingère dans l'ordre d'arrivée avec
leur horodatage d'origine.

Côté guichet papier, un **accusé de dépôt papier** horodaté par un
dispositif de confiance (horodateur mécanique ou tampon avec date et
heure) est remis au déposant ; l'agent saisit ultérieurement avec
l'horodatage du papier.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 al. 2 | 🟢 **Stricte** — ordre d'arrivée préservé |
| Conformité TDR § 5.3 (« horodatées à leur date d'arrivée effective ») | 🟢 Stricte |
| Coût de déploiement | 🟠 Modéré — composant de collecte + persistance |
| Dépendance | 🟠 Nouveau composant à superviser |
| Résilience | 🟢 Élevée — la collecte est un composant simple, indépendant |
| Complexité | 🟠 Deux systèmes à maintenir (collecte + central) |
| Risque d'incohérence | 🟠 Modéré — la synchronisation de l'horloge du composant de collecte avec le central doit être garantie (lien avec F5) |
| Exploitation | 🟠 Supervision de deux composants |

**Avantages** : préserve strictement l'ordre d'arrivée ; tolère des
indisponibilités longues.
**Inconvénients** : deuxième composant à exploiter ; dépendance à la
fiabilité du dispositif de collecte.

### 4.2 Option b — Rejet temporaire avec préservation de la chronologie par accusé papier

**Description** : en cas d'indisponibilité, le portail électronique
est mis en mode **dégradé** : toute nouvelle soumission reçoit une
réponse HTTP 503 (Service Unavailable) avec message explicite. Les
déposants sont redirigés vers le **guichet papier** qui, lui, reste
opérationnel. Au guichet, un **accusé papier** horodaté
(tampon + signature agent) est remis. À la reprise, les demandes
papier sont saisies normalement avec leur horodatage papier comme
`instant_arrivee`.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 al. 2 | 🟢 Préservée via accusé papier |
| Conformité TDR § 5.3 | 🟠 Partielle — perd les déposants sans accès au guichet |
| Coût de déploiement | 🟢 **Très faible** |
| Dépendance | 🟢 Aucune infrastructure supplémentaire |
| Accessibilité | 🔴 Déplacement au guichet obligatoire pendant incident |
| Risque de contentieux | 🟠 Déposants distants privés de canal |

**Avantages** : simplicité, coût nul.
**Inconvénients** : exclut les déposants qui ne peuvent accéder au
guichet ; contraire à l'esprit de dématérialisation.

### 4.3 Option c — Mode lecture seule + journal des tentatives

**Description** : en cas d'incident majeur, le système bascule en
**mode lecture seule** (recherche publique encore disponible si
possible, consultation d'inscriptions OK) tandis que toute tentative
d'écriture retourne 503 avec un **identifiant unique de tentative**.
Les déposants dont la tentative a produit un identifiant peuvent
ressoumettre leur demande à la reprise ; le système accepte alors
l'horodatage d'arrivée initial (présent dans l'identifiant de
tentative) plutôt que l'horodatage de resoumission.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 al. 2 | 🟠 Dépend de la bonne foi du déposant qui doit ressoumettre avec l'identifiant |
| Conformité TDR § 5.3 | 🟠 Partielle |
| Coût | 🟢 Faible |
| Résilience | 🟠 Aux déposants à agir |
| Complexité | 🟠 Gestion des identifiants de tentative |
| Risque de fraude | 🔴 Des tentatives non renouvelées pourraient être utilisées abusivement (prioritisation a posteriori) |

**Avantages** : simple à mettre en œuvre côté serveur.
**Inconvénients** : report de la responsabilité sur les déposants ;
risque de fraude.

### 4.4 Option d — Architecture haute disponibilité (HA) active / active

**Description** : investir dans une architecture techniquement
résiliente : deux instances du système sur sites distincts, avec
réplication synchrone ou quasi-synchrone de la base de données,
bascule automatique sans interruption (RTO ≈ 0).

Le dispositif de file d'attente devient superflu car le service
central reste disponible même en cas de défaillance d'un site.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 al. 2 | 🟢 **Stricte** — pas d'interruption |
| Conformité TDR § 5.3 | 🟢 Objectifs RPO / RTO maximaux |
| Coût | 🔴 **Élevé** — double infrastructure |
| Complexité | 🔴 Élevée — gestion de la réplication, cohérence du chaînage d'audit sous réplication |
| Dépendance | 🟠 Expertise haute disponibilité |
| Adéquation à la taille du RSM | 🟠 Dimensionnement à évaluer |

**Avantages** : absence d'interruption perceptible par l'utilisateur.
**Inconvénients** : coût élevé, complexité opérationnelle (la
réplication du journal d'audit chaîné doit être soigneusement
conçue).

### 4.5 Option e — Architecture haute disponibilité active / passive + file d'attente

**Description** : instance principale + instance de secours en mode
actif/passif avec bascule manuelle ou automatique (RTO ≈ minutes).
Couplé avec option a (file d'attente en amont) pour gérer les
microcoupures durant la bascule.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 al. 2 | 🟢 Stricte |
| Conformité TDR § 5.3 | 🟢 Élevée |
| Coût | 🟠 Modéré à élevé |
| Complexité | 🟠 Modérée |
| Adéquation | 🟢 Bonne — équilibre coût / résilience |

**Avantages** : compromis coût / fiabilité.
**Inconvénients** : bascule peut créer une brève indisponibilité.

### 4.6 Option f — Dispositif d'accusé électronique horodaté par tiers (TSA)

**Description** : chaque soumission électronique reçoit en temps réel
un **accusé signé par une autorité d'horodatage tierce** (TSA
RFC 3161). L'accusé porte un identifiant de soumission et un
horodatage tiers. Même si le système central est indisponible et que
la soumission n'est pas immédiatement traitée, l'accusé fournit une
preuve d'arrivée opposable.

À la reprise, les soumissions sont ingérées selon l'ordre attesté par
les horodatages de la TSA.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 78 al. 2 | 🟢 Stricte (ordre attesté par TSA) |
| Valeur probante de l'accusé | 🟢 **Maximale** |
| Coût | 🟠 Modéré (licence TSA + intégration) |
| Dépendance | 🔴 TSA externe (disponibilité critique) |
| Mutualisation F5 / F4 | 🟢 Oui si TSA commune |
| Résilience | 🟢 L'accusé reste valide même si le système central est défaillant |

**Avantages** : opposabilité maximale de l'horodatage d'arrivée,
même en incident.
**Inconvénients** : dépend de la TSA (qui doit elle-même être
disponible).

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Modifications |
|--------|---------------|
| a | Nouveau service de collecte (file d'attente persistante) + ingestor à la reprise |
| b | Page « service indisponible » + procédure guichet documentée |
| c | Gestion d'identifiants de tentative + endpoint de resoumission |
| d | Réplication base + cohérence chaînage audit |
| e | Options a + infrastructure HA passive |
| f | Intégration TSA + modèle `AccusuReception` à ajouter |

### 5.2 Impacts sur les tests

- Nouveau test : simulation d'indisponibilité du service central
  pendant N secondes → vérification que l'ordre d'arrivée est préservé à la reprise.
- Nouveau test : soumissions concurrentes via file d'attente (option a)
  → vérification de l'ingestion ordonnée.
- Nouveau test : comportement du client en cas de 503 (option b, c).

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L1 § 7 Plan d'étapes | Ajout d'une étape « Plan de continuité d'activité » |
| L2.1 § 1.2 (canaux d'arrivée) | Mention du canal de secours |
| L2.3 Messages système | Ajout du message `systeme.indisponibilite` + `systeme.reprise` |
| L2.5 § 9.1 | Nouveaux messages techniques |
| L3.2 § 9 | Section « Disponibilité et résilience » à enrichir |
| L3.5 | Nouveau rempart « continuité » |
| L11 | Passage de `A4` à IMPLÉMENTÉ ; évolution de R4 |

### 5.4 Dépendances transversales

- **F5 (source de temps)** : l'horodatage du composant de collecte
  (option a) ou de la TSA (option f) doit être synchronisé avec la
  source officielle.
- **F7 (distinction horodatages)** : l'horodatage d'arrivée posé par
  la file d'attente ou la TSA sert de `instant_arrivee` au moment de
  l'ingestion, sans écraser la chronologie réelle.
- **F6 (scellement)** : l'ingestion différée ne doit pas rompre le
  chaînage du journal d'audit (à tester rigoureusement).

### 5.5 Impacts sur l'exploitation

- **Plan de continuité documenté** (PCA) — requis par TDR § 5.3.
- **Procédure de bascule** documentée (qui déclenche, qui valide,
  qui notifie).
- **Tests de restauration** périodiques (§ 5.3 TDR — « au moins
  semestriels, documentés »).
- **Communication de crise** : modèle de message aux utilisateurs en
  cas d'interruption, délai de rétablissement annoncé.
- **Journal d'incidents** : registre des indisponibilités, cause,
  durée, impact.

---

## 6. Tradeoffs synthétiques

| Critère | a (File d'attente) | b (503 + papier) | c (Identifiants tentative) | d (HA active/active) | e (HA passive + file) | f (TSA) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| Conformité art. 78 al. 2 | Stricte | Dégradée pour externes | Dépend de la bonne foi | Stricte | Stricte | Stricte |
| Conformité TDR § 5.3 | Élevée | Partielle | Partielle | **Maximale** | Élevée | Élevée |
| Coût initial | Modéré | Très faible | Faible | **Très élevé** | Élevé | Modéré |
| Coût récurrent | Modéré | Nul | Faible | Élevé | Modéré | Modéré (licence TSA) |
| Complexité d'exploitation | Modérée | Très faible | Faible | Élevée | Modérée | Modérée |
| Accessibilité pendant incident | Bonne | Faible (guichet) | Partielle | **Maximale** | Bonne | Bonne |
| Dépendance externe | Nouveau composant | Guichet physique | Déposants | Expertise HA | HA + composant | TSA |
| Valeur probante de l'accusé | Interne | Papier | Interne | Immédiate | Mixte | **Maximale** |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Objectifs RPO et RTO** définitifs (proposés indicativement par
   le TDR à ≤ 1 h et ≤ 4 h — à confirmer ou réviser).
2. **Canal de secours officiellement retenu** : guichet papier
   uniquement, ou combinaison avec file d'attente électronique ?
3. **Budget** disponible pour l'infrastructure de résilience.
4. **Dimensionnement attendu** des volumes de soumissions
   électroniques (utile pour décider entre a, d, e).
5. **Autorité déclenchant la bascule** : automatique ou manuelle ?
   Qui valide le basculement vers le plan de continuité ?
6. **Seuil d'indisponibilité** à partir duquel le plan de continuité
   s'active (ex. 5 min, 30 min, 1 h) ?
7. **Politique de communication** aux utilisateurs pendant
   l'incident.
8. **Conservation des accusés** pendant l'indisponibilité : durée
   minimale, format, preuve.
9. **Gestion des soumissions en doublon** (un déposant impatient
   renvoie sa demande) : règle de déduplication.
10. **Obligations réglementaires sectorielles** éventuelles (banque,
    notariat) qui imposeraient un niveau de disponibilité supérieur.

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ autre : ______ |
| RPO arbitré | _(à renseigner)_ |
| RTO arbitré | _(à renseigner)_ |
| Canal de secours | _(à renseigner)_ |
| Autorité de bascule | _(à renseigner)_ |
| Seuil de déclenchement du PCA | _(à renseigner)_ |
| Règle de déduplication | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Objectifs disponibilité / continuité : [L1 § 5](../L1_note_de_cadrage.md).
- TDR § 5.3 (consolidé) : [L3.2 § 9](../L3_2_architecture_modulaire.md).
- Source de temps (F5) : [F5_source_de_temps.md](F5_source_de_temps.md) — complémentaire.
- Distinction horodatages (F7) : [F7_distinction_horodatages.md](F7_distinction_horodatages.md) — complémentaire.
- Scellement (F6) : [F6_scellement_cryptographique.md](F6_scellement_cryptographique.md) — chaînage d'audit sous incident.
- Risque R4 : [L11](../L11_tracabilite_articles_76_97.md).
