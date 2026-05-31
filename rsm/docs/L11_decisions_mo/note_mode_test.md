# Note L11 — Mode TEST / RECETTE

## Objet

Cette note acte la mise en place d'un **MODE TEST** distinct du mode
PRODUCTION, destiné exclusivement à la recette fonctionnelle des
parcours métier (dépôt, validation, modification, renouvellement,
radiation, consultation, audit). Aucune donnée produite en mode TEST
n'est juridiquement opposable : la signalétique « MODE TEST — AUCUNE
VALEUR JURIDIQUE » est affichée en permanence sur l'ensemble des écrans.

## Activation

Le mode TEST est piloté par la variable d'environnement `RSM_MODE_TEST`
(défaut `true` dans `.env.test`, doit être `false` en production).

L'état est exposé par l'endpoint `/api/v1/auth/whoami/` dans le champ
`systeme.mode_test`. Le frontend lit cette valeur via `AuthContext` et
affiche le bandeau permanent `BandeauModeTest`.

## Périmètre activé

### Authentification
- Connexion par session Django via `/api/v1/auth/login/`.
- Comptes de test générés par `seed_demo_test` :
  - `agent_saisie`
  - `greffier`
  - `auditeur`
  - `declarant_externe`
  - `admin_fonctionnel`, `admin_technique`, `prod_stats`
- Mots de passe : voir le script `seed_demo_test.py`.
- Aucun MFA, aucune signature qualifiée, aucun e-ID.

### Parcours métier complets
- **Dépôt** (art. 85) — `POST /api/v1/inscriptions/` par
  `declarant_externe` ou `agent_saisie`. Statut initial
  `EN_CONTROLE_FORME`.
- **Validation greffier** (art. 78, 86) — `POST
  /api/v1/inscriptions/{ref}/valider/` par `autorite_validation`,
  attribution du numéro d'ordre horodaté.
- **Rejet motivé** (art. 80) — `POST
  /api/v1/inscriptions/{ref}/rejeter/` avec motif limitatif.
- **Modification** (art. 88) — `POST /api/v1/modifications/`.
- **Renouvellement** (art. 91) — `POST /api/v1/renouvellements/`.
- **Radiation** (art. 92) — `POST /api/v1/radiations/`.
- **Consultation** — `GET /api/v1/inscriptions/` et
  `GET /api/v1/inscriptions/{ref}/`.
- **Recherche publique** (art. 94-97) — `POST /api/v1/recherche/`.
- **Journal d'audit** (art. 79, § 5.2) — `GET /api/v1/audit/entrees/`.

### Mécanismes probants — simulés (non opposables)
- **Horodatage** : `RSM_TIMESOURCE_MODE=local_stub` ; renvoie
  `timezone.now()` avec drapeau `opposable=False`.
- **Scellement** : `RSM_SEAL_MODE=disabled` ; SHA-256 non signé.
- **Signature électronique** : booléens `accord_*_confirme` côté
  modèle, sans PKI.
- **Certificats** : structure `Certificat` peuplée, drapeau
  `probant=False`. Tout PDF produit doit porter visiblement la mention
  « TEST / NON OPPOSABLE ».
- **MFA** : `RSM_MFA_MODE=disabled`.

## Signalétique

- **Bandeau permanent** : `BandeauModeTest` posé en haut de chaque
  écran, fond rouge, texte blanc (palette officielle RIM).
- **Texte FR** : « MODE TEST — AUCUNE VALEUR JURIDIQUE ».
- **Texte AR** : « وضع اختبار — لا قيمة قانونية ».
- **Bandeau secondaire** existant « Paramètres opérationnels en
  attente » conservé pour rappeler les fiches F1-F6 en attente.

## Séparation stricte mode TEST / mode PRODUCTION

| Élément | Mode TEST | Mode PRODUCTION (futur) |
|---|---|---|
| `RSM_MODE_TEST` | `true` | `false` |
| Bandeau « MODE TEST » | visible | masqué |
| Comptes seed démo | présents | **interdits** |
| Mots de passe en clair | tolérés | **interdits** |
| `RSM_TIMESOURCE_MODE` | `local_stub` | `tsa_<désigné>` |
| `RSM_SEAL_MODE` | `disabled` | `<algos désignés>` |
| `RSM_ESIGN_MODE` | `disabled` | `<régime désigné>` |
| `RSM_MFA_MODE` | `disabled` | `<mécanisme désigné>` |
| Certificat `probant` | `False` | `True` après scellement |

## Garanties

- Aucune règle métier n'a été inventée pour le mode TEST.
- Le décret 2021-033 et les TDR ne sont pas modifiés.
- Le journal d'audit reste append-only et inaltérable, y compris en
  mode TEST.
- La levée du mode TEST se fait par bascule unique de la variable
  `RSM_MODE_TEST`, sans modification du code métier.

## Référence à la décision mère

Cette note complète :
- la décision MO n° 0001/2026 du 22 avril 2026 (levée juridique des
  zones gelées F1-F14, paramètres techniques en attente) ;
- la note L11 du 23 avril 2026 sur la cohérence du parcours de dépôt
  (OPTION B + ajout d'un mécanisme d'authentification de session).
