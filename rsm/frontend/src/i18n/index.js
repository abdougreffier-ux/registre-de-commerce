/**
 * Internationalisation FR/AR — RSM.
 *
 * Règles imposées par le TDR (§ 7) :
 *   - mêmes fonctionnalités, mêmes messages, mêmes règles dans les deux langues ;
 *   - basculement automatique de la direction d'écriture (ltr/rtl) en fonction
 *     de la langue active ;
 *   - aucune libellé juridique codé en dur dans un composant : chaque texte
 *     passe par le référentiel de traductions.
 *
 * Les libellés juridiques définitifs sont validés par le comité désigné
 * par le maître d'ouvrage (§ 7.3 TDR). Les traductions ci-dessous sont
 * une amorce technique : elles doivent être relues et validées avant
 * mise en production.
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import fr from './fr.json';
import ar from './ar.json';

const LANGUES = {
  fr: { traduction: fr, direction: 'ltr', label: 'Français' },
  ar: { traduction: ar, direction: 'rtl', label: 'العربية' },
};

export const LANGUES_DISPONIBLES = Object.keys(LANGUES);

export function appliquerDirection(langue) {
  const dir = (LANGUES[langue] || LANGUES.fr).direction;
  document.documentElement.setAttribute('dir', dir);
  document.documentElement.setAttribute('lang', langue);
}

i18n
  .use(initReactI18next)
  .init({
    resources: Object.fromEntries(
      Object.entries(LANGUES).map(([code, v]) => [code, { translation: v.traduction }])
    ),
    lng: localStorage.getItem('rsm.langue') || 'fr',
    fallbackLng: 'fr',
    interpolation: { escapeValue: false },
  });

i18n.on('languageChanged', (langue) => {
  localStorage.setItem('rsm.langue', langue);
  appliquerDirection(langue);
});

// Applique la direction dès le chargement.
appliquerDirection(i18n.language);

export default i18n;
