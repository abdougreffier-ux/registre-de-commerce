import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * StatutBadge — affichage unifié des statuts d'inscription RSM.
 *
 * Source unique de vérité pour la traduction visuelle des 9 statuts
 * métier vers les 6 variantes graphiques de la charte
 * (--neutre, --attente, --succes, --rejet, --info, --archive).
 *
 * Principes UX/UI (refonte mai 2026) :
 *   - une seule façon d'afficher un statut dans toute l'application ;
 *   - couleur + libellé + pastille = jamais la couleur seule
 *     (accessibilité, lecteurs d'écran, daltonisme) ;
 *   - libellés résolus via i18n, identiques en effet juridique FR/AR ;
 *   - aucune logique métier dans ce composant.
 *
 * Garde-fous respectés :
 *   - intégrité : aucune mutation côté front ;
 *   - traçabilité : aucune action ;
 *   - parité FR/AR : même clé i18n des deux côtés.
 */

/**
 * Mapping statut → variante visuelle.
 * Centralisé ici pour qu'aucune divergence ne soit possible entre pages.
 */
export const VARIANTE_PAR_STATUT = {
  recue:              'neutre',
  en_controle_forme:  'info',
  rejetee:            'rejet',
  inscrite:           'succes',
  modifiee:           'succes',
  renouvelee:         'succes',
  radiee:             'attente',
  expiree:            'neutre',
  archivee:           'archive',
};

/**
 * Variantes acceptées (alignées sur charte.css `.rim-statut.--*`).
 */
const VARIANTES_VALIDES = new Set([
  'neutre', 'attente', 'succes', 'rejet', 'info', 'archive',
]);

/**
 * Composant principal.
 *
 * Affichage par défaut :
 *   - libellé COURT (clé inscription.statut_court.<statut>) pour la lisibilité
 *     dans tableaux, listes et fiches ;
 *   - libellé LÉGAL COMPLET (clé inscription.statut.<statut>) en infobulle,
 *     conservé pour les certificats officiels et les documents probants.
 *
 * @param {object} props
 * @param {string} props.statut         clé technique du statut métier (recue, inscrite, ...)
 * @param {string} [props.variante]     forçage manuel d'une variante visuelle (override)
 * @param {string} [props.libelle]      libellé personnalisé (sinon résolu via i18n)
 * @param {string} [props.cleI18n]      clé i18n personnalisée pour le libellé visible
 * @param {boolean} [props.pastille=true] afficher la pastille colorée
 * @param {boolean} [props.complet=false] forcer l'affichage du libellé légal complet
 * @param {string} [props.title]        infobulle optionnelle (sinon = libellé légal complet)
 * @param {object} [props.style]        style en ligne
 * @param {string} [props.className]    classes CSS additionnelles
 */
export default function StatutBadge({
  statut,
  variante,
  libelle,
  cleI18n,
  pastille = true,
  complet = false,
  title,
  style,
  className,
}) {
  const { t } = useTranslation();

  // Détermination de la variante visuelle (override > mapping > fallback)
  const v = variante && VARIANTES_VALIDES.has(variante)
    ? variante
    : (VARIANTE_PAR_STATUT[statut] || 'neutre');

  // Libellé légal complet (toujours résolu — utilisé en infobulle ou en mode complet)
  const cleLegal = `inscription.statut.${statut}`;
  const libelleLegal = statut
    ? t(cleLegal, { defaultValue: statut })
    : '—';

  // Libellé visible : param > clé custom > court > légal
  let texte;
  if (libelle) {
    texte = libelle;
  } else if (cleI18n) {
    texte = t(cleI18n, { defaultValue: statut || '—' });
  } else if (complet) {
    texte = libelleLegal;
  } else if (statut) {
    // Préférer la version courte si elle existe ; sinon retomber sur le légal
    const cleCourte = `inscription.statut_court.${statut}`;
    const tentativeCourte = t(cleCourte, { defaultValue: '__MISSING__' });
    texte = tentativeCourte === '__MISSING__' ? libelleLegal : tentativeCourte;
  } else {
    texte = '—';
  }

  const classes = ['rim-statut', `--${v}`];
  if (className) classes.push(className);

  return (
    <span
      className={classes.join(' ')}
      style={style}
      title={title || libelleLegal}
      role="status"
    >
      {pastille && <span className="rim-statut__pastille" aria-hidden="true" />}
      <span>{texte}</span>
    </span>
  );
}
