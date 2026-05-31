# L2.5 — Cartographie des messages système

**Livrable** : L2.5 — partie du livrable L2 (§ 8 du TDR).
**Objet** : catalogue consolidé des messages système identifiés par
clés neutres, avec amorces bilingues FR/AR.
**Fondement** : TDR § 4, § 7 ; articles 76 à 97.
**État** : consolidation. **Aucune règle nouvelle.**

---

## 1. Principes directeurs

### 1.1 Identification par clé neutre

Chaque message système est identifié par une **clé neutre
linguistiquement** qui :
- est stable (n'est jamais renommée une fois validée) ;
- structure la navigation : `<domaine>.<action>.<resultat>` ou
  `<domaine>.<type>.<details>` ;
- apparaît telle quelle dans le journal d'audit (§ 7.6 TDR).

### 1.2 Libellés FR/AR — amorces à valider

Les colonnes « Libellé FR » et « Libellé AR » ci-dessous sont des
**amorces techniques**. Elles doivent être validées par le comité de
terminologie juridique avant mise en production (§ 7.3 TDR — zone
d'arbitrage A6).

### 1.3 Équivalence juridique stricte (§ 7.3)

Deux amorces FR et AR ayant la même clé neutre produisent **le même
effet juridique**. Cette équivalence est vérifiée par les tests
`tests/test_api_d3_accept_language.py` — cf. L3.6.

### 1.4 Canaux d'émission

| Canal | Rôle | État |
|-------|:----:|------|
| UI (templates + React) | Affichage utilisateur | Actif |
| API / handler d'exceptions | Corps de réponse HTTP | Actif |
| Journal d'audit | Traçabilité interne | Actif |
| Notification externe (email, SMS, portail) | Information du déposant | ⚠️ GELÉ — zone `L11/interconnexions` |

Aucune notification externe n'est câblée tant que l'arbitrage MO sur
les canaux de notification n'est pas rendu.

### 1.5 Taxonomie

Les messages sont répartis en 8 familles :

1. **Action — Succès** (§ 4)
2. **Action — Rejet art. 80** (motifs limitatifs)
3. **Action — Refus art. 88** (motifs limitatifs de modification)
4. **Action — Refus métier** (renouvellement, transitions interdites, recherche)
5. **Action — Refus d'autorisation** (§ 4.1)
6. **Intégrité et immuabilité** (art. 79, § 5.2)
7. **Transitions de statut** (§ 4.3 — cf. L2.3 § 4)
8. **Système et exploitation** (§ 5.3, zones gelées)

---

## 2. Famille 1 — Messages de succès

Émis en retour d'une opération réussie. Canal principal : UI + journal d'audit.

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Émis par | Article |
|------------|---------------------|---------------------|----------|:-------:|
| `inscription.depot.succes` | Demande enregistrée ; contrôle de forme en cours. | تم تسجيل الطلب ؛ مراقبة الشكل قيد المعالجة. | POST `/inscriptions/` | 85 |
| `inscription.validation.succes` | Inscription validée ; numéro d'ordre attribué. | تم التحقق من التسجيل وإسناد رقم الترتيب. | POST `/valider/` | 87 |
| `inscription.rejet.notifie` | Rejet prononcé ; le déposant sera notifié. | صدر الرفض ؛ سيُبلَّغ المودع. | POST `/rejeter/` | 80 |
| `modification.depot.succes` | Demande de modification enregistrée. | تم تسجيل طلب التعديل. | POST `/modifications/` | 88 |
| `modification.application.succes` | Modification appliquée ; snapshots enregistrés. | تم تطبيق التعديل ؛ تم تسجيل اللقطات. | POST `/modifications/<id>/appliquer/` | 88, 90 |
| `renouvellement.depot.succes` | Demande de renouvellement enregistrée. | تم تسجيل طلب التجديد. | POST `/renouvellements/` | 91 |
| `renouvellement.application.succes` | Renouvellement appliqué ; période prorogée. | تم تطبيق التجديد وإطالة الفترة. | POST `/renouvellements/<id>/appliquer/` | 91 |
| `radiation.depot.succes` | Demande de radiation enregistrée. | تم تسجيل طلب الشطب. | POST `/radiations/` | 92 |
| `radiation.application.succes` | Radiation enregistrée ; mention « radiée » activée. | تم تسجيل الشطب ؛ تفعيل ذكر « مشطوبة ». | POST `/radiations/<id>/appliquer/` | 92 al. 2 |
| `recherche.resultat.delivre` | Résultat de recherche délivré (aperçu non opposable). | تم تقديم نتيجة البحث (معاينة غير قابلة للاحتجاج). | POST `/recherche/` | 94, 96, 97 |
| `statistiques.extraction.succes` | Extraction statistique produite. | تم إنتاج الاستخراج الإحصائي. | POST `/statistiques/produire/` | 82 |
| `audit.chaine.integre` | Chaîne d'audit intègre. | سلسلة التدقيق سليمة. | GET `/audit/verification-chaine/` | § 5.2 |
| `affectation.creation.succes` | Affectation de rôle enregistrée. | تم تسجيل إسناد الدور. | Admin | § 4.1 |
| `affectation.revocation.succes` | Affectation de rôle révoquée. | تم إبطال إسناد الدور. | Admin | § 4.1 |
| `referentiels.seed.succes` | Référentiels bilingues chargés. | تم تحميل المراجع ثنائية اللغة. | Commande `seed_referentiels` | § 7.3 |
| `inscription.expiration.succes` | Inscription expirée et archivée. | انتهت صلاحية التسجيل وتمت أرشفته. | Commande `expirer_inscriptions` | 85, 92 al. 3 |

---

## 3. Famille 2 — Rejet motivé (art. 80)

Motifs **LIMITATIFS** prévus par l'article 80. Clé neutre identifiant
le motif structuré. Canal : HTTP 400 + journal d'audit + notification
externe GELÉE.

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Article |
|------------|---------------------|---------------------|:-------:|
| `rejet.art80.canal_non_autorise` | Canal de soumission non autorisé. | قناة الإرسال غير مرخص بها. | 80 |
| `rejet.art80.informations_illisibles` | Informations illisibles. | معلومات غير مقروءة. | 80 |
| `rejet.art80.informations_incomprehensibles` | Informations incompréhensibles. | معلومات غير مفهومة. | 80 |
| `rejet.art76.nature_hors_liste` | Nature de sûreté hors liste limitative. | طبيعة الضمان خارج القائمة الحصرية. | 76 |
| `rejet.art80.motif_hors_liste` | Motif de rejet hors liste art. 80. | سبب الرفض خارج قائمة المادة 80. | 80 |

---

## 4. Famille 3 — Refus d'application d'une modification (art. 88)

Motifs **LIMITATIFS** énumérés par `MotifRefusModification` (L3.1 § 2.9).
Clé neutre identique au code. Canal : HTTP 400 + journal
(`modification.refuser`) + marquage persistant `REJETEE`.

| Clé neutre (`MotifRefusModification`) | Libellé FR (amorce) | Libellé AR (amorce) | Article |
|---------------------------------------|---------------------|---------------------|:-------:|
| `etat_final_constituant_absent` | Modification sans effet : plus aucun constituant actif. | تعديل بلا أثر: لم يعد هناك منشئ فعّال. | 88 al. 4 |
| `etat_final_creancier_absent` | Modification sans effet : plus aucun créancier garanti actif. | تعديل بلا أثر: لم يعد هناك دائن مضمون فعّال. | 88 al. 4 |
| `etat_final_bien_absent` | Modification sans effet : plus aucun bien grevé actif. | تعديل بلا أثر: لم يعد هناك مال مرهون فعّال. | 88 al. 4 |
| `accords_manquants` | Accords du créancier et/ou du constituant non confirmés. | موافقات الدائن و/أو المنشئ غير مؤكدة. | 88 |
| `statut_inscription_incompatible` | Inscription non en cours de validité. | التسجيل ليس ساري المفعول. | § 4.3 |
| `diff_invalide` | Différentiel non conforme au schéma strict. | الفرق غير مطابق للمخطط الصارم. | 88, 90 al. 2 |
| `diff_vide` | Aucune modification effective proposée. | لم يُقترح أي تعديل فعلي. | 88 |
| `demande_non_applicable` | Demande déjà traitée (appliquée ou rejetée). | الطلب قد تم معالجته بالفعل. | — |

---

## 5. Famille 4 — Refus métier (renouvellement, transitions, recherche)

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Article | Exception levée |
|------------|---------------------|---------------------|:-------:|-----------------|
| `renouvellement.refus.hors_delai` | Renouvellement impossible après expiration. | يستحيل التجديد بعد انتهاء الصلاحية. | 91 | `RenouvellementHorsDelai` |
| `renouvellement.refus.inscription_non_active` | L'inscription n'est plus en cours de validité. | التسجيل لم يعد ساري المفعول. | § 4.3 | `RenouvellementHorsDelai` / `TransitionInterdite` |
| `radiation.refus.inscription_non_active` | Radiation impossible : inscription non en cours. | يستحيل الشطب: التسجيل ليس ساري المفعول. | 92 | `TransitionInterdite` |
| `workflow.refus.transition_interdite` | Transition de statut interdite. | انتقال حالة محظور. | § 4.3 | `TransitionInterdite` |
| `workflow.refus.transition_inconnue` | Événement de transition inconnu. | حدث انتقال غير معروف. | § 4.3 | `LookupError` → `TransitionInterdite` |
| `recherche.refus.criteres_insuffisants` | La recherche exige au moins deux critères. | يتطلب البحث معيارين على الأقل. | 96 | `RechercheCriteresInsuffisants` |
| `recherche.refus.critere_hors_liste` | Critère hors liste limitative art. 96. | معيار خارج قائمة المادة 96 الحصرية. | 96 | `ValidationError` (serializer strict) |

---

## 6. Famille 5 — Refus d'autorisation (§ 4.1)

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Article | Exception levée |
|------------|---------------------|---------------------|:-------:|-----------------|
| `autorisation.refus.non_authentifie` | Authentification requise. | المصادقة مطلوبة. | § 5.1 | `NotAuthenticated` (DRF) |
| `autorisation.refus.role_manquant` | Habilitation manquante pour cette opération. | تفويض غير كافٍ لهذه العملية. | § 4.1 | `AutorisationRefusee` |
| `autorisation.refus.separation_stricte` | Cumul saisie/validation sur la même demande refusé. | يُرفض الجمع بين الإدخال والمصادقة على الطلب ذاته. | § 4.1 | `AutorisationRefusee` |
| `autorisation.refus.monopole_statistiques` | Production statistique refusée : monopole du greffe. | إنتاج الإحصائيات مرفوض: احتكار الكتابة. | 82 | `AutorisationRefusee` |
| `autorisation.refus.non_auditeur` | Accès au journal d'audit réservé à l'auditeur. | الوصول إلى سجل التدقيق مقتصر على المراقب. | § 4.1 | `PermissionDenied` (DRF) |
| `autorisation.refus.ecriture_metier_admin` | Les administrateurs n'ont pas d'écriture métier. | المسؤولون ليس لهم صلاحية الكتابة المهنية. | § 4.1 | `AutorisationRefusee` |

---

## 7. Famille 6 — Intégrité et immuabilité (art. 79, § 5.2)

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Article | Déclencheur |
|------------|---------------------|---------------------|:-------:|-------------|
| `integrite.refus.suppression_interdite` | Suppression interdite (article 79). | الحذف محظور (المادة 79). | 79 | `save()` sur append-only, `delete()` |
| `integrite.refus.modification_journal_audit` | Le journal d'audit est append-only. | سجل التدقيق غير قابل للتعديل. | 79, § 5.2 | Tentative UPDATE sur journal |
| `integrite.refus.snapshot_immuable` | Snapshot immuable (article 79). | اللقطة غير قابلة للتعديل (المادة 79). | 79 | `save()` sur `SnapshotInscription` existant |
| `integrite.refus.transition_immuable` | Transition de statut immuable. | انتقال الحالة غير قابل للتعديل. | 79 | `save()` sur `TransitionStatut` existant |
| `integrite.refus.numero_ordre_immuable` | Le numéro d'ordre est immuable (article 78). | رقم الترتيب غير قابل للتعديل (المادة 78). | 78 | Schéma de diff refuse cette clé |
| `integrite.refus.durée_immuable` | La durée ne peut être modifiée que par un renouvellement. | لا يمكن تعديل المدة إلا بالتجديد. | 90 al. 2 | Schéma de diff refuse cette clé |
| `integrite.alerte.chaine_rompue` | Rupture de chaîne d'audit détectée. | تم رصد انقطاع في سلسلة التدقيق. | § 5.2 | `verifier_chaine()` renvoie `(False, id)` |

---

## 8. Famille 7 — Transitions de statut (§ 4.3)

Cf. [L2.3 § 4.2](L2_3_matrice_statuts_transitions.md) pour le
catalogue complet des 8 messages de transition. Rappel :

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) |
|------------|---------------------|---------------------|
| `workflow.transition.prise_en_charge` | Demande prise en charge pour contrôle de forme. | تم استلام الطلب لإجراء مراقبة الشكل. |
| `workflow.transition.rejet_art80` | Rejet motivé au titre de l'article 80. | رفض مسبب بموجب المادة 80. |
| `workflow.transition.validation_greffier` | Inscription validée, numéro d'ordre attribué. | تم التحقق من التسجيل وإسناد رقم الترتيب. |
| `workflow.transition.modification_art88` | Modification appliquée au titre de l'article 88. | تم تطبيق التعديل بموجب المادة 88. |
| `workflow.transition.renouvellement_art91` | Renouvellement appliqué, période prorogée. | تم تطبيق التجديد وإطالة فترة المفعول. |
| `workflow.transition.radiation_art92` | Radiation enregistrée, mention « radiée ». | تم تسجيل الشطب وتفعيل ذكر « مشطوبة ». |
| `workflow.transition.expiration_automatique` | Inscription expirée, sortie du fichier public. | انتهت صلاحية التسجيل وخروجه من الملف العمومي. |
| `workflow.transition.transfert_fichier_general` | Transfert au fichier général (art. 92 al. 3). | نقل إلى الملف العام (المادة 92 الفقرة 3). |

---

## 9. Famille 8 — Système et exploitation

### 9.1 Messages informatifs

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Canal | Article |
|------------|---------------------|---------------------|-------|:-------:|
| `sante.ok` | Service disponible. | الخدمة متاحة. | GET `/sante/` | § 5.3 |
| `referentiels.invariant.ecart_enum_detecte` | Écart référentiel / énumération détecté. | تم رصد انحراف بين المرجع والتعداد. | Commande `seed_referentiels` | — |

### 9.2 Messages d'avertissement — Zones gelées actives

Ces messages sont émis par `warnings.warn()` Python lors de l'usage
d'une zone gelée. Visible dans les logs et dans la sonde de santé
(`zones_gelees` du JSON).

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Zone |
|------------|---------------------|---------------------|------|
| `zone_gelee.horodatage.stub` | Horodatage en mode STUB — inscription non opposable. | التأريخ في نمط تجريبي — التسجيل غير قابل للاحتجاج. | `L11/horodatage` |
| `zone_gelee.scellement.stub` | Scellement en mode STUB — sceaux non opposables. | الختم في نمط تجريبي — الأختام غير قابلة للاحتجاج. | `L11/A5` |
| `zone_gelee.esign.stub` | Signature électronique non vérifiée cryptographiquement. | التوقيع الإلكتروني غير متحقق منه تشفيريا. | `L11/A2` |
| `zone_gelee.mfa.inactive` | Authentification forte non active. | المصادقة القوية غير مفعلة. | `L11/MFA` |
| `zone_gelee.certificat_probant.inactif` | Certificat non probant tant que scellement et horodatage ne sont pas arbitrés. | الشهادة غير ذات حجية ما لم يُحسم في الختم والتأريخ. | `L11/A5` |
| `zone_gelee.paiement.inactif` | Paiement électronique non exigé (politique tarifaire non arbitrée). | الدفع الإلكتروني غير مفروض (السياسة التعريفية غير محسومة). | `L11/A7` |
| `zone_gelee.rccm_interconnexion.inactive` | Pas de vérification auprès du RCCM. | لا تحقق لدى السجل التجاري والائتماني. | `L11/interconnexions` |
| `zone_gelee.parties_reutilisation.inactive` | Chaque ajout de partie crée une nouvelle entrée (conservatisme). | كل إضافة طرف تُنشئ قيداً جديداً (تحفظ). | `L11/parties_reutilisation` |

### 9.3 Messages de notification externe — RÉSERVÉS (GELÉS)

Ces clés sont réservées pour la future intégration des canaux
externes (email, SMS, portail). Aucune émission n'a lieu tant que
l'arbitrage MO sur les interconnexions n'est pas rendu.

| Clé neutre | Libellé FR (amorce) | Libellé AR (amorce) | Canal cible |
|------------|---------------------|---------------------|-------------|
| `notification.depot.externe` | Votre demande a été enregistrée (réf. : …). | تم تسجيل طلبكم (المرجع: …). | Email / SMS déposant |
| `notification.validation.externe` | Votre inscription a été validée (n° : …). | تم التحقق من تسجيلكم (الرقم: …). | Email / SMS déposant |
| `notification.rejet.externe` | Votre demande a été rejetée : … | تم رفض طلبكم: … | Email / SMS déposant |
| `notification.modification.externe` | Votre modification a été appliquée. | تم تطبيق تعديلكم. | Email / SMS déposant |
| `notification.radiation.externe` | La radiation a été enregistrée. | تم تسجيل الشطب. | Email / SMS déposant |
| `notification.certificat.emission` | Votre certificat est disponible. | شهادتكم متوفرة. | Email déposant |
| `paiement.demande` | Règlement des émoluments attendu. | يتوقع تسديد الرسوم. | Portail paiement |

⚠️ **Aucune de ces clés ne doit être émise tant que le MO n'a pas
arbitré**. Elles figurent au registre des arbitrages en attente
(`L11/interconnexions`, `L11/A5`, `L11/A7`).

---

## 10. Messages d'audit (§ 5.2) — cartographie des actions

Cf. L3.5 § 9 pour la liste consolidée. Rappel synthétique des
`action_cle` produites au journal d'audit :

| Catégorie (`CategorieAudit`) | Actions tracées (`action_cle`) |
|------------------------------|--------------------------------|
| `connexion` | (connexion, déconnexion, tentative) — à instrumenter lors de l'activation MFA |
| `compte` | `affectation.creer`, `affectation.mettre_a_jour` |
| `demande` | `inscription.deposer`, `modification.appliquer`, `renouvellement.appliquer`, `radiation.appliquer`, `transition.<evenement>` |
| `controle_forme` | (réservé) |
| `validation` | `inscription.valider`, `transition.validation_greffier` |
| `rejet` | `inscription.rejeter`, `modification.refuser` |
| `certificat` | `certificat.preparer` |
| `recherche` | `recherche.lancer` |
| `export_stat` | `statistiques.extraire` |
| `admin` | `referentiels.seed` |
| `systeme` | `inscription.expirer_archiver` |

Toute action d'audit est stockée **par clé neutre** et n'admet aucun
libellé dépendant de la langue (§ 7.6 TDR).

---

## 11. Règles de rédaction des libellés FR/AR

Règles normatives pour le comité de terminologie (§ 7.3 TDR — zone
A6). Ces règles ne sont pas imposées par le décret mais par la
cohérence du système :

1. **Concision** : une phrase courte par libellé ; pas de paragraphes.
2. **Même densité informative** en FR et en AR — l'un ne peut pas être
   plus informatif que l'autre.
3. **Références d'articles** : mentionnées à l'identique dans les deux
   langues (ex. « art. 88 » / « المادة 88 »).
4. **Référence aux clés limitatives** du décret (natures art. 76,
   motifs art. 80, critères art. 96) : utiliser les libellés officiels
   du référentiel, pas de paraphrases.
5. **Pas de termes techniques d'implémentation** (rollback, savepoint,
   DRF, PostgreSQL) : les libellés sont destinés au déposant / au
   greffier / à l'auditeur, pas au développeur.
6. **Format des dates et nombres** : respecte la locale ; la substance
   (valeur numérique, jour exact) reste identique.
7. **Terminologie juridique** : alignée sur le décret et le glossaire
   OHADA si applicable.

---

## 12. Matrice récapitulative — nombre de messages par famille

| Famille | Nombre | Référence locale |
|---------|:------:|------------------|
| 1. Succès | 16 | § 2 |
| 2. Rejet art. 80 | 5 | § 3 |
| 3. Refus art. 88 | 8 | § 4 |
| 4. Refus métier divers | 7 | § 5 |
| 5. Refus d'autorisation | 6 | § 6 |
| 6. Intégrité / immuabilité | 7 | § 7 |
| 7. Transitions de statut | 8 | § 8 (renvoi L2.3) |
| 8a. Système informatif | 2 | § 9.1 |
| 8b. Zones gelées | 8 | § 9.2 |
| 8c. Notifications externes (RÉSERVÉ) | 7 | § 9.3 |
| Audit (catégories × actions) | ~15 | § 10 |
| **Total catalogué** | **~89** | — |

---

## 13. Cohérence avec L3.6 — équivalence juridique FR/AR

Tous les messages FR et AR produisent **le même effet juridique** par
construction :
- la clé neutre est l'élément opposable ;
- les libellés FR/AR sont des vues d'affichage de cette clé ;
- aucune décision métier n'est prise sur la base d'un libellé —
  toutes les décisions reposent sur les clés neutres (statuts,
  motifs, rôles, critères).

Preuve formelle : cf. L3.6 § 13 (« Synthèse finale — démonstration
d'équivalence juridique ») et les tests
[tests/test_api_d3_accept_language.py](../backend/tests/test_api_d3_accept_language.py).

---

## 14. Zones gelées impactant le catalogue

| Zone | Impact sur L2.5 |
|------|-----------------|
| `L11/A6` (glossaire § 7.3) | L'ensemble des libellés FR/AR est en **amorce** ; validation finale attendue par le comité. |
| `L11/interconnexions` | Les 7 messages de notification externe (§ 9.3) sont **réservés**, non émis. |
| `L11/A7` (paiement) | `paiement.demande` réservé. |
| `L11/A5` (certificat probant) | `notification.certificat.emission` réservé ; messages d'avertissement `zone_gelee.*` actifs. |
| `L11/horodatage` | Messages d'avertissement `zone_gelee.horodatage.*` actifs à chaque appel de `maintenant_opposable()` en STUB. |
| `L11/MFA` | Messages `autorisation.refus.non_authentifie` émis uniquement via auth Django session. |

---

## 15. Mise en œuvre technique

Les messages sont résolus à l'affichage via les mécanismes i18n
standards, sans duplication de logique métier :

| Couche | Mécanisme |
|--------|-----------|
| Backend Django (templates) | `gettext` + fichiers `.po` (`locale/fr/LC_MESSAGES/`, `locale/ar/LC_MESSAGES/`) |
| Backend DRF (réponses API) | `get_*_display()` + clés neutres dans `detail` ; libellés optionnellement localisés |
| Frontend React | `react-i18next` + fichiers `fr.json` / `ar.json` |
| Journal d'audit | **Clé neutre uniquement** — pas de libellé |

Aucune décision métier n'appelle `gettext()` — les libellés résolus
sont confinés à la couche d'affichage.

---

## 16. Renvois croisés

- Formulaires : [L2.1](L2_1_formulaires_bilingues.md).
- Règles de validation : [L2.2](L2_2_regles_validation.md).
- Statuts × transitions : [L2.3](L2_3_matrice_statuts_transitions.md).
- Rôles × opérations : [L2.4](L2_4_roles_operations.md).
- Scénarios fonctionnels : [L2.6](L2_6_scenarios_fonctionnels.md).
- Handler d'exceptions + catalogue exceptions : [L3.4 § 15](L3_4_dictionnaire_api.md).
- Bilinguisme et équivalence juridique : [L3.6](L3_6_matrice_bilingue.md).
- Actions d'audit : [L3.5 § 9](L3_5_securite_integrite.md).
- Registre des arbitrages MO : [L11](L11_tracabilite_articles_76_97.md) + `backend/tests/arbitrages_mo_en_attente.txt`.
