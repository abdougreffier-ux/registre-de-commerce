# Fiche MO — F10 — Durée maximale d'inscription (art. 85)

**Référence L11** : `A3`
**Articles fondateurs** : article 85 (contenu d'inscription) ; art. 91
(renouvellement) ; TDR § 9.3 (zone d'ambiguïté signalée).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `A3` — Durée maximale d'inscription |
| Articles fondateurs | Art. 85 (durée déclarée par le requérant) ; art. 91 (renouvellement fondé sur la durée initiale) |
| Statut actuel | **Aucune borne supérieure**. Le champ `Inscription.duree_en_jours` accepte tout entier ≥ 1. |
| Dépendances | F7 (horodatage de saisie détermine la date d'expiration) ; F11 (la politique tarifaire peut dépendre de la durée). |
| Impact transverse | Toutes les inscriptions. |

---

## 2. Contexte juridique

### 2.1 Silence du décret sur la borne supérieure

L'article 85 demande que l'inscription mentionne « la durée pour
laquelle l'inscription est requise » et « sa date d'expiration ». Le
décret ne fixe **pas** de borne supérieure — ni plancher au-dessus
d'un jour. L'article 91 prévoit le renouvellement pour une durée
égale à la durée initiale, sans limiter le nombre de renouvellements.

### 2.2 Ambiguïté signalée au TDR § 9.3

> *« Article 85 : la durée pour laquelle l'inscription est requise
>   n'est pas plafonnée par le texte. »*

Le TDR adopte par défaut la durée **déclarée par le requérant**, sans
contrôle automatique de plafond. Il signale cette position comme
hypothèse de mise en œuvre à arbitrer par le MO.

### 2.3 Enjeux juridiques et opérationnels

- **Sécurité juridique** : une inscription à durée illimitée est
  théoriquement admise par le silence du texte, mais peut poser des
  questions d'opposabilité dans le très long terme (archives,
  évolutions légales).
- **Charge du fichier public** : sans plafond, le fichier public peut
  accumuler des inscriptions de très longue durée, affectant les
  performances de recherche art. 94-97.
- **Effet utile** : une durée déraisonnablement courte (ex. 1 jour)
  ou déraisonnablement longue (ex. 99 ans) peut être contestée sur
  le fondement de l'abus de droit.

### 2.4 Risques juridiques en l'absence d'arbitrage

- **Risque cardinal** : un déposant malveillant pourrait déclarer une
  durée arbitraire (ex. 100 ans) sans base métier, ce qui produirait
  une inscription valide en droit mais problématique en pratique.
- **Risque d'incohérence avec la pratique** bancaire ou commerciale,
  si les durées habituelles sont très courtes (6 mois pour un prêt
  court terme) ou très longues (15 ans pour un nantissement de fonds
  de commerce).

---

## 3. Situation actuelle dans le système

### 3.1 Contraintes actuelles

| Contrainte | Valeur |
|-----------|--------|
| Minimum | 1 jour (`PositiveIntegerField` + validation serializer `min_value=1`) |
| Maximum | **Aucun** — entier sans borne |
| Contrôle bloquant | Aucun |
| Avertissement UI | Aucun |
| Référence code | [apps/inscriptions/models.py](../../backend/apps/inscriptions/models.py) |

### 3.2 Interaction avec le renouvellement

Règle D-91.2 (L2.2 § 2.11) : la durée de prorogation lors d'un
renouvellement est égale à la **durée initiale** (`duree_en_jours`)
— hypothèse A3 adoptée par défaut. Sans plafond, un renouvellement
peut donc étendre l'inscription indéfiniment.

---

## 4. Options d'arbitrage

### 4.1 Option a — Aucune borne (statu quo — durée au choix du déposant)

**Description** : le décret est strictement suivi : la durée est
celle déclarée par le requérant, sans borne. Toute inscription est
recevable quelle que soit la durée.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 85 | 🟢 Stricte (silence du texte respecté) |
| Risque d'abus | 🔴 Modéré — durée déraisonnable possible |
| Complexité | 🟢 Nulle (aucun contrôle) |
| Compatibilité art. 86 | 🟢 Régime déclaratif respecté — aucun contrôle au fond |
| Impact performance | 🟠 Croissant avec le temps |

**Avantages** : conformité stricte au silence du texte ; simplicité.
**Inconvénients** : risque d'inscriptions à durée déraisonnable.

### 4.2 Option b — Plafond maximum fixe arbitré par le MO

**Description** : le MO arbitre un plafond (ex. 10 ans, 15 ans,
30 ans). Toute durée demandée au-delà est **rejetée** au dépôt avec
motif spécifique (à ajouter au registre L2.5). Le plafond vaut pour
l'inscription initiale ; le renouvellement reste possible sans limite
de nombre de renouvellements.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 85 | 🟠 Ajoute une règle non expresse (à défendre juridiquement) |
| Compatibilité art. 86 | 🟠 Contrôle de forme — admissible si plafond est connu d'avance |
| Simplicité | 🟢 |
| Prévisibilité | 🟢 Élevée |
| Risque juridique | 🟠 Plafond pourrait être contesté si non fondé sur une disposition expresse |

**Avantages** : maîtrise opérationnelle.
**Inconvénients** : introduction d'une règle ajoutée au décret —
fondement juridique à clarifier (arrêté d'application, F9 option d).

### 4.3 Option c — Plafond différencié par nature de sûreté

**Description** : variante de l'option b avec un plafond différent
selon la nature (art. 76) :
- Sûretés courantes (stocks, créances, compte bancaire) : 3 ans par
  défaut.
- Sûretés structurelles (fonds de commerce, outillage, droits
  associés) : 10 ans par défaut.
- Privilèges (Trésor, douanes, fiscal, social) : durée alignée sur la
  prescription fiscale / sociale.
- Droits de propriété intellectuelle : durée alignée sur la durée de
  protection du droit sous-jacent.

| Dimension | Évaluation |
|-----------|------------|
| Pertinence métier | 🟢 Élevée |
| Complexité | 🟠 Table de plafonds à maintenir par le MO |
| Risque juridique | 🟠 Nouvelle règle non expresse, mais mieux justifiée |
| Impact code | 🟠 Contrôle par nature + table paramétrable |

**Avantages** : adaptation aux réalités métier.
**Inconvénients** : complexité de gouvernance ; nécessite une
fondement réglementaire (arrêté).

### 4.4 Option d — Avertissement sans blocage (soft cap)

**Description** : aucun plafond bloquant, mais un **avertissement**
affiché au déposant lorsque la durée dépasse un seuil indicatif
(ex. 10 ans). Le déposant peut maintenir sa saisie sur confirmation
explicite. L'avertissement est tracé au journal d'audit.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 85 | 🟢 Stricte (aucun contrôle bloquant) |
| Compatibilité art. 86 | 🟢 Respectée |
| Prévention des abus | 🟠 Partielle (dépend de la conscience du déposant) |
| Complexité | 🟢 Faible |
| Auditabilité | 🟢 Avertissement tracé |

**Avantages** : conformité stricte + filet de sécurité pédagogique.
**Inconvénients** : ne bloque pas les abus volontaires.

### 4.5 Option e — Plafond paramétrable par l'administrateur fonctionnel

**Description** : la durée plafond est un **paramètre configurable**
par l'administrateur fonctionnel (admin Django), avec un défaut
retenu par le MO et modifiable au fil du temps selon l'expérience
d'exploitation. Les paramétrages sont tracés au journal d'audit.

| Dimension | Évaluation |
|-----------|------------|
| Flexibilité | 🟢 Élevée |
| Prévisibilité | 🟠 Le plafond peut varier — à publier clairement |
| Complexité de gouvernance | 🟠 Le MO doit superviser les modifications |
| Conformité art. 86 | 🟢 Respectée |
| Impact code | 🟠 Nouveau modèle `ParametreSysteme` ou équivalent |

**Avantages** : adaptabilité sans évolution du code.
**Inconvénients** : responsabilité d'exploitation accrue ; traçabilité
des évolutions critiques.

### 4.6 Option f — Double limite (durée initiale + cumul renouvellements)

**Description** : combine un plafond sur la durée initiale (ex. 10
ans) **et** un plafond sur le cumul des durées après renouvellements
(ex. 30 ans cumulés). Au-delà du cumul, le renouvellement est
refusé — l'inscription arrive à échéance naturelle et doit donner
lieu à une nouvelle inscription initiale si le besoin subsiste.

| Dimension | Évaluation |
|-----------|------------|
| Prévention des abus | 🟢 Élevée |
| Conformité art. 91 | 🟠 Ajoute une règle de plafond non expresse au renouvellement |
| Complexité | 🔴 Modérée — calcul cumulatif à implémenter |
| Impact art. 79 | 🟢 Préservé (données conservées après expiration naturelle) |

**Avantages** : contre l'effet « inscriptions perpétuelles ».
**Inconvénients** : complexité accrue ; nouvelle règle non expresse.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Modifications |
|--------|---------------|
| a | Aucune |
| b | Ajout d'un plafond dans serializer + service `creer_demande` |
| c | Table de plafonds par nature + contrôle croisé |
| d | Mécanisme d'avertissement + confirmation explicite + audit |
| e | Modèle `ParametreSysteme` + admin `EditionRestreinteAdmin` |
| f | Contrôle cumulatif dans `appliquer_renouvellement` |

### 5.2 Impacts sur les tests

- Nouveau test : durée au-delà du plafond (si option b, c, e, f) →
  rejet avec motif dédié.
- Nouveau test : avertissement émis (option d).
- Nouveau test : cumul des durées (option f).
- Compatibilité avec S1 : scénarios actuels avec 365 jours restent
  valides.

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 § 2.1 (durée en jours) | Préciser le plafond arbitré |
| L2.2 Règle B-85.* | Ajouter une règle sur la durée |
| L2.5 | Nouveau motif de rejet potentiel : `duree_hors_limite` (à créer si option b, c, e, f) |
| L11 | Passage de `A3` à IMPLÉMENTÉ |

### 5.4 Dépendances transversales

- **F7** : la date d'expiration découle de l'horodatage de saisie +
  durée. Si F7 retient une politique où les deux horodatages sont
  distincts, l'effet sur la date d'expiration est prévisible.
- **F11** : la politique tarifaire (si proportionnelle à la durée)
  dépend de la plage retenue ici.

---

## 6. Tradeoffs synthétiques

| Critère | a (Aucune borne) | b (Plafond fixe) | c (Plafond par nature) | d (Avertissement) | e (Paramétrable) | f (Double limite) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| Conformité stricte art. 85 | Maximale | Modérée | Modérée | Maximale | Maximale | Modérée |
| Prévention des abus | Nulle | Élevée | Élevée | Modérée | Variable | **Maximale** |
| Complexité code | Nulle | Faible | Modérée | Faible | Modérée | Élevée |
| Prévisibilité pour le déposant | Maximale | Élevée | Modérée | Élevée | Faible | Modérée |
| Fondement juridique de la règle ajoutée | N/A | À justifier | À justifier | N/A | À justifier | À justifier |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Analyse des pratiques** : quelles durées sont effectivement
   demandées dans les registres comparables (RCCM, registres OHADA) ?
2. **Fondement juridique** d'un éventuel plafond (options b, c, e, f) :
   arrêté d'application (F9), circulaire du Ministre de la Justice,
   convention de service ?
3. **Durées types par nature** (option c) : table à fournir par le MO.
4. **Valeur par défaut** du plafond paramétrable (option e).
5. **Politique de transition** pour les inscriptions déjà en cours
   avec des durées au-delà du plafond retenu.
6. **Règle en cas d'absence de durée** déclarée par le déposant :
   refus, ou durée par défaut ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ autre : ______ |
| Plafond arbitré (si applicable) | _(à renseigner — en jours ou en années)_ |
| Table par nature (option c) | _(à renseigner)_ |
| Plafond cumulatif (option f) | _(à renseigner)_ |
| Fondement juridique | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Modèle `Inscription.duree_en_jours` : [L3.1 § 2.8](../L3_1_modele_donnees.md).
- Règle B-85.* : [L2.2 § 2.6](../L2_2_regles_validation.md).
- Service d'attribution de la date d'expiration : [L3.2 § 4.1](../L3_2_architecture_modulaire.md).
- Fiche F7 (horodatages) : [F7_distinction_horodatages.md](F7_distinction_horodatages.md).
- Fiche F11 (paiement) : [F11_politique_tarifaire.md](F11_politique_tarifaire.md).
- Registre : [L11](../L11_tracabilite_articles_76_97.md).
