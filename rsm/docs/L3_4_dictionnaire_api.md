# L3.4 — Dictionnaire API

**Livrable** : L3.4 — partie du livrable L3 (§ 8 du TDR).
**Objet** : table consolidée et opposable des endpoints REST du système RSM.
**Fondement** : chapitre IV du décret 2021-033 ; TDR § 4.2, § 6.2.
**État** : consolidation de l'existant. **Aucun nouvel endpoint.**

---

## 1. Principes généraux

### 1.1 Préfixe et versionnement

Toutes les routes d'API sont préfixées par `/api/v1/`. Le numéro de
version est figé : toute évolution non rétrocompatible imposera un
préfixe `/api/v2/` et la conservation de la v1 durant une période
documentée. Aucune rupture silencieuse.

### 1.2 Authentification

Mécanisme d'authentification actif : **`SessionAuthentication`** (Django
standard).

⚠️ **ZONE GELÉE — L11/MFA** : l'authentification forte (TOTP, certificat
X.509, identité numérique nationale) reste à arbitrage MO. La
configuration `RSM_MFA_MODE=disabled` bloque formellement toute
bascule silencieuse. Les endpoints d'écriture restent accessibles
uniquement aux comptes authentifiés via session Django.

### 1.3 Permissions par défaut

`DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` — toute vue non
autrement déclarée exige un utilisateur authentifié. Exception
documentée : la recherche publique (art. 94) et la consultation des
référentiels — explicitement `AllowAny`.

### 1.4 Codes HTTP normalisés (via `rsm_exception_handler`)

| Classe d'exception levée | HTTP | Corps |
|--------------------------|:----:|-------|
| `ErreurMetierRSM` et filles (`RejetForme`, `ModificationSansEffet`, `RenouvellementHorsDelai`, `TransitionInterdite`, `RechercheCriteresInsuffisants`, `RegimeDeclaratifViole`) | 400 | `{detail, article, classe}` |
| `AutorisationRefusee` (habilitations § 4.1) | 403 | `{detail, article, classe}` |
| `PermissionError` (append-only, art. 79) | 403 | `{detail, article="79", classe="PermissionError"}` |
| `ValidationError` DRF (serializer) | 400 | Structure DRF + champ `non_autorises` si clé inconnue |
| Exception non typée | 500 | Géré par Django (DEBUG contrôle la verbosité) |

### 1.5 Sérialisation stricte (cohérence globale)

Tous les serializers d'entrée dérivent de `StrictInputMixin` via
`StrictInputSerializer` ou `StrictModelSerializer` (cf.
[apps/core/serializers.py](../backend/apps/core/serializers.py)). Toute
clé inconnue est refusée — la règle s'applique **uniformément** à tous
les endpoints d'écriture.

### 1.6 Pagination

`PageNumberPagination`, `PAGE_SIZE = 25`. Requêtes GET paginées
renvoient `{count, next, previous, results}`.

### 1.7 Format et encodage

- Content-Type : `application/json` (UTF-8 strict, `ensure_ascii=False` possible).
- Dates : ISO-8601 à la seconde (`YYYY-MM-DDTHH:MM:SS+TZ`).
- Décimaux : chaîne décimale (ex. `"1000000.00"`).
- Énumérations : **clés neutres** (ex. `"nant_outillage"`). Les
  libellés FR/AR sont résolus par `*_libelle` côté sortie selon
  `Accept-Language`.

---

## 2. Endpoints racine

| Route | Méthode | Permissions | Rôle / observations |
|-------|:-------:|-------------|---------------------|
| `/i18n/setlang/` | POST | `AllowAny` | Bascule de langue (Django natif). |
| `/fr/` ou `/ar/` | GET | `AllowAny` | Pages traduites (accueil, santé). |
| `/fr/administration/` ou `/ar/administration/` | GET | `IsAdminUser` (+ restrictions L3.2 § 6) | Admin Django verrouillée. |
| `/api/v1/` | — | — | Racine des endpoints REST. Cf. sections 3 à 12. |

---

## 3. Inscriptions — art. 78, 80, 85, 86, 87

**Module** : [apps/inscriptions/api_urls.py](../backend/apps/inscriptions/api_urls.py), [views.py](../backend/apps/inscriptions/views.py).

### 3.1 `POST /api/v1/inscriptions/` — Dépôt

| Propriété | Valeur |
|-----------|--------|
| Vue | `ListeDeposerInscription` |
| Permission | `IsAuthenticated` |
| Rôle TDR | `AGENT_SAISIE` OU `DECLARANT_EXTERNE` (vérifié par `peut_enregistrer_demande`) |
| Serializer d'entrée | `DeposerInscriptionSerializer` (strict) |
| Serializer de sortie | `InscriptionSerializer` |
| Codes HTTP | 201 (créé, statut passe automatiquement à `EN_CONTROLE_FORME`) ; 400 (canal ou nature hors liste — `RejetForme` art. 80) ; 403 (non habilité) |
| Article fondateur | 78 al. 1, 85 |
| Exceptions métier | `RejetForme` (canal, nature), `AutorisationRefusee` |

**Payload (strict)** :
```json
{
  "canal_saisie": "guichet_papier | portail_electronique",
  "nature_droit": "<clé NaturesDroitInscrit (12 valeurs limitatives)>",
  "somme_garantie": "1000000.00",
  "monnaie": "MRU",
  "duree_en_jours": 365,
  "adresse_electronique_notifications": "optionnel@exemple.mr"
}
```

### 3.2 `GET /api/v1/inscriptions/` — Liste

| Propriété | Valeur |
|-----------|--------|
| Vue | `ListeDeposerInscription` |
| Permission | `IsAuthenticated` |
| Sortie | Page `InscriptionSerializer` |
| Codes HTTP | 200 ; 403 |
| Article fondateur | 77, 93 |
| Observation | Liste interne ; la recherche publique (§ 4.2.5) est distincte — cf. § 8. |

### 3.3 `GET /api/v1/inscriptions/<uuid:reference_demande>/` — Détail

| Propriété | Valeur |
|-----------|--------|
| Vue | `DetailInscription` |
| Permission | `IsAuthenticated` |
| Sortie | `InscriptionSerializer` |
| Codes HTTP | 200 ; 404 |

### 3.4 `POST /api/v1/inscriptions/<uuid>/valider/` — Validation

| Propriété | Valeur |
|-----------|--------|
| Vue | `ValiderInscription` |
| Permission | `IsAuthenticated` |
| Rôle TDR | `AUTORITE_VALIDATION` (séparation stricte § 4.1 : `saisie_par != acteur`) |
| Serializer d'entrée | aucun (action sans payload) |
| Serializer de sortie | `InscriptionSerializer` (numéro d'ordre attribué) |
| Codes HTTP | 200 ; 400 (statut non compatible) ; 403 (cumul saisie/validation ou rôle manquant) |
| Article fondateur | 78 al. 4, 85, 86, 87 |
| Effets | Attribution du numéro d'ordre `NNNNNN-AAAAMMJJHHMMSS` ; `instant_saisie_opposable` (STUB opposable=False) ; `date_expiration` = `instant.date() + duree_en_jours` ; transition → `INSCRITE` ; audit `inscription.valider`. |

### 3.5 `POST /api/v1/inscriptions/<uuid>/rejeter/` — Rejet motivé

| Propriété | Valeur |
|-----------|--------|
| Vue | `RejeterInscription` |
| Permission | `IsAuthenticated` |
| Rôle TDR | `AUTORITE_VALIDATION` (séparation stricte § 4.1) |
| Serializer d'entrée | `RejeterInscriptionSerializer` (strict) |
| Serializer de sortie | `InscriptionSerializer` |
| Codes HTTP | 200 ; 400 (motif hors liste — `RejetForme` art. 80) ; 403 |
| Article fondateur | 80, 86 |
| Effets | Transition → `REJETEE` ; `motif_rejet` figé ; commentaires bilingues ; audit `inscription.rejeter`. |

**Payload (strict)** :
```json
{
  "motif": "canal_non_autorise | informations_illisibles | informations_incomprehensibles",
  "commentaire_fr": "optionnel",
  "commentaire_ar": "اختياري"
}
```

---

## 4. Modifications — art. 88, 90, 93

**Module** : [apps/modifications/api_urls.py](../backend/apps/modifications/api_urls.py).

### 4.1 `POST /api/v1/modifications/` — Création demande

| Propriété | Valeur |
|-----------|--------|
| Vue | `ListeCreerModification` |
| Permission | `IsAuthenticated` |
| Serializer | `DemandeModificationSerializer` (strict) |
| Codes HTTP | 201 ; 400 ; 403 |
| Article fondateur | 88, 93 |
| Observation | À ce stade, la demande est à l'état `RECUE` ; elle n'est PAS encore appliquée. |

**Payload** (extrait — clés strictes) :
```json
{
  "inscription": <id>,
  "objet_modification_fr": "...",
  "objet_modification_ar": "...",
  "diff_propose": {
    "parties": {"ajouter": [...], "retirer": [...]},
    "biens":   {"ajouter": [...], "retirer": [...]},
    "scalaires": {"nature_droit"|"somme_garantie"|"monnaie"|"adresse_electronique_notifications": ...}
  },
  "accord_createur_confirme": true,
  "accord_constituant_confirme": true
}
```

### 4.2 `GET /api/v1/modifications/` — Liste

| Propriété | Valeur |
|-----------|--------|
| Permissions | `IsAuthenticated` |
| Serializer sortie | `DemandeModificationSerializer` (expose `motif_refus_code`) |
| Codes HTTP | 200 ; 403 |

### 4.3 `POST /api/v1/modifications/<int:pk>/appliquer/` — Application

| Propriété | Valeur |
|-----------|--------|
| Vue | `AppliquerModification` |
| Rôle TDR | `AUTORITE_VALIDATION` (séparation stricte) |
| Codes HTTP | 200 ; 400 (`ModificationSansEffet` — art. 88 dernier al.) ; 403 (cumul / habilitation) |
| Article fondateur | 88, 90 |
| Exceptions | `ModificationSansEffet` (8 motifs `MotifRefusModification`), `AutorisationRefusee` |
| Effets | Savepoint ; snapshots AVANT/APRÈS ; transition → `MODIFIEE` ; audit `modification.appliquer` OU `modification.refuser` selon issue. |

**Motifs limitatifs de refus** (`MotifRefusModification`) :
`etat_final_constituant_absent`, `etat_final_creancier_absent`,
`etat_final_bien_absent`, `accords_manquants`,
`statut_inscription_incompatible`, `diff_invalide`, `diff_vide`,
`demande_non_applicable`.

---

## 5. Renouvellements — art. 91

**Module** : [apps/renouvellements/api_urls.py](../backend/apps/renouvellements/api_urls.py).

### 5.1 `POST /api/v1/renouvellements/` — Création demande

| Propriété | Valeur |
|-----------|--------|
| Serializer | `DemandeRenouvellementSerializer` (strict) |
| Codes HTTP | 201 ; 400 ; 403 |
| Article fondateur | 91 |

**Payload** :
```json
{"inscription": <id>}
```

### 5.2 `POST /api/v1/renouvellements/<int:pk>/appliquer/` — Application

| Propriété | Valeur |
|-----------|--------|
| Rôle TDR | `AUTORITE_VALIDATION` |
| Codes HTTP | 200 ; 400 (`RenouvellementHorsDelai`) ; 403 |
| Article fondateur | 91 |
| Exceptions | `RenouvellementHorsDelai`, `TransitionInterdite`, `AutorisationRefusee` |
| Effets | Prorogation : `nouvelle_date_expiration = ancienne_date_expiration + duree_en_jours` (hypothèse A3 — durée initiale). Transition → `RENOUVELEE`. |

---

## 6. Radiations — art. 92

**Module** : [apps/radiations/api_urls.py](../backend/apps/radiations/api_urls.py).

### 6.1 `POST /api/v1/radiations/` — Création demande

| Propriété | Valeur |
|-----------|--------|
| Serializer | `DemandeRadiationSerializer` (strict) |
| Codes HTTP | 201 ; 400 ; 403 |
| Article fondateur | 92 al. 1 |

**Payload** (champs art. 92 al. 1) :
```json
{
  "inscription": <id>,
  "fondement": "consentement | jugement | requerant_original",
  "nom_constituant": "...", "prenom_constituant": "...",
  "denomination_constituant": "...", "adresse_constituant": "...",
  "numero_rc_constituant": "..."
}
```

### 6.2 `POST /api/v1/radiations/<int:pk>/appliquer/`

| Propriété | Valeur |
|-----------|--------|
| Codes HTTP | 200 ; 400 (`TransitionInterdite`) ; 403 |
| Article fondateur | 92 al. 2 |
| Effets | Activation de `mention_radiee`, transition → `RADIEE`. Le transfert au fichier général (art. 92 al. 3) reste déclenché à l'échéance par `expirer_inscriptions`. |

---

## 7. Rejets — art. 80 (vue dédiée)

**Module** : [apps/rejets/api_urls.py](../backend/apps/rejets/api_urls.py).

### 7.1 `GET /api/v1/rejets/` — Liste des inscriptions rejetées

| Propriété | Valeur |
|-----------|--------|
| Vue | `ListeRejets` |
| Permissions | `IsAuthenticated` |
| Filtre optionnel | `?motif=<MotifRejet>` |
| Sortie | `InscriptionSerializer` limité aux `statut=REJETEE` |
| Codes HTTP | 200 ; 403 |
| Observation | Vue de consultation ; le prononcé du rejet passe par `POST /api/v1/inscriptions/<uuid>/rejeter/`. |

---

## 8. Recherche publique — art. 94 à 97

**Module** : [apps/recherche/api_urls.py](../backend/apps/recherche/api_urls.py).

### 8.1 `POST /api/v1/recherche/`

| Propriété | Valeur |
|-----------|--------|
| Vue | `RecherchePublique` |
| Permission | `AllowAny` (art. 94 — « ouverture à tout intéressé ») |
| Serializer d'entrée | `_CriteresSerializer` (strict — 4 critères limitatifs art. 96) |
| Codes HTTP | 200 ; 400 (`RechercheCriteresInsuffisants` art. 96 ; clé hors liste via `StrictInputSerializer`) |
| Article fondateur | 94, 95, 96, 97 al. 2 |
| Effets | Requête tracée dans `RequeteRecherche` (append-only) + audit `recherche.lancer`. |

**Payload** (4 clés maximum, liste limitative) :
```json
{
  "nom_constituant": "...",
  "numero_rc": "...",
  "numero_serie_bien": "...",
  "numero_inscription": "..."
}
```

**Règle** : au moins 2 des 4 clés renseignées (art. 96).

**Réponse (extrait)** :
```json
{
  "instant": "2026-04-21T12:00:00+00:00",
  "requete_id": 42,
  "criteres_utilises": ["nom_constituant", "numero_rc"],
  "nombre_resultats": 1,
  "inscriptions": [ /* InscriptionSerializer[] */ ],
  "homonymes_par_inscription": {
    "<pk>": [ {"nom", "prenom", "denomination", "adresse", "date_naissance"} ]
  },
  "avertissement": "Aperçu non opposable — certificat probant art. 97 GELÉ."
}
```

---

## 9. Certificats — art. 78, 86, 88-92, 97

**Module** : [apps/certificats/api_urls.py](../backend/apps/certificats/api_urls.py).

### 9.1 `GET /api/v1/certificats/` — Liste

| Propriété | Valeur |
|-----------|--------|
| Serializer sortie | `CertificatSerializer` (strict — expose `probant`) |
| Codes HTTP | 200 ; 403 |

### 9.2 `GET /api/v1/certificats/<int:pk>/` — Détail

| Propriété | Valeur |
|-----------|--------|
| Codes HTTP | 200 ; 403 ; 404 |
| ⚠️ | **ZONE GELÉE L11/A5** : `Certificat.probant` reste à `False` ; la production PDF/A bilingue signée (art. 97 dernier al.) n'est PAS câblée. Aucun endpoint de téléchargement probant. |

---

## 10. Statistiques — art. 82

**Module** : [apps/statistiques/api_urls.py](../backend/apps/statistiques/api_urls.py).

### 10.1 `GET /api/v1/statistiques/` — Liste des extractions

| Propriété | Valeur |
|-----------|--------|
| Serializer sortie | `ExtractionStatistiqueSerializer` (strict) |
| Codes HTTP | 200 ; 403 |

### 10.2 `POST /api/v1/statistiques/produire/` — Produire une extraction

| Propriété | Valeur |
|-----------|--------|
| Vue | `ProduireExtraction` |
| Permission | `IsAuthenticated` |
| **Rôle TDR** | `PROD_STATS` — **monopole art. 82** (vérifié par `peut_produire_statistiques`) |
| Codes HTTP | 200 ; 403 (`AutorisationRefusee` si rôle absent) |
| Article fondateur | 82 |

**Payload** :
```json
{
  "perimetre": {
    "date_debut": "2026-01-01",
    "date_fin":   "2026-12-31"
  }
}
```

**Réponse** : agrégats `par_statut`, `par_nature_droit`, `par_canal_saisie`, `total`, `instant_calcul`.

---

## 11. Référentiels bilingues — consultation publique

**Module** : [apps/referentiels/api_urls.py](../backend/apps/referentiels/api_urls.py).

| Route | Modèle | Article fondateur |
|-------|--------|-------------------|
| `GET /api/v1/referentiels/natures-droit/` | `LibelleNatureDroit` | 76 |
| `GET /api/v1/referentiels/motifs-rejet/` | `LibelleMotifRejet` | 80 |
| `GET /api/v1/referentiels/canaux-saisie/` | `LibelleCanalSaisie` | 78 |
| `GET /api/v1/referentiels/criteres-recherche/` | `LibelleCritereRecherche` | 96 |
| `GET /api/v1/referentiels/types-certificats/` | `LibelleTypeCertificat` | — |

| Propriété commune | Valeur |
|-------------------|--------|
| Permission | `AllowAny` |
| Codes HTTP | 200 |
| Champs | `cle, libelle_fr, libelle_ar, langue_faisant_foi, description_fr, description_ar, ordre` |

---

## 12. Journal d'audit — § 5.2

**Module** : [apps/audit/api_urls.py](../backend/apps/audit/api_urls.py).

### 12.1 `GET /api/v1/audit/entrees/`

| Propriété | Valeur |
|-----------|--------|
| Vue | `ListeEntreesAudit` |
| Permission | `_PermissionLectureAudit` (placeholder — actuellement `is_staff=True`, à remplacer par rôle `AUDITEUR` dès § 4.1 complet) |
| Serializer sortie | `EntreeAuditSerializer` (strict, read-only) |
| Codes HTTP | 200 ; 403 (non-auditeur) |
| Article fondateur | 79, § 5.2 |

### 12.2 `GET /api/v1/audit/verification-chaine/`

| Propriété | Valeur |
|-----------|--------|
| Vue | `VerificationChaineAudit` |
| Permission | idem |
| Réponse | `{integre: bool, premiere_entree_alteree: int\|null}` |
| Codes HTTP | 200 ; 403 |
| Article fondateur | 79 al. 2 |

---

## 13. Matrice condensée des endpoints

| Route | Méthode | Perm | Article | 200 | 201 | 400 | 403 | 404 |
|-------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `/api/v1/inscriptions/` | POST | Auth | 78, 85 | | ✅ | ✅ | ✅ | |
| `/api/v1/inscriptions/` | GET | Auth | 77 | ✅ | | | ✅ | |
| `/api/v1/inscriptions/<uuid>/` | GET | Auth | — | ✅ | | | ✅ | ✅ |
| `/api/v1/inscriptions/<uuid>/valider/` | POST | Auth+greff. | 85, 87 | ✅ | | ✅ | ✅ | ✅ |
| `/api/v1/inscriptions/<uuid>/rejeter/` | POST | Auth+greff. | 80 | ✅ | | ✅ | ✅ | ✅ |
| `/api/v1/modifications/` | POST/GET | Auth | 88, 93 | ✅ | ✅ | ✅ | ✅ | |
| `/api/v1/modifications/<id>/appliquer/` | POST | Auth+greff. | 88, 90 | ✅ | | ✅ | ✅ | ✅ |
| `/api/v1/renouvellements/` | POST/GET | Auth | 91 | ✅ | ✅ | ✅ | ✅ | |
| `/api/v1/renouvellements/<id>/appliquer/` | POST | Auth+greff. | 91 | ✅ | | ✅ | ✅ | ✅ |
| `/api/v1/radiations/` | POST/GET | Auth | 92 | ✅ | ✅ | ✅ | ✅ | |
| `/api/v1/radiations/<id>/appliquer/` | POST | Auth+greff. | 92 | ✅ | | ✅ | ✅ | ✅ |
| `/api/v1/rejets/` | GET | Auth | 80 | ✅ | | | ✅ | |
| `/api/v1/recherche/` | POST | **Public** | 94, 96, 97 | ✅ | | ✅ | | |
| `/api/v1/certificats/` | GET | Auth | — | ✅ | | | ✅ | |
| `/api/v1/certificats/<id>/` | GET | Auth | — | ✅ | | | ✅ | ✅ |
| `/api/v1/statistiques/` | GET | Auth | 82 | ✅ | | | ✅ | |
| `/api/v1/statistiques/produire/` | POST | Auth+PROD_STATS | 82 | ✅ | | ✅ | ✅ | |
| `/api/v1/referentiels/*` | GET | **Public** | 76/78/80/96 | ✅ | | | | |
| `/api/v1/audit/entrees/` | GET | Auditeur | 79, § 5.2 | ✅ | | | ✅ | |
| `/api/v1/audit/verification-chaine/` | GET | Auditeur | § 5.2 | ✅ | | | ✅ | |

---

## 14. Matrice de bilinguisme par endpoint

| Endpoint | Langue d'entrée | Langue de sortie |
|----------|-----------------|------------------|
| Dépôt d'inscription | Clés neutres (`canal_saisie`, `nature_droit`) ; monnaie ISO | Clés neutres + `*_libelle` résolus selon `Accept-Language` |
| Rejet d'inscription | `motif` neutre + commentaires FR/AR | Commentaires bilingues préservés |
| Demande de modification | `objet_modification_fr` + `objet_modification_ar` ; diff neutre (clés) | Idem |
| Renouvellement | Neutre (identifiant seul) | Dates neutres |
| Radiation | Champs art. 92 neutres ; `fondement` clé neutre | Idem |
| Recherche publique | Clés neutres (`nom_constituant`, `numero_rc`, …) | Données neutres ; avertissement fourni par i18n (fr/ar selon `Accept-Language`) |
| Référentiels | — | Paires `libelle_fr`, `libelle_ar` + `langue_faisant_foi` |
| Audit | — | Clés d'action neutres (`inscription.deposer`, `modification.refuser`, …) |

**Principe** : aucune API ne produit une réponse dont la **substance
juridique** dépend de la langue. Seuls les libellés d'affichage sont
localisés ; toutes les clés, numéros, horodatages, montants, statuts
sont rendus en version neutre.

---

## 15. Exceptions métier catalogue

Tableau des exceptions qui peuvent remonter à l'API et leur traduction
HTTP (cf. `rsm_exception_handler`).

| Exception (module `apps.core.exceptions` / autres) | Article | HTTP | Cas d'émission |
|----------------------------------------------------|:-------:|:----:|----------------|
| `RejetForme` | 80 | 400 | Canal hors liste, nature hors liste, motif de rejet hors liste |
| `ModificationSansEffet` | 88 | 400 | Diff invalide, diff vide, état final invalide, accords manquants, statut incompatible, demande non ré-applicable |
| `RenouvellementHorsDelai` | 91 | 400 | Renouvellement demandé après expiration |
| `RechercheCriteresInsuffisants` | 96 | 400 | < 2 critères renseignés |
| `TransitionInterdite` | — (§ 4.3) | 400 | Transition hors matrice ou interdiction explicite |
| `RegimeDeclaratifViole` | 86 | 400 | (Réservé — pour garde-fous futurs) |
| `AutorisationRefusee` | § 4.1 | 403 | Habilitation manquante ou cumul saisie/validation sur la même demande |
| `PermissionError` | 79 | 403 | Tentative de `save()` / `delete()` sur modèle append-only |

---

## 16. Cohérence avec L11 et L3.2

- La colonne « Article fondateur » de chaque endpoint renvoie à L11 (traçabilité article par article).
- Les flux applicatifs détaillés figurent dans L3.2 § 4.
- Les règles de sécurité qui s'appliquent transversalement à ces endpoints sont consolidées dans L3.5.
- L'équivalence juridique FR/AR des endpoints est démontrée dans L3.6.

---

## 17. Renvois croisés

- Modèle de données : [L3.1](L3_1_modele_donnees.md).
- Architecture et flux : [L3.2](L3_2_architecture_modulaire.md).
- Horodatage et scellement : [L3.3](L3_3_horodatage_scellement.md).
- Sécurité et intégrité : [L3.5](L3_5_securite_integrite.md).
- Bilinguisme : [L3.6](L3_6_matrice_bilingue.md).
- Traçabilité : [L11](L11_tracabilite_articles_76_97.md).
