# Site institutionnel bilingue du CCRCSM

Site web institutionnel du **Comité de Coordination du Registre du Commerce et des Sûretés
Mobilières** (CCRCSM), organe para-judiciaire placé auprès du Ministère de la Justice de la
République Islamique de Mauritanie.

Le site est **bilingue** français / arabe (avec RTL complet), conçu conformément aux Termes de
Référence du maître d'ouvrage (v1.0, Nouakchott, 2026).

## Sommaire de la documentation

- [README.md](README.md) — présent fichier : installation, développement, déploiement.
- [docs/architecture.md](docs/architecture.md) — choix techniques et arborescence du code.
- [docs/editorial.md](docs/editorial.md) — charte éditoriale, règles de publication, flux de validation.
- [docs/bilinguisme-rtl.md](docs/bilinguisme-rtl.md) — gestion du bilinguisme et du RTL.
- [docs/accessibilite.md](docs/accessibilite.md) — mise en œuvre WCAG 2.1 AA.
- [docs/securite.md](docs/securite.md) — mesures de sécurité applicative et serveur.
- [docs/performance.md](docs/performance.md) — objectifs et pratiques de performance.
- [docs/deploiement.md](docs/deploiement.md) — procédure de déploiement et de sauvegarde.

## Périmètre de la présente livraison

Cette livraison correspond au **prototype fonctionnel (L3)** prévu par les TDRs :

- arborescence complète et contenus synchronisés FR/AR ;
- respect des exigences WCAG 2.1 AA, CSP stricte, HSTS, HTTPS ;
- moteur de recherche interne côté client (index JSON construit au build) ;
- flux RSS (Atom) pour les avis et les actualités ;
- formulaire de saisine avec validation progressive (client + structure pour serveur) ;
- pages de conformité (accessibilité, confidentialité, cookies, mentions légales).

Le **CMS Git-based** (Decap CMS / équivalent) et le **traitement serveur** du formulaire de saisine
ne sont pas encore installés ; ils font l'objet d'un lot complémentaire (voir *docs/architecture.md*,
§ « Évolutions prévues »).

## Prérequis

- **Node.js** ≥ 18 (l'équipe utilise la version 20 LTS — voir [.nvmrc](.nvmrc)) ;
- un gestionnaire de paquets : `npm` (inclus) ou `pnpm`.

## Installation

```bash
# 1. Cloner le dépôt, puis depuis le dossier du projet :
npm install

# 2. Lancer le serveur de développement avec rechargement à chaud
npm run dev
# Le site est servi sur http://localhost:8080
```

## Commandes

| Commande | Rôle |
|---|---|
| `npm run dev` | Démarre Eleventy en mode watch + serveur local |
| `npm run build` | Génère le site de production dans `_site/` |
| `npm run clean` | Supprime le dossier `_site/` |
| `npm run serve` | Sert le site de production local (sans rebuild watch) |

## Structure du projet

```
ccrcsm-site/
├── .eleventy.js           # Configuration Eleventy (filtres, collections, passthrough)
├── package.json
├── src/
│   ├── _data/             # Données globales (site, i18n, navigation, glossaire)
│   ├── _includes/
│   │   ├── layouts/       # base.njk, page.njk, article.njk, home.njk
│   │   └── partials/      # header, footer, lang-switcher, breadcrumb, saisine-form
│   ├── assets/
│   │   ├── css/main.css   # CSS modulaire, RTL via propriétés logiques
│   │   ├── js/main.js     # Menu mobile, validation, recherche
│   │   ├── fonts/         # Polices auto-hébergées (Inter, Noto Naskh Arabic)
│   │   └── img/           # Logos, favicons, pictogrammes SVG
│   ├── fr/                # Arborescence française
│   │   ├── fr.11tydata.js # Données par défaut (locale, layout, alternate)
│   │   ├── index.njk      # Accueil
│   │   ├── le-comite.md
│   │   ├── organigramme.md
│   │   ├── partenaires.md
│   │   ├── glossaire.njk
│   │   ├── textes/        # Textes juridiques
│   │   ├── publications/  # Avis, communiqués, actualités
│   │   ├── services/      # Formulaires, guides, FAQ
│   │   ├── contact.njk
│   │   ├── recherche.njk
│   │   ├── feeds/         # Flux Atom
│   │   ├── plan-du-site.njk
│   │   ├── accessibilite.md
│   │   ├── confidentialite.md
│   │   ├── cookies.md
│   │   └── mentions-legales.md
│   ├── ar/                # Arborescence arabe (miroir de fr/)
│   ├── 404.njk            # Page d'erreur bilingue
│   ├── sitemap.xml.njk    # Sitemap XML avec hreflang
│   ├── robots.txt
│   └── index.njk          # Redirige / vers /fr/
├── server/
│   ├── nginx.conf         # Configuration NGINX de référence
│   ├── apache.htaccess    # Équivalent Apache
│   └── _headers           # Netlify / Cloudflare Pages
└── docs/                  # Documentation technique et éditoriale
```

## Conventions de contenu

- **Pas de contenu publié que dans une seule langue** sans justification explicite (bandeau de page).
- **Terminologie juridique** validée par le secrétariat : toute modification du
  [glossaire](src/_data/glossaire.js) requiert validation.
- **Identifiants stables** : chaque avis porte un nom de fichier pérenne (ex. `avis-2026-001.md`)
  et une URL non réutilisée.
- Voir [docs/editorial.md](docs/editorial.md).

## Licence

Le code source produit dans le cadre du marché est cédé au CCRCSM conformément aux §12.5 des TDRs.
Les dépendances tierces conservent leur licence d'origine (toutes open source permissives).

## Contact

Maître d'ouvrage : Comité de Coordination du Registre du Commerce et des Sûretés Mobilières —
Ministère de la Justice, République Islamique de Mauritanie.
