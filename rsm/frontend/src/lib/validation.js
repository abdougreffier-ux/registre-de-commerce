/**
 * Validations communes côté frontend, alignées sur les contraintes
 * backend (DRF EmailField, etc.).
 *
 * Garde-fous :
 *   - parité FR/AR : les messages d'erreur sont résolus via i18n ;
 *   - cohérence : un seul jeu de règles utilisé partout dans le système.
 */

/**
 * Regex stricte de validation d'adresse e-mail (RFC 5322 simplifiée,
 * conforme à la regex utilisée par DRF/Django côté backend).
 *
 * - Local part : caractères alphanumériques + . _ % + -
 * - @
 * - Domaine : caractères alphanumériques + - . avec TLD ≥ 2 caractères.
 *
 * Refuse explicitement :
 *   - espaces (intérieurs ou en bordures) ;
 *   - double @ ;
 *   - TLD trop court ;
 *   - parties locales/domaines vides.
 */
export const REGEX_EMAIL_STRICT = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

/**
 * Regex stricte d'un NNI mauritanien : exactement 10 chiffres,
 * et rejet des séquences à chiffre unique (0000000000, 1111111111…).
 */
export const REGEX_NNI = /^\d{10}$/;

/**
 * Regex d'un numéro mauritanien (sans indicatif) : 8 chiffres commençant
 * par 2, 3 ou 4.
 */
export const REGEX_TELEPHONE_MR_LOCAL = /^[234]\d{7}$/;

/**
 * Regex d'un numéro mauritanien international : +222 puis 8 chiffres
 * commençant par 2, 3 ou 4 (espace toléré après +222).
 */
export const REGEX_TELEPHONE_MR_INTL = /^\+222\s?[234]\d{7}$/;

/**
 * Regex d'un numéro international générique : + suivi de 1-3 chiffres
 * d'indicatif, espace optionnel, puis 6-14 chiffres.
 */
export const REGEX_TELEPHONE_INTL = /^\+\d{1,3}\s?\d{6,14}$/;

/**
 * Normalisation : convertit en MAJUSCULES (respect Unicode, ex. accents).
 */
export function normaliserNom(value) {
  if (value === null || value === undefined) return value;
  return String(value).toLocaleUpperCase('fr-FR');
}

/**
 * Règle AntD : nom obligatoire converti en MAJUSCULES côté UI.
 * À utiliser conjointement avec `normalize={normaliserNom}` sur le Form.Item
 * pour transformer en temps réel.
 */
export function reglesNom(t, { required = true } = {}) {
  const regles = [
    {
      validator: (_, value) => {
        if (!value || !value.trim()) {
          return required
            ? Promise.reject(new Error(t('validation.nom.obligatoire')))
            : Promise.resolve();
        }
        if (value !== normaliserNom(value)) {
          // Sécurité : si la normalisation est désactivée côté UI,
          // on rejette explicitement les minuscules.
          return Promise.reject(new Error(t('validation.nom.majuscules')));
        }
        return Promise.resolve();
      },
    },
  ];
  return regles;
}

/**
 * Règle AntD : NNI mauritanien — exactement 10 chiffres, pas tous identiques.
 */
export function reglesNNI(t, { required = true } = {}) {
  return [
    {
      validator: (_, value) => {
        const v = (value || '').trim();
        if (!v) {
          return required
            ? Promise.reject(new Error(t('validation.nni.obligatoire')))
            : Promise.resolve();
        }
        if (!REGEX_NNI.test(v)) {
          return Promise.reject(new Error(t('validation.nni.format')));
        }
        // Refuse les séquences répétitives (tous les chiffres identiques)
        if (new Set(v.split('')).size === 1) {
          return Promise.reject(new Error(t('validation.nni.repetitif')));
        }
        return Promise.resolve();
      },
    },
  ];
}

/**
 * Règle AntD : passeport — champ non vide, min 4 caractères (minimum
 * raisonnable).
 */
export function reglesPasseport(t, { required = true } = {}) {
  return [
    {
      validator: (_, value) => {
        const v = (value || '').trim();
        if (!v) {
          return required
            ? Promise.reject(new Error(t('validation.passeport.obligatoire')))
            : Promise.resolve();
        }
        if (v.length < 4) {
          return Promise.reject(new Error(t('validation.passeport.trop_court')));
        }
        return Promise.resolve();
      },
    },
  ];
}

/**
 * Règle AntD : téléphone au format international, avec règle spéciale
 * pour la Mauritanie (+222 + 8 chiffres commençant par 2/3/4).
 */
export function reglesTelephone(t, { required = false } = {}) {
  return [
    {
      validator: (_, value) => {
        const v = (value || '').trim();
        if (!v) {
          return required
            ? Promise.reject(new Error(t('validation.telephone.obligatoire')))
            : Promise.resolve();
        }
        if (!v.startsWith('+')) {
          return Promise.reject(new Error(t('validation.telephone.indicatif_requis')));
        }
        // Cas Mauritanie : règle stricte 8 chiffres commençant par 2/3/4
        if (v.startsWith('+222')) {
          if (!REGEX_TELEPHONE_MR_INTL.test(v)) {
            return Promise.reject(new Error(t('validation.telephone.mr_format')));
          }
          return Promise.resolve();
        }
        // Autre pays : format international générique
        if (!REGEX_TELEPHONE_INTL.test(v)) {
          return Promise.reject(new Error(t('validation.telephone.intl_format')));
        }
        return Promise.resolve();
      },
    },
  ];
}


/**
 * Règle de validation AntD pour les champs e-mail.
 *
 * @param {function} t  fonction i18n
 * @param {object}   options
 * @param {boolean}  options.required  si true, le champ est obligatoire
 */
export function reglesEmail(t, { required = false } = {}) {
  const regles = [
    // type: 'email' apporte une première validation de format ; la regex
    // ci-dessous renforce et harmonise avec le backend.
    {
      type: 'email',
      message: t('validation.email.format_invalide'),
    },
    {
      validator: (_, value) => {
        if (!value) return Promise.resolve(); // champ vide → ok (sauf si required)
        const v = String(value).trim();
        if (!REGEX_EMAIL_STRICT.test(v)) {
          return Promise.reject(
            new Error(t('validation.email.format_invalide'))
          );
        }
        return Promise.resolve();
      },
    },
  ];
  if (required) {
    regles.unshift({
      required: true,
      message: t('validation.email.obligatoire'),
    });
  }
  return regles;
}
