# Fiche MO — F11 — Politique tarifaire et paiement (art. 85)

**Référence L11** : `A7`
**Articles fondateurs** : article 85 (prépaiement des émoluments) ;
TDR § 3.2 (périmètre — définition de la politique tarifaire relève du
Greffe).

---

## 1. Identification

| Attribut | Valeur |
|----------|--------|
| Référence L11 | `A7` — Politique tarifaire / paiement |
| Articles fondateurs | Art. 85 (« le requérant règle d'avance les émoluments du greffe ») ; TDR § 3.2 (politique tarifaire = MO) |
| Statut actuel | **Non implémenté**. Aucun champ tarifaire, aucun module de paiement. |
| Dépendances | F2 (authentification déclarant externe — préalable au paiement en ligne) ; F9 (arrêté d'application pourrait préciser les tarifs) ; F10 (durée maximale — si tarif proportionnel). |
| Impact transverse | Dépôts d'inscriptions, modifications, renouvellements, radiations, recherches, certificats. |

---

## 2. Contexte juridique

### 2.1 Exigence de l'article 85

> *« Le requérant règle d'avance les émoluments du greffe. »*

Cet impératif pose :
- un **prérequis temporel** : règlement **avant** l'inscription ;
- une **nature contractuelle** : émoluments du greffe (non fiscaux) ;
- un **silence sur la forme** : aucune mention d'espèces, chèque,
  virement, mobile money, ou paiement électronique.

### 2.2 Exigence du TDR § 3.2

> *« La perception des émoluments : l'article 85 prévoit que le
>   requérant règle d'avance les émoluments du greffe, sans préciser
>   de modalités électroniques. L'intégration d'un moyen de paiement
>   électronique fait partie du périmètre ; la définition de la
>   politique tarifaire relève du Greffe. »*

Le TDR attribue donc **au MO/Greffe** la décision sur :
- le **barème** (montants) ;
- les **moyens** de paiement acceptés ;
- les **modalités** de perception (caisse, portail, tiers).

### 2.3 Articulation avec le régime déclaratif

L'art. 86 interdit toute vérification au fond. Le paiement n'est pas
une énonciation du bordereau : c'est une condition préalable. Son
contrôle par le greffe est donc admissible, mais il doit rester
limité à la **vérification du paiement**, non à l'appréciation du
fond de la demande.

### 2.4 Articulation avec l'art. 82

L'art. 82 réserve le monopole statistique au greffe. Les recettes
tarifaires peuvent faire l'objet d'extractions statistiques — à
arbitrer dans le cadre de l'éventuel module de statistiques
financières.

### 2.5 Risques juridiques en l'absence d'arbitrage

- **Risque de blocage de l'art. 85** : si aucun mécanisme de
  prépaiement n'est en place, toute inscription via le canal
  électronique est impossible (le déposant ne peut pas « régler
  d'avance »).
- **Risque d'inégalité de traitement** : le canal papier peut
  continuer à fonctionner avec des modalités traditionnelles
  (caisse, chèque) tandis que le canal électronique reste bloqué.
- **Risque opérationnel** : sans règle claire sur la politique
  tarifaire, les agents du greffe appliquent des pratiques
  éventuellement divergentes.

---

## 3. Situation actuelle dans le système

### 3.1 État technique

| Élément | État |
|---------|------|
| Champ tarifaire sur `Inscription` | Inexistant |
| Module de paiement | Non câblé |
| Tests désactivés liés | `test_api_zones_gelees.py::test_depot_refuse_sans_paiement_des_emoluments` |
| Notification de paiement | `paiement.demande` (L2.5 § 9.3) — clé réservée, non émise |

### 3.2 Ce qui est cependant possible aujourd'hui

- Le canal papier fonctionne : l'agent de saisie accepte le bordereau
  papier et vérifie manuellement le paiement aux guichets du greffe
  (hors système informatique).
- La référence au paiement peut être ajoutée en commentaire interne,
  mais elle n'a pas de valeur opposable.

---

## 4. Options d'arbitrage

### 4.1 Option a — Gratuité totale

**Description** : aucun émolument perçu. Le service est gratuit pour
tous les déposants et tous les types d'inscriptions. L'art. 85 est
interprété comme n'imposant le prépaiement que si un montant est
effectivement dû ; à défaut, il est sans objet.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 85 | 🟠 Interprétation extensive (silence sur les montants) |
| Accessibilité | 🟢 Maximale |
| Financement du greffe | 🔴 Aucun par cette voie |
| Complexité technique | 🟢 Nulle |
| Risque d'usage abusif | 🔴 Élevé — inscriptions de complaisance |

**Avantages** : simplicité, accessibilité.
**Inconvénients** : tension avec le texte (« règle d'avance les
émoluments ») ; pas de signal de sérieux ; financement ?

### 4.2 Option b — Barème fixe par type d'acte

**Description** : le MO établit un **barème officiel** avec un tarif
par type d'acte (ex. inscription initiale, modification,
renouvellement, radiation, certificat de recherche). Le barème est
publié et appliqué uniformément. Le montant est fixe indépendamment
de la somme garantie ou du volume de biens.

Exemple indicatif (ordre de grandeur, à arbitrer) :

| Acte | Tarif indicatif |
|------|-----------------|
| Inscription initiale | X |
| Modification | Y |
| Renouvellement | Y |
| Radiation | Y |
| Certificat de recherche | Z |

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 85 | 🟢 Stricte (prépaiement possible) |
| Prévisibilité | 🟢 Maximale |
| Simplicité administrative | 🟢 |
| Équité | 🟠 Peut sembler disproportionné pour petites vs grandes sûretés |

**Avantages** : simplicité, prévisibilité, équité formelle.
**Inconvénients** : pas d'ajustement à la nature ou à l'enjeu.

### 4.3 Option c — Barème proportionnel à la somme garantie

**Description** : tarif composé d'une part fixe + part proportionnelle
à la `somme_garantie` (ex. 0,1 % plafonné à un maximum).

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 85 | 🟢 Stricte |
| Équité économique | 🟢 Proportionnée à l'enjeu |
| Complexité administrative | 🟠 Barème plus complexe à expliquer |
| Stabilité | 🟠 Variation selon inflation |

**Avantages** : justice économique.
**Inconvénients** : complexité, potentielles contestations sur les
plafonds et planchers.

### 4.4 Option d — Barème différencié par nature de sûreté

**Description** : tarifs modulés selon la nature (art. 76). Exemples :
privilèges fiscaux ou sociaux (gratuité administrative), sûretés
commerciales (tarifs standards), propriété intellectuelle (tarifs
spécifiques).

| Dimension | Évaluation |
|-----------|------------|
| Pertinence métier | 🟢 Élevée |
| Complexité administrative | 🟠 Table de tarifs par nature |
| Justice sectorielle | 🟢 |
| Cohérence avec la pratique | 🟠 Dépend du paysage réglementaire mauritanien |

**Avantages** : adaptation fine.
**Inconvénients** : gouvernance plus lourde ; risque de discriminations.

### 4.5 Option e — Tarif + abonnement pour utilisateurs récurrents

**Description** : tarif standard (option b) **plus** un abonnement
optionnel pour les utilisateurs institutionnels (banques, notaires,
mandataires) qui réalisent de nombreuses inscriptions. L'abonnement
donne accès à un tarif unitaire réduit ou à un forfait.

| Dimension | Évaluation |
|-----------|------------|
| Accessibilité | 🟢 Élevée |
| Attrait pour institutionnels | 🟢 |
| Complexité technique | 🔴 Deux modèles en parallèle |
| Risque juridique | 🟠 Discrimination tarifaire à justifier |

**Avantages** : incitation à l'adoption par professionnels.
**Inconvénients** : gouvernance complexe, questions d'égalité
d'accès.

### 4.6 Option f — Paiement par virement / caisse (sans module électronique)

**Description** : le prépaiement s'effectue par **virement bancaire**
vers un compte du greffe ou **en caisse** physique. Le numéro
d'opération / référence est reporté manuellement dans le bordereau
(champ optionnel ajouté). Le portail électronique n'intègre pas de
module de paiement mais exige la référence du virement.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 85 | 🟢 |
| Simplicité technique | 🟢 Très élevée |
| Accessibilité | 🟠 Dépend de la bancarisation du déposant |
| Délai | 🔴 Le virement peut prendre plusieurs jours |
| Sécurité | 🟠 Risque de fausses références |

**Avantages** : aucune infrastructure de paiement.
**Inconvénients** : lenteur, nécessite un contrôle manuel du
paiement par l'agent.

### 4.7 Option g — Paiement électronique intégré (mobile money, carte bancaire)

**Description** : intégration d'un **module de paiement électronique**
au portail, via un prestataire local (Sedad, Bankily) ou
international (solution conforme BCEAO / AMF). Le paiement est
vérifié en temps réel ; le dépôt n'est admis qu'après confirmation.

| Dimension | Évaluation |
|-----------|------------|
| Conformité art. 85 | 🟢 Stricte |
| Accessibilité | 🟢 Élevée (mobile money largement répandu) |
| Délai | 🟢 Immédiat |
| Complexité technique | 🔴 Intégration prestataire + conformité PCI-DSS (si carte) |
| Dépendance externe | 🔴 Prestataire(s) de paiement |
| Coût récurrent | 🟠 Commissions par transaction |

**Avantages** : rapidité, modernité.
**Inconvénients** : infrastructure et coût récurrent.

### 4.8 Option h — Modèle hybride (caisse + virement + électronique)

**Description** : le MO accepte **plusieurs moyens** — caisse pour
déposants physiques, virement pour professionnels bancarisés,
paiement électronique pour déposants en ligne. Chaque canal a sa
procédure de vérification.

| Dimension | Évaluation |
|-----------|------------|
| Accessibilité | 🟢 Maximale |
| Complexité opérationnelle | 🔴 Trois flux à gérer |
| Coût | 🟠 Cumul |
| Équité | 🟢 |

**Avantages** : adaptation à toutes les populations.
**Inconvénients** : complexité d'exploitation.

---

## 5. Impacts transversaux

### 5.1 Impacts sur le code

| Option | Modifications |
|--------|---------------|
| a | Aucune |
| b | Table de tarifs paramétrable + champ `emolument_paye` sur demande |
| c | Fonction de calcul de tarif + contrôle proportionnel |
| d | Table tarifs × nature |
| e | Système d'abonnement + comptes institutionnels |
| f | Champ `reference_virement` + contrôle manuel côté greffier |
| g | Module de paiement complet (intégration prestataire) |
| h | Combinaison b à g |

### 5.2 Impacts sur les tests

- Activation de `test_api_zones_gelees.py::test_depot_refuse_sans_paiement_des_emoluments`.
- Nouveau test : tarif correctement calculé selon barème retenu.
- Nouveau test : dépôt refusé si émolument impayé.
- Cohérence avec S1 : le scénario nominal devra inclure l'étape de
  paiement (option b à h).

### 5.3 Impacts sur les livrables

| Livrable | Impact |
|----------|--------|
| L2.1 § 2.2 | Préciser les étapes de paiement préalables |
| L2.5 § 9.3 | Activation des messages `paiement.*` |
| L2.6 scénarios A, B | Étape de paiement à ajouter |
| L3.1 | Nouveau modèle `OperationPaiement` ou équivalent |
| L11 | Passage de `A7` à IMPLÉMENTÉ |

### 5.4 Dépendances transversales

- **F2 (MFA)** : le déclarant externe doit être authentifié avant
  d'accéder au paiement.
- **F9 (arrêté)** : l'arrêté d'application pourrait fixer le barème
  officiellement.
- **F10 (durée max)** : si tarif proportionnel à la durée, la
  politique tarifaire dépend de la politique de durée.

### 5.5 Impacts sur l'exploitation

- Caisse physique du greffe (option f, h).
- Comptabilité et reddition financière.
- Remboursement en cas d'annulation.
- Réconciliation bancaire.
- Lutte anti-blanchiment (grands montants).

---

## 6. Tradeoffs synthétiques

| Critère | a (Gratuité) | b (Fixe) | c (Proportionnel) | d (Par nature) | e (Abonnement) | f (Virement) | g (Électronique) | h (Hybride) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Conformité art. 85 | Discutable | Stricte | Stricte | Stricte | Stricte | Stricte | Stricte | Stricte |
| Accessibilité | Maximale | Élevée | Élevée | Élevée | Élevée | Modérée | Élevée | Maximale |
| Complexité technique | Nulle | Faible | Modérée | Modérée | Élevée | Faible | Élevée | Très élevée |
| Coût de déploiement | Nul | Faible | Faible | Modéré | Élevé | Très faible | Élevé | Élevé |
| Coût récurrent | Nul | Nul | Nul | Nul | Modéré | Faible | Modéré (commissions) | Modéré |
| Délai | Immédiat | Immédiat | Court | Court | Moyen | Moyen | Long | Long |
| Financement du greffe | Nul | Oui | Oui | Oui | Oui | Oui | Oui | Oui |
| Adéquation mobile money | N/A | N/A | N/A | N/A | N/A | Non | Oui | Oui |

---

## 7. Points à préciser lors de l'arbitrage MO

1. **Besoin de financement** du greffe par les émoluments (montants
   attendus annuels).
2. **Barème indicatif** : le MO dispose-t-il déjà d'un barème de
   référence (ex. RCCM) ?
3. **Existence d'un arrêté tarifaire** distinct de l'arrêté
   d'application F9 ?
4. **Politiques de gratuité** éventuelles (privilèges du Trésor, de
   la sécurité sociale, etc.) ?
5. **Prestataires de paiement** disponibles en Mauritanie (mobile
   money, cartes, banques partenaires) ?
6. **Politique d'abonnement** pour institutionnels (banques,
   notaires) ?
7. **Procédure de remboursement** en cas d'annulation ou de
   double-paiement.
8. **Traitement comptable** : compte séparé, reddition, audit.
9. **Seuils anti-blanchiment** : au-delà d'un montant, déclaration
   CENTIF ?
10. **Monnaie retenue** : MRU exclusivement, ou acceptation devises ?

---

## 8. Décision MO

**À compléter séparément par une décision écrite et référencée du
Maître d'ouvrage.**

| Champ | Valeur |
|-------|--------|
| Option retenue | ☐ a  ☐ b  ☐ c  ☐ d  ☐ e  ☐ f  ☐ g  ☐ h  ☐ autre : ______ |
| Barème officiel | _(à renseigner)_ |
| Prestataires de paiement retenus | _(à renseigner)_ |
| Politique de remboursement | _(à renseigner)_ |
| Fondement juridique | _(à renseigner)_ |
| Motivation | _(à renseigner)_ |
| Signataire | _(à renseigner)_ |
| Date | _(à renseigner)_ |
| Référence du document officiel | _(à renseigner)_ |

---

## 9. Renvois croisés

- Article 85 (prépaiement) : [L11](../L11_tracabilite_articles_76_97.md).
- TDR § 3.2 (périmètre) : [L1](../L1_note_de_cadrage.md).
- Message `paiement.demande` : [L2.5 § 9.3](../L2_5_messages_systeme.md).
- Scénarios A, B : [L2.6](../L2_6_scenarios_fonctionnels.md).
- Fiche F2 (authentification) : [F2_authentification_forte.md](F2_authentification_forte.md).
- Fiche F9 (arrêté d'application) : [F9_arrete_application.md](F9_arrete_application.md).
- Fiche F10 (durée) : [F10_duree_maximale.md](F10_duree_maximale.md) — interaction si tarif proportionnel.
