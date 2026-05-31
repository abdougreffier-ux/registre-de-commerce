# L2.4 — Matrice rôles × opérations

**Livrable** : L2.4 — partie du livrable L2 (§ 8 du TDR).
**Objet** : matrice consolidée et opposable des habilitations.
**Fondement** : TDR § 4.1 (acteurs et rôles applicatifs) ; articles 79,
82, 83, 86, 88 ; § 5.1 (gestion des habilitations).
**État** : consolidation. **Aucune règle nouvelle.**

---

## 1. Les 7 rôles applicatifs (§ 4.1 TDR)

Liste **limitative** — cf.
[apps/utilisateurs/models.py::RoleApplicatif](../backend/apps/utilisateurs/models.py).

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Responsabilité (§ 4.1 TDR) |
|------------|---------------------|---------------------|----------------------------|
| `agent_saisie` | Agent de saisie (Greffe) | عون الإدخال (الكتابة) | Enregistre les bordereaux papier reçus au guichet ; contrôle de forme au sens de l'art. 80 ; transmet pour validation. |
| `autorite_validation` | Autorité de validation (Greffier) | سلطة المصادقة (كاتب الضبط) | Prononce l'inscription ou le rejet motivé ; déclenche le numéro d'ordre horodaté. |
| `admin_fonctionnel` | Administrateur fonctionnel | المسؤول الوظيفي | Gère utilisateurs, rôles, référentiels, modèles de certificats. **Jamais** d'accès à la modification directe des inscriptions. |
| `admin_technique` | Administrateur technique | المسؤول التقني | Exploitation (sauvegardes, supervision, correctifs). **Jamais** d'accès utile aux contenus métier. |
| `auditeur` | Auditeur / Contrôleur | المراقب | Lecture seule du journal d'audit et des données. Correspond au rôle du Président du Tribunal de commerce de Nouakchott ou du juge commis (art. 83). |
| `prod_stats` | Producteur de statistiques (Greffe) | منتج الإحصائيات (الكتابة) | Extrait et diffuse les statistiques conformément au **monopole art. 82**. |
| `declarant_externe` | Déclarant externe authentifié | المصرّح الخارجي الموثّق | Soumet par voie électronique ses demandes. |

**Rôle hors table** — **Usager public non authentifié** : effectue des
recherches dans le fichier public (art. 94 à 97) ; retire copies et
certificats. **Pas un rôle applicatif** au sens des affectations ; pas
de compte associé.

**Code** : les 7 rôles sont exposés par `RoleApplicatif.choices` et
attribuables via `AffectationRole`. Le détail du modèle est en
[L3.1 § 2.4](L3_1_modele_donnees.md).

---

## 2. Inventaire exhaustif des opérations

### 2.1 Opérations métier d'écriture

| Clé d'opération | Endpoint (cf. L3.4) | Article | Description fonctionnelle |
|-----------------|---------------------|:-------:|---------------------------|
| `inscription.deposer` | `POST /api/v1/inscriptions/` | 78, 85 | Créer une demande d'inscription initiale |
| `inscription.valider` | `POST /api/v1/inscriptions/<uuid>/valider/` | 78, 85, 87 | Attribuer le numéro d'ordre et publier au fichier public |
| `inscription.rejeter` | `POST /api/v1/inscriptions/<uuid>/rejeter/` | 80 | Prononcer un rejet motivé (3 motifs limitatifs) |
| `modification.creer` | `POST /api/v1/modifications/` | 88 | Soumettre une demande de modification |
| `modification.appliquer` | `POST /api/v1/modifications/<id>/appliquer/` | 88, 90 | Appliquer une modification (contrôle état final art. 88 al. 4) |
| `renouvellement.creer` | `POST /api/v1/renouvellements/` | 91 | Soumettre une demande de renouvellement |
| `renouvellement.appliquer` | `POST /api/v1/renouvellements/<id>/appliquer/` | 91 | Proroger la période d'effet (avant expiration) |
| `radiation.creer` | `POST /api/v1/radiations/` | 92 | Soumettre une demande de radiation |
| `radiation.appliquer` | `POST /api/v1/radiations/<id>/appliquer/` | 92 | Activer la mention « radiée » au fichier public |

### 2.2 Opérations métier de lecture

| Clé d'opération | Endpoint | Article |
|-----------------|----------|:-------:|
| `inscription.consulter` | `GET /api/v1/inscriptions/<uuid>/` | — |
| `inscription.lister` | `GET /api/v1/inscriptions/` | 77, 93 |
| `rejets.lister` | `GET /api/v1/rejets/` | 80 |
| `modification.consulter` | `GET /api/v1/modifications/` | 88 |
| `renouvellement.consulter` | `GET /api/v1/renouvellements/` | 91 |
| `radiation.consulter` | `GET /api/v1/radiations/` | 92 |
| `certificats.consulter` | `GET /api/v1/certificats/` | 78, 97 |
| `snapshots.consulter` | Admin Django + API à venir | 79 |

### 2.3 Opérations publiques (art. 94)

| Clé d'opération | Endpoint | Article |
|-----------------|----------|:-------:|
| `recherche.lancer` | `POST /api/v1/recherche/` | 94, 96, 97 |
| `referentiels.consulter` | `GET /api/v1/referentiels/*` | 76, 78, 80, 96 |
| `accueil.consulter` | `GET /{fr,ar}/` | — |
| `sante.consulter` | `GET /{fr,ar}/sante/` | § 5.3 |

### 2.4 Opérations d'administration métier

| Clé d'opération | Endpoint / chemin | Article |
|-----------------|-------------------|:-------:|
| `utilisateur.creer` / `utilisateur.modifier` | Admin Django (§ 4.1) | § 4.1 |
| `affectation_role.creer` / `modifier` | Admin Django (`EditionRestreinteAdmin`) | § 4.1, § 5.2 |
| `referentiels.editer` | Admin Django (`EditionRestreinteAdmin`) | § 4.1, § 7.3 |
| `parametres.editer` | Admin Django (à venir) | — |

### 2.5 Opérations statistiques (art. 82)

| Clé d'opération | Endpoint | Article |
|-----------------|----------|:-------:|
| `statistiques.lister` | `GET /api/v1/statistiques/` | 82 |
| `statistiques.produire` | `POST /api/v1/statistiques/produire/` | 82 (monopole) |

### 2.6 Opérations d'audit (§ 5.2)

| Clé d'opération | Endpoint | Article |
|-----------------|----------|:-------:|
| `audit.consulter_entrees` | `GET /api/v1/audit/entrees/` | 79, § 5.2 |
| `audit.verifier_chaine` | `GET /api/v1/audit/verification-chaine/` | 79, § 5.2 |

### 2.7 Opérations système (automatiques)

| Clé d'opération | Déclencheur | Article |
|-----------------|-------------|:-------:|
| `expiration.auto` | `python manage.py expirer_inscriptions` | 85, 92 al. 3 |
| `seed.referentiels` | `python manage.py seed_referentiels` | — |
| `audit.ecrire` | Appels implicites `tracer()` | § 5.2 |
| `snapshot.produire` | Appels internes des services | 79 |

---

## 3. Matrice rôles × opérations

**Légende** :
- ✅ **Autorisé** (sans condition particulière)
- 🔹 **Autorisé sous condition** (séparation stricte ou rôle spécifique)
- ❌ **Refusé** explicitement
- 🌐 **Public** (aucun rôle requis — art. 94)
- ⚙️ **Système** (acteur `null`, opération automatique)

### 3.1 Opérations métier d'écriture

| Opération | Agent saisie | Autorité validation | Admin fonct. | Admin tech. | Auditeur | Prod. stats | Déclarant externe | Public | Article fondateur |
|-----------|:------------:|:-------------------:|:------------:|:-----------:|:--------:|:-----------:|:-----------------:|:------:|:-----------------:|
| `inscription.deposer` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | art. 85 |
| `inscription.valider` | ❌ | 🔹 (1) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | art. 87 |
| `inscription.rejeter` | ❌ | 🔹 (1) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | art. 80 |
| `modification.creer` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | art. 88 |
| `modification.appliquer` | ❌ | 🔹 (1) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | art. 88, 90 |
| `renouvellement.creer` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | art. 91 |
| `renouvellement.appliquer` | ❌ | 🔹 (1) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | art. 91 |
| `radiation.creer` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | art. 92 |
| `radiation.appliquer` | ❌ | 🔹 (1) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | art. 92 |

**Condition (1) — séparation stricte § 4.1** : l'acteur qui applique
(valider, rejeter, modification/renouvellement/radiation `appliquer`)
**ne doit pas être le créateur de la demande**. Le contrôle repose sur
`peut_valider_demande(acteur, saisie_par)` — cf. L3.5 § 4.3.

### 3.2 Opérations métier de lecture

| Opération | Agent saisie | Autorité validation | Admin fonct. | Admin tech. | Auditeur | Prod. stats | Déclarant externe | Public |
|-----------|:------------:|:-------------------:|:------------:|:-----------:|:--------:|:-----------:|:-----------------:|:------:|
| `inscription.consulter` | ✅ | ✅ | ✅ (lecture) | ✅ (lecture) | ✅ | ✅ | 🔹 (2) | ❌ |
| `inscription.lister` | ✅ | ✅ | ✅ (lecture) | ✅ (lecture) | ✅ | ✅ | 🔹 (2) | ❌ |
| `rejets.lister` | ✅ | ✅ | ✅ (lecture) | ❌ | ✅ | ✅ | ❌ | ❌ |
| `modification.consulter` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | 🔹 (2) | ❌ |
| `renouvellement.consulter` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | 🔹 (2) | ❌ |
| `radiation.consulter` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | 🔹 (2) | ❌ |
| `certificats.consulter` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | 🔹 (2) | ❌ |
| `snapshots.consulter` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

**Condition (2)** : le déclarant externe ne consulte que les demandes
dont il est l'auteur. (Filtrage applicatif à câbler lors de
l'activation du portail externe — zone `L11/MFA` + arbitrage du
périmètre d'accès — DOCUMENTÉ SANS IMPLÉMENTATION à ce stade.)

### 3.3 Opérations publiques (art. 94)

| Opération | Tout acteur | Public |
|-----------|:-----------:|:------:|
| `recherche.lancer` | 🌐 | 🌐 |
| `referentiels.consulter` | 🌐 | 🌐 |
| `accueil.consulter` | 🌐 | 🌐 |
| `sante.consulter` | 🌐 | 🌐 |

Aucun rôle requis. Conformément à l'article 94, la recherche est
ouverte « à tout intéressé ».

### 3.4 Opérations d'administration métier

| Opération | Admin fonct. | Admin tech. | Autres rôles | Public |
|-----------|:------------:|:-----------:|:------------:|:------:|
| `utilisateur.creer` | ✅ | ❌ | ❌ | ❌ |
| `utilisateur.modifier` (hors désactivation) | ✅ | ❌ | ❌ | ❌ |
| `utilisateur.supprimer` | ❌ | ❌ | ❌ | ❌ |
| `affectation_role.creer` | ✅ | ❌ | ❌ | ❌ |
| `affectation_role.modifier` (désactivation) | ✅ | ❌ | ❌ | ❌ |
| `affectation_role.supprimer` | ❌ | ❌ | ❌ | ❌ |
| `referentiels.editer` (libellés) | ✅ | ❌ | ❌ | ❌ |
| `referentiels.ajouter_cle` | ❌ | ❌ | ❌ | ❌ |
| `referentiels.supprimer` | ❌ | ❌ | ❌ | ❌ |
| `parametres.editer` (à venir) | ✅ | ❌ | ❌ | ❌ |

**Règle cardinale § 4.1** : aucun administrateur (fonctionnel ou
technique) n'a de chemin d'écriture vers les contenus métier
(inscriptions, biens, parties, demandes M/R/Rad). Garanti par :
- Classes `ConsultationMetierAdmin` (L3.2 § 6) ;
- `ecriture_metier_autorisee(acteur)` qui renvoie `False` pour les
  administrateurs.

**Règle art. 79** : aucune suppression d'utilisateur ni d'affectation
de rôle. Désactivation uniquement via `compte_actif=False` /
`actif=False`.

### 3.5 Opérations statistiques (art. 82)

| Opération | Agent saisie | Autorité validation | Admin fonct. | Admin tech. | Auditeur | **Prod. stats** | Déclarant externe | Public |
|-----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `statistiques.lister` | ❌ | ❌ | ❌ | ❌ | ✅ (lecture audit) | ✅ | ❌ | ❌ |
| `statistiques.produire` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (monopole art. 82) | ❌ | ❌ |

**Règle cardinale art. 82** : seul le rôle `prod_stats` peut produire
des extractions statistiques. Monopole du greffe. Toute autre
tentative → `AutorisationRefusee` → HTTP 403.

### 3.6 Opérations d'audit (§ 5.2)

| Opération | **Auditeur** | Autres rôles | Public |
|-----------|:-:|:-:|:-:|
| `audit.consulter_entrees` | ✅ | ❌ | ❌ |
| `audit.verifier_chaine` | ✅ | ❌ | ❌ |

**Règle** : l'auditeur dispose d'un accès **strictement en lecture**
au journal d'audit. Toute écriture est refusée par :
- les overrides `save()` / `delete()` (L3.5 § 3.1) ;
- les triggers PostgreSQL (L3.5 § 2.1) ;
- les classes admin `LectureSeuleAdmin` (L3.2 § 6).

### 3.7 Opérations système

| Opération | Déclencheur | Acteur |
|-----------|-------------|--------|
| `expiration.auto` | Cron quotidien | ⚙️ `null` |
| `seed.referentiels` | Commande admin | ⚙️ admin exécutant |
| `audit.ecrire` | Implicite (tracer) | ⚙️ `null` ou acteur courant |
| `snapshot.produire` | Implicite (services de modification) | Acteur de la modification |

---

## 4. Règles de séparation et de non-cumul

### 4.1 Séparation stricte saisie / validation (§ 4.1 TDR — règle cardinale)

**Règle** :
> *« Aucun utilisateur ne peut cumuler les rôles d'agent de saisie et
>   d'autorité de validation sur la même demande. »*

**Portée** :
- La règle opère **au niveau de la demande**, PAS au niveau du compte.
- Un même utilisateur peut théoriquement détenir `agent_saisie` ET
  `autorite_validation` (pour la polyvalence opérationnelle), mais :
  - il pourra déposer OU valider, **pas les deux sur la même demande**.
- Vérification : `peut_valider_demande(acteur, saisie_par)` compare
  `saisie_par.pk` et `acteur.pk`.

**Applications** : toutes les opérations marquées 🔹 (1) dans le § 3.1
(validation, rejet, application M/R/Rad).

**Tests** : [test_habilitations.py::SeparationStricteTests](../backend/tests/test_habilitations.py) ;
[test_api_d1_separation_stricte.py](../backend/tests/test_api_d1_separation_stricte.py)
(4 classes HTTP couvrant les 4 opérations soumises à la règle).

### 4.2 Cumul interdit administrateur + écriture métier

**Règle** (§ 4.1 TDR) :
> *« Aucun administrateur, fonctionnel ou technique, n'a le pouvoir de
>   créer, modifier ou supprimer une inscription dans le fichier du
>   Registre. »*

**Portée** : les rôles `admin_fonctionnel` et `admin_technique` ne
peuvent **jamais** exercer d'opération d'écriture métier. Le fait
qu'un administrateur détienne également un autre rôle est permis,
mais ses actes d'écriture métier passent alors **sous ce second
rôle**, jamais sous le rôle administratif.

**Mise en œuvre** :
- `ecriture_metier_autorisee(acteur)` renvoie `False` si l'acteur
  détient un rôle ∈ `ROLES_ADMINISTRATION = {admin_fonctionnel, admin_technique}`
  **sans** détenir également un rôle écriture métier.
- Classes admin `ConsultationMetierAdmin` pour les entités métier.

### 4.3 Monopole art. 82

**Règle** : seul le rôle `prod_stats` produit des extractions
statistiques. Toute autre tentative → `AutorisationRefusee`.

### 4.4 Règle d'abstention de l'auditeur

L'auditeur **ne peut exercer aucune opération d'écriture**, même sur
les référentiels ou les affectations de rôle. Son rôle est strictement
circonscrit au contrôle (art. 83 — contrôle du Président du Tribunal
ou du juge commis).

### 4.5 Verrou architectural global

Même un compte `is_superuser=True` Django :
- ne peut pas modifier / supprimer une entrée d'audit (triggers SQL) ;
- ne peut pas modifier / supprimer une inscription via l'admin
  (classes `ConsultationMetierAdmin`) ;
- ne peut pas contourner la règle 🔹 (1) si elle s'applique
  (les services vérifient `peut_valider_demande` indépendamment du
  `is_superuser`).

Cf. L3.5 pour les 4 remparts de défense en profondeur.

---

## 5. Schéma de décision d'autorisation

Pour chaque opération métier, le schéma de décision est :

```
                  Requête HTTP authentifiée
                           │
                           ▼
            ┌──────────────────────────────┐
            │ 1. Permission DRF ?          │
            │    (IsAuthenticated,         │
            │     AllowAny public, etc.)   │
            └───────────┬──────────────────┘
                        │ ok
                        ▼
            ┌──────────────────────────────┐
            │ 2. Serializer strict ?       │
            │    (clés inconnues refusées) │
            └───────────┬──────────────────┘
                        │ ok
                        ▼
            ┌──────────────────────────────┐
            │ 3. Rôle applicatif ?         │
            │    (peut_enregistrer_demande │
            │     peut_valider_demande     │
            │     peut_lire_audit          │
            │     peut_produire_stats)     │
            └───────────┬──────────────────┘
                        │ ok
                        ▼
            ┌──────────────────────────────┐
            │ 4. Séparation stricte ?      │
            │    (acteur ≠ saisie_par si   │
            │    opération de validation)  │
            └───────────┬──────────────────┘
                        │ ok
                        ▼
            ┌──────────────────────────────┐
            │ 5. Règles métier (art. 80,   │
            │    85, 88, 91, 92, 96)       │
            └───────────┬──────────────────┘
                        │ ok
                        ▼
                   Exécution service
```

Toute étape refusée produit l'exception HTTP correspondante :

| Étape | Exception | HTTP |
|-------|-----------|:----:|
| 1 | `NotAuthenticated` | 401 |
| 2 | `ValidationError` | 400 |
| 3 | `AutorisationRefusee` | 403 |
| 4 | `AutorisationRefusee` | 403 |
| 5 | `RejetForme` / `ModificationSansEffet` / `RenouvellementHorsDelai` / `RechercheCriteresInsuffisants` / `TransitionInterdite` | 400 |

---

## 6. Couverture par les tests

| Règle | Tests de référence |
|-------|---------------------|
| Matrice rôles × opérations (service) | [tests/test_habilitations.py](../backend/tests/test_habilitations.py) |
| Séparation stricte (HTTP) | [tests/test_api_d1_separation_stricte.py](../backend/tests/test_api_d1_separation_stricte.py) |
| Monopole art. 82 | [tests/test_habilitations.py::test_monopole_statistiques](../backend/tests/test_habilitations.py) |
| Pas d'écriture métier pour admin | [tests/test_habilitations.py::HabilitationsParRoleTests](../backend/tests/test_habilitations.py) |
| Admin Django verrouillée | [tests/test_admin_lecture_seule.py](../backend/tests/test_admin_lecture_seule.py) |
| Accès audit limité à l'auditeur | [tests/test_api_s5_audit.py](../backend/tests/test_api_s5_audit.py) |
| Recherche publique sans auth | [tests/test_api_s4_recherche_coherence.py::test_recherche_deux_criteres_ouverte_sans_auth](../backend/tests/test_api_s4_recherche_coherence.py) |

---

## 7. Zones gelées applicables aux habilitations

| Zone | Impact sur les habilitations |
|------|------------------------------|
| `L11/MFA` | Authentification forte non câblée ; mise en œuvre actuelle : session Django. Affecte les endpoints d'écriture (pas d'impact sur la matrice rôles/opérations). |
| Placeholder auditeur | `_PermissionLectureAudit` contrôle actuellement `is_staff` (développement). À remplacer par vérification du rôle `auditeur` lors de l'activation complète de la matrice. |

---

## 8. Cohérence bilingue

Les 7 rôles sont stockés par **clé neutre** dans `AffectationRole.role`
et dans toutes les entrées d'audit. Les libellés FR/AR sont :
- issus de `RoleApplicatif.choices` (Django i18n natif) ;
- marqués **amorce** tant que le glossaire § 7.3 n'est pas validé
  (zone `L11/A6`).

Aucune décision d'autorisation ne dépend de la langue. Cf. L3.6 et le
test [tests/test_api_d3_accept_language.py](../backend/tests/test_api_d3_accept_language.py)
qui démontre l'équivalence juridique FR/AR.

---

## 9. Renvois croisés

- Formulaires : [L2.1](L2_1_formulaires_bilingues.md).
- Règles de validation : [L2.2](L2_2_regles_validation.md).
- Statuts × transitions × messages : [L2.3](L2_3_matrice_statuts_transitions.md).
- Cartographie des messages système : [L2.5](L2_5_messages_systeme.md).
- Scénarios fonctionnels : [L2.6](L2_6_scenarios_fonctionnels.md).
- Modèle `RoleApplicatif` / `AffectationRole` : [L3.1 § 2.4](L3_1_modele_donnees.md).
- Matrice admin Django : [L11](L11_tracabilite_articles_76_97.md).
- Défense en profondeur : [L3.5](L3_5_securite_integrite.md).
