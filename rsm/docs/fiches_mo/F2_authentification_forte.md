# Fiche MO — F2 — Authentification forte des acteurs

**Référence L11** : `L11/MFA`
**Articles fondateurs** : TDR § 5.1 (sécurité et intégrité).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/MFA` — Authentification forte |
| Articles fondateurs | TDR § 5.1 ; art. 78 al. 1 (canal électronique) ; art. 83 (réversibilité — choix non captif) |
| Statut actuel | **Désactivé** (`RSM_MFA_MODE=disabled`). Authentification par session Django en mode développement. |
| Dépendances | Prérequis à l'ouverture du portail électronique (art. 78) ; préalable à tout dépôt par un déclarant externe. Débloque l'Option B (frontend). |
| Impact transverse | Tous les comptes : agents du greffe, greffiers, administrateurs, auditeurs, déclarants externes. |

---

## 2. Contexte juridique

### 2.1 Exigence du TDR § 5.1

> *« Authentification forte des utilisateurs internes (agents,
>   greffiers, administrateurs, auditeurs) reposant au minimum sur un
>   second facteur. »*

Cette exigence s'étend implicitement aux déclarants externes par la
combinaison de l'art. 78 al. 1 (canal électronique) et de la nécessité
de preuve de l'identité du déposant au titre de l'article 85 (identité
du requérant) — tout en respectant le régime déclaratif de
l'article 86 (pas de vérification d'identité au fond, mais
authentification de la session opposable).

### 2.2 Articulation avec l'article 86

L'art. 86 interdit au greffier de vérifier l'identité d'une partie
dans les énonciations du bordereau. Il **n'interdit pas** (au
contraire) d'authentifier le compte qui dépose la demande. Le
mécanisme de MFA porte donc sur **l'accès au système**, pas sur la
véracité des énonciations.

### 2.3 Articulation avec l'article 83 (réversibilité)

L'art. 83 exige que le système puisse être transféré à un autre
organisme. Le choix du MFA doit donc permettre une **migration sans
captivité** : les identifiants ne doivent pas dépendre d'un
fournisseur unique non renouvelable.

### 2.4 Risques en l'absence d'arbitrage

- **Portail électronique non ouvrable** : tant que le MFA n'est pas
  arbitré, aucun déclarant externe ne peut déposer en ligne. L'art. 78
  al. 1 reste donc inopérant côté portail.
- **Risque de compromission** d'un compte interne en cas de fuite du
  mot de passe seul.
- **Risque de contestation** lors d'un rejet (art. 80) ou d'une
  application (art. 88/91/92) si l'authentification du greffier
  repose uniquement sur un mot de passe réputé insuffisant au regard
  de § 5.1.

---

## 3. Situation actuelle dans le système

### 3.1 Mécanisme en place

- Authentification Django classique par session (mot de passe seul).
- `RSM_MFA_MODE=disabled` dans `.env.example`.
- Les tests `@arbitrage_mo(reference="L11/MFA", …)` sont désactivés
  (cf. `tests/test_api_zones_gelees.py`).
- L'admin Django utilise les mêmes sessions que l'API.
- Les endpoints d'écriture exigent `IsAuthenticated` — mais sans
  second facteur.

### 3.2 Points d'extension prévus

- Variable `.env` `RSM_MFA_MODE` avec valeurs cibles documentées en
  L3.3 § 5 (`totp`, `x509_card`, `id_numerique_nationale`).
- Placeholder `apps/utilisateurs/habilitations.py` — aucun appel à un
  adaptateur MFA n'est câblé à ce jour.
- Sonde de santé `GET /sante/` expose l'état « MFA inactive » en
  clair, signalant aux auditeurs que les actes ne sont pas
  authentifiés fortement.

### 3.3 Populations d'utilisateurs concernées

| Catégorie | Exemple | Volume estimé | Canal principal |
|-----------|---------|:-------------:|-----------------|
| Agents du greffe | Agent de saisie, greffier | dizaines | Intranet |
| Administrateurs | Fonctionnel, technique | unités | Intranet |
| Auditeurs | Président du Tribunal, juge commis (art. 83) | unités | Intranet |
| Déclarants externes | Créanciers, notaires, mandataires | centaines à milliers | Internet |

---

## 4. Options d'arbitrage

### 4.1 Option a — TOTP (Time-based One-Time Password)

**Description** : second facteur par application mobile (Google
Authenticator, FreeOTP, Authy…) ou par SMS fallback. Le compte
partage un secret avec l'application, qui génère un code temporel
renouvelé toutes les 30 secondes. À la connexion, l'utilisateur saisit
mot de passe + code TOTP.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🟢 **Très faible** — bibliothèque Python (`pyotp`) + QR code de provisionnement |
| Dépendance externe | 🟠 Application mobile de l'utilisateur (multiples options libres) |
| Robustesse | 🟠 Modérée — vulnérable au phishing du code ; TOTP via SMS vulnérable au SIM swap |
| Accessibilité | 🟢 Tout utilisateur avec un smartphone ou un PC |
| Déclarants externes | 🟢 Adapté |
| Agents internes | 🟢 Adapté |
| Migration / réversibilité | 🟢 Standard RFC 6238, indépendant fournisseur |
| Conformité § 5.1 | 🟠 Minimum TDR satisfait — « au minimum un second facteur » |

**Avantages** : simple, rapide à déployer, bien documenté, adapté à
tous profils.
**Inconvénients** : niveau de sécurité modéré ; nécessite la
récupération en cas de perte de l'application.

### 4.2 Option b — Certificat X.509 sur carte à puce ou token matériel

**Description** : chaque compte reçoit une carte à puce ou un token
USB (YubiKey, SafeNet, etc.) portant un certificat X.509. L'accès
exige la présentation du certificat (mutual TLS) ou une signature
challenge-response. Idéalement appuyé sur une PKI nationale si elle
existe.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🔴 **Élevé** — acquisition de tokens, infrastructure PKI, support utilisateur |
| Dépendance externe | 🔴 Dépendant d'une PKI (interne ou nationale) |
| Robustesse | 🟢 **Élevée** — résistant au phishing, résistant au vol de mot de passe |
| Accessibilité | 🟠 Matériel à distribuer et à remplacer en cas de perte |
| Déclarants externes | 🔴 Complexe — distribution à des milliers d'utilisateurs externes peu pratique |
| Agents internes | 🟢 Adapté |
| Migration / réversibilité | 🟠 La PKI doit être cessible (art. 83) |
| Conformité § 5.1 | 🟢 **Maximale** |

**Avantages** : très haute sécurité, résistance aux attaques à
distance.
**Inconvénients** : coûteux, inadapté aux déclarants externes
hétérogènes, dépendance à une infrastructure lourde.

### 4.3 Option c — Identité numérique nationale

**Description** : utilisation d'une identité numérique nationale
mauritanienne, si elle existe et est opérationnelle (ex. par carte
d'identité électronique, système d'identité fédéré, ou application
gouvernementale). Le système RSM délègue l'authentification au
fournisseur d'identité officiel.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🟠 Dépend de l'état d'avancement du programme national |
| Dépendance externe | 🔴 Dépendant d'un service national |
| Robustesse | 🟢 Élevée en général |
| Accessibilité | 🟢 Uniforme pour tous les citoyens |
| Déclarants externes | 🟢 **Très adapté** — toute personne disposant de l'identité nationale peut se connecter |
| Agents internes | 🟢 Adapté |
| Migration / réversibilité | 🟠 Le service reste disponible même en cas de transfert du RSM (art. 83). |
| Conformité § 5.1 | 🟢 Élevée |
| Conformité art. 86 | 🟢 L'identité est vérifiée par le fournisseur national, pas par le greffier. |

**Avantages** : expérience utilisateur intégrée, identité forte,
réversibilité préservée (l'identité reste utilisable par un
repreneur).
**Inconvénients** : dépend de l'existence et de la couverture du
programme national ; peut exclure les étrangers (notaires ou mandataires
internationaux).

### 4.4 Option d — Mécanisme bi-niveau (agents internes vs déclarants externes)

**Description** : combinaison de deux mécanismes selon la population :
- **Agents internes** (greffe, administration, audit) : option b
  (certificat X.509 sur token matériel) — sécurité maximale pour les
  décisions officielles.
- **Déclarants externes** : option a (TOTP) ou option c (identité
  numérique nationale) — accessibilité maximale.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement | 🟠 Modéré — tokens uniquement pour les agents (petit volume) |
| Dépendance externe | 🟠 Selon le mécanisme retenu pour les externes |
| Robustesse | 🟢 Hétérogène mais proportionnée |
| Accessibilité | 🟢 Adaptée à chaque population |
| Conformité § 5.1 | 🟢 Élevée (tous les utilisateurs ont un second facteur) |
| Complexité d'exploitation | 🔴 **Élevée** — deux infrastructures à maintenir |

**Avantages** : chaque population reçoit le mécanisme le mieux adapté.
**Inconvénients** : double infrastructure, double procédure de
support, risque d'incohérence dans la politique de sécurité.

### 4.5 Option e — Approche par paliers

**Description** : démarrage avec option a (TOTP universel) pour une
mise en production rapide. Bascule ultérieure vers option b ou c
lorsque les infrastructures sont disponibles, sans interruption de
service. Pendant la période de palier, le niveau de sécurité est celui
de l'option a mais les fonctions critiques (validation art. 87,
rejet art. 80, application art. 88) peuvent exiger une
ré-authentification immédiate.

| Dimension | Évaluation |
|-----------|------------|
| Coût de déploiement initial | 🟢 Très faible |
| Coût total | 🟠 Croissant avec les paliers |
| Dépendance externe | 🟢 Nulle au démarrage |
| Robustesse | 🟠 Modérée au départ, croissante |
| Ouverture du portail | 🟢 **Rapide** — les déclarants externes peuvent déposer en quelques mois |
| Conformité § 5.1 | 🟠 Acceptable dans la phase initiale, renforcée ensuite |
| Complexité d'exploitation | 🟠 Gestion des migrations inter-paliers |

**Avantages** : mise en service rapide, évolutivité.
**Inconvénients** : deux ou trois paliers successifs créent un risque
d'oubli ou d'enlisement ; politique de sécurité évolutive à
communiquer.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Module à câbler |
|--------|-----------------|
| a | `apps.utilisateurs` — ajout d'un modèle `SecretTOTP` + vue de provisionnement + validation du code au login |
| b | Adaptateur mutual TLS + intégration PKI + gestion des révocations (OCSP, CRL) |
| c | Connecteur OpenID Connect ou SAML vers le fournisseur national |
| d | Combinaison des précédents avec routage selon le profil |
| e | Démarrage à l'option a puis extension |

Dans tous les cas, l'interface stable est déjà prévue par le paramètre
`RSM_MFA_MODE` (cf. L3.3 § 5). Le code métier (habilitations § 4.1)
n'a **pas besoin d'être modifié** — seule la couche d'authentification
change.

### 5.2 Impacts sur les tests

- Activation de `test_api_zones_gelees.py::test_acces_refuse_sans_second_facteur`.
- Activation de `test_api_zones_gelees.py::test_soumission_portail_exige_authentification_forte`.
- Nouveau test : tentative de connexion sans second facteur → 401
  avec message `autorisation.refus.non_authentifie`.
- Compatibilité des tests S1–S6 et D.1–D.3 : utilisent
  `force_authenticate`, indépendants du mécanisme MFA.

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 Formulaires | Mention de l'authentification attendue par canal |
| L2.4 Habilitations | Mise à jour du schéma de décision (étape 1 enrichie) |
| L2.5 Messages système | Activation de `autorisation.refus.non_authentifie` |
| L3.5 Sécurité | Section § 6.4 (détournement de session) mise à jour |
| L11 Registre | Passage de `L11/MFA` à IMPLÉMENTÉ |

### 5.4 Impacts sur l'exploitation

- Formation des utilisateurs (procédure de second facteur).
- Procédure de récupération en cas de perte (réinitialisation TOTP,
  remise d'une nouvelle carte X.509, ré-enrôlement identité
  nationale).
- Journal d'audit : les événements `connexion` (catégorie
  `CategorieAudit.CONNEXION`, aujourd'hui non instrumentée) doivent
  être tracés avec le mécanisme de second facteur utilisé.

### 5.5 Impacts sur l'Option B (frontend)

Débloque le développement du portail externe (Option B) :
- Formulaire de connexion avec second facteur.
- Pages de provisionnement et de récupération.
- Bandeaux d'alerte en cas de session à privilège temporaire.

---

## 6. Tradeoffs synthétiques

| Critère | a (TOTP) | b (X.509) | c (Identité nationale) | d (Bi-niveau) | e (Paliers) |
|---------|:-:|:-:|:-:|:-:|:-:|
| Coût initial | Très faible | Élevé | Modéré | Modéré | Très faible |
| Coût récurrent | Faible | Modéré | Variable | Élevé | Faible → croissant |
| Robustesse technique | Modérée | Maximale | Élevée | Hétérogène | Modérée → croissante |
| Adapté aux externes | Oui | Faible | Très adapté si dispo | Oui (volet externe) | Oui |
| Adapté aux internes | Oui | Très adapté | Oui | Très adapté (volet interne) | Oui |
| Délai d'ouverture portail | Court | Long | Dépend du national | Long (interne) | Court |
| Réversibilité (art. 83) | Élevée (RFC) | Dépendante PKI | Dépendante du national | Hétérogène | Élevée |
| Conformité § 5.1 | Satisfaisant | Maximale | Élevée | Élevée | Progressive |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Existence d'une identité numérique nationale** en Mauritanie :
   couverture, disponibilité d'API d'authentification (SAML, OIDC),
   licences d'usage.
2. **Existence d'une PKI nationale ou sectorielle** : infrastructure,
   coût d'émission de certificats, révocation.
3. **Budget annuel** alloué à l'exploitation du second facteur.
4. **Niveau de maturité numérique** des populations cibles (en
   particulier les mandataires et notaires).
5. **Obligations sectorielles** éventuelles (banque, finance) qui
   imposeraient un niveau de sécurité minimal pour les déclarants
   externes.
6. **Politique de récupération** en cas de perte du second facteur :
   procédure au guichet, délai, documents nécessaires.
7. **Journalisation des événements d'authentification** : niveau de
   détail attendu au journal d'audit (catégorie `connexion`).

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ autre : ______ |
| Mécanisme précis (si option a, c, e) | _(à renseigner)_ |
| Valeur arbitrée de `RSM_MFA_MODE` | _(à renseigner : `totp` / `x509_card` / `id_numerique_nationale` / …)_ |
| Politique de récupération | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Politique d'horodatage et de scellement (modes cibles MFA) : [L3.3 § 5](../L3_3_horodatage_scellement.md).
- Dispositifs de sécurité : [L3.5](../L3_5_securite_integrite.md) § 6.4.
- Dictionnaire API — permissions : [L3.4 § 1.2](../L3_4_dictionnaire_api.md).
- Rôles × opérations : [L2.4](../L2_4_roles_operations.md).
- Registre des arbitrages : [L11](../L11_tracabilite_articles_76_97.md).
