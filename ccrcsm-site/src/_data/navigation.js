/**
 * Structure de navigation principale du site.
 * Les clés i18n (via `i18n[locale].nav.<key>`) permettent de générer les libellés
 * dans chaque langue sans dupliquer la hiérarchie.
 *
 * `href` est exprimé sans le préfixe de locale : les layouts y préfixent `/fr/` ou `/ar/`.
 */
module.exports = {
  primary: [
    { key: "home", href: "/" },
    {
      key: "committee",
      href: "/le-comite/",
      children: [
        { key: "committeePresentation", href: "/le-comite/#presentation" },
        { key: "committeeMissions", href: "/le-comite/#missions" },
        { key: "committeeFramework", href: "/le-comite/#cadre-juridique" },
        { key: "committeeComposition", href: "/le-comite/#composition" },
        { key: "committeeOperations", href: "/le-comite/#fonctionnement" },
        { key: "orgChart", href: "/organigramme/" },
        { key: "partners", href: "/partenaires/" },
      ],
    },
    {
      key: "texts",
      href: "/textes/",
      children: [
        { key: "textsCode", href: "/textes/code-de-commerce/" },
        { key: "textsDecree", href: "/textes/decret-2021-033/" },
        { key: "textsLaw", href: "/textes/loi-2022-011/" },
        { key: "textsOrders", href: "/textes/arretes/" },
        { key: "textsGlossary", href: "/glossaire/" },
      ],
    },
    {
      key: "publications",
      href: "/publications/",
      children: [
        { key: "avis", href: "/publications/avis/" },
        { key: "communiques", href: "/publications/communiques/" },
        { key: "news", href: "/publications/actualites/" },
      ],
    },
    {
      key: "services",
      href: "/services/",
      children: [
        { key: "forms", href: "/services/formulaires/" },
        { key: "guides", href: "/services/guides/" },
        { key: "faq", href: "/services/faq/" },
      ],
    },
    { key: "contact", href: "/contact/" },
  ],
  footer: {
    institutional: [
      { key: "committee", href: "/le-comite/" },
      { key: "orgChart", href: "/organigramme/" },
      { key: "partners", href: "/partenaires/" },
      { key: "contact", href: "/contact/" },
    ],
    legalCorner: [
      { key: "accessibility", href: "/accessibilite/" },
      { key: "privacy", href: "/confidentialite/" },
      { key: "cookies", href: "/cookies/" },
      { key: "legal", href: "/mentions-legales/" },
      { key: "sitemap", href: "/plan-du-site/" },
    ],
  },
};
