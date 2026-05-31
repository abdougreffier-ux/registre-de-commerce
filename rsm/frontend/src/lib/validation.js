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
