/**
 * Données par défaut appliquées à toutes les pages de la branche AR (RTL).
 * Les pages individuelles peuvent surcharger ces valeurs dans leur front-matter.
 */
module.exports = {
  locale: "ar",
  layout: "layouts/page.njk",
  tags: ["ar"],
  eleventyComputed: {
    // URL équivalente dans l'autre langue (FR) — remplace `/ar/` par `/fr/`.
    alternate: (data) =>
      data.page && data.page.url ? data.page.url.replace(/^\/ar\//, "/fr/") : null,
  },
};
