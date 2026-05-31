# Bilinguisme FR/AR et RTL

## Principe

Le site offre une **expérience intégralement équivalente** dans les deux langues (§7.1 TDR). Les
contenus français et arabes sont structurellement liés par leur chemin : `src/fr/<x>.md` et
`src/ar/<x>.md` donnent respectivement `/fr/<x>/` et `/ar/<x>/`, et chacun pointe vers l'autre via
`<link rel="alternate" hreflang="...">` et le sélecteur de langue.

## Bascule droite-à-gauche (§7.2 TDR)

Mise en œuvre :

1. **Au niveau du document** : `<html dir="rtl" lang="ar">` pour les pages arabes. Géré par le layout
   de base (`base.njk`) à partir de la variable `locale` exposée par `ar.11tydata.js`.
2. **Au niveau CSS** : exclusivement des **propriétés logiques** (`margin-inline-start`,
   `padding-inline-end`, `border-inline-start`, `inset-inline-start`, etc.) au lieu de `left`/`right`.
   Ainsi la mise en page se miroite automatiquement sans règles CSS dupliquées.
3. **Icônes directionnelles** : le fil d'Ariane utilise `›` en LTR et `‹` en RTL (règle `[dir="rtl"]`
   ciblée).
4. **Textes mixtes** : un extrait français inséré dans un texte arabe porte `lang="fr" dir="ltr"` ;
   inversement pour un mot arabe dans un texte français. Vérifié pour le numéro de téléphone.

## Typographie arabe (§7.3 TDR)

- **Police auto-hébergée** : Noto Naskh Arabic (variable, WOFF2) chargée depuis `/assets/fonts/`
  avec `font-display: swap`.
- **Interlignage** augmenté (`--lh-normal: 1.75` en RTL) car l'arabe gagne en lisibilité avec plus
  d'air vertical.
- **Typographie latine** de repli : Inter, puis fallback système.
- Pas d'appel à Google Fonts ni à aucun CDN tiers — raisons de confidentialité et de performance.

## Équivalence des contenus

Règles éditoriales :

- **Tout contenu publiable doit exister dans les deux langues** (§7.1).
- Exception autorisée pour un texte officiel ne faisant foi que dans une langue : la version
  existante doit alors être précédée d'un **bandeau d'information** signalant l'absence temporaire
  de traduction et le statut juridique du document. Exemple dans `loi-2022-011.md` : champ
  `authoritativeLanguage: AR` qui alimente l'info-bulle dans l'index des textes.
- **Métadonnées** synchronisées : date, référence, rubrique.
- **Terminologie** : tout terme juridique passe par le [glossaire](../src/_data/glossaire.js),
  validé par le secrétariat du Comité.

## Sélecteur de langue

Implémentation dans [`partials/lang-switcher.njk`](../src/_includes/partials/lang-switcher.njk) :

- La langue courante est signalée par `aria-current="true"`.
- Le lien vers l'autre langue porte `hreflang` + `lang` + `dir` pour que le libellé soit lu
  correctement par les lecteurs d'écran.
- Si une page équivalente n'existe pas dans l'autre langue (cas de rupture), le lien pointe vers la
  racine linguistique (`/fr/` ou `/ar/`) — comportement à ajuster en phase 2 si besoin.

## Dates bilingues

Les dates sont rendues dans le format long attendu par la langue :

| Locale | Format | Exemple |
|---|---|---|
| FR | `d LLLL yyyy` | 11 mars 2021 |
| AR | `d LLLL yyyy` (locale `ar`) | 11 مارس 2021 |

Gérées par les filtres `dateFR` / `dateAR` dans [`.eleventy.js`](../.eleventy.js), via la
bibliothèque Luxon.

## Numéros de téléphone et URLs

Les numéros internationaux sont explicitement encadrés par `<... dir="ltr">` dans les versions
arabes pour préserver l'ordre visuel « +222 … ».

## Contrôle qualité bilingue

- **Parité d'arborescence** : script à ajouter en phase 2 qui compare les fichiers `src/fr/**` et
  `src/ar/**` et signale les absences.
- **Parité i18n** : toute nouvelle clé dans `i18n.js` doit exister dans les deux langues.
- **Tests visuels** : chaque gabarit (article, liste, formulaire) doit être testé dans les deux
  langues à chaque modification structurelle.

## Recherche et indexation multilingue

Deux index distincts sont générés au build (`search-index.fr.json`, `search-index.ar.json`). Le
normaliseur JS supprime les diacritiques latins et arabes (tatweel, fatḥa, ḍamma, kasra, shadda,
sukūn, harakāt), et homogénéise l'alif (أ/إ/آ → ا), la ya (ى → ي) et la ta marbūṭa (ة → ه) pour
tolérer les variations orthographiques.
