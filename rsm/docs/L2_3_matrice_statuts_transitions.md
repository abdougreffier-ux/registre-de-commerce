# L2.3 — Matrice statuts × transitions × messages système

**Livrable** : L2.3 — partie du livrable L2 (§ 8 du TDR).
**Objet** : vue fonctionnelle consolidée du workflow des inscriptions.
**Fondement** : TDR § 4.3 ; articles 78, 80, 85, 86, 87, 88, 90, 91, 92.
**État** : consolidation. **Aucune règle nouvelle.**

---

## 1. Les 9 statuts d'inscription (§ 4.3 TDR)

Liste **limitative** — cf. [apps/workflow/statuts.py::StatutInscription](../backend/apps/workflow/statuts.py).

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Description fonctionnelle | Fichier |
|------------|---------------------|---------------------|---------------------------|:-------:|
| `recue` | Reçue | مستلمة | Demande enregistrée avec horodatage d'arrivée, sans prise d'effet juridique. | — |
| `en_controle_forme` | En contrôle de forme | قيد مراقبة الشكل | Vérification des motifs limitatifs art. 80 par l'autorité de validation. | — |
| `rejetee` | Rejetée | مرفوضة | Rejet motivé art. 80 notifié ; demande conservée au journal, absente du fichier public. | — |
| `inscrite` | Inscrite (en cours de validité) | مسجّلة (سارية المفعول) | Inscription validée, numéro d'ordre attribué, publique. | PUBLIC |
| `modifiee` | Modifiée | معدّلة | Une ou plusieurs modifications associées ; reste en cours de validité. | PUBLIC |
| `renouvelee` | Renouvelée | مجدَّدة | Période d'effet prorogée d'une durée égale à la durée initiale. | PUBLIC |
| `radiee` | Radiée (en cours de validité) | مشطوبة (سارية المفعول) | Radiation enregistrée ; mention « radiée » ; conservée au fichier public jusqu'à expiration (art. 92 al. 2). | PUBLIC |
| `expiree` | Expirée | منتهية الصلاحية | Date d'expiration atteinte ; sortie du fichier public. | — |
| `archivee` | Archivée (fichier général) | مؤرشفة (الملف العام) | Conservation pérenne (art. 79), sortie du fichier public (art. 92 al. 3). | GENERAL |

**Groupes logiques** (cf. [apps/workflow/statuts.py](../backend/apps/workflow/statuts.py)) :

- `STATUTS_PRE_VALIDATION = {recue, en_controle_forme}`
- `STATUTS_FICHIER_PUBLIC = {inscrite, modifiee, renouvelee, radiee}`
- `STATUTS_EN_COURS_DE_VALIDITE = {inscrite, modifiee, renouvelee}`
- `STATUTS_FICHIER_GENERAL = {archivee}`
- `STATUTS_TERMINAUX = {expiree, archivee, rejetee}`

---

## 2. Les 15 transitions autorisées (§ 4.3 TDR)

Référence technique : [apps/workflow/statuts.py::TRANSITIONS](../backend/apps/workflow/statuts.py).

### 2.1 Vue synthétique

```
                   ┌────────────────────┐
                   │   ➊  Reçue         │
                   └─────────┬──────────┘
                             │  prise_en_charge (auto)
                             ▼
                   ┌────────────────────┐
                   │ ➋ En contrôle      │
                   │   de forme         │
                   └─────┬──────────┬───┘
          rejet_art80   │          │  validation_greffier
                        ▼          ▼
                ┌──────────────┐   ┌────────────────────┐
                │ ➌ Rejetée    │   │ ➍ Inscrite         │
                │ (terminal)   │   └──┬─────────────────┘
                └──────────────┘      │
                                      │ modification_art88 ◄──┐
                                      ▼                       │
                                   ┌────────────┐             │
                                   │ ➎ Modifiée │──────────┐  │
                                   └─────┬──────┘          │  │
                                         │ renouv_art91    │  │
                                         ▼                 │  │
                                   ┌──────────────┐        │  │
                                   │ ➏ Renouvelée │────────┤  │
                                   └──────┬───────┘        │  │
                                          │                │  │
                                          │  radiation_art92 (depuis Inscrite/Modifiée/Renouvelée)
                                          ▼
                                   ┌──────────────┐
                                   │ ➐ Radiée      │
                                   └──────┬───────┘
                                          │ expiration_automatique (auto, depuis tout statut du public)
                                          ▼
                                   ┌──────────────┐
                                   │ ➑ Expirée    │
                                   └──────┬───────┘
                                          │ transfert_fichier_general (auto)
                                          ▼
                                   ┌──────────────┐
                                   │ ➒ Archivée   │
                                   └──────────────┘
```

### 2.2 Tableau consolidé

| # | Depuis | Vers | Événement | Articles | Acteur | Auto | Précondition | Postcondition | Message système (clé) |
|:-:|--------|------|-----------|:--------:|--------|:----:|--------------|---------------|-----------------------|
| T1 | `recue` | `en_controle_forme` | `prise_en_charge` | 78 | système | ✅ | Demande venant d'être reçue | Mise en attente du contrôle de forme | `workflow.transition.prise_en_charge` |
| T2 | `en_controle_forme` | `rejetee` | `rejet_art80` | 80 | AUTORITE_VALIDATION | ❌ | Motif ∈ `MotifRejet` ; séparation stricte § 4.1 | Inscription figée hors fichier public ; `motif_rejet` et `instant_rejet` posés | `workflow.transition.rejet_art80` |
| T3 | `en_controle_forme` | `inscrite` | `validation_greffier` | 78 al. 4, 85, 86 | AUTORITE_VALIDATION | ❌ | Conditions art. 85 réunies ; séparation stricte § 4.1 | Numéro d'ordre attribué ; `instant_saisie_opposable` posé ; date d'expiration calculée | `workflow.transition.validation_greffier` |
| T4 | `inscrite` | `modifiee` | `modification_art88` | 88 | AUTORITE_VALIDATION | ❌ | Accords art. 88 ; diff valide ; état final valide (≥1 constituant, ≥1 créancier, ≥1 bien actifs) | Snapshots avant/après ; durée inchangée | `workflow.transition.modification_art88` |
| T5 | `modifiee` | `modifiee` | `modification_art88` | 88 | AUTORITE_VALIDATION | ❌ | idem T4 | idem T4 | idem |
| T6 | `renouvelee` | `modifiee` | `modification_art88` | 88 | AUTORITE_VALIDATION | ❌ | idem T4 | idem T4 | idem |
| T7 | `inscrite` | `renouvelee` | `renouvellement_art91` | 91 | AUTORITE_VALIDATION | ❌ | Avant expiration ; séparation stricte | `date_expiration += duree_en_jours` (durée initiale) | `workflow.transition.renouvellement_art91` |
| T8 | `modifiee` | `renouvelee` | `renouvellement_art91` | 91 | AUTORITE_VALIDATION | ❌ | idem T7 | idem T7 | idem |
| T9 | `inscrite` | `radiee` | `radiation_art92` | 92 | AUTORITE_VALIDATION | ❌ | Fondement ∈ `FondementRadiation` | `mention_radiee = True` ; inscription reste au fichier public jusqu'à expiration | `workflow.transition.radiation_art92` |
| T10 | `modifiee` | `radiee` | `radiation_art92` | 92 | AUTORITE_VALIDATION | ❌ | idem T9 | idem T9 | idem |
| T11 | `renouvelee` | `radiee` | `radiation_art92` | 92 | AUTORITE_VALIDATION | ❌ | idem T9 | idem T9 | idem |
| T12 | `inscrite` | `expiree` | `expiration_automatique` | 85, 92 | système | ✅ | `date_expiration ≤ aujourd'hui` | Sortie du fichier public | `workflow.transition.expiration_automatique` |
| T13 | `modifiee` | `expiree` | `expiration_automatique` | 85, 92 | système | ✅ | idem T12 | idem T12 | idem |
| T14 | `renouvelee` | `expiree` | `expiration_automatique` | 91 | système | ✅ | idem T12 | idem T12 | idem |
| T15 | `radiee` | `expiree` | `expiration_automatique` | 92 | système | ✅ | idem T12 | idem T12 | idem |
| T16 | `expiree` | `archivee` | `transfert_fichier_general` | 79, 92 al. 3 | système | ✅ | Automatique après T12-T15 | `fichier_actuel = "general"` | `workflow.transition.transfert_fichier_general` |

**Note** : la matrice du code comporte 15 transitions « distinctes » au
sens `(depuis, vers, evenement)` ; le tableau ci-dessus en compte 16
car T5 et T6 correspondent à l'événement `modification_art88` appliqué
à des statuts déjà en cours de validité. Cette redondance documentaire
est volontaire pour la lisibilité fonctionnelle.

---

## 3. Les 4 interdictions explicites (§ 4.3 TDR)

Référence : [apps/workflow/statuts.py::INTERDICTIONS_EXPLICITES](../backend/apps/workflow/statuts.py).

| # | Depuis | Vers | Motif (TDR) | Effet |
|:-:|--------|------|-------------|-------|
| I1 | `radiee` | `inscrite` | Pas de retour en arrière d'une radiation (§ 4.3 TDR). Une réinscription exige une nouvelle inscription. | `TransitionInterdite` → HTTP 400 |
| I2 | `expiree` | `modifiee` | Pas de modification après expiration (art. 90, § 4.3). | idem |
| I3 | `expiree` | `renouvelee` | Pas de renouvellement après expiration (art. 91). | idem |
| I4 | `archivee` | `inscrite` | Pas de sortie du fichier général vers le fichier public. | idem |

**Règle de cohérence globale** : la matrice des transitions autorisées
et l'ensemble des interdictions explicites sont **disjoints** —
vérifié par [tests/test_workflow.py::test_matrice_et_interdictions_disjointes](../backend/tests/test_workflow.py).

**Règle complémentaire** : toute transition non listée dans la matrice
autorisée est refusée par défaut (règle d'admissibilité close). Testé
par `tests/test_workflow.py::test_transition_inconnue_leve_erreur`.

---

## 4. Messages système — catalogue lié aux transitions

### 4.1 Principe

Chaque transition écrit une ligne de `TransitionStatut` (append-only)
et une entrée au journal d'audit. Le message système associé est
**identifié par une clé neutre** ; les libellés FR/AR sont une amorce
à valider par le comité de terminologie (§ 7.3 TDR — zone A6).

### 4.2 Catalogue des messages de transition

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Émis à | Destinataire |
|------------|---------------------|---------------------|--------|--------------|
| `workflow.transition.prise_en_charge` | Demande prise en charge pour contrôle de forme. | تم استلام الطلب لإجراء مراقبة الشكل. | Auditeur + historique inscription | UI greffe + journal |
| `workflow.transition.rejet_art80` | Rejet motivé au titre de l'article 80. | رفض مسبب بموجب المادة 80. | Idem + notification déposant (canal GELÉ) | UI + journal + déposant |
| `workflow.transition.validation_greffier` | Inscription validée, numéro d'ordre attribué. | تم التحقق من التسجيل وإسناد رقم الترتيب. | Idem + certificat d'inscription (structurel, GELÉ pour probant) | UI + journal + déposant |
| `workflow.transition.modification_art88` | Modification appliquée au titre de l'article 88. | تم تطبيق التعديل بموجب المادة 88. | Idem + snapshots avant/après | UI + journal |
| `workflow.transition.renouvellement_art91` | Renouvellement appliqué, période prorogée. | تم تطبيق التجديد وإطالة فترة المفعول. | Idem | UI + journal |
| `workflow.transition.radiation_art92` | Radiation enregistrée, mention « radiée » activée. | تم تسجيل الشطب وتفعيل ذكر « مشطوبة ». | Idem | UI + journal |
| `workflow.transition.expiration_automatique` | Inscription expirée, sortie du fichier public. | انتهت صلاحية التسجيل وخروجه من الملف العمومي. | Idem (acteur null — système) | Journal technique |
| `workflow.transition.transfert_fichier_general` | Transfert au fichier général (art. 92 al. 3). | نقل إلى الملف العام (المادة 92 الفقرة 3). | Idem | Journal technique |

### 4.3 Catalogue des messages de refus

Tous les refus produisent une réponse HTTP structurée (cf. L3.4 § 15)
avec `detail`, `article`, `classe` + clé neutre dédiée.

| Classe d'exception | Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Article |
|--------------------|------------|---------------------|---------------------|:-------:|
| `RejetForme` (canal) | `rejet.art80.canal_non_autorise` | Canal de soumission non autorisé. | قناة الإرسال غير مرخص بها. | 80 |
| `RejetForme` (nature) | `rejet.art76.nature_hors_liste` | Nature de sûreté hors liste limitative. | طبيعة الضمان خارج القائمة الحصرية. | 76 |
| `RejetForme` (motif rejet) | `rejet.art80.motif_hors_liste` | Motif de rejet hors liste art. 80. | سبب الرفض خارج قائمة المادة 80. | 80 |
| `ModificationSansEffet` (ETAT_FINAL_CONSTITUANT_ABSENT) | `modification.refus.etat_final_constituant_absent` | Modification sans effet : plus aucun constituant actif (art. 88). | تعديل بلا أثر: لم يعد هناك منشئ فعّال (المادة 88). | 88 |
| `ModificationSansEffet` (ETAT_FINAL_CREANCIER_ABSENT) | `modification.refus.etat_final_creancier_absent` | Modification sans effet : plus aucun créancier garanti actif. | تعديل بلا أثر: لم يعد هناك دائن مضمون فعّال. | 88 |
| `ModificationSansEffet` (ETAT_FINAL_BIEN_ABSENT) | `modification.refus.etat_final_bien_absent` | Modification sans effet : plus aucun bien grevé actif. | تعديل بلا أثر: لم يعد هناك مال مرهون فعّال. | 88 |
| `ModificationSansEffet` (ACCORDS_MANQUANTS) | `modification.refus.accords_manquants` | Accords du créancier et/ou constituant non confirmés. | موافقات الدائن و/أو المنشئ غير مؤكدة. | 88 |
| `ModificationSansEffet` (STATUT_INSCRIPTION_INCOMPATIBLE) | `modification.refus.statut_incompatible` | Inscription non en cours de validité. | التسجيل ليس ساري المفعول. | § 4.3 |
| `ModificationSansEffet` (DIFF_INVALIDE) | `modification.refus.diff_invalide` | Différentiel non conforme au schéma strict. | الفرق غير مطابق للمخطط الصارم. | 88, 90 al. 2 |
| `ModificationSansEffet` (DIFF_VIDE) | `modification.refus.diff_vide` | Aucune modification effective proposée. | لم يُقترح أي تعديل فعلي. | 88 |
| `ModificationSansEffet` (DEMANDE_NON_APPLICABLE) | `modification.refus.demande_non_applicable` | Demande déjà traitée. | الطلب قد تم بالفعل. | — |
| `RenouvellementHorsDelai` | `renouvellement.refus.hors_delai` | Renouvellement impossible après expiration. | يستحيل التجديد بعد انتهاء الصلاحية. | 91 |
| `TransitionInterdite` | `workflow.refus.transition_interdite` | Transition de statut interdite. | انتقال حالة محظور. | § 4.3 |
| `RechercheCriteresInsuffisants` | `recherche.refus.criteres_insuffisants` | La recherche exige au moins deux critères. | يتطلب البحث معيارين على الأقل. | 96 |
| `AutorisationRefusee` (cumul) | `autorisation.refus.separation_stricte` | Cumul saisie/validation sur la même demande refusé. | يُرفض الجمع بين الإدخال والمصادقة على الطلب ذاته. | § 4.1 |
| `AutorisationRefusee` (rôle) | `autorisation.refus.role_manquant` | Habilitation manquante pour cette opération. | تفويض غير كافٍ لهذه العملية. | § 4.1 |
| `PermissionError` | `integrite.refus.suppression_interdite` | Suppression interdite (article 79). | الحذف محظور (المادة 79). | 79 |

⚠️ Les libellés FR et AR sont des **amorces techniques**. Le glossaire
juridique officiel doit être validé par le comité de terminologie
(TDR § 7.3 — zone A6) avant mise en production.

### 4.4 Catalogue des messages de succès

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Contexte |
|------------|---------------------|---------------------|----------|
| `inscription.depot.succes` | Demande enregistrée ; contrôle de forme en cours. | تم تسجيل الطلب ؛ مراقبة الشكل قيد المعالجة. | Retour POST `/inscriptions/` |
| `inscription.validation.succes` | Inscription validée ; numéro d'ordre attribué. | تم التحقق من التسجيل وإسناد رقم الترتيب. | Retour POST `/valider/` |
| `inscription.rejet.notifie` | Rejet prononcé ; le déposant sera notifié. | صدر الرفض ؛ سيُبلَّغ المودع. | Retour POST `/rejeter/` |
| `modification.application.succes` | Modification appliquée ; snapshots enregistrés. | تم تطبيق التعديل ؛ تم تسجيل اللقطات. | Retour POST `/modifications/<id>/appliquer/` |
| `renouvellement.application.succes` | Renouvellement appliqué. | تم تطبيق التجديد. | Retour POST `/renouvellements/<id>/appliquer/` |
| `radiation.application.succes` | Radiation enregistrée. | تم تسجيل الشطب. | Retour POST `/radiations/<id>/appliquer/` |
| `recherche.resultat` | Résultat de recherche délivré. | تم تقديم نتيجة البحث. | Retour POST `/recherche/` |
| `audit.chaine.integre` | Chaîne d'audit intègre. | سلسلة التدقيق سليمة. | Retour GET `/audit/verification-chaine/` |

### 4.5 Messages dépendant d'arbitrage MO

| Clé neutre | Sujet | Zone |
|------------|-------|------|
| `notification.depot.externe` | Notification par email au déposant après dépôt. | `L11/interconnexions` |
| `notification.rejet.externe` | Notification motivée de rejet. | `L11/interconnexions` |
| `notification.certificat.emission` | Envoi du certificat probant. | `L11/A5` |
| `paiement.demande` | Demande de prépaiement des émoluments. | `L11/A7` |

Ces clés sont **réservées** mais aucun canal n'est câblé tant que le
MO n'a pas arbitré les interconnexions externes et la politique de
certificats probants.

---

## 5. Actions d'audit associées

Chaque transition produit au moins deux entrées au journal d'audit
(cf. L3.5 § 9) :

- une entrée de catégorie métier (`demande`, `validation`, `rejet`…) ;
- une entrée de catégorie transition (clé `transition.<evenement>`).

| Transition | Actions `EntreeAudit.action_cle` typiquement enregistrées |
|------------|-----------------------------------------------------------|
| T1 Reçue → En contrôle de forme | `inscription.deposer` + `transition.prise_en_charge` |
| T2 → Rejetée | `inscription.rejeter` + `transition.rejet_art80` |
| T3 → Inscrite | `inscription.valider` + `transition.validation_greffier` |
| T4/T5/T6 → Modifiée | `modification.appliquer` + `transition.modification_art88` |
| T7/T8 → Renouvelée | `renouvellement.appliquer` + `transition.renouvellement_art91` |
| T9/T10/T11 → Radiée | `radiation.appliquer` + `transition.radiation_art92` |
| T12–T15 → Expirée | `inscription.expirer_archiver` + `transition.expiration_automatique` |
| T16 → Archivée | `transition.transfert_fichier_general` |

En cas de **rejet art. 88** à l'application d'une modification
(échec de contrôle d'état final), l'action supplémentaire
`modification.refuser` est tracée avec `motif_code` structuré, **sans**
entrée `transition.*` (aucune transition de statut de l'inscription
n'a été effective).

---

## 6. Matrice « événement × acteur habilité »

| Événement | AGENT_SAISIE | AUTORITE_VALIDATION | DECLARANT_EXTERNE | Système / auto | Séparation stricte ? |
|-----------|:-:|:-:|:-:|:-:|:-:|
| Création de la demande (`deposer`) | ✅ | ❌ | ✅ | — | — |
| `prise_en_charge` | — | — | — | ✅ | — |
| `rejet_art80` | ❌ | ✅ | ❌ | — | ✅ |
| `validation_greffier` | ❌ | ✅ | ❌ | — | ✅ |
| `modification_art88` (application) | ❌ | ✅ | ❌ | — | ✅ |
| `renouvellement_art91` (application) | ❌ | ✅ | ❌ | — | ✅ |
| `radiation_art92` (application) | ❌ | ✅ | ❌ | — | ✅ |
| `expiration_automatique` | — | — | — | ✅ | — |
| `transfert_fichier_general` | — | — | — | ✅ | — |

Détail des habilitations complètes : [L2.4](L2_4_roles_operations.md)
(prochaine livraison, tour 2).

---

## 7. Invariants de sécurité associés aux transitions

| Invariant | Contrôle |
|-----------|----------|
| Matrice close | Tout `(statut_actuel, statut_cible, evenement)` hors `TRANSITIONS` est refusé par `transition_requise()` |
| Interdictions explicites prioritaires | `est_explicitement_interdite()` est appelée **avant** toute recherche dans la matrice |
| Historisation append-only | `TransitionStatut` : `save()` si `pk` refuse, `delete()` refuse |
| Transaction atomique | `apps.workflow.services.appliquer_transition` décoré `@transaction.atomic` |
| Matrice et interdictions disjointes | Vérifié par test (cf. § 3) |

---

## 8. Durée juridique et transitions automatiques

Les transitions `expiration_automatique` et `transfert_fichier_general`
sont déclenchées par la commande :

```
python manage.py expirer_inscriptions
```

À planifier quotidiennement en exploitation. Pour chaque inscription
dont :
- `statut ∈ STATUTS_FICHIER_PUBLIC` ;
- `date_expiration ≤ aujourd'hui`

le système applique la séquence `T → EXPIREE → ARCHIVEE` (+
bascule `fichier_actuel = "general"`). Acteur : `null` (système).

⚠️ **Zone gelée `L11/horodatage`** : tant que la source de temps
officielle n'est pas arbitrée, la détection s'appuie sur l'horloge
serveur locale. Voir L3.3 pour les modes cibles.

---

## 9. Cohérence avec les tests

| Aspect | Test de référence |
|--------|-------------------|
| Matrice des transitions enregistrée | [tests/test_workflow.py::MatriceTransitionsTests](../backend/tests/test_workflow.py) |
| Interdictions explicites | `test_interdictions_explicites_enregistrees` |
| Disjonction matrice / interdictions | `test_matrice_et_interdictions_disjointes` |
| Application transactionnelle | `test_transition_autorisee_enregistre_historique` |
| Immuabilité de l'historique | `test_historique_immuable` |
| Cycle nominal complet | [tests/test_api_s1_cycle_nominal.py](../backend/tests/test_api_s1_cycle_nominal.py) |
| Transitions interdites | [tests/test_api_s3_transitions_interdites.py](../backend/tests/test_api_s3_transitions_interdites.py) |
| Expiration automatique | Commande `expirer_inscriptions` testée dans S1 et S4 |

---

## 10. Renvois croisés

- Formulaires : [L2.1](L2_1_formulaires_bilingues.md).
- Règles de validation : [L2.2](L2_2_regles_validation.md).
- Rôles × opérations (matrice complète à venir) : [L2.4](L2_4_roles_operations.md).
- Messages système (catalogue détaillé à venir) : [L2.5](L2_5_messages_systeme.md).
- Modèle de données : [L3.1](L3_1_modele_donnees.md).
- Flux métier détaillés : [L3.2](L3_2_architecture_modulaire.md) § 4.
- Horodatage (expiration) : [L3.3](L3_3_horodatage_scellement.md) § 2.
- Dictionnaire API : [L3.4](L3_4_dictionnaire_api.md).
- Sécurité et traçabilité : [L3.5](L3_5_securite_integrite.md).
- Bilinguisme : [L3.6](L3_6_matrice_bilingue.md).
- Traçabilité article par article : [L11](L11_tracabilite_articles_76_97.md).
