# Fiche MO — F4 — Charte documentaire et certificats probants (art. 97)

**Référence L11** : `L11/A5` (volet rendu documentaire — le volet
scellement cryptographique fait l'objet de la fiche F6 au Tour 2).
**Articles fondateurs** : article 97 al. 3 et dernier alinéa ;
articles 78, 86, 88-92 ; TDR § 4.2.5 (point critique), § 7.5.

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/A5` — Charte documentaire et certificats probants |
| Articles fondateurs | Art. 78 al. 3 (certificat d'inscription), art. 86 in fine, art. 88-92 (certificats de modification / renouvellement / radiation), art. 97 al. 3 et dernier alinéa (certificat de recherche probant) ; TDR § 4.2.5, § 7.5 |
| Statut actuel | **STUB** — `Certificat.probant = False` pour tous les certificats produits. Rendu PDF/A non câblé. |
| Dépendances | Lié à F3 (signature électronique — si la PKI retenue pour F3 sert à signer les certificats, mutualisation possible) et à F6 (scellement cryptographique, Tour 2). |
| Impact transverse | 5 types de certificats × 3 langues de génération (`fr`, `ar`, `fr-ar`) × valeur probante. |

---

## 2. Contexte juridique

### 2.1 Exigences du décret

| Article | Exigence |
|---------|----------|
| Art. 78 al. 3 | « Il est attribué à cette inscription un certificat portant un numéro de série… » |
| Art. 86 in fine | Le greffier délivre copie de l'inscription au demandeur. |
| Art. 88-92 | Les modifications, renouvellements et radiations donnent lieu à des certificats correspondants (implicite, par parallélisme avec art. 78). |
| **Art. 97 al. 3** | « À l'issue de la recherche, le Registre délivre un certificat de recherche, sur support papier ou électronique au choix du requérant, reflétant le résultat de la recherche. » |
| **Art. 97 dernier al.** (point critique) | « Le certificat de recherche est admissible comme élément de preuve devant une instance judiciaire et, en l'absence de preuve contraire, constitue une preuve concluante quant aux points qu'il atteste. » |

### 2.2 Exigences du TDR § 7.5

> *« Tous les certificats — d'inscription, de modification, de
>   renouvellement, de radiation, de recherche — peuvent être
>   produits en français, en arabe ou en version bilingue.
>   Le contenu juridique est strictement équivalent entre les
>   versions linguistiques. L'équivalence est documentée dans un
>   plan de tests dédié. La version bilingue fait apparaître côte à
>   côte, sur le même document, les deux textes, avec une mise en
>   page soignée pour l'arabe en écriture de droite à gauche. »*

### 2.3 Point critique TDR § 4.2.5

> *« Le certificat de recherche est admissible comme élément de
>   preuve devant une instance judiciaire […]. La cohérence stricte
>   entre les données du fichier public au moment exact de la
>   recherche et le contenu du certificat doit être garantie
>   techniquement. »*

### 2.4 Risques juridiques en l'absence d'arbitrage

- **Certificats non probants** : tant que la charte documentaire et
  le scellement ne sont pas arbitrés, aucun certificat émis par le
  système n'est opposable devant un tribunal. L'art. 97 dernier al.
  reste inopérant.
- **Risque de divergence FR/AR** : en l'absence de charte documentaire
  validée, la mise en page bilingue (RTL pour l'arabe, polices,
  ordre des blocs) peut varier, compromettant l'équivalence § 7.5.
- **Risque de conservation** : un format documentaire non pérenne
  (PDF standard sans archivage) peut devenir illisible avec les
  années, en contradiction avec l'art. 79.
- **Risque sur la vérifiabilité après transfert (art. 83)** : un
  certificat non vérifiable hors du système d'origine remet en cause
  la réversibilité.

---

## 3. Situation actuelle dans le système

### 3.1 Mécanisme en place

| Élément | État |
|---------|------|
| `Certificat.type_certificat` | 5 valeurs de l'enum `TypeCertificat` (inscription, modification, renouvellement, radiation, recherche) |
| `Certificat.langue_generation` | 3 valeurs : `fr`, `ar`, `fr-ar` |
| `Certificat.probant` | **Toujours `False`** tant que scellement et horodatage ne sont pas arbitrés |
| `Certificat.empreinte` | SHA-256 STUB du contenu canonique |
| `Certificat.contenu_json` | Sérialisation canonique bilingue (données neutres + libellés) |
| `Certificat.fichier_pdf` | Non câblé — aucune génération PDF/A |
| Service | `preparer_certificat(type, contenu, langue)` dans `apps.certificats.services` |
| Paramètre env | `RSM_SEAL_MODE=disabled` (volet scellement) |
| Tests désactivés | 3 placeholders `@arbitrage_mo("L11/A5", …)` dans `test_api_zones_gelees.py` |

### 3.2 Points d'extension prévus

- Interface stable `preparer_certificat` : attend uniquement un payload
  bilingue neutre, la charte est appliquée par un moteur de rendu
  séparé.
- Bibliothèques déjà dans `requirements.txt` : `reportlab`, `arabic-reshaper`,
  `python-bidi` — structurelles, jamais exécutées pour produire un
  document opposable en STUB.
- Avertissement `zone_gelee.certificat_probant.inactif` émis
  automatiquement à chaque appel de `preparer_certificat`.

### 3.3 Populations concernées

| Certificat | Destinataires | Volume typique |
|------------|---------------|:--------------:|
| Inscription (art. 78) | Déposant, créancier, constituant | 1 par inscription validée |
| Modification | Déposant, parties accordantes | 1 par modification appliquée |
| Renouvellement | Déposant | 1 par renouvellement |
| Radiation | Demandeur de radiation | 1 par radiation |
| **Recherche** (art. 97) | Tout intéressé (public) | **Volume potentiellement élevé** |

---

## 4. Options d'arbitrage

### 4.1 Option a — PDF/A-3 avec signature numérique embarquée (PAdES)

**Description** : chaque certificat est rendu au format **PDF/A-3**
(norme ISO 19005-3, archivage long terme) avec la signature
numérique embarquée au format **PAdES** (PDF Advanced Electronic
Signatures). Format bilingue côte à côte : bloc FR à gauche (LTR),
bloc AR à droite (RTL), avec polices embarquées pour les deux
scripts. La signature couvre l'ensemble du fichier.

| Dimension | Évaluation |
|-----------|------------|
| Conservation pérenne | 🟢 **Maximale** — PDF/A est conçu pour l'archivage ISO |
| Opposabilité | 🟢 **Maximale** — signature embarquée vérifiable par toute partie |
| Vérifiabilité post-transfert (art. 83) | 🟢 Vérifiable hors ligne par un lecteur PDF standard |
| Polices arabes | 🟢 Embarquées (Amiri, Noto Naskh, etc.) |
| Mise en page bilingue | 🟢 Côte à côte (§ 7.5) |
| Complexité de production | 🟠 Modérée — bibliothèques matures (reportlab + signature PAdES) |
| Taille de fichier | 🟠 Modérée — polices embarquées augmentent la taille |
| Dépendance PKI | 🔴 Dépend du choix F3 (clé privée de signature) |

**Avantages** : standard international, archivage pérenne, opposable
sans dépendance au système d'origine.
**Inconvénients** : exige une PKI pour la signature (F3) ;
bibliothèques PAdES plus complexes que la signature détachée.

### 4.2 Option b — PDF/A-3 + signature détachée (XAdES ou CAdES)

**Description** : le certificat est rendu au format PDF/A-3 (même que
option a pour le rendu). La **signature est produite séparément**
au format XAdES (XML) ou CAdES (CMS), portant sur l'empreinte du PDF.
Le greffe délivre **deux fichiers** : le PDF du certificat et le
fichier de signature. La vérification exige les deux.

| Dimension | Évaluation |
|-----------|------------|
| Conservation pérenne | 🟢 PDF/A + signature normalisée |
| Opposabilité | 🟢 Élevée — dépend du maintien des deux fichiers |
| Vérifiabilité post-transfert | 🟢 Outils standards (xmlsectool, OpenSSL) |
| Polices arabes | 🟢 Identique à option a |
| Risque pratique | 🔴 **Perte d'un fichier** : si le signataire ne conserve que le PDF sans la signature détachée, il perd la valeur probante |
| Complexité de production | 🟢 Plus simple que PAdES |
| Dépendance PKI | 🔴 Idem option a |

**Avantages** : plus simple techniquement, meilleure séparation des
responsabilités (le PDF est lisible par tous, la signature est
vérifiée par ceux qui en ont besoin).
**Inconvénients** : risque opérationnel de perte de la signature
détachée par l'utilisateur.

### 4.3 Option c — Format hybride : XML signé + rendu PDF dérivé

**Description** : la **source canonique** du certificat est un **XML
signé** (XAdES) ; le PDF/A est **dérivé** du XML à la demande, pour
lecture humaine. La valeur probante réside dans le XML ; le PDF est
une commodité d'affichage. Toute divergence entre les deux est
détectable (empreinte croisée). Convient particulièrement à la
conservation et à l'interopérabilité avec d'autres registres
(OHADA, cadastre, etc.).

| Dimension | Évaluation |
|-----------|------------|
| Conservation pérenne | 🟢 Source XML facilement archivable et réinterprétable |
| Opposabilité | 🟢 Élevée (XAdES) |
| Vérifiabilité | 🟢 Multiples outils XML standards |
| Polices arabes | 🟢 Gérées au rendu PDF |
| Interopérabilité | 🟢 **Maximale** — XML échangeable entre systèmes |
| Complexité de production | 🔴 Plus élevée — pipeline XML → PDF |
| Dépendance PKI | 🔴 Idem |

**Avantages** : interopérabilité avec d'autres SI, séparation propre
des couches.
**Inconvénients** : complexité technique ; l'utilisateur final peut
confondre PDF (commodité) et XML (valeur probante).

### 4.4 Option d — PDF standard + timestamp RFC 3161 (sans signature embarquée)

**Description** : en l'absence de PKI nationale opérationnelle, le
certificat est rendu au format PDF/A-3 (sans signature embarquée) mais
accompagné d'un **horodatage qualifié** au format RFC 3161, produit
par une autorité d'horodatage (TSA) reconnue. L'horodatage atteste
de l'existence du document à une date certaine. La signature est
apposée ultérieurement si et quand une PKI devient disponible
(bascule sans retravail du contenu).

| Dimension | Évaluation |
|-----------|------------|
| Conservation pérenne | 🟢 PDF/A-3 |
| Opposabilité | 🟠 Intermédiaire — horodatage seul atteste l'antériorité, pas l'origine |
| Vérifiabilité | 🟢 Timestamp RFC 3161 largement supporté |
| Accessibilité | 🟢 Pas de PKI requise au démarrage |
| Évolutivité | 🟢 Bascule vers option a ou b ultérieure possible |
| Dépendance | 🟠 TSA externe (plusieurs fournisseurs possibles) |

**Avantages** : déploiement rapide, sans attendre la PKI ;
évolutivité vers une signature complète.
**Inconvénients** : force probante moindre qu'un certificat signé.

### 4.5 Option e — Rendu bilingue + délivrance papier avec tampon du greffe

**Description** : pendant une période transitoire, les certificats
sont produits en **papier** avec la signature manuscrite du greffier
et le tampon officiel. Le format numérique (PDF) est fourni à titre
d'information sans valeur probante. La bascule vers un certificat
électronique probant est programmée après mise en place de la PKI.

| Dimension | Évaluation |
|-----------|------------|
| Conservation | 🟢 Pratique traditionnelle connue |
| Opposabilité | 🟢 Maximale (authentique si tampon) |
| Vérifiabilité électronique | 🔴 Nulle côté numérique |
| Accessibilité | 🔴 Contrainte du guichet |
| Conformité art. 97 al. 3 (« support électronique au choix du requérant ») | 🟠 Option de choix restreinte côté requérant |
| Coût de déploiement | 🟢 Très faible |

**Avantages** : simplicité et sécurité juridique immédiate.
**Inconvénients** : contraire à l'esprit de dématérialisation du
système, limite le choix ouvert par l'art. 97.

### 4.6 Option f — Charte minimale avec scellement SHA-256 + conservation interne

**Description** : rendu PDF/A-3 bilingue **sans signature** mais avec
empreinte SHA-256 imprimée sur le document et stockée dans le journal
d'audit. La valeur probante repose sur la correspondance entre le PDF
délivré et l'empreinte conservée pérennement dans le journal
append-only (§ 5.2). Un utilisateur peut, à tout moment, vérifier la
non-altération du PDF en recalculant son SHA-256 et en le comparant à
l'entrée d'audit.

| Dimension | Évaluation |
|-----------|------------|
| Conservation pérenne | 🟢 PDF/A |
| Opposabilité | 🟠 **Intermédiaire** — l'empreinte dans le journal atteste la délivrance mais ne signe pas l'émetteur |
| Vérifiabilité | 🟢 Outils standards (sha256sum) |
| Dépendance | 🟢 Aucune externe |
| Post-transfert (art. 83) | 🟢 Le journal d'audit est cessible ; la vérification reste possible |
| Coût | 🟢 Très faible |

**Avantages** : aucun prérequis externe, déploiement rapide.
**Inconvénients** : n'établit pas la paternité du document, juste
son intégrité.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Composant | Impact |
|-----------|--------|
| `Certificat.fichier_pdf` | Sera peuplé par le moteur de rendu (aujourd'hui vide) |
| `apps.certificats.services.preparer_certificat` | Doit invoquer le moteur de rendu et, selon option, le signataire |
| Nouveau module | `apps.certificats.moteur_rendu` — conversion `contenu_json` → PDF/A |
| Dépendances à ajouter | Librairie de signature PAdES/XAdES si options a, b, c |
| Librairies déjà prévues | `reportlab` (rendu), `arabic-reshaper`, `python-bidi` (RTL arabe) |
| Paramètre env | `RSM_SEAL_MODE` bascule vers le mode actif retenu |

### 5.2 Impacts sur les tests

- Activation de `test_api_zones_gelees.py::test_certificat_recherche_probant_genere`.
- Activation de `test_api_zones_gelees.py::test_coherence_fichier_public_certificat`.
- Activation de `test_api_zones_gelees.py::test_verification_certificat_apres_transfert`.
- Nouveau test : identité stricte du contenu juridique entre les
  versions FR, AR et bilingue d'un même certificat (§ 7.5 — preuve
  par sérialisation canonique).
- Nouveau test : vérification post-transfert simulée — un certificat
  délivré par le système A est vérifié par un système B disposant
  uniquement du journal d'audit et des clés publiques.

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 § 2.2, § 8.2 | Délivrance du certificat : format et canal selon l'option |
| L2.5 § 9.3 | `notification.certificat.emission` peut être activée |
| L3.1 § 2.12 | Ajout éventuel de champs : `format`, `horodatage_signature`, `reference_externe` |
| L3.3 § 4 | Alignement sur le scellement retenu (F6) |
| L3.5 | Mise à jour de la section dispositifs de sécurité |
| L11 Registre | Passage du volet rendu documentaire de `L11/A5` à IMPLÉMENTÉ |

### 5.4 Dépendances transversales avec d'autres fiches

- **F1 (glossaire)** : la charte documentaire utilise le glossaire
  validé — aucun certificat opposable ne peut être émis avant
  validation de F1.
- **F3 (signature électronique art. 88)** : si la même infrastructure
  PKI est retenue, mutualisation avec F4.
- **F6 (scellement cryptographique — Tour 2)** : volet frère de F4 ;
  F4 traite le rendu documentaire, F6 traite le scellement profond
  (snapshots, journal d'audit, chaîne).
- **F5 (source de temps — Tour 2)** : l'horodatage du certificat
  dépend de la source arbitrée. Sans F5, aucun certificat n'est
  pleinement opposable au sens de l'art. 78 al. 3.

### 5.5 Impacts sur l'exploitation

- **Volumétrie** : les certificats de recherche (art. 97) peuvent
  représenter le volume dominant. Estimation indicative : si la
  recherche publique est très utilisée, plusieurs centaines de
  certificats générés par jour en production.
- **Stockage** : les PDF/A sont plus volumineux que les PDF standards
  (polices embarquées). Dimensionnement à prévoir.
- **Performance** : génération de PDF/A en temps réel — à
  benchmarker. L'asynchronisme (file d'attente + notification de
  disponibilité) peut être nécessaire pour les certificats de
  recherche volumineux.
- **Révocation** : politique à définir si un certificat délivré doit
  être révoqué (ex. détection ultérieure d'une altération du fichier
  public à l'instant T de la recherche).

---

## 6. Tradeoffs synthétiques

| Critère | a (PAdES embarqué) | b (PDF/A + sig. détachée) | c (XML signé + PDF dérivé) | d (PDF/A + timestamp RFC 3161) | e (Papier transitoire) | f (Empreinte SHA-256 interne) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| Opposabilité juridique | Maximale | Élevée | Maximale | Intermédiaire | Maximale (papier) | Intermédiaire |
| Conservation pérenne | Excellente | Excellente | Excellente | Excellente | Dépend | Très bonne |
| Vérifiabilité (art. 83) | Oui, hors ligne | Oui, 2 fichiers | Oui (XML) | Oui (timestamp) | Non (numérique) | Oui (journal + PDF) |
| Interopérabilité avec d'autres SI | Bonne | Bonne | **Excellente** | Bonne | Faible | Modérée |
| Complexité de mise en œuvre | Modérée | Faible | Élevée | Faible | Très faible | Faible |
| Dépendance à une PKI | Oui | Oui | Oui | Oui (TSA) | Non | Non |
| Délai de déploiement | Moyen | Court | Long | Court | Immédiat | Court |
| Adéquation à une mise en production rapide | Moyenne | Bonne | Faible | Bonne | Excellente | Excellente |
| Couverture art. 97 dernier al. | Maximale | Élevée | Maximale | Partielle | Conforme (papier) | Partielle |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Format officiel du document** (PDF/A-3 recommandé par
   l'archivage international ; autre format à défendre
   explicitement).
2. **Disposition bilingue** : côte à côte (§ 7.5 TDR) ou séquentielle
   (blocs FR puis AR) ?
3. **Polices arabes officielles** : Amiri, Noto Naskh, Scheherazade,
   ou police officielle mauritanienne ?
4. **Langue de délivrance par défaut** : au choix du requérant
   (art. 97 al. 3), mais faut-il une langue par défaut en l'absence
   de précision ? FR ? AR ? bilingue ?
5. **Reconnaissance d'une TSA** (option d) : autorité retenue,
   licence d'usage.
6. **Politique de conservation des certificats** : durée de
   stockage serveur, éventuelle purge / transfert aux archives.
7. **Politique de révocation** : conditions, procédure, mention sur
   le certificat lui-même.
8. **Certificats de recherche — canal de délivrance** : téléchargement
   immédiat, envoi différé, retrait au guichet ?
9. **Mention de non-opposabilité** pendant la phase transitoire :
   comment l'indiquer sur les certificats (si options d, e, f, ou si
   la bascule vers a/b/c est progressive) ?
10. **Intégration avec F3** : si F3 retient une PKI, F4 peut-elle
    réutiliser la même infrastructure ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ autre : ______ |
| Format arbitré | _(à renseigner — ex. PDF/A-3 + PAdES)_ |
| Polices arabes | _(à renseigner)_ |
| Disposition bilingue | _(à renseigner — côte à côte / séquentielle)_ |
| Langue par défaut | _(à renseigner)_ |
| TSA retenue (si applicable) | _(à renseigner)_ |
| Valeur arbitrée de `RSM_SEAL_MODE` | _(à renseigner — `hmac`, `asymmetric_signature`, `chained_log`, ou valeur nouvelle)_ |
| Politique de révocation | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Modèle `Certificat` : [L3.1 § 2.12](../L3_1_modele_donnees.md).
- Service `preparer_certificat` : [apps/certificats/services.py](../../backend/apps/certificats/services.py).
- Politique de scellement (volet F6 Tour 2) : [L3.3 § 4](../L3_3_horodatage_scellement.md).
- Formulaire de recherche et certificat associé : [L2.1 § 6](../L2_1_formulaires_bilingues.md).
- Règle G-97.2 : [L2.2 § 2.16](../L2_2_regles_validation.md).
- Messages système liés aux certificats : [L2.5 § 9.3](../L2_5_messages_systeme.md).
- Réversibilité art. 83 : [L3.2 § 10](../L3_2_architecture_modulaire.md).
- Matrice bilingue § 6 (Documents officiels bilingues) : [L3.6](../L3_6_matrice_bilingue.md).
- Registre des arbitrages : [L11](../L11_tracabilite_articles_76_97.md).
