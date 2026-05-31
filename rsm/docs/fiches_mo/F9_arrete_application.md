# Fiche MO — F9 — Arrêté d'application (art. 8, 81, 84)

**Référence L11** : `A1`
**Articles fondateurs** : articles 8, 81, 84 du décret 2021-033.

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `A1` — Arrêté d'application non fourni |
| Articles fondateurs | Art. 8 (arrêté du ministre de la Justice), art. 81 (procédure dématérialisée d'inscription, modification et radiation), art. 84 (voie électronique) |
| Statut actuel | **Arrêté non publié / non communiqué**. Paramétrages par défaut retenus, explicitement signalés comme hypothèses. |
| Dépendances | Impacte potentiellement toutes les autres fiches — l'arrêté peut préciser la source de temps, le régime de signature, les formats, le paiement, etc. |
| Impact transverse | Transversal : l'arrêté peut modifier la portée de l'ensemble du système. |

---

## 2. Contexte juridique

### 2.1 Renvois explicites du décret

Trois articles du décret renvoient à un arrêté :

| Article | Objet du renvoi |
|---------|-----------------|
| Art. 8 | Dispositions générales — règles d'organisation fixées par arrêté du ministre de la Justice |
| Art. 81 | Procédure dématérialisée d'inscription, de modification et de radiation |
| Art. 84 | Voie électronique |

### 2.2 Avertissement du TDR

> *« Le texte fondateur renvoie à un arrêté (articles 8, 81, 84) pour
>   la fixation des règles relatives à la procédure dématérialisée
>   d'inscription, de modification et de radiation, ainsi qu'à la
>   procédure de recherche. Cet arrêté d'application n'est pas joint
>   aux présents TDR. Le prestataire sera tenu, dès la publication
>   ou la communication de cet arrêté, d'aligner sans surcoût les
>   paramétrages du système sur ses exigences. »*

### 2.3 Périmètre potentiellement couvert par l'arrêté

L'arrêté pourrait, selon sa rédaction, préciser :

- le **format exact** des bordereaux (contenu complémentaire à l'art. 85) ;
- la **procédure électronique** (authentification, certification, validation) ;
- la **source de temps** officielle ;
- le **mécanisme de signature électronique** des parties ;
- la **politique tarifaire** (émoluments du greffe) ;
- les **modalités de notification** ;
- les **interconnexions** obligatoires avec d'autres registres.

### 2.4 Risques juridiques en l'absence d'arbitrage

- **Risque d'incompatibilité** : si le système est déployé avec des
  paramétrages par défaut qui s'écartent de l'arrêté ultérieur, une
  reconfiguration sera nécessaire ; certaines décisions opposables
  pourraient être remises en question.
- **Risque de coût de mise en conformité** : la publication tardive
  de l'arrêté peut imposer des retravaux coûteux.
- **Risque de blocage juridique** : sans publication, certaines
  dispositions du décret (notamment l'art. 81 sur la procédure
  dématérialisée) pourraient être considérées comme imparfaites.

---

## 3. Situation actuelle dans le système

### 3.1 Hypothèses provisoires adoptées

Le TDR signale les hypothèses retenues par défaut, encadrées
explicitement dans le code et la documentation :

| Domaine | Hypothèse provisoire | Code |
|---------|----------------------|------|
| Canal électronique | Soumission authentifiée + accusé horodaté (§ 3.2 TDR) | `RSM_MFA_MODE=disabled` + session Django |
| Signature électronique | Flags booléens `accord_*_confirme` | `RSM_ESIGN_MODE=disabled` |
| Source de temps | Horloge locale | `RSM_TIMESOURCE_MODE=local_stub` |
| Scellement | SHA-256 non signé | `RSM_SEAL_MODE=disabled` |
| Paiement | Non implémenté | — |
| Procédure de recherche | Endpoint public sans authentification (art. 94) | `AllowAny` |

### 3.2 Préparation à la publication de l'arrêté

Le système a été conçu pour pouvoir absorber la publication de
l'arrêté **sans réécriture du cœur métier**. Les interfaces stables
(`horodatage`, `scellement`, `habilitations`, fiches F1 à F8) sont
câblables par configuration.

### 3.3 Ce qui n'est pas paré à absorber sans travail

- Une éventuelle **nouvelle énumération limitative** introduite par
  l'arrêté (nouveau canal, nouveau motif, nouveau critère) imposerait
  une mise à jour du code (ajout d'une valeur à l'enum, du référentiel,
  des libellés bilingues).
- Une éventuelle **procédure non prévue** (ex. étape intermédiaire
  entre dépôt et validation) imposerait une modification de la
  matrice des transitions (§ 4.3).
- Un **cahier de charges art. 83** (si délégation) imposerait la fiche
  F12 — traitée séparément.

---

## 4. Options d'arbitrage

### 4.1 Option a — Attentisme strict (aucune mise en production avant arrêté)

**Description** : la mise en production du système est **subordonnée**
à la publication de l'arrêté. Pendant l'attente, le système reste en
environnement de pré-production / recette ; seule la préparation
documentaire et de recette avance.

| Dimension | Évaluation |
|-----------|------------|
| Sécurité juridique | 🟢 **Maximale** |
| Délai de mise en production | 🔴 **Dépendant de l'arrêté** (indéterminé) |
| Coût d'attente | 🔴 Coûts fixes sans bénéfice opérationnel |
| Risque de retravail | 🟢 Nul |
| Pression politique | 🔴 Peut être mal perçu si l'arrêté tarde longtemps |

**Avantages** : aucun risque de non-conformité.
**Inconvénients** : retarde toute exploitation, y compris les cas
où le système est utilisable sans arrêté (ex. tenue interne au
greffe, inscriptions papier).

### 4.2 Option b — Mise en production partielle (canal papier uniquement)

**Description** : le canal **guichet papier** (art. 78 al. 1) est
mis en production sans dépendance à l'arrêté, puisque la procédure
papier relève du décret sans renvoi à l'arrêté. Le **canal
électronique** (art. 78 al. 1 + art. 81, 84) reste en attente.

| Dimension | Évaluation |
|-----------|------------|
| Sécurité juridique | 🟢 Élevée (canal papier est entièrement couvert par le décret) |
| Accessibilité | 🔴 Limitée au guichet physique |
| Délai de mise en service | 🟢 **Court** |
| Coût d'attente | 🟢 Réduit (exploitation partielle) |
| Risque d'évolution | 🟠 Le canal électronique devra être activé ultérieurement |

**Avantages** : ouverture du service sans attendre l'arrêté.
**Inconvénients** : exclusion des déposants distants ; canal
électronique restant en suspens.

### 4.3 Option c — Mise en production complète avec paramétrages par défaut documentés

**Description** : le système est mis en production avec les
paramétrages par défaut (issus des hypothèses TDR + décisions MO
prises au travers des autres fiches F1 à F8). Chaque paramétrage est
**explicitement documenté** comme « configuration provisoire en
attente d'arrêté ». À la publication, une procédure de mise en
conformité est déclenchée (sans surcoût conformément au TDR).

| Dimension | Évaluation |
|-----------|------------|
| Accessibilité | 🟢 Complète |
| Risque juridique | 🟠 Modéré — dépend des écarts potentiels avec l'arrêté futur |
| Délai | 🟢 Court |
| Coût d'attente | 🟢 Nul — système opérationnel |
| Coût de mise en conformité ultérieure | 🟠 Indéterminé |
| Traçabilité | 🟢 Chaque paramétrage est documenté avec sa motivation |

**Avantages** : mise en service rapide, réponse au besoin.
**Inconvénients** : exposition à des écarts avec l'arrêté ;
nécessite une procédure de reprise documentée.

### 4.4 Option d — Charte provisoire MO + prestataire

**Description** : le MO signe avec le prestataire (ou en interne) une
**charte provisoire** formalisant les paramétrages retenus jusqu'à
publication de l'arrêté. La charte :
- énumère explicitement chaque paramétrage concerné ;
- fixe la procédure de révision à la publication ;
- engage les parties sur la bonne foi de la conformité provisoire.

| Dimension | Évaluation |
|-----------|------------|
| Sécurité juridique | 🟢 Élevée — la charte a valeur d'engagement opposable aux signataires |
| Accessibilité | 🟢 Complète |
| Délai | 🟢 Court |
| Complexité administrative | 🟠 Rédaction et signature de la charte |
| Compatibilité avec l'art. 86 | 🟢 Respectée |
| Visibilité externe | 🟢 Le public sait à quoi s'en tenir |

**Avantages** : combine mise en service rapide et sécurité juridique.
**Inconvénients** : exige un document administratif supplémentaire à
produire et signer.

### 4.5 Option e — Déploiement par étapes conditionnelles

**Description** : le système est mis en production **par vagues** :
- **Vague 1** : fonctions purement internes (admin, saisie guichet,
  consultation) — aucune dépendance à l'arrêté.
- **Vague 2** : publication au fichier public (recherche art. 94 à 97)
  — dépendance limitée.
- **Vague 3** : canal électronique complet (dépôt par déclarant
  externe, modification en ligne) — subordonnée à la publication de
  l'arrêté.

| Dimension | Évaluation |
|-----------|------------|
| Sécurité juridique | 🟢 Proportionnée à chaque vague |
| Accessibilité | 🟠 Progressive |
| Délai | 🟢 Vague 1 immédiate, vagues 2-3 progressives |
| Coût | 🟢 Étalé |
| Complexité de gouvernance | 🟠 Chaque vague exige une décision de bascule |

**Avantages** : pragmatisme opérationnel maximal.
**Inconvénients** : gouvernance multi-étapes ; risque de confusion
sur le statut juridique des fonctions activées.

### 4.6 Option f — Sollicitation active de l'arrêté par le MO

**Description** : en parallèle de l'une des options précédentes (a,
b, c, d, e), le MO **sollicite officiellement** le ministère de la
Justice pour la publication de l'arrêté, en fournissant une note
technique préparée par le prestataire (notamment à partir des fiches
F1 à F8). L'objectif est d'accélérer la sortie du texte en apportant
les éléments techniques au législateur.

Cette option n'est pas exclusive : elle peut accompagner les options
a, b, c, d ou e.

| Dimension | Évaluation |
|-----------|------------|
| Effet accélérateur | 🟢 Potentiellement élevé |
| Coût | 🟢 Faible (rédaction d'une note) |
| Dépendance | 🟠 Réactivité du ministère |
| Rôle du MO | 🟠 Place le MO comme contributeur au législateur |

**Avantages** : agit sur la cause (absence d'arrêté) plutôt que sur
les symptômes.
**Inconvénients** : aucune garantie de succès ou de calendrier.

---

## 5. Impacts transversaux

### 5.1 Impacts sur les fiches F1 à F8

L'arrêté pourrait **préciser ou contredire** les options MO arbitrées
sur les fiches F1 à F8. Chaque décision MO doit donc comporter une
clause de révision automatique à la publication de l'arrêté.

### 5.2 Impacts sur le code

| Option | Implication technique |
|--------|------------------------|
| a | Aucune mise en production ; maintenance du code en recette |
| b | Désactivation du canal électronique en production (`CanalSaisie.PORTAIL_ELECTRONIQUE` refusé) |
| c | Aucune — paramétrages actuels |
| d | Ajout d'un bandeau « paramétrage provisoire — arrêté en attente » |
| e | Feature flags par vague (paramétrage fin en settings) |
| f | Aucune incidence technique |

### 5.3 Impacts sur les livrables

- L1 Note de cadrage : section « Arrêté d'application » à préciser.
- L11 : ligne `A1` à faire évoluer selon la décision.
- Plan de recette (L7 à venir) : portée adaptée selon l'option.

### 5.4 Dépendances transversales

- Si l'arrêté spécifie une **source de temps officielle** → F5
  automatiquement tranchée.
- Si l'arrêté spécifie un **régime de signature électronique** → F3
  automatiquement tranchée.
- Si l'arrêté précise des **notifications obligatoires** → F13 et
  L2.5 § 9.3 impactées.

---

## 6. Tradeoffs synthétiques

| Critère | a (Attentisme) | b (Papier seul) | c (Complète + doc) | d (Charte MO) | e (Vagues) | f (Sollicitation) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| Sécurité juridique | Maximale | Élevée | Modérée | Élevée | Proportionnée | Variable |
| Délai de mise en service | Indéterminé | Court | Court | Court | Très court (V1) | Variable |
| Risque de retravail | Nul | Faible | Modéré | Faible | Faible | Faible |
| Coût opérationnel d'attente | Élevé | Modéré | Faible | Faible | Très faible | Faible |
| Accessibilité | Nulle | Limitée | Complète | Complète | Progressive | Complète |
| Valeur signal politique | Positive | Neutre | Risquée | Positive | Neutre | Positive |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Calendrier attendu** de publication de l'arrêté (connaissance du
   MO).
2. **Périmètre supposé** de l'arrêté : couvre-t-il seulement la
   procédure dématérialisée, ou d'autres aspects ?
3. **Autorité compétente** pour la charte provisoire (option d) :
   Ministre de la Justice, Président du Tribunal, Direction du
   Greffe ?
4. **Relation avec les fiches F1 à F8** : les décisions MO prises sur
   ces fiches sont-elles contractuellement considérées comme
   provisoires ?
5. **Procédure de mise en conformité** à la publication : délai
   maximum, tests de régression, validation MO.
6. **Clause de non-surcoût** (TDR) : qui prend en charge le retravail
   si la charte s'écarte trop de l'arrêté publié ?
7. **Conformité des inscriptions produites avant arrêté** : quid
   juridiquement des actes enregistrés en période provisoire ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ autre : ______ |
| Option accompagnée de option f (sollicitation) ? | ☐ oui  ☐ non |
| Calendrier de bascule (option e) | _(à renseigner)_ |
| Référence de la charte provisoire (option d) | _(à renseigner)_ |
| Procédure de mise en conformité | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Avertissement préliminaire du TDR : extrait dans [L1 § 1](../L1_note_de_cadrage.md).
- Autres fiches dépendantes : F1, F2, F3, F4, F5, F6, F7, F8, F11, F13 (toute la chaîne arbitrage).
- Registre : [L11](../L11_tracabilite_articles_76_97.md).
