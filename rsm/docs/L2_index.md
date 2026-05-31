# L2 — Spécifications fonctionnelles détaillées

**Livrable** : L2 (§ 8 du TDR).
**Objet** : référentiel fonctionnel opposable au MO et au greffe :
formulaires bilingues, règles de validation, matrices statuts /
transitions / rôles, cartographie des messages système, scénarios
d'usage.

**Angle** : strictement **fonctionnel**. Tout élément technique est
renvoyé à L3.

**État** : ✅ **Livré intégralement (6 sous-livrables)**.

## Sous-livrables

| Sous-livrable | Objet | État |
|---------------|-------|------|
| [L2.1](L2_1_formulaires_bilingues.md) | Formulaires bilingues (art. 85, 88, 91, 92, 96, 80, validation art. 87) | ✅ Livré (tour 1) |
| [L2.2](L2_2_regles_validation.md) | Règles de validation consolidées article par article + matrice des exceptions | ✅ Livré (tour 1) |
| [L2.3](L2_3_matrice_statuts_transitions.md) | Matrice 9 statuts × 15 transitions × messages système + 4 interdictions explicites | ✅ Livré (tour 1) |
| [L2.4](L2_4_roles_operations.md) | Matrice rôles × opérations (7 rôles, séparation stricte, cumuls interdits) | ✅ Livré (tour 2) |
| [L2.5](L2_5_messages_systeme.md) | Cartographie des messages système — catalogue bilingue complet (~89 messages) | ✅ Livré (tour 2) |
| [L2.6](L2_6_scenarios_fonctionnels.md) | 8 scénarios fonctionnels bout-en-bout + matrices règles × scénarios × zones gelées | ✅ Livré (tour 2) |

## Règles de conformité du livrable

- Aucune zone gelée levée — les zones gelées sont mentionnées et
  renvoyées à L11 sans implémentation implicite.
- Aucune règle nouvelle introduite — L2 consolide les règles déjà
  présentes dans le code et dans L3.
- Régime déclaratif (art. 86) respecté : contrôles de forme
  uniquement, aucun contrôle de fond.
- Bilinguisme strict : clés neutres en référence, libellés FR/AR en
  amorce à valider par le comité de terminologie (§ 7.3).
- Cohérence stricte avec L3 (modèle, architecture, API, sécurité,
  bilinguisme) et L11 (traçabilité article par article).

## Plan de lecture recommandé

1. **[L1](L1_note_de_cadrage.md)** — Contexte général.
2. **[L2.1](L2_1_formulaires_bilingues.md)** — Que saisit-on ?
3. **[L2.2](L2_2_regles_validation.md)** — Quelles règles appliquer ?
4. **[L2.3](L2_3_matrice_statuts_transitions.md)** — Dans quels
   enchaînements de statuts ?
5. **[L2.4](L2_4_roles_operations.md)** — Qui peut faire quoi ?
6. **[L2.5](L2_5_messages_systeme.md)** — Quels messages sont émis ?
7. **[L2.6](L2_6_scenarios_fonctionnels.md)** — Comment se déroule
   un cycle de vie complet ?
8. **[L3](L3_index.md)** — Comment est-ce implémenté techniquement ?
9. **[L11](L11_tracabilite_articles_76_97.md)** — Où est prouvée la
   conformité article par article ?

## Renvois croisés

- Note de cadrage : [L1](L1_note_de_cadrage.md).
- Spécifications techniques consolidées : [L3 — index](L3_index.md).
- Traçabilité et matrices admin / risques / hypothèses : [L11](L11_tracabilite_articles_76_97.md).
