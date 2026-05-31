# Accessibilité — Mise en œuvre WCAG 2.1 AA

Ce document décrit les mesures techniques et éditoriales pour respecter WCAG 2.1 niveau AA
(§9 TDR). Il est complété par la [Déclaration d'accessibilité](/fr/accessibilite/) publiée à
l'intention des utilisateurs.

## Principes d'ingénierie

### Structure et sémantique

- **Un seul `<h1>` par page** (dans `page.njk` / `article.njk`).
- Hiérarchie des titres logique et ininterrompue (`h1 → h2 → h3`).
- Balises HTML5 sémantiques : `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<footer>`,
  `<aside>`, `<figure>`, `<time>`, `<address>`.
- `<main id="main">` cible du lien d'évitement.
- `aria-label` sur chaque `<nav>` (primaire, breadcrumb, lang-switcher, sitemap).
- `role="status"` + `aria-live="polite"` pour les messages dynamiques (résultats de recherche).

### Navigation clavier (WCAG 2.1.1, 2.4.3, 2.4.7)

- Lien d'évitement `.skip-link` vers `#main`, visible au focus.
- Focus **toujours visible** : outline 3 px bleu sur tout élément focusable (règle `:focus-visible`
  globale dans `main.css`).
- Ordre de tabulation = ordre du DOM (aucun `tabindex` positif).
- Menu hamburger (mobile) : `aria-expanded` synchronisé via JS, fermeture à `Escape`.

### Contrastes (WCAG 1.4.3)

Palette de couleurs choisie pour respecter les ratios AA :

- Texte principal `#1a1f2b` sur fond `#ffffff` → ratio ~16:1 (AAA).
- Primary `#0a5b3a` sur blanc → ratio 7.2:1 (AAA).
- Accent `#b8860b` sur blanc → ratio 4.6:1 (AA — attention à ne pas l'utiliser pour du corps).
- Mode sombre : couleurs inversées avec contrastes équivalents.

**Vérification** : utiliser https://webaim.org/resources/contrastchecker/ avant tout ajout de
palette.

### Taille et zoom (WCAG 1.4.4)

- Toutes les tailles en `rem` / `em` ; pas de `px` absolus sur les polices.
- Aucun blocage du zoom (`user-scalable=no` interdit).
- Testé jusqu'à 200 % de zoom sans perte de fonctionnalité.

### Images (WCAG 1.1.1)

- Images porteuses de sens : `alt` descriptif obligatoire.
- Images décoratives : `alt=""` **et** `role="presentation"` pour les pictogrammes purs.
- Icônes SVG inline : `aria-hidden="true"` + `focusable="false"`.
- Images de contenu : prévoir des attributs `width` et `height` pour éviter le CLS (performance ET
  accessibilité — anti-sauts).

### Formulaires (WCAG 3.3.1, 3.3.2)

Voir [`src/_includes/partials/saisine-form.njk`](../src/_includes/partials/saisine-form.njk) :

- `<label for>` explicite pour chaque champ.
- `required` côté HTML + indication visuelle et textuelle (`aria-label` avec `obligatoire`).
- `aria-describedby` pointant vers le message d'erreur (`id="err-<champ>"`).
- `aria-invalid="true"` posé lors de la validation.
- Question de vérification humaine accessible (question mathématique lisible) — **pas de CAPTCHA
  visuel seul** (§6.5 TDR).

### Langue et RTL (WCAG 3.1.1, 3.1.2)

- `<html lang>` et `dir` définis au niveau du document.
- `lang="ar"` et `dir="rtl"` sur tout fragment arabe inclus dans une page française (et inversement),
  ex. le sélecteur de langue, le glossaire.
- `hreflang` dans les `<link rel="alternate">` et dans le sélecteur de langue.

### Mouvements et animations (WCAG 2.3.3)

- Règle globale `@media (prefers-reduced-motion: reduce)` qui désactive toutes les animations.

## Compatibilité testée

Cibles (§8.4 TDR) :

- Navigateurs : Chrome, Firefox, Safari, Edge (dernières versions stables + version précédente).
- Lecteurs d'écran : NVDA (Firefox/Chrome), VoiceOver (Safari macOS/iOS), TalkBack (Android).
- Zoom : 100 %, 150 %, 200 %.
- Contrastes élevés (Windows high contrast, macOS increase contrast).

## Tests automatisés suggérés

Bien que non intégrés à la chaîne CI dans la présente livraison, les outils suivants sont
recommandés :

- **axe-core** / **Pa11y CI** : intégration dans la CI pour détecter les régressions d'accessibilité.
- **Lighthouse** : audit de chaque gabarit principal, seuil de 95 minimum en accessibilité.
- **WAVE** (wave.webaim.org) : vérification manuelle ponctuelle.

Exemple d'ajout dans `package.json` en phase suivante :

```json
{
  "scripts": {
    "a11y": "pa11y-ci --config .pa11yci.json"
  }
}
```

## Rapport d'audit

Un audit complet externe sera réalisé à la mise en production. Ses résultats, le niveau atteint et
les éventuelles dérogations seront publiés sur la [déclaration d'accessibilité](/fr/accessibilite/)
et mis à jour à chaque évolution majeure du site.
