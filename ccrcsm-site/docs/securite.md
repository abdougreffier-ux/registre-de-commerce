# Sécurité

## Modèle de menace

Compte tenu du caractère para-judiciaire du CCRCSM (§10.1 TDR), les risques critiques sont :

1. **Défiguration** : modification non autorisée de pages du site.
2. **Publication frauduleuse d'un avis** : contenu apparaissant comme officiel sans l'être.
3. **Fuite de données** : exposition des saisines reçues via le formulaire.
4. **Indisponibilité** : déni de service affectant un canal officiel de publication.

## Mesures en place

### Architecture statique

Le site étant servi en HTML statique, la surface d'attaque applicative est quasi nulle : pas
d'injection SQL possible, pas d'exécution de code au rendu. Les risques se déplacent vers le
serveur web et l'infrastructure, plus faciles à durcir.

### En-têtes HTTP de sécurité (§10.2 TDR)

Les fichiers [`server/nginx.conf`](../server/nginx.conf), [`server/apache.htaccess`](../server/apache.htaccess)
et [`server/_headers`](../server/_headers) configurent :

| En-tête | Valeur | Rôle |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | HSTS — force HTTPS |
| `Content-Security-Policy` | `default-src 'self'; ...` (stricte) | Anti-XSS, anti-injection d'actifs tiers |
| `X-Frame-Options` | `DENY` | Anti-clickjacking |
| `X-Content-Type-Options` | `nosniff` | Anti-MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limite la fuite d'URL |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), interest-cohort=()` | Désactive API sensibles |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isolement des onglets |
| `Cross-Origin-Resource-Policy` | `same-site` | Restriction du chargement tiers |

La **CSP est stricte** : `script-src 'self'`, `style-src 'self'` — pas de `'unsafe-inline'`. Le code
du site n'utilise aucun script ni style inline (c'est une règle d'ingénierie à maintenir).

### TLS (§10.3 TDR)

- TLS 1.2 et 1.3 uniquement ; suites de chiffrement modernes (ECDHE, AES-GCM, ChaCha20).
- HSTS activé **après** vérification du bon fonctionnement HTTPS.
- Redirection systématique HTTP → HTTPS.
- Stapling OCSP pour la vérification de révocation.

### Formulaire de saisine (§10.4 TDR)

Côté client (main.js + saisine-form.njk) :

- Validation progressive (longueur, email, PDF, taille ≤ 10 Mo).
- **Honeypot** invisible — un robot qui remplit tous les champs trahit sa nature.
- **Timestamp** d'ouverture du formulaire — le serveur peut rejeter toute soumission < 1.5 s (robot).
- **Question de vérification humaine** accessible (addition simple).
- `required`, `maxlength`, `accept`, `pattern` sur chaque champ.

Côté serveur (endpoint à implémenter en phase 3) :

- **Jeton CSRF** à valider pour chaque soumission.
- **Rate limiting** (NGINX : 5 req/min/IP).
- Vérification du honeypot et du timestamp.
- Vérification de la question humaine.
- Validation stricte des types et tailles.
- Stockage **chiffré au repos** (base de données chiffrée ou documents chiffrés).
- **Pas de stockage** de données sensibles non nécessaires.
- **Accusé de réception** avec numéro de référence, envoyé par courriel signé DKIM.

### Protection des données personnelles (§10.7 TDR)

Voir [/fr/confidentialite/](/fr/confidentialite/) et la page équivalente arabe.

Principes :

- **Minimisation** : le formulaire ne collecte que les champs strictement utiles.
- **Finalité** : traitement de la demande uniquement.
- **Durée de conservation** documentée.
- **Pas de cookie non essentiel**. Le `localStorage` utilisé pour mémoriser la langue est un stockage
  local non traçant — décrit sur la [page cookies](/fr/cookies/).
- **Pas de dépendance tierce** introduisant de cookies (polices auto-hébergées, pas de CDN).

### Sauvegardes (§10.6 TDR)

Voir [deploiement.md](deploiement.md).

- Sauvegarde quotidienne du dépôt Git et des données de formulaires.
- Conservation : 30 jours pour les quotidiennes, 6 mois pour les hebdomadaires.
- **Test de restauration** annuel, documenté.
- RPO ≤ 24 h, RTO ≤ 8 h conformément aux TDRs.

### Mises à jour (§10.5 TDR)

- `npm audit` au minimum avant chaque déploiement.
- Veille CVE sur les dépendances et le serveur (NGINX, OS).
- Toute mise à jour testée en **pré-production** avant la production.
- Correctifs de sécurité appliqués dans les 7 jours (critique : < 24 h).

### Gestion des accès (§6.4 TDR, phase 2)

En phase 2, l'interface d'administration utilisera OAuth via le fournisseur Git (GitHub/GitLab) avec :

- **Authentification à deux facteurs obligatoire** pour tous les comptes ;
- **Rôles distincts** : admin technique, admin fonctionnel, valideur juridique, éditeur, relecteur ;
- **Journal d'audit** = historique des commits Git (immuable) ;
- **Politique de mot de passe** déléguée au fournisseur Git (robuste par défaut).

## Règles d'ingénierie à maintenir

1. **Pas de script ni style inline**. La CSP sert aussi de garde-fou à cette règle.
2. **Pas d'innerHTML avec des données externes**. Utiliser `textContent` ou créer les éléments en JS.
3. **Pas de dépendance runtime tierce** (CDN, trackers, polices externes). Tout auto-héberger.
4. **Validation serveur systématique** pour toute soumission.
5. **Revue de code obligatoire** pour toute modification touchant `_includes/partials/saisine-form.njk`
   ou `src/assets/js/main.js`.

## Tests

- **Audit de sécurité** à la mise en production : scan OWASP ZAP, vérification TLS (Qualys SSL Labs
  visant rang A+), vérification des en-têtes (securityheaders.com visant rang A+).
- **Revue trimestrielle** de sécurité (§12.3 TDR) avec rapport au maître d'ouvrage.
- **Tests d'intrusion légers** à l'occasion des revues trimestrielles.
