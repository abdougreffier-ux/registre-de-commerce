# Procédure de déploiement

## Environnements (§4.1 TDR)

| Environnement | Rôle | URL type |
|---|---|---|
| Développement | Travail local des développeurs / éditeurs | http://localhost:8080 |
| Pré-production | Validation fonctionnelle, tests d'accessibilité et de charge | https://preprod.ccrcsm.gov.mr |
| Production | Site officiel public | https://www.ccrcsm.gov.mr |

## Construction

Sur toute machine ou serveur d'intégration disposant de Node ≥ 18 :

```bash
git clone <url-du-depot> ccrcsm-site
cd ccrcsm-site
npm ci              # installation reproductible depuis package-lock.json
npm run build       # produit le dossier _site/
```

Le dossier `_site/` est un **artefact statique** : n'importe quel serveur web peut le servir.

## Déploiement

### Option A — Serveur géré (NGINX)

1. Copier le contenu de `_site/` vers `/var/www/ccrcsm/_site/` (par exemple via `rsync --delete`).
2. Vérifier la configuration : [`server/nginx.conf`](../server/nginx.conf) (adapter chemins et
   domaine).
3. `sudo nginx -t && sudo systemctl reload nginx`.
4. Vérifier les en-têtes de sécurité : `curl -I https://www.ccrcsm.gov.mr`.

### Option B — Plateforme de publication statique (Netlify, Cloudflare Pages, …)

1. Connecter le dépôt Git.
2. Configurer : commande de build `npm run build`, dossier publié `_site`.
3. Placer [`server/_headers`](../server/_headers) à la racine du dossier publié.
4. Configurer le nom de domaine et l'HTTPS automatique.

### Option C — Docker (optionnel)

```Dockerfile
# Image de build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Image d'exécution : NGINX statique
FROM nginx:1.27-alpine
COPY --from=build /app/_site /usr/share/nginx/html
COPY server/nginx.conf /etc/nginx/conf.d/default.conf
```

## DNS et certificats (§8.5, §8.6 TDR)

- Nom de domaine recommandé : `ccrcsm.gov.mr` (ou `ccrcsm.mr`), déposé au nom du Ministère de la
  Justice.
- **DNSSEC** activé.
- **SPF / DKIM / DMARC** configurés sur le domaine pour les courriels institutionnels
  (`contact@ccrcsm.gov.mr`, notifications de saisines).
- Certificats TLS automatiques (Let's Encrypt) ou certificats institutionnels. Renouvellement
  automatique vérifié.

## Sauvegardes (§10.6 TDR)

### Fréquence

- **Quotidiennes** : dépôt Git (déjà implicite via hébergement Git) + sauvegarde des soumissions de
  formulaires (phase 2).
- **Hebdomadaires** : snapshot complet du serveur de production.

### Conservation

- Sauvegardes quotidiennes : 30 jours.
- Sauvegardes hebdomadaires : 6 mois.

### Chiffrement

- Chiffrement au repos (AES-256) avec clé stockée à part du support de sauvegarde.

### Restauration

- Procédure documentée dans le **runbook interne**.
- Test de restauration **au moins une fois par an** (§10.6 TDR), compte-rendu conservé.

### Objectifs

- **RPO** ≤ 24 h.
- **RTO** ≤ 8 h.

## Pré-flight checklist avant mise en production

- [ ] `npm run build` passe sans erreur ni avertissement.
- [ ] Lighthouse > 90 en accessibilité, performance, SEO sur l'accueil FR + AR.
- [ ] `curl -I` confirme tous les en-têtes de sécurité.
- [ ] Qualys SSL Labs : rang A ou A+.
- [ ] securityheaders.com : rang A ou A+.
- [ ] Vérification visuelle sur Chrome, Firefox, Safari.
- [ ] Vérification mobile (iOS Safari, Chrome Android).
- [ ] Vérification RTL : /ar/ — header, menu, fil d'Ariane, formulaires, tableaux.
- [ ] Recherche : `/fr/recherche/?q=avis` retourne des résultats.
- [ ] Flux RSS : `/fr/feeds/avis.xml` valide (feedvalidator.org).
- [ ] Sitemap : `/sitemap.xml` valide.
- [ ] `/404.html` s'affiche correctement (curl -I vers une URL inexistante renvoie 404).
- [ ] Formulaire de saisine : soumission → accusé de réception avec numéro de référence.
- [ ] Audit WCAG externe achevé et publié sur `/fr/accessibilite/`.

## Supervision (§11.4 TDR)

- Sonde de disponibilité externe (UptimeRobot ou équivalent) — vérification toutes les 5 min.
- Alerte courriel et SMS vers l'astreinte technique.
- Rapport mensuel au maître d'ouvrage.

## Procédure d'incident

- **Bloquant** (site indisponible, défiguration) : prise en charge immédiate, résolution < 4 h ouvrées.
- **Majeur** (fonctionnalité essentielle inopérante) : résolution < 24 h ouvrées.
- **Mineur** (confort d'usage) : résolution < 5 jours ouvrés.

Chaque incident fait l'objet d'un compte-rendu écrit : date, durée, impact, cause racine, correctif
appliqué, mesures préventives.
