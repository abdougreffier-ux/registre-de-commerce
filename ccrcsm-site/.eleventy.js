/**
 * Configuration Eleventy — Site institutionnel CCRCSM.
 *
 * Le site est bilingue FR/AR. Les contenus FR vivent dans src/fr/, les contenus AR
 * dans src/ar/. Les layouts, partials et données sont partagés via des clés i18n.
 * Chaque contenu publiable porte un identifiant `id` (dans ses front-matter) qui
 * permet le lien croisé entre versions — voir `_includes/partials/lang-switcher.njk`.
 */

const { DateTime } = require("luxon");
const rssPlugin = require("@11ty/eleventy-plugin-rss");
const markdownIt = require("markdown-it");
const markdownItAnchor = require("markdown-it-anchor");
const markdownItAttrs = require("markdown-it-attrs");
const Nunjucks = require("nunjucks");

module.exports = function (eleventyConfig) {
  // Plugins officiels
  eleventyConfig.addPlugin(rssPlugin);

  // Configuration Nunjucks — on redéfinit les délimiteurs de commentaire pour
  // éviter le conflit avec la syntaxe markdown-it-attrs `{#id}`.
  // Commentaires Nunjucks : {! ... !} (au lieu du défaut {# ... #})
  const nunjucksEnv = new Nunjucks.Environment(
    new Nunjucks.FileSystemLoader("src/_includes"),
    {
      autoescape: true,
      throwOnUndefined: false,
      tags: {
        blockStart: "{%",
        blockEnd: "%}",
        variableStart: "{{",
        variableEnd: "}}",
        commentStart: "{!",
        commentEnd: "!}",
      },
    }
  );
  eleventyConfig.setLibrary("njk", nunjucksEnv);

  // Moteur Markdown (anchors pour liens intra-page accessibles + attributs {#id})
  const md = markdownIt({ html: true, linkify: true, typographer: true })
    .use(markdownItAttrs, { allowedAttributes: ["id", "class"] })
    .use(markdownItAnchor, {
      permalink: markdownItAnchor.permalink.headerLink({
        class: "heading-anchor",
        safariReaderFix: true,
      }),
    });
  eleventyConfig.setLibrary("md", md);

  // Actifs copiés tels quels
  eleventyConfig.addPassthroughCopy({ "src/assets": "assets" });
  eleventyConfig.addPassthroughCopy({ "src/robots.txt": "robots.txt" });

  // Observation pour le hot-reload
  eleventyConfig.addWatchTarget("src/assets/css/");
  eleventyConfig.addWatchTarget("src/assets/js/");

  // --- Filtres ---

  // Date longue FR : 11 mars 2021
  eleventyConfig.addFilter("dateFR", (value) => {
    if (!value) return "";
    return DateTime.fromJSDate(new Date(value), { zone: "utc" })
      .setLocale("fr")
      .toFormat("d LLLL yyyy");
  });

  // Date longue AR (calendrier grégorien, libellé arabe)
  eleventyConfig.addFilter("dateAR", (value) => {
    if (!value) return "";
    return DateTime.fromJSDate(new Date(value), { zone: "utc" })
      .setLocale("ar")
      .toFormat("d LLLL yyyy");
  });

  // Date ISO pour attributs <time datetime="...">
  eleventyConfig.addFilter("dateISO", (value) => {
    if (!value) return "";
    return DateTime.fromJSDate(new Date(value), { zone: "utc" }).toISODate();
  });

  // Date ISO complète pour flux RSS
  eleventyConfig.addFilter("dateRFC", (value) => {
    if (!value) return "";
    return DateTime.fromJSDate(new Date(value), { zone: "utc" }).toRFC2822();
  });

  // Locale d'une page d'après son URL (/fr/… ou /ar/…)
  eleventyConfig.addFilter("localeOf", (url) => {
    if (!url) return "fr";
    if (url.startsWith("/ar/")) return "ar";
    return "fr";
  });

  // Direction d'une locale
  eleventyConfig.addFilter("dirOf", (locale) => (locale === "ar" ? "rtl" : "ltr"));

  // Filtre d'échappement strict pour JSON inline (évite `</script>` dans payload)
  eleventyConfig.addFilter("jsonSafe", (value) =>
    JSON.stringify(value).replace(/</g, "\\u003C").replace(/>/g, "\\u003E")
  );

  // Filtre : limite un tableau
  eleventyConfig.addFilter("take", (arr, n) => (arr || []).slice(0, n));

  // Filtre : tri décroissant par date
  eleventyConfig.addFilter("sortByDateDesc", (arr) =>
    [...(arr || [])].sort((a, b) => new Date(b.date) - new Date(a.date))
  );

  // Filtre : URL absolue pour RSS/sitemap
  eleventyConfig.addFilter("absoluteUrl", (url, base) => {
    try {
      return new URL(url, base).toString();
    } catch {
      return url;
    }
  });

  // --- Collections ---
  // Avis du Comité (FR + AR, distinguées par locale)
  ["fr", "ar"].forEach((loc) => {
    eleventyConfig.addCollection(`avis_${loc}`, (api) =>
      api
        .getFilteredByGlob(`src/${loc}/publications/avis/*.md`)
        .sort((a, b) => new Date(b.date) - new Date(a.date))
    );
    eleventyConfig.addCollection(`actualites_${loc}`, (api) =>
      api
        .getFilteredByGlob(`src/${loc}/publications/actualites/*.md`)
        .sort((a, b) => new Date(b.date) - new Date(a.date))
    );
    eleventyConfig.addCollection(`communiques_${loc}`, (api) =>
      api
        .getFilteredByGlob(`src/${loc}/publications/communiques/*.md`)
        .sort((a, b) => new Date(b.date) - new Date(a.date))
    );
    eleventyConfig.addCollection(`textes_${loc}`, (api) =>
      api
        .getFilteredByGlob(`src/${loc}/textes/*.md`)
        .sort((a, b) => (a.data.order || 0) - (b.data.order || 0))
    );
  });

  // Collections plates pour indexation recherche (une par locale)
  const buildSearchIndex = (api, loc) =>
    api
      .getAll()
      .filter(
        (it) =>
          it.data.searchable !== false &&
          it.data.layout &&
          it.url &&
          it.url.startsWith(`/${loc}/`)
      )
      .map((it) => ({
        url: it.url,
        title: it.data.title || "",
        description: it.data.description || "",
        rubrique: it.data.rubrique || "",
        date: it.data.date ? new Date(it.data.date).toISOString() : null,
        type: it.data.type || "page",
      }));

  eleventyConfig.addCollection("searchIndexFr", (api) => buildSearchIndex(api, "fr"));
  eleventyConfig.addCollection("searchIndexAr", (api) => buildSearchIndex(api, "ar"));

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
    // Templates pris en charge
    templateFormats: ["njk", "md", "11ty.js", "html"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
    dataTemplateEngine: "njk",
    pathPrefix: "/",
  };
};
