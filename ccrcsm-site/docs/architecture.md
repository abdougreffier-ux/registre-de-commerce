# Architecture technique

## Principe directeur

Le site est un **site statique pré-rendu** généré par [Eleventy](https://www.11ty.dev/). Les pages
HTML sont produites à la compilation à partir de contenus Markdown/Nunjucks, de données JSON/JS et
de couches de templates. À la mise en production, le serveur ne sert que des fichiers statiques, sans
exécution applicative côté serveur pour le rendu.

Ce choix répond aux exigences du cahier des charges :

- **Sécurité (§10)** : surface d'attaque minimale — pas de base de données exposée, pas d'interprète
  au moment du rendu. Les seules composantes dynamiques sont (1) le formulaire de saisine, qui appelle
  un endpoint distinct, et (2) la future interface d'administration Git-based.
- **Performance (§11)** : les pages sont déjà optimisées au build ; le serveur n'a qu'à les servir.
- **Disponibilité (§11.4)** : un site statique est plus facile à rendre hautement disponible.
- **Pérennité (§8.1)** : technologies matures (HTML/CSS/JS), pas de dépendance éditeur propriétaire.

## Pile technique

| Couche | Choix | Justification |
|---|---|---|
| Générateur | **Eleventy 3.x** | Mature, Node.js, pas de « magic », excellent support multilingue et markdown |
| Templates | **Nunjucks** | Autoescaping par défaut (anti-XSS), syntaxe lisible, familier aux intégrateurs |
| Contenus | **Markdown** (avec front-matter YAML) + **.njk** pour les templates dynamiques | Markdown facilite l'édition par des non-développeurs |
| Styles | **CSS3 moderne** (propriétés logiques, variables CSS, Grid, Flexbox) | Pas de pré-processeur, compilation native moderne |
| Scripts | **JavaScript vanilla** (ES2020) | Pas de framework côté client, surface minimale |
| Polices | **Inter** (latin) + **Noto Naskh Arabic** (arabe) — auto-hébergées | §7.3 TDR : servies localement |
| Recherche | **Index JSON + moteur client** | Pas de backend ; adapté à un petit volume |
| Flux | **Atom** via plugin officiel | Standard |

## Arborescence

Voir [README.md](../README.md#structure-du-projet).

### Répartition des responsabilités

- `src/_data/` : **source de vérité** des métadonnées et traductions d'interface.
  - `site.js` : identité institutionnelle (noms, contact, URLs)
  - `i18n.js` : toutes les chaînes d'interface FR/AR
  - `navigation.js` : structure des menus
  - `glossaire.js` : terminologie juridique bilingue
- `src/_includes/layouts/` : squelettes HTML.
- `src/_includes/partials/` : fragments réutilisables.
- `src/fr/` et `src/ar/` : **arborescence de contenus**, symétriques.
- `src/assets/` : CSS, JS, polices, images — copiés tels quels vers `_site/assets/`.
- `server/` : configurations serveur pour la production.

### Règle de symétrie FR ↔ AR

Chaque page `src/fr/<chemin>.md` doit avoir son équivalent `src/ar/<chemin>.md`. Le filtre
`eleventyComputed.alternate` calcule l'URL équivalente pour le lien `<link rel="alternate">` et
pour le sélecteur de langue. Rompre la symétrie (pour un texte n'existant que dans une langue
faisant foi) est autorisé mais doit être signalé dans la page par un bandeau.

## Collections

Définies dans `.eleventy.js` :

| Collection | Contenu |
|---|---|
| `avis_fr` / `avis_ar` | Avis du Comité |
| `actualites_fr` / `actualites_ar` | Actualités |
| `communiques_fr` / `communiques_ar` | Communiqués |
| `textes_fr` / `textes_ar` | Textes juridiques |
| `searchIndexFr` / `searchIndexAr` | Index de recherche |

Chaque item porte des métadonnées typées : `title`, `date`, `description`, `type`, `reference`,
`rubrique`. Ces champs sont consommés par les listings, l'index de recherche et les flux RSS.

## Flux de génération

```
src/ (Markdown + Nunjucks + data)
  └─> Eleventy (au build)
        ├─> _site/ (HTML statique)
        ├─> _site/assets/js/search-index.fr.json
        ├─> _site/assets/js/search-index.ar.json
        ├─> _site/fr/feeds/avis.xml, _site/fr/feeds/actualites.xml
        ├─> _site/ar/feeds/avis.xml, _site/ar/feeds/actualites.xml
        ├─> _site/sitemap.xml
        └─> _site/404.html
```

## Évolutions prévues

### Phase 2 — CMS Git-based

Ajout de **Decap CMS** (anciennement Netlify CMS) pour l'administration éditoriale. Il s'agit d'une
interface web servie en statique qui lit et écrit directement dans le dépôt Git.

Bénéfices :

- Workflow de validation natif (brouillon / relecture / publication) (§6.3 TDR) ;
- Authentification OAuth via fournisseur Git ;
- Pas de base de données supplémentaire ;
- Journal d'audit = historique Git (immuable, §6.3 TDR).

### Phase 3 — Traitement serveur du formulaire de saisine

Endpoint minimaliste (Node/Express ou équivalent) derrière NGINX :

- réception de la soumission `/{locale}/saisine/` ;
- validation CSRF, anti-spam (honeypot + timestamp + question) ;
- génération d'un numéro de référence ;
- notification par courriel au secrétariat ;
- accusé de réception à l'expéditeur.

## Évolutivité et réversibilité (§12.4, §12.5 TDR)

- Tout le code est versionné en Git, avec historique complet.
- Les contenus sont en Markdown, portable vers tout autre générateur.
- Aucune dépendance à un éditeur propriétaire.
- Licence des dépendances vérifiée : toutes open source permissives.
