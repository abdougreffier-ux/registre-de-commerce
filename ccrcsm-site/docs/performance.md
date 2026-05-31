# Performance et qualité

Objectifs §11 TDR : LCP ≤ 2.5 s, CLS ≤ 0.1, INP ≤ 200 ms (seuil « bon » Core Web Vitals) ; poids
total de page ≤ 1.5 Mo après chargement initial.

## Ce que le site met en œuvre

### Architecture

- **Pages statiques pré-rendues** : pas de rendu serveur, `Time to First Byte` minimal.
- **HTML, CSS, JS servis en gzip/brotli** (voir configs serveur).
- **Cache long (1 an, immuable)** sur les actifs (`/assets/*`) ; cache court (5 min,
  `must-revalidate`) sur le HTML.

### Poids

- **CSS monolithique** minifiable (~30 Ko hors compression), inlinable en optimisation future.
- **JS unique** minifiable (~6 Ko hors compression), chargé en `defer`.
- **Polices** WOFF2, variables, subsetable — cf. recommandations ci-dessous.
- **Icônes SVG inline** (pas d'appel HTTP externe).

### Chargement

- `<link rel="preload">` pour les polices critiques.
- `loading="lazy"` sur les images non visibles au-dessus de la ligne de flottaison.
- `<img width height>` obligatoires pour éviter le CLS.

### Sobriété (§11.3)

- **Aucune dépendance tierce runtime** : pas de Google Fonts, pas de Google Analytics, pas de Maps,
  pas de widgets réseaux sociaux. Les polices sont auto-hébergées.
- **Minimisation** des dépendances Node : seules Eleventy, le plugin RSS, Luxon et markdown-it.

## À réaliser pour atteindre l'objectif

Ces optimisations sont recommandées pour la mise en production :

### 1. Polices — subset

Noto Naskh Arabic et Inter sont fournies en version variable. Il est recommandé de produire un
sous-ensemble incluant uniquement :

- Latin de base + supplémentaire (pour l'apostrophe courbe, etc.) ;
- Arabe standard + caractères diacritiques.

Outils : `pyftsubset` (fonttools), `glyphhanger`.

Exemple :
```bash
pyftsubset Inter-Var.ttf \
  --unicodes="U+0020-007E,U+00A0-00FF,U+2010-2019,U+2022" \
  --flavor=woff2 \
  --layout-features='*' \
  --output-file=inter-var.woff2
```

### 2. Images

Fournir les images en **WebP + JPEG** via `<picture>`, avec versions adaptatives (`srcset`).

### 3. Compression serveur

Activer Brotli niveau 6 en complément de gzip (NGINX : compiler `ngx_brotli`).

### 4. HTTP/2 ou HTTP/3

Les configs NGINX et Apache fournies activent HTTP/2. HTTP/3 (QUIC) est à envisager selon la
version du serveur.

### 5. Mesures

- **Lighthouse** (CLI) en CI sur les gabarits principaux.
- **Sitespeed.io** ou **Webpagetest** pour des mesures réalistes en conditions mauritaniennes
  (latence élevée, bande passante variable). Le TDR §11.1 impose des tests explicites sur
  connexions à faible débit.

## Sobriété numérique — recommandations éditoriales

- Ne pas publier de vidéos lourdes sans compression (utiliser H.264/AV1).
- Préférer le HTML/CSS aux images pour présenter des tableaux, schémas simples.
- Éviter les PDF de plus de 5 Mo ; offrir également une version HTML quand c'est possible.

## Disponibilité (§11.4 TDR)

- **Cible** 99,5 % par an, hors maintenance programmée.
- **Supervision** par un service externe (UptimeRobot, Checkly, StatusCake) avec alerte courriel et
  SMS vers l'astreinte technique.
- **Incident** : les interventions sont documentées (date, durée, impact, cause, correctif) et
  suivent les délais du §12.1 TDR (bloquant < 4 h, majeur < 24 h, mineur < 5 j).
