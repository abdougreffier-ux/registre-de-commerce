# Support d'aide à la décision — Comparatif synthétique F1 × F3 × F4 × F5

**Objet** : document d'aide à la décision MO pour les quatre zones
gelées formant le **nœud cardinal** d'opposabilité du système RSM.
**Portée** : synthèse comparative, matrice d'interdépendances,
scénarios de cohérence globale. **Aucune recommandation tranchée.**
**État** : support destiné à faciliter la prise de décisions MO
séparées pour F1, F3, F4 et F5.

---

## 1. Pourquoi ces quatre fiches ensemble ?

### 1.1 Nœud cardinal d'opposabilité

Les quatre fiches F1, F3, F4 et F5 constituent un **ensemble
indivisible** du point de vue de la valeur juridique du système :

```
                    ┌───────────────────────┐
                    │  F1 — Glossaire       │
                    │  juridique FR/AR      │
                    │  (libellés officiels) │
                    └───────────┬───────────┘
                                │ alimente
                                ▼
┌──────────────┐    ┌──────────────────────┐    ┌──────────────┐
│ F3 — Signa-  │    │ F4 — Charte          │    │ F5 — Source  │
│ ture élec.   │───▶│ documentaire et      │◀───│ de temps     │
│ art. 88      │    │ certificats probants │    │ art. 78      │
└──────────────┘    └──────────────────────┘    └──────────────┘
       │                      ▲                        │
       │                      │                        │
       └──── mutualisation PKI éventuelle ─────────────┘
```

**Sans décision sur les quatre** :
- aucun certificat probant ne peut être émis (F4 dépend de F1, F3, F5) ;
- aucune modification art. 88 n'est cryptographiquement vérifiée (F3) ;
- aucun horodatage n'est juridiquement opposable (F5) ;
- aucun libellé officiel n'est publié (F1).

### 1.2 Effet de levier

Une décision MO sur ces quatre fiches **débloque en cascade** :
- l'ouverture du portail électronique (via F2 en complément) ;
- la production probante des certificats d'inscription, de
  modification, de renouvellement, de radiation et de recherche ;
- la levée des tests `@arbitrage_mo` qui dépendent de ces zones ;
- le chantier frontend (Option B).

---

## 2. Rappel synthétique des options

### 2.1 F1 — Glossaire juridique bilingue FR/AR (5 options)

| Option | Description synthétique | Délai | Coût |
|--------|-------------------------|:-----:|:----:|
| a | Comité complet (juristes + linguistes) | Long | Élevé |
| b | Corpus existant (OHADA, lexique national) | Court | Réduit |
| c | Validation incrémentale par catégorie | Progressif | Étalé |
| d | Double terminologie (juridique + UI libre) | Court | Réduit |
| e | Glossaire minimal + protocole d'équivalence | Très court | Réduit |

### 2.2 F3 — Signature électronique art. 88 (5 options)

| Option | Description synthétique | Délai | Coût |
|--------|-------------------------|:-----:|:----:|
| a | PKI nationale | Moyen | Modéré |
| b | Certificats qualifiés tiers (eIDAS-like) | Moyen-long | Modéré-élevé |
| c | Signature simple + SMS/email horodaté | Court | Modéré |
| d | Bi-niveau (qualifiée critique + simple mineur) | Long | Élevé |
| e | Papier transitoire (pas d'électronique pour modif) | Immédiat | Très faible |

### 2.3 F4 — Charte documentaire + certificats probants art. 97 (6 options)

| Option | Description synthétique | Délai | Coût |
|--------|-------------------------|:-----:|:----:|
| a | PDF/A-3 + PAdES (signature embarquée) | Moyen | Modéré |
| b | PDF/A-3 + signature détachée (XAdES/CAdES) | Court | Modéré |
| c | XML signé + PDF dérivé | Long | Modéré-élevé |
| d | PDF/A-3 + timestamp RFC 3161 | Court | Modéré |
| e | Papier transitoire avec tampon | Immédiat | Très faible |
| f | PDF/A + empreinte SHA-256 conservée au journal | Court | Très faible |

### 2.4 F5 — Source de temps officielle art. 78 (6 options)

| Option | Description synthétique | Délai | Coût |
|--------|-------------------------|:-----:|:----:|
| a | NTP stratum 1 ou 2 de confiance | Très court | Faible |
| b | PTP (précision sub-microseconde) | Long | Élevé |
| c | Horloge interne HSM de confiance | Long | Élevé |
| d | NTP + TSA externe (RFC 3161) | Moyen | Modéré |
| e | Paliers (NTP → HSM/TSA ensuite) | Très court | Progressif |
| f | Double source (contrôle croisé) | Long | Très élevé |

---

## 3. Matrice d'interdépendances

### 3.1 Dépendances structurelles

| De ↓ / Vers → | F1 Glossaire | F3 Signature | F4 Charte/Certif. | F5 Temps |
|---------------|:-:|:-:|:-:|:-:|
| **F1 Glossaire** | — | Libellés messages signature | **Forte** — libellés officiels des certificats | Libellés avertissements |
| **F3 Signature** | — | — | Possible PKI commune avec F4 | Dépend de F5 pour opposabilité temporelle |
| **F4 Charte/Certif.** | Dépend (libellés) | Possible PKI commune | — | **Forte** — horodatage du certificat |
| **F5 Temps** | — | Horodatage signature | **Forte** — horodatage du certificat | — |

### 3.2 Dépendances d'activation (quoi doit venir avant)

```
Production probante des certificats (F4)
  ├── requiert F1 (glossaire validé pour libellés officiels)
  ├── requiert F5 (horodatage opposable pour l'instant du certificat)
  └── requiert F3 (signature des modifications sous-jacentes)

Vérification des modifications (F3)
  └── requiert F5 (horodatage de la signature)

Source de temps (F5)
  └── indépendante

Glossaire (F1)
  └── indépendant
```

**Conséquence** : F1 et F5 peuvent être décidées **en premier** ; F3 et F4 bénéficient de leurs arbitrages.

### 3.3 Mutualisations possibles

| Combinaison | Mutualisation | Économie |
|-------------|---------------|----------|
| F3 option a + F4 options a/b + F5 option c | Même HSM + même PKI | Forte |
| F3 option b + F4 options a/b | Même prestataire qualifié tiers | Moyenne |
| F3 option c + F4 option d/f + F5 option a | Aucune PKI, infrastructure légère | Très forte (coût) |
| F4 option c (XML signé) + interconnexions ultérieures (F13) | Interopérabilité maximale | Organisationnelle |

---

## 4. Scénarios de cohérence globale

Cette section présente **sept scénarios types** de combinaisons
cohérentes. **Chacun est présenté de manière neutre, sans
recommandation.** Le MO peut retenir l'un d'entre eux, une
combinaison personnalisée, ou une approche non listée.

### 4.1 Scénario α — Conservateur rapide

**Objectif** : mise en service la plus rapide possible avec un
niveau d'opposabilité basique.

| Fiche | Option | Justification interne au scénario |
|-------|--------|-----------------------------------|
| F1 | **e** (glossaire minimal + protocole) | Délai très court |
| F3 | **e** (papier transitoire) | Aucune infra à mettre en place |
| F4 | **e** (papier transitoire) OU **f** (SHA-256 interne) | Pas de PKI |
| F5 | **a** (NTP stratum 2) | Infrastructure standard |

| Dimension | Évaluation |
|-----------|------------|
| Délai total | Très court (1 à 3 mois) |
| Coût cumulé | Très faible |
| Opposabilité | Intermédiaire (art. 97 dernier al. non opposable sans signature) |
| Couverture portail électronique | Partielle (modification par papier seulement) |

**Tradeoff** : mise en service rapide, opposabilité dégradée pour
les certificats et les modifications électroniques.

### 4.2 Scénario β — Progressif par paliers

**Objectif** : démarrer vite, monter en gamme avec le temps.

| Fiche | Option | Justification |
|-------|--------|---------------|
| F1 | **c** (validation incrémentale) | Libellés critiques d'abord, UI ensuite |
| F3 | **c** (SMS/email horodaté) puis bascule | Compatible F5 option e |
| F4 | **f** (SHA-256 interne) puis bascule **a** ou **b** | Montée en gamme |
| F5 | **e** (paliers NTP → HSM/TSA) | Aligné sur F4 |

| Dimension | Évaluation |
|-----------|------------|
| Délai palier 1 | Court (2-4 mois) |
| Délai palier final | Moyen (12-18 mois) |
| Coût cumulé | Progressif |
| Opposabilité palier 1 | Intermédiaire |
| Opposabilité finale | Élevée |

**Tradeoff** : mise en service progressive, nécessite plusieurs
bascules techniques et communications MO.

### 4.3 Scénario γ — Référence OHADA / corpus existant

**Objectif** : s'appuyer au maximum sur des corpus et standards
existants.

| Fiche | Option | Justification |
|-------|--------|---------------|
| F1 | **b** (corpus existant — OHADA ou lexique national) | Court délai |
| F3 | **b** (certificats qualifiés tiers) | Reconnaissance régionale |
| F4 | **b** (PDF/A + signature détachée) | Standard OHADA |
| F5 | **a** (NTP stratum 2) OU **d** (NTP + TSA) | Standard |

| Dimension | Évaluation |
|-----------|------------|
| Délai | Court à moyen |
| Coût | Modéré |
| Opposabilité | Élevée |
| Interopérabilité régionale | Maximale |
| Dépendance externe | Plusieurs prestataires tiers |

**Tradeoff** : alignement régional, dépendance aux prestataires
reconnus.

### 4.4 Scénario δ — Souveraineté nationale

**Objectif** : minimiser les dépendances externes internationales.

| Fiche | Option | Justification |
|-------|--------|---------------|
| F1 | **a** (comité national) | Souveraineté terminologique |
| F3 | **a** (PKI nationale si disponible) | Souveraineté cryptographique |
| F4 | **a** (PAdES embarqué — signé par PKI nationale) | Cohérence |
| F5 | **a** (NTP national) ou **c** (HSM national) | Cohérence |

| Dimension | Évaluation |
|-----------|------------|
| Délai | Moyen à long |
| Coût | Modéré à élevé |
| Opposabilité | Maximale si PKI nationale opérationnelle |
| Dépendance | PKI / identité nationale |
| Résilience géopolitique | Élevée |

**Tradeoff** : indépendance nationale vs dépendance à la maturité
des infrastructures nationales.

### 4.5 Scénario ε — Maximalisme cryptographique

**Objectif** : opposabilité juridique maximale, indépendante de
toute remise en cause.

| Fiche | Option | Justification |
|-------|--------|---------------|
| F1 | **a** (comité complet) | Validation définitive |
| F3 | **a** (PKI nationale) ou **b** (tiers qualifiés) | Opposabilité maximale |
| F4 | **a** (PAdES) + **c** en sous-main (XML pour archives) | Double format |
| F5 | **c** (HSM) + option f (double source) | Résistance maximale |

| Dimension | Évaluation |
|-----------|------------|
| Délai | Long (18-24 mois) |
| Coût | Élevé |
| Opposabilité | **Maximale** |
| Complexité opérationnelle | Élevée |
| Résilience | Maximale |

**Tradeoff** : protection juridique maximale, investissement élevé.

### 4.6 Scénario ζ — Accessibilité maximale (mobile money + identité nationale)

**Objectif** : ouverture au plus large public, y compris déclarants
distants peu bancarisés.

| Fiche | Option | Justification |
|-------|--------|---------------|
| F1 | **d** (double terminologie — UI fluide, juridique strict) | UX simple |
| F3 | **c** (SMS/email horodaté) | Accessibilité |
| F4 | **d** (PDF/A + timestamp RFC 3161) ou **f** | Pas de PKI complexe pour l'utilisateur |
| F5 | **d** (NTP + TSA externe) | Opposabilité moyenne |

| Dimension | Évaluation |
|-----------|------------|
| Délai | Court à moyen |
| Coût | Modéré |
| Opposabilité | Intermédiaire à élevée |
| Accessibilité | **Maximale** |
| Dépendance | Prestataires SMS/email + TSA |

**Tradeoff** : large ouverture, opposabilité légèrement en retrait.

### 4.7 Scénario η — Papier prédominant (mise en service guichet seul)

**Objectif** : ouvrir la tenue au guichet sans attendre
l'infrastructure numérique.

| Fiche | Option | Justification |
|-------|--------|---------------|
| F1 | **c** (incrémental) | Priorité au noyau |
| F3 | **e** (papier transitoire) | Pas de canal électronique modif |
| F4 | **e** (papier transitoire) | Certificats papier avec tampon |
| F5 | **a** (NTP stratum 2) | Suffit pour tenue interne |

| Dimension | Évaluation |
|-----------|------------|
| Délai | Immédiat à court |
| Coût | Très faible |
| Opposabilité | Élevée (papier + tampon) |
| Couverture portail | **Nulle** — guichet uniquement |

**Tradeoff** : solution purement transitoire, adaptée à une première
vague.

---

## 5. Matrice synthétique des scénarios

| Scénario | F1 | F3 | F4 | F5 | Délai | Coût | Opposabilité | Couverture électronique |
|----------|:--:|:--:|:--:|:--:|:-----:|:----:|:------------:|:-----------------------:|
| α Conservateur rapide | e | e | e ou f | a | Très court | Très faible | Intermédiaire | Partielle |
| β Progressif paliers | c | c→a/b | f→a/b | e | Court → long | Progressif | Progressive | Progressive |
| γ Référence OHADA | b | b | b | a ou d | Court-moyen | Modéré | Élevée | Oui |
| δ Souveraineté nationale | a | a | a | a ou c | Moyen-long | Modéré-élevé | Maximale* | Oui |
| ε Maximalisme crypto | a | a ou b | a + c | c + f | Long | Élevé | **Maximale** | Oui |
| ζ Accessibilité max | d | c | d ou f | d | Court-moyen | Modéré | Intermédiaire-élevée | **Maximale** |
| η Papier prédominant | c | e | e | a | Immédiat | Très faible | Élevée (papier) | Nulle |

*sous réserve de maturité de la PKI nationale.

---

## 6. Séquence temporelle recommandée pour les décisions

Les décisions **peuvent** être prises dans l'ordre ci-dessous pour
maximiser la cohérence, **sans que cela soit contraignant** :

### 6.1 Décision 1 — F1 (glossaire) et F5 (source de temps)

Ces deux fiches sont **indépendantes** des autres. Elles peuvent
être arbitrées en premier, en parallèle.

- **F1** débloque la validation des libellés de tous les messages et
  de tous les certificats.
- **F5** débloque l'opposabilité temporelle de l'ensemble des actes.

### 6.2 Décision 2 — F3 (signature art. 88) et F4 (charte / certificats)

Ces deux fiches **dépendent** de F5 (horodatage) et, pour F4, de F1
(libellés). Elles peuvent être arbitrées conjointement pour
bénéficier des mutualisations cryptographiques (PKI commune).

- Si F5 retient l'option c (HSM) : F3 et F4 peuvent mutualiser le HSM.
- Si F5 retient l'option d (NTP + TSA) : F4 peut mutualiser la TSA
  (option d).

### 6.3 Décisions hors nœud cardinal

Une fois F1, F3, F4, F5 arbitrées, les autres zones gelées (F2, F6,
F7, F8, F9, F10, F11, F12, F13, F14) peuvent être traitées
séparément ou en package.

---

## 7. Tableau récapitulatif des décisions à rendre

| Décision | Référence L11 | Options | Prérequis | Impact direct |
|----------|:-------------:|:-------:|-----------|---------------|
| F1 Glossaire | `L11/A6` | a–e | Aucun | Libellés officiels partout |
| F5 Source de temps | `L11/horodatage` | a–f | Aucun | Opposabilité des horodatages |
| F3 Signature | `L11/A2` | a–e | F5 (idéalement) | Vérification art. 88 |
| F4 Charte/Certificats | `L11/A5` | a–f | F1 + F5 (idéalement) | Certificats probants art. 97 |

---

## 8. Points d'attention pour le MO

### 8.1 Ne pas trancher F3 avant F5

Plusieurs options de F3 supposent un horodatage opposable (options a,
b, d). Trancher F3 sans avoir arbitré F5 peut conduire à une
incohérence (ex. signature valide horodatée par une source non
opposable).

### 8.2 F4 implique nécessairement un rendu bilingue

Toutes les options de F4 (sauf e papier) exigent un rendu PDF avec
polices arabes embarquées et disposition bilingue (§ 7.5 TDR). Le
coût d'intégration des polices est inclus dans le chiffrage de
chaque option.

### 8.3 F1 option e (glossaire minimal) conditionne les amorces actuelles

Si le MO retient F1 option e, les libellés actuellement chargés par
`seed_referentiels` restent en place après validation minimale — pas
de refonte du code.

### 8.4 Effet de l'arrêté d'application (F9)

L'arrêté d'application (F9) peut **préciser ou contredire** les
options MO arbitrées sur F1 à F5. Les décisions MO devraient
comporter une clause de révision automatique à la publication de
l'arrêté (cf. F9 option d — charte provisoire).

### 8.5 Réversibilité (art. 83)

Toutes les options cryptographiques (F3, F4, F5 option c) doivent
permettre la vérification post-transfert. Les options retenues
doivent préciser la politique de conservation des clés publiques et
des infrastructures vérificatrices après un éventuel changement
d'organisme tenant le Registre.

---

## 9. Rappel de gouvernance

- Ce document est un **support d'aide à la décision**. Il n'exprime
  **aucune préférence** et n'anticipe **aucune décision**.
- Les scénarios α à η sont des **illustrations** de combinaisons
  cohérentes possibles — ni exhaustives, ni recommandées. Le MO
  reste libre de toute combinaison, y compris non listée.
- Chaque décision sur F1, F3, F4, F5 fait l'objet d'une décision MO
  écrite et référencée **distincte** pour chaque fiche, consignée
  dans la section « Décision MO » de la fiche correspondante ou dans
  un document officiel séparé.
- Toute activation technique reste **conditionnée** à ces décisions.

---

## 10. Renvois croisés

- Fiche F1 — Glossaire juridique bilingue : [F1_glossaire_bilingue.md](F1_glossaire_bilingue.md).
- Fiche F3 — Signature électronique art. 88 : [F3_signature_electronique.md](F3_signature_electronique.md).
- Fiche F4 — Charte documentaire / certificats probants : [F4_charte_documentaire_certificats.md](F4_charte_documentaire_certificats.md).
- Fiche F5 — Source de temps officielle : [F5_source_de_temps.md](F5_source_de_temps.md).
- Index des fiches MO : [index.md](index.md).
- Registre L11 des zones gelées : [../L11_tracabilite_articles_76_97.md](../L11_tracabilite_articles_76_97.md).
