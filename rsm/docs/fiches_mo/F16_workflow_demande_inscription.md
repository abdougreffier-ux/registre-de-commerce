# Fiche MO F16 — Workflow Demande ⇄ Inscription

**Statut** : arbitrée et implémentée — directive MO du 2026-05-31.
**Périmètre** : distinction DEMANDE / INSCRIPTION, retour avec observation,
resoumission par le déclarant.

---

## 1. Énoncé du principe (formulation MO)

> *Une demande ne devient une inscription QUE si elle est validée par
> le greffier. Le système doit distinguer clairement DEMANDE et INSCRIPTION.*

## 2. Statuts cibles MO

| Statut MO | Sémantique |
|---|---|
| `brouillon` | Demande saisie mais non encore soumise au greffe. |
| `soumis` | Soumise au greffe, en file d'attente. |
| `en_attente_validation` | Prise en charge par le greffe, examinée. |
| `retournee` | Retournée au déclarant avec observation. |
| `valide` | Décision positive du greffier. |
| `inscrit` | Acte inscrit au registre avec numéro d'ordre. |

## 3. Mapping pragmatique vers `StatutInscription` (base de données)

Pour préserver l'existant (matrice TRANSITIONS et tests S1/S2 déjà validés),
le mapping retenu **n'introduit en base que deux statuts réellement nouveaux** :

| Statut MO | Valeur en base (`StatutInscription`) | Type |
|---|---|---|
| `brouillon` | `BROUILLON` (NOUVEAU) | Statut technique |
| `soumis` | `RECUE` (existant) | Mapping i18n |
| `en_attente_validation` | `EN_CONTROLE_FORME` (existant) | Mapping i18n |
| `retournee` | `RETOURNEE` (NOUVEAU) | Statut technique |
| `valide` | `INSCRITE` (existant) | Mapping i18n |
| `inscrit` | `INSCRITE` (existant) | Identique à `valide` |

Conséquence : les libellés MO sont portés par l'i18n frontend
(`inscription.statut.*`, `inscription.statut_court.*`), pas par la base.
Aucune migration destructrice.

## 4. Transitions ajoutées (TRANSITIONS)

| Depuis | Vers | Événement | Articles |
|---|---|---|---|
| `BROUILLON` | `RECUE` | `soumission_declarant` | 78, 85 |
| `EN_CONTROLE_FORME` | `RETOURNEE` | `retour_observation` | 85, 86 |
| `RETOURNEE` | `EN_CONTROLE_FORME` | `resoumission_declarant` | 78, 85 |

## 5. Interdictions explicites ajoutées (verrous)

| Depuis | Vers | Motif |
|---|---|---|
| `RETOURNEE` | `INSCRITE` | Une demande retournée doit repasser par le contrôle de forme après resoumission. |
| `INSCRITE` | `RETOURNEE` | Une inscription validée ne peut être retournée ; la correction passe uniquement par une modification art. 88. |

## 6. Modèle `ObservationRetour` (append-only)

- FK `inscription` (PROTECT) → conservation pérenne (art. 79).
- `observation_fr` + `observation_ar` : **obligatoires et non vides**
  (parité juridique FR/AR stricte).
- `cree_par` : greffier émetteur, `cree_le` indexé.
- `instant_resoumission` + `resoumis_par` : renseignés une seule fois
  à la resoumission, immuables ensuite.
- `save()` interdit la modification des champs après création ;
  `delete()` lève `PermissionError`.
- Plusieurs `ObservationRetour` peuvent exister par inscription
  (cycles N retours/resoumissions historisés).

## 7. Services et endpoints

### Services métier (`apps.inscriptions.services`)

| Fonction | Acteur | Précondition | Effet |
|---|---|---|---|
| `retourner_demande` | Greffier (autorité de validation) | `statut == EN_CONTROLE_FORME` + séparation stricte (acteur ≠ créateur) + observation FR+AR non vides | Crée `ObservationRetour`, passe à `RETOURNEE`, trace audit |
| `resoumettre_demande` | Déclarant initial uniquement | `statut == RETOURNEE` | Marque la dernière observation comme résolue, passe à `EN_CONTROLE_FORME`, trace audit |

### Endpoints REST

| Méthode | Route | Acteur | Description |
|---|---|---|---|
| `POST` | `/api/v1/inscriptions/<ref>/retourner/` | Greffier | Retour avec observation FR + AR |
| `POST` | `/api/v1/inscriptions/<ref>/resoumettre/` | Déclarant initial | Resoumission après correction |

## 8. Audit (catégories et résultats ajoutés)

- `CategorieAudit.RETOUR_CORRECTION` : retour au déclarant pour correction.
- `ResultatAudit.RETOUR_POUR_CORRECTION` : résultat intermédiaire (réversible).
- Actions tracées : `inscription.retourner` (greffier) et
  `inscription.resoumettre` (déclarant).

## 9. UX frontend

### Greffier (rôles : `autorite_validation`, `agent_saisie`, `auditeur`)

- **TableauBordGreffe** : KPI « Demandes en instance » + KPI
  « Demandes retournées » (en attente déclarant) + section dédiée.
- **DetailInscription** : 3 boutons d'action quand
  `statut == en_controle_forme` : **Valider**, **Retourner avec
  observation** (modale FR + AR), **Rejeter** (art. 80).
- **Historique des observations** : liste chronologique visible de tous
  les acteurs habilités, avec mention « Résolue » dès resoumission.

### Déclarant (rôle : `declarant_externe`)

- **MonEspace** : KPI « À corriger » + section « Mes demandes à corriger ».
- **DetailInscription** : observations visibles + bouton
  « Resoumettre la demande » (visible si `statut == retournee` ET
  propriétaire de la demande).

## 10. Garde-fous (non négociables)

1. **Intégrité** : append-only sur `ObservationRetour`, transition
   `RETOURNEE → INSCRITE` directe interdite.
2. **Traçabilité** : audit obligatoire pour chaque retour et chaque
   resoumission.
3. **Parité FR/AR** : observation obligatoirement bilingue (parité
   juridique stricte).
4. **Séparation stricte** : l'agent qui a saisi la demande ne peut
   pas la retourner lui-même (réutilisation de `peut_valider_demande`).
5. **Aucune demande ne devient inscription sans validation** : la
   transition vers `INSCRITE` reste sous l'unique contrôle de
   `valider_inscription()`.

## 11. Tests (`tests/test_workflow_retour_resoumission.py`)

7 tests couvrant :
1. Cycle nominal complet.
2. Observation FR/AR obligatoire.
3. Séparation stricte du retour.
4. Resoumission réservée au déclarant initial.
5. Verrou validation directe d'une `RETOURNEE`.
6. Cycles multiples historisés.
7. Immutabilité après création.

## 12. Référentiel documentaire

- `apps/workflow/statuts.py` — enum + matrice + interdictions.
- `apps/inscriptions/models.py` — modèle `ObservationRetour`.
- `apps/inscriptions/services.py` — `retourner_demande`, `resoumettre_demande`.
- `apps/inscriptions/views.py` — vues `RetournerDemande`, `ResoumettreDemande`.
- `frontend/src/pages/DetailInscription.jsx` — modale retour + bouton
  resoumettre.
- `frontend/src/pages/TableauBordGreffe.jsx` — files en instance + retournées.
- `frontend/src/pages/MonEspace.jsx` — section À corriger.
- `frontend/src/components/StatutBadge.jsx` — variantes BROUILLON / RETOURNEE.
- `frontend/src/i18n/{fr,ar}.json` — libellés MO et messages.
