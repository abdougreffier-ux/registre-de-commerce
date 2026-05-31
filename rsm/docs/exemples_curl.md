# Exemples d'appels API — Environnement de TEST fonctionnel

**Objet** : collection de commandes `curl` directement exploitables
pour tester le système RSM en environnement de test.
**Base URL** : `http://localhost:8000`
**Format** : JSON UTF-8

⚠️ Toutes les données produites par ces appels sont **de test, non
opposables**. Les zones gelées (horodatage, scellement, signature,
MFA) restent en mode STUB.

---

## 0. Préparation

### 0.1 Authentification par session Django

Pour les endpoints authentifiés, l'approche la plus simple en test
est d'utiliser l'authentification HTTP Basic (activable en mode
DEBUG) ou de se connecter d'abord à l'admin Django pour obtenir un
cookie de session.

**Variante Basic Auth (recommandée en test, nécessite ajustement) :**

Ajouter temporairement dans `rsm_project/settings.py` (à retirer en production) :

```python
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "rest_framework.authentication.BasicAuthentication",
    "rest_framework.authentication.SessionAuthentication",
]
```

Puis :

```bash
export AUTH_GREFFIER='-u greffier:test-rsm-greffier-2026'
export AUTH_AGENT='-u agent_saisie:test-rsm-agent-2026'
export AUTH_DECLARANT='-u declarant_externe:test-rsm-declarant-2026'
export AUTH_AUDITEUR='-u auditeur:test-rsm-auditeur-2026'
export AUTH_STATS='-u prod_stats:test-rsm-stats-2026'
```

**Variante Session Django (si Basic Auth non activé) :**

1. Se connecter à http://localhost:8000/fr/administration/ avec un navigateur.
2. Copier le cookie `sessionid` depuis les outils développeur.
3. Utiliser `-b "sessionid=..."` dans curl.

### 0.2 Préparation d'en-têtes

```bash
export JSON='-H "Content-Type: application/json"'
export ACCEPT_FR='-H "Accept-Language: fr"'
export ACCEPT_AR='-H "Accept-Language: ar"'
```

---

## 1. Sonde de santé (non authentifié)

```bash
curl http://localhost:8000/fr/sante/
```

Réponse attendue (`langue_resolue: "fr"`, indicateurs de zones gelées).

Même chose en arabe :

```bash
curl http://localhost:8000/ar/sante/
```

---

## 2. Référentiels publics (non authentifiés)

```bash
# 12 natures de sûretés (art. 76)
curl http://localhost:8000/api/v1/referentiels/natures-droit/

# 3 motifs de rejet (art. 80)
curl http://localhost:8000/api/v1/referentiels/motifs-rejet/

# 4 critères de recherche (art. 96)
curl http://localhost:8000/api/v1/referentiels/criteres-recherche/

# Canaux de saisie (art. 78)
curl http://localhost:8000/api/v1/referentiels/canaux-saisie/

# 5 types de certificats
curl http://localhost:8000/api/v1/referentiels/types-certificats/
```

---

## 3. Scénario A — Cycle complet d'une inscription

### 3.1 Dépôt d'une demande (agent de saisie)

```bash
curl -X POST http://localhost:8000/api/v1/inscriptions/ \
  $AUTH_AGENT \
  -H "Content-Type: application/json" \
  -d '{
    "canal_saisie": "guichet_papier",
    "nature_droit": "nant_outillage",
    "somme_garantie": "2500000.00",
    "monnaie": "MRU",
    "duree_en_jours": 365,
    "adresse_electronique_notifications": "demo@test.rsm"
  }'
```

Réponse : HTTP 201 + corps JSON contenant `reference_demande` (UUID)
et `statut: "en_controle_forme"`.

**Noter la `reference_demande` retournée**, elle sert aux étapes suivantes :

```bash
export REF="<uuid-retourné>"
```

### 3.2 Peuplement des parties et biens (admin Django)

À ce jour, l'ajout de parties et de biens passe par **l'admin Django**
(en raison du gel de l'Option B). Se connecter à
http://localhost:8000/fr/administration/ avec `admin_technique`, puis
créer manuellement via les entités `Partie`, `RoleInscriptionPartie`,
`BienGreve`.

Alternative : le `seed_demo_test` a déjà produit 6 inscriptions
complètes, qui peuvent servir pour tester les étapes suivantes sans
nouveau peuplement manuel.

### 3.3 Validation par le greffier

```bash
curl -X POST http://localhost:8000/api/v1/inscriptions/$REF/valider/ \
  $AUTH_GREFFIER
```

Réponse : HTTP 200 + `numero_ordre` au format `NNNNNN-AAAAMMJJHHMMSS`
+ `statut: "inscrite"` + `instant_saisie_opposable`.

### 3.4 Consultation de l'inscription (authentifié)

```bash
curl $AUTH_AGENT \
  http://localhost:8000/api/v1/inscriptions/$REF/
```

### 3.5 Liste paginée

```bash
curl $AUTH_AGENT \
  http://localhost:8000/api/v1/inscriptions/
```

---

## 4. Scénario B — Rejet motivé art. 80

### 4.1 Motif hors liste (refus attendu)

```bash
curl -X POST http://localhost:8000/api/v1/inscriptions/$REF/rejeter/ \
  $AUTH_GREFFIER \
  -H "Content-Type: application/json" \
  -d '{"motif": "motif_fantaisiste"}'
```

Réponse attendue : HTTP 400 + `{"detail": "...", "article": "80", "classe": "RejetForme"}`.

### 4.2 Motif limitatif (accepté)

```bash
curl -X POST http://localhost:8000/api/v1/inscriptions/$REF/rejeter/ \
  $AUTH_GREFFIER \
  -H "Content-Type: application/json" \
  -d '{
    "motif": "informations_illisibles",
    "commentaire_fr": "Document scanné illisible (TEST)",
    "commentaire_ar": "الوثيقة الممسوحة غير مقروءة (اختبار)"
  }'
```

Réponse : HTTP 200 + `statut: "rejetee"` + motif conservé.

---

## 5. Scénario C — Modification contrôlée

### 5.1 Création d'une demande de modification

```bash
# Supposant l'inscription 1 créée par seed_demo_test, on récupère son id :
curl $AUTH_AGENT \
  "http://localhost:8000/api/v1/inscriptions/?status=inscrite"

# Puis création de la demande (remplacer <id> par la pk réelle)
curl -X POST http://localhost:8000/api/v1/modifications/ \
  $AUTH_AGENT \
  -H "Content-Type: application/json" \
  -d '{
    "inscription": <id>,
    "objet_modification_fr": "Augmentation du montant garanti",
    "objet_modification_ar": "زيادة المبلغ المضمون",
    "diff_propose": {
      "scalaires": {"somme_garantie": "3000000.00"}
    },
    "accord_createur_confirme": true,
    "accord_constituant_confirme": true
  }'
```

Réponse : HTTP 201 + `id` de la demande.

### 5.2 Application par le greffier

```bash
curl -X POST http://localhost:8000/api/v1/modifications/<id_demande>/appliquer/ \
  $AUTH_GREFFIER
```

Réponse : HTTP 200 + mise à jour de l'inscription + snapshots
avant/après produits + audit `modification.appliquer`.

---

## 6. Scénario D — Refus art. 88 dernier alinéa

### 6.1 Tentative de retrait du dernier constituant

```bash
# Identifier d'abord le RoleInscriptionPartie CONSTITUANT actif
# (via admin Django ou liste inscriptions avec leurs rôles)

curl -X POST http://localhost:8000/api/v1/modifications/ \
  $AUTH_AGENT \
  -H "Content-Type: application/json" \
  -d '{
    "inscription": <id_inscription>,
    "objet_modification_fr": "Tentative de vidage constituants",
    "objet_modification_ar": "محاولة إفراغ المنشئين",
    "diff_propose": {
      "parties": {"retirer": [<id_lien_constituant>]}
    },
    "accord_createur_confirme": true,
    "accord_constituant_confirme": true
  }'
```

Réponse : HTTP 201 + `id` de la demande.

### 6.2 Application → refus attendu

```bash
curl -X POST http://localhost:8000/api/v1/modifications/<id_demande>/appliquer/ \
  $AUTH_GREFFIER
```

Réponse attendue : HTTP 400 + `{"detail": "...", "article": "88", "classe": "ModificationSansEffet"}`.

### 6.3 Consultation du motif structuré

```bash
curl $AUTH_AGENT \
  http://localhost:8000/api/v1/modifications/
```

Vérifier dans la réponse que la demande rejetée expose
`motif_refus_code: "etat_final_constituant_absent"`.

---

## 7. Scénario E — Renouvellement

### 7.1 Création de la demande

```bash
curl -X POST http://localhost:8000/api/v1/renouvellements/ \
  $AUTH_AGENT \
  -H "Content-Type: application/json" \
  -d '{"inscription": <id_inscription_en_cours>}'
```

### 7.2 Application

```bash
curl -X POST http://localhost:8000/api/v1/renouvellements/<id>/appliquer/ \
  $AUTH_GREFFIER
```

Réponse : HTTP 200 + `ancienne_date_expiration` + `nouvelle_date_expiration`.

### 7.3 Renouvellement après expiration (refus attendu)

Forcer une expiration via admin Django puis :

```bash
curl -X POST http://localhost:8000/api/v1/renouvellements/<id>/appliquer/ \
  $AUTH_GREFFIER
```

Réponse attendue : HTTP 400 + `article: "91"` + classe `RenouvellementHorsDelai`.

---

## 8. Scénario F — Radiation

### 8.1 Création de la demande

```bash
curl -X POST http://localhost:8000/api/v1/radiations/ \
  $AUTH_AGENT \
  -H "Content-Type: application/json" \
  -d '{
    "inscription": <id_inscription>,
    "fondement": "consentement",
    "denomination_constituant": "Établissements Ould Ahmed SARL",
    "adresse_constituant": "BP 123, Nouakchott",
    "numero_rc_constituant": "RC/NKT/2024/0001"
  }'
```

### 8.2 Application

```bash
curl -X POST http://localhost:8000/api/v1/radiations/<id>/appliquer/ \
  $AUTH_GREFFIER
```

Réponse : HTTP 200 + `mention_radiee: true`.

---

## 9. Scénario G — Recherche publique

### 9.1 Deux critères minimum (art. 96)

```bash
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -d '{
    "nom_constituant": "Ould Ahmed",
    "numero_rc": "RC/NKT/2024/0001"
  }'
```

### 9.2 Un seul critère → refus

```bash
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -d '{"nom_constituant": "Ould Ahmed"}'
```

Réponse attendue : HTTP 400 + `article: "96"` + `classe: "RechercheCriteresInsuffisants"`.

### 9.3 Clé hors liste → refus

```bash
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -d '{
    "nom_constituant": "X",
    "numero_rc": "Y",
    "nom_creancier": "hors liste art. 96"
  }'
```

Réponse attendue : HTTP 400 + champ `non_autorises`.

### 9.4 Recherche sur homonymes (DUPONT)

```bash
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -d '{
    "nom_constituant": "DUPONT",
    "numero_rc": "RC/NKT/2024/0001"
  }'
```

Le champ `homonymes_par_inscription` de la réponse liste **tous** les
constituants portant le nom « DUPONT » (art. 97 al. 2).

### 9.5 Recherche en arabe (équivalence juridique FR/AR)

```bash
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -H "Accept-Language: ar" \
  -d '{
    "nom_constituant": "Ould Ahmed",
    "numero_rc": "RC/NKT/2024/0001"
  }'
```

Vérifier que les clés juridiques neutres (`statut`, `numero_ordre`,
etc.) sont strictement identiques à celles retournées avec
`Accept-Language: fr`.

---

## 10. Scénario H — Audit et intégrité

### 10.1 Liste des entrées d'audit

```bash
curl $AUTH_AUDITEUR \
  http://localhost:8000/api/v1/audit/entrees/
```

### 10.2 Vérification de la chaîne

```bash
curl $AUTH_AUDITEUR \
  http://localhost:8000/api/v1/audit/verification-chaine/
```

Réponse attendue : `{"integre": true, "premiere_entree_alteree": null}`.

### 10.3 Refus pour un compte non auditeur

```bash
curl $AUTH_AGENT \
  http://localhost:8000/api/v1/audit/entrees/
```

Réponse attendue : HTTP 403.

---

## 11. Scénario I — Expiration et archivage

### 11.1 Forcer l'expiration (admin Django)

Se connecter à http://localhost:8000/fr/administration/ avec
`admin_technique`, localiser une inscription, et rétrodater
`date_expiration`. Noter que l'admin est en **lecture seule** par
design (cf. L3.2 § 6) — cette opération exige donc l'assouplissement
temporaire d'un paramètre `ConsultationMetierAdmin` OU une opération
via le shell Django :

```bash
# Shell Django
python manage.py shell -c "
from apps.inscriptions.models import Inscription
from datetime import date, timedelta
Inscription.objects.filter(numero_ordre__isnull=False).update(
    date_expiration=date.today() - timedelta(days=1)
)
"
```

### 11.2 Lancer la tâche d'expiration

```bash
python manage.py expirer_inscriptions
```

### 11.3 Vérifier la sortie du fichier public

```bash
# Recherche : l'inscription expirée NE DOIT PAS apparaître
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -d '{"numero_inscription":"<num_ordre>","numero_rc":"RC/NKT/2024/0001"}'
```

---

## 12. Scénario J — Statistiques (monopole art. 82)

### 12.1 Tentative par un autre rôle (refus)

```bash
curl -X POST http://localhost:8000/api/v1/statistiques/produire/ \
  $AUTH_AGENT \
  -H "Content-Type: application/json" \
  -d '{}'
```

Réponse attendue : HTTP 403.

### 12.2 Production par le rôle habilité

```bash
curl -X POST http://localhost:8000/api/v1/statistiques/produire/ \
  $AUTH_STATS \
  -H "Content-Type: application/json" \
  -d '{"perimetre": {}}'
```

---

## 13. Bascule de langue (Accept-Language)

L'équivalence juridique FR/AR est démontrée en soumettant le même
payload avec deux valeurs distinctes d'`Accept-Language` :

```bash
# Réponse FR
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -H "Accept-Language: fr" \
  -d '{"nom_constituant":"Ould Ahmed","numero_rc":"RC/NKT/2024/0001"}'

# Réponse AR
curl -X POST http://localhost:8000/api/v1/recherche/ \
  -H "Content-Type: application/json" \
  -H "Accept-Language: ar" \
  -d '{"nom_constituant":"Ould Ahmed","numero_rc":"RC/NKT/2024/0001"}'
```

Comparer les deux réponses : les clés neutres (statut, numéro d'ordre,
horodatages, montants) doivent être **strictement identiques**.

---

## 14. Variante HTTPie

Si vous préférez [HTTPie](https://httpie.io) :

```bash
# Dépôt (agent_saisie)
http -a agent_saisie:test-rsm-agent-2026 POST http://localhost:8000/api/v1/inscriptions/ \
  canal_saisie=guichet_papier \
  nature_droit=nant_outillage \
  somme_garantie=2500000.00 \
  monnaie=MRU \
  duree_en_jours:=365

# Validation (greffier)
http -a greffier:test-rsm-greffier-2026 POST \
  "http://localhost:8000/api/v1/inscriptions/$REF/valider/"

# Recherche publique
http POST http://localhost:8000/api/v1/recherche/ \
  nom_constituant="Ould Ahmed" \
  numero_rc="RC/NKT/2024/0001"
```

---

## 15. Diagnostic des réponses d'erreur

Toutes les exceptions métier sont traduites par le handler DRF global
(`apps.core.exception_handler`) en réponse JSON structurée :

| Classe | HTTP | Article | Cas typique |
|--------|:----:|:-------:|-------------|
| `RejetForme` | 400 | 80 | Canal invalide, motif hors liste, nature hors liste |
| `ModificationSansEffet` | 400 | 88 | Accords manquants, état final invalide, diff invalide |
| `RenouvellementHorsDelai` | 400 | 91 | Renouvellement après expiration |
| `RechercheCriteresInsuffisants` | 400 | 96 | < 2 critères de recherche |
| `TransitionInterdite` | 400 | § 4.3 | Transition hors matrice |
| `AutorisationRefusee` | 403 | § 4.1 | Cumul rôles, rôle manquant |
| `PermissionError` | 403 | 79 | Tentative d'écriture sur append-only |
| `ValidationError` DRF | 400 | — | Clé inconnue, format invalide |

Exemple de réponse typique d'erreur :

```json
{
  "detail": "Article 88 dernier alinéa — aucune partie constituante active après application : modification sans effet.",
  "article": "88",
  "classe": "ModificationSansEffet"
}
```

---

## 16. Cas d'usage non testables via API en STUB

Les comportements suivants ne peuvent **pas** être testés en
environnement de test tant que les arbitrages MO correspondants ne
sont pas rendus :

| Cas | Fiche MO bloquante |
|-----|--------------------|
| Vérification cryptographique de signature électronique (art. 88) | F3 |
| Génération de certificat probant bilingue (art. 97 dernier al.) | F4 |
| Horodatage juridiquement opposable (art. 78) | F5 |
| Authentification forte MFA | F2 |
| Paiement des émoluments | F11 |
| Notifications externes aux parties | F13 |
| Vérification d'existence du n° RC auprès du RCCM | F13 |

Ces cas sont matérialisés par les 11 tests `@arbitrage_mo` qui
apparaissent comme SKIPPED dans la suite `python manage.py test`.

---

## 17. Renvois croisés

- Guide environnement de test : [guide_environnement_test.md](guide_environnement_test.md).
- Dictionnaire complet des endpoints : [L3.4](L3_4_dictionnaire_api.md).
- Scénarios fonctionnels opposables : [L2.6](L2_6_scenarios_fonctionnels.md).
- Matrice des habilitations : [L2.4](L2_4_roles_operations.md).
- Messages système (codes d'erreur FR/AR) : [L2.5](L2_5_messages_systeme.md).
