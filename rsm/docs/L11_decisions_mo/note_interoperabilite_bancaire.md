# Note L11 — Interopérabilité du RSM avec les institutions bancaires

## Contexte

À l'occasion d'une mission de la Banque mondiale, la consultante a
recommandé que le système du Registre des Sûretés Mobilières (RSM) soit
**interopérable avec les banques** par le biais d'API, afin de soutenir
l'accès au financement des PME. Cette recommandation s'inscrit dans la
finalité même du Registre (décret 2021-033, articles 76 et 86) :
publicité des sûretés et opposabilité aux tiers.

Cette note **acte la recommandation** sans engager d'implémentation
fonctionnelle, conformément aux règles de gouvernance du projet
(« aucune invention fonctionnelle, signalement obligatoire des
ambiguïtés »).

## Position juridique

L'interconnexion avec des tiers (institutions bancaires, organismes de
microfinance, sociétés financières) **relève d'une zone d'arbitrage
institutionnel** au sens du TDR :

| Référence | Citation pertinente |
|---|---|
| Décret 2021-033, art. 82 | « Le greffe détient le monopole de la production et de la diffusion des statistiques relatives aux sûretés mobilières. » |
| Décret 2021-033, art. 83 | « La tenue du RSM peut être confiée à un organisme public ou privé selon les conditions fixées par cahier des charges approuvé par arrêté du ministre de la Justice. » |
| Décret 2021-033, art. 86 | « Le greffier n'est pas tenu de vérifier l'identité de la personne procédant à l'inscription ni les énonciations contenues dans la demande. » |
| Décret 2021-033, art. 94-97 | Recherches publiques : ouverture à tout intéressé, deux critères minimum (art. 96), certificat de recherche probant (art. 97). |
| TDR § 3.1 | « Périmètre explicitement exclu : interconnexions externes — relèvent d'arbitrages MO. » |
| TDR § 6.3 | Réversibilité du système (article 83). |

L'API bancaire envisagée doit donc :
1. **Respecter** l'article 94 — la recherche reste ouverte à tout
   intéressé et n'est pas réservée aux banques.
2. **Respecter** l'article 96 — au moins deux critères parmi la liste
   limitative. Aucune voie de contournement.
3. **Respecter** l'article 97 — chaque consultation aboutit à un
   certificat de recherche probant.
4. **Préserver** le monopole statistique (art. 82) — aucune extraction
   massive non tracée.
5. **Garantir** la traçabilité (art. 79) — append-only, identification
   du consommateur de l'API.
6. **Préserver** la réversibilité (art. 83) — la dépendance technique
   à un fournisseur d'API tiers ne peut pas créer un verrouillage.

## Décisions à obtenir (fiche F15 ouverte)

Pour activer l'interopérabilité, le maître d'ouvrage doit trancher :

1. **Régime juridique** : convention bilatérale, arrêté ministériel,
   cahier des charges art. 83 ?
2. **Identification des partenaires** : quels établissements
   (banques agréées BCM, microfinance, etc.) ? procédure d'agrément ?
3. **Authentification machine-to-machine** : mTLS, jeton OAuth 2,
   signature ETSI ? Lien avec la fiche F2 (MFA) ?
4. **Périmètre de données exposées** : strictement art. 96 ? ou
   enrichi (montant, durée, statut) ? Que reste-t-il privé ?
5. **Consentement** : un débiteur/constituant doit-il consentir
   explicitement à la consultation par tel établissement, ou la
   consultation publique art. 94 suffit-elle ?
6. **Tarification** : redevance par requête (cahier des charges
   art. 83) ou gratuité ?
7. **Quotas** : limite par partenaire ? détection de scraping ?
8. **Certificat de recherche probant** (art. 97) : produit pour
   chaque appel API ? quel format machine-lisible (PDF/A + signature) ?
9. **Notifications inverses** (banque → RSM) : autorisée ? format ?
   par exemple, notification d'intention de constituer une sûreté
   avant dépôt ?
10. **Audit & supervision** : qui audite les flux ? auditeur RSM
    seul, ou supervision BCM en plus ?

## Architecture cible (préparée, non active)

L'application Django `apps.interconnexions` est créée en squelette :
modèles techniques en place, **aucune route HTTP exposée** tant que
les paramètres ci-dessus ne sont pas reçus. Variable de configuration
`RSM_INTEROP_BANQUES_MODE = "disabled"`.

| Modèle | Rôle |
|---|---|
| `PartenaireBancaire` | Fiche d'un établissement habilité (raison sociale, code, statut d'agrément, dates de validité, contact technique). |
| `ConsentementInterconnexion` | Consentement explicite d'un constituant à la consultation par un partenaire donné (art. 96 + RGPD-équivalent). |
| `JournalAccesAPI` | Journal append-only de chaque appel : partenaire, requête, instant, certificat de recherche émis, résultat. |

L'authentification mTLS, la signature des requêtes, la production
automatisée de certificats de recherche probants et la limitation de
quotas sont **conditionnés** aux fiches F2, F3, F4, F5 et F15.

## Plan d'activation (à valider par le MO)

1. **Recevoir** la note MO « Interopérabilité bancaire » signée
   actant les 10 décisions de la section précédente.
2. **Migrer** les modèles `apps.interconnexions` (déjà créés mais
   non activés).
3. **Implémenter** les services et endpoints `/api/v1/banques/*` sur
   la base des paramètres techniques transmis (sans invention).
4. **Tester** en mode TEST avec partenaires fictifs avant production.
5. **Auditer** la première semaine d'exploitation et rapporter au MO.

## Garanties

- Aucune route HTTP `/api/v1/banques/*` n'est exposée à ce stade.
- Aucun partenaire n'est inscrit en base sans décision MO.
- L'article 94 du décret reste pleinement opérationnel : la recherche
  publique demeure accessible à tout intéressé, sans privilège
  bancaire.
- Le journal d'audit (art. 79) intégrera les flux d'API dès leur
  activation, à raison d'une entrée par appel.
