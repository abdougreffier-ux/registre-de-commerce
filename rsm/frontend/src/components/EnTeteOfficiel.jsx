import React from 'react';
import { useTranslation } from 'react-i18next';

import SceauOfficiel from './SceauOfficiel';

/**
 * En-tête officiel — version COMPACTE mono-ligne.
 *
 * Refonte UX/UI institutionnelle (mai 2026) :
 *   - hauteur réduite à environ 76 px (vs ~300 px précédemment) ;
 *   - sceau circulaire à liseré bicolore (jaune / vert) — taille 52 px ;
 *   - mention nationale + entité juridictionnelle sur une même ligne,
 *     séparées par un losange jaune RIM ;
 *   - sous-titre discret « Registre des Sûretés Mobilières » ;
 *   - filet tricolore RIM (rouge / vert / jaune) en pied de bande.
 *
 * L'en-tête s'affiche exclusivement dans la LANGUE ACTIVE :
 *   - i18n.language ∈ { 'ar', 'ar-…' } → mentions arabes uniquement ;
 *   - sinon → mentions françaises uniquement.
 * Le bouton de bascule de langue dans la barre de navigation conserve
 * l'accès intégral aux deux versions linguistiques.
 *
 * Aucune information juridique n'est altérée : la devise nationale est
 * désormais portée par le pied de page institutionnel pour soulager
 * l'en-tête, sans perte d'aucun signal officiel.
 *
 * Direction RTL/LTR appliquée automatiquement par la feuille globale.
 */
export default function EnTeteOfficiel() {
  const { t, i18n } = useTranslation();
  const ar = (i18n.language || 'fr').toLowerCase().startsWith('ar');

  const nation = ar ? t('institution.nation_ar') : t('institution.nation_fr');
  const entite = ar ? t('institution.entite_ar') : t('institution.entite_fr');
  const systeme = ar ? t('institution.systeme_ar') : t('institution.systeme_fr');

  return (
    <header className="rim-entete-conteneur">
      <div className="rim-entete-compact">
        <div className="rim-entete-compact__sceau">
          <SceauOfficiel taille={46} titre={nation} />
        </div>

        <div className="rim-entete-compact__textes">
          <div className="rim-entete-compact__ligne1">
            <span className="rim-entete-compact__nation" lang={ar ? 'ar' : 'fr'}>
              {nation}
            </span>
            <span className="rim-entete-compact__sep" aria-hidden="true" />
            <span className="rim-entete-compact__entite" lang={ar ? 'ar' : 'fr'}>
              {entite}
            </span>
          </div>
          <div className="rim-entete-compact__systeme" lang={ar ? 'ar' : 'fr'}>
            {systeme}
          </div>
        </div>

        <div className="rim-entete-compact__filet" aria-hidden="true">
          <span /><span /><span />
        </div>
      </div>
    </header>
  );
}
