# Fiche MO — F1 — Glossaire juridique bilingue FR/AR

**Référence L11** : `L11/A6`
**Articles fondateurs** : TDR § 7.3 (neutralité juridique des langues), § 7.4 (gestion des données multilingues).
**Classe d'arbitrage** : hypothèse signalée au TDR (zone A6).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/A6` — Glossaire bilingue juridique |
| Articles fondateurs | TDR § 7.3, § 7.4 ; art. 76 (natures limitatives) ; art. 80 (motifs limitatifs) ; art. 96 (critères limitatifs) |
| Statut actuel | **Amorces techniques chargées** par `seed_referentiels`. Non opposables tant que non validées. |
| Dépendances | Débloque intégralement la cartographie des messages système (L2.5) et prépare l'Option B (frontend). |
| Impact transverse | 9 énumérations limitatives × ~50 libellés + 8 statuts + ~89 messages système + 5 types de certificats |

---

## 2. Contexte juridique

### 2.1 Exigence du TDR § 7.3

> *« Les versions française et arabe produisent les mêmes effets
>   juridiques, sans interprétation divergente possible.
>   La terminologie juridique est validée par le secrétariat ou le
>   comité désigné par le maître d'ouvrage, sur la base d'un glossaire
>   bilingue annexé au contrat. Lorsqu'un terme juridique ne dispose
>   pas d'équivalent établi dans l'une des deux langues, un
>   équivalent est validé par le maître d'ouvrage avant mise en
>   production. »*

### 2.2 Exigence du TDR § 7.4 — Langue faisant foi

Pour chaque libellé présent dans une seule langue ou pour lequel une
divergence d'interprétation serait possible, **une langue faisant foi
doit être désignée**. L'enum `LangueFaisantFoi` prévoit trois valeurs :
- `fr` — seule la version FR prévaut ;
- `ar` — seule la version AR prévaut ;
- `equ` — les deux versions sont réputées strictement équivalentes.

### 2.3 Risque juridique en l'absence d'arbitrage

- **Risque de divergence d'interprétation** entre les versions FR et
  AR d'un libellé (art. 76 nature, art. 80 motif, art. 96 critère,
  statut § 4.3), avec conséquence potentielle sur l'opposabilité.
- Risque de contestation lors d'une recherche publique si un
  constituant arabophone comprend autrement un libellé de nature
  de sûreté que le greffe francophone.
- Risque de nullité partielle d'un certificat de recherche (art. 97
  dernier alinéa) si le comité de terminologie n'a pas validé les
  libellés officiels avant production opposable.

---

## 3. Situation actuelle dans le système

### 3.1 Périmètre des libellés à valider

| Catégorie | Nombre | Stocké dans | Référence |
|-----------|:------:|-------------|-----------|
| Natures de sûretés (art. 76) | 12 | `LibelleNatureDroit` | [apps/referentiels/fixtures/natures_droit.json](../../backend/apps/referentiels/fixtures/natures_droit.json) |
| Motifs de rejet limitatifs (art. 80) | 3 | `LibelleMotifRejet` | `motifs_rejet.json` |
| Canaux de saisie (art. 78) | 2 | `LibelleCanalSaisie` | `canaux_saisie.json` |
| Critères de recherche (art. 96) | 4 | `LibelleCritereRecherche` | `criteres_recherche.json` |
| Types de certificats | 5 | `LibelleTypeCertificat` | `types_certificats.json` |
| Statuts d'inscription (§ 4.3) | 9 | `StatutInscription.choices` + i18n | L2.3 |
| Rôles applicatifs (§ 4.1) | 7 | `RoleApplicatif.choices` + i18n | L2.4 |
| Motifs de refus modification (art. 88) | 8 | `MotifRefusModification.choices` + i18n | L2.5 § 4 |
| Messages système (familles 1 à 8) | ~89 | Fichiers `.po` / `.json` | L2.5 |
| Statuts de demandes | 3 × 3 | Enums par app | L3.1 |

**Total approximatif** : **~140 libellés** FR/AR à valider.

### 3.2 État actuel des amorces

- Les amorces FR sont issues des formulations du décret et du TDR ;
  elles sont raisonnablement proches d'un libellé juridique acceptable
  mais **n'ont pas été validées** par un comité de terminologie.
- Les amorces AR ont été produites comme traductions fonctionnelles
  des amorces FR ; elles sont formellement cohérentes mais **n'ont
  pas été validées** par un arabophone compétent en terminologie
  juridique.

### 3.3 Mécanisme technique

- Tous les libellés sont chargés via `python manage.py seed_referentiels`.
- Les amorces sont marquées `langue_faisant_foi="equ"` par défaut,
  ce qui présume — à tort — une équivalence validée.
- Toute validation par le comité se traduit par une mise à jour des
  fixtures et un nouveau `seed_referentiels --reset=false` (idempotent).

### 3.4 Tests désactivés liés

- `tests/test_api_zones_gelees.py::ZonesGelees_Placeholders_Tests` —
  les messages FR/AR produits par l'API (certificats, notifications)
  sont actuellement testés uniquement sur leurs clés neutres.
- Aucun test ne vérifie la validation du comité — l'option d'un
  contrôle automatisé figure parmi les options ci-dessous.

---

## 4. Options d'arbitrage

### 4.1 Option a — Validation normative complète par un comité désigné

**Description** : le MO désigne formellement un comité de terminologie
bilingue juridique (minimum 3 membres : un juriste francophone, un
juriste arabophone, un terminologue ou linguiste). Le comité valide
en un ou plusieurs tours l'ensemble des ~140 libellés. Chaque libellé
validé est scellé avec `langue_faisant_foi="equ"`. Les amorces non
validées sont bloquées en pré-production.

| Dimension | Évaluation |
|-----------|------------|
| Fondement TDR | 🟢 Stricte conformité au § 7.3 (« glossaire annexé au contrat »). |
| Sécurité juridique | 🟢 **Maximale** — aucun libellé non validé en production. |
| Délai | 🔴 **Long** — mobilisation d'un comité, plusieurs sessions ; estimation indicative : 2 à 4 mois selon disponibilité. |
| Coût direct | 🟠 Honoraires des membres du comité + secrétariat. |
| Retour arrière | 🟢 Aucun — une fois validé, le glossaire est officiel. |
| Impact sur le code | 🟢 Nul — la seule opération est la mise à jour des fixtures. |
| Risques | 🟠 Si un terme n'a pas d'équivalent établi, le comité doit en forger un — processus potentiellement long. |

### 4.2 Option b — Référence à un corpus existant

**Description** : le MO retient un corpus terminologique pré-existant
— par exemple le lexique juridique OHADA bilingue (s'il couvre
le périmètre des sûretés mobilières en arabe), ou un corpus publié par
une autorité linguistique nationale. Les amorces sont alignées sur ce
corpus et validées par un seul expert pour homogénéité. L'écart au
corpus de référence n'est autorisé que sur décision MO expresse pour
les termes non couverts.

| Dimension | Évaluation |
|-----------|------------|
| Fondement TDR | 🟢 Conformité au § 7.3 si le corpus est reconnu comme référence juridique. |
| Sécurité juridique | 🟢 Élevée — adossée à une terminologie établie. |
| Délai | 🟢 **Court** — 2 à 6 semaines selon complétude du corpus. |
| Coût direct | 🟢 Réduit — licence d'usage éventuelle + un expert de validation. |
| Retour arrière | 🟠 Les évolutions du corpus de référence peuvent imposer une mise à jour. |
| Impact sur le code | 🟢 Nul. |
| Risques | 🟠 Si le corpus ne couvre pas les 12 natures de sûretés du décret 2021-033 (qui sont spécifiques à la Mauritanie), des compléments ad hoc restent nécessaires. |

### 4.3 Option c — Validation incrémentale par catégorie

**Description** : le MO valide le glossaire **par vagues**, en
commençant par les libellés critiques (natures art. 76, motifs art. 80,
critères art. 96) puis en progressant vers les messages système et
les libellés UI. Chaque vague passe en pré-production (fichier public
accessible) au fur et à mesure. Les libellés non encore validés
portent `langue_faisant_foi` explicitement renseigné pour éviter la
présomption d'équivalence.

| Dimension | Évaluation |
|-----------|------------|
| Fondement TDR | 🟠 Compatible si les libellés critiques sont validés avant ouverture publique ; à encadrer. |
| Sécurité juridique | 🟢 Élevée sur le noyau juridique, 🟠 modérée sur les messages périphériques. |
| Délai | 🟢 **Progressif** — ouverture publique possible en 1 à 2 mois sur le noyau. |
| Coût direct | 🟢 Étalé dans le temps. |
| Retour arrière | 🟢 Corrections possibles sans bloquer le système. |
| Impact sur le code | 🟠 Nécessite un drapeau par entrée de référentiel (« validé », « amorce », « en revue ») — évolution mineure du modèle `LibelleReferentiel`. |
| Risques | 🟠 Coexistence de libellés validés et non validés en production ; exige une communication claire aux utilisateurs. |

### 4.4 Option d — Double terminologie (juridique figée + UI reformulable)

**Description** : le MO valide un glossaire **juridique strict** pour
les libellés qui apparaissent dans les certificats probants, les
bordereaux officiels et le journal d'audit (termes opposables). En
revanche, les libellés d'interface utilisateur (boutons, messages de
succès, aides contextuelles) sont reformulables par l'administrateur
fonctionnel dans un registre de traductions séparé, sans revalidation
par le comité.

| Dimension | Évaluation |
|-----------|------------|
| Fondement TDR | 🟠 Compatible — le § 7.3 n'exige de validation que de la *terminologie juridique*. L'UI peut être gérée par l'admin fonctionnel (§ 4.1). |
| Sécurité juridique | 🟢 Élevée sur le périmètre opposable. |
| Délai | 🟢 Court sur le périmètre juridique ; flexibilité sur l'UI. |
| Coût direct | 🟢 Réduit — comité mobilisé sur un périmètre restreint. |
| Retour arrière | 🟢 UI ajustable en continu. |
| Impact sur le code | 🟠 Nécessite une distinction formelle entre libellés « juridiques scellés » et « libellés UI libres » dans `LibelleReferentiel` ou via un second modèle. |
| Risques | 🟠 Risque d'incohérence entre UI et certificats si les libellés UI s'éloignent trop de la terminologie officielle. Exige une gouvernance claire. |

### 4.5 Option e — Glossaire minimal bilingue + protocole de validation de l'équivalence

**Description** : le MO valide uniquement un **glossaire minimal
bilingue** couvrant les termes cardinaux (natures art. 76, motifs
art. 80, critères art. 96, statuts § 4.3) — une trentaine de termes.
Le reste des libellés suit le principe du « libellé dérivé » : les
formulations des messages et de l'UI se composent à partir du
glossaire minimal, de façon traçable. Un protocole de validation de
l'équivalence FR/AR pour les libellés dérivés est mis en place (ex. :
contrôle automatique de la présence des termes cardinaux dans chaque
langue).

| Dimension | Évaluation |
|-----------|------------|
| Fondement TDR | 🟠 Compatible si le protocole d'équivalence est explicité. |
| Sécurité juridique | 🟢 Élevée sur le noyau, 🟠 dépendante du protocole pour le reste. |
| Délai | 🟢 **Très court** — 2 à 4 semaines pour le glossaire minimal. |
| Coût direct | 🟢 Réduit. |
| Retour arrière | 🟢 Évolutif. |
| Impact sur le code | 🟠 Nécessite le développement d'un outil de dérivation automatique ou d'une revue assistée. |
| Risques | 🟠 Le protocole de validation des dérivés doit être rigoureux, sans quoi des divergences s'introduisent. |

---

## 5. Impacts transversaux

### 5.1 Impacts sur les livrables existants

| Livrable | Impact |
|----------|--------|
| L2.5 Messages système | ~89 messages à valider selon l'option retenue (total ou partiel) |
| L2.3 Libellés de statuts | 9 statuts à valider |
| L2.4 Libellés de rôles | 7 rôles à valider |
| L3.6 Matrice bilingue | Mise à jour de la section « amorce à valider » en « validée par le comité » |
| L11 Registre | Passage de `A6` à IMPLÉMENTÉ |
| Fixtures référentiels | Mise à jour de `libelle_fr`, `libelle_ar`, `langue_faisant_foi` |

### 5.2 Impacts sur les zones gelées connexes

| Zone gelée | Impact |
|------------|--------|
| `L11/A5` (certificats probants) | Les certificats ne peuvent être produits en langue officielle tant que le glossaire n'est pas validé. |
| `L11/interconnexions` (notifications) | Les libellés des 7 notifications externes dépendent du glossaire. |

### 5.3 Impacts sur les tests

- Aucun test désactivé n'est directement lié à la validation du
  glossaire ; les tests bilingues existants (`test_api_d3_accept_language.py`)
  portent sur l'identité des clés neutres, indépendamment des libellés.
- Option c ou d : nécessite un nouveau test de cohérence (présence
  systématique d'un libellé validé pour chaque clé avant production).

### 5.4 Dépendances externes

| Option | Dépendance |
|--------|------------|
| a | Désignation du comité par arrêté du Président du Tribunal ou par note ministérielle. |
| b | Licence ou convention d'usage du corpus choisi. |
| c | Disponibilité séquentielle des membres du comité. |
| d | Définition d'une gouvernance UI (qui peut reformuler, sur quels libellés). |
| e | Développement éventuel d'un outil de validation automatique. |

---

## 6. Tradeoffs synthétiques

| Critère | a (Comité complet) | b (Corpus existant) | c (Incrémental) | d (Double terminologie) | e (Glossaire minimal + protocole) |
|---------|:-:|:-:|:-:|:-:|:-:|
| Sécurité juridique (opposabilité) | Maximale | Élevée | Élevée (noyau) | Élevée (noyau juridique) | Élevée (noyau) |
| Délai de mise en production | Long | Court | Progressif | Court | Très court |
| Coût direct | Élevé | Réduit | Étalé | Réduit | Réduit |
| Adaptabilité post-déploiement | Faible | Modérée | Élevée | Élevée (UI) | Élevée |
| Impact code requis | Nul | Nul | Mineur | Mineur | Modéré (outillage) |
| Complexité de gouvernance | Basse | Basse | Moyenne | Moyenne | Élevée |
| Conformité stricte au § 7.3 | Maximale | Élevée (si corpus reconnu) | Progressive | Élevée si périmètre opposable couvert | Conditionnelle au protocole |

---

## 7. Points à préciser lors de l'arbitrage MO

Quelle que soit l'option retenue, le MO devra préciser :

1. **Composition du comité** (si option a ou c) : profils, autorité de nomination.
2. **Corpus de référence** (si option b ou e) : identification formelle, licence.
3. **Traitement des termes sans équivalent établi** (art. 76, cas de sûretés spécifiques à la Mauritanie) : procédure de forge terminologique.
4. **Règle de sécurisation** entre « amorce » et « validé » : comment un libellé non validé est-il identifié et empêché d'apparaître sur un document officiel ?
5. **Fréquence de revalidation** : le glossaire est-il figé à la réception ou révisable en cours d'exploitation ?
6. **Impact sur la recette (L7)** : la recette bilingue (§ 10.6 TDR) est-elle conduite sur le glossaire validé ou sur les amorces ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ autre : ______ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |
| Précisions complémentaires | _(à renseigner)_ |

---

## 9. Renvois croisés

- Matrice de conformité bilingue : [L3.6](../L3_6_matrice_bilingue.md).
- Cartographie des messages système : [L2.5](../L2_5_messages_systeme.md).
- Statuts et transitions : [L2.3](../L2_3_matrice_statuts_transitions.md).
- Rôles applicatifs : [L2.4](../L2_4_roles_operations.md).
- Modèles `Libelle*` : [L3.1 § 2.5](../L3_1_modele_donnees.md).
- Registre des arbitrages : [L11](../L11_tracabilite_articles_76_97.md).
