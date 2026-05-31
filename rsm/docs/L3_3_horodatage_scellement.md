# L3.3 — Politique d'horodatage et de scellement

**Livrable** : L3.3 — partie du livrable L3 (§ 8 du TDR).
**Objet** : formalisation des mécanismes d'horodatage et de scellement, en cohérence stricte avec l'existant, y compris la documentation explicite des zones gelées.
**Fondement** : articles 78, 87, 90, 97 du décret 2021-033 ; TDR § 5.1, § 6.3.
**État** : spécifications techniques consolidant l'existant. **Aucune zone gelée n'est levée par ce livrable.**

---

## 1. Rôle juridique de l'horodatage et du scellement

### 1.1 Horodatage (art. 78, 87, 90)

L'horodatage du RSM fonde :

- la **chronologie d'arrivée** des demandes (art. 78 al. 2) ;
- la **prise d'effet juridique** des inscriptions et modifications (art. 78 al. 3, art. 87, art. 90 al. 1) ;
- le **numéro d'ordre** (art. 78 al. 4) dont la composante temporelle est portée à la seconde.

**Toute dérive non détectée porte atteinte à l'opposabilité des inscriptions** (§ 5.1 TDR, point critique).

### 1.2 Scellement (art. 97, § 6.3)

Le scellement fonde :

- la **force probante** des certificats de recherche (art. 97 dernier al.) ;
- la **vérifiabilité a posteriori** du contenu des inscriptions (§ 6.3) ;
- la **cohérence fichier public ↔ certificat** à l'instant T (§ 4.2.5, point critique).

---

## 2. Distinction de deux horodatages

Le système distingue deux horodatages — le TDR (§ 9.3) identifie
l'ambiguïté potentielle. La politique retenue est la suivante :

| Horodatage | Champ ORM | Rôle juridique | Quand posé |
|------------|-----------|----------------|------------|
| **Arrivée** (`instant_arrivee`) | `Inscription.instant_arrivee` | Ordre chronologique art. 78 al. 2 | À la réception de la demande (POST `/api/v1/inscriptions/`). |
| **Saisie opposable** (`instant_saisie_opposable`) | `Inscription.instant_saisie_opposable` | Prise d'effet art. 78 al. 3, art. 87, art. 90 al. 1 | À la validation par le greffier. |

**Politique actuelle** : l'horodatage d'arrivée est produit par
`django.utils.timezone.now()` (horloge serveur), tandis que
l'horodatage de saisie opposable passe par `apps.core.horodatage.maintenant_opposable()`
dont le mode STUB renvoie également l'horloge serveur avec un
avertissement explicite.

**Zone d'arbitrage MO (A9)** : la distinction précise entre les deux et
la politique applicable en cas d'indisponibilité du service (§ 5.3 TDR,
R4) doivent être formellement arrêtées par le MO. En l'état, les deux
champs utilisent l'horloge serveur, clairement signalée comme non
opposable (cf. § 3 ci-dessous).

---

## 3. Interface stable du service d'horodatage

### 3.1 Signature publique

Module : `apps.core.horodatage`.

```python
@dataclass(frozen=True)
class ResultatHorodatage:
    instant: datetime   # à la seconde (art. 78 al. 4)
    source: str         # identifiant du mode (ex. "local_stub", "ntp_stratum_1")
    opposable: bool     # True uniquement si la source est arbitrée et active


def maintenant_opposable() -> ResultatHorodatage: ...
def format_numero_ordre(instant: datetime, numero_sequence: int) -> str: ...
```

**Stabilité garantie** : la signature ci-dessus est **contractuelle**. Les services métier (`valider_inscription`, `appliquer_modification`, etc.) n'appellent JAMAIS `timezone.now()` directement pour fonder une prise d'effet — ils passent tous par `maintenant_opposable()`. Cette centralisation permet la bascule sans réécriture.

### 3.2 Mode STUB actuel (`local_stub`)

Comportement lorsque `RSM_TIMESOURCE_MODE=local_stub` :

1. Appelle `timezone.now()` (horloge serveur).
2. Émet un `warnings.warn` Python rappelant que l'inscription n'est PAS opposable.
3. Retourne `ResultatHorodatage(..., source="local_stub", opposable=False)`.

**Conséquence opérationnelle** : tant que le mode STUB est actif,
`Inscription.instant_saisie_opposable` est positionné mais les
inscriptions **n'ont pas de valeur juridique au sens de l'article 87**.
Les tests d'intégration S1–S6 produisent des inscriptions de test, non
opposables.

### 3.3 Modes cibles — à arbitrage MO

Les quatre modes cibles suivants sont prévus par la configuration mais
**non implémentés** (les adaptateurs levent `NotImplementedError` avec
un message explicite) :

| Mode | Description | Décision MO attendue |
|------|-------------|----------------------|
| `ntp_stratum_1` | Horloge NTP de confiance, stratum 1 (source atomique). | Choix du ou des serveurs NTP désignés par l'État ou par un tiers de confiance. |
| `ntp_stratum_2` | Horloge NTP stratum 2, synchronisée sur stratum 1 officiel. | Choix du serveur intermédiaire ; fréquence de synchronisation. |
| `ptp` | Precision Time Protocol (IEEE 1588), infrastructure dédiée. | Choix d'un déploiement PTP au sein du datacenter. |
| `hsm_trusted_clock` | Horloge interne d'un HSM certifié, non manipulable par l'exploitant. | Choix du HSM, politique d'accès, cycle de révision. |

### 3.4 Contrat d'implémentation d'un adaptateur

Tout adaptateur écrit pour lever la zone gelée **doit** :

1. Retourner un `datetime` à la seconde (tronqué ou arrondi selon la règle MO, à définir).
2. Positionner `source` à l'identifiant du mode.
3. Positionner `opposable=True` UNIQUEMENT si la source est réputée de confiance par le MO.
4. En cas d'indisponibilité ou de dérive détectée, soit retourner `opposable=False`, soit lever une exception métier empêchant la validation.
5. Écrire une entrée d'audit `systeme.horodatage_X` à chaque bascule ou dérive.

### 3.5 Format du numéro d'ordre (art. 78 al. 4)

Spécification **immuable** (arrêtée par le décret) :

```
NNNNNN-AAAAMMJJHHMMSS
│      │
│      └─ composante temporelle à la seconde
└──────── numéro séquentiel, au moins 6 chiffres, strictement positif, jamais réutilisé
```

Implémentation : `apps.core.horodatage.format_numero_ordre`.

**Invariants** :
- `numero_sequence` > 0 (rejet sinon).
- `instant.strftime("%Y%m%d%H%M%S")` — la composante temporelle s'incrit SANS fuseau : on stocke toujours en `Africa/Nouakchott` (cf. `settings.TIME_ZONE`).
- Sérialisation déterministe : deux appels avec le même `(instant, ordre)` produisent la même chaîne au bit près.

---

## 4. Interface stable du service de scellement

### 4.1 Signature publique

Module : `apps.core.scellement`.

```python
@dataclass(frozen=True)
class Sceau:
    empreinte_hex: str    # hex-encoded digest
    algorithme: str       # identifiant de l'algorithme ou mode actif
    opposable: bool       # True uniquement après arbitrage MO


def sceller(contenu: bytes) -> Sceau: ...
def verifier(contenu: bytes, sceau: Sceau) -> bool: ...
```

**Stabilité garantie** : identique au service d'horodatage — tous les
usages métier (`SnapshotInscription.empreinte`,
`PieceJointe.sceau_empreinte`, `Certificat.empreinte`) passent par
`sceller()` sans jamais calculer de hash directement.

### 4.2 Canonicalisation préalable

Avant scellement, le contenu est canonicalisé pour garantir la
reproductibilité au bit près :

- Module : `apps.modifications.serialisation.encoder_canonique`.
- Algorithme : `json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))` puis UTF-8.
- Champs bilingues : sérialisés en paires `{"fr": "...", "ar": "...", "langue_faisant_foi": "..."}`.
- Champs temporels : ISO-8601 à la seconde.

Cette canonicalisation est **irrévocable** : toute évolution doit passer par un versionnement explicite (`apps.modifications.serialisation.VERSION` à introduire le moment venu).

### 4.3 Mode STUB actuel (`disabled`)

Comportement lorsque `RSM_SEAL_MODE=disabled` :

1. Calcul SHA-256 du contenu canonicalisé.
2. Émet un `warnings.warn`.
3. Retourne `Sceau(empreinte_hex=..., algorithme="sha256-stub", opposable=False)`.

**Conséquence** : toutes les empreintes produites (snapshots, journal d'audit, certificats) permettent de détecter une altération, mais NE sont PAS juridiquement opposables tant que l'arbitrage MO n'a pas été rendu.

### 4.4 Modes cibles — à arbitrage MO

| Mode | Description | Décision MO attendue |
|------|-------------|----------------------|
| `hmac` | HMAC-SHA-256 avec clé conservée dans un HSM. Sceau vérifiable par toute partie disposant de la clé. | Infrastructure HSM ; politique de rotation ; accessibilité post-transfert art. 83. |
| `asymmetric_signature` | Signature RSA ou ECDSA ; clé privée dans HSM, clé publique distribuée. Sceau vérifiable par tout auditeur sans accès à la clé privée. | Choix de l'algorithme et de la taille ; politique de publication de la clé publique ; traitement de la révocation. |
| `chained_log` | Journal append-only chaîné (déjà en place pour l'audit) étendu aux snapshots et aux certificats ; preuve de non-altération par inclusion dans la chaîne. | À combiner avec l'un des deux modes ci-dessus pour la preuve d'identité de l'émetteur. |

### 4.5 Contrat d'implémentation

Tout adaptateur futur **doit** :

1. Produire un `Sceau` dont l'`empreinte_hex` est stable et reproductible pour un même contenu (déterminisme).
2. Positionner `opposable=True` UNIQUEMENT si la chaîne de confiance est active (clé disponible, certificat non révoqué, horloge de référence disponible).
3. Implémenter `verifier()` de sorte qu'il reste fonctionnel après transfert du Registre (art. 83) — c'est-à-dire sans dépendance captive à l'infrastructure d'origine.

---

## 5. Paramétrage du système (`.env`)

```ini
# apps.core.horodatage
RSM_TIMESOURCE_MODE=local_stub            # | ntp_stratum_1 | ntp_stratum_2 | ptp | hsm_trusted_clock

# apps.core.scellement
RSM_SEAL_MODE=disabled                    # | hmac | asymmetric_signature | chained_log

# Signature électronique (apps.modifications)
RSM_ESIGN_MODE=disabled                   # | PKI_nationale | certificat_qualifie | autre (MO)

# Authentification forte (§ 5.1)
RSM_MFA_MODE=disabled                     # | totp | x509_card | id_numerique_nationale
```

**Règle** : aucune valeur par défaut ne bascule automatiquement en
mode opposable. Toute activation d'un mode non-STUB :

- requiert une **décision MO écrite et référencée** (cf. rappel impératif du MO) ;
- doit être accompagnée de la levée des tests `@arbitrage_mo` correspondants ;
- doit tracer une entrée d'audit système `systeme.bascule_mode`.

---

## 6. Interactions entre horodatage et scellement

### 6.1 Snapshot d'inscription

```
À chaque modification / renouvellement / radiation / validation :

1. serialiser_inscription(inscription) → dict canonique
2. encoder_canonique(dict) → bytes UTF-8 déterministes
3. sceller(bytes) → Sceau
4. SnapshotInscription.objects.create(
       contenu=dict, empreinte=sceau.empreinte_hex,
       instant=timezone.now(),   # horodatage TECHNIQUE d'archivage
       evenement=..., inscription=..., demande_modification=...,
   )
```

**Note** : l'horodatage du snapshot est TECHNIQUE (simple date de
capture, utilisée pour le tri et l'auditeur). Il ne se confond pas avec
les horodatages juridiques portés par `Inscription` (`instant_arrivee`
et `instant_saisie_opposable`).

### 6.2 Certificat de recherche (art. 97)

```
Après une recherche retournant R inscriptions à l'instant T :

1. Photographier l'état du fichier public à T (requête
   STATUTS_FICHIER_PUBLIC avec les filtres art. 96).
2. Sérialiser canoniquement {instant: T, criteres, resultats, homonymes}.
3. sceller(bytes) → empreinte.
4. Certificat.objects.create(
       type_certificat="recherche",
       requete_recherche=..., langue_generation=...,
       probant=sceau.opposable,
       empreinte=sceau.empreinte_hex,
       contenu_json=payload,
   )
5. ZONE GELÉE : la génération PDF/A bilingue et la signature qualifiée
   ne sont pas câblées. `probant` reste False tant que l'arbitrage n'est
   pas rendu.
```

### 6.3 Journal d'audit

Le journal d'audit utilise sa propre logique de chaînage (distincte du
scellement général) :

```
empreinte(n) = SHA-256( canonicalise({
    "precedente": empreinte(n-1),
    "entree":     {instant, catégorie, action_cle, résultat, acteur_id,
                   acteur_role, objet_type, objet_reference, details},
}) )
```

Le chaînage est testé sous concurrence (cf. `tests/test_audit_concurrence.py`
— 8 threads × 25 écritures). Après l'arbitrage MO sur le scellement, la
chaîne d'empreintes pourra être **additionnellement** signée à
intervalles réguliers par le mode `asymmetric_signature`, sans
modification de la logique de chaînage.

---

## 7. Journal des tentatives et alertes

Toute bascule sur un mode autre que STUB doit s'accompagner d'une
écriture d'audit :

| Événement | Catégorie | Action | Détails |
|-----------|-----------|--------|---------|
| Bascule de mode d'horodatage | `systeme` | `systeme.bascule_horodatage` | ancien_mode, nouveau_mode, acteur, motif |
| Bascule de mode de scellement | `systeme` | `systeme.bascule_scellement` | idem |
| Dérive détectée (horloge) | `systeme` | `systeme.derive_horloge` | écart_secondes, source, seuil |
| Vérification de chaîne | `systeme` | `systeme.verifier_chaine` | résultat (intègre / premier id altéré) |
| Certificat émis non opposable | `certificat` | `certificat.preparer` | type, probant=False (audit existant) |

Ces événements sont à produire par les futurs adaptateurs (modes cibles) et **ne sont pas câblés à ce jour** (zone gelée).

---

## 8. Cohérence avec les obligations juridiques

| Exigence | Mécanisme | État |
|----------|-----------|------|
| Unicité du numéro d'ordre (art. 78 + § 10.1) | `SequenceNumeroOrdre` avec `SELECT … FOR UPDATE` + test de concurrence 20 threads | IMPLÉMENTÉ |
| Numéro d'ordre jamais réutilisé (§ 10.1) | Séquence monotone, pas de décrément | IMPLÉMENTÉ |
| Horodatage à la seconde (art. 78 al. 4) | Format strict `NNNNNN-AAAAMMJJHHMMSS` | IMPLÉMENTÉ |
| Ordre d'arrivée respecté (art. 78 al. 2) | `instant_arrivee` indexé ; verrou pessimiste sur la séquence | IMPLÉMENTÉ |
| Prise d'effet à la saisie (art. 87, 90) | `instant_saisie_opposable` posé à la validation | STRUCTUREL (opposable=False en STUB) |
| Source de temps fiable, supervisée (§ 5.1) | Interface `maintenant_opposable()` + modes cibles configurables | **GELÉ** (arbitrage MO) |
| Scellement vérifiable indéfiniment (§ 6.3) | Interface `sceller()` / `verifier()` + canonicalisation déterministe | **GELÉ** (arbitrage MO) |
| Cohérence fichier public ↔ certificat (§ 4.2.5) | Lecture transactionnelle + snapshot canonique | STRUCTUREL (non opposable) |
| Force probante du certificat de recherche (art. 97) | `Certificat.probant` | **GELÉ** |

---

## 9. Récapitulatif des zones gelées — L3.3

| Zone | Référence L11 | Interface posée | Paramétrage | Activation attendue |
|------|---------------|-----------------|-------------|---------------------|
| Horodatage opposable | L11/horodatage | `apps.core.horodatage.maintenant_opposable()` | `RSM_TIMESOURCE_MODE` | Source de temps MO + adaptateur dédié |
| Scellement cryptographique | L11/A5 (partiel) | `apps.core.scellement.sceller()` / `verifier()` | `RSM_SEAL_MODE` | HSM / PKI MO + adaptateur |
| Signature électronique des parties | L11/A2 | Flags `accord_*_confirme` | `RSM_ESIGN_MODE` | Régime PKI retenu par le MO |
| Certificats probants art. 97 | L11/A5 | `Certificat.probant` + `preparer_certificat()` | (dépend des 2 précédents) | Bascule cumulative |
| Paiement électronique | L11/A7 | Non implémenté | — | Politique tarifaire MO |
| Interconnexions externes (RCCM, identité) | L11/interconnexions | Non implémentées | — | Décision MO |
| Authentification forte | L11/MFA | Auth Django session | `RSM_MFA_MODE` | Choix second facteur MO |
| Réutilisation Partie existante | L11/parties_reutilisation | Schéma de diff figé | — | Décision MO |

**Rappel impératif** : aucune de ces zones ne peut être levée sans
décision MO écrite et référencée. Toute levée déclenchera une révision
de L11 (registre des hypothèses) et du présent document.

---

## 10. Renvois croisés

- Modèle de données : [L3.1](L3_1_modele_donnees.md).
- Architecture modulaire : [L3.2](L3_2_architecture_modulaire.md).
- Traçabilité article par article : [L11](L11_tracabilite_articles_76_97.md).
- Code :
  - Service d'horodatage : [apps/core/horodatage.py](../backend/apps/core/horodatage.py).
  - Service de scellement : [apps/core/scellement.py](../backend/apps/core/scellement.py).
  - Sérialisation canonique : [apps/modifications/serialisation.py](../backend/apps/modifications/serialisation.py).
  - Journal d'audit chaîné : [apps/audit/services.py](../backend/apps/audit/services.py).
