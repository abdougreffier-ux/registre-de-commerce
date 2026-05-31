# L3.5 — Dispositifs de sécurité et d'intégrité

**Livrable** : L3.5 — partie du livrable L3 (§ 8 du TDR).
**Objet** : formalisation complète de la défense en profondeur, des
contrôles d'habilitation, de la robustesse transactionnelle et des
protections contre les vulnérabilités courantes.
**Fondement** : TDR § 5.1 (sécurité et intégrité), § 5.2 (traçabilité),
§ 4.1 (rôles) ; articles 78, 79, 82, 86, 92, 97 du décret.
**État** : consolidation de l'existant. **Aucune règle nouvelle.**

---

## 1. Vue d'ensemble — quatre remparts indépendants

Le système applique une **défense en profondeur** : une même règle
juridique est garantie par plusieurs mécanismes techniques
indépendants, afin qu'une compromission d'un niveau soit neutralisée
par les autres.

```
┌─────────────────────────────────────────────────────────────────┐
│ REMPART 4 — Admin Django (L3.2 § 6)                             │
│  LectureSeuleAdmin / ConsultationMetierAdmin /                  │
│  EditionRestreinteAdmin + actions de masse désactivées          │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ REMPART 3 — API REST (DRF)                                      │
│  Handler d'exceptions uniforme, serializers stricts,            │
│  permissions, matrice d'habilitation                            │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ REMPART 2 — ORM / Services                                      │
│  Overrides save()/delete(), middleware d'audit,                 │
│  transactions atomiques + savepoints, validators                │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ REMPART 1 — PostgreSQL                                          │
│  Triggers d'immutabilité, CheckConstraints, UniqueConstraints   │
│  conditionnelles, verrous pessimistes                           │
└─────────────────────────────────────────────────────────────────┘
```

**Aucune règle critique** (art. 78, 79, 82, § 4.1, § 5.2) **n'est
protégée par un seul rempart.**

---

## 2. Rempart 1 — PostgreSQL

### 2.1 Triggers d'immutabilité

**Fichier** : [apps/audit/migrations/0002_append_only_triggers.py](../backend/apps/audit/migrations/0002_append_only_triggers.py).

```sql
CREATE OR REPLACE FUNCTION rsm_audit_interdire_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '42501',
        MESSAGE = 'Journal d''audit inaltérable : UPDATE/DELETE interdit (article 79).';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER rsm_audit_pas_update
BEFORE UPDATE ON audit_entreeaudit
FOR EACH ROW EXECUTE FUNCTION rsm_audit_interdire_mutation();

CREATE TRIGGER rsm_audit_pas_delete
BEFORE DELETE ON audit_entreeaudit
FOR EACH ROW EXECUTE FUNCTION rsm_audit_interdire_mutation();
```

**Portée** : toute tentative de modification ou suppression d'une ligne
du journal d'audit, **quelle que soit son origine** (application, accès
shell SQL, outil d'administration BDD), est refusée au niveau moteur.

### 2.2 Contraintes de cohérence

| Contrainte | Modèle | Règle |
|------------|--------|-------|
| `pp_sans_denomination` (CheckConstraint) | `Partie` | Une personne physique ne porte jamais de dénomination sociale. |
| `unique_role_actif_par_utilisateur` (UniqueConstraint conditionnelle `actif=True`) | `AffectationRole` | Un utilisateur ne peut avoir deux affectations actives du même rôle ; la réactivation reste possible après révocation. |
| `unique_partie_role_actif_par_inscription` (UniqueConstraint conditionnelle `actif=True`) | `RoleInscriptionPartie` | Un même lien (inscription, partie, rôle) ne peut exister qu'une fois actif ; historique préservé. |

### 2.3 Index pour l'intégrité des recherches (art. 93, 96)

| Index | Usage juridique |
|-------|-----------------|
| `Partie.(nom, prenom)` | Critère art. 96 (nom du constituant) |
| `Partie.denomination_sociale` | Critère art. 96 (dénomination) |
| `Partie.numero_rc` | Critère art. 96 (numéro RC) |
| `BienGreve.numero_serie` | Indexation additionnelle art. 93, critère art. 96 |
| `BienGreve.(inscription, actif)` | Résolution rapide des biens actifs (vue fichier public) |
| `Inscription.(statut, fichier_actuel)` | Séparation fichier public / général (art. 77) |
| `Inscription.numero_ordre` | Recherche par n° d'inscription (art. 96) |
| `Inscription.instant_saisie_opposable` | Chronologie opposable (art. 78 al. 3) |
| `Inscription.date_expiration` | Détection des expirations (art. 85, art. 92 al. 3) |
| `EntreeAudit.(categorie, instant)` | Consultation auditeur |
| `EntreeAudit.(objet_type, objet_reference)` | Reconstruction de l'historique d'un objet |

### 2.4 Verrous pessimistes

Point critique : l'unicité et la chronologie du numéro d'ordre
(art. 78 al. 4 ; critère § 10.1).

```python
# apps/inscriptions/services.py::attribuer_numero_ordre
seq = SequenceNumeroOrdre.objects.select_for_update().get_or_create(pk=1)[0]
ordre = seq.prochaine_valeur
seq.prochaine_valeur = ordre + 1
```

**Effet** : `SELECT … FOR UPDATE` verrouille la ligne unique de la
séquence pour la durée de la transaction. Tout autre demandeur est mis
en attente. **Testé sous 20 threads parallèles** (cf.
`tests/test_concurrence_art78.py`) — 20 numéros contigus, aucun
doublon, aucun trou.

### 2.5 Transactions atomiques

Toutes les opérations critiques sont encapsulées dans
`@transaction.atomic` :

- `apps.inscriptions.services.attribuer_numero_ordre` / `creer_demande` / `valider_inscription` / `prononcer_rejet` ;
- `apps.modifications.services.appliquer_modification` (+ savepoint interne) ;
- `apps.renouvellements.services.appliquer_renouvellement` ;
- `apps.radiations.services.appliquer_radiation` ;
- `apps.workflow.services.appliquer_transition` ;
- `apps.audit.services.tracer` ;
- `apps.inscriptions.management.commands.expirer_inscriptions._expirer_puis_archiver`.

---

## 3. Rempart 2 — ORM et services

### 3.1 Overrides `save()` / `delete()`

| Modèle | `save()` de update refusé | `delete()` refusé | Référence article |
|--------|:-:|:-:|:-----------------:|
| `EntreeAudit` | ✅ | ✅ | 79, § 5.2 |
| `TransitionStatut` | ✅ | ✅ | 79, § 4.3 |
| `RequeteRecherche` | ✅ | ✅ | 79, § 5.2 |
| `SnapshotInscription` | ✅ | ✅ | 79 |
| `ExtractionStatistique` | ✅ | ✅ | 79, 82 |
| `SequenceNumeroOrdre` | ✅ (hors service) | ✅ | 78 |
| `BienGreve` | ✅ (via ValiditeTemporelle) | ✅ | 79 |
| `RoleInscriptionPartie` | ✅ (via validité) | ✅ | 79 |

Exemple :
```python
# apps/audit/models.py::EntreeAudit
def save(self, *args, **kwargs):
    if self.pk is not None:
        raise PermissionError(
            "Le journal d'audit est append-only : toute modification "
            "d'une entrée existante est interdite."
        )
    super().save(*args, **kwargs)

def delete(self, *args, **kwargs):
    raise PermissionError(
        "Le journal d'audit est append-only : toute suppression est "
        "interdite (article 79 du décret 2021-033)."
    )
```

### 3.2 Savepoints et rollback ciblé

**Fichier critique** :
[apps/modifications/services.py::appliquer_modification](../backend/apps/modifications/services.py).

```python
sid = transaction.savepoint()
try:
    snap_avant = _produire_snapshot(...)
    # ... mutation des rôles, biens, scalaires
    _verifier_etat_final(inscription)   # art. 88 dernier al.
    snap_apres = _produire_snapshot(...)
    appliquer_transition(...)
except EtatFinalInvalide as exc:
    transaction.savepoint_rollback(sid)
    _marquer_rejet(demande=..., motif_code=exc.motif_code, detail=str(exc))
    raise ModificationSansEffet(str(exc)) from exc
transaction.savepoint_commit(sid)
```

**Garantie** : en cas de violation de l'art. 88, l'intégralité des
mutations (incluant `SnapshotInscription` « AVANT ») est annulée, mais
la demande est persistée avec `statut=REJETEE` et `motif_refus_code`
structuré. **Impossible de contourner le contrôle art. 88 par
modifications successives** — cf. tests anti-contournement dans
[tests/test_modifications_cas_limites.py](../backend/tests/test_modifications_cas_limites.py).

### 3.3 Middleware d'audit — contexte du requêteur

**Fichier** : [apps/audit/middleware.py](../backend/apps/audit/middleware.py).

Pour chaque requête HTTP, `CurrentActorMiddleware` peuple un
`ContextVar` avec :
- identifiant utilisateur ;
- rôle applicatif actif ;
- adresse IP (avec gestion `X-Forwarded-For` à raffiner avec
  l'arbitrage infrastructure) ;
- user-agent tronqué à 255 caractères.

Les services d'audit appellent `contexte_courant()` sans avoir à
transporter l'acteur manuellement. **Compatible asynchrone**
(`contextvars`).

### 3.4 Signaux de traçabilité

**Fichier** : [apps/utilisateurs/signals.py](../backend/apps/utilisateurs/signals.py).

Tout `post_save` sur `AffectationRole` est automatiquement tracé
(`categorie=compte`, `action_cle=affectation.creer` ou
`affectation.mettre_a_jour`). **L'administrateur fonctionnel ne peut
donc pas attribuer un rôle sans laisser de trace.**

### 3.5 Chaînage cryptographique du journal d'audit

**Fichier** : [apps/audit/services.py::_calculer_empreinte](../backend/apps/audit/services.py).

```
empreinte(n) = SHA-256( canonicalise({
    "precedente": empreinte(n-1),
    "entree":     {instant, catégorie, action_cle, résultat,
                   acteur_id, acteur_role, objet_type,
                   objet_reference, details}
}) )
```

**Détection d'altération** : la fonction `verifier_chaine()` recalcule
toute la chaîne ; toute incohérence identifie l'id de la première
entrée altérée. Exposée via `GET /api/v1/audit/verification-chaine/`.

**Testé sous concurrence** : 8 threads × 25 écritures simultanées
(cf. `tests/test_audit_concurrence.py`) — chaîne intègre, aucune
empreinte dupliquée.

---

## 4. Rempart 3 — API REST (DRF)

### 4.1 Handler d'exceptions centralisé

**Fichier** : [apps/core/exception_handler.py](../backend/apps/core/exception_handler.py).

Configuré dans `REST_FRAMEWORK["EXCEPTION_HANDLER"]` —
traduit uniformément les exceptions métier en réponses HTTP
structurées (cf. L3.4 § 15).

**Bénéfice** : aucune vue ne gère les exceptions manuellement → pas de
fuite d'informations techniques, pas de divergence de codes entre
endpoints.

### 4.2 Serializers stricts — rejet des clés inconnues

**Fichier** : [apps/core/serializers.py](../backend/apps/core/serializers.py).

```python
class StrictInputMixin:
    def to_internal_value(self, data):
        if isinstance(data, dict):
            admises = set(self.fields.keys())
            recues = set(data.keys())
            inconnues = recues - admises
            if inconnues:
                raise serializers.ValidationError({
                    "non_autorises": [...],
                })
        return super().to_internal_value(data)
```

**Portée** : appliqué à TOUS les serializers d'entrée de l'API (cf.
L3.4 pour l'inventaire). Tests d'uniformité dans
[tests/test_serializers_stricts.py](../backend/tests/test_serializers_stricts.py).

### 4.3 Matrice d'habilitation (§ 4.1)

**Fichier** : [apps/utilisateurs/habilitations.py](../backend/apps/utilisateurs/habilitations.py).

Les décisions d'autorisation sont **centralisées** dans ce module.
Aucune vue ni service ne contient de logique d'autorisation en dur.

| Opération | Fonction d'autorisation | Règle |
|-----------|------------------------|-------|
| Déposer une demande | `peut_enregistrer_demande(acteur)` | `AGENT_SAISIE` OU `DECLARANT_EXTERNE` |
| Valider / rejeter une demande | `peut_valider_demande(acteur, saisie_par)` | `AUTORITE_VALIDATION` ET `saisie_par ≠ acteur` (séparation stricte) |
| Vérifier non-cumul (outil d'audit) | `verifier_non_cumul(acteur)` | Refuse si `AGENT_SAISIE` et `AUTORITE_VALIDATION` sur le même compte (usage conseil, non imposé) |
| Écriture métier générale | `ecriture_metier_autorisee(acteur)` | `False` pour les administrateurs (§ 4.1) |
| Lire le journal d'audit | `peut_lire_audit(acteur)` | `AUDITEUR` |
| Produire des statistiques | `peut_produire_statistiques(acteur)` | `PROD_STATS` (monopole art. 82) |

**Toute modification de cette matrice doit être tracée par une mise à
jour explicite du livrable L11.**

### 4.4 Permissions DRF par endpoint

Cf. L3.4 § 13 — matrice condensée.

Points cardinaux :

- **Public** (`AllowAny`) : recherche (art. 94) et référentiels.
- **Authentifié + rôle** : tous les endpoints d'écriture.
- **Auditeur** : `/api/v1/audit/*`.

### 4.5 Règle de séparation stricte (§ 4.1)

Vérification dans chaque service de validation :
```python
if not peut_valider_demande(acteur, saisie_par=inscription.cree_par):
    raise AutorisationRefusee(
        "Validation refusée (séparation stricte, § 4.1)."
    )
```

Testé par `tests/test_habilitations.py::SeparationStricteTests` et
par le scénario d'intégration API S1 (cf. `tests/test_api_s1_cycle_nominal.py`).

---

## 5. Rempart 4 — Admin Django

Cf. L3.2 § 6 et L11 (matrice d'habilitation de l'administration Django).

Synthèse :
- 5 modèles append-only → `LectureSeuleAdmin` (aucune permission d'écriture).
- 9 modèles métier → `ConsultationMetierAdmin` (mutations exclusivement par services).
- 5 référentiels + affectations de rôles → `EditionRestreinteAdmin` (add/delete contrôlés, change admis).
- `Utilisateur` → `UserAdmin` + `has_delete=False` + actions désactivées.
- Actions de masse **désactivées uniformément** (classe mère `_BaseAdminRSM`).

**Testé** : [tests/test_admin_lecture_seule.py](../backend/tests/test_admin_lecture_seule.py) —
y compris pour un `is_superuser=True`.

---

## 6. Protections contre les vulnérabilités courantes (TDR § 5.1)

Le TDR exige des protections contre les injections, XSS, CSRF,
détournement de session, contournement d'autorisation. Consolidation :

### 6.1 Injection SQL

- **Rempart 1** : ORM Django paramétré — aucune concaténation SQL brute dans l'application.
- **Rempart 2** : les rares `RunSQL` (triggers d'audit) sont statiques et figés dans une migration versionnée.
- **Test** : la liste limitative des champs modifiables par le diff (`CHAMPS_SCALAIRES_MODIFIABLES`) empêche d'injecter un nom de colonne arbitraire via un payload.

### 6.2 XSS (Cross-Site Scripting)

- **Templates Django** : auto-escape par défaut — aucun `{% autoescape off %}` dans le projet.
- **DRF** : les réponses sont JSON (pas d'HTML sérialisé côté serveur).
- **Frontend React** : Ant Design gère l'échappement ; aucun `dangerouslySetInnerHTML` dans le code livré.
- **Observation bilingue** : les libellés arabes (RTL) sont échappés comme les libellés latins ; aucune différence de traitement entre FR et AR.

### 6.3 CSRF

- **Middleware Django** `CsrfViewMiddleware` actif dans `settings.MIDDLEWARE`.
- API DRF : la politique de session exige le token CSRF sur les requêtes `unsafe`.
- Point d'exploitation GELÉ : la politique définitive (cookies `SameSite`, `Secure`) sera fixée à l'arbitrage infrastructure (L11/MFA).

### 6.4 Détournement de session

- Sessions Django classiques ; en production, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE` à positionner (GELÉ, lié aux arbitrages d'infrastructure).
- Rotation de session à chaque changement de privilège (non câblée, GELÉ avec MFA).

### 6.5 Contournement d'autorisation

- Matrice centralisée dans `apps.utilisateurs.habilitations` (§ 4.3 du présent document).
- Chaque vue passe par un service — les services vérifient l'habilitation **avant** toute mutation.
- Les administrateurs n'ont jamais de chemin d'écriture métier (Rempart 4).
- L'accès aux endpoints d'audit est filtré par permission explicite.

### 6.6 Upload de fichiers

- **Modèle** `PieceJointe` : accepte `File` avec chemin `pieces_jointes/%Y/%m/`.
- Contrôle de format / antivirus : **GELÉ** (dépend de l'infrastructure de production). À arbitrage MO + équipe d'exploitation.
- Empreinte SHA-256 stockée dans `sceau_empreinte` (STUB pour opposabilité).

---

## 7. Horloge et cryptographie — ZONES GELÉES (rappel)

Les mécanismes de temps et de scellement sont décrits en détail dans
[L3.3](L3_3_horodatage_scellement.md). Rappel de leur contribution à
la sécurité :

| Dispositif | État | Bascule attendue |
|------------|:----:|------------------|
| Source de temps supervisée (art. 78, § 5.1) | GELÉ | `ntp_stratum_X` / `ptp` / `hsm_trusted_clock` |
| Scellement des inscriptions et snapshots | STUB SHA-256 (non opposable) | `hmac` / `asymmetric_signature` / `chained_log` |
| Signature électronique des parties (art. 88) | Flags applicatifs | Vérification cryptographique PKI |
| Authentification forte (§ 5.1) | Session Django | `totp` / `x509_card` / `id_numerique_nationale` |

⚠️ **Aucune de ces zones ne peut être activée sans décision MO écrite
et référencée.**

---

## 8. Robustesse transactionnelle

### 8.1 Atomicité garantie

- Toute fonction de service critique est décorée `@transaction.atomic`.
- Le savepoint interne d'`appliquer_modification` protège l'état final art. 88.
- Aucune opération partielle ne subsiste en cas d'erreur — cf.
  `tests/test_robustesse_transactionnelle.py`.

### 8.2 Concurrence

- Verrou pessimiste sur la séquence du n° d'ordre (art. 78).
- Chaînage de l'audit résistant à la concurrence (testé 8×25).
- `UniqueConstraint` conditionnelles sur `(utilisateur, role)` et
  `(inscription, partie, role)` — collisions d'insertion détectées
  par PostgreSQL en cas de concurrence.

### 8.3 Défaillance partielle

Trois scénarios testés :
- défaillance après snapshot AVANT mais avant contrôle état final ;
- défaillance après contrôle état final mais avant transition ;
- défaillance pendant la production du snapshot APRÈS.

Dans les trois cas, le rollback est complet : aucun snapshot orphelin,
aucune désactivation résiduelle, aucune trace `modification.appliquer`.

---

## 9. Intégrité du journal d'audit — exhaustivité

Chaque service métier appelle `tracer()` avec les champs obligatoires
§ 5.2 (acteur, horodatage, objet, résultat). L'exhaustivité est
vérifiée par le scénario S1 ([tests/test_api_s1_cycle_nominal.py](../backend/tests/test_api_s1_cycle_nominal.py))
qui constate la présence des 13 `action_cle` attendues au cours d'un
cycle de vie complet.

Actions tracées (non limitatif) :
- `inscription.deposer`
- `inscription.valider`
- `inscription.rejeter`
- `inscription.expirer_archiver`
- `modification.appliquer` / `modification.refuser`
- `renouvellement.appliquer`
- `radiation.appliquer`
- `transition.<evenement>` (15 transitions de la matrice)
- `recherche.lancer`
- `certificat.preparer`
- `statistiques.extraire`
- `affectation.creer` / `affectation.mettre_a_jour`
- `referentiels.seed`

---

## 10. Tests de sécurité consolidés

| Fichier | Couverture |
|---------|-----------|
| [tests/test_audit.py](../backend/tests/test_audit.py) | Chaînage, immuabilité update/delete, indépendance linguistique |
| [tests/test_audit_concurrence.py](../backend/tests/test_audit_concurrence.py) | Chaîne intègre sous concurrence 8×25 |
| [tests/test_concurrence_art78.py](../backend/tests/test_concurrence_art78.py) | 20 threads → 20 numéros contigus uniques |
| [tests/test_habilitations.py](../backend/tests/test_habilitations.py) | Rôles § 4.1, séparation stricte, monopole art. 82 |
| [tests/test_robustesse_transactionnelle.py](../backend/tests/test_robustesse_transactionnelle.py) | Rollback complet en cas de défaillance |
| [tests/test_admin_lecture_seule.py](../backend/tests/test_admin_lecture_seule.py) | Verrouillage admin y compris superuser |
| [tests/test_serializers_stricts.py](../backend/tests/test_serializers_stricts.py) | Rejet uniforme des clés inconnues |
| [tests/test_workflow.py](../backend/tests/test_workflow.py) | Matrice et interdictions disjointes ; immuabilité historique |
| [tests/test_modifications_cas_limites.py](../backend/tests/test_modifications_cas_limites.py) | Anti-contournement art. 88 |
| [tests/test_api_s5_audit.py](../backend/tests/test_api_s5_audit.py) | Accès API auditeur, refus non-auditeur, vérification chaîne HTTP |
| [tests/test_api_s6_conservation.py](../backend/tests/test_api_s6_conservation.py) | Désactivation logique, snapshots avant/après, immutabilité |

---

## 11. Supervision et exploitation

### 11.1 Sonde de santé

`GET /fr/sante/` ou `/ar/sante/` → JSON non divulguant de données
métier, exposant :
- état instance `"ok"`,
- langue résolue,
- carte des zones gelées actives.

### 11.2 Commandes d'exploitation

- `python manage.py migrate` — applique triggers + contraintes + tables.
- `python manage.py seed_referentiels` — charge les libellés bilingues officiels.
- `python manage.py expirer_inscriptions` — expiration + archivage quotidien (art. 92 al. 3).
- `python manage.py lister_arbitrages_mo` — registre des tests désactivés pour arbitrage MO.

### 11.3 Journaux techniques

- `logger = logging.getLogger(__name__)` dans les modules critiques.
- Les `warnings.warn` émis par les zones gelées (horodatage, scellement, certificats) sont visibles dans les sorties standard.
- Point d'arbitrage MO : politique de centralisation des logs (SIEM, syslog) — non câblé.

---

## 12. Conformité aux exigences § 5.1 du TDR

| Exigence § 5.1 | Dispositif |
|----------------|-----------|
| Authentification forte | ZONE GELÉE L11/MFA — interface `RSM_MFA_MODE` posée, session Django en STUB |
| Gestion fine des habilitations | Matrice centralisée `apps.utilisateurs.habilitations` |
| Séparation stricte des fonctions | `peut_valider_demande(acteur, saisie_par)` |
| Chiffrement des communications (TLS) | Configuration d'exploitation — à positionner au déploiement |
| Chiffrement au repos | Configuration PostgreSQL (TDE ou disques chiffrés) — arbitrage d'infrastructure |
| Protection OWASP | § 6 ci-dessus |
| Scellement cryptographique | ZONE GELÉE — cf. L3.3 |
| Horloge fiable et surveillée | ZONE GELÉE — cf. L3.3 |
| Gestion rigoureuse des comptes techniques | Traçabilité `AffectationRole` + admin `EditionRestreinteAdmin` |

---

## 13. Conformité aux exigences § 5.2 du TDR

| Exigence § 5.2 | Dispositif |
|----------------|-----------|
| Journal d'audit inaltérable | `EntreeAudit` append-only + triggers PostgreSQL + chaînage |
| Chaque entrée porte acteur, horodatage, objet, résultat | Champs obligatoires du modèle, peuplés par `tracer()` |
| Ruptures d'intégrité détectables | `verifier_chaine()` exposé par `/api/v1/audit/verification-chaine/` |
| Indépendance linguistique | Clés d'action stables (ex. `inscription.deposer`), `details` neutre |
| Accès lecture seule auditeur | Permission `_PermissionLectureAudit` ; Admin en `LectureSeuleAdmin` |

---

## 14. Renvois croisés

- Modèle de données : [L3.1](L3_1_modele_donnees.md).
- Architecture et flux : [L3.2](L3_2_architecture_modulaire.md).
- Horodatage et scellement : [L3.3](L3_3_horodatage_scellement.md).
- Dictionnaire API : [L3.4](L3_4_dictionnaire_api.md).
- Bilinguisme : [L3.6](L3_6_matrice_bilingue.md).
- Traçabilité article par article : [L11](L11_tracabilite_articles_76_97.md).
