# Fiches de décision MO — Registre des Sûretés Mobilières

**Objet** : dossiers d'arbitrage structurés pour les zones gelées du
système RSM, destinés à la prise de décisions MO écrites et
référencées, conformément à la gouvernance établie.

**Règles de production** :
- Options présentées **sans préférence tranchée** — la décision reste
  du ressort exclusif du MO.
- Chaque option est accompagnée de ses **impacts juridiques et
  techniques** de façon équilibrée.
- Aucune levée de zone gelée implicite — toute fiche est un support à
  décision, jamais une mise en œuvre.
- Format unifié — facilite la comparaison et la traçabilité.

## Format unifié des fiches

```
1. Identification
   - Référence L11 + article(s) fondateur(s)
   - Statut actuel (STUB / non implémenté)
   - Dépendances
2. Contexte juridique
3. Situation actuelle dans le système
4. Options d'arbitrage (a, b, c…)
   Pour chaque option : description, impacts juridiques,
   impacts techniques, coût de mise en œuvre, dépendances externes,
   avantages / inconvénients
5. Impacts transversaux
6. Tradeoffs synthétiques (neutralité stricte)
7. Décision MO (zone vide, à compléter séparément)
```

## État des fiches

### Tour 1 — Fiches structurantes pour l'Option B (frontend)

| Fiche | Référence L11 | Objet | État |
|-------|---------------|-------|------|
| [F1](F1_glossaire_bilingue.md) | `L11/A6` | Glossaire juridique bilingue (§ 7.3) | ✅ Produite |
| [F2](F2_authentification_forte.md) | `L11/MFA` | Authentification forte (§ 5.1) | ✅ Produite |
| [F3](F3_signature_electronique.md) | `L11/A2` | Signature électronique (art. 88) | ✅ Produite |
| [F4](F4_charte_documentaire_certificats.md) | `L11/A5` | Charte documentaire et certificats probants (art. 97) | ✅ Produite |

### Tour 2 — Fiches cryptographie et temporalité

| Fiche | Référence L11 | Objet | État |
|-------|---------------|-------|------|
| [F5](F5_source_de_temps.md) | `L11/horodatage` | Source de temps officielle (art. 78) | ✅ Produite |
| [F6](F6_scellement_cryptographique.md) | `L11/A5` (volet scellement) | Scellement cryptographique (§ 6.3) | ✅ Produite |
| [F7](F7_distinction_horodatages.md) | `A9` | Distinction horodatage d'arrivée / horodatage de saisie | ✅ Produite |
| [F8](F8_politique_indisponibilite.md) | `A4` | Politique d'indisponibilité (§ 5.3) | ✅ Produite |

### Tour 3 — Fiches complémentaires

| Fiche | Référence L11 | Objet | État |
|-------|---------------|-------|------|
| [F9](F9_arrete_application.md) | `A1` | Arrêté d'application (art. 8, 81, 84) | ✅ Produite |
| [F10](F10_duree_maximale.md) | `A3` | Durée maximale d'inscription (art. 85) | ✅ Produite |
| [F11](F11_politique_tarifaire.md) | `A7` | Politique tarifaire / paiement (art. 85) | ✅ Produite |
| [F12](F12_cahier_charges_art83.md) | `A8` | Cahier des charges art. 83 (si délégation) | ✅ Produite |
| [F13](F13_interconnexions_externes.md) | `L11/interconnexions` | RCCM + identité numérique (art. 96) | ✅ Produite |
| [F14](F14_reutilisation_partie.md) | `L11/parties_reutilisation` | Référencement partie existante dans diff art. 88 | ✅ Produite |

---

**État consolidé** : ✅ **14 fiches MO livrées sur 14 (100 %)**. Le
dossier d'arbitrages est complet ; le MO dispose désormais de
l'ensemble des instruments d'instruction pour rendre ses décisions.

## Supports d'aide à la décision

| Document | Objet | État |
|----------|-------|------|
| [Comparatif F1 × F3 × F4 × F5](comparatif_F1_F3_F4_F5.md) | Synthèse comparative du nœud cardinal d'opposabilité (glossaire, signature art. 88, certificats art. 97, source de temps art. 78) — matrice d'interdépendances + 7 scénarios de cohérence globale, sans recommandation tranchée | ✅ Produit |

## Procédure de décision

1. Le MO lit une ou plusieurs fiches.
2. Le MO sélectionne une option (a, b, c, d, …) ou formule une option e
   alternative argumentée.
3. La décision est consignée **séparément** dans un document officiel
   signé (hors dépôt de code ou avec mention formelle).
4. Le livrable L11 est mis à jour pour refléter la décision (passage
   de la zone à l'état IMPLÉMENTÉ après activation technique).
5. Les tests `@arbitrage_mo` correspondants sont activés par les
   développeurs après validation technique.

## Renvois croisés

- Registre consolidé des arbitrages en attente :
  [L11](../L11_tracabilite_articles_76_97.md).
- Registre des tests désactivés :
  `backend/tests/arbitrages_mo_en_attente.txt` (généré par
  `python manage.py lister_arbitrages_mo`).
- Cadrage initial des zones gelées :
  [L3.3](../L3_3_horodatage_scellement.md).
