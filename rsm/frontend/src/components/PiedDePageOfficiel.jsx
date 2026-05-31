import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Pied de page institutionnel — conforme à la charte graphique
 * (fond vert foncé, texte blanc, séparateur rouge en haut).
 */
export default function PiedDePageOfficiel() {
  const { t } = useTranslation();
  return (
    <footer>
      <div className="rim-tricolore" aria-hidden="true">
        <span /><span /><span />
      </div>
      <div className="rim-pied">
        <div lang="ar">{t('institution.entite_ar')}</div>
        <div lang="fr">{t('institution.entite_fr')}</div>
        <div style={{ opacity: 0.85, marginTop: 4 }}>
          {t('institution.pied_mention')}
        </div>
      </div>
    </footer>
  );
}
