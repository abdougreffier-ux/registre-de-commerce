/**
 * Client HTTP du frontend.
 *
 * Aucune logique métier ici : la logique réside dans le backend.
 * Le client ajoute l'entête Accept-Language à partir de la langue active,
 * ce qui n'a AUCUN effet sur la substance juridique — seulement sur les
 * éventuelles réponses localisées par le serveur.
 *
 * ``formatMessageErreur`` garantit qu'AUCUN message générique ne soit
 * affiché : toute erreur est traduite en un libellé fonctionnel précis,
 * strictement identique en FR et en AR via les clés ``erreur.*``.
 */
import axios from 'axios';
import i18n from '../i18n';

const client = axios.create({
  baseURL: process.env.REACT_APP_API_BASE || '/api/v1',
  timeout: 15000,
  withCredentials: true,
});

/**
 * Lit un cookie par son nom (Django pose ``csrftoken``).
 */
function lireCookie(nom) {
  if (typeof document === 'undefined') return null;
  const cibles = document.cookie ? document.cookie.split('; ') : [];
  for (const ligne of cibles) {
    const [cle, ...reste] = ligne.split('=');
    if (decodeURIComponent(cle) === nom) {
      return decodeURIComponent(reste.join('='));
    }
  }
  return null;
}

client.interceptors.request.use((config) => {
  config.headers['Accept-Language'] = i18n.language || 'fr';
  // Méthodes mutantes : injecter le jeton CSRF lu depuis le cookie
  // ``csrftoken`` posé par ``WhoamiView`` (via ``ensure_csrf_cookie``).
  const methode = (config.method || 'get').toLowerCase();
  if (!['get', 'head', 'options', 'trace'].includes(methode)) {
    const jeton = lireCookie('csrftoken');
    if (jeton) config.headers['X-CSRFToken'] = jeton;
  }
  return config;
});

/**
 * Traduit une erreur Axios en message fonctionnel bilingue.
 * Aucun message générique : pour chaque type d'erreur rencontrée, un
 * libellé spécifique doit être retourné.
 */
export function formatMessageErreur(erreur, t) {
  // 1) Aucune réponse HTTP : panne réseau / backend indisponible.
  if (!erreur || !erreur.response) {
    return t('erreur.reseau');
  }

  const statut = erreur.response.status;
  const donnees = erreur.response.data;

  // 2) Authentification / autorisation — messages procéduraux explicites.
  if (statut === 401) return t('erreur.authentification_requise');
  if (statut === 403) {
    const detail = extraireDetail(donnees);
    return detail
      ? `${t('erreur.autorisation_refusee')} — ${detail}`
      : t('erreur.autorisation_refusee');
  }

  // 3) Erreurs métier backend (ErreurMetierRSM → 400 {detail, article}).
  if (donnees && typeof donnees === 'object') {
    if (donnees.detail) {
      const article = donnees.article ? ` (${donnees.article})` : '';
      return `${donnees.detail}${article}`;
    }
    if (donnees.motif_refus) {
      return String(donnees.motif_refus);
    }
    if (donnees.message) {
      return String(donnees.message);
    }
    // 4) Erreurs de validation DRF : `{champ: ["erreur1", "erreur2"]}`.
    const erreursChamps = Object.entries(donnees)
      .filter(([, v]) => Array.isArray(v) && v.length > 0)
      .map(([champ, messages]) => `${champ} : ${messages.join(', ')}`);
    if (erreursChamps.length > 0) {
      return `${t('erreur.validation')} — ${erreursChamps.join(' · ')}`;
    }
  }

  // 5) Erreurs serveur / passerelle.
  if (statut >= 500 && statut <= 599) return t('erreur.service_indisponible');
  if (statut === 404) return t('erreur.ressource_introuvable');
  if (statut === 409) return t('erreur.conflit_etat');
  if (statut === 429) return t('erreur.trop_de_demandes');

  // 6) Dernier recours : on affiche le code HTTP pour traçabilité.
  return t('erreur.http_statut', { statut });
}

function extraireDetail(donnees) {
  if (!donnees) return null;
  if (typeof donnees === 'string') return null;
  if (donnees.detail) return String(donnees.detail);
  return null;
}

export default client;

export async function rechercher(criteres) {
  const { data } = await client.post('/recherche/', criteres);
  return data;
}
