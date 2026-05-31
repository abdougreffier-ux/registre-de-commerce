# Fiche MO — F12 — Cahier des charges (art. 83 — délégation éventuelle)

**Référence L11** : `A8`
**Articles fondateurs** : article 83 du décret 2021-033 (délégation
possible de la tenue du RSM).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `A8` — Cahier des charges art. 83 (si applicable) |
| Articles fondateurs | Art. 83 (délégation) |
| Statut actuel | **Non applicable à ce jour**. Le système est conçu pour être tenu directement par le Greffe. Aucun cahier des charges de délégation. |
| Dépendances | Transverse à toutes les autres fiches (les décisions MO des fiches F1 à F14 conditionneraient les clauses d'un cahier des charges). |
| Impact transverse | Totalité du système si délégation engagée. |

---

## 2. Contexte juridique

### 2.1 Exigence de l'article 83

> *« La tenue du registre peut être confiée à un organisme public ou
>   privé dans les conditions fixées par un cahier des charges
>   approuvé par arrêté du ministre de la Justice, sous le contrôle
>   du Président du Tribunal de commerce de Nouakchott. »*

### 2.2 Conditions cumulatives

Quatre conditions doivent être réunies si la tenue est déléguée :

1. **Organisme attributaire** : public ou privé, identifié.
2. **Cahier des charges** : document contractuel fixant les
   conditions.
3. **Arrêté du Ministre de la Justice** : approbation formelle du
   cahier des charges.
4. **Contrôle du Président du Tribunal de commerce de Nouakchott** :
   supervision permanente.

### 2.3 Articulation avec les principes du système

- **Art. 79 (conservation pérenne)** : l'organisme délégataire doit
  garantir la conservation pérenne, y compris en cas de fin du
  contrat.
- **Réversibilité (art. 83 implicite)** : le système doit pouvoir
  être repris par un autre organisme sans captivité technologique
  (L3.2 § 10).
- **§ 4.1 TDR (rôles applicatifs)** : le Greffe, le Président du
  Tribunal, l'auditeur conservent leurs rôles même en cas de
  délégation.

### 2.4 Risques juridiques en l'absence d'arbitrage

- **Risque de non-conformité** : si le MO décide une délégation sans
  cahier des charges arrêté, l'art. 83 n'est pas respecté.
- **Risque de captivité technologique** : si le système est conçu
  sans réversibilité, la délégation devient inamovible.
- **Risque de perte de contrôle** : si le cahier des charges ne
  formalise pas le contrôle du Président du Tribunal, la supervision
  n'est pas effective.

---

## 3. Situation actuelle dans le système

### 3.1 Tenue directe par défaut

Le système est conçu pour être **tenu directement par le Greffe du
Tribunal de commerce de Nouakchott**. Aucune délégation n'est à
arbitrage à ce stade.

### 3.2 Préparation à une éventuelle délégation

Le système a été conçu pour permettre, **si nécessaire**, une
délégation sans retravail majeur :

| Exigence art. 83 | Préparation intégrée au système |
|------------------|----------------------------------|
| Réversibilité | Code open à la cession ; base PostgreSQL exportable ; documentation L3 complète (cf. L3.2 § 10) |
| Contrôle du Président | Rôle `auditeur` exposé au niveau des habilitations (§ 4.1) |
| Cahier des charges | Documentation L2 + L3 peuvent servir de matière première à sa rédaction |
| Arrêté du Ministre | Indépendant du système (acte externe) |

### 3.3 Rôle applicatif `auditeur`

Le rôle `auditeur` existe déjà (L2.4 § 1) avec accès lecture seule au
journal d'audit et aux données. Il est **explicitement** associé au
rôle du Président du Tribunal ou du juge commis, comme prévu par
l'art. 83 in fine.

---

## 4. Options d'arbitrage

### 4.1 Option a — Tenue directe par le Greffe (aucune délégation)

**Description** : la tenue du RSM reste confiée au Greffe du Tribunal
de commerce de Nouakchott. Aucun cahier des charges n'est nécessaire
(art. 83 est sans objet). Cette fiche **devient sans objet** pour la
décision MO, mais reste conservée pour traçabilité.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 83 | 🟢 Sans objet (art. 83 ouvre une faculté, ne l'impose pas) |
| Gouvernance | 🟢 Directe |
| Coût | 🟢 Inclus dans l'exploitation Greffe |
| Complexité | 🟢 Faible |
| Évolutivité | 🟢 Une délégation reste possible ultérieurement |

**Avantages** : simplicité, continuité institutionnelle.
**Inconvénients** : aucun (c'est la situation de référence).

### 4.2 Option b — Délégation à un organisme public

**Description** : la tenue est déléguée à un **organisme public**
spécialisé (ex. Agence nationale de la modernisation de
l'administration, ANSI, ou un établissement public dédié). Le MO
prépare un cahier des charges approuvé par arrêté du Ministre de la
Justice. Le Président du Tribunal assure le contrôle.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 83 | 🟢 Stricte (si conditions cumulatives remplies) |
| Expertise technique | 🟢 Mutualisation possible |
| Gouvernance | 🟠 Double (MO + délégataire) |
| Coût pour l'État | 🟠 Budget entre administrations |
| Risque de captivité | 🟢 Faible (acteur public) |
| Temps de mise en place | 🔴 Long (arrêté + contractualisation) |

**Avantages** : tenue par un acteur public compétent ; mutualisation
d'infrastructure.
**Inconvénients** : circuit administratif lourd ; responsabilité
partagée.

### 4.3 Option c — Délégation à un organisme privé

**Description** : la tenue est déléguée à un **organisme privé**
(entreprise de services numériques, opérateur spécialisé en
registres numériques). Appel d'offres + cahier des charges + arrêté
du Ministre + contrôle du Président du Tribunal.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 83 | 🟢 Stricte (si conditions cumulatives remplies) |
| Expertise technique | 🟢 Compétence de marché |
| Gouvernance | 🟠 Public-privé |
| Coût | 🟠 Redevance contractuelle |
| Risque de captivité | 🔴 Modéré (à encadrer strictement par le cahier des charges) |
| Temps de mise en place | 🔴 Long (appel d'offres + contractualisation) |
| Contrôle démocratique | 🟠 À renforcer |

**Avantages** : souplesse et expertise marché.
**Inconvénients** : risque de captivité, nécessité d'un encadrement
rigoureux ; questions d'intérêt général.

### 4.4 Option d — Délégation partielle (exploitation technique seule)

**Description** : la **tenue juridique** reste au Greffe (actes
opposables, validation, décisions) mais l'**exploitation technique**
(hébergement, sauvegardes, supervision, correctifs) est déléguée à
un prestataire. Le cahier des charges est allégé (exploitation
seule).

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 83 | 🟠 À vérifier — la notion de « tenue » art. 83 inclut-elle l'exploitation technique ? |
| Expertise | 🟢 Prestataire spécialisé |
| Gouvernance | 🟢 Greffe conserve l'autorité juridique |
| Risque de captivité | 🟠 Modéré (clauses de réversibilité) |
| Temps de mise en place | 🟠 Modéré |
| Coût | 🟠 Modéré |

**Avantages** : compromis entre compétence et maîtrise.
**Inconvénients** : fondement juridique de la distinction « tenue
juridique » / « exploitation technique » à clarifier ; peut nécessiter
un arrêté explicite.

### 4.5 Option e — Consortium public-privé

**Description** : la tenue est confiée à une **structure mixte**
associant un organisme public (garant juridique) et un prestataire
privé (opérateur technique). Le cahier des charges formalise les
rôles respectifs.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 83 | 🟠 Conditions cumulatives applicables à la structure mixte |
| Gouvernance | 🔴 Complexe (tri-partite : MO + public + privé) |
| Expertise | 🟢 Combinée |
| Risque de captivité | 🟠 Partagé |
| Temps de mise en place | 🔴 Long |
| Coût | 🟠 Cumulé |

**Avantages** : meilleure des deux mondes théoriquement.
**Inconvénients** : complexité de gouvernance ; responsabilités
partagées plus difficiles à tracer.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Modifications |
|--------|---------------|
| a | Aucune |
| b à e | Aucune fonctionnalité interne à ajouter — la délégation est un acte de gouvernance, pas une fonctionnalité système. En revanche, le cahier des charges peut imposer des **clauses d'exploitation** qui se traduisent par des SLA (niveau de service), des rapports d'audit, des obligations de transfert — à documenter dans L3.2 § 10 (réversibilité) et dans le plan de continuité (F8). |

### 5.2 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L1 | Section sur la gouvernance à enrichir |
| L3.2 § 10 (réversibilité) | Clauses de transfert à préciser |
| L11 | Passage de `A8` à IMPLÉMENTÉ ou SANS OBJET |
| Cahier des charges (document externe) | À rédiger si option b, c, d, e |

### 5.3 Dépendances transversales

- **Toutes les fiches F1 à F14** : les décisions MO prises sur ces
  fiches **font partie intégrante** du cahier des charges si
  délégation. Le cahier des charges reprend et contractualise ces
  décisions.
- **L3.2 § 10 (réversibilité)** : les clauses de réversibilité du
  cahier des charges reprennent les éléments de cessibilité déjà
  documentés.
- **L2.4 (rôle auditeur)** : le contrôle du Président du Tribunal
  (art. 83) s'appuie sur ce rôle applicatif.

### 5.4 Impacts sur l'exploitation

Si délégation engagée (options b, c, d, e) :

- **SLA** (niveau de service) à contractualiser (disponibilité,
  performance, sécurité, reprise sur incident).
- **Rapports périodiques** du délégataire au Greffe et au Président
  du Tribunal.
- **Audit indépendant** annuel (recommandé).
- **Plan de réversibilité** documenté et testé.
- **Assurance responsabilité** du délégataire.
- **Clauses de sortie** : préavis, transfert des données, des
  matériels et des personnes.

---

## 6. Tradeoffs synthétiques

| Critère | a (Tenue directe) | b (Org. public) | c (Org. privé) | d (Délégation partielle) | e (Consortium) |
|---------|:-:|:-:|:-:|:-:|:-:|
| Conformité art. 83 | Sans objet | Stricte | Stricte | À clarifier | Stricte |
| Simplicité de gouvernance | Maximale | Modérée | Modérée | Élevée | Faible |
| Expertise technique | Variable | Élevée | Élevée | Élevée | Très élevée |
| Risque de captivité | Nul | Faible | Modéré | Modéré | Partagé |
| Coût de mise en place | Nul | Modéré | Élevé | Modéré | Élevé |
| Temps de mise en place | Immédiat | Long | Long | Modéré | Très long |
| Contrôle démocratique | Maximal | Élevé | Modéré | Élevé | Modéré |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Intention du MO** : souhaite-t-il réellement déléguer, ou la
   fiche est-elle sans objet ?
2. **Motifs d'une délégation éventuelle** : expertise, coût,
   disponibilité, facteur politique ?
3. **Organisme candidat** identifié (si option b, c, d, e) ?
4. **Dotation budgétaire** : capacité à supporter une redevance ?
5. **Calendrier** : horizon de la délégation (immédiat, moyen
   terme) ?
6. **Contrôle du Président du Tribunal** : modalités concrètes
   (rapports, accès direct, audits) ?
7. **Clauses de sortie / réversibilité** envisagées ?
8. **Articulation avec l'arrêté d'application F9** : l'arrêté peut-il
   ou doit-il se cumuler avec un cahier des charges ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ autre : ______ |
| Organisme délégataire (si applicable) | _(à renseigner)_ |
| Portée de la délégation (totale / partielle) | _(à renseigner)_ |
| Durée contractuelle | _(à renseigner)_ |
| SLA principaux | _(à renseigner)_ |
| Modalités du contrôle du Président du Tribunal | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence de l'arrêté du Ministre de la Justice | _(à renseigner)_ |

---

## 9. Renvois croisés

- Réversibilité (art. 83) : [L3.2 § 10](../L3_2_architecture_modulaire.md).
- Rôle auditeur (§ 4.1) : [L2.4 § 1](../L2_4_roles_operations.md).
- Toutes les fiches F1 à F14 comme matière du cahier des charges.
- Registre : [L11](../L11_tracabilite_articles_76_97.md).
