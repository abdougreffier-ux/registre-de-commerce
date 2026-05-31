# Fiche MO — F5 — Source de temps officielle (art. 78)

**Référence L11** : `L11/horodatage`
**Articles fondateurs** : article 78 alinéas 2, 3, 4 ; articles 87,
90, 91, 92 al. 3 ; TDR § 5.1 (point critique — horodatage fiable),
§ 6.3.

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/horodatage` — Source de temps officielle |
| Articles fondateurs | Art. 78 al. 2 (ordre d'arrivée), al. 3 (prise d'effet à la saisie), al. 4 (numéro d'ordre horodaté à la seconde) ; art. 87, 90 al. 1 (prise d'effet des modifications) ; art. 91, 92 al. 3 (expiration, transfert) ; TDR § 5.1 |
| Statut actuel | **STUB** — `RSM_TIMESOURCE_MODE=local_stub` ; tous les horodatages sont produits par `timezone.now()` (horloge serveur Django). Non opposables. |
| Dépendances | Conditionne l'opposabilité de tout acte du système (inscription, modification, renouvellement, radiation, recherche). Lien étroit avec F6 (scellement) et F7 (distinction horodatage arrivée / saisie). |
| Impact transverse | Toutes les inscriptions ; toutes les transitions ; tous les snapshots ; tout le journal d'audit ; tous les certificats. |

---

## 2. Contexte juridique

### 2.1 Exigence de l'article 78

| Alinéa | Exigence |
|:------:|----------|
| al. 2 | « Les demandes sont enregistrées dans l'ordre de leur date d'arrivée. » |
| al. 3 | « L'inscription prend effet à la date et à l'heure auxquelles les informations sont saisies dans le fichier du Registre de façon à être accessibles aux personnes effectuant une recherche. » |
| al. 4 | « Il est attribué à cette inscription un certificat portant un numéro de série formé d'un numéro d'ordre suivi de l'année, du mois, du jour, de l'heure, de la minute et des secondes. » |

L'art. 78 impose donc une **horloge à la seconde** qui fonde :
- la chronologie d'arrivée (rang des inscriptions) ;
- la prise d'effet juridique (opposabilité aux tiers) ;
- la composition du numéro d'ordre (identifiant unique opposable).

### 2.2 Exigences du TDR § 5.1 (point critique)

> *« Horloge serveur fiable et surveillée, synchronisée sur une source
>   de temps de confiance : compte tenu de l'exigence d'horodatage à
>   la seconde portée par l'article 78, toute dérive non détectée
>   porte atteinte à la valeur juridique des inscriptions. »*

Le TDR qualifie explicitement l'horodatage comme un **point critique**.

### 2.3 Exigences TDR complémentaires

- § 5.1 : « Le système doit s'appuyer sur une source de temps
  centrale, tracée, supervisée et protégée contre toute manipulation,
  y compris par un administrateur technique. »
- § 6.3 : l'unicité de la base et la neutralité linguistique du
  stockage n'ont de sens que si les horodatages ont eux-mêmes une
  valeur juridique.

### 2.4 Risques juridiques en l'absence d'arbitrage

- **Risque cardinal** : aucune inscription produite en mode STUB n'est
  juridiquement opposable (art. 78 al. 3 inopérant).
- **Risque de contestation** du rang d'une inscription (art. 78 al. 2)
  si un contentieux oppose deux déposants dont les demandes ont
  été soumises à quelques secondes d'intervalle.
- **Risque de dérive d'horloge** invisible (serveur mal synchronisé,
  manipulation par un administrateur technique) : risque R1 du L11.
- **Risque de non-reproductibilité** du numéro d'ordre en cas de
  contentieux si l'instant auquel il a été produit n'est pas
  vérifiable.

---

## 3. Situation actuelle dans le système

### 3.1 Mécanisme en place

| Élément | État |
|---------|------|
| Interface stable | `apps.core.horodatage.maintenant_opposable()` |
| Mode actif | `RSM_TIMESOURCE_MODE=local_stub` |
| Comportement STUB | Appelle `timezone.now()` + `warnings.warn()` + renvoie `ResultatHorodatage(..., opposable=False)` |
| Format du n° d'ordre | `NNNNNN-AAAAMMJJHHMMSS` (art. 78 al. 4) — **format stable** ; seule la source de l'instant varie selon le mode |
| Synchronisation NTP serveur | Dépend de la configuration système (souvent `systemd-timesyncd` ou `chrony`) — **non contrôlée** par le RSM |
| Supervision | Aucune alerte de dérive configurée |
| Tests désactivés | `test_api_zones_gelees.py::test_horodatage_opposable_source_officielle` |

### 3.2 Garanties techniques déjà en place

- Verrou pessimiste sur `SequenceNumeroOrdre` (L3.5 § 2.4) : l'ordre
  d'attribution est sérialisé sous concurrence (20 threads parallèles
  → 20 numéros contigus, testé).
- Monotonie du numéro séquentiel garantie indépendamment de l'horloge.
- Chaînage d'empreintes du journal d'audit (L3.5 § 2.1) : indépendant
  de la fiabilité horaire.

### 3.3 Périmètre impacté

- **Tout instant juridiquement opposable** : `instant_arrivee`,
  `instant_saisie_opposable`, `date_expiration` (dérivée), `applique_le`,
  `instant_rejet`, `ancienne_date_expiration`, `nouvelle_date_expiration`.
- Les horodatages purement techniques (`cree_le`, `modifie_le`) ne sont
  pas concernés par l'opposabilité.

### 3.4 Distinction avec F7

F5 traite la **source de temps** (d'où vient la valeur horaire ?) ;
F7 traite la **sémantique** des horodatages (quelle différence entre
horodatage d'arrivée et horodatage de saisie opposable ?). Les deux
fiches sont complémentaires mais indépendantes.

---

## 4. Options d'arbitrage

### 4.1 Option a — NTP de confiance (stratum 1 ou 2)

**Description** : synchronisation du serveur RSM sur un ou plusieurs
serveurs NTP de confiance, idéalement stratum 1 (source atomique
directe) ou stratum 2 (synchronisé sur stratum 1). Sources
envisageables : serveur NTP désigné par l'État mauritanien, serveurs
internationaux de confiance (`pool.ntp.org`, `time.nist.gov`,
`time.google.com`), éventuellement redondance sur plusieurs
serveurs.

Le mode `RSM_TIMESOURCE_MODE=ntp_stratum_X` implémente un adaptateur
qui :
- vérifie périodiquement la synchronisation (chrony / ntpd + query API) ;
- détecte la dérive (seuil configurable, ex. 100 ms) ;
- refuse de délivrer un horodatage opposable si la dérive dépasse le seuil.

| Dimension | Évaluation |
|-----------|------------|
| Précision | 🟢 Millisecondes à quelques dizaines de millisecondes |
| Conformité art. 78 al. 4 (seconde) | 🟢 Largement suffisante |
| Coût de déploiement | 🟢 **Faible** — configuration système + adaptateur Python |
| Dépendance externe | 🟠 Serveurs NTP (redondance indispensable) |
| Protection contre manipulation interne | 🟠 Un administrateur système peut modifier la configuration NTP |
| Conformité TDR § 5.1 (« protégée… y compris par administrateur technique ») | 🟠 **Partielle** — protection additionnelle requise (cf. option d) |
| Vérifiabilité post-transfert (art. 83) | 🟢 Les serveurs NTP restent accessibles après transfert |
| Délai de mise en œuvre | 🟢 Très court (quelques semaines) |

**Avantages** : standard universel, peu coûteux, bien documenté.
**Inconvénients** : vulnérabilité à une manipulation par
l'administrateur technique (désynchronisation volontaire) ; le TDR § 5.1
exige une protection contre cette manipulation.

### 4.2 Option b — PTP (Precision Time Protocol, IEEE 1588)

**Description** : PTP offre une précision sub-microseconde, conçue
pour les environnements où la granularité NTP est insuffisante (ex.
finance, télécoms). Nécessite une infrastructure dédiée : serveur
grandmaster, switches PTP-aware, configuration sur les hôtes.

| Dimension | Évaluation |
|-----------|------------|
| Précision | 🟢 Sub-microseconde |
| Conformité art. 78 al. 4 | 🟢 Excessive (art. 78 demande la seconde) |
| Coût de déploiement | 🔴 **Élevé** — infrastructure réseau PTP (switches, serveur dédié) |
| Dépendance externe | 🟢 Infrastructure interne (maîtrisable) |
| Protection contre manipulation | 🟠 Identique à NTP tant qu'on ne couple pas à un HSM |
| Conformité TDR § 5.1 | 🟠 Partielle pour les mêmes raisons que NTP |
| Vérifiabilité post-transfert | 🟢 Standard IEEE |
| Cas d'usage pertinent | 🟠 PTP n'est pas dimensionné pour les besoins du RSM (seconde) |

**Avantages** : précision maximale, résilience aux perturbations
réseau.
**Inconvénients** : **surdimensionné** pour le besoin art. 78 ;
coût et complexité injustifiés pour une granularité à la seconde.

### 4.3 Option c — Horloge interne HSM de confiance

**Description** : le système délègue la production d'horodatages à un
**Hardware Security Module** (HSM) certifié (Common Criteria EAL4+
ou FIPS 140-2 niveau 3). Le HSM maintient sa propre horloge interne,
protégée matériellement contre toute manipulation logicielle, y
compris par un administrateur. Le HSM est appelé à chaque opération
nécessitant un horodatage opposable.

| Dimension | Évaluation |
|-----------|------------|
| Précision | 🟢 Microseconde à seconde selon modèle |
| Conformité art. 78 al. 4 | 🟢 Suffisante |
| Coût de déploiement | 🔴 **Élevé** — acquisition d'un HSM + licences + intégration |
| Dépendance externe | 🟠 Fabricant du HSM (Thales, Utimaco, AWS CloudHSM, etc.) |
| Protection contre manipulation interne | 🟢 **Maximale** — l'horloge HSM n'est pas modifiable par l'administrateur système |
| Conformité TDR § 5.1 (« protégée… y compris par administrateur technique ») | 🟢 **Stricte** |
| Vérifiabilité post-transfert | 🟠 Nécessite le transfert du HSM ou la conservation des horodatages signés par l'ancien HSM |
| Mutualisation possible avec F6 (scellement) et F3/F4 (signature) | 🟢 Le même HSM peut porter l'horloge, la clé de scellement, et les clés de signature — mutualisation attractive |
| Délai de mise en œuvre | 🔴 Long (plusieurs mois) — commande HSM, certification, intégration |

**Avantages** : conformité TDR § 5.1 **maximale** ; résistance à la
compromission administrative ; mutualisation avec autres services
cryptographiques.
**Inconvénients** : coût élevé, dépendance fournisseur, délai de
déploiement important.

### 4.4 Option d — NTP + autorité d'horodatage externe (RFC 3161)

**Description** : combine NTP pour la synchronisation courante (option a)
**et** une **Time Stamping Authority** (TSA) externe pour les actes
juridiques critiques. Chaque horodatage opposable (inscription
validée, modification appliquée, radiation, expiration) fait l'objet
d'une requête à une TSA reconnue qui délivre un token d'horodatage
signé (RFC 3161). Ce token est conservé dans le journal d'audit et
reproduit dans le certificat.

| Dimension | Évaluation |
|-----------|------------|
| Précision | 🟢 Seconde |
| Conformité art. 78 al. 4 | 🟢 Stricte |
| Coût de déploiement | 🟠 Modéré — licence TSA + intégration (bibliothèques disponibles) |
| Dépendance externe | 🔴 Fournisseur TSA |
| Protection contre manipulation interne | 🟢 **Élevée** — la TSA externe signe l'horodatage avec sa propre clé |
| Conformité TDR § 5.1 | 🟢 Élevée (le MO peut choisir une TSA indépendante) |
| Vérifiabilité post-transfert (art. 83) | 🟢 Les tokens TSA sont vérifiables hors ligne avec la clé publique de la TSA |
| Volumétrie | 🟠 Requête TSA à chaque acte critique — latence et coût unitaire |
| Performance | 🟠 Dépendance au temps de réponse de la TSA |

**Avantages** : conformité forte, indépendance de l'administrateur
technique, standard international.
**Inconvénients** : dépendance à un service externe ; latence et
coût unitaire à chaque horodatage critique ; volumétrie à
dimensionner.

### 4.5 Option e — Approche hybride à paliers

**Description** : démarrage en option a (NTP stratum 2 avec
redondance) pour une mise en service rapide, avec adaptateur logiciel
détectant la dérive (seuil 100 ms) et refusant de délivrer un
horodatage opposable hors plage. Bascule ultérieure vers option c
(HSM) ou d (TSA externe) une fois l'infrastructure disponible,
**sans interruption de service**. Pendant la phase initiale, chaque
horodatage embarque la mention de son mode pour traçabilité.

| Dimension | Évaluation |
|-----------|------------|
| Coût initial | 🟢 Faible |
| Coût total | 🟠 Croissant avec les paliers |
| Robustesse | 🟠 Modérée initialement, maximale ensuite |
| Ouverture rapide | 🟢 **Très rapide** |
| Conformité TDR § 5.1 | 🟠 Acceptable dans la phase initiale ; stricte ensuite |
| Complexité d'exploitation | 🟠 Gestion des migrations inter-paliers |

**Avantages** : permet une mise en service rapide du RSM sans attendre
les infrastructures lourdes.
**Inconvénients** : période initiale avec conformité § 5.1 partielle ;
exige un engagement MO formel sur le calendrier de bascule.

### 4.6 Option f — Double source avec contrôle croisé

**Description** : le système s'appuie simultanément sur **deux
sources de temps indépendantes** (par exemple NTP stratum 1 + TSA
externe, ou NTP + HSM). À chaque horodatage opposable, les deux
sources sont consultées ; si elles divergent de plus d'un seuil
arbitré (ex. 500 ms), le système refuse de délivrer l'horodatage et
émet une alerte. Le journal d'audit trace les deux valeurs.

| Dimension | Évaluation |
|-----------|------------|
| Précision | 🟢 Seconde |
| Détection de dérive | 🟢 **Maximale** — divergence détectable automatiquement |
| Coût de déploiement | 🔴 Double infrastructure |
| Performance | 🟠 Deux requêtes par horodatage |
| Conformité TDR § 5.1 | 🟢 Stricte |
| Vérifiabilité | 🟢 Double trace |
| Complexité | 🔴 Très élevée |

**Avantages** : détection infaillible d'une manipulation
unilatérale ; traçabilité maximale.
**Inconvénients** : infrastructure double ; cas de divergence
à gérer opérationnellement (qui tranche ?).

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Adaptateur à câbler |
|--------|---------------------|
| a | Vérificateur de synchronisation NTP (chrony, ntpd) + contrôle de dérive |
| b | Intégration PTP + câblage réseau dédié |
| c | SDK du HSM choisi (PKCS#11 ou propriétaire) |
| d | Bibliothèque RFC 3161 + client TSA |
| e | Adaptateur a + plan de bascule vers c ou d |
| f | Deux adaptateurs en parallèle + logique de comparaison |

L'interface `maintenant_opposable() → ResultatHorodatage` reste
inchangée. L'activation passe par `RSM_TIMESOURCE_MODE` et le
code métier n'est pas impacté.

### 5.2 Impacts sur les tests

- Activation de `test_api_zones_gelees.py::test_horodatage_opposable_source_officielle`.
- Nouveau test : détection de dérive — simulation d'une horloge
  décalée → refus de l'horodatage avec clé `autorisation.refus.derive_horloge`
  (à ajouter à L2.5 si arbitrage requiert cette clé).
- Nouveau test : post-transfert — un numéro d'ordre produit en
  période A est vérifiable sur un système B (lecture seule du journal).
- Compatibilité des tests de concurrence (`test_concurrence_art78.py`) :
  indépendants de la source de temps au niveau unité.

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 § 2.2 (inscription) | Mention de la source de temps retenue + implications pour l'opposabilité |
| L2.2 Règle G-78.3 | Passage de STUB à IMPLÉMENTÉ |
| L2.2 Règle C-78.2 (format n° d'ordre) | Inchangé (format stable) |
| L3.3 § 3 | Section « modes cibles » renseignée avec l'option retenue |
| L3.5 § 10 | Mise à jour des tests de sécurité |
| L11 | Passage de `L11/horodatage` à IMPLÉMENTÉ ; mise à jour du risque R1 |

### 5.4 Dépendances transversales avec d'autres fiches

- **F6 (scellement)** : si option c (HSM) retenue pour F5, l'horloge
  HSM peut être utilisée simultanément pour le scellement → forte
  mutualisation ; le MO peut arbitrer F5 et F6 conjointement.
- **F7 (distinction horodatages)** : la distinction entre
  `instant_arrivee` et `instant_saisie_opposable` dépend de la source
  — F5 fixe le référentiel temporel commun.
- **F8 (indisponibilité)** : la politique d'indisponibilité fixe ce
  qu'il advient des demandes reçues lorsque la source de temps est
  momentanément indisponible.
- **F4 (certificats)** : certaines options F4 (notamment d — timestamp
  RFC 3161) peuvent être mutualisées avec F5 option d (TSA commune).

### 5.5 Impacts sur l'exploitation

- **Supervision continue** : seuils d'alerte de dérive à surveiller
  en permanence.
- **Procédure de bascule** : en cas de perte de la source primaire,
  procédure documentée de passage à la source de secours
  (option e, f).
- **Journal des événements d'horloge** : catégorie d'audit
  `systeme` + actions `systeme.bascule_horodatage`, `systeme.derive_horloge`
  (L3.3 § 7 — déjà structurellement prévues, à activer).
- **Calibration périodique** : vérification régulière de la dérive,
  documentée et tracée.

---

## 6. Tradeoffs synthétiques

| Critère | a (NTP) | b (PTP) | c (HSM) | d (NTP + TSA) | e (Paliers) | f (Double source) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| Précision | Millisecondes | Sub-µs | Microsecondes | Seconde | Évolutive | Seconde |
| Conformité art. 78 al. 4 (seconde) | Satisfaisante | Excessive | Satisfaisante | Stricte | Progressive | Stricte |
| Conformité TDR § 5.1 (protégée contre admin tech.) | Partielle | Partielle | **Maximale** | Élevée | Progressive | Stricte |
| Coût de déploiement | Faible | Élevé | Élevé | Modéré | Faible → progressif | Très élevé |
| Coût récurrent | Nul | Faible | Licences HSM | Par horodatage | Évolutif | Cumul |
| Délai de mise en service | Très court | Long | Long | Moyen | Très court | Long |
| Mutualisation F3 / F4 / F6 | Non | Non | Oui (HSM commun) | Partielle | Possible ensuite | Possible |
| Dépendance externe | NTP publics | Infrastructure interne | Fournisseur HSM | TSA externe | Variable | Double |
| Résistance à la compromission admin technique | Faible | Faible | **Maximale** | Élevée | Évolutive | Très élevée |
| Vérifiabilité post-transfert (art. 83) | Élevée | Élevée | Modérée (HSM à migrer) | Élevée | Évolutive | Élevée |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Existence d'un serveur NTP national** (option a, d, e) : source
   officielle mauritanienne, disponibilité, redondance.
2. **Disponibilité d'une TSA reconnue** (option d, e, f) : prestataire
   national ou international, conformité eIDAS ou équivalent.
3. **Budget infrastructure** : capacité d'acquisition d'un HSM
   (option c) ou de licences TSA (option d).
4. **Seuil de dérive toléré** : en millisecondes, au-delà duquel
   l'horodatage n'est plus délivré. Proposition indicative : 100 ms.
5. **Politique en cas de dérive détectée** : arrêt du service
   (sécurité) ou dégradation (continuité) ?
6. **Politique de rotation** : la source primaire est-elle fixe ou
   peut-elle être changée en cours d'exploitation ? Procédure ?
7. **Opposabilité rétroactive** : si une bascule vers une source plus
   sûre intervient, les horodatages antérieurs restent-ils valables
   dans leur forme initiale, ou sont-ils ré-horodatés ?
8. **Intégration avec F6** : le MO arbitre-t-il conjointement F5 et
   F6 (HSM commun) ou séparément ?
9. **Calendrier de bascule** (option e) : engagement MO sur les
   paliers et leur durée.
10. **Procédure de vérification** par un tiers (auditeur, juge) : comment
    un tiers vérifie-t-il qu'un horodatage du RSM est bien issu de
    la source officielle ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ autre : ______ |
| Source précise | _(à renseigner — ex. NTP stratum 2 du MNT + redondance time.nist.gov)_ |
| Valeur arbitrée de `RSM_TIMESOURCE_MODE` | _(à renseigner — `ntp_stratum_1`, `ntp_stratum_2`, `ptp`, `hsm_trusted_clock`, `ntp_tsa_combine`, …)_ |
| Seuil de dérive | _(à renseigner — en millisecondes)_ |
| Politique en cas de dérive | _(à renseigner — arrêt / dégradation)_ |
| Calendrier (si option e) | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Politique d'horodatage et de scellement : [L3.3 § 2 et § 3](../L3_3_horodatage_scellement.md).
- Service stable `maintenant_opposable()` : [apps/core/horodatage.py](../../backend/apps/core/horodatage.py).
- Format du numéro d'ordre : [L2.2 § 2.2](../L2_2_regles_validation.md).
- Test de concurrence sur le numéro d'ordre : [tests/test_concurrence_art78.py](../../backend/tests/test_concurrence_art78.py).
- Fiche F6 (scellement) : [F6_scellement_cryptographique.md](F6_scellement_cryptographique.md) — mutualisation éventuelle.
- Fiche F7 (distinction horodatages) : [F7_distinction_horodatages.md](F7_distinction_horodatages.md) — complémentaire.
- Fiche F8 (indisponibilité) : [F8_politique_indisponibilite.md](F8_politique_indisponibilite.md) — politique si source momentanément indisponible.
- Registre des arbitrages : [L11](../L11_tracabilite_articles_76_97.md) ; risque R1 (dérive d'horloge).
