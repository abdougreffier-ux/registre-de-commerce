import React, {
  createContext, useCallback, useContext, useEffect, useMemo, useState,
} from 'react';

import client from '../api/client';

/**
 * Contexte d'authentification — consomme les endpoints
 * /api/v1/auth/whoami/, /api/v1/auth/login/, /api/v1/auth/logout/.
 *
 * Aucune information sensible n'est persistée côté client : seule la
 * session Django (cookie ``sessionid``) fait autorité. L'état React
 * reflète uniquement le résultat du dernier ``whoami``.
 */
const AuthContext = createContext(null);

const ETAT_INITIAL = {
  pret: false,
  authentifie: false,
  utilisateur: null,
  roles: [],
  systeme: { mode_test: false },
};

export function AuthProvider({ children }) {
  const [etat, setEtat] = useState(ETAT_INITIAL);

  const rafraichir = useCallback(async () => {
    try {
      const { data } = await client.get('/auth/whoami/');
      setEtat({
        pret: true,
        authentifie: !!data.authentifie,
        utilisateur: data.authentifie ? data : null,
        roles: data.roles || [],
        systeme: data.systeme || { mode_test: false },
      });
      return data;
    } catch (e) {
      setEtat({
        pret: true, authentifie: false, utilisateur: null, roles: [],
        systeme: { mode_test: false },
      });
      return null;
    }
  }, []);

  useEffect(() => {
    rafraichir();
  }, [rafraichir]);

  const seConnecter = useCallback(async ({ username, password }) => {
    const { data } = await client.post('/auth/login/', { username, password });
    if (data && data.authentifie) {
      setEtat({
        pret: true,
        authentifie: true,
        utilisateur: data,
        roles: data.roles || [],
        systeme: data.systeme || { mode_test: false },
      });
      return { ok: true, utilisateur: data };
    }
    return { ok: false };
  }, []);

  /**
   * Change le mot de passe de l'utilisateur courant.
   * Ne génère aucune entrée d'audit métier (art. 79).
   */
  const changerMotDePasse = useCallback(async ({ ancien, nouveau, confirmation }) => {
    const { data } = await client.post('/auth/changer-mot-de-passe/', {
      ancien, nouveau, confirmation,
    });
    if (data && data.authentifie) {
      setEtat((prev) => ({
        ...prev,
        utilisateur: data,
        roles: data.roles || prev.roles,
        systeme: data.systeme || prev.systeme,
      }));
    }
    return data;
  }, []);

  const seDeconnecter = useCallback(async () => {
    let systeme = { mode_test: false };
    try {
      const rep = await client.post('/auth/logout/', {});
      if (rep?.data?.systeme) systeme = rep.data.systeme;
    } catch (_) {
      // la session a déjà pu expirer : on vide l'état local de toute façon
    }
    setEtat({
      pret: true, authentifie: false, utilisateur: null, roles: [], systeme,
    });
  }, []);

  const valeur = useMemo(
    () => ({
      ...etat,
      motDePasseInitial: !!etat.utilisateur?.mot_de_passe_initial,
      rafraichir, seConnecter, seDeconnecter, changerMotDePasse,
    }),
    [etat, rafraichir, seConnecter, seDeconnecter, changerMotDePasse],
  );

  return <AuthContext.Provider value={valeur}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth doit être utilisé à l’intérieur d’un <AuthProvider>.');
  }
  return ctx;
}

/**
 * Retourne ``true`` si l'utilisateur courant porte au moins un des rôles
 * fournis. Utilisé pour n'activer la soumission d'une demande que pour
 * un Agent de saisie ou un Déclarant externe (TDR § 4.1).
 */
export function aUnRole(auth, rolesRequis) {
  if (!auth || !auth.authentifie) return false;
  if (!rolesRequis || rolesRequis.length === 0) return true;
  return rolesRequis.some((r) => auth.roles.includes(r));
}
