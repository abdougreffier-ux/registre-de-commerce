# Fiche MO — F15 — Interopérabilité avec les banques (consultation API)

**Référence L11** : `L11/interoperabilite_banques`
**Articles fondateurs** : article 94 (recherche ouverte à tout
intéressé) ; article 96 (deux critères minimum) ; article 97
(certificat de recherche probant) ; article 82 (monopole statistique
du greffe) ; article 83 (réversibilité) ; article 79 (traçabilité).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `L11/interoperabilite_banques` |
| Articles fondateurs | Art. 79, 82, 83, 94, 96, 97 |
| Statut actuel | **Non implémenté**. Prévision architecturale posée par `apps.interconnexions` (squelette modèles, aucun endpoint exposé). |
| Origine | Recommandation de mission Banque mondiale (avril 2026). |
| Dépendances | F2 (authentification forte), F3 (signature), F4 (certificats probants), F5 (horodatage), F13 (interconnexions amont). |
| Impact transverse | Recherche art. 94-97, certificats, audit. |

---

## 2. Contexte juridique

### 2.1 Article 94 — recherche ouverte à tout intéressé

> *« Toute personne qui y a un intérêt peut effectuer une recherche
>   dans le RSM. »*

L'API d'interopérabilité bancaire **n'introduit pas de privilège** :
toute personne peut déjà consulter le Registre, et l'API ne fait que
fournir un canal machine-à-machine pour le même type de consultation.

### 2.2 Article 96 — critères limitatifs

L'API doit imposer **au moins deux critères parmi les quatre**
limitativement énumérés. Aucun contournement par filtres complémentaires
(typologie, montant, secteur) n'est admis.

### 2.3 Article 97 — certificat probant

Chaque consultation, qu'elle soit guichet, web ou API, doit aboutir
à un certificat de recherche probant. L'API doit donc retourner,
pour chaque appel, soit un identifiant de certificat, soit le
certificat scellé lui-même (PDF/A signé).

### 2.4 Article 82 — monopole statistique du greffe

L'API ne doit **pas** permettre l'extraction massive ou le calcul
d'indicateurs agrégés par les banques : ce serait une production
statistique externe, contraire au monopole.

### 2.5 Article 83 — réversibilité

Le système doit pouvoir être confié à un autre organisme. L'API
bancaire ne peut donc pas reposer sur un fournisseur tiers
verrouillant ce changement.

### 2.6 Article 79 — traçabilité append-only

Chaque appel API doit produire une entrée d'audit immuable
identifiant le partenaire, l'instant, la requête et le certificat
émis.

---

## 3. Cas d'usage métier (recommandation Banque mondiale)

| # | Cas | Description | Conformité décret |
|---|---|---|---|
| 1 | Pré-décision crédit | Une banque vérifie, avant l'octroi d'un crédit, si le bien proposé en garantie n'est pas déjà grevé. | Art. 94, 96 ✓ |
| 2 | Surveillance portefeuille | Une banque surveille périodiquement les sûretés constituées sur ses clients. | Art. 94 ✓ — nécessite consentement client |
| 3 | Notification d'intention | Une banque notifie au RSM son intention de constituer une sûreté avant dépôt formel (réservation). | **Hors décret** — ⚠️ création de droit nouveau, exclue |
| 4 | Dépôt automatisé | Une banque dépose elle-même la demande d'inscription via API. | Art. 78 ✓ — conforme au canal électronique |
| 5 | Consultation statistique sectorielle | Une banque récupère des indicateurs agrégés sur le marché du crédit. | **Art. 82** ⚠️ — monopole greffe |

Les cas 1, 2 et 4 sont conformes et constituent le périmètre cible.
Le cas 3 est **hors décret** et doit être écarté. Le cas 5 est
**réservé au greffe** et doit être écarté de l'API bancaire.

---

## 4. Risques juridiques en l'absence d'arbitrage

- **Risque art. 94** : si l'API est réservée aux banques agréées sans
  ouverture aux autres tiers, on crée un privilège contraire à
  l'ouverture publique. Solution : la recherche publique web reste
  opérationnelle ; l'API est un canal machine pour les mêmes données.
- **Risque art. 96** : si l'API accepte un seul critère, elle viole
  l'exigence légale.
- **Risque art. 97** : si l'API ne produit pas de certificat probant,
  les consultations API ne sont pas opposables et la banque garde
  une exposition juridique.
- **Risque art. 82** : si l'API permet l'agrégation statistique, le
  monopole du greffe est contourné.
- **Risque RGPD-équivalent** : exposition de données à caractère
  personnel (nom du constituant, adresse, n° RC) à un acteur tiers
  sans base légale précise.
- **Risque sécurité** : appels API non authentifiés ou non scellés
  exposent le Registre à du scraping, à de l'usurpation et à de la
  fraude.

---

## 5. Architecture cible (préparée — squelette créé)

### 5.1 Modèles techniques (`apps.interconnexions`)

| Modèle | Rôle |
|---|---|
| `PartenaireBancaire` | Établissement habilité (raison sociale, code, agrément BCM, contact technique, statut). |
| `AccreditationPartenaire` | Conventions signées et en cours, avec dates, plafond requêtes/jour, niveau d'habilitation (lecture seule / dépôt). |
| `ClePubliquePartenaire` | Clé publique X.509 du partenaire pour la signature des requêtes (mTLS et / ou JWS). |
| `ConsentementInterconnexion` | Consentement explicite d'un constituant à la consultation périodique par un partenaire donné (cas d'usage 2). |
| `JournalAccesAPI` | Append-only — partenaire, instant, requête, certificat émis, code retour. |

### 5.2 Endpoints (à activer après arbitrage)

| Méthode | URL | Cas d'usage | Permission |
|---|---|---|---|
| GET | `/api/v1/banques/recherche/` | 1 (pré-décision) | mTLS partenaire + 2 critères art. 96 |
| GET | `/api/v1/banques/inscriptions/{ref}/certificat/` | 1, 2 | mTLS partenaire + identifiant certificat |
| POST | `/api/v1/banques/inscriptions/` | 4 (dépôt automatisé) | mTLS + signature requête + consentement constituant |
| POST | `/api/v1/banques/surveillance/` | 2 (surveillance) | mTLS + consentement constituant |

**Aucune** route n'est exposée tant que `RSM_INTEROP_BANQUES_MODE = "active"`.

### 5.3 Sécurité technique

- **mTLS** : authentification mutuelle obligatoire ; la banque présente
  son certificat client signé par une autorité agréée (à désigner).
- **Signature JWS** : chaque requête sensible (dépôt, consentement)
  est signée par la clé privée du partenaire.
- **Limitation de débit** : par partenaire, par jour, paramétrée dans
  `AccreditationPartenaire`.
- **Anti-scraping** : refus si plus de N recherches identiques
  consécutives ; détection d'énumération de critères.
- **Journal d'audit** : entrée par appel, append-only (art. 79).

---

## 6. Décisions à obtenir du Maître d'ouvrage

| # | Décision | Options possibles |
|---|---|---|
| 1 | Régime juridique de l'API | Convention bilatérale par banque ; arrêté général ; cahier des charges art. 83 |
| 2 | Liste des partenaires éligibles | Banques agréées BCM uniquement ; + microfinance ; + sociétés financières ; + IFI |
| 3 | Mécanisme d'authentification machine | mTLS seul ; mTLS + JWS ; OAuth 2 mTLS Bound ; eIDAS-like |
| 4 | Périmètre des données exposées | Strict art. 96 ; + montant ; + durée ; + statut radiée/expirée |
| 5 | Consentement du constituant | Implicite (recherche publique art. 94) ; explicite à chaque appel ; explicite renouvelable annuellement |
| 6 | Tarification | Gratuit ; redevance par appel ; abonnement annuel ; cahier des charges art. 83 |
| 7 | Quotas | Aucun ; par partenaire ; par jour ; par client final |
| 8 | Format du certificat probant API | PDF/A scellé ; JSON-LD signé W3C-VC ; les deux |
| 9 | Notifications inverses | Refusées (cas 3) ; acceptées en mode information non opposable ; acceptées en mode réservation |
| 10 | Audit & supervision | Auditeur RSM seul ; + supervision BCM ; + commission de suivi MO |
| 11 | Politique en cas de panne API | Rejet fail-fast ; mode dégradé documenté ; bascule vers recherche web |
| 12 | Réversibilité (art. 83) | Standardisation OpenAPI publique ; couche d'abstraction qui isole le fournisseur ; clause de cessibilité dans les conventions |

---

## 7. Tradeoffs synthétiques

| Décision clé | Option restrictive | Option ouverte | Recommandation Banque mondiale |
|---|---|---|---|
| Périmètre données | Strict art. 96 | + statuts/montants | Ouvert (utile pour scoring crédit) |
| Consentement | Explicite | Implicite (art. 94) | À arbitrer avec autorité de protection des données |
| Tarification | Gratuit | Redevance | À aligner sur F11 |
| Authentification | mTLS seul | mTLS + JWS + OAuth | Standard internationaux (mTLS + JWS) |

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|---|---|
| Régime juridique retenu | ☐ Convention bilatérale  ☐ Arrêté  ☐ Cahier des charges art. 83 |
| Partenaires éligibles | ☐ Banques BCM  ☐ Microfinance  ☐ Sociétés financières  ☐ IFI  ☐ autres : ______ |
| Authentification machine | ☐ mTLS  ☐ mTLS + JWS  ☐ OAuth 2 mTLS  ☐ eIDAS-like |
| Périmètre de données | ☐ Strict art. 96  ☐ + montant  ☐ + durée  ☐ + statut |
| Consentement constituant | ☐ Implicite art. 94  ☐ Explicite à chaque appel  ☐ Renouvelable annuellement |
| Tarification | ☐ Gratuit  ☐ Redevance/appel  ☐ Abonnement |
| Quotas par partenaire | ☐ Aucun  ☐ Plafond ____/jour |
| Format certificat API | ☐ PDF/A signé  ☐ JSON-LD VC  ☐ Les deux |
| Notifications inverses | ☐ Refusées  ☐ Information non opposable  ☐ Réservation opposable |
| Audit | ☐ RSM seul  ☐ + BCM  ☐ + commission MO |
| Politique panne | ☐ Rejet  ☐ Mode dégradé  ☐ Bascule web |
| Réversibilité | ☐ OpenAPI public  ☐ Couche d'abstraction  ☐ Clause cessibilité |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Recherche art. 94-97 : [L2.6 § 5](../L2_6_scenarios_fonctionnels.md).
- Régime déclaratif art. 86 : [L2.2 § 2.7](../L2_2_regles_validation.md).
- Monopole statistique art. 82 : [F12 cahier des charges art. 83](F12_cahier_charges_art83.md).
- Interconnexions amont (RCCM, identité) : [F13](F13_interconnexions_externes.md).
- Authentification forte : [F2](F2_authentification_forte.md).
- Signature électronique : [F3](F3_signature_electronique.md).
- Certificats probants : [F4](F4_charte_documentaire_certificats.md).
- Tarification : [F11 politique tarifaire](F11_politique_tarifaire.md).
- Note L11 cadrage : [note_interoperabilite_bancaire.md](../L11_decisions_mo/note_interoperabilite_bancaire.md).
- Décision mère levée zones gelées : [decision_0001_2026.md](../L11_decisions_mo/decision_0001_2026.md).
