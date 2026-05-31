# L8 — Note d'architecture technique et de déploiement

**Système du Registre des Sûretés Mobilières (RSM)**

*Document officiel à destination du prestataire d'hébergement, de
déploiement et d'exploitation. À jour de l'état du système. Aucun
extrait de code source ni élément confidentiel n'y figure.*

---

## 1. Présentation générale du système

### 1.1 Objectif

Le Registre des Sûretés Mobilières (RSM) est l'outil informatique de
mise en œuvre du chapitre IV — articles 76 à 97 — du décret 2021-033
relatif au Registre du commerce et des sûretés mobilières. Sa
finalité est triple :

1. **Publicité** des sûretés mobilières et opposabilité aux tiers
   (art. 76).
2. **Conservation** intégrale des informations régulièrement
   enregistrées, sans suppression possible (art. 79).
3. **Délivrance** de certificats à valeur probante en regard de
   l'article 97.

Le système est entièrement informatisé conformément à l'article 77.

### 1.2 Rôle du registre dans l'écosystème RCCM / Greffe

Le RSM se distingue institutionnellement du RCCM (Registre du
commerce et du crédit mobilier) tout en étant rattaché au même Greffe
du Tribunal de commerce de Nouakchott. Le RCCM identifie les
commerçants et les sociétés ; le RSM publie les sûretés grevant des
biens mobiliers, qu'ils appartiennent à un commerçant inscrit ou à
toute autre personne. Les deux systèmes sont indépendants
techniquement mais peuvent être interconnectés à terme (cf. fiche MO
F13).

### 1.3 Acteurs

Sept rôles applicatifs limitatifs (TDR § 4.1), plus l'usager public
anonyme :

| Rôle | Rôle métier | Permission métier principale |
|---|---|---|
| `agent_saisie` | Agent de saisie au guichet | Enregistrer une demande |
| `autorite_validation` | Greffier | Valider ou rejeter une demande (art. 80, 86) |
| `declarant_externe` | Personne agréée pour le portail externe | Déposer en ligne (art. 78, 81, 84) |
| `auditeur` | Contrôleur / juge commis (art. 83) | Lecture seule du journal d'audit |
| `prod_stats` | Producteur de statistiques | Extractions monopole greffe (art. 82) |
| `admin_fonctionnel` | Administrateur fonctionnel | Référentiels, comptes, rôles ; **aucun accès écriture métier** |
| `admin_technique` | Administrateur technique | Exploitation système ; **aucun accès utile aux contenus** |
| Usager public | Anonyme | Recherche publique art. 94-97, sans authentification |

Règle de séparation stricte : un même utilisateur ne peut pas cumuler
`agent_saisie` et `autorite_validation` sur la même demande.

### 1.4 Environnements

Deux environnements logiques distincts, pilotés par la variable
`RSM_MODE_TEST` :

| Environnement | `RSM_MODE_TEST` | Vocation |
|---|---|---|
| **TEST / RECETTE** | `true` | Recette fonctionnelle, formation, démonstrations. Bandeau permanent « MODE TEST — AUCUNE VALEUR JURIDIQUE ». |
| **PRODUCTION** | `false` | Régime opérationnel opposable. Bandeau masqué, règles de sécurité durcies. |

Toute donnée produite en TEST porte cette mention et n'a aucune
valeur juridique.

---

## 2. Architecture globale

### 2.1 Vue d'ensemble

Architecture trois-tiers classique, sans couplage fort entre les
couches :

```
   ┌────────────────────────────────────────┐
   │  Navigateur (poste agent / usager)     │
   │                                        │
   │  → Interface React (SPA)               │
   └───────────────┬────────────────────────┘
                   │ HTTPS — JSON sur HTTP/1.1
                   │ Cookie session + (CSRF en production)
                   ▼
   ┌────────────────────────────────────────┐
   │  Reverse proxy (recommandé : nginx)    │
   │  - terminaison TLS                     │
   │  - en-têtes de sécurité                │
   │  - répartition statique / dynamique    │
   └───────────┬───────────────────┬────────┘
               │                   │
       statique│           dynamique│
               ▼                   ▼
   ┌──────────────────┐    ┌──────────────────────┐
   │  Static / CDN    │    │  Application Django  │
   │  (build React)   │    │  + DRF (API JSON)    │
   └──────────────────┘    └────────┬─────────────┘
                                    │
                                    ▼
                           ┌────────────────────┐
                           │  PostgreSQL 14+    │
                           │  (prod : 16 ou 18) │
                           │  - tables métier   │
                           │  - triggers audit  │
                           │  - index FR/AR     │
                           └────────────────────┘
```

### 2.2 Séparation des responsabilités

| Couche | Responsabilité | Ne fait pas |
|---|---|---|
| **Frontend SPA** | Présentation, navigation, formulaires dynamiques, validation ergonomique | Aucune règle métier, aucune autorisation autoritative |
| **API REST (Django + DRF)** | Règles métier, autorisations, validations strictes, audit, transactions | Aucun rendu HTML métier (sauf admin Django, lecture seule) |
| **Base de données (PostgreSQL)** | Persistance, contraintes d'intégrité, triggers append-only | Aucune logique applicative au-delà des contraintes |

Cette séparation garantit que :
- la règle métier autoritative est centralisée côté serveur ;
- le frontend peut être remplacé sans réécrire les règles ;
- l'auditeur consulte les données via une vue lecture seule sans
  passer par l'application.

### 2.3 Flux principaux

**Connexion** : `POST /api/v1/auth/login/` → cookie de session Django,
vérifiable via `GET /api/v1/auth/whoami/`.

**Dépôt d'inscription (art. 85)** :
1. Authentification (`declarant_externe` ou `agent_saisie`).
2. `POST /api/v1/inscriptions/` avec les 6 champs scalaires (canal,
   nature, somme, monnaie, durée, e-mail).
3. Service `creer_demande()` : création, transition automatique
   `RECUE → EN_CONTROLE_FORME`, écriture du journal d'audit.

**Validation par le greffier** :
1. Authentification (`autorite_validation`, distinct du saisisseur).
2. `POST /api/v1/inscriptions/<ref>/valider/`.
3. Service `valider_inscription()` : attribution du numéro d'ordre
   horodaté (art. 78 al. 4), calcul de la date d'expiration,
   transition vers `INSCRITE`, écriture d'audit.

**Consultation publique** : `POST /api/v1/recherche/` avec deux
critères au moins parmi les quatre énumérés à l'article 96 ; aucune
authentification requise (art. 94).

Toute autre opération (modification, renouvellement, radiation) suit
la même structure : dépôt → file de contrôle de forme → décision du
greffier → transition → audit.

---

## 3. Stack technique détaillée

### 3.1 Frontend

| Technologie | Rôle | Justification |
|---|---|---|
| **React 18** | Bibliothèque UI déclarative | Standard de l'industrie, large communauté, rendu prévisible, isolation des erreurs (ErrorBoundary). |
| **react-router-dom 6** | Routage côté client | Permet une SPA sans rechargement complet ; cohérent avec un dépôt de formulaire à étapes. |
| **Ant Design 5** | Système de composants UI | Bibliothèque mature avec support natif RTL (arabe), formulaires complexes, accessibilité par défaut. |
| **i18next** | Internationalisation FR/AR | Architecture clé/valeur identique en FR et AR, garantie de parité (TDR § 7). |
| **Axios** | Client HTTP | Intercepteurs (langue, CSRF, formatage des erreurs métier). |
| **dayjs** | Manipulation de dates | Léger, fuseau horaire Africa/Nouakchott. |

Build : `react-scripts` (Create React App). En production, le bundle
est généré une fois (`npm run build`) puis servi statiquement.

### 3.2 Backend

| Technologie | Rôle | Justification |
|---|---|---|
| **Python 3.12** | Runtime | Long-term support, performance, larges bibliothèques juridiques disponibles. |
| **Django 4.2 LTS** | Framework web | Maturité, ORM robuste, admin auto-générée pour la lecture seule, écosystème complet. |
| **Django REST Framework** | Couche API | Sérialisation stricte, classes de permissions composables, gestion native de l'authentification de session. |
| **django-decouple** | Configuration via .env | Sépare proprement les secrets du code. |
| **django-filter** | Filtrage paginé | Recherche avec critères multiples sans réinventer un parseur. |
| **django-cors-headers** | Politique CORS | Maîtrise fine des origines autorisées en production. |
| **whitenoise** | Service des fichiers statiques | Permet à Django de servir les statiques sans dépendre d'un nginx tiers en environnement contraint. |
| **pillow** | Traitement image (sceau, logo) | Standard. |

### 3.3 Base de données

**PostgreSQL 14+** (testé sur PostgreSQL 18, recommandé en production
PostgreSQL 16 LTS). Choix justifié :

- **Triggers** SQL utilisés pour matérialiser le caractère
  append-only du journal d'audit (article 79) — interdit toute
  mise à jour ou suppression directement au niveau du moteur.
- **Index full-text** capables de gérer simultanément le français et
  l'arabe (extension `pg_trgm` recommandée).
- **Transactions ACID** strictes, indispensables pour l'attribution
  séquentielle du numéro d'ordre (art. 78 al. 4).
- **JSONB** pour les schémas dynamiques (catégories de biens,
  attributs spécifiques) avec indexation possible.
- **Contraintes** d'unicité partielles (ex. une seule version active
  par catégorie de bien, séparation stricte des rôles).

### 3.4 Frameworks et bibliothèques accessoires

- **Tests backend** : `unittest` + `django.test.TestCase` (150 tests
  applicatifs au moment de la rédaction).
- **Migrations** : Django migrations classiques + migrations de
  données pour le seed des référentiels (catégories de biens,
  natures de droits).
- **Validation des mots de passe** : `AUTH_PASSWORD_VALIDATORS`
  Django (longueur, similarité avec l'identifiant, mots de passe
  communs, contenu numérique).

---

## 4. Gestion des utilisateurs et des rôles

### 4.1 Typologie des comptes

| Origine | Création | Cycle de vie |
|---|---|---|
| Administrateur fonctionnel | Création par `admin_technique` (premier compte par `createsuperuser`) | Mot de passe initial obligatoire à changer |
| Comptes greffe | Création par `admin_fonctionnel` | Idem ; affectation des rôles via l'interface d'administration |
| Déclarants externes | Création par `admin_fonctionnel` après agrément | Idem ; cible production avec MFA (cf. fiche F2) |
| Auditeur | Création par `admin_fonctionnel` ; en lecture seule | Compte révocable mais traces conservées |

### 4.2 Rôles applicatifs et séparation des responsabilités

Les rôles sont matérialisés par la table `AffectationRole` qui lie un
utilisateur à un rôle parmi la liste limitative des sept rôles. Une
contrainte applicative refuse explicitement le cumul des rôles
incompatibles (`agent_saisie` + `autorite_validation`).

Chaque endpoint API protégé applique une vérification de rôle. Les
administrateurs (fonctionnel et technique) **n'ont jamais accès en
écriture** aux entités métier (inscription, modification, radiation,
renouvellement) : leurs permissions sont restreintes à
l'administration des comptes, des référentiels et de l'exploitation.

### 4.3 Authentification et sessions

L'authentification repose sur la session Django (cookie
`sessionid`), gérée par DRF via `SessionAuthentication`. Le cookie
est marqué `HttpOnly` et `SameSite=Lax`. Le jeton CSRF (`csrftoken`)
est posé automatiquement par l'endpoint `whoami` au premier appel ; en
mode TEST, l'enforcement CSRF est désactivé pour faciliter la recette
avec proxy de développement, mais la session reste exigée.

Endpoints d'authentification :

| Méthode | URL | Rôle |
|---|---|---|
| GET | `/api/v1/auth/whoami/` | État courant + cookie csrf |
| POST | `/api/v1/auth/login/` | Connexion |
| POST | `/api/v1/auth/logout/` | Déconnexion |
| POST | `/api/v1/auth/changer-mot-de-passe/` | Changement autonome du mot de passe |

### 4.4 Gestion des mots de passe

| Aspect | Mode TEST | Cible production |
|---|---|---|
| Mot de passe initial | Fixé par l'administrateur | Idem |
| Drapeau de changement obligatoire | `mot_de_passe_initial = true` à la création | Idem |
| Garde de redirection | Frontend redirige systématiquement vers la page de changement tant que le drapeau est posé | Idem + permission backend (cf. F2) |
| Validateurs | Validateurs Django par défaut | À renforcer (longueur ≥ 12, complexité, historique) |
| MFA | Désactivé (`RSM_MFA_MODE=disabled`) | À activer après transmission des paramètres F2 |
| Stockage | Hashage Django (PBKDF2-SHA256 par défaut) | Idem ou Argon2 |

Aucune entrée d'audit métier (art. 79) n'est produite par le
changement de mot de passe : il s'agit d'une opération technique.

---

## 5. Workflow métier RCCM / Sûretés mobilières

### 5.1 Statuts d'inscription

Liste limitative, alignée sur § 4.3 du TDR :

| Code | Sens | Visibilité tiers |
|---|---|---|
| `recue` | Demande enregistrée, prise en charge en cours | Non (transitoire) |
| `en_controle_forme` | En attente de décision du greffier | Oui (interne) |
| `rejetee` | Décision motivée art. 80 | Oui |
| `inscrite` | Sûreté en cours de validité, publiée au fichier public | Oui (recherche art. 94) |
| `modifiee` | Une modification (art. 88) a été appliquée | Oui |
| `renouvelee` | Période d'effet prorogée (art. 91) | Oui |
| `radiee` | Radiation enregistrée (art. 92) | Oui (mention « radiée ») |
| `expiree` | Date d'expiration atteinte | Non (sortie du fichier public) |
| `archivee` | Transférée au fichier général (art. 79) | Non |

### 5.2 Dépôt d'inscription (art. 85)

Champs strictement acceptés à la création : canal, nature, somme,
monnaie, durée, e-mail. La saisie des parties et des biens grevés
relève de la modification (art. 88) ; aucune autre clé n'est
acceptée par le serializer.

Conformément à l'article 86, le greffier ne vérifie pas l'identité
du déposant ni les énonciations contenues : seul le respect des
motifs limitatifs de rejet (art. 80) est contrôlé.

### 5.3 Validation / rejet

| Action | Effet |
|---|---|
| **Validation** | Attribution du numéro d'ordre `NNNNNN-AAAAMMJJHHMMSS` (art. 78 al. 4), calcul de la date d'expiration, transition vers `INSCRITE`, journal d'audit |
| **Rejet** | Sélection d'un motif limitatif (`canal_non_autorise`, `informations_illisibles`, `informations_incomprehensibles`), commentaires FR et AR optionnels, transition vers `REJETEE` |

### 5.4 Modification (art. 88)

Une demande de modification porte un différentiel structuré
(`diff_propose`) avec trois clés autorisées : `parties`, `biens`,
`scalaires`. Toute clé hors schéma est rejetée. Le service
d'application contrôle automatiquement les motifs limitatifs de refus
(art. 88 dernier alinéa) : un état final vidant les constituants,
les créanciers garantis ou les biens sans en désigner de nouveaux est
sans effet.

### 5.5 Renouvellement (art. 91)

Une demande de renouvellement n'est recevable que si l'inscription
est encore en cours de validité. La période est prorogée d'une durée
égale à la durée initiale (interprétation TDR § 9.3).

### 5.6 Radiation (art. 92)

Trois fondements limitatifs : consentement, jugement, requérant
original. L'inscription radiée demeure au fichier public avec la
mention « radiée » jusqu'à la date d'expiration, puis bascule au
fichier général.

### 5.7 Catégories de biens (référentiel versionné)

Le référentiel comporte 18 catégories (véhicules, matériel
professionnel, stocks et marchandises, etc.) avec, pour chacune, un
schéma de champs propres (libellés FR et AR, type, caractère
obligatoire). Le référentiel est :

- **versionné** : chaque modification crée une nouvelle version ;
- **non rétroactif** : les biens déjà déposés conservent la version
  utilisée à la saisie ;
- **verrouillé** : une version utilisée par au moins un bien grevé
  devient immuable, toute évolution passe par la publication d'une
  nouvelle version ;
- **administré** par les rôles `autorite_validation` et
  `admin_fonctionnel` via une interface dédiée (`/admin/categories-biens`).

### 5.8 Traçabilité

Toute action métier produit une entrée dans le journal d'audit
(`apps.audit.models.EntreeAudit`) avec : instant, acteur, rôle,
objet (référence d'inscription), action, résultat, contexte et
chaînage par hachage cryptographique. La table est protégée à deux
niveaux :

1. Application : la méthode `save` lève `PermissionError` si
   `pk is not None` (interdiction de mise à jour) et la méthode
   `delete` est interdite.
2. Base de données : un trigger PostgreSQL (`rsm_audit_pas_update`,
   `rsm_audit_pas_delete`) refuse toute opération `UPDATE` ou
   `DELETE` sur la table d'audit, indépendamment du chemin
   applicatif.

---

## 6. Génération de documents officiels

### 6.1 Types de documents prévus

| Document | Article | Moment de génération |
|---|---|---|
| Certificat d'inscription | Art. 78 al. 3, 86 | Après validation par le greffier |
| Certificat de modification | Art. 88-90 | Après application d'une modification |
| Certificat de renouvellement | Art. 91 | Après application d'un renouvellement |
| Certificat de radiation | Art. 92 | Après application d'une radiation |
| Certificat de recherche | Art. 97 | À l'issue de chaque recherche art. 94-96 |

### 6.2 Données utilisées

Les certificats puisent leurs données dans la table `Certificat` qui
porte une description structurée bilingue. Les libellés sont produits
à partir des référentiels versionnés (catégories de biens, natures de
droits, motifs de rejet) afin que le contenu reste reproductible et
cohérent dans la durée.

### 6.3 Documents de test vs documents probants

| Aspect | Mode TEST | Cible production |
|---|---|---|
| Drapeau `Certificat.probant` | Toujours `False` | `True` après scellement |
| Mention obligatoire | « TEST / NON OPPOSABLE » à imprimer en gros caractères | Aucune mention de test |
| Horodatage | Horloge locale (`local_stub`) | Horodatage opposable via TSA RFC 3161 (fiche F5) |
| Scellement | SHA-256 simple (informatif) | Scellement signé via PKI (fiche F6) |
| Charte graphique | Charte officielle RIM appliquée | Idem + sceau et polices officielles déposés |

### 6.4 Préparation à la production probante

Quatre fiches MO conditionnent l'émission probante :

- **F4** : modèles PDF/A bilingues approuvés et charte documentaire
- **F5** : source de temps officielle désignée
- **F6** : algorithmes de scellement et politique de gestion des clés
- **F1** : glossaire juridique bilingue validé

Tant que ces paramètres ne sont pas communiqués par le maître
d'ouvrage, le système reste en mode `disabled` pour les volets
correspondants. Aucun mécanisme par défaut n'est inventé.

---

## 7. Sécurité et intégrité

### 7.1 Principes de sécurité globaux

- **Authentification obligatoire** pour toute opération métier
  (`IsAuthenticated` par défaut côté API).
- **Recherche publique anonyme** autorisée uniquement pour
  l'endpoint `/recherche/`, conformément à l'article 94.
- **Permissions par rôle** vérifiées dans les services métier (et
  pas seulement aux frontières HTTP).
- **Sérialisation stricte** : toute clé inattendue dans un payload
  est rejetée (StrictInputSerializer).
- **Validation côté serveur** autoritative ; la validation côté
  frontend est purement ergonomique.

### 7.2 CSRF / CORS / sessions

| Mécanisme | TEST | PRODUCTION |
|---|---|---|
| Cookie `sessionid` | `HttpOnly`, `SameSite=Lax` | Idem + `Secure` (HTTPS) |
| Cookie `csrftoken` | Posé par `whoami`, non vérifié | Posé et **vérifié** sur toute requête mutante |
| `CSRF_TRUSTED_ORIGINS` | inclut `localhost:3100` et `localhost:8000` | À configurer avec le domaine réel de production |
| `CORS_ALLOWED_ORIGINS` | non strict | À restreindre au domaine du portail RSM |
| Durée de session | Par défaut Django (2 semaines) | À durcir (ex. 30 minutes inactif) |
| Verrouillage par tentatives | Non | À ajouter (django-axes ou équivalent) |

### 7.3 Séparation des rôles

La séparation est triple :

1. **Modèle** : un même utilisateur peut avoir plusieurs rôles, mais
   pas la combinaison `agent_saisie` + `autorite_validation`.
2. **Service** : chaque service métier appelle explicitement la
   fonction d'habilitation correspondante.
3. **Demande** : un même utilisateur ne peut pas valider une demande
   qu'il a saisie lui-même, même si techniquement il a les deux rôles
   (cas marginal explicitement testé).

### 7.4 Journal d'audit append-only

Le journal d'audit est protégé à deux niveaux indépendants
(application + base de données). Il enregistre :

- chaque dépôt, modification, renouvellement, radiation, validation,
  rejet ;
- chaque consultation de la recherche publique (art. 94) avec son
  certificat associé (art. 97) ;
- chaque action sur les comptes (création, affectation de rôle,
  changement de rôle).

Le chaînage par hachage permet de détecter toute altération a
posteriori, y compris si un acteur disposant d'un accès direct à la
base parvenait à contourner les triggers (situation à signaler par
l'auditeur).

### 7.5 Intégrité des données

- Toute écriture critique (dépôt, validation, modification) est
  encadrée par une transaction atomique (`@transaction.atomic`).
- L'attribution du numéro d'ordre utilise un verrou applicatif
  exclusif (`SELECT ... FOR UPDATE` sur la séquence) afin de garantir
  l'unicité et l'ordre chronologique exigés par l'article 78.
- Les contraintes d'intégrité référentielle empêchent toute
  suppression en cascade : une inscription ne peut pas être
  physiquement supprimée tant que des biens, parties ou snapshots y
  font référence.

### 7.6 Différence sécurité TEST / PRODUCTION

| Volet | TEST | PRODUCTION |
|---|---|---|
| Mots de passe seed | Texte clair affiché dans la documentation | **Interdits** |
| Bandeau MODE TEST | Visible | Masqué |
| `DJANGO_DEBUG` | `True` | **`False`** (impératif) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Domaine réel uniquement |
| `SECRET_KEY` | Valeur de développement | **Générée aléatoirement, conservée en coffre-fort** |
| HTTPS | Optionnel | **Obligatoire**, terminaison TLS au reverse proxy |
| Logs sensibles | Verbeux | Filtrés (pas de payloads avec données personnelles) |
| Comptes seedés | 7 comptes de test | **Aucun** ; comptes créés un à un par l'admin |

---

## 8. Déploiement et exploitation

### 8.1 Pré-requis techniques

| Composant | Version minimale | Notes |
|---|---|---|
| Système d'exploitation | Linux serveur (Debian 12, Ubuntu 22.04 LTS, RHEL 9) | Windows non recommandé en production |
| Python | 3.12 | Inclure `pip` et `venv` |
| PostgreSQL | 14+ (recommandé 16 ou 18) | Encodage `UTF-8` obligatoire, locale `fr_FR.UTF-8` ou `C.UTF-8` |
| Node.js | 18 LTS | Pour le build du frontend (étape ponctuelle) |
| Reverse proxy | nginx 1.22+ ou équivalent | Terminaison TLS, en-têtes de sécurité |
| Serveur d'application | gunicorn 21+ ou uWSGI | Mode worker recommandé : `gthread` ou `sync` |
| Espace disque | 50 Go (système) + selon volume documentaire | Croissance principale liée aux pièces jointes |
| Mémoire | 4 Go minimum, 8 Go recommandé | À calibrer selon le nombre de workers |

### 8.2 Variables d'environnement (fichier `.env`)

Toutes les variables sont lues via `python-decouple`. Aucune n'est
codée en dur.

| Variable | Type | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | secret | Clé de signature des sessions ; à générer aléatoirement |
| `DJANGO_DEBUG` | booléen | `False` en production |
| `DJANGO_ALLOWED_HOSTS` | csv | Domaines servis par l'application |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | csv | Origines de confiance pour le CSRF |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | divers | Connexion PostgreSQL |
| `DEFAULT_LANGUAGE` | code | `fr` par défaut |
| `TIME_ZONE` | IANA | `Africa/Nouakchott` |
| `RSM_MODE_TEST` | booléen | `false` en production |
| `RSM_TIMESOURCE_MODE` | code | `local_stub` jusqu'à F5, puis valeur désignée |
| `RSM_SEAL_MODE` | code | `disabled` jusqu'à F6 |
| `RSM_ESIGN_MODE` | code | `disabled` jusqu'à F3 |
| `RSM_MFA_MODE` | code | `disabled` jusqu'à F2 |
| `RSM_INTEROP_BANQUES_MODE` | code | `disabled` jusqu'à F15 |

### 8.3 Démarrage des services

Étapes ordonnées (à automatiser dans l'outil de déploiement) :

1. Activer l'environnement virtuel Python.
2. Installer les dépendances backend (`pip install -r requirements.txt`).
3. Appliquer les migrations (`python manage.py migrate`).
4. Collecter les fichiers statiques (`python manage.py collectstatic --noinput`).
5. Charger les référentiels (`python manage.py seed_referentiels`).
6. Vérifier que `seed_demo_test` n'est **pas** lancé en production.
7. Lancer le serveur d'application (gunicorn ou équivalent) sur un
   port interne (par exemple `127.0.0.1:8000`).
8. Configurer le reverse proxy : terminaison TLS, redirection HTTP →
   HTTPS, en-têtes de sécurité, fichier statique servi directement.
9. Vérifier que `GET /api/v1/auth/whoami/` répond `200`.

Le frontend est compilé une fois (`npm install` puis `npm run build`)
et déployé sous forme de fichiers statiques. Le proxy de
développement de Create React App n'est utilisé qu'en TEST.

### 8.4 Gestion des logs

| Source | Type | Recommandation |
|---|---|---|
| Django (vues, services) | Logs applicatifs | Journalisation au niveau `INFO` en production, `WARNING` minimum côté disque |
| Erreurs serveur | Tracebacks | Capture par Sentry ou équivalent ; ne pas laisser les tracebacks accessibles à l'utilisateur (`DJANGO_DEBUG=False`) |
| Audit métier | Table `EntreeAudit` | Append-only, conservé sans rotation |
| Reverse proxy | Accès et erreurs HTTP | Format combiné, conservé selon la politique RGPD locale |
| PostgreSQL | Slow queries, dead-locks | À surveiller |

Les logs **ne doivent pas** contenir les payloads de connexion,
les mots de passe, les jetons CSRF ni le contenu détaillé des
inscriptions.

### 8.5 Sauvegardes

- **Base de données** : sauvegarde quotidienne complète + archivage
  WAL (point-in-time recovery). Test mensuel de restauration
  documenté.
- **Pièces jointes** (médias) : sauvegarde synchronisée vers un
  stockage tiers chiffré.
- **Configuration** : `.env` et certificats hors arborescence du code,
  sauvegardés dans un coffre-fort dédié.
- **Cible RPO ≤ 1 heure, RTO ≤ 4 heures** (TDR § 5.3).

### 8.6 Montée en charge

Architecture conçue stateless côté application : la session est
stockée en base, chaque worker peut servir n'importe quelle requête
sans affinité. Pour absorber la charge :

- augmenter le nombre de workers gunicorn (règle empirique : 2× CPU
  cœurs + 1) ;
- configurer un pool de connexions PostgreSQL (pgbouncer recommandé) ;
- placer les fichiers statiques derrière un CDN ou activer le
  cache HTTP au niveau du reverse proxy ;
- horizontalement, plusieurs instances applicatives peuvent être
  ajoutées derrière un répartiteur de charge — l'unicité du numéro
  d'ordre reste garantie par PostgreSQL via le verrou exclusif.

---

## 9. Contraintes d'hébergement

### 9.1 Exigences serveur minimales

| Profil | Recommandation |
|---|---|
| TEST / RECETTE | 2 vCPU, 4 Go RAM, 50 Go SSD |
| PRODUCTION (démarrage) | 4 vCPU, 8 Go RAM, 100 Go SSD + sauvegardes externes |
| PRODUCTION (consolidée) | 8 vCPU, 16 Go RAM, 200 Go SSD + cluster PostgreSQL en réplication |

### 9.2 Système d'exploitation

Linux serveur LTS recommandé. Mises à jour de sécurité activées par
défaut (`unattended-upgrades` Debian, ou équivalent). Pare-feu local
(`ufw` ou `firewalld`) configuré pour ne laisser ouverts que les
ports strictement nécessaires.

### 9.3 Réseau et ports

| Port | Sortant | Entrant | Note |
|---|---|---|---|
| 443 | — | Public | HTTPS (terminaison reverse proxy) |
| 80 | — | Public | Redirection 301 vers HTTPS |
| 22 | — | Restreint à l'admin | SSH ; clé publique uniquement |
| 5432 | — | **Aucun externe** | PostgreSQL accessible uniquement depuis l'application (réseau interne) |
| Sortants | 80, 443, 53 | — | Mises à jour, NTP, monitoring |

### 9.4 Base de données

Instance PostgreSQL dédiée au RSM, isolée des autres applications.
Compte d'application avec privilèges **strictement** sur la base RSM
(création de table, lecture, écriture sur les tables applicatives,
**aucun privilège** sur les triggers d'audit pour empêcher leur
désactivation).

### 9.5 Stockage

- Volume principal : code, configuration, logs.
- Volume de médias (pièces jointes) : monté séparément, chiffré au
  repos.
- Volume de sauvegardes : externalisé.

### 9.6 Séparation des environnements

Les environnements **TEST** et **PRODUCTION** sont strictement
séparés :

- Serveurs distincts (ou au minimum machines virtuelles distinctes).
- Bases de données distinctes (jamais de réplication TEST → PROD ni
  inverse, sauf ce qui est explicitement prévu pour la pré-production).
- Comptes d'accès distincts (un administrateur production n'utilise
  pas les mêmes identifiants que pour la recette).
- Domaines distincts (par exemple `rsm-test.example.mr` et
  `rsm.example.mr`).
- Sauvegardes séparées et non interchangeables.

---

## 10. Points d'attention pour l'hébergeur

### 10.1 Points critiques à surveiller

1. **Disponibilité de la base de données** : toute indisponibilité
   bloque les inscriptions. Configurer une supervision active.
2. **Verrou sur la séquence du numéro d'ordre** : un long
   verrouillage peut indiquer un dead-lock ; alerter au-delà de 5 secondes.
3. **Croissance de la table d'audit** : append-only, jamais purgée.
   Surveiller l'espace disque et planifier l'archivage légal (mais pas
   la suppression — l'article 79 l'interdit).
4. **Synchronisation horaire** : décalage NTP > 1 seconde → alerte.
   Critique pour l'article 78 (horodatage à la seconde).
5. **Erreurs HTTP 500** : toutes anormales en production. Doivent
   déclencher une alerte immédiate.

### 10.2 Erreurs fréquentes à éviter

- Activer `DJANGO_DEBUG=True` en production : expose les variables
  d'environnement et tracebacks ; **interdit**.
- Lancer `seed_demo_test` en production : crée des comptes avec
  mots de passe en clair ; **interdit**.
- Désactiver les triggers d'audit pour des opérations de
  maintenance : viole l'article 79 ; toute action de ce type doit
  être tracée hors-bande et signalée à l'auditeur.
- Modifier directement la base de données via l'admin Django avec un
  super-utilisateur : l'admin est paramétrée en lecture seule
  précisément pour empêcher cette dérive.
- Lever les modes `RSM_*_MODE` (TIMESOURCE, SEAL, ESIGN, MFA,
  INTEROP) sans la note MO correspondante : génère des données
  incomplètes ou non opposables.

### 10.3 Paramètres sensibles

Les variables suivantes ne doivent **jamais** apparaître dans les
logs, le système de versionnement, les tickets ou les courriels :

- `DJANGO_SECRET_KEY`
- `DB_PASSWORD`
- Mots de passe d'administrateur ou de service
- Clés privées TLS, clés API tierces, jetons OAuth

Stockage recommandé : coffre-fort de secrets (HashiCorp Vault, AWS
Secrets Manager, ou solution équivalente locale). Les comptes
d'administration humains utilisent un gestionnaire de mots de passe
agréé.

### 10.4 Bonnes pratiques d'exploitation

- Toute modification du système (déploiement, mise à jour, migration)
  fait l'objet d'un ticket de changement avec date, auteur, motif.
- Les déploiements suivent une procédure documentée :
  pré-production → recette → bascule production → fenêtre de retour
  arrière de 24 heures.
- Les sauvegardes sont testées mensuellement par restauration sur un
  environnement isolé.
- Les logs sont conservés selon la politique légale applicable (au
  minimum 5 ans pour les actes notariés et registres publics, à
  vérifier auprès du Tribunal).
- L'auditeur (rôle `auditeur` dans le système) a un accès de
  consultation au journal d'audit et doit être informé de toute
  modification significative de l'infrastructure.

### 10.5 Éléments à valider avant mise en production

| # | Vérification |
|---|---|
| 1 | `DJANGO_DEBUG=False` |
| 2 | `RSM_MODE_TEST=false`, bandeau MODE TEST absent |
| 3 | `DJANGO_SECRET_KEY` régénérée et stockée hors code |
| 4 | `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` cantonnés au domaine de production |
| 5 | HTTPS actif, redirection HTTP → HTTPS opérationnelle |
| 6 | Les triggers PostgreSQL d'audit append-only sont vérifiés présents et actifs |
| 7 | Le compte admin technique a un mot de passe robuste, MFA si possible (cf. F2) |
| 8 | Aucun compte seed (`declarant_externe`, `greffier`, etc.) ne subsiste |
| 9 | Sauvegarde quotidienne testée, chiffrée |
| 10 | Plan de continuité documenté (RPO ≤ 1 h, RTO ≤ 4 h) |
| 11 | Synchronisation NTP active sur tous les serveurs |
| 12 | Pare-feu : seuls 80/443 ouverts au public, 22 restreint, 5432 fermé à l'externe |
| 13 | Logs centralisés et exempts de données personnelles |
| 14 | Procédure de gestion des incidents documentée et notifiée à l'équipe |
| 15 | Procès-verbal de mise en production signé par les parties (greffe, hébergeur, MO) |

---

## Annexes

### A. Conformité bilingue FR / AR

Toutes les fonctionnalités exposées au public ou aux agents
disposent de libellés FR et AR. La parité est garantie au niveau du
référentiel de traductions : mêmes clés, mêmes effets. La direction
d'écriture (LTR / RTL) est appliquée automatiquement par la feuille
de style globale en fonction de la langue active.

Aucune divergence d'effet juridique ne doit exister entre les deux
versions linguistiques (TDR § 7.1).

### B. Documents associés

| Référence | Sujet |
|---|---|
| L1 — Note de cadrage | Fondations institutionnelles |
| L2 — Spécifications fonctionnelles | Formulaires, règles de validation, statuts, rôles |
| L3 — Spécifications techniques | Modèle de données, dictionnaire d'API |
| L11 — Traçabilité | Articles 76 à 97, registre des décisions MO |
| Décision n° 0001/2026 | Levée juridique des zones gelées |
| Fiches MO F1 à F15 | Arbitrages institutionnels |

### C. Glossaire technique

| Terme | Sens dans le RSM |
|---|---|
| **SPA** | Single-Page Application : l'interface React |
| **DRF** | Django REST Framework |
| **CSRF** | Cross-Site Request Forgery (protection des formulaires) |
| **CORS** | Cross-Origin Resource Sharing |
| **Append-only** | Mode d'écriture interdisant la modification et la suppression |
| **MFA** | Multi-Factor Authentication (authentification forte) |
| **TSA** | Time Stamping Authority (autorité d'horodatage RFC 3161) |
| **PKI** | Public Key Infrastructure |
| **PDF/A** | Format PDF d'archivage normé ISO 19005 |
| **RTL / LTR** | Right-To-Left / Left-To-Right (sens d'écriture) |

---

*Fin de la note d'architecture technique et de déploiement — RSM.*
