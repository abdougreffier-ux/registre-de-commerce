# Fiche MO — F13 — Interconnexions externes (RCCM, identité numérique)

**Référence L11** : `L11/interconnexions`
**Articles fondateurs** : article 96 (critère de recherche par numéro
RC) ; article 86 (régime déclaratif — limite essentielle) ; art. 85
(n° RC du constituant).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/interconnexions` — Interconnexions externes |
| Articles fondateurs | Art. 85, 96 (n° RC) ; art. 86 (limite : régime déclaratif) |
| Statut actuel | **Non implémenté**. Le n° RC et l'identité des parties sont des pures énonciations (art. 86). |
| Dépendances | F2 (authentification — si identité nationale retenue) ; F4 (notifications externes) ; F9 (arrêté peut préciser) |
| Impact transverse | Recherche publique (art. 96), enregistrement art. 85, notifications. |

---

## 2. Contexte juridique

### 2.1 Contexte de l'article 96

> *« La recherche s'effectue sur la base d'au moins deux des quatre
>   critères limitativement énumérés : …, numéro d'immatriculation au
>   registre du commerce du constituant, … »*

Le n° RC est un critère de recherche. Sa présence dans l'inscription
(art. 85) est une énonciation du déposant. Le décret ne prévoit pas
expressément de vérification automatique auprès du RCCM.

### 2.2 Limite essentielle de l'article 86

> *« Le greffier n'est pas tenu de vérifier l'identité de la personne
>   procédant à l'inscription, ni les énonciations contenues dans la
>   demande. »*

Cette disposition, cardinale, a deux lectures :
- **Lecture a** : le greffier **ne doit pas** vérifier (régime
  strictement déclaratif, lecture stricte).
- **Lecture b** : le greffier **n'est pas tenu** de vérifier (il n'a
  pas l'obligation, mais rien n'interdit au système de fournir une
  vérification informative).

Le choix entre les deux lectures influence directement les options
de cette fiche.

### 2.3 Interconnexions envisageables

| Cible | Finalité | Lien juridique |
|-------|----------|-----------------|
| **RCCM** (Registre du Commerce et du Crédit Mobilier) | Vérification d'existence du n° RC (art. 85, 96) | Fort (art. 96) |
| **Identité numérique nationale** | Authentification déclarant externe (F2) | Indirect (§ 5.1) |
| **Registre foncier** | Si bien grevé concerne un immeuble | Indirect |
| **Administration fiscale / douanes** | Si privilèges art. 76 (Trésor, fiscal, douanes) | Possible pour enregistrement automatique |
| **Sécurité sociale** | Si privilège art. 76 (prévoyance sociale) | Possible |
| **Registres d'intellectuelle** (OAPI) | Si nantissement de PI art. 76 | Possible |

### 2.4 Risques juridiques en l'absence d'arbitrage

- **Risque de double lecture de l'art. 86** : lecture stricte vs
  lecture souple — décision MO nécessaire.
- **Risque de décisions prises sur des énonciations erronées** (ex.
  inscription au nom d'une société inexistante au RCCM, non détectée).
- **Risque de charge excessive du déposant** : sans interconnexion,
  le déposant doit connaître et bien saisir le n° RC ; les erreurs
  alimentent les contentieux.
- **Risque de rigidité** : un système strictement déclaratif,
  techniquement dépassé par les interconnexions modernes, peut être
  perçu comme vieillissant.

---

## 3. Situation actuelle dans le système

### 3.1 Mécanisme en place

| Élément | État |
|---------|------|
| `Partie.numero_rc` | Champ texte libre, indexé (pour critère art. 96) ; aucune vérification |
| Validation à la saisie | Uniquement le format (longueur, caractères) |
| Recherche art. 96 | Utilise `numero_rc` comme critère, sans rapprochement externe |
| Notification externe | Non câblée (clés réservées L2.5 § 9.3) |
| Tests désactivés | `test_api_zones_gelees.py::test_verification_numero_rc_existant` |

### 3.2 Ce qui existe déjà

Un projet RCCM voisin (`web/` dans l'écosystème du Tribunal — cf.
L1) repose sur la même stack technique (Django + PostgreSQL + React).
Une interconnexion technique serait donc **facilitée** par la
proximité institutionnelle et technologique.

---

## 4. Options d'arbitrage

### 4.1 Option a — Aucune interconnexion (régime strictement déclaratif — statu quo)

**Description** : le système reste en lecture stricte de l'art. 86 :
toutes les énonciations (n° RC, identité, etc.) sont saisies telles
que déclarées, sans contrôle automatique. La responsabilité du
déposant est totale.

| Dimension | Évaluation |
|-----------|------------|
| Conformité stricte art. 86 | 🟢 Maximale |
| Simplicité technique | 🟢 Maximale |
| Protection contre abus / erreurs | 🔴 Faible |
| Coût | 🟢 Nul |
| Délai | 🟢 Immédiat |
| Réversibilité (art. 83) | 🟢 Totale |

**Avantages** : simplicité, conformité stricte.
**Inconvénients** : aucune protection contre erreurs ou fraudes
d'énonciation.

### 4.2 Option b — Interconnexion RCCM passive (lecture informative)

**Description** : le système **interroge** le RCCM à titre
**informatif** lors de la saisie d'un n° RC. Si le n° RC n'existe pas
au RCCM, un **avertissement** (non bloquant) est affiché au déposant
et au greffier. La décision d'inscrire reste celle du déposant / du
greffier (art. 86 préservé).

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟢 Préservée (contrôle informatif, non bloquant) |
| Protection | 🟢 Élevée |
| Complexité technique | 🟠 Intégration RCCM (API ou table partagée) |
| Dépendance externe | 🟠 Disponibilité du RCCM |
| Délai | 🟠 Moyen |

**Avantages** : balance judicieuse entre art. 86 et sécurité.
**Inconvénients** : dépendance à l'API RCCM.

### 4.3 Option c — Interconnexion RCCM active (blocage si incohérence)

**Description** : si le n° RC saisi n'existe pas au RCCM, le dépôt
est **refusé**. Le système agit en « gatekeeper ».

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🔴 **Tension** — le greffier opère alors un contrôle d'énonciation (lecture stricte de l'art. 86 contredite) |
| Protection | 🟢 Maximale |
| Risque juridique | 🔴 Contentieux potentiel sur le fondement du refus |
| Dépendance externe | 🔴 Indisponibilité RCCM = blocage inscriptions |
| Délai | 🟠 Moyen à long |

**Avantages** : qualité maximale des données.
**Inconvénients** : contrariété avec l'art. 86 ; sensibilité à la
disponibilité du RCCM.

### 4.4 Option d — Interconnexion identité numérique nationale

**Description** : si le MO dispose d'une identité numérique nationale
(F2 option c), l'authentification des déclarants externes passe par
ce service. Les données d'identité (nom, prénom, date de naissance)
sont alors **pré-remplies** ou **vérifiées** par le fournisseur
d'identité.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟢 Préservée (l'identité est authentifiée en amont, pas vérifiée par le greffier) |
| UX | 🟢 Améliorée |
| Dépendance externe | 🔴 Programme national d'identité numérique |
| Complexité | 🟠 Modérée |
| Interaction avec F2 | 🟢 Forte mutualisation |

**Avantages** : expérience utilisateur intégrée ; réduction des erreurs.
**Inconvénients** : dépend de l'existence et de la couverture du
programme.

### 4.5 Option e — Notifications externes aux parties (email / SMS)

**Description** : lors d'une inscription ou d'une modification, les
parties (créancier, constituant, débiteur) reçoivent une notification
à l'adresse e-mail ou au numéro mobile déclaré (`Partie.adresse_electronique`,
`Partie.telephone`). Pas de vérification d'identité — simple
information que leur nom figure dans une inscription.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 86 | 🟢 Préservée |
| Transparence | 🟢 Maximale |
| Prévention des abus | 🟢 Les parties peuvent contester rapidement |
| Dépendance externe | 🟠 Fournisseur SMS / email |
| Coût | 🟠 Commissions SMS |
| Risque de spam | 🟠 Si l'e-mail / téléphone déclaré est erroné |

**Avantages** : les parties sont informées et peuvent agir.
**Inconvénients** : dépend de la justesse des contacts déclarés.

### 4.6 Option f — Interconnexions multiples (RCCM + identité + notifications)

**Description** : combinaison des options b + d + e. Le système est
interconnecté à plusieurs sources externes pour améliorer la qualité
des données, tout en restant conforme à l'art. 86 (lecture souple).

| Dimension | Évaluation |
|-----------|------------|
| Qualité des données | 🟢 Maximale |
| Complexité | 🔴 Élevée |
| Dépendances | 🔴 Multiples |
| Coût | 🔴 Élevé |
| Délai | 🔴 Long |

**Avantages** : qualité maximale de l'écosystème RSM.
**Inconvénients** : coût et complexité cumulés.

### 4.7 Option g — Approche par paliers

**Description** : démarrage en option a (régime strict), bascule
progressive vers b (RCCM informatif), puis d (identité) et e
(notifications), au fur et à mesure que les infrastructures
partenaires sont disponibles et les conventions signées.

| Dimension | Évaluation |
|-----------|------------|
| Adaptabilité | 🟢 Maximale |
| Conformité progressive | 🟢 Dernière étape = option f |
| Complexité de gouvernance | 🟠 Plusieurs paliers |
| Délai | 🟢 Mise en service rapide |

**Avantages** : pragmatisme.
**Inconvénients** : plusieurs migrations successives.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Modifications |
|--------|---------------|
| a | Aucune |
| b | Client API RCCM + affichage d'avertissement ; aucune règle bloquante |
| c | Client API RCCM + blocage au dépôt si n° inconnu |
| d | Connecteur identité (cf. F2 option c) |
| e | Module de notification externe + gestion e-mail / SMS + logs opt-in |
| f | Cumul |
| g | Adaptateurs découplés + feature flags |

### 5.2 Impacts sur les tests

- Activation de `test_verification_numero_rc_existant`.
- Nouveaux tests : disponibilité RCCM, comportement en cas
  d'indisponibilité, notification envoyée, consentement (RGPD /
  réglementation locale à préciser).

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 § 2.1 (n° RC) | Mention de l'interconnexion informative ou bloquante |
| L2.2 Règle A-96.* | Précision selon option |
| L2.5 § 9.3 | Activation des clés `notification.*.externe` |
| L3.2 | Ajout d'un module `interconnexions` |
| L3.5 | Sécurité des flux sortants (TLS, authentification API) |
| L11 | Passage de `L11/interconnexions` à IMPLÉMENTÉ |

### 5.4 Dépendances transversales

- **F2 (MFA)** : si option d retenue, F2 option c est retenue
  simultanément.
- **F4 (certificats)** : notifications de délivrance de certificat
  = option e appliquée à cette notification.
- **F9 (arrêté)** : l'arrêté peut fixer les interconnexions
  obligatoires.

### 5.5 Impacts sur l'exploitation

- Convention de service avec chaque partenaire (RCCM, identité,
  opérateur SMS).
- SLA pour la disponibilité des API partenaires.
- Supervision des flux sortants.
- Politique de confidentialité / RGPD : quelles données échangées,
  avec quelle base légale ?
- Consentement des parties notifiées (opt-in ou notification
  systématique ?).

---

## 6. Tradeoffs synthétiques

| Critère | a (Aucune) | b (RCCM passif) | c (RCCM actif) | d (Identité) | e (Notifications) | f (Cumul) | g (Paliers) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Conformité stricte art. 86 | Maximale | Préservée | **Tension** | Préservée | Préservée | Préservée | Évolutive |
| Qualité des données | Faible | Élevée | Maximale | Élevée | Modérée | Maximale | Évolutive |
| Complexité technique | Nulle | Modérée | Modérée | Modérée | Modérée | Élevée | Évolutive |
| Coût | Nul | Modéré | Modéré | Modéré | Modéré (SMS) | Élevé | Progressif |
| Dépendance externe | Aucune | RCCM | RCCM critique | Identité nationale | SMS / email | Multiple | Variable |
| Bénéfice déposant | Faible | Bon | Maximal | Élevé | Bon | Maximal | Croissant |
| Bénéfice greffe | Faible | Bon | Maximal (mais risqué) | Bon | Bon | Maximal | Croissant |
| Risque juridique | Faible | Faible | Élevé | Faible | Faible | Modéré | Faible |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Lecture de l'art. 86** : stricte (aucune vérification) ou souple
   (vérification informative admise) ?
2. **Existence d'une API RCCM** au sein du même Tribunal ou au
   niveau national ?
3. **Convention de service** avec le RCCM : signée, en préparation ?
4. **Identité numérique nationale** : état d'avancement (lien avec
   F2 option c) ?
5. **Opérateurs SMS / email** : prestataires disponibles,
   qualité/coût.
6. **Base légale** du traitement des notifications (consentement
   implicite par déclaration, ou opt-in explicite) ?
7. **Cadre RGPD / protection des données personnelles** : quelle
   législation applicable (locale, OHADA) ?
8. **Articulation avec l'arrêté (F9)** : l'arrêté pourrait imposer ou
   interdire certaines interconnexions.
9. **Politique en cas d'indisponibilité** d'une interconnexion (ex. API
   RCCM en panne) : mode dégradé, rejet, file d'attente ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ g  ☐ autre : ______ |
| Interconnexions retenues (détail) | ☐ RCCM  ☐ Identité nationale  ☐ Notifications email/SMS  ☐ Registre foncier  ☐ Fiscal/Douanes  ☐ Sécurité sociale  ☐ OAPI |
| Lecture de l'art. 86 retenue | ☐ Stricte  ☐ Souple (informative) |
| Prestataires retenus | _(à renseigner)_ |
| Politique d'indisponibilité partenaire | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Critère de recherche art. 96 : [L2.2 § 2.15](../L2_2_regles_validation.md).
- Régime déclaratif art. 86 : [L2.2 § 2.7](../L2_2_regles_validation.md).
- Notifications externes (L2.5 § 9.3) : [L2.5](../L2_5_messages_systeme.md).
- Fiche F2 (identité) : [F2_authentification_forte.md](F2_authentification_forte.md).
- Fiche F4 (notifications délivrance) : [F4_charte_documentaire_certificats.md](F4_charte_documentaire_certificats.md).
- Fiche F9 (arrêté) : [F9_arrete_application.md](F9_arrete_application.md).
- Registre : [L11](../L11_tracabilite_articles_76_97.md).
