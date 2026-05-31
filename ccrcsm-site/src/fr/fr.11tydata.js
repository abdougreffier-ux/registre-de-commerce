/**
 * Données par défaut appliquées à toutes les pages de la branche FR.
 * Les pages individuelles peuvent surcharger ces valeurs dans leur front-matter.
 */
module.exports = {
  locale: "fr",
  layout: "layouts/page.njk",
  tags: ["fr"],
  eleventyComputed: {
    // URL équivalente dans l'autre langue (AR) — remplace `/fr/` par `/ar/`.
    alternate: (data) =>
      data.page && data.page.url ? data.page.url.replace(/^\/fr\//, "/ar/") : null,
  },
};
