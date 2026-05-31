/**
 * Métadonnées institutionnelles du site CCRCSM.
 * Accessible via `site.<clé>` dans tous les templates.
 *
 * Ces valeurs sont consommées par les métadonnées (OpenGraph, Twitter Card),
 * les flux RSS, le sitemap et les mentions légales. L'URL de production sera
 * confirmée par le maître d'ouvrage au moment du déploiement.
 */
module.exports = {
  name: {
    fr: "Comité de Coordination du Registre du Commerce et des Sûretés Mobilières",
    ar: "لجنة تنسيق السجل التجاري والضمانات المنقولة",
  },
  shortName: {
    fr: "CCRCSM",
    ar: "ل.ت.س.ت.ض.م",
  },
  tagline: {
    fr: "Organe para-judiciaire de coordination — République Islamique de Mauritanie",
    ar: "هيئة شبه قضائية للتنسيق — الجمهورية الإسلامية الموريتانية",
  },
  republic: {
    fr: "République Islamique de Mauritanie",
    ar: "الجمهورية الإسلامية الموريتانية",
  },
  motto: {
    fr: "Honneur – Fraternité – Justice",
    ar: "شرف - إخاء - عدل",
  },
  ministry: {
    fr: "Ministère de la Justice",
    ar: "وزارة العدل",
  },
  // URL de production — à confirmer. Domaine cible .gov.mr (cf. §8.6).
  url: "https://www.ccrcsm.gov.mr",
  locales: ["fr", "ar"],
  defaultLocale: "fr",
  contact: {
    address: {
      fr: "Secrétariat du CCRCSM, Ministère de la Justice, Nouakchott, Mauritanie",
      ar: "أمانة لجنة تنسيق السجل التجاري والضمانات المنقولة، وزارة العدل، نواكشوط، موريتانيا",
    },
    email: "contact@ccrcsm.gov.mr",
    phone: "+222 00 00 00 00",
    hours: {
      fr: "Dimanche à jeudi, 9h – 16h",
      ar: "من الأحد إلى الخميس، 9 صباحًا – 4 مساءً",
    },
  },
  // Direction par locale (pour attribut dir sur <html>)
  direction: {
    fr: "ltr",
    ar: "rtl",
  },
  // Année de publication
  version: "1.0",
  // Active le preload des WOFF2 dans le <head>. À passer à true une fois les fichiers
  // de polices déposés dans src/assets/fonts/ (voir src/assets/fonts/README.md).
  hasLocalFonts: false,
};
