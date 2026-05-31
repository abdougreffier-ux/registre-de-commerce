# L2.2 — Règles de validation

**Livrable** : L2.2 — partie du livrable L2 (§ 8 du TDR).
**Objet** : inventaire fonctionnel et opposable des règles de
validation appliquées par le système.
**Fondement** : articles 76 à 97 du décret 2021-033 ; TDR § 4.
**État** : consolidation de l'existant. **Aucune règle nouvelle.**

---

## 1. Principes généraux

### 1.1 Régime déclaratif (art. 86) — règle cardinale

Le système applique **exclusivement** des contrôles de forme. Sont
**interdits** :

- vérifier l'identité réelle d'une partie ;
- vérifier l'existence d'un bien au-delà de la description fournie ;
- vérifier la véracité d'un numéro d'immatriculation auprès du RCCM
  (zone gelée `L11/interconnexions`) ;
- vérifier la conformité d'un accord entre parties au-delà de la
  présence des flags déclarés ;
- apprécier le bien-fondé d'une sûreté.

Toute règle listée ci-dessous est un **contrôle de forme** admissible
car elle découle d'une disposition expresse du décret ou du TDR.

### 1.2 Classification des règles

| Classe | Nature | Exemple |
|--------|--------|---------|
| A — Listes limitatives | Appartenance à une énumération officielle | Nature art. 76, motif de rejet art. 80, critère art. 96 |
| B — Champs obligatoires | Présence / absence | Identification des parties art. 85 |
| C — Formats | Conformité au format attendu | ISO-8601, Decimal, email |
| D — Contraintes temporelles | Date cohérente | Renouvellement avant expiration art. 91 |
| E — Invariants d'état | Contraintes sur l'état résultant | Art. 88 dernier alinéa (état final) |
| F — Séparation de pouvoirs | Habilitation / non-cumul | § 4.1 TDR |
| G — Cohérence cryptographique | Empreintes, chaînage | Journal d'audit, snapshots (en mode STUB) |

### 1.3 Issue d'une règle violée

Toute violation d'une règle produit :
- une **exception typée** (cf. L3.4 § 15) ;
- un **code HTTP** (400 métier, 403 autorisation) ;
- une **clé de motif neutre** (ex. `MotifRejet`, `MotifRefusModification`) ;
- une **entrée au journal d'audit** si l'opération dépasse la
  recevabilité initiale.

---

## 2. Règles article par article

### 2.1 Article 76 — Liste limitative des natures

**Règle A-76.1** — Nature de droit ∈ `NaturesDroitInscrit` (12 valeurs).

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 76, § 1.1 TDR |
| Classe | A — Liste limitative |
| Application | Dépôt d'inscription ; diff de modification |
| Contrôle | `nature_droit ∈ dict(NaturesDroitInscrit.choices)` |
| Exception levée | `RejetForme` (dépôt) / `DiffModification.ValueError → DIFF_INVALIDE` (modification) |
| HTTP | 400 |
| Référence code | [apps/core/enums.py](../backend/apps/core/enums.py) |
| Test | [test_regles_metier.py::test_nature_droit_hors_liste_rejetee](../backend/tests/test_regles_metier.py) |

---

### 2.2 Article 78 — Canaux, ordre, numéro d'ordre

**Règle A-78.1** — Canal ∈ {`guichet_papier`, `portail_electronique`}.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 78 alinéa 1 |
| Classe | A |
| Application | Dépôt d'inscription |
| Exception levée | `RejetForme` (motif `canal_non_autorise` art. 80) |
| Test | [test_api_s2_rejet_art80.py::test_canal_hors_liste_refuse_au_depot](../backend/tests/test_api_s2_rejet_art80.py) |

**Règle C-78.2** — Format du numéro d'ordre `NNNNNN-AAAAMMJJHHMMSS`.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 78 alinéa 4 |
| Classe | C — Format |
| Application | Attribution au moment de la validation |
| Contrôle | `format_numero_ordre(instant, numero_sequence)` (L3.3 § 3.5) |
| Garanties | Unique, chronologique, jamais réutilisé (§ 10.1 TDR) |
| Test | [test_concurrence_art78.py::test_attributions_concurrentes_toutes_uniques](../backend/tests/test_concurrence_art78.py) |

**Règle G-78.3** — Horodatage à la seconde fondant l'ordre d'arrivée
et la prise d'effet.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 78 al. 2, 3, 4 |
| Classe | G — Cohérence temporelle |
| État | ⚠️ STUB — zone gelée `L11/horodatage` |
| Interface | `apps.core.horodatage.maintenant_opposable()` (L3.3 § 3.1) |

**Règle E-78.4** — Immutabilité du numéro d'ordre et des horodatages.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 78 al. 4, art. 87, art. 90 al. 1 |
| Classe | E |
| Application | Les champs `numero_ordre`, `instant_arrivee`, `instant_saisie_opposable` sont dans `CHAMPS_JAMAIS_MODIFIABLES` du diff de modification |
| Exception levée | `ModificationSansEffet` avec motif `DIFF_INVALIDE` |
| Test | [test_modifications.py::test_champs_jamais_modifiables_refuses](../backend/tests/test_modifications.py) |

---

### 2.3 Article 79 — Conservation pérenne

**Règle G-79.1** — Aucune suppression physique d'une donnée
régulièrement enregistrée.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 79 |
| Classe | G |
| Application | Tous les modèles append-only ou à validité temporelle (L3.1 § 3.2) |
| Mise en œuvre | Overrides ORM + triggers PostgreSQL pour le journal d'audit (L3.5 § 2.1, § 3.1) |
| Exception levée | `PermissionError` → HTTP 403 article 79 |
| Test | [test_modifications.py::ConservationIntegraleTests](../backend/tests/test_modifications.py) |

**Règle E-79.2** — Rupture de chaîne d'empreintes détectable.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 79 al. 2, § 5.2 TDR |
| Classe | G |
| Mise en œuvre | `verifier_chaine()` exposé par `/api/v1/audit/verification-chaine/` |
| Test | [test_audit.py](../backend/tests/test_audit.py) et [test_audit_concurrence.py](../backend/tests/test_audit_concurrence.py) |

---

### 2.4 Article 80 — Motifs LIMITATIFS de rejet

**Règle A-80.1** — Motif ∈ `MotifRejet` (3 valeurs uniquement).

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 80 |
| Classe | A |
| Application | Prononcé d'un rejet par l'autorité de validation |
| Motifs limitatifs | `canal_non_autorise`, `informations_illisibles`, `informations_incomprehensibles` |
| Exception levée | `RejetForme` si motif hors liste |
| HTTP | 400 avec `article="80"` |
| Test | [test_api_s2_rejet_art80.py::test_rejet_motif_hors_liste_refuse](../backend/tests/test_api_s2_rejet_art80.py) |

**Règle F-80.2** — Notification du rejet sans délai.

⚠️ **Zone gelée** `L11/interconnexions` + `L11/MFA` : le canal de
notification (email, SMS, portail) dépend de l'arbitrage MO. Le
système trace le rejet immédiatement à l'audit et fige l'inscription
en `statut=REJETEE` dès le prononcé.

---

### 2.5 Article 82 — Monopole statistique du greffe

**Règle F-82.1** — Seul un acteur de rôle `PROD_STATS` peut produire
une extraction statistique.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 82 |
| Classe | F |
| Application | Endpoint `POST /api/v1/statistiques/produire/` |
| Mise en œuvre | `apps.utilisateurs.habilitations.peut_produire_statistiques` (L3.5 § 4.3) |
| Exception levée | `AutorisationRefusee` → HTTP 403 |
| Test | [test_habilitations.py::test_monopole_statistiques](../backend/tests/test_habilitations.py) |

---

### 2.6 Article 85 — Contenu obligatoire d'inscription

**Règle B-85.1** — Contenu obligatoire : nature, somme, identification
des créanciers / constituants / débiteurs, description des biens,
durée, identité du requérant.

Cf. détails complets dans [L2.1 § 2](L2_1_formulaires_bilingues.md).

**Règle B-85.2** — Biens individualisés : numéro de série, fabricant,
modèle, année NON BLOQUANTS.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 85 alinéa 3 |
| Classe | B |
| Règle | Leur omission ne prive pas l'inscription d'effet si les biens sont décrits par ailleurs |
| Mise en œuvre | Champs `blank=True` sur `BienGreve` ; aucune validation de présence imposée |
| Test | [test_regles_metier.py::test_champs_bien_grevé_optionnels_non_bloquants](../backend/tests/test_regles_metier.py) |

**Règle B-85.3** — Adresse électronique pour notifications facultative.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 85 avant-dernier alinéa |
| Classe | B |
| Règle | `adresse_electronique_notifications` optionnelle |

---

### 2.7 Article 86 — Régime déclaratif

**Règle (méta)** — Aucun contrôle au fond ; uniquement contrôles de
forme. Cf. § 1.1 du présent document.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 86 |
| Classe | — (règle de restriction méthodologique) |
| Mise en œuvre | Par design ; revue de code obligatoire pour détecter toute dérive |

---

### 2.8 Article 87 — Prise d'effet à la saisie

**Règle G-87.1** — Prise d'effet = instant de saisie opposable.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 87 |
| Classe | G |
| État | ⚠️ STUB (`L11/horodatage`) — non opposable tant que la source de temps n'est pas arbitrée |
| Mise en œuvre | `Inscription.instant_saisie_opposable` posé à la transition → `INSCRITE` |

---

### 2.9 Article 88 — Modifications

**Règle A-88.1** — Schéma strict du diff.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 88 |
| Classe | A |
| Clés racine admises | `parties`, `biens`, `scalaires` |
| Clés scalaires admises | `nature_droit`, `somme_garantie`, `monnaie`, `adresse_electronique_notifications` |
| Clés NEVER modifiables | `numero_ordre`, `instant_arrivee`, `instant_saisie_opposable`, `reference_demande`, `duree_en_jours`, `date_expiration`, `statut`, `fichier_actuel`, `mention_radiee`, `motif_rejet` |
| Exception levée | `ModificationSansEffet` avec motif `DIFF_INVALIDE` |
| Test | [test_modifications.py::SchemaDiffStrictTests](../backend/tests/test_modifications.py) |

**Règle B-88.2** — Accord du créancier et du constituant obligatoire.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 88 |
| Classe | B |
| Champs | `accord_createur_confirme`, `accord_constituant_confirme` |
| Règle | Tous deux `True` pour appliquer |
| Exception levée | `ModificationSansEffet` avec motif `ACCORDS_MANQUANTS` |
| État | ⚠️ Vérification cryptographique GELÉE (`L11/A2`) — flags booléens uniquement |
| Test | [test_modifications_cas_limites.py::test_rejet_pour_accords_manquants](../backend/tests/test_modifications_cas_limites.py) |

**Règle E-88.3 (cardinale)** — État final de l'inscription après
application doit comporter :
- ≥ 1 **constituant** actif,
- ≥ 1 **créancier garanti** actif,
- ≥ 1 **bien grevé** actif.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 88 dernier alinéa, § 4.3 TDR |
| Classe | E — Invariant d'état |
| Mise en œuvre | `_verifier_etat_final(inscription)` APRÈS application dans un savepoint |
| Motifs de rejet | `ETAT_FINAL_CONSTITUANT_ABSENT`, `ETAT_FINAL_CREANCIER_ABSENT`, `ETAT_FINAL_BIEN_ABSENT` |
| Effet | Rollback du savepoint + marquage `REJETEE` + audit `modification.refuser` |
| Garantie anti-contournement | Le contrôle porte sur l'ÉTAT FINAL, pas sur le diff isolé. Aucune succession de modifications ne peut aboutir à un état invalide. |
| Test | [test_modifications_cas_limites.py::ControleEtatFinalTests, AntiContournementParSuccessionTests](../backend/tests/test_modifications_cas_limites.py) ; [test_api_d2_rejet_art88.py](../backend/tests/test_api_d2_rejet_art88.py) |

---

### 2.10 Article 90 alinéa 2 — Durée non modifiable

**Règle E-90.1** — `duree_en_jours` et `date_expiration` sont dans
`CHAMPS_JAMAIS_MODIFIABLES` du diff.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 90 al. 2 |
| Classe | E |
| Effet | La durée ne peut être modifiée que par un renouvellement (art. 91) |
| Exception levée | `ModificationSansEffet` avec motif `DIFF_INVALIDE` |
| Test | [test_api_s3_transitions_interdites.py::test_modification_durée_ou_date_expiration_refusee](../backend/tests/test_api_s3_transitions_interdites.py) |

---

### 2.11 Article 91 — Renouvellement avant expiration

**Règle D-91.1** — Date d'expiration courante strictement future.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 91 |
| Classe | D — Contrainte temporelle |
| Contrôle | `inscription.date_expiration ≥ aujourd'hui` ET `statut ∈ STATUTS_EN_COURS_DE_VALIDITE` |
| Exception levée | `RenouvellementHorsDelai` → HTTP 400 article 91 |
| Test | [test_regles_metier.py::test_renouvellement_apres_expiration_refuse](../backend/tests/test_regles_metier.py) ; [test_api_s3_transitions_interdites.py::test_renouvellement_apres_expiration_refuse](../backend/tests/test_api_s3_transitions_interdites.py) |

**Règle D-91.2 (hypothèse A3)** — Prorogation = durée initiale,
décomptée à partir de la date d'expiration en cours.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 91, hypothèse adoptée TDR § 9.3 |
| Interprétation retenue | « Durée initiale » = durée fixée à l'inscription (non à un renouvellement antérieur) |
| Formule | `nouvelle_date_expiration = ancienne_date_expiration + duree_en_jours` |
| État | En attente d'arbitrage MO formel (zone `L11/A3`) |
| Test | [test_regles_metier.py::test_renouvellement_proroge_de_duree_initiale](../backend/tests/test_regles_metier.py) |

---

### 2.12 Article 92 — Radiation

**Règle B-92.1** — Contenu du bordereau de radiation.

Cf. [L2.1 § 5](L2_1_formulaires_bilingues.md).

**Règle A-92.2** — Fondement ∈ `FondementRadiation`
(`consentement`, `jugement`, `requerant_original`).

**Règle E-92.3** — Mention « radiée » au fichier public jusqu'à expiration.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 92 al. 2 |
| Classe | E |
| Effet | `mention_radiee = True` ; inscription reste au fichier public |
| Test | [test_api_s4_recherche_coherence.py::test_inscription_radiee_visible_au_fichier_public](../backend/tests/test_api_s4_recherche_coherence.py) |

**Règle D-92.4** — Transfert automatique au fichier général après expiration.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 92 al. 3 |
| Classe | D |
| Mise en œuvre | `python manage.py expirer_inscriptions` (commande quotidienne) |
| Transition | Automatique `RADIEE → EXPIREE → ARCHIVEE` ; `fichier_actuel = "general"` |
| Test | [test_api_s4_recherche_coherence.py::test_inscription_archivee_invisible_au_fichier_public](../backend/tests/test_api_s4_recherche_coherence.py) |

---

### 2.13 Article 93 — Indexation

**Règle G-93.1** — Index par nom du constituant.

**Règle G-93.2** — Index additionnel par numéro de série pour les
biens qui en portent un.

**Règle G-93.3** — Modifications et radiations associées au numéro
de l'inscription initiale (rattachement FK).

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 93 |
| Classe | G |
| Mise en œuvre | Index SQL (L3.5 § 2.3) ; FK `inscription` sur `DemandeModification`, `DemandeRenouvellement`, `DemandeRadiation` |

---

### 2.14 Article 94 — Ouverture à tout intéressé

**Règle F-94.1** — Recherche publique accessible sans authentification.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 94 |
| Classe | F |
| Mise en œuvre | `permissions.AllowAny` sur `RecherchePublique` |
| Test | [test_api_s4_recherche_coherence.py::test_recherche_deux_criteres_ouverte_sans_auth](../backend/tests/test_api_s4_recherche_coherence.py) |

---

### 2.15 Article 96 — Deux critères minimum

**Règle A-96.1** — Critères ∈ `CritereRecherche` (4 valeurs
limitatives).

**Règle B-96.2** — AU MOINS deux critères renseignés.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 96 |
| Classe | B |
| Contrôle | `NB_MIN_CRITERES = 2` |
| Exception levée | `RechercheCriteresInsuffisants` → HTTP 400 article 96 |
| Test | [test_regles_metier.py::test_recherche_un_seul_critere_refusee](../backend/tests/test_regles_metier.py) |

**Règle A-96.3** — Clés hors liste refusées explicitement (durcissement
serializers, cohérence globale).

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 96, TDR cohérence globale |
| Mise en œuvre | `_CriteresSerializer(StrictInputSerializer)` |
| HTTP | 400 avec champ `non_autorises` |
| Test | [test_api_s4_recherche_coherence.py::test_critere_hors_liste_refuse_par_l_api](../backend/tests/test_api_s4_recherche_coherence.py) ; [test_api_d3_accept_language.py](../backend/tests/test_api_d3_accept_language.py) |

---

### 2.16 Article 97 — Homonymes et certificat probant

**Règle B-97.1** — Si `nom_constituant` utilisé, résultat exhaustif
des homonymes avec nom, prénom, adresse, date de naissance.

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 97 alinéa 2 |
| Classe | B |
| Mise en œuvre | `homonymes_par_inscription` dans la réponse de recherche |
| Test | [test_regles_metier.py::test_homonymes_inclus_quand_recherche_par_nom](../backend/tests/test_regles_metier.py) ; [test_api_s4_recherche_coherence.py::test_homonymes_constituants_retournes_en_totalite](../backend/tests/test_api_s4_recherche_coherence.py) |

**Règle G-97.2** — Certificat de recherche probant (art. 97 dernier alinéa).

| Propriété | Valeur |
|-----------|--------|
| Fondement | art. 97 dernier al. |
| Classe | G |
| État | **ZONE GELÉE `L11/A5`** — `Certificat.probant = False` tant que scellement et horodatage ne sont pas arbitrés |

---

## 3. Règles transverses du TDR

### 3.1 § 4.1 TDR — Séparation stricte

**Règle F-4.1.1** — Aucun utilisateur ne peut valider / appliquer sur la même demande qu'il a lui-même déposée.

| Propriété | Valeur |
|-----------|--------|
| Fondement | § 4.1 TDR |
| Classe | F |
| Application | Validation, rejet, application M/R/Rad |
| Mise en œuvre | `peut_valider_demande(acteur, saisie_par)` rejette si `saisie_par.pk == acteur.pk` |
| Exception levée | `AutorisationRefusee` → HTTP 403 |
| Test | [test_habilitations.py::SeparationStricteTests](../backend/tests/test_habilitations.py) ; [test_api_d1_separation_stricte.py](../backend/tests/test_api_d1_separation_stricte.py) |

**Règle F-4.1.2** — Administrateurs (fonctionnel et technique) : aucune écriture métier.

| Propriété | Valeur |
|-----------|--------|
| Fondement | § 4.1 TDR |
| Mise en œuvre | `ecriture_metier_autorisee()` + classes admin verrouillées (L3.5 § 5) |

---

### 3.2 § 4.3 TDR — Matrice des transitions

Cf. [L2.3](L2_3_matrice_statuts_transitions.md) pour la matrice
complète (15 transitions autorisées + 4 interdictions explicites).

---

### 3.3 § 5.2 TDR — Traçabilité

**Règle G-5.2.1** — Toute action significative est tracée.

Liste des actions tracées : cf. L3.5 § 9.

**Règle G-5.2.2** — Immuabilité et chaînage.

Cf. § 2.3 (Règle G-79.1 et G-79.2).

---

### 3.4 § 6.3 / § 7 TDR — Bilinguisme

**Règle (méta)** — Mêmes effets juridiques FR et AR.

Cf. [L3.6](L3_6_matrice_bilingue.md) pour la démonstration par
construction. Tests : [test_api_d3_accept_language.py](../backend/tests/test_api_d3_accept_language.py).

---

### 3.5 Cohérence globale — durcissement API

**Règle A-global.1** — Rejet des clés inconnues dans TOUS les
serializers d'entrée.

| Propriété | Valeur |
|-----------|--------|
| Fondement | TDR cohérence globale |
| Mise en œuvre | `StrictInputMixin` (L3.5 § 4.2) |
| Test | [test_serializers_stricts.py](../backend/tests/test_serializers_stricts.py) |

---

## 4. Matrice récapitulative des exceptions métier

| Classe d'exception | Article | Motifs associés | HTTP |
|--------------------|:-------:|-----------------|:----:|
| `RejetForme` | 80 | Canal hors liste, nature hors liste, motif de rejet hors liste | 400 |
| `ModificationSansEffet` | 88 | 8 motifs `MotifRefusModification` | 400 |
| `RenouvellementHorsDelai` | 91 | Renouvellement postérieur à expiration | 400 |
| `RechercheCriteresInsuffisants` | 96 | < 2 critères | 400 |
| `TransitionInterdite` | § 4.3 | Hors matrice ou dans les interdictions explicites | 400 |
| `AutorisationRefusee` | § 4.1 | Rôle manquant, cumul saisie/validation | 403 |
| `PermissionError` | 79 | Tentative de `save()` / `delete()` sur append-only | 403 |

---

## 5. Matrice récapitulative des règles par phase

| Phase | Règles appliquées |
|-------|-------------------|
| Dépôt | A-78.1, A-76.1, C (formats), B-85.* |
| Contrôle de forme | A-80.1, schéma du bordereau, art. 86 (abstention) |
| Validation | B-85.*, F-4.1.1, G-78.3 (STUB), G-87.1 (STUB) |
| Rejet | A-80.1, F-4.1.1 |
| Modification — création | A-88.1, B-88.2 (flags présents) |
| Modification — application | E-88.3, E-90.1, F-4.1.1 |
| Renouvellement — application | D-91.1, D-91.2, F-4.1.1 |
| Radiation — application | E-92.3, F-4.1.1 |
| Recherche publique | A-96.1, B-96.2, F-94.1 |
| Expiration automatique | D-92.4 (commande + transition auto) |
| Tout moment | G-79.1, G-79.2, G-5.2.1, A-global.1 |

---

## 6. Renvois croisés

- Formulaires : [L2.1](L2_1_formulaires_bilingues.md).
- Statuts, transitions, messages : [L2.3](L2_3_matrice_statuts_transitions.md).
- Modèle de données : [L3.1](L3_1_modele_donnees.md).
- Architecture et flux : [L3.2](L3_2_architecture_modulaire.md).
- Horodatage et scellement : [L3.3](L3_3_horodatage_scellement.md).
- Dictionnaire API : [L3.4](L3_4_dictionnaire_api.md).
- Sécurité et intégrité : [L3.5](L3_5_securite_integrite.md).
- Bilinguisme : [L3.6](L3_6_matrice_bilingue.md).
- Traçabilité article par article : [L11](L11_tracabilite_articles_76_97.md).
