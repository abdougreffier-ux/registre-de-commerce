# L3 — Spécifications techniques consolidées

**Livrable** : L3 (§ 8 du TDR).
**Objet** : document de référence technique opposable, consolidant le
modèle de données, l'architecture, les politiques d'horodatage et de
scellement, l'API interne, les dispositifs de sécurité et la matrice
de conformité bilingue du système RSM.

**État** : ✅ **Livré intégralement (6 sous-livrables)**.

## Sous-livrables

| Sous-livrable | Objet | État |
|---------------|-------|------|
| [L3.1](L3_1_modele_donnees.md) | Modèle de données consolidé | ✅ Livré et validé MO |
| [L3.2](L3_2_architecture_modulaire.md) | Architecture modulaire | ✅ Livré et validé MO |
| [L3.3](L3_3_horodatage_scellement.md) | Politique d'horodatage et de scellement (zones gelées documentées) | ✅ Livré et validé MO |
| [L3.4](L3_4_dictionnaire_api.md) | Dictionnaire API (endpoints, serializers, exceptions, matrice bilinguisme) | ✅ Livré |
| [L3.5](L3_5_securite_integrite.md) | Dispositifs de sécurité et d'intégrité (4 remparts, OWASP, robustesse) | ✅ Livré |
| [L3.6](L3_6_matrice_bilingue.md) | Matrice de conformité bilingue FR/AR (équivalence juridique) | ✅ Livré |

## Règles de conformité du livrable

- Aucune zone gelée n'est levée à l'occasion de L3. Les zones gelées
  sont documentées **en tant que zones gelées**.
- Aucune règle nouvelle n'est introduite. L3 consolide l'existant.
- Chaque description est strictement cohérente avec le code, les tests
  et le registre L11 (traçabilité article par article).
- Les mécanismes bilingues sont décrits comme produisant des effets
  juridiques strictement identiques en français et en arabe.

## Plan de lecture recommandé

1. **[L1](L1_note_de_cadrage.md)** — Contexte, principes, stack, zones gelées.
2. **[L3.2](L3_2_architecture_modulaire.md)** — Vue d'ensemble architecturale.
3. **[L3.1](L3_1_modele_donnees.md)** — Détail des entités et contraintes.
4. **[L3.4](L3_4_dictionnaire_api.md)** — API exposée, contrats.
5. **[L3.3](L3_3_horodatage_scellement.md)** — Zones gelées cryptographiques.
6. **[L3.5](L3_5_securite_integrite.md)** — Sécurité et intégrité.
7. **[L3.6](L3_6_matrice_bilingue.md)** — Bilinguisme et équivalence juridique.
8. **[L11](L11_tracabilite_articles_76_97.md)** — Traçabilité article par article.

## Renvois croisés

- Cadrage initial : [L1](L1_note_de_cadrage.md).
- Traçabilité article par article + matrice admin + registre des hypothèses et risques : [L11](L11_tracabilite_articles_76_97.md).
- Registre des tests désactivés pour arbitrage MO : `backend/tests/arbitrages_mo_en_attente.txt` (produit par `python manage.py lister_arbitrages_mo`).
