# Charte éditoriale et workflow de publication

Ce document précise les règles rédactionnelles et le circuit de validation des contenus (§6.3,
§7.4 TDR).

## Ton et style

- **Institutionnel, administratif, neutre, factuel.** Pas de formulations promotionnelles.
- Phrases courtes, vocabulaire accessible. Explication des termes techniques au premier emploi.
- Dates en format long : « 11 mars 2021 » (pas « 11/03/21 »).
- Références aux textes juridiques **normalisées** : numéro, date, objet, source.
- Pas d'emoji.

## Types de contenu

| Type | Dossier | Identifiant | Rubrique affichée |
|---|---|---|---|
| Avis | `publications/avis/` | `avis-{année}-{num}` | Avis du Comité |
| Communiqué | `publications/communiques/` | `comm-{année}-{num}` | Communiqués |
| Actualité | `publications/actualites/` | `slug-descriptif` | Actualités |
| Texte juridique | `textes/` | `slug-reference` | Textes juridiques |

Chaque article porte, dans sa front-matter :

```yaml
layout: layouts/article.njk
title: Titre complet de l'avis
reference: Avis n° 2026-001       # pour les avis/communiqués
description: Résumé en une phrase.
type: avis                        # avis | communique | actualite | texte
rubrique: Avis du Comité
date: 2026-03-12                  # date de la session ou de publication
permalink: /fr/publications/avis/avis-2026-001/
```

## Règles sur les identifiants (§6.1 TDR)

- **Chaque publication officielle a un identifiant pérenne**. Le `permalink` ne doit jamais être
  changé après publication.
- En cas d'erreur, **créer un nouvel avis** (avec nouvel identifiant) qui rectifie le précédent,
  plutôt que de modifier l'URL d'origine.
- Le nom de fichier = identifiant humainement lisible, même structure que l'URL finale.

## Circuit de publication (§6.3 TDR)

Phase 1 (actuelle) — circuit Git manuel :

1. **Rédaction** : l'éditeur crée une branche, rédige les versions FR **et** AR.
2. **Relecture linguistique** : FR par un relecteur francophone, AR par un relecteur arabophone.
3. **Validation juridique** : le secrétariat du Comité relit et valide les termes juridiques.
4. **Publication** : après merge de la pull-request, le déploiement est déclenché.
5. **Journal d'audit** : historique Git complet, immuable.

Phase 2 — CMS Git-based (Decap CMS) :

1. **Rédaction** dans l'interface web du CMS ; brouillon sauvegardé dans Git.
2. **Relecture** : changement de statut `draft → in_review`.
3. **Validation juridique** : approbation via l'interface.
4. **Publication** : changement de statut `in_review → published` + déploiement automatique.

## Parité linguistique

Aucune publication ne doit être mise en ligne **uniquement** en français ou **uniquement** en arabe,
sauf exception dûment motivée (texte officiel n'existant que dans une langue faisant foi). Dans ce
cas, le champ `authoritativeLanguage` doit être renseigné et un bandeau doit l'indiquer.

## Métadonnées obligatoires

Chaque page publiée doit porter :

- `title` — clair, spécifique, sans verbe d'action.
- `description` — 120–160 caractères, synthèse factuelle.
- `date` — date de session ou de publication officielle.
- `lastUpdated` — pour les pages institutionnelles, mise à jour à chaque modification substantielle.

## Rédaction inclusive

- Alterner les formulations au besoin, privilégier les termes épicènes quand c'est naturel.
- Pas de recours à des tournures qui alourdiraient la lecture à l'écran (écriture inclusive avec
  points médians déconseillée ici car elle perturbe certains lecteurs d'écran).

## Images

- **Pas de texte intégré** dans les images (le texte doit rester dans le HTML — sauf logos).
- **Attribut `alt`** systématique ; si l'image est décorative, `alt=""`.
- Format privilégié : SVG (logos, pictogrammes), WebP (photographies).

## Pièces jointes (PDF)

- Les PDF mis en ligne doivent être **accessibles** (balisage correct, lecture par synthèse vocale
  possible). Les PDF scannés sans OCR sont à éviter.
- Compression raisonnable (< 5 Mo par document normatif ; < 15 Mo pour un document illustré).

## Corrections

- Les **erreurs d'orthographe ou de formulation** peuvent être corrigées silencieusement, via Git.
- Les **erreurs de fond** (numéro, date, référence) doivent faire l'objet d'un erratum tracé — soit
  par un nouvel avis rectificatif, soit par une mention visible en haut de la page avec la date et
  la nature de la correction.
