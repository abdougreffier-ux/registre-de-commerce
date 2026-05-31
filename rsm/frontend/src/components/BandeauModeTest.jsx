import React from 'react';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../contexts/AuthContext';

/**
 * Bandeau permanent MODE TEST — version « filet » discrète mais
 * institutionnelle (rouge plein, lettrage majuscule, pictogrammes jaunes).
 *
 * Strictement bilingue FR/AR. Aucune couleur hors charte.
 */
export default function BandeauModeTest() {
  const { t } = useTranslation();
  const auth = useAuth();
  const modeTest = !!auth?.utilisateur?.systeme?.mode_test
    || !!auth?.systeme?.mode_test
    || (typeof window !== 'undefined' && window.RSM_MODE_TEST === true);
  if (!modeTest) return null;
  return (
    <div className="rim-bandeau-test" role="alert">
      {t('mode_test.bandeau.titre')}
    </div>
  );
}
