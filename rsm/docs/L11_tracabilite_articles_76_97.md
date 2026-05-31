# L11 — Fiche de traçabilité article par article (articles 76 à 97)

**Règle** : Chaque disposition du décret 2021-033 est couverte par au
moins une exigence des TDR et par une fonctionnalité du système. En
retour, chaque fonctionnalité a un fondement explicite dans le texte ou
est identifiée comme **hypothèse de mise en œuvre** (encadré TDR).

Colonnes :

- **Article** — numéro de l'article du décret.
- **Disposition** — résumé opposable de la règle.
- **Section du TDR** — renvoi au document de référence.
- **Couverture système** — modules / fichiers implémentant la règle.
- **État** — IMPLÉMENTÉ / STRUCTUREL / GELÉ / HYPOTHÈSE.

| Art. | Disposition | Section TDR | Couverture système | État |
|------|-------------|-------------|--------------------|------|
| 76 | Finalité du RSM — publicité et opposabilité | § 1.1, 1.2 | `apps.core.enums.NaturesDroitInscrit`, page d'accueil bilingue | IMPLÉMENTÉ |
| 77 | Registre informatisé ; fichier public + fichier général | § 3.1, 6.1, 6.3 | `apps.core.enums.FichierRegistre`, `Inscription.fichier_actuel`, `STATUTS_FICHIER_PUBLIC` | IMPLÉMENTÉ |
| 78 (al. 1) | Canaux de saisie (papier, électronique) | § 4.2.1 | `CanalSaisie`, `Inscription.canal_saisie` | IMPLÉMENTÉ |
| 78 (al. 2) | Ordre d'arrivée | § 4.2.1 | `Inscription.instant_arrivee` (horodatage de réception) | IMPLÉMENTÉ |
| 78 (al. 3) | Prise d'effet à la saisie | § 4.2.1 | `Inscription.instant_saisie_opposable` | STRUCTUREL (GELÉ pour opposabilité) |
| 78 (al. 4) | Numéro d'ordre horodaté à la seconde | § 4.2.1, 5.1 | `SequenceNumeroOrdre`, `horodatage.format_numero_ordre` | STRUCTUREL (GELÉ — source de temps) |
| 79 | Conservation pérenne | § 4.3, 5.1, 5.3 | Override `delete()` + triggers PostgreSQL (journal d'audit) | IMPLÉMENTÉ |
| 80 | Motifs limitatifs de rejet | § 4.2.1, 4.4.1 | `MotifRejet`, `services.prononcer_rejet` | IMPLÉMENTÉ |
| 81 | Renvoi à l'arrêté pour la procédure dématérialisée | Avertissement | Paramétrage via `.env` (ex. `RSM_TIMESOURCE_MODE`) | HYPOTHÈSE |
| 82 | Monopole statistique du greffe | § 4.1, 6.2 | `apps.statistiques`, habilitation `peut_produire_statistiques` | IMPLÉMENTÉ |
| 83 | Contrôle du Président du Tribunal ; réversibilité | § 2.1, 6.3 | Rôle `AUDITEUR`, code intégralement cessible | IMPLÉMENTÉ (structurel) |
| 84 | Voie électronique | § 4.2.1 | Canal `portail_electronique` + portail externe (à câbler sur auth) | STRUCTUREL |
| 85 | Contenu du formulaire d'inscription initiale | § 4.2.1, 4.4.3 | `Inscription` + `Partie` + `BienGreve` + `RoleInscriptionPartie` | IMPLÉMENTÉ |
| 86 | Régime déclaratif | § 4.2.1 (règle cardinale), § 3.2 | Absence de contrôle d'identité / cohérence au fond | IMPLÉMENTÉ (par design) |
| 87 | Prise d'effet à la saisie | § 4.2.1 | `services.valider_inscription` | STRUCTUREL (GELÉ pour opposabilité) |
| 88 | Contenu du formulaire de modification | § 4.2.2 | `DemandeModification` + `DiffModification` (schéma strict) + enum limitative `MotifRefusModification` ; **couverture HTTP** par `tests/test_api_d2_rejet_art88.py` (exposition `motif_refus_code` au serializer vérifiée sur les 7 motifs limitatifs) | IMPLÉMENTÉ |
| 88 (dernier al.) | Modification vidant tout = sans effet | § 4.2.2 | `services._verifier_etat_final` + savepoint + rollback + marquage persistant REJETEE + motif structuré + audit `modification.refuser` → contournement par modifications successives IMPOSSIBLE ; **scénario HTTP bout-en-bout** dans `tests/test_api_d2_rejet_art88.py` | IMPLÉMENTÉ |
| 89 | Modalités pratiques | § 4.2.2 | Formulaire structuré + accords des parties (`accord_createur_confirme` / `accord_constituant_confirme`, vérification cryptographique GELÉE) | STRUCTUREL |
| 90 (al. 1) | Prise d'effet de la modification à la saisie | § 4.2.2 | `DemandeModification.applique_le` | STRUCTUREL (GELÉ pour opposabilité) |
| 90 (al. 2) | Pas d'effet sur la durée (sauf renouvellement) | § 4.2.2 | `CHAMPS_JAMAIS_MODIFIABLES` exclut `duree_en_jours` et `date_expiration` du diff — toute tentative provoque un refus | IMPLÉMENTÉ |
| 91 | Renouvellement avant expiration | § 4.2.3 | `services.appliquer_renouvellement` + `RenouvellementHorsDelai` | IMPLÉMENTÉ |
| 92 (al. 1) | Contenu du bordereau de radiation | § 4.2.4 | `DemandeRadiation` | IMPLÉMENTÉ |
| 92 (al. 2) | Mention « radiée » au fichier public jusqu'à expiration | § 4.2.4, 4.3 | `Inscription.mention_radiee`, statut `RADIEE` | IMPLÉMENTÉ |
| 92 (al. 3) | Transfert au fichier général après expiration | § 4.3 | `commandes.expirer_inscriptions` (statut `ARCHIVEE`) | IMPLÉMENTÉ |
| 93 | Indexation par nom du constituant et par numéro de série | § 6.2 | Index SQL sur `Partie.nom/denomination` et `BienGreve.numero_serie` | IMPLÉMENTÉ |
| 94 | Ouverture à tout intéressé | § 4.2.5 | Endpoint `POST /api/v1/recherche/` avec `AllowAny` | IMPLÉMENTÉ |
| 95 | Canaux de recherche | § 4.2.5 | API en ligne (bordereau physique = saisie par agent) | IMPLÉMENTÉ |
| 96 | Deux critères minimum parmi quatre | § 4.2.5, 10.2 | `services.rechercher` + `NB_MIN_CRITERES=2` | IMPLÉMENTÉ |
| 97 (al. 1) | Résultat exhaustif des homonymes | § 4.2.5 | `homonymes_par_inscription` (art. 97 al. 2) | IMPLÉMENTÉ |
| 97 (al. 2) | Adresse et date de naissance | § 4.2.5 | Champs `adresse`, `date_naissance` dans la réponse | IMPLÉMENTÉ |
| 97 (al. 3) | Certificat de recherche probant | § 4.2.5, 5.1 | `apps.certificats.services.preparer_certificat` (probant=False) | GELÉ |
| 97 (al. 4) | Force probante devant la justice | § 4.2.5 (point critique) | Conditionné au scellement et horodatage officiels | GELÉ |

## Registre des hypothèses

| Réf. | Hypothèse signalée / risque | Portée | Décision attendue |
|------|-----------------------------|--------|-------------------|
| A1 | Arrêté d'application art. 8, 81, 84 non fourni | Paramétrage procédure dématérialisée | Intégration dès publication |
| A2 | Régime signature électronique art. 88 | Canal électronique, accords parties | Choix PKI / alternative |
| A3 | Durée maximale d'inscription art. 85 | Bornes paramétrables | Plafond éventuel |
| A4 | Politique d'indisponibilité, rang chronologique art. 78 al. 2 | Continuité § 5.3 | Procédure documentée |
| A5 | Art. 94 vs art. 97 (copies / certificats) | Unification retenue | Validation MO |
| A6 | Glossaire bilingue juridique | Libellés officiels | Comité de terminologie |
| A7 | Politique tarifaire art. 85 | Module paiement | Définition MO |
| A8 | Cahier des charges art. 83 | Tenue déléguée | Fourniture MO si applicable |
| A9 | Distinction horodatage d'arrivée / horodatage de saisie | Rang chronologique | Politique officielle |
| **parties_reutilisation** | Référencement d'une ``Partie`` existante dans un diff de modification (art. 88) | Réutilisation de parties / recréation systématique | Arbitrage MO : recréation conservatrice OU réutilisation avec périmètre d'accessibilité et politique de désactivation à fixer |

## Registre des risques juridiques (TDR § 9.2)

| # | Risque | Atténuation prévue |
|---|--------|--------------------|
| R1 | Dérive d'horloge non détectée | Source de temps supervisée (GELÉE) |
| R2 | Divergence bilingue | Tests FR/AR systématiques, clés i18n uniques |
| R3 | Incohérence fichier public ↔ certificat de recherche | Instantané transactionnel + scellement (GELÉS) |
| R4 | Indisponibilité et rang | Politique de continuité (GELÉE) |
| R5 | Homonymie mal indexée | Index SQL sur nom/dénomination + tests |
| R6 | Signature électronique non reconnue | Adaptateur pluggable (GELÉ) |
| R7 | Suppression accidentelle dans le journal d'audit | Triggers PostgreSQL + override applicatif |
| R8 | Injection de champs non prévus via l'API | Durcissement global des serializers (`StrictInputMixin` / `StrictInputSerializer` / `StrictModelSerializer`) + tests d'uniformité |
| R9 | Concurrence sur l'attribution du numéro d'ordre (art. 78) | `SELECT … FOR UPDATE` sur `SequenceNumeroOrdre` + test concurrent `TransactionTestCase` avec barrière threading |
| R10 | Défaillance partielle dans `appliquer_modification` laissant un état incohérent | Savepoint isolant + rollback ciblé + tests de robustesse avec injection de défaillance |
| R11 | Contournement des règles métier via l'admin Django (y compris `is_superuser`) — § 4.1 TDR interdit à tout administrateur, fonctionnel ou technique, de créer / modifier / supprimer une inscription | Classes de base centralisées (`apps.core.admin_base`) : `LectureSeuleAdmin` (append-only), `ConsultationMetierAdmin` (métier créé uniquement par service), `EditionRestreinteAdmin` (référentiels + affectations de rôles) ; désactivation uniforme des actions de masse ; `is_superuser` ne contourne rien ; suite de tests `tests/test_admin_lecture_seule.py` |

## Matrice d'habilitation de l'administration Django

Cette matrice formalise, pour chaque famille d'objets, les opérations
autorisées et interdites via l'admin Django, en application du § 4.1
du TDR et de l'article 79.

| Famille d'objets | Modèles | Classe admin | Ajout | Modif. | Suppr. | Actions de masse |
|------------------|---------|--------------|:-:|:-:|:-:|:-:|
| Journal d'audit (art. 79, § 5.2) | `EntreeAudit` | `LectureSeuleAdmin` | ❌ | ❌ | ❌ | ❌ |
| Historique des transitions (§ 4.3) | `TransitionStatut` | `LectureSeuleAdmin` | ❌ | ❌ | ❌ | ❌ |
| Traces de recherches (art. 94-97) | `RequeteRecherche` | `LectureSeuleAdmin` | ❌ | ❌ | ❌ | ❌ |
| Snapshots d'inscription (art. 79) | `SnapshotInscription` | `LectureSeuleAdmin` | ❌ | ❌ | ❌ | ❌ |
| Extractions statistiques (art. 82) | `ExtractionStatistique` | `LectureSeuleAdmin` | ❌ | ❌ | ❌ | ❌ |
| Séquence du n° d'ordre (art. 78) | `SequenceNumeroOrdre` | `LectureSeuleAdmin` | ❌ | ❌ | ❌ | ❌ |
| Inscriptions et objets rattachés (art. 85) | `Inscription`, `RoleInscriptionPartie`, `PieceJointe` | `ConsultationMetierAdmin` | ❌ | ❌ | ❌ | ❌ |
| Parties (art. 85) | `Partie` | `ConsultationMetierAdmin` | ❌ | ❌ | ❌ | ❌ |
| Biens grevés (art. 85, 93) | `BienGreve` | `ConsultationMetierAdmin` | ❌ | ❌ | ❌ | ❌ |
| Demandes M / R / Rad (art. 88, 91, 92) | `DemandeModification`, `DemandeRenouvellement`, `DemandeRadiation` | `ConsultationMetierAdmin` | ❌ | ❌ | ❌ | ❌ |
| Certificats (art. 78, 97) | `Certificat` | `ConsultationMetierAdmin` | ❌ | ❌ | ❌ | ❌ |
| Référentiels bilingues (§ 4.1) | 5 modèles `Libelle…` | `EditionRestreinteAdmin` | ❌ (seeding officiel) | ✅ libellés | ❌ | ❌ |
| Affectations de rôle (§ 4.1, § 5.2) | `AffectationRole` | `EditionRestreinteAdmin` | ✅ | ✅ | ❌ | ❌ |
| Utilisateurs (§ 4.1) | `Utilisateur` | `UserAdmin` + restriction | ✅ | ✅ | ❌ | ❌ |

**Lecture** : ❌ = opération refusée **même pour `is_superuser=True`** ;
✅ = opération autorisée pour les comptes disposant de la permission
Django correspondante.

**Couches de défense en profondeur** :

1. Triggers PostgreSQL (niveau base de données) — journal d'audit.
2. Overrides ORM (`save()`/`delete()`) — modèles append-only et métier.
3. Exception handler DRF — traduction des refus en 403.
4. **Classes de base de l'admin Django** — présent livrable.

Toute tentative d'écriture via l'un ou l'autre chemin est refusée.

## Tests de conformité transverses — Option D

La suite d'intégration API est complétée par trois tests transverses
(Option D) qui démontrent la conformité aux règles cardinales du TDR :

| Test | Règle | Couverture |
|------|-------|-----------|
| [tests/test_api_d1_separation_stricte.py](../backend/tests/test_api_d1_separation_stricte.py) | § 4.1 — séparation stricte saisie / validation | Vérification **au niveau HTTP** sur les 4 opérations soumises à la règle (validation, rejet, application modification, application renouvellement, application radiation) — cohérence globale prouvée. |
| [tests/test_api_d2_rejet_art88.py](../backend/tests/test_api_d2_rejet_art88.py) | Art. 88 dernier alinéa | Scénario HTTP complet (création demande → tentative d'application → refus 400 + `motif_refus_code` exposé → demande REJETEE persistée → ré-application refusée) + exposition uniforme au serializer des 7 motifs limitatifs de `MotifRefusModification`. |
| [tests/test_api_d3_accept_language.py](../backend/tests/test_api_d3_accept_language.py) | § 7.3 TDR — équivalence juridique stricte FR/AR | Preuve HTTP que les clés juridiques neutres (`statut`, `canal_saisie`, `nature_droit`, `motif_rejet`, `article`, `classe`, horodatages, numéros, montants) sont **strictement identiques** entre `Accept-Language: fr` et `Accept-Language: ar` sur : détail d'inscription, liste, recherche publique, rejet, dépôt, référentiels, refus art. 88. |

---

*Version initiale ; chaque livraison incrémentale met à jour la colonne « État » et, le cas échéant, ajoute de nouvelles lignes pour toute hypothèse ou risque identifié.*
