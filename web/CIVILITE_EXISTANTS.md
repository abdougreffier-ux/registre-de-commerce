# RCCM — Gestion de la civilité pour les personnes physiques existantes

## Contexte

La migration `entites.0003_personnephysique_civilite` a ajouté le champ `civilite`
à la table `personnes_physiques` via une opération `AddField(blank=True)`.

Cette opération est **non destructive** : les enregistrements existants reçoivent
automatiquement la valeur `''` (chaîne vide) pour ce champ.

---

## Comportement vérifié — Enregistrements existants (civilite = '')

### 1. Affichage dans les listes et tableaux (frontend)

```javascript
const civ = { MR: 'M.', MME: 'Mme', MLLE: 'Mlle' }[r.civilite] || '';
return [civ, r.prenom, r.nom].filter(Boolean).join(' ');
// civilite='' → civ='' → filtré → résultat : "Prénom Nom"
```

✅ **Résultat** : `"Ahmed Ould Salem"` (sans préfixe) — cohérent avec l'état antérieur.

---

### 2. Propriété `nom_complet` sur PersonnePhysique

```python
_CIV_DISPLAY = {'MR': 'M.', 'MME': 'Mme', 'MLLE': 'Mlle'}

@property
def nom_complet(self):
    civ = self._CIV_DISPLAY.get(self.civilite, '')  # '' → ''
    parts = [p for p in [civ, self.prenom, self.nom] if p]  # '' filtré
    return ' '.join(parts)
    # → "Ahmed Ould Salem"
```

✅ **Résultat** : nom sans préfixe — cohérent, aucune régression.

---

### 3. Génération PDF (extraits RC, certificats, RBE)

Fonction centrale `_civ(civilite, lang)` dans `apps/rapports/views.py` :

```python
def _civ(civilite, lang='fr'):
    if not civilite:          # '' → falsy → retourne ''
        return ''
    if lang == 'ar':
        return _CIVILITE_AR.get(civilite, '')
    return _CIVILITE_FR.get(civilite, '')
```

Utilisation dans les extraits RC :
```python
civ_ph = _civ(getattr(ph, 'civilite', ''), lang)
nom_complet = f"{civ_ph} {ph.prenom} {ph.nom}".strip()
# → "Ahmed Ould Salem"  (strip() élimine l'espace initial si civ_ph='')
```

✅ **Résultat** : PDF affiche `"Ahmed Ould Salem"` — identique aux PDF générés
   avant l'introduction de la civilité. **Aucune incohérence documentaire.**

---

### 4. Formulaires de modification (frontend)

Quand un opérateur ouvre un dossier PH existant en mode édition :

- Le champ `civilite` est un `<Select>` avec `rules=[{ required: true }]`
- Si `civilite=''`, le Select s'affiche **sans valeur sélectionnée**
- L'opérateur **doit sélectionner une civilité** avant de pouvoir sauvegarder

✅ **Effet** : mécanisme de **complétion progressive des données** — la civilité
   sera saisie lors de la première modification ultérieure du dossier, sans
   blocage des dossiers non modifiés.

---

## Tableau de synthèse

| Contexte | Valeur `civilite` | Affichage | Statut |
|----------|-------------------|-----------|--------|
| Enregistrement avant migration | `''` (vide) | "Prénom Nom" | ✅ Cohérent |
| Enregistrement après migration (nouveau) | `'MR'`/`'MME'`/`'MLLE'` | "M. Prénom Nom" | ✅ Correct |
| PDF extrait RC — ancien dossier | `''` | "Prénom Nom" | ✅ Identique à l'ancien PDF |
| PDF extrait RC — nouveau dossier | `'MME'` | "Mme Prénom Nom" | ✅ Correct |
| Certificat greffier — ancien dossier | `''` | "Prénom Nom" | ✅ Cohérent |
| Formulaire modification | `''` | Select vide (saisie requise) | ✅ Complétion progressive |

---

## Risque résiduel identifié — AUCUN

| Question | Réponse |
|----------|---------|
| Un PDF ancien et un PDF nouveau du même dossier (sans modification) seront-ils différents ? | **Non** — les deux affichent "Prénom Nom" |
| Un dossier existant peut-il provoquer une erreur Python ? | **Non** — `_CIV_DISPLAY.get('', '')` retourne `''` sans exception |
| Un dossier existant peut-il provoquer une erreur dans un PDF ? | **Non** — `_civ('', lang)` retourne `''`, `strip()` absorbe l'espace résiduel |
| Des données ont-elles été modifiées ou perdues par la migration ? | **Non** — `AddField(blank=True)` sans `default` ne touche pas les données |

---

## Suivi qualité — Commande de contrôle

```bash
python manage.py check_deploy
```

La commande signale à l'étape 3/4 le nombre de PH sans civilité :

```
3/4  Qualité données civilité … 47/120 personnes sans civilité (39 %)
     ↳ Ces personnes seront affichées sans préfixe (M./Mme/Mlle).
       La civilité sera requise à la prochaine modification.
```

Ce compteur décroîtra naturellement au fil des modifications de dossiers,
sans action de masse nécessaire.
