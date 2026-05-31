# Fiche MO — F6 — Scellement cryptographique (§ 6.3 TDR)

**Référence L11** : `L11/A5` (volet scellement — complémentaire à F4
qui traite le volet rendu documentaire).
**Articles fondateurs** : article 79 (conservation) ; TDR § 5.1,
§ 6.3 (point critique — scellement) ; § 4.2.5 (cohérence fichier public
/ certificat) ; art. 97 dernier alinéa (force probante).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/A5` — volet scellement cryptographique |
| Articles fondateurs | Art. 79, 97 ; TDR § 5.1, § 6.3, § 4.2.5 |
| Statut actuel | **STUB** — `RSM_SEAL_MODE=disabled` ; SHA-256 sans signature. Non opposable. |
| Dépendances | Lié à F4 (rendu documentaire) et F5 (source de temps) — l'opposabilité du scellement dépend d'un horodatage fiable |
| Impact transverse | Journal d'audit (chaînage), snapshots d'inscription, certificats, pièces jointes. |

---

## 2. Contexte juridique

### 2.1 Exigence du TDR § 6.3

> *« Scellement : chaque inscription, modification, radiation et
>   certificat émis est scellé (empreinte cryptographique) ; les
>   scellés sont conservés et vérifiables à tout moment. »*

### 2.2 Exigence du TDR § 5.1

> *« Scellement cryptographique des inscriptions : calcul d'une
>   empreinte (hachage) lors de l'enregistrement, conservation de
>   cette empreinte et possibilité de vérification ultérieure. »*

### 2.3 Exigence du TDR § 4.2.5 (point critique)

> *« Le certificat de recherche est admissible comme élément de preuve
>   devant une instance judiciaire et, en l'absence de preuve
>   contraire, constitue une preuve concluante quant aux points qu'il
>   atteste (article 97 dernier alinéa). La cohérence stricte entre
>   les données du fichier public au moment exact de la recherche
>   et le contenu du certificat doit être garantie techniquement. »*

### 2.4 Articulation avec l'art. 83 (réversibilité)

Les scellés produits par le système doivent rester **vérifiables après
transfert** de la tenue du Registre à un autre organisme. L'architecture
cryptographique ne doit donc pas créer de captivité.

### 2.5 Distinction F4 / F6

- **F4** traite le rendu documentaire (format PDF/A, disposition
  bilingue, signature du certificat comme document d'affichage).
- **F6** traite le scellement cryptographique en profondeur :
  empreintes du journal d'audit, des snapshots, des pièces jointes,
  et la **chaîne de confiance** qui rend vérifiable l'intégrité
  interne du système sur le long terme.

Les deux fiches peuvent converger vers une infrastructure commune
(HSM partagé, PKI partagée) mais adressent des enjeux différents.

### 2.6 Risques juridiques en l'absence d'arbitrage

- **Risque cardinal** : aucun scellement produit en mode STUB n'est
  opposable. Les empreintes SHA-256 détectent l'altération mais ne
  permettent pas d'attester l'**origine** — une empreinte peut être
  recalculée par quiconque dispose du contenu.
- **Risque R3 (L11)** : incohérence fichier public ↔ certificat de
  recherche non détectable avec certitude sans signature.
- **Risque R7 (L11)** : suppression accidentelle dans le journal
  d'audit — mitigée par les triggers SQL + overrides ORM (déjà en
  place), mais sans scellement opposable la chaîne reste
  auto-attestée.

---

## 3. Situation actuelle dans le système

### 3.1 Mécanismes déjà implémentés (indépendants du scellement)

| Mécanisme | État | Référence |
|-----------|:----:|-----------|
| Triggers PostgreSQL sur journal d'audit | ✅ | L3.5 § 2.1 |
| Overrides ORM `save()` / `delete()` sur modèles append-only | ✅ | L3.5 § 3.1 |
| Chaînage interne d'empreintes du journal d'audit (SHA-256) | ✅ | L3.5 § 3.5 |
| Canonicalisation déterministe des snapshots | ✅ | L3.3 § 4.2 |
| Empreintes SHA-256 sur snapshots et certificats | ✅ (STUB) | L3.1 |

### 3.2 Ce qui manque (zone gelée)

| Lacune | Conséquence |
|--------|-------------|
| Aucune signature cryptographique | Empreintes détectent l'altération mais pas l'origine |
| Aucune clé conservée après transfert (art. 83) | Un repreneur ne peut pas vérifier les scellés passés |
| Aucun horodatage qualifié intégré aux scellés | L'antériorité des scellés n'est pas prouvable sans F5 |
| Aucune autorité tierce attestant l'intégrité | Le système s'atteste lui-même |

### 3.3 Interface stable exposée

- `apps.core.scellement.sceller(bytes) → Sceau(empreinte_hex, algorithme, opposable)` ;
- `apps.core.scellement.verifier(bytes, sceau) → bool` ;
- `apps.modifications.serialisation.encoder_canonique(payload) → bytes` (canonicalisation déterministe).

L'interface est stable : l'activation passe par `RSM_SEAL_MODE` sans
modification du code métier.

### 3.4 Tests désactivés liés

- `test_api_zones_gelees.py::test_certificat_recherche_probant_genere`
- `test_api_zones_gelees.py::test_coherence_fichier_public_certificat`
- `test_api_zones_gelees.py::test_verification_certificat_apres_transfert`

### 3.5 Populations de données concernées

| Type de donnée | Volumétrie indicative | Sensibilité |
|----------------|-----------------------|-------------|
| Entrées du journal d'audit | Très élevée (plusieurs par opération métier) | Cardinale |
| Snapshots d'inscription | 1 à 2 par modification / renouvellement / radiation | Très élevée |
| Certificats émis | Forte volumétrie si recherche publique très utilisée | Très élevée (opposabilité) |
| Pièces jointes | Variable (radiations avec actes) | Élevée |

---

## 4. Options d'arbitrage

### 4.1 Option a — HMAC avec clé stockée en HSM

**Description** : chaque scellé est un **HMAC-SHA-256** (ou HMAC-SHA-3)
produit avec une clé maître conservée dans un HSM certifié
(FIPS 140-2 niveau 3 ou équivalent Common Criteria). La vérification
exige l'accès à la clé (ou à un service d'audit exposé par le HSM).

| Dimension | Évaluation |
|-----------|------------|
| Sécurité intrinsèque | 🟢 Élevée si clé bien protégée |
| Vérifiabilité par un tiers | 🟠 **Limitée** — la clé doit être partagée ou un service HSM doit être exposé |
| Opposabilité juridique | 🟠 **Intermédiaire** — un HMAC ne prouve pas l'origine (tout détenteur de la clé peut produire) |
| Coût | 🟠 Modéré — HSM unique |
| Dépendance fournisseur | 🔴 Dépendant du HSM choisi |
| Réversibilité (art. 83) | 🟠 Clé à transférer, ou scellements historiques à ré-émettre |
| Vitesse | 🟢 Très rapide (HMAC ~microsecondes) |
| Mutualisation F5 (horloge HSM) | 🟢 Oui |

**Avantages** : simple, rapide, faible coût récurrent.
**Inconvénients** : ne prouve pas l'origine ; difficulté de
vérification par un tiers sans accès à la clé.

### 4.2 Option b — Signature asymétrique (RSA-PSS ou ECDSA)

**Description** : chaque scellé est une **signature numérique**
produite avec une clé privée conservée dans un HSM. La **clé
publique** est largement diffusée (autorités judiciaires, site
public du Tribunal, archives). Tout tiers peut vérifier le scellé
sans accès à la clé privée.

| Dimension | Évaluation |
|-----------|------------|
| Sécurité intrinsèque | 🟢 Très élevée |
| Vérifiabilité par un tiers | 🟢 **Maximale** — clé publique diffusée |
| Opposabilité juridique | 🟢 **Maximale** — prouve l'origine ET l'intégrité |
| Coût | 🔴 Plus élevé — HSM + distribution de la clé publique |
| Dépendance fournisseur | 🟠 HSM du MO |
| Réversibilité (art. 83) | 🟢 La clé publique reste vérifiable même après transfert ; les scellés historiques restent opposables |
| Vitesse | 🟠 Plus lent que HMAC (millisecondes par signature) |
| Rotation de clés | 🟠 À planifier (ré-signature des scellés vivants) |
| Mutualisation F3/F4 | 🟢 Possible — même HSM pour signer les certificats |

**Avantages** : opposabilité maximale, vérification universelle,
conforme à l'esprit eIDAS / standards internationaux.
**Inconvénients** : coût plus élevé, plan de rotation des clés à
gérer sur le long terme.

### 4.3 Option c — Chaînage cryptographique append-only renforcé (arbre de Merkle + ancrage externe)

**Description** : approche de type « blockchain » interne. Le journal
d'audit (déjà chaîné par SHA-256) est consolidé périodiquement
(chaque heure, chaque jour) en un **arbre de Merkle**. La **racine
de Merkle** est ensuite ancrée périodiquement dans un service externe
de confiance :
- **Ancrage dans un journal public signé** par une autorité tierce
  (TSA avec RFC 3161) ;
- **Ancrage dans un registre distribué** (blockchain publique ou
  privée consortium).

L'intégrité interne est garantie par le chaînage ; l'**origine et
l'antériorité** sont garanties par l'ancrage externe.

| Dimension | Évaluation |
|-----------|------------|
| Sécurité intrinsèque | 🟢 Très élevée |
| Vérifiabilité par un tiers | 🟢 Élevée — via la racine ancrée |
| Opposabilité juridique | 🟢 **Élevée** — standard établi (eIDAS qualifie les services de preuve par chaînage ancré) |
| Coût | 🟠 Modéré (fréquence d'ancrage à ajuster) |
| Dépendance externe | 🟠 Ancrage TSA ou registre distribué |
| Réversibilité (art. 83) | 🟢 Les racines ancrées restent vérifiables |
| Complexité | 🔴 Élevée |
| Vitesse | 🟢 Scellement interne rapide ; latence d'ancrage en arrière-plan |
| Mutualisation | 🟠 Indépendant de F3/F4 (peut s'ajouter en plus) |

**Avantages** : intégrité démontrable sans dépendre d'une clé unique ;
résilience (même en cas de compromission de la clé, la chaîne déjà
ancrée reste attestée).
**Inconvénients** : mise en œuvre plus complexe ; choix d'un
registre d'ancrage nécessite une décision politique et technique.

### 4.4 Option d — Combinaison signature asymétrique + chaînage ancré

**Description** : option b **et** option c combinées.
- Chaque scellé est signé asymétriquement (HSM, clé publique diffusée).
- Le journal d'audit est chaîné SHA-256 **et** sa racine est ancrée
  périodiquement dans un service tiers (TSA ou blockchain).

C'est le niveau de protection **maximal** : les scellés sont opposables
individuellement (signature) ET attestés collectivement (chaînage
ancré).

| Dimension | Évaluation |
|-----------|------------|
| Sécurité intrinsèque | 🟢 **Maximale** |
| Vérifiabilité par un tiers | 🟢 Double (individuelle + collective) |
| Opposabilité juridique | 🟢 **Maximale** |
| Coût | 🔴 Élevé |
| Complexité | 🔴 Élevée |
| Réversibilité | 🟢 Maximale (clé publique + ancrages externes) |

**Avantages** : défense en profondeur cryptographique.
**Inconvénients** : coût et complexité cumulés.

### 4.5 Option e — HMAC simple + empreinte conservée au journal d'audit (scellement interne renforcé)

**Description** : en l'absence d'infrastructure HSM ou PKI disponible,
le système reste en SHA-256 (pas de signature) **mais** :
- chaque scellé est inscrit immédiatement au journal d'audit (déjà
  chaîné append-only) ;
- la chaîne d'empreintes du journal est vérifiée régulièrement ;
- le journal est **sauvegardé hors site** avec empreinte globale
  datée par l'exploitant.

La valeur probante repose sur la conservation pérenne + la
vérification de la chaîne, en l'absence d'autorité tierce.

| Dimension | Évaluation |
|-----------|------------|
| Sécurité intrinsèque | 🟠 Modérée (auto-attestation) |
| Vérifiabilité par un tiers | 🟠 Dépend de la crédibilité de l'exploitant |
| Opposabilité juridique | 🟠 Intermédiaire |
| Coût | 🟢 Très faible |
| Complexité | 🟢 Faible |
| Réversibilité | 🟢 Totale (logiciel standard) |
| Adéquation transitoire | 🟢 Utilisable comme palier avant infrastructure |

**Avantages** : déploiement immédiat, coût nul.
**Inconvénients** : opposabilité juridique limitée, dépend de la
crédibilité institutionnelle du greffe.

### 4.6 Option f — Approche hybride progressive

**Description** : démarrage en option e (scellement interne) pour une
mise en service immédiate. Bascule vers option b (signature
asymétrique) dès que la PKI est opérationnelle. Ajout ultérieur de
l'ancrage (option c) si le MO juge nécessaire un niveau supérieur.

| Dimension | Évaluation |
|-----------|------------|
| Adéquation rapide | 🟢 Mise en service immédiate |
| Évolutivité | 🟢 Trois paliers possibles |
| Coût total | 🟠 Modéré à élevé selon palier final |
| Conformité § 6.3 initiale | 🟠 Partielle |
| Conformité § 6.3 finale | 🟢 Stricte |

**Avantages** : pragmatisme opérationnel.
**Inconvénients** : plusieurs migrations successives ; période
initiale avec conformité § 6.3 partielle.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Adaptateur à câbler |
|--------|---------------------|
| a | Client PKCS#11 du HSM + calcul HMAC |
| b | Client PKCS#11 + bibliothèque de signature (RSA-PSS, ECDSA) |
| c | Bibliothèque arbre de Merkle + client TSA ou blockchain |
| d | Options b + c combinées |
| e | Aucun adaptateur externe ; modifications mineures dans `apps.core.scellement` |
| f | Parcours a/e → b → c |

L'interface `sceller() / verifier()` reste stable ; `Sceau.algorithme`
et `Sceau.opposable` reflètent le mode actif.

### 5.2 Impacts sur les tests

- Activation des 3 tests `@arbitrage_mo("L11/A5", …)`.
- Nouveau test : rotation de clé — un scellé émis sous clé K1 reste
  vérifiable après passage à K2.
- Nouveau test : simulation d'ancrage externe — la racine du journal
  d'audit à T0 correspond à la racine ancrée au service tiers.
- Nouveau test : vérification post-transfert — un système B vérifie
  un scellé issu du système A avec la seule clé publique.

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L3.3 § 4 | Section « modes cibles » renseignée |
| L3.5 | Mise à jour du rempart cryptographique |
| L3.6 | Démonstration d'équivalence FR/AR consolidée avec scellés |
| L11 | Passage de `L11/A5` (volet scellement) à IMPLÉMENTÉ ; évolution du risque R3 et R7 |

### 5.4 Dépendances transversales

- **F5 (source de temps)** : l'opposabilité d'un scellé dépend de
  l'opposabilité de son horodatage. Les options F6/F5 sont à arbitrer
  conjointement. Si F5 option c (HSM) est retenue, mutualisation
  naturelle avec F6 option a/b (HSM).
- **F4 (rendu documentaire)** : un certificat signé (F4 option a) est
  déjà un scellé. Éviter le double scellement — la fiche F4 couvre
  le « certificat comme document » ; F6 couvre le « scellement du
  système » (snapshots, audit, etc.).
- **F3 (signature électronique art. 88)** : même PKI possible.

### 5.5 Impacts sur l'exploitation

- Gestion du cycle de vie des clés (génération, activation,
  rotation, révocation).
- Publication et conservation de la clé publique (option b, d).
- Fréquence d'ancrage (option c, d, f palier c) — compromis entre
  coût et fraîcheur de la preuve.
- Procédure post-incident : que faire si une clé est compromise ?
  Ré-émettre tous les scellés ? Invalider la période ?
- Supervision : alerte en cas d'échec d'ancrage ou de dérive de la
  chaîne.

---

## 6. Tradeoffs synthétiques

| Critère | a (HMAC+HSM) | b (Signature PKI) | c (Chaînage ancré) | d (Signature + ancrage) | e (Interne renforcé) | f (Paliers) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| Sécurité intrinsèque | Élevée | Très élevée | Très élevée | Maximale | Modérée | Évolutive |
| Vérifiabilité par tiers sans accès à clé | Limitée | Maximale | Élevée | Maximale | Limitée | Évolutive |
| Opposabilité juridique | Intermédiaire | Maximale | Élevée | Maximale | Intermédiaire | Évolutive |
| Coût déploiement | Modéré | Élevé | Modéré | Élevé | Faible | Progressif |
| Coût récurrent | Faible | Moyen | Moyen | Élevé | Nul | Évolutif |
| Complexité | Faible | Moyenne | Élevée | Élevée | Faible | Croissante |
| Mutualisation avec F3/F4/F5 | Oui (HSM) | Oui (HSM + PKI) | Non directe | Oui | Non | Possible ensuite |
| Résilience en cas de compromission | Modérée | Modérée | **Élevée** | **Maximale** | Faible | Évolutive |
| Délai de mise en service | Moyen | Long | Moyen | Long | Très court | Très court puis progressif |
| Réversibilité (art. 83) | Modérée | Élevée | Élevée | Élevée | Totale | Évolutive |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Infrastructure HSM** : existe-t-elle déjà au sein du Tribunal ou
   du ministère ? Budget d'acquisition ?
2. **Infrastructure PKI** : interne (MO) ou adossée à une PKI
   nationale ? Autorité de certification émettrice ?
3. **Service d'ancrage externe** (si option c, d, f) : TSA ?
   blockchain ? consortium sectoriel ? registre notarial national ?
4. **Politique de rotation des clés** : durée de vie, procédure de
   renouvellement, traitement des scellés sous ancienne clé.
5. **Publication de la clé publique** : modalités (site officiel,
   bulletin du Tribunal, archives nationales).
6. **Fréquence d'ancrage** (option c, d) : temps réel, horaire,
   quotidien, hebdomadaire ?
7. **Périmètre des éléments scellés** : uniquement journal d'audit et
   snapshots, ou également chaque certificat, chaque pièce jointe,
   chaque modification individuelle ?
8. **Gestion d'une compromission** : scénario de compromission de la
   clé privée et procédure de remise en confiance.
9. **Arbitrage conjoint F5 / F6** : le MO envisage-t-il un choix
   conjoint de l'infrastructure (HSM commun pour horloge + clés) ?
10. **Compatibilité avec archives nationales** : format des scellés
    exportables pour versement aux archives publiques.

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ autre : ______ |
| Infrastructure HSM | _(à renseigner)_ |
| Infrastructure PKI | _(à renseigner)_ |
| Service d'ancrage (si applicable) | _(à renseigner)_ |
| Valeur arbitrée de `RSM_SEAL_MODE` | _(à renseigner — `hmac`, `asymmetric_signature`, `chained_log`, …)_ |
| Politique de rotation | _(à renseigner)_ |
| Périmètre scellé | _(à renseigner)_ |
| Fréquence d'ancrage | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Service `sceller()` / `verifier()` : [apps/core/scellement.py](../../backend/apps/core/scellement.py).
- Canonicalisation déterministe : [apps/modifications/serialisation.py](../../backend/apps/modifications/serialisation.py).
- Chaînage du journal d'audit : [L3.5 § 3.5](../L3_5_securite_integrite.md).
- Modèle `SnapshotInscription` : [L3.1 § 2.9](../L3_1_modele_donnees.md).
- Politique d'horodatage et de scellement : [L3.3 § 4](../L3_3_horodatage_scellement.md).
- Fiche F4 (volet rendu documentaire) : [F4_charte_documentaire_certificats.md](F4_charte_documentaire_certificats.md).
- Fiche F5 (source de temps) : [F5_source_de_temps.md](F5_source_de_temps.md) — mutualisation possible.
- Risques R3, R7 : [L11](../L11_tracabilite_articles_76_97.md).
