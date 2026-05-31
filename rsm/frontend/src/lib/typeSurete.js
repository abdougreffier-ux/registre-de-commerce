/**
 * Mapping ``type_surete`` → ``nature_droit`` pour les parcours
 * contextuels (privilege_vendeur, reserve_propriete, credit_bail).
 *
 * Dans ces 3 parcours, la nature du droit est intrinsèquement
 * déterminée par le type de sûreté inscrit ; l'utilisateur n'a
 * pas à la choisir (directive MO du 2026-05-31). Le frontend envoie
 * la valeur en silence pour satisfaire la contrainte backend
 * (le champ Inscription.nature_droit reste requis).
 *
 * Les valeurs cibles correspondent à des entrées présentes dans la
 * table LibelleNatureDroit (paramétrable) :
 *   - "priv_vendeur_fonds" : entrée native du décret (art. 76).
 *   - "reserve_propriete"  : ajoutée par data migration
 *                             referentiels.0002_natures_derivees.
 *   - "credit_bail"        : idem.
 *
 * Pour le parcours générique ``depot_surete``, l'utilisateur
 * choisit lui-même la nature dans la liste paramétrable complète.
 */
export const NATURE_DROIT_PAR_TYPE_SURETE = {
  privilege_vendeur: 'priv_vendeur_fonds',
  reserve_propriete: 'reserve_propriete',
  credit_bail: 'credit_bail',
};

/**
 * Canal de saisie unique du système.
 *
 * Le registre étant entièrement numérisé (directive MO du 2026-05-31),
 * le canal de saisie utilisateur est désormais implicite. L'enum
 * backend conserve les deux valeurs (guichet_papier, portail_electronique)
 * pour la traçabilité des dépôts historiques (art. 79).
 */
export const CANAL_SAISIE_DEFAUT = 'portail_electronique';
