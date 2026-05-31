/**
 * Génère le document Word L8 — Note d'architecture technique et de déploiement.
 *
 * Format A4, charte officielle RIM (couleurs vert/rouge/jaune en accents),
 * police Arial.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, PageOrientation, LevelFormat,
  PositionalTab, PositionalTabAlignment, PositionalTabRelativeTo,
  PositionalTabLeader, TabStopType, TabStopPosition,
  HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber,
  PageBreak, VerticalAlign, ExternalHyperlink,
} = require("docx");

// ---------------------------------------------------------------------------
// Charte couleurs RIM (palette officielle, mai 2020)
// ---------------------------------------------------------------------------
const RIM_VERT = "00A95C";
const RIM_ROUGE = "D01C1F";
const RIM_JAUNE = "FFD700";
const NEUTRAL_FILL = "F2F2F2";
const ACCENT_LIGHT = "E9F7F0";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const border = (color = "CCCCCC", size = 1) => ({
  style: BorderStyle.SINGLE, size, color,
});
const borders = {
  top: border(), bottom: border(), left: border(), right: border(),
};

function p(text, opts = {}) {
  if (text === "") return new Paragraph({ children: [new TextRun(" ")] });
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 120 },
    ...(opts.alignment ? { alignment: opts.alignment } : {}),
  });
}

function h(text, level) {
  const map = { 1: HeadingLevel.HEADING_1, 2: HeadingLevel.HEADING_2,
                3: HeadingLevel.HEADING_3 };
  return new Paragraph({
    heading: map[level],
    children: [new TextRun({ text })],
  });
}

function bullet(text) {
  return new Paragraph({
    text, bullet: { level: 0 }, spacing: { after: 60 },
  });
}

function tCell({ text = "", bold = false, fill, color, align = AlignmentType.LEFT,
                  paragraphs, width, colSpan }) {
  return new TableCell({
    borders,
    width: width ? { size: width, type: WidthType.DXA } : undefined,
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    columnSpan: colSpan,
    children: paragraphs || [
      new Paragraph({
        alignment: align,
        children: [new TextRun({
          text, bold,
          color, font: "Arial", size: 20,
        })],
      }),
    ],
  });
}

function table(headers, rows, columnWidths) {
  const totalWidth = columnWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((titre, i) => tCell({
          text: titre, bold: true, fill: ACCENT_LIGHT,
          width: columnWidths[i],
        })),
      }),
      ...rows.map((row) => new TableRow({
        children: row.map((cell, i) => {
          if (cell && typeof cell === "object" && "text" in cell) {
            return tCell({ ...cell, width: columnWidths[i] });
          }
          return tCell({ text: String(cell || ""), width: columnWidths[i] });
        }),
      })),
    ],
  });
}

// ---------------------------------------------------------------------------
// Construction du document
// ---------------------------------------------------------------------------
const doc = new Document({
  creator: "Tribunal de commerce de Nouakchott",
  title: "L8 — Note d'architecture technique et de déploiement",
  description: "Système du Registre des Sûretés Mobilières (RSM)",
  styles: {
    default: {
      document: {
        run: { font: "Arial", size: 22 },
        paragraph: { spacing: { line: 320 } },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: RIM_VERT },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "1A1A1A" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 23, bold: true, font: "Arial", color: "1A1A1A" },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0, format: LevelFormat.BULLET, text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          // A4 : 210 × 297 mm = 11906 × 16838 DXA
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            children: [
              new TextRun({
                text: "République Islamique de Mauritanie — Tribunal de commerce de Nouakchott",
                size: 16, color: "707070",
              }),
              new TextRun({
                children: [new PositionalTab({
                  alignment: PositionalTabAlignment.RIGHT,
                  relativeTo: PositionalTabRelativeTo.MARGIN,
                })],
              }),
              new TextRun({
                text: "L8 — Note d'architecture",
                size: 16, color: "707070", bold: true,
              }),
            ],
            border: {
              bottom: { style: BorderStyle.SINGLE, size: 6,
                        color: RIM_VERT, space: 4 },
            },
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
                text: "Système du Registre des Sûretés Mobilières — page ",
                size: 16, color: "707070",
              }),
              new TextRun({ children: [PageNumber.CURRENT],
                            size: 16, color: "707070" }),
              new TextRun({ text: " / ", size: 16, color: "707070" }),
              new TextRun({ children: [PageNumber.TOTAL_PAGES],
                            size: 16, color: "707070" }),
            ],
          })],
        }),
      },
      children: [
        // ---------------------------------------------------------------- COVER
        new Paragraph({ children: [new TextRun(" ")], spacing: { before: 1200 } }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "RÉPUBLIQUE ISLAMIQUE DE MAURITANIE",
            bold: true, size: 24, color: RIM_VERT,
          })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "Honneur — Fraternité — Justice",
            italics: true, size: 20, color: "707070",
          })],
          spacing: { after: 200 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "Tribunal de commerce de Nouakchott",
            bold: true, size: 26, color: RIM_ROUGE,
          })],
          spacing: { after: 800 },
          border: {
            top: { style: BorderStyle.SINGLE, size: 6, color: RIM_ROUGE, space: 6 },
            bottom: { style: BorderStyle.SINGLE, size: 6, color: RIM_ROUGE, space: 6 },
          },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "L8",
            bold: true, size: 72, color: RIM_VERT,
          })],
          spacing: { after: 200 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "Note d'architecture technique et de déploiement",
            bold: true, size: 36,
          })],
          spacing: { after: 240 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "Système du Registre des Sûretés Mobilières (RSM)",
            size: 24, italics: true, color: "404040",
          })],
          spacing: { after: 1200 },
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text:
              "Document officiel à destination du prestataire d'hébergement, " +
              "de déploiement et d'exploitation. À jour de l'état du système. " +
              "Aucun extrait de code source ni élément confidentiel n'y figure.",
            size: 20, italics: true, color: "404040",
          })],
        }),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- TOC
        h("Sommaire", 1),
        ...[
          "1.  Présentation générale du système",
          "2.  Architecture globale",
          "3.  Stack technique détaillée",
          "4.  Gestion des utilisateurs et des rôles",
          "5.  Workflow métier RCCM / Sûretés mobilières",
          "6.  Génération de documents officiels",
          "7.  Sécurité et intégrité",
          "8.  Déploiement et exploitation",
          "9.  Contraintes d'hébergement",
          "10. Points d'attention pour l'hébergeur",
          "Annexe A — Conformité bilingue FR / AR",
          "Annexe B — Documents associés",
          "Annexe C — Glossaire technique",
        ].map((entry) => new Paragraph({
          children: [new TextRun({ text: entry, size: 22 })],
          spacing: { after: 80 },
        })),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 1
        h("1. Présentation générale du système", 1),
        h("1.1 Objectif", 2),
        p("Le Registre des Sûretés Mobilières (RSM) est l'outil informatique de mise en œuvre du chapitre IV — articles 76 à 97 — du décret 2021-033 relatif au Registre du commerce et des sûretés mobilières. Sa finalité est triple :"),
        bullet("Publicité des sûretés mobilières et opposabilité aux tiers (art. 76)."),
        bullet("Conservation intégrale des informations régulièrement enregistrées, sans suppression possible (art. 79)."),
        bullet("Délivrance de certificats à valeur probante en regard de l'article 97."),
        p("Le système est entièrement informatisé conformément à l'article 77."),

        h("1.2 Rôle du registre dans l'écosystème RCCM / Greffe", 2),
        p("Le RSM se distingue institutionnellement du RCCM (Registre du commerce et du crédit mobilier) tout en étant rattaché au même Greffe du Tribunal de commerce de Nouakchott. Le RCCM identifie les commerçants et les sociétés ; le RSM publie les sûretés grevant des biens mobiliers, qu'ils appartiennent à un commerçant inscrit ou à toute autre personne. Les deux systèmes sont indépendants techniquement mais peuvent être interconnectés à terme (cf. fiche MO F13)."),

        h("1.3 Acteurs", 2),
        p("Sept rôles applicatifs limitatifs (TDR § 4.1), plus l'usager public anonyme :"),
        table(
          ["Rôle", "Rôle métier", "Permission métier principale"],
          [
            ["agent_saisie", "Agent de saisie au guichet", "Enregistrer une demande"],
            ["autorite_validation", "Greffier", "Valider ou rejeter une demande (art. 80, 86)"],
            ["declarant_externe", "Personne agréée pour le portail externe", "Déposer en ligne (art. 78, 81, 84)"],
            ["auditeur", "Contrôleur / juge commis (art. 83)", "Lecture seule du journal d'audit"],
            ["prod_stats", "Producteur de statistiques", "Extractions monopole greffe (art. 82)"],
            ["admin_fonctionnel", "Administrateur fonctionnel", "Référentiels, comptes, rôles ; aucun accès écriture métier"],
            ["admin_technique", "Administrateur technique", "Exploitation système ; aucun accès utile aux contenus"],
            ["Usager public", "Anonyme", "Recherche publique art. 94-97, sans authentification"],
          ],
          [2200, 3000, 4160],
        ),
        p("Règle de séparation stricte : un même utilisateur ne peut pas cumuler agent_saisie et autorite_validation sur la même demande."),

        h("1.4 Environnements", 2),
        p("Deux environnements logiques distincts, pilotés par la variable RSM_MODE_TEST :"),
        table(
          ["Environnement", "RSM_MODE_TEST", "Vocation"],
          [
            ["TEST / RECETTE", "true", "Recette fonctionnelle, formation, démonstrations. Bandeau permanent « MODE TEST — AUCUNE VALEUR JURIDIQUE »."],
            ["PRODUCTION", "false", "Régime opérationnel opposable. Bandeau masqué, règles de sécurité durcies."],
          ],
          [3000, 2000, 4360],
        ),
        p("Toute donnée produite en TEST porte cette mention et n'a aucune valeur juridique."),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 2
        h("2. Architecture globale", 1),
        h("2.1 Vue d'ensemble", 2),
        p("Architecture trois-tiers classique, sans couplage fort entre les couches :"),
        new Paragraph({
          children: [new TextRun({
            text: [
              "   ┌────────────────────────────────────────┐",
              "   │  Navigateur (poste agent / usager)     │",
              "   │  → Interface React (SPA)               │",
              "   └───────────────┬────────────────────────┘",
              "                   │ HTTPS — JSON sur HTTP/1.1",
              "                   │ Cookie session + (CSRF en prod)",
              "                   ▼",
              "   ┌────────────────────────────────────────┐",
              "   │  Reverse proxy (recommandé : nginx)    │",
              "   │  - terminaison TLS                     │",
              "   │  - en-têtes de sécurité                │",
              "   │  - répartition statique / dynamique    │",
              "   └───────────┬───────────────────┬────────┘",
              "       statique│           dynamique│",
              "               ▼                   ▼",
              "   ┌──────────────────┐    ┌──────────────────────┐",
              "   │  Static / CDN    │    │  Application Django  │",
              "   │  (build React)   │    │  + DRF (API JSON)    │",
              "   └──────────────────┘    └────────┬─────────────┘",
              "                                    │",
              "                                    ▼",
              "                           ┌────────────────────┐",
              "                           │  PostgreSQL 14+    │",
              "                           │  (prod : 16 ou 18) │",
              "                           │  - tables métier   │",
              "                           │  - triggers audit  │",
              "                           │  - index FR/AR     │",
              "                           └────────────────────┘",
            ].join("\n"),
            font: "Consolas", size: 16,
          })],
          spacing: { after: 200 },
        }),

        h("2.2 Séparation des responsabilités", 2),
        table(
          ["Couche", "Responsabilité", "Ne fait pas"],
          [
            ["Frontend SPA", "Présentation, navigation, formulaires dynamiques, validation ergonomique", "Aucune règle métier, aucune autorisation autoritative"],
            ["API REST (Django + DRF)", "Règles métier, autorisations, validations strictes, audit, transactions", "Aucun rendu HTML métier (sauf admin Django, lecture seule)"],
            ["Base de données (PostgreSQL)", "Persistance, contraintes d'intégrité, triggers append-only", "Aucune logique applicative au-delà des contraintes"],
          ],
          [2400, 3500, 3460],
        ),
        p("Cette séparation garantit que :"),
        bullet("la règle métier autoritative est centralisée côté serveur ;"),
        bullet("le frontend peut être remplacé sans réécrire les règles ;"),
        bullet("l'auditeur consulte les données via une vue lecture seule sans passer par l'application."),

        h("2.3 Flux principaux", 2),
        new Paragraph({ children: [new TextRun({ text: "Connexion : ", bold: true }), new TextRun("POST /api/v1/auth/login/ → cookie de session Django, vérifiable via GET /api/v1/auth/whoami/.")], spacing: { after: 120 } }),
        new Paragraph({ children: [new TextRun({ text: "Dépôt d'inscription (art. 85) : ", bold: true }), new TextRun("authentification (declarant_externe ou agent_saisie), POST /api/v1/inscriptions/ avec les 6 champs scalaires (canal, nature, somme, monnaie, durée, e-mail), création + transition automatique RECUE → EN_CONTROLE_FORME, écriture du journal d'audit.")], spacing: { after: 120 } }),
        new Paragraph({ children: [new TextRun({ text: "Validation par le greffier : ", bold: true }), new TextRun("authentification (autorite_validation), POST /api/v1/inscriptions/<ref>/valider/ → attribution du numéro d'ordre horodaté (art. 78 al. 4), calcul de la date d'expiration, transition vers INSCRITE.")], spacing: { after: 120 } }),
        new Paragraph({ children: [new TextRun({ text: "Consultation publique : ", bold: true }), new TextRun("POST /api/v1/recherche/ avec deux critères au moins parmi les quatre énumérés à l'article 96 ; aucune authentification requise (art. 94).")], spacing: { after: 200 } }),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 3
        h("3. Stack technique détaillée", 1),
        h("3.1 Frontend", 2),
        table(
          ["Technologie", "Rôle", "Justification"],
          [
            ["React 18", "Bibliothèque UI déclarative", "Standard de l'industrie, large communauté, rendu prévisible, isolation des erreurs."],
            ["react-router-dom 6", "Routage côté client", "Permet une SPA sans rechargement complet."],
            ["Ant Design 5", "Système de composants UI", "Bibliothèque mature avec support natif RTL (arabe), formulaires complexes, accessibilité par défaut."],
            ["i18next", "Internationalisation FR/AR", "Architecture clé/valeur identique en FR et AR, garantie de parité (TDR § 7)."],
            ["Axios", "Client HTTP", "Intercepteurs (langue, CSRF, formatage des erreurs métier)."],
            ["dayjs", "Manipulation de dates", "Léger, fuseau horaire Africa/Nouakchott."],
          ],
          [2200, 2800, 4360],
        ),
        p("Build : react-scripts (Create React App). En production, le bundle est généré une fois (npm run build) puis servi statiquement."),

        h("3.2 Backend", 2),
        table(
          ["Technologie", "Rôle", "Justification"],
          [
            ["Python 3.12", "Runtime", "Long-term support, performance, larges bibliothèques disponibles."],
            ["Django 4.2 LTS", "Framework web", "Maturité, ORM robuste, admin auto-générée pour la lecture seule, écosystème complet."],
            ["Django REST Framework", "Couche API", "Sérialisation stricte, classes de permissions composables, gestion native de l'authentification de session."],
            ["django-decouple", "Configuration via .env", "Sépare proprement les secrets du code."],
            ["django-filter", "Filtrage paginé", "Recherche avec critères multiples sans réinventer un parseur."],
            ["django-cors-headers", "Politique CORS", "Maîtrise fine des origines autorisées en production."],
            ["whitenoise", "Service des fichiers statiques", "Permet à Django de servir les statiques sans dépendre d'un nginx tiers en environnement contraint."],
            ["pillow", "Traitement image (sceau, logo)", "Standard."],
          ],
          [2400, 2700, 4260],
        ),

        h("3.3 Base de données", 2),
        p("PostgreSQL 14+ (testé sur PostgreSQL 18, recommandé en production PostgreSQL 16 LTS). Choix justifié :"),
        bullet("Triggers SQL utilisés pour matérialiser le caractère append-only du journal d'audit (article 79) — interdit toute mise à jour ou suppression directement au niveau du moteur."),
        bullet("Index full-text capables de gérer simultanément le français et l'arabe (extension pg_trgm recommandée)."),
        bullet("Transactions ACID strictes, indispensables pour l'attribution séquentielle du numéro d'ordre (art. 78 al. 4)."),
        bullet("JSONB pour les schémas dynamiques (catégories de biens, attributs spécifiques) avec indexation possible."),
        bullet("Contraintes d'unicité partielles (ex. une seule version active par catégorie de bien, séparation stricte des rôles)."),

        h("3.4 Frameworks et bibliothèques accessoires", 2),
        bullet("Tests backend : unittest + django.test.TestCase (150 tests applicatifs au moment de la rédaction)."),
        bullet("Migrations : Django migrations classiques + migrations de données pour le seed des référentiels (catégories de biens, natures de droits)."),
        bullet("Validation des mots de passe : AUTH_PASSWORD_VALIDATORS Django (longueur, similarité avec l'identifiant, mots de passe communs, contenu numérique)."),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 4
        h("4. Gestion des utilisateurs et des rôles", 1),
        h("4.1 Typologie des comptes", 2),
        table(
          ["Origine", "Création", "Cycle de vie"],
          [
            ["Administrateur fonctionnel", "Création par admin_technique (premier compte par createsuperuser)", "Mot de passe initial obligatoire à changer"],
            ["Comptes greffe", "Création par admin_fonctionnel", "Idem ; affectation des rôles via l'interface d'administration"],
            ["Déclarants externes", "Création par admin_fonctionnel après agrément", "Idem ; cible production avec MFA (cf. fiche F2)"],
            ["Auditeur", "Création par admin_fonctionnel ; en lecture seule", "Compte révocable mais traces conservées"],
          ],
          [3000, 3300, 3060],
        ),

        h("4.2 Rôles applicatifs et séparation des responsabilités", 2),
        p("Les rôles sont matérialisés par la table AffectationRole qui lie un utilisateur à un rôle parmi la liste limitative des sept rôles. Une contrainte applicative refuse explicitement le cumul des rôles incompatibles (agent_saisie + autorite_validation)."),
        p("Chaque endpoint API protégé applique une vérification de rôle. Les administrateurs (fonctionnel et technique) n'ont jamais accès en écriture aux entités métier (inscription, modification, radiation, renouvellement) : leurs permissions sont restreintes à l'administration des comptes, des référentiels et de l'exploitation."),

        h("4.3 Authentification et sessions", 2),
        p("L'authentification repose sur la session Django (cookie sessionid), gérée par DRF via SessionAuthentication. Le cookie est marqué HttpOnly et SameSite=Lax. Le jeton CSRF (csrftoken) est posé automatiquement par l'endpoint whoami au premier appel ; en mode TEST, l'enforcement CSRF est désactivé pour faciliter la recette avec proxy de développement, mais la session reste exigée."),
        p("Endpoints d'authentification :"),
        table(
          ["Méthode", "URL", "Rôle"],
          [
            ["GET", "/api/v1/auth/whoami/", "État courant + cookie csrf"],
            ["POST", "/api/v1/auth/login/", "Connexion"],
            ["POST", "/api/v1/auth/logout/", "Déconnexion"],
            ["POST", "/api/v1/auth/changer-mot-de-passe/", "Changement autonome du mot de passe"],
          ],
          [1500, 4000, 3860],
        ),

        h("4.4 Gestion des mots de passe", 2),
        table(
          ["Aspect", "Mode TEST", "Cible production"],
          [
            ["Mot de passe initial", "Fixé par l'administrateur", "Idem"],
            ["Drapeau de changement obligatoire", "mot_de_passe_initial = true à la création", "Idem"],
            ["Garde de redirection", "Frontend redirige systématiquement vers la page de changement tant que le drapeau est posé", "Idem + permission backend (cf. F2)"],
            ["Validateurs", "Validateurs Django par défaut", "À renforcer (longueur ≥ 12, complexité, historique)"],
            ["MFA", "Désactivé (RSM_MFA_MODE=disabled)", "À activer après transmission des paramètres F2"],
            ["Stockage", "Hashage Django (PBKDF2-SHA256 par défaut)", "Idem ou Argon2"],
          ],
          [3000, 3000, 3360],
        ),
        p("Aucune entrée d'audit métier (art. 79) n'est produite par le changement de mot de passe : il s'agit d'une opération technique."),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 5
        h("5. Workflow métier RCCM / Sûretés mobilières", 1),
        h("5.1 Statuts d'inscription", 2),
        p("Liste limitative, alignée sur § 4.3 du TDR :"),
        table(
          ["Code", "Sens", "Visibilité tiers"],
          [
            ["recue", "Demande enregistrée, prise en charge en cours", "Non (transitoire)"],
            ["en_controle_forme", "En attente de décision du greffier", "Oui (interne)"],
            ["rejetee", "Décision motivée art. 80", "Oui"],
            ["inscrite", "Sûreté en cours de validité, publiée au fichier public", "Oui (recherche art. 94)"],
            ["modifiee", "Une modification (art. 88) a été appliquée", "Oui"],
            ["renouvelee", "Période d'effet prorogée (art. 91)", "Oui"],
            ["radiee", "Radiation enregistrée (art. 92)", "Oui (mention « radiée »)"],
            ["expiree", "Date d'expiration atteinte", "Non (sortie du fichier public)"],
            ["archivee", "Transférée au fichier général (art. 79)", "Non"],
          ],
          [2400, 4400, 2560],
        ),

        h("5.2 Dépôt d'inscription (art. 85)", 2),
        p("Champs strictement acceptés à la création : canal, nature, somme, monnaie, durée, e-mail. La saisie des parties et des biens grevés relève de la modification (art. 88) ; aucune autre clé n'est acceptée par le serializer."),
        p("Conformément à l'article 86, le greffier ne vérifie pas l'identité du déposant ni les énonciations contenues : seul le respect des motifs limitatifs de rejet (art. 80) est contrôlé."),

        h("5.3 Validation / rejet", 2),
        table(
          ["Action", "Effet"],
          [
            ["Validation", "Attribution du numéro d'ordre NNNNNN-AAAAMMJJHHMMSS (art. 78 al. 4), calcul de la date d'expiration, transition vers INSCRITE, journal d'audit."],
            ["Rejet", "Sélection d'un motif limitatif (canal_non_autorise, informations_illisibles, informations_incomprehensibles), commentaires FR et AR optionnels, transition vers REJETEE."],
          ],
          [2200, 7160],
        ),

        h("5.4 Modification (art. 88)", 2),
        p("Une demande de modification porte un différentiel structuré (diff_propose) avec trois clés autorisées : parties, biens, scalaires. Toute clé hors schéma est rejetée. Le service d'application contrôle automatiquement les motifs limitatifs de refus (art. 88 dernier alinéa) : un état final vidant les constituants, les créanciers garantis ou les biens sans en désigner de nouveaux est sans effet."),

        h("5.5 Renouvellement (art. 91)", 2),
        p("Une demande de renouvellement n'est recevable que si l'inscription est encore en cours de validité. La période est prorogée d'une durée égale à la durée initiale (interprétation TDR § 9.3)."),

        h("5.6 Radiation (art. 92)", 2),
        p("Trois fondements limitatifs : consentement, jugement, requérant original. L'inscription radiée demeure au fichier public avec la mention « radiée » jusqu'à la date d'expiration, puis bascule au fichier général."),

        h("5.7 Catégories de biens (référentiel versionné)", 2),
        p("Le référentiel comporte 18 catégories (véhicules, matériel professionnel, stocks et marchandises, etc.) avec, pour chacune, un schéma de champs propres (libellés FR et AR, type, caractère obligatoire). Le référentiel est :"),
        bullet("versionné : chaque modification crée une nouvelle version ;"),
        bullet("non rétroactif : les biens déjà déposés conservent la version utilisée à la saisie ;"),
        bullet("verrouillé : une version utilisée par au moins un bien grevé devient immuable, toute évolution passe par la publication d'une nouvelle version ;"),
        bullet("administré par les rôles autorite_validation et admin_fonctionnel via une interface dédiée (/admin/categories-biens)."),

        h("5.8 Traçabilité", 2),
        p("Toute action métier produit une entrée dans le journal d'audit (apps.audit.models.EntreeAudit) avec : instant, acteur, rôle, objet (référence d'inscription), action, résultat, contexte et chaînage par hachage cryptographique. La table est protégée à deux niveaux :"),
        bullet("Application : la méthode save lève PermissionError si pk is not None (interdiction de mise à jour) et la méthode delete est interdite."),
        bullet("Base de données : un trigger PostgreSQL (rsm_audit_pas_update, rsm_audit_pas_delete) refuse toute opération UPDATE ou DELETE sur la table d'audit, indépendamment du chemin applicatif."),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 6
        h("6. Génération de documents officiels", 1),
        h("6.1 Types de documents prévus", 2),
        table(
          ["Document", "Article", "Moment de génération"],
          [
            ["Certificat d'inscription", "Art. 78 al. 3, 86", "Après validation par le greffier"],
            ["Certificat de modification", "Art. 88-90", "Après application d'une modification"],
            ["Certificat de renouvellement", "Art. 91", "Après application d'un renouvellement"],
            ["Certificat de radiation", "Art. 92", "Après application d'une radiation"],
            ["Certificat de recherche", "Art. 97", "À l'issue de chaque recherche art. 94-96"],
          ],
          [3000, 2200, 4160],
        ),

        h("6.2 Données utilisées", 2),
        p("Les certificats puisent leurs données dans la table Certificat qui porte une description structurée bilingue. Les libellés sont produits à partir des référentiels versionnés (catégories de biens, natures de droits, motifs de rejet) afin que le contenu reste reproductible et cohérent dans la durée."),

        h("6.3 Documents de test vs documents probants", 2),
        table(
          ["Aspect", "Mode TEST", "Cible production"],
          [
            ["Drapeau Certificat.probant", "Toujours False", "True après scellement"],
            ["Mention obligatoire", "« TEST / NON OPPOSABLE » à imprimer en gros caractères", "Aucune mention de test"],
            ["Horodatage", "Horloge locale (local_stub)", "Horodatage opposable via TSA RFC 3161 (fiche F5)"],
            ["Scellement", "SHA-256 simple (informatif)", "Scellement signé via PKI (fiche F6)"],
            ["Charte graphique", "Charte officielle RIM appliquée", "Idem + sceau et polices officielles déposés"],
          ],
          [2800, 3300, 3260],
        ),

        h("6.4 Préparation à la production probante", 2),
        p("Quatre fiches MO conditionnent l'émission probante :"),
        bullet("F4 : modèles PDF/A bilingues approuvés et charte documentaire"),
        bullet("F5 : source de temps officielle désignée"),
        bullet("F6 : algorithmes de scellement et politique de gestion des clés"),
        bullet("F1 : glossaire juridique bilingue validé"),
        p("Tant que ces paramètres ne sont pas communiqués par le maître d'ouvrage, le système reste en mode disabled pour les volets correspondants. Aucun mécanisme par défaut n'est inventé."),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 7
        h("7. Sécurité et intégrité", 1),
        h("7.1 Principes de sécurité globaux", 2),
        bullet("Authentification obligatoire pour toute opération métier (IsAuthenticated par défaut côté API)."),
        bullet("Recherche publique anonyme autorisée uniquement pour l'endpoint /recherche/, conformément à l'article 94."),
        bullet("Permissions par rôle vérifiées dans les services métier (et pas seulement aux frontières HTTP)."),
        bullet("Sérialisation stricte : toute clé inattendue dans un payload est rejetée (StrictInputSerializer)."),
        bullet("Validation côté serveur autoritative ; la validation côté frontend est purement ergonomique."),

        h("7.2 CSRF / CORS / sessions", 2),
        table(
          ["Mécanisme", "TEST", "PRODUCTION"],
          [
            ["Cookie sessionid", "HttpOnly, SameSite=Lax", "Idem + Secure (HTTPS)"],
            ["Cookie csrftoken", "Posé par whoami, non vérifié", "Posé et vérifié sur toute requête mutante"],
            ["CSRF_TRUSTED_ORIGINS", "inclut localhost:3100 et localhost:8000", "À configurer avec le domaine réel de production"],
            ["CORS_ALLOWED_ORIGINS", "non strict", "À restreindre au domaine du portail RSM"],
            ["Durée de session", "Par défaut Django (2 semaines)", "À durcir (ex. 30 minutes inactif)"],
            ["Verrouillage par tentatives", "Non", "À ajouter (django-axes ou équivalent)"],
          ],
          [2800, 3300, 3260],
        ),

        h("7.3 Séparation des rôles", 2),
        p("La séparation est triple :"),
        bullet("Modèle : un même utilisateur peut avoir plusieurs rôles, mais pas la combinaison agent_saisie + autorite_validation."),
        bullet("Service : chaque service métier appelle explicitement la fonction d'habilitation correspondante."),
        bullet("Demande : un même utilisateur ne peut pas valider une demande qu'il a saisie lui-même, même si techniquement il a les deux rôles."),

        h("7.4 Journal d'audit append-only", 2),
        p("Le journal d'audit est protégé à deux niveaux indépendants (application + base de données). Il enregistre :"),
        bullet("chaque dépôt, modification, renouvellement, radiation, validation, rejet ;"),
        bullet("chaque consultation de la recherche publique (art. 94) avec son certificat associé (art. 97) ;"),
        bullet("chaque action sur les comptes (création, affectation de rôle, changement de rôle)."),
        p("Le chaînage par hachage permet de détecter toute altération a posteriori, y compris si un acteur disposant d'un accès direct à la base parvenait à contourner les triggers (situation à signaler par l'auditeur)."),

        h("7.5 Intégrité des données", 2),
        bullet("Toute écriture critique (dépôt, validation, modification) est encadrée par une transaction atomique."),
        bullet("L'attribution du numéro d'ordre utilise un verrou applicatif exclusif (SELECT ... FOR UPDATE sur la séquence) afin de garantir l'unicité et l'ordre chronologique exigés par l'article 78."),
        bullet("Les contraintes d'intégrité référentielle empêchent toute suppression en cascade : une inscription ne peut pas être physiquement supprimée tant que des biens, parties ou snapshots y font référence."),

        h("7.6 Différence sécurité TEST / PRODUCTION", 2),
        table(
          ["Volet", "TEST", "PRODUCTION"],
          [
            ["Mots de passe seed", "Texte clair affiché dans la documentation", "Interdits"],
            ["Bandeau MODE TEST", "Visible", "Masqué"],
            ["DJANGO_DEBUG", "True", "False (impératif)"],
            ["ALLOWED_HOSTS", "localhost,127.0.0.1", "Domaine réel uniquement"],
            ["SECRET_KEY", "Valeur de développement", "Générée aléatoirement, conservée en coffre-fort"],
            ["HTTPS", "Optionnel", "Obligatoire, terminaison TLS au reverse proxy"],
            ["Logs sensibles", "Verbeux", "Filtrés (pas de payloads avec données personnelles)"],
            ["Comptes seedés", "7 comptes de test", "Aucun ; comptes créés un à un par l'admin"],
          ],
          [2800, 3000, 3560],
        ),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 8
        h("8. Déploiement et exploitation", 1),
        h("8.1 Pré-requis techniques", 2),
        table(
          ["Composant", "Version minimale", "Notes"],
          [
            ["Système d'exploitation", "Linux serveur (Debian 12, Ubuntu 22.04 LTS, RHEL 9)", "Windows non recommandé en production"],
            ["Python", "3.12", "Inclure pip et venv"],
            ["PostgreSQL", "14+ (recommandé 16 ou 18)", "Encodage UTF-8 obligatoire, locale fr_FR.UTF-8 ou C.UTF-8"],
            ["Node.js", "18 LTS", "Pour le build du frontend (étape ponctuelle)"],
            ["Reverse proxy", "nginx 1.22+ ou équivalent", "Terminaison TLS, en-têtes de sécurité"],
            ["Serveur d'application", "gunicorn 21+ ou uWSGI", "Mode worker recommandé : gthread ou sync"],
            ["Espace disque", "50 Go (système) + selon volume documentaire", "Croissance principale liée aux pièces jointes"],
            ["Mémoire", "4 Go minimum, 8 Go recommandé", "À calibrer selon le nombre de workers"],
          ],
          [2800, 3500, 3060],
        ),

        h("8.2 Variables d'environnement (fichier .env)", 2),
        p("Toutes les variables sont lues via python-decouple. Aucune n'est codée en dur."),
        table(
          ["Variable", "Type", "Description"],
          [
            ["DJANGO_SECRET_KEY", "secret", "Clé de signature des sessions ; à générer aléatoirement"],
            ["DJANGO_DEBUG", "booléen", "False en production"],
            ["DJANGO_ALLOWED_HOSTS", "csv", "Domaines servis par l'application"],
            ["DJANGO_CSRF_TRUSTED_ORIGINS", "csv", "Origines de confiance pour le CSRF"],
            ["DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT", "divers", "Connexion PostgreSQL"],
            ["DEFAULT_LANGUAGE", "code", "fr par défaut"],
            ["TIME_ZONE", "IANA", "Africa/Nouakchott"],
            ["RSM_MODE_TEST", "booléen", "false en production"],
            ["RSM_TIMESOURCE_MODE", "code", "local_stub jusqu'à F5, puis valeur désignée"],
            ["RSM_SEAL_MODE", "code", "disabled jusqu'à F6"],
            ["RSM_ESIGN_MODE", "code", "disabled jusqu'à F3"],
            ["RSM_MFA_MODE", "code", "disabled jusqu'à F2"],
            ["RSM_INTEROP_BANQUES_MODE", "code", "disabled jusqu'à F15"],
          ],
          [3500, 1500, 4360],
        ),

        h("8.3 Démarrage des services", 2),
        p("Étapes ordonnées (à automatiser dans l'outil de déploiement) :"),
        bullet("Activer l'environnement virtuel Python."),
        bullet("Installer les dépendances backend (pip install -r requirements.txt)."),
        bullet("Appliquer les migrations (python manage.py migrate)."),
        bullet("Collecter les fichiers statiques (python manage.py collectstatic --noinput)."),
        bullet("Charger les référentiels (python manage.py seed_referentiels)."),
        bullet("Vérifier que seed_demo_test n'est PAS lancé en production."),
        bullet("Lancer le serveur d'application (gunicorn ou équivalent) sur un port interne (par exemple 127.0.0.1:8000)."),
        bullet("Configurer le reverse proxy : terminaison TLS, redirection HTTP → HTTPS, en-têtes de sécurité, fichier statique servi directement."),
        bullet("Vérifier que GET /api/v1/auth/whoami/ répond 200."),
        p("Le frontend est compilé une fois (npm install puis npm run build) et déployé sous forme de fichiers statiques."),

        h("8.4 Gestion des logs", 2),
        table(
          ["Source", "Type", "Recommandation"],
          [
            ["Django (vues, services)", "Logs applicatifs", "Niveau INFO en production, WARNING minimum côté disque"],
            ["Erreurs serveur", "Tracebacks", "Capture par Sentry ou équivalent ; ne pas laisser les tracebacks accessibles à l'utilisateur (DJANGO_DEBUG=False)"],
            ["Audit métier", "Table EntreeAudit", "Append-only, conservé sans rotation"],
            ["Reverse proxy", "Accès et erreurs HTTP", "Format combiné, conservé selon la politique RGPD locale"],
            ["PostgreSQL", "Slow queries, dead-locks", "À surveiller"],
          ],
          [2800, 2500, 4060],
        ),
        p("Les logs ne doivent pas contenir les payloads de connexion, les mots de passe, les jetons CSRF ni le contenu détaillé des inscriptions."),

        h("8.5 Sauvegardes", 2),
        bullet("Base de données : sauvegarde quotidienne complète + archivage WAL (point-in-time recovery). Test mensuel de restauration documenté."),
        bullet("Pièces jointes (médias) : sauvegarde synchronisée vers un stockage tiers chiffré."),
        bullet("Configuration : .env et certificats hors arborescence du code, sauvegardés dans un coffre-fort dédié."),
        bullet("Cible RPO ≤ 1 heure, RTO ≤ 4 heures (TDR § 5.3)."),

        h("8.6 Montée en charge", 2),
        p("Architecture conçue stateless côté application : la session est stockée en base, chaque worker peut servir n'importe quelle requête sans affinité. Pour absorber la charge :"),
        bullet("augmenter le nombre de workers gunicorn (règle empirique : 2× CPU cœurs + 1) ;"),
        bullet("configurer un pool de connexions PostgreSQL (pgbouncer recommandé) ;"),
        bullet("placer les fichiers statiques derrière un CDN ou activer le cache HTTP au niveau du reverse proxy ;"),
        bullet("horizontalement, plusieurs instances applicatives peuvent être ajoutées derrière un répartiteur de charge — l'unicité du numéro d'ordre reste garantie par PostgreSQL via le verrou exclusif."),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 9
        h("9. Contraintes d'hébergement", 1),
        h("9.1 Exigences serveur minimales", 2),
        table(
          ["Profil", "Recommandation"],
          [
            ["TEST / RECETTE", "2 vCPU, 4 Go RAM, 50 Go SSD"],
            ["PRODUCTION (démarrage)", "4 vCPU, 8 Go RAM, 100 Go SSD + sauvegardes externes"],
            ["PRODUCTION (consolidée)", "8 vCPU, 16 Go RAM, 200 Go SSD + cluster PostgreSQL en réplication"],
          ],
          [3500, 5860],
        ),

        h("9.2 Système d'exploitation", 2),
        p("Linux serveur LTS recommandé. Mises à jour de sécurité activées par défaut (unattended-upgrades Debian, ou équivalent). Pare-feu local (ufw ou firewalld) configuré pour ne laisser ouverts que les ports strictement nécessaires."),

        h("9.3 Réseau et ports", 2),
        table(
          ["Port", "Sortant", "Entrant", "Note"],
          [
            ["443", "—", "Public", "HTTPS (terminaison reverse proxy)"],
            ["80", "—", "Public", "Redirection 301 vers HTTPS"],
            ["22", "—", "Restreint à l'admin", "SSH ; clé publique uniquement"],
            ["5432", "—", "Aucun externe", "PostgreSQL accessible uniquement depuis l'application"],
            ["Sortants", "80, 443, 53", "—", "Mises à jour, NTP, monitoring"],
          ],
          [1500, 2000, 2500, 3360],
        ),

        h("9.4 Base de données", 2),
        p("Instance PostgreSQL dédiée au RSM, isolée des autres applications. Compte d'application avec privilèges strictement sur la base RSM (création de table, lecture, écriture sur les tables applicatives, AUCUN privilège sur les triggers d'audit pour empêcher leur désactivation)."),

        h("9.5 Stockage", 2),
        bullet("Volume principal : code, configuration, logs."),
        bullet("Volume de médias (pièces jointes) : monté séparément, chiffré au repos."),
        bullet("Volume de sauvegardes : externalisé."),

        h("9.6 Séparation des environnements", 2),
        p("Les environnements TEST et PRODUCTION sont strictement séparés :"),
        bullet("Serveurs distincts (ou au minimum machines virtuelles distinctes)."),
        bullet("Bases de données distinctes (jamais de réplication TEST → PROD ni inverse, sauf ce qui est explicitement prévu pour la pré-production)."),
        bullet("Comptes d'accès distincts (un administrateur production n'utilise pas les mêmes identifiants que pour la recette)."),
        bullet("Domaines distincts (par exemple rsm-test.example.mr et rsm.example.mr)."),
        bullet("Sauvegardes séparées et non interchangeables."),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- 10
        h("10. Points d'attention pour l'hébergeur", 1),
        h("10.1 Points critiques à surveiller", 2),
        bullet("Disponibilité de la base de données : toute indisponibilité bloque les inscriptions. Configurer une supervision active."),
        bullet("Verrou sur la séquence du numéro d'ordre : un long verrouillage peut indiquer un dead-lock ; alerter au-delà de 5 secondes."),
        bullet("Croissance de la table d'audit : append-only, jamais purgée. Surveiller l'espace disque et planifier l'archivage légal (mais pas la suppression — l'article 79 l'interdit)."),
        bullet("Synchronisation horaire : décalage NTP > 1 seconde → alerte. Critique pour l'article 78 (horodatage à la seconde)."),
        bullet("Erreurs HTTP 500 : toutes anormales en production. Doivent déclencher une alerte immédiate."),

        h("10.2 Erreurs fréquentes à éviter", 2),
        bullet("Activer DJANGO_DEBUG=True en production : expose les variables d'environnement et tracebacks ; INTERDIT."),
        bullet("Lancer seed_demo_test en production : crée des comptes avec mots de passe en clair ; INTERDIT."),
        bullet("Désactiver les triggers d'audit pour des opérations de maintenance : viole l'article 79 ; toute action de ce type doit être tracée hors-bande et signalée à l'auditeur."),
        bullet("Modifier directement la base de données via l'admin Django avec un super-utilisateur : l'admin est paramétrée en lecture seule précisément pour empêcher cette dérive."),
        bullet("Lever les modes RSM_*_MODE (TIMESOURCE, SEAL, ESIGN, MFA, INTEROP) sans la note MO correspondante : génère des données incomplètes ou non opposables."),

        h("10.3 Paramètres sensibles", 2),
        p("Les variables suivantes ne doivent JAMAIS apparaître dans les logs, le système de versionnement, les tickets ou les courriels :"),
        bullet("DJANGO_SECRET_KEY"),
        bullet("DB_PASSWORD"),
        bullet("Mots de passe d'administrateur ou de service"),
        bullet("Clés privées TLS, clés API tierces, jetons OAuth"),
        p("Stockage recommandé : coffre-fort de secrets (HashiCorp Vault, AWS Secrets Manager, ou solution équivalente locale). Les comptes d'administration humains utilisent un gestionnaire de mots de passe agréé."),

        h("10.4 Bonnes pratiques d'exploitation", 2),
        bullet("Toute modification du système (déploiement, mise à jour, migration) fait l'objet d'un ticket de changement avec date, auteur, motif."),
        bullet("Les déploiements suivent une procédure documentée : pré-production → recette → bascule production → fenêtre de retour arrière de 24 heures."),
        bullet("Les sauvegardes sont testées mensuellement par restauration sur un environnement isolé."),
        bullet("Les logs sont conservés selon la politique légale applicable (au minimum 5 ans pour les actes notariés et registres publics, à vérifier auprès du Tribunal)."),
        bullet("L'auditeur (rôle auditeur dans le système) a un accès de consultation au journal d'audit et doit être informé de toute modification significative de l'infrastructure."),

        h("10.5 Éléments à valider avant mise en production", 2),
        table(
          ["#", "Vérification"],
          [
            ["1", "DJANGO_DEBUG=False"],
            ["2", "RSM_MODE_TEST=false, bandeau MODE TEST absent"],
            ["3", "DJANGO_SECRET_KEY régénérée et stockée hors code"],
            ["4", "ALLOWED_HOSTS et CSRF_TRUSTED_ORIGINS cantonnés au domaine de production"],
            ["5", "HTTPS actif, redirection HTTP → HTTPS opérationnelle"],
            ["6", "Triggers PostgreSQL d'audit append-only vérifiés présents et actifs"],
            ["7", "Compte admin technique avec mot de passe robuste, MFA si possible (cf. F2)"],
            ["8", "Aucun compte seed (declarant_externe, greffier, etc.) ne subsiste"],
            ["9", "Sauvegarde quotidienne testée, chiffrée"],
            ["10", "Plan de continuité documenté (RPO ≤ 1 h, RTO ≤ 4 h)"],
            ["11", "Synchronisation NTP active sur tous les serveurs"],
            ["12", "Pare-feu : seuls 80/443 ouverts au public, 22 restreint, 5432 fermé à l'externe"],
            ["13", "Logs centralisés et exempts de données personnelles"],
            ["14", "Procédure de gestion des incidents documentée et notifiée à l'équipe"],
            ["15", "Procès-verbal de mise en production signé par les parties (greffe, hébergeur, MO)"],
          ],
          [800, 8560],
        ),
        new Paragraph({ children: [new PageBreak()] }),

        // ---------------------------------------------------------------- ANNEXES
        h("Annexe A — Conformité bilingue FR / AR", 1),
        p("Toutes les fonctionnalités exposées au public ou aux agents disposent de libellés FR et AR. La parité est garantie au niveau du référentiel de traductions : mêmes clés, mêmes effets. La direction d'écriture (LTR / RTL) est appliquée automatiquement par la feuille de style globale en fonction de la langue active."),
        p("Aucune divergence d'effet juridique ne doit exister entre les deux versions linguistiques (TDR § 7.1)."),

        h("Annexe B — Documents associés", 1),
        table(
          ["Référence", "Sujet"],
          [
            ["L1 — Note de cadrage", "Fondations institutionnelles"],
            ["L2 — Spécifications fonctionnelles", "Formulaires, règles de validation, statuts, rôles"],
            ["L3 — Spécifications techniques", "Modèle de données, dictionnaire d'API"],
            ["L11 — Traçabilité", "Articles 76 à 97, registre des décisions MO"],
            ["Décision n° 0001/2026", "Levée juridique des zones gelées"],
            ["Fiches MO F1 à F15", "Arbitrages institutionnels"],
          ],
          [3500, 5860],
        ),

        h("Annexe C — Glossaire technique", 1),
        table(
          ["Terme", "Sens dans le RSM"],
          [
            ["SPA", "Single-Page Application : l'interface React"],
            ["DRF", "Django REST Framework"],
            ["CSRF", "Cross-Site Request Forgery (protection des formulaires)"],
            ["CORS", "Cross-Origin Resource Sharing"],
            ["Append-only", "Mode d'écriture interdisant la modification et la suppression"],
            ["MFA", "Multi-Factor Authentication (authentification forte)"],
            ["TSA", "Time Stamping Authority (autorité d'horodatage RFC 3161)"],
            ["PKI", "Public Key Infrastructure"],
            ["PDF/A", "Format PDF d'archivage normé ISO 19005"],
            ["RTL / LTR", "Right-To-Left / Left-To-Right (sens d'écriture)"],
          ],
          [2200, 7160],
        ),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "— Fin de la note d'architecture technique et de déploiement —",
            italics: true, color: "707070",
          })],
          spacing: { before: 400 },
        }),
      ],
    },
  ],
});

const out = path.join(__dirname, "L8_note_architecture_deploiement.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(out, buf);
  console.log("OK:", out, "(", buf.length, "octets )");
});
