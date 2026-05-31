# Fiche MO — F3 — Signature électronique des parties (art. 88)

**Référence L11** : `L11/A2`
**Articles fondateurs** : article 88 du décret 2021-033 ; TDR § 5.1 (intégrité), § 4.2.2 (modification).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/A2` — Signature électronique |
| Articles fondateurs | Article 88 (« signatures du créancier et du constituant ») ; TDR § 5.1 ; risque R6 du L11. |
| Statut actuel | **STUB** — flags booléens `accord_createur_confirme` et `accord_constituant_confirme` captés, mais **aucune vérification cryptographique**. `RSM_ESIGN_MODE=disabled`. |
| Dépendances | Est distincte de F2 (MFA) — MFA authentifie l'accès au système, la signature électronique art. 88 atteste l'accord substantiel des parties à une modification. Liée à F4 (PKI commune possible). |
| Impact transverse | Toute application de modification art. 88. |

---

## 2. Contexte juridique

### 2.1 Exigence de l'article 88

L'art. 88 liste le contenu obligatoire du formulaire de modification,
qui comprend :

> *« les signatures du créancier et du constituant attestant de leur
>   accord. »*

Cette exigence diffère du MFA (qui concerne l'accès au système) :
elle porte sur **l'accord matériel du créancier garanti et du
constituant** sur le contenu de la modification (ajout/retrait de
parties ou de biens, modification de la somme garantie…).

### 2.2 Silence du décret sur le régime applicable à la voie électronique

Le décret 2021-033 ne précise **pas** le régime de la signature
électronique pour le canal électronique prévu par l'article 78
alinéa 1. Le TDR § 4.2.2 signale cette ambiguïté comme un « Risque /
ambiguïté » et renvoie à un arrêté d'application non fourni (zones
`A1` et `A2`).

### 2.3 Articulation avec l'article 86 (régime déclaratif)

L'art. 86 interdit au greffier de vérifier les énonciations de la
demande — en particulier l'identité des signataires. Mais la
vérification **cryptographique** d'une signature électronique
(intégrité du contenu + correspondance clé / certificat) n'est pas un
contrôle de fond : c'est un contrôle de forme au sens de l'art. 80.

Le système peut donc, sans contrevenir à l'art. 86 :
- vérifier que la signature est cryptographiquement valide ;
- vérifier que le certificat n'est pas révoqué ;
- vérifier que la signature couvre le contenu exact soumis.

Il ne peut **pas** :
- vérifier que le signataire est effectivement le créancier (pouvoir,
  identité réelle) ;
- vérifier la capacité juridique à consentir ;
- apprécier la validité du consentement au fond.

### 2.4 Risques juridiques en l'absence d'arbitrage

- **Risque majeur de contestation** : une modification appliquée sur
  la seule base de cases à cocher (flags booléens) n'a aucune valeur
  probante des accords des parties en cas de contentieux. Le
  créancier ou le constituant pourrait contester avoir consenti.
- **Risque d'invalidité de la modification** au regard de l'art. 88 :
  si la jurisprudence considère que « signature » exige un degré de
  certitude supérieur à un flag booléen, les modifications produites
  en mode STUB pourraient être jugées nulles.
- Absence de **traçabilité opposable** du consentement des parties.

---

## 3. Situation actuelle dans le système

### 3.1 Implémentation STUB

| Élément | État |
|---------|------|
| `DemandeModification.accord_createur_confirme` | Booléen captured mais **non vérifié cryptographiquement** |
| `DemandeModification.accord_constituant_confirme` | Idem |
| Vérification à l'application | Contrôle uniquement que les deux flags sont `True` (cf. L3.1 § 2.9 + `MotifRefusModification.ACCORDS_MANQUANTS`) |
| Paramètre env | `RSM_ESIGN_MODE=disabled` |
| Tests désactivés | `test_api_zones_gelees.py::test_signature_invalide_provoque_refus_modification`, `test_revocation_certificat_provoque_refus` |

### 3.2 Interface stable exposée

Aucun adaptateur métier ne dépend de la mise en œuvre concrète —
l'interface stable est le couple `(accord_createur_confirme,
accord_constituant_confirme)`. L'activation cryptographique se fera
par câblage d'un adaptateur sans toucher au modèle ni aux services.

### 3.3 Lien avec la matrice des refus (L2.5 § 4)

En STUB, le refus `accords_manquants` se déclenche si l'un des flags
est `False`. Post-arbitrage, il se déclenchera également si la
vérification cryptographique échoue (signature invalide, certificat
révoqué, contenu altéré). Le code de motif reste identique
(`ACCORDS_MANQUANTS`), ce qui préserve la stabilité fonctionnelle.

---

## 4. Options d'arbitrage

### 4.1 Option a — PKI nationale (si disponible)

**Description** : si la Mauritanie dispose d'une PKI nationale
(autorité de certification publique émettant des certificats qualifiés
à destination des personnes physiques et morales), le RSM exige la
présentation de deux signatures (créancier + constituant) produites
par cette PKI. Le système vérifie la chaîne de confiance, la non-révocation
(OCSP ou CRL) et l'intégrité du contenu signé.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🟠 Modéré — intégration d'un vérificateur de signature (eIDAS-like, XAdES, CAdES) |
| Dépendance externe | 🔴 Dépendant de l'existence et de la disponibilité de la PKI nationale |
| Robustesse juridique | 🟢 **Maximale** — signature qualifiée opposable |
| Accessibilité | 🟠 Chaque partie doit disposer d'un certificat national (émission, distribution) |
| Conformité art. 88 | 🟢 Maximale |
| Réversibilité (art. 83) | 🟢 PKI nationale reste disponible même après transfert du RSM |

**Avantages** : opposabilité juridique maximale, indépendance du
système RSM.
**Inconvénients** : subordonné à l'existence effective d'une PKI
nationale et à la détention de certificats par les parties.

### 4.2 Option b — Certificats qualifiés de tiers agréés

**Description** : le MO agrée un ou plusieurs prestataires tiers de
certification (éventuellement internationaux reconnus par les accords
multilatéraux — eIDAS, OHADA, etc.). Le système accepte les
signatures produites par ces prestataires selon une politique
d'acceptation (« trust list ») gérée par l'administrateur
fonctionnel.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🟠 Modéré — vérificateur multi-autorité + gestion de la trust list |
| Dépendance externe | 🟠 Plusieurs prestataires (redondance → résilience) |
| Robustesse juridique | 🟢 Élevée si les prestataires sont reconnus |
| Accessibilité | 🟠 Les parties doivent acquérir un certificat auprès d'un prestataire agréé |
| Conformité art. 88 | 🟢 Élevée |
| Réversibilité (art. 83) | 🟢 Trust list exportable |

**Avantages** : moins dépendant d'un acteur unique, ouvert à des
parties internationales.
**Inconvénients** : complexité de gouvernance de la trust list,
risque d'hétérogénéité des niveaux de garantie entre prestataires.

### 4.3 Option c — Signature simple + double authentification par SMS / e-mail avec horodatage

**Description** : en l'absence de PKI disponible, le système produit
son propre dispositif de signature : chaque partie (créancier,
constituant) valide l'accord via un lien envoyé par e-mail ou SMS à
une adresse préalablement déclarée. Le système horodate chaque
validation et produit un **constat d'accord** scellé avec la modification.
La valeur probante repose sur la procédure et la conservation
pérenne (art. 79).

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🟢 Modéré — infrastructure SMS/email + template sécurisé |
| Dépendance externe | 🟠 Opérateurs SMS / fournisseur email |
| Robustesse juridique | 🟠 **Intermédiaire** — signature simple au sens eIDAS, opposabilité moindre qu'une signature qualifiée |
| Accessibilité | 🟢 Très adapté — chaque partie a une adresse email ou un numéro de téléphone |
| Conformité art. 88 | 🟠 Dépend de l'interprétation donnée à « signature » par le MO |
| Réversibilité (art. 83) | 🟢 Procédure interne, pas de dépendance externe forte |
| Conditionnalité | 🔴 Dépend de l'arbitrage de F4 (canal de notification) et de F2 (identité sous-jacente) |

**Avantages** : rapide à déployer, accessible, ne dépend pas d'une
infrastructure externe.
**Inconvénients** : force probante moindre, risque de contestation
plus élevé.

### 4.4 Option d — Mécanisme bi-niveau (qualifiée pour actes critiques, simple pour actes mineurs)

**Description** : distinction selon le type de modification :
- **Modifications critiques** (remplacement de toutes les parties ou
  de tous les biens, modification de la nature de la sûreté,
  modification du montant) : signature qualifiée obligatoire
  (option a ou b).
- **Modifications mineures** (adresse électronique, monnaie, ajout
  d'un bien supplémentaire sans retrait) : signature simple (option c).

Le système classe automatiquement la modification selon le diff et
exige le niveau de signature adapté.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🔴 Élevé — double infrastructure et gouvernance |
| Dépendance externe | 🟠 Selon les deux mécanismes retenus |
| Robustesse juridique | 🟢 Proportionnée aux enjeux |
| Complexité | 🔴 Élevée — classification des modifications + double flux |
| Risque d'erreur | 🟠 Classification erronée = modification traitée avec niveau inadapté |
| Conformité art. 88 | 🟠 Nécessite un arbitrage sur ce qui relève du « critique » vs « mineur » — potentiellement contestable |

**Avantages** : adaptation au risque.
**Inconvénients** : complexité, nécessite un socle juridique pour la
distinction, risque de contestation sur le classement.

### 4.5 Option e — Dispositif transitoire papier avant arbitrage final

**Description** : tant qu'aucune infrastructure de signature
électronique n'est retenue, le canal électronique art. 78 reste
théoriquement fermé pour les modifications. Seul le canal
« guichet papier » est admis : les signatures sont manuscrites sur
bordereau et conservées en original au greffe (la pièce jointe
numérisée portant l'empreinte SHA-256 pour contrôle d'intégrité,
zone `L11/A5`). Le dispositif électronique art. 88 est activé
ultérieurement avec l'option a, b ou c.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🟢 Très faible |
| Dépendance externe | 🟢 Aucune |
| Robustesse juridique | 🟢 Maximale (papier traditionnel) |
| Accessibilité | 🟠 Contraignante (déplacement au guichet) |
| Conformité art. 88 | 🟢 Incontestable |
| Conformité art. 78 al. 1 (canal électronique) | 🟠 Le portail électronique ne peut pas recevoir de modifications pendant la période transitoire |

**Avantages** : zéro risque juridique, simplicité.
**Inconvénients** : portail électronique inopérant pour les
modifications ; contraint les parties à venir au guichet.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Adaptateur à câbler |
|--------|---------------------|
| a | Vérificateur XAdES/CAdES/PAdES + connecteur OCSP/CRL de la PKI nationale |
| b | Idem + gestion multi-autorité (trust list) |
| c | Générateur de liens SMS/email + page de validation + horodatage interne |
| d | Combinaison a/b + c + classificateur de modification |
| e | Aucun câblage électronique ; désactivation du canal électronique sur `POST /api/v1/modifications/` |

Dans tous les cas, le modèle `DemandeModification` reste inchangé.
L'adaptateur est appelé dans `appliquer_modification` avant le contrôle
d'état final (L3.1 § 2.9). Le paramètre `RSM_ESIGN_MODE` bascule
entre les implémentations.

### 5.2 Impacts sur les tests

- Activation de `test_api_zones_gelees.py::test_signature_invalide_provoque_refus_modification`.
- Activation de `test_api_zones_gelees.py::test_revocation_certificat_provoque_refus`.
- Nouveau test : vérification de l'intégrité du contenu signé —
  toute altération du diff entre la signature et l'application →
  refus avec motif structuré.
- Compatibilité des tests D.2 (rejet art. 88 via API) : les flags
  booléens restent utilisés dans les tests ; leur sémantique change
  (auparavant « cochés », désormais « signature valide vérifiée »).

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 § 3.3 Formulaire de modification | Précision sur la procédure de signature selon l'option |
| L2.2 Règle B-88.2 | Évolution : « accords cryptographiquement valides » au lieu de « flags confirmés » |
| L2.5 § 4 Messages | Nouveau motif potentiel : `accords_signature_invalide` (à ajouter si l'option retenue le justifie) |
| L3.1 § 2.9 | Ajout éventuel d'un champ `preuve_signature` (JSON avec empreinte, horodatage, identifiant certificat) |
| L3.5 § 4.3 / § 6 | Mise à jour de la section protections OWASP |
| L11 Registre | Passage de `L11/A2` à IMPLÉMENTÉ |

### 5.4 Dépendances transversales avec d'autres fiches

- **F1 (glossaire)** : les libellés liés à la signature (« signature
  valide », « certificat révoqué », « empreinte altérée ») doivent
  être dans le glossaire validé.
- **F2 (MFA)** : si l'option c est retenue pour F3, une MFA forte
  (F2 option a, b ou c) devient d'autant plus importante pour éviter
  qu'un compte compromis produise des signatures simples frauduleuses.
- **F4 (charte documentaire / certificats probants)** : si la PKI
  retenue pour F3 est la même que pour F4, mutualisation de
  l'infrastructure.
- **F6 (scellement — Tour 2)** : une signature qualifiée peut servir
  de base au scellement global des snapshots.

### 5.5 Impacts sur l'exploitation

- Procédure de mise à jour des CRL / interrogation OCSP (option a, b).
- Procédure d'ajout / retrait d'un prestataire agréé (option b).
- Procédure de récupération d'un lien de validation perdu (option c).
- Formation des parties à l'usage de leur certificat (options a, b).

---

## 6. Tradeoffs synthétiques

| Critère | a (PKI nationale) | b (Tiers agréés) | c (SMS/email horodaté) | d (Bi-niveau) | e (Papier transitoire) |
|---------|:-:|:-:|:-:|:-:|:-:|
| Coût de déploiement | Modéré | Modéré-élevé | Modéré | Élevé | Très faible |
| Délai de mise en service | Moyen | Moyen | Court | Long | Immédiat |
| Force probante | Maximale | Élevée | Intermédiaire | Proportionnée | Maximale (papier) |
| Ouverture portail électronique | Oui | Oui | Oui | Oui | Non (modifications) |
| Accessibilité pour les parties | Modérée | Modérée | Élevée | Hétérogène | Faible |
| Réversibilité (art. 83) | Élevée | Élevée | Totale | Élevée | Totale |
| Conformité stricte art. 88 | Incontestable | Élevée | Dépendante de l'interprétation | Proportionnée | Incontestable |
| Dépendance externe | PKI nationale | Prestataires tiers | Opérateurs SMS/email | Combinée | Aucune |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Existence et maturité** d'une PKI nationale en Mauritanie
   (certificats pour personnes physiques et morales).
2. **Reconnaissance** éventuelle de prestataires internationaux de
   certification (OHADA, eIDAS, autres).
3. **Interprétation du terme « signature »** dans l'art. 88 : stricte
   (signature qualifiée) ou fonctionnelle (toute manifestation
   équivalente de consentement) ?
4. **Disponibilité de la procédure papier** en parallèle — ou
   exclusivité électronique à terme ?
5. **Politique de conservation** des preuves de signature dans le
   journal d'audit (§ 5.2 + art. 79).
6. **Gestion de la révocation** : un certificat révoqué après la
   signature affecte-t-il rétroactivement la validité de la
   modification ? (Point juridique complexe — à arbitrer par le MO
   avec le conseil juridique.)
7. **Délai d'expiration** de la validité d'une demande de modification
   entre dépôt et application — si les parties signent au dépôt mais
   que l'application est tardive, faut-il ré-signer ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ autre : ______ |
| Infrastructure précise (PKI, prestataires) | _(à renseigner)_ |
| Valeur arbitrée de `RSM_ESIGN_MODE` | _(à renseigner : `PKI_nationale` / `certificat_qualifie` / `sms_email` / …)_ |
| Règle sur la révocation a posteriori | _(à renseigner)_ |
| Délai de validité d'une demande signée | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Modèle `DemandeModification` + flags : [L3.1 § 2.9](../L3_1_modele_donnees.md).
- Service `appliquer_modification` : [L3.2 § 4.2](../L3_2_architecture_modulaire.md).
- Motif de refus `ACCORDS_MANQUANTS` : [L2.5 § 4](../L2_5_messages_systeme.md).
- Règle B-88.2 des accords art. 88 : [L2.2 § 2.9](../L2_2_regles_validation.md).
- Scellement et empreintes (fiche F6 à venir) : [L3.3](../L3_3_horodatage_scellement.md).
- Registre des arbitrages : [L11](../L11_tracabilite_articles_76_97.md).
