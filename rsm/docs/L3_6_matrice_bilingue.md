# L3.6 — Matrice de conformité bilingue FR/AR

**Livrable** : L3.6 — partie du livrable L3 (§ 8 du TDR).
**Objet** : démonstration formelle que chaque règle du décret 2021-033
et du TDR produit **exactement les mêmes effets juridiques** en
français et en arabe, conformément au § 7 du TDR.
**Fondement** : TDR § 6.3, § 7 (bilinguisme obligatoire sans
divergence) ; articles 76 à 97.
**État** : consolidation de l'existant. **Aucune règle nouvelle.**

---

## 1. Principes architecturaux (rappel TDR § 7)

Le TDR pose sept principes dont le respect est vérifié ici :

| Principe § 7 | Mécanisme RSM |
|--------------|---------------|
| 7.1 Parité fonctionnelle totale | Une seule logique de routage, un seul ensemble de routes `/api/v1/*` sans duplication par langue |
| 7.2 Unicité de la logique métier | Services centralisés (`apps.*.services`) sans branche par langue |
| 7.3 Neutralité juridique des langues | Clés limitatives neutres stockées en base ; libellés FR/AR externalisés aux référentiels |
| 7.4 Gestion des données multilingues | Champs classifiés en 3 catégories (neutre / multilingue / dépendant de l'affichage) avec règle `langue_faisant_foi` |
| 7.5 Documents officiels bilingues | `Certificat.langue_generation ∈ {fr, ar, fr-ar}` ; ZONE GELÉE L11/A5 pour la production probante |
| 7.6 Traçabilité indépendante de la langue | `EntreeAudit.action_cle` et `details` stockés en clés neutres |
| 7.7 Tests et acceptation bilingues | Suite de tests couvrant les deux langues (§ 10 ci-dessous) |

---

## 2. Taxonomie stricte des champs

Le TDR (§ 7.4) impose trois catégories. Le système les matérialise sans
ambiguïté.

### 2.1 Champs NEUTRES linguistiquement

Un champ neutre a **une seule représentation** en base, indépendante
de la langue d'accès. Toute restitution dans une interface affiche la
même valeur ; seule la mise en forme typographique et directionnelle
(RTL pour l'arabe) peut varier.

| Catégorie | Exemples | Rationale |
|-----------|----------|-----------|
| Identifiants | `numero_ordre`, `reference_demande`, `id`, `numero_rc` | Valeurs juridiques primaires |
| Dates | `instant_arrivee`, `instant_saisie_opposable`, `date_expiration`, `date_naissance` | ISO-8601 UTC, rendu localisé en présentation |
| Montants | `somme_garantie`, `monnaie` | Decimal + code ISO 4217 |
| Clés d'énumération | `statut`, `canal_saisie`, `nature_droit`, `motif_rejet`, `type_certificat`, `role` | Clés limitatives du décret |
| Identités | `nom`, `prenom`, `denomination_sociale` | Saisies telles qu'énoncées par le déposant (art. 86 — régime déclaratif) |
| Empreintes | `empreinte`, `empreinte_precedente`, `sceau_empreinte` | SHA-256 hex |
| Indicateurs | `actif`, `mention_radiee`, `probant`, `automatique` | Booléens |

### 2.2 Champs MULTILINGUES

Un champ multilingue existe en paire `*_fr` / `*_ar` avec une mention
de la **langue faisant foi** lorsqu'une seule version est renseignée
(§ 7.4). Les deux langues sont stockées conjointement.

| Modèle | Couple de champs | Langue faisant foi |
|--------|------------------|--------------------|
| `BienGreve` | `description_fr`, `description_ar` | `langue_faisant_foi_description` (enum `LangueFaisantFoi`) |
| `DemandeModification` | `objet_modification_fr`, `objet_modification_ar` | Héritée du mixin `DescriptionBilingue` |
| `Inscription` | `commentaire_rejet_fr`, `commentaire_rejet_ar` | — (non obligatoire) |
| `Libelle*` (5 modèles) | `libelle_fr`, `libelle_ar`, `description_fr`, `description_ar` | `langue_faisant_foi` (enum) |

**Invariant** — contrôlé par `apps.core.models.Bilingue.clean()` :

```python
if not (self.libelle_fr or self.libelle_ar):
    raise ValidationError(
        "Au moins une des versions (français ou arabe) doit être renseignée."
    )
```

### 2.3 Champs DÉPENDANTS de l'affichage

Ces champs sont des **libellés résolus à la présentation** à partir
d'une clé neutre. Ils n'apparaissent QUE côté API sortie / UI.

| Exemple API | Champ neutre associé | Source du libellé |
|-------------|----------------------|-------------------|
| `statut_libelle` | `statut` | `get_statut_display()` Django + i18n gettext |
| `canal_saisie_libelle` | `canal_saisie` | idem |
| `nature_droit_libelle` | `nature_droit` | idem |
| `motif_rejet_libelle` | `motif_rejet` | idem |

**Règle** : lorsque deux comptes consultent la même inscription avec
`Accept-Language: fr` ou `Accept-Language: ar`, ils reçoivent
strictement les mêmes valeurs neutres et des libellés résolus dans la
langue demandée. **La substance juridique est identique**.

---

## 3. Énumérations limitatives et correspondance FR/AR

### 3.1 Natures de sûretés et droits (art. 76)

12 valeurs limitatives — [apps/core/enums.py::NaturesDroitInscrit](../backend/apps/core/enums.py).

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) |
|------------|---------------------|---------------------|
| `nant_outillage` | Nantissement de l'outillage, du matériel… | رهن العدة أو المعدات أو المعدات المهنية |
| `nant_droits_associes` | Nantissement des droits d'associés… | رهن حقوق الشركاء… |
| `nant_fonds_commerce` | Nantissement du fonds de commerce | رهن الأصل التجاري |
| `priv_vendeur_fonds` | Privilège du vendeur de fonds de commerce | امتياز بائع الأصل التجاري |
| `nant_stocks` | Nantissement des stocks | رهن المخزونات |
| `priv_tresor` | Privilège du Trésor | امتياز الخزينة العامة |
| `priv_fiscal` | Privilège des services fiscaux | امتياز المصالح الجبائية |
| `priv_douanes` | Privilège de l'administration des douanes | امتياز إدارة الجمارك |
| `priv_prevoyance` | Privilège des organismes de prévoyance sociale | امتياز هيئات الضمان الاجتماعي |
| `nant_creance` | Nantissement de créance | رهن الدين |
| `nant_compte_bancaire` | Nantissement de compte bancaire | رهن الحساب البنكي |
| `nant_pi` | Nantissement des droits de propriété intellectuelle | رهن حقوق الملكية الفكرية |

**Source** : [apps/referentiels/fixtures/natures_droit.json](../backend/apps/referentiels/fixtures/natures_droit.json).

⚠️ Libellés actuels = **amorce technique à valider par le comité de
terminologie juridique** (§ 7.3 TDR — zone A6). La clé neutre, en
revanche, est définitive.

### 3.2 Motifs de rejet (art. 80 — limitatifs)

3 valeurs — [apps/core/enums.py::MotifRejet](../backend/apps/core/enums.py).

| Clé neutre | FR | AR |
|------------|----|----|
| `canal_non_autorise` | Demande soumise par un canal non autorisé (art. 80) | طلب مقدم عبر قناة غير مرخص بها (المادة 80) |
| `informations_illisibles` | Informations illisibles (art. 80) | معلومات غير مقروءة (المادة 80) |
| `informations_incomprehensibles` | Informations incompréhensibles (art. 80) | معلومات غير مفهومة (المادة 80) |

### 3.3 Canaux de saisie (art. 78)

| Clé neutre | FR | AR |
|------------|----|----|
| `guichet_papier` | Bordereau papier au guichet (art. 78) | كشف ورقي عند الشباك (المادة 78) |
| `portail_electronique` | Voie électronique (art. 78) | الوسيلة الإلكترونية (المادة 78) |

### 3.4 Critères de recherche (art. 96 — limitatifs)

4 valeurs — [apps/core/enums.py::CritereRecherche](../backend/apps/core/enums.py).

| Clé neutre | FR | AR |
|------------|----|----|
| `nom_constituant` | Nom et prénom ou dénomination sociale du constituant (art. 96) | الاسم واللقب أو التسمية الاجتماعية للمنشئ (المادة 96) |
| `numero_rc` | Numéro d'immatriculation au registre du commerce (art. 96) | رقم التسجيل في السجل التجاري (المادة 96) |
| `numero_serie_bien` | Numéro de série du bien (art. 96) | الرقم التسلسلي للمال (المادة 96) |
| `numero_inscription` | Numéro de l'inscription initiale ou de la modification (art. 96) | رقم التسجيل الأولي أو التعديل (المادة 96) |

### 3.5 Types de certificats

5 valeurs — [apps/core/enums.py::TypeCertificat](../backend/apps/core/enums.py).

### 3.6 Statuts d'inscription (§ 4.3)

9 valeurs — [apps/workflow/statuts.py::StatutInscription](../backend/apps/workflow/statuts.py).

| Clé neutre | FR | AR (clé i18n) |
|------------|----|---------------|
| `recue` | Reçue | `inscription.statut.recue` |
| `en_controle_forme` | En contrôle de forme | `inscription.statut.en_controle_forme` |
| `rejetee` | Rejetée | `inscription.statut.rejetee` |
| `inscrite` | Inscrite (en cours de validité) | `inscription.statut.inscrite` |
| `modifiee` | Modifiée | `inscription.statut.modifiee` |
| `renouvelee` | Renouvelée | `inscription.statut.renouvelee` |
| `radiee` | Radiée (en cours de validité) | `inscription.statut.radiee` |
| `expiree` | Expirée | `inscription.statut.expiree` |
| `archivee` | Archivée (fichier général) | `inscription.statut.archivee` |

**Source traductions frontend** :
[rsm/frontend/src/i18n/fr.json](../frontend/src/i18n/fr.json),
[rsm/frontend/src/i18n/ar.json](../frontend/src/i18n/ar.json).

### 3.7 Rôles applicatifs (§ 4.1)

7 rôles — [apps/utilisateurs/models.py::RoleApplicatif](../backend/apps/utilisateurs/models.py).

### 3.8 Motifs de refus de modification (art. 88)

8 motifs — [apps/modifications/models.py::MotifRefusModification](../backend/apps/modifications/models.py).

### 3.9 Catégories d'audit (§ 5.2)

11 catégories — [apps/audit/models.py::CategorieAudit](../backend/apps/audit/models.py).

**Invariant de cohérence globale** : pour chacune de ces 9
énumérations, l'ensemble des clés en base doit correspondre
EXACTEMENT à l'ensemble des valeurs de l'enum Python. Vérifié par la
commande `seed_referentiels` et par les tests
`test_referentiels.py::SeedReferentielsTests::test_couverture_exacte_des_enums`.

---

## 4. Matrice par chapitre du TDR

| Chapitre / article | Exigence bilingue | Mécanisme RSM | Test d'équivalence |
|--------------------|-------------------|---------------|---------------------|
| Art. 76 — Finalité | Liste limitative identique FR/AR | Enum `NaturesDroitInscrit` + référentiel `LibelleNatureDroit` | `test_seed_est_idempotent`, `test_couverture_exacte_des_enums` |
| Art. 78 — Canal, n° d'ordre | Numéro neutre ; format identique | `format_numero_ordre()` + `CanalSaisie` | `test_attributions_concurrentes_toutes_uniques` (format identique) |
| Art. 80 — Motifs de rejet | Motifs limitatifs identiques FR/AR | Enum `MotifRejet` + fixture bilingue | `test_rejet_motif_limitatif_accepte` |
| Art. 85 — Contenu d'inscription | Champs neutres ; descriptions bilingues | Modèles `Inscription`, `Partie`, `BienGreve` | `test_cycle_nominal_complet` (S1) |
| Art. 86 — Régime déclaratif | Pas de contrôle de fond (aucune différence FR/AR) | Absence volontaire de vérification | implicite dans chaque test de rejet art. 80 |
| Art. 88 — Modification | Diff schéma strict neutre ; motifs limitatifs FR/AR | `DiffModification` + `MotifRefusModification` | `test_rejet_pour_diff_invalide_trace`, `ControleEtatFinalTests` |
| Art. 91 — Renouvellement | Règle de délai identique FR/AR | Service unique `appliquer_renouvellement` | `test_renouvellement_apres_expiration_refuse` (S3) |
| Art. 92 — Radiation | Mention « radiée » gérée par flag neutre | `Inscription.mention_radiee` + libellés i18n | `test_inscription_radiee_visible_au_fichier_public` (S4) |
| Art. 94 — Ouverture publique | Endpoint unique accessible FR/AR | `RecherchePublique` + `AllowAny` | `test_recherche_deux_criteres_ouverte_sans_auth` (S4) |
| Art. 96 — 4 critères limitatifs | Clés neutres, libellés bilingues | `_CriteresSerializer` strict | `test_recherche_un_seul_critere_refusee`, `test_critere_hors_liste_refuse_par_l_api` |
| Art. 97 al. 2 — Homonymes | Résultat exhaustif identique | Service `rechercher()` | `test_homonymes_constituants_retournes_en_totalite` (S4) |
| § 4.1 — Rôles | Rôles limitatifs identiques FR/AR | Enum `RoleApplicatif` + habilitations | `test_meme_utilisateur_ne_peut_valider_sa_propre_demande` |
| § 4.3 — Transitions | Matrice unique FR/AR | `TRANSITIONS` / `INTERDICTIONS_EXPLICITES` | `test_interdictions_explicites_enregistrees` |
| § 5.2 — Audit | Clés d'action neutres | `EntreeAudit.action_cle` + tests | `test_independance_linguistique_stockage` |

---

## 5. Langue faisant foi — règles

### 5.1 Enum `LangueFaisantFoi`

[apps/core/models.py::LangueFaisantFoi](../backend/apps/core/models.py) :

| Valeur | Sens |
|--------|------|
| `fr` | Seule la version française est renseignée ; elle prévaut. |
| `ar` | Seule la version arabe est renseignée ; elle prévaut. |
| `equ` | Les deux versions sont réputées équivalentes (traduction validée par le comité). |

### 5.2 Portée

- **Référentiels** : chaque libellé officiel porte un `langue_faisant_foi`. La commande `seed_referentiels` positionne `equ` par défaut, à valider par le comité de terminologie (§ 7.3 TDR — zone A6).
- **Descriptions de biens** : la partie renseignée librement ; la langue faisant foi est déclarée par le déposant (régime déclaratif art. 86).
- **Commentaires de rejet** : pas de `langue_faisant_foi` obligatoire ; les deux langues sont simplement préservées côte à côte.

### 5.3 Affichage

Lorsqu'un champ bilingue n'existe que dans une seule langue et que
l'utilisateur consulte dans l'autre, **l'interface doit** :

1. Afficher la version disponible.
2. Mentionner explicitement la langue faisant foi (badge « langue faisant foi : français » / « اللغة المعتمدة : العربية »).

**Règle stricte** : **jamais** de traduction inventée par le système.
Cf. `apps.core.models.Bilingue.libelle(langue)` — retourne la version
disponible sans traduction automatique.

---

## 6. Documents officiels bilingues (§ 7.5)

**État** : STRUCTUREL — **ZONE GELÉE L11/A5** pour la production probante.

| Certificat | Langues possibles | Mécanisme |
|------------|-------------------|-----------|
| Inscription (art. 78, 86) | `fr`, `ar`, `fr-ar` | `Certificat.langue_generation` |
| Modification (art. 88-90) | idem | idem |
| Renouvellement (art. 91) | idem | idem |
| Radiation (art. 92) | idem | idem |
| Recherche (art. 97) | idem | idem |

**Contrat bilingue** : lorsque `langue_generation="fr-ar"`, le certificat
présente les deux textes côte à côte. **L'équivalence juridique entre
les deux textes est la règle** : ils expriment exactement les mêmes
faits (numéro d'ordre, horodatage, parties, biens, durée, date
d'expiration…).

Le rendu PDF/A signé et l'activation de la force probante sont
**GELÉS** en attente d'arbitrage MO (cf. L3.3 § 4.3 — modes cibles).

---

## 7. Trace d'audit — indépendance linguistique (§ 7.6)

Le journal d'audit est stocké **exclusivement en clés neutres** :

| Champ | Exemple de valeur |
|-------|-------------------|
| `action_cle` | `inscription.deposer`, `modification.refuser`, `transition.validation_greffier` |
| `categorie` | `demande`, `validation`, `rejet`, `certificat`, `recherche`, … |
| `resultat` | `succes`, `echec`, `rejet`, `refus_autorisation` |
| `objet_type` | `inscription`, `modification`, `demande_modification`, `recherche` |
| `details` | JSON neutre, clés latines (ex. `{"motif_code": "etat_final_bien_absent", "diff_resume": {…}}`) |

**Règle** : les valeurs de `details` qui proviennent d'une saisie
utilisateur (commentaires, descriptions) sont stockées **telles quelles**
(FR et/ou AR) sans traduction. Un auditeur consulte la trace dans la
langue qu'il préfère sans altération des faits.

**Test** : [tests/test_audit.py::test_independance_linguistique_stockage](../backend/tests/test_audit.py).

---

## 8. Direction d'écriture (LTR / RTL)

### 8.1 Backend — templates

`<html lang="{{ LANGUE }}" dir="{% if LANGUE == 'ar' %}rtl{% else %}ltr{% endif %}">` — cf.
[backend/templates/base.html](../backend/templates/base.html).

### 8.2 Frontend — React

```js
// src/i18n/index.js
i18n.on('languageChanged', (langue) => {
  localStorage.setItem('rsm.langue', langue);
  appliquerDirection(langue);  // pose dir="rtl" ou "ltr" sur <html>
});
```

### 8.3 CSS

`rsm/backend/static/rsm/base.css` utilise les propriétés logiques
(`margin-inline-start`, `border-inline-start`, etc.) — aucune règle
`left:` / `right:` en dur, aucune direction codée.

### 8.4 Interface Ant Design

La bascule RTL d'Ant Design se fait par `ConfigProvider direction="rtl"`
(à câbler dans le futur `App.jsx` à l'initialisation i18n ; le composant
[src/components/Layout.jsx](../frontend/src/components/Layout.jsx)
exploitera ce mécanisme).

---

## 9. Tests et recette bilingues (§ 7.7)

**Règle TDR § 7.7** : tous les tests fonctionnels et juridiques sont
exécutés dans les deux langues.

### 9.1 Tests neutres (valeurs identiques FR/AR)

La majorité des tests unitaires et d'intégration portent sur des clés
neutres : leur résultat est **identique quelle que soit la langue** par
construction. Ces tests couvrent :

- règles métier (`tests/test_regles_metier.py`) ;
- workflow et transitions (`tests/test_workflow.py`) ;
- modifications et anti-contournement (`tests/test_modifications_cas_limites.py`) ;
- concurrence et robustesse (`tests/test_concurrence_art78.py`, `tests/test_robustesse_transactionnelle.py`) ;
- cycle de vie API (`tests/test_api_s1_cycle_nominal.py` à S6) ;
- admin (`tests/test_admin_lecture_seule.py`).

**Démonstration** : les résultats de ces tests sont indépendants de
l'`Accept-Language` puisque les décisions reposent sur des clés
neutres. Toute régression qui dépendrait de la langue serait visible
dès la première exécution.

### 9.2 Tests explicitement bilingues

- [tests/test_referentiels.py::BilinguismePairesTests](../backend/tests/test_referentiels.py) — vérifie que, pour chaque référentiel, les libellés FR et AR sont tous deux renseignés après `seed_referentiels`, et que `Bilingue.libelle('fr')` et `Bilingue.libelle('ar')` retournent des versions distinctes non vides.
- [tests/test_api_s2_rejet_art80.py::test_rejet_motif_limitatif_accepte](../backend/tests/test_api_s2_rejet_art80.py) — préserve les commentaires FR et AR tels que fournis.
- Scénarios S4, S6 incluent des chaînes arabes (descriptions, objets de modification) — vérifient que l'écriture RTL traverse l'API sans altération.

### 9.3 Équivalence juridique (principe) — vérification par construction

Le TDR § 7.3 impose que **les versions française et arabe produisent
les mêmes effets juridiques**. La vérification repose sur l'architecture :

- Le moteur de règles est unique (clés neutres uniquement).
- Les statuts, transitions, motifs de refus, natures, critères sont
  stockés par clé neutre : une règle métier ne peut pas produire un
  résultat différent en FR et en AR.
- Les libellés FR/AR ne sont que des rendus d'affichage : ils ne
  modifient aucune décision de service.

**Corollaire** : toute occurrence d'une chaîne FR ou AR en dur dans un
service métier constituerait une violation structurelle du bilinguisme.
Les revues de code doivent le refuser.

---

## 10. Tableau récapitulatif — règle par règle, preuve par preuve

| Règle juridique (article / § TDR) | Clé neutre | Libellés FR/AR | Test(s) d'équivalence |
|-----------------------------------|------------|----------------|-----------------------|
| Art. 76 — Natures limitatives | `NaturesDroitInscrit` | `LibelleNatureDroit` | `test_couverture_exacte_des_enums` |
| Art. 78 — Canaux de saisie | `CanalSaisie` | `LibelleCanalSaisie` | idem |
| Art. 78 al. 4 — Format n° d'ordre | `format_numero_ordre` | — (neutre) | `test_chronologie_coherente_avec_le_numero` |
| Art. 79 — Conservation | `delete()` refusé partout | — | `ConservationIntegraleTests` |
| Art. 80 — Motifs limitatifs | `MotifRejet` | `LibelleMotifRejet` | `test_motif_rejet_hors_liste_refuse`, `test_rejet_motif_limitatif_accepte` |
| Art. 82 — Monopole statistiques | `RoleApplicatif.PROD_STATS` | — | `test_monopole_statistiques` |
| Art. 85 — Champs non bloquants | (structure) | — | `test_champs_bien_grevé_optionnels_non_bloquants` |
| Art. 86 — Régime déclaratif | (absence de contrôle) | — | `test_rejet_motif_hors_liste_refuse` (négatif) |
| Art. 88 dernier al. — Effet utile | `MotifRefusModification.*ABSENT*` | Libellés de l'enum | `ControleEtatFinalTests` (4 tests) + `AntiContournementParSuccessionTests` |
| Art. 90 al. 2 — Durée | `CHAMPS_JAMAIS_MODIFIABLES` | — | `test_modification_durée_ou_date_expiration_refusee` |
| Art. 91 — Avant expiration | (service + exception) | — | `test_renouvellement_apres_expiration_refuse`, `test_renouvellement_proroge_de_duree_initiale` |
| Art. 92 al. 2 — Mention radiée | `Inscription.mention_radiee` | `inscription.statut.radiee` i18n | `test_radiation_active_mention_et_statut`, `test_inscription_radiee_visible_au_fichier_public` |
| Art. 92 al. 3 — Transfert fichier général | Command `expirer_inscriptions` | — | `test_inscription_archivee_invisible_au_fichier_public` |
| Art. 94 — Ouverture publique | `permissions.AllowAny` | — | `test_recherche_deux_criteres_ouverte_sans_auth` |
| Art. 96 — 2 critères minimum | `NB_MIN_CRITERES` + `CritereRecherche` | `LibelleCritereRecherche` | `test_recherche_un_seul_critere_refusee`, `test_critere_hors_liste_refuse_par_l_api` |
| Art. 97 al. 2 — Homonymes exhaustifs | `homonymes_par_inscription` | — | `test_homonymes_constituants_retournes_en_totalite` |
| § 4.1 — Séparation stricte | `peut_valider_demande(acteur, saisie_par)` | — | `test_meme_utilisateur_ne_peut_valider_sa_propre_demande` |
| § 4.3 — Matrice transitions | `TRANSITIONS`, `INTERDICTIONS_EXPLICITES` | `inscription.statut.*` i18n | `MatriceTransitionsTests`, `ApplicationTransitionsTests` |
| § 5.2 — Audit immuable | `EntreeAudit` + triggers | `action_cle` neutre | `JournalAuditTests`, `AuditConcurrent_Tests` |
| § 7 — Bilinguisme | Taxonomie 3 catégories | Tous les `Libelle*` | `BilinguismePairesTests` |

**Couverture** : chaque règle juridique matérialisée dans le code est
adossée à au moins un test dont le résultat ne peut pas dépendre de
la langue. Réciproquement, chaque libellé bilingue est adossé à un
référentiel dont la couverture par rapport à l'enum du décret est
testée.

---

## 11. Points de vigilance et zones gelées bilingues

| Zone | Impact bilinguisme | État |
|------|---------------------|------|
| Glossaire juridique officiel FR/AR | Les libellés des référentiels sont une AMORCE ; la version opposable doit être validée par le comité (§ 7.3 TDR). | GELÉ — `A6` |
| Rendu PDF bilingue des certificats (§ 7.5) | Format PDF/A, mise en page côte à côte, intégration des fonts arabes et latines. | GELÉ — `A5` |
| Ant Design RTL | La bascule `ConfigProvider direction="rtl"` doit être câblée au futur travail frontend. | À traiter lorsque Option B sera engagée |
| Pluralisation et mise en forme nombres | Non câblée — dépend du glossaire et des conventions MO. | À arbitrer |

---

## 12. Tests complémentaires à envisager (sans levée d'arbitrage)

Sans lever aucune zone gelée, la couverture bilingue peut être encore
renforcée par :

1. Un test paramétré exécutant chaque scénario d'intégration API avec
   `Accept-Language: fr` puis `Accept-Language: ar`, comparant que les
   clés neutres renvoyées sont strictement identiques (les libellés
   résolus pouvant différer).
2. Un test vérifiant que tous les libellés du référentiel `Libelle*`
   pour lesquels `langue_faisant_foi = equ` ont bien deux versions non
   vides — garantit que le comité a validé les deux langues avant mise
   en production.
3. Un test garantissant que l'exception handler DRF ne génère aucun
   message en dur dans une seule langue (actuellement les messages
   d'erreur incluent des formulations françaises — à raffiner par
   passage par i18n).

Ces tests sont proposés pour **Option D** (tests d'intégration
complémentaires), sans aucun impact sur le cadre MO actuel.

---

## 13. Synthèse finale — démonstration d'équivalence juridique

Le système RSM est bilingue **par construction structurelle**, non par
duplication. L'équivalence juridique FR/AR repose sur trois piliers :

1. **Un seul modèle de données.** Les champs neutres stockent la
   substance juridique (clés, numéros, dates, identités, montants).
   Aucune branche FR / AR dans les modèles.
2. **Un seul moteur de règles.** Tous les services métier prennent des
   clés neutres en entrée et produisent des clés neutres en sortie.
   Aucun test `if langue == 'fr' …` ne figure dans un service.
3. **Des libellés externalisés.** Les libellés FR/AR sont confinés aux
   référentiels, aux fichiers `.po` / `.json` et aux templates. Ils
   n'influencent aucune décision juridique.

Conséquence : **toute règle du décret 2021-033 produit strictement les
mêmes effets en français et en arabe**, par impossibilité
architecturale de produire un résultat divergent. Les tests
consolidés dans le tableau § 10 prouvent cette équivalence pour
l'ensemble des articles 76 à 97 et des chapitres transverses du TDR.

---

## 14. Renvois croisés

- Modèle de données : [L3.1](L3_1_modele_donnees.md).
- Architecture et bilinguisme architectural : [L3.2](L3_2_architecture_modulaire.md) § 7.
- Horodatage et scellement (zones gelées) : [L3.3](L3_3_horodatage_scellement.md).
- Dictionnaire API et matrice bilinguisme par endpoint : [L3.4](L3_4_dictionnaire_api.md) § 14.
- Sécurité et intégrité : [L3.5](L3_5_securite_integrite.md).
- Traçabilité article par article + zone d'arbitrage A6 (glossaire) : [L11](L11_tracabilite_articles_76_97.md).
