/**
 * Conversion d'un montant en lettres — français et arabe.
 *
 * Utilisé en temps réel sous le champ "Somme garantie" du formulaire
 * d'inscription (art. 85). Le backend conserve une version autoritative
 * via la bibliothèque ``num2words`` (Python) ; le frontend produit
 * uniquement l'aperçu instantané pour l'utilisateur.
 *
 * Garde-fous :
 *   - parité FR/AR stricte : le même montant produit toujours la même
 *     chaîne dans les deux langues, indépendamment de l'environnement.
 *   - graceful degradation : si la bibliothèque n'est pas disponible
 *     ou si la valeur est invalide, renvoie une chaîne vide.
 */
import { toCardinal as cardinalFr } from 'n2words/fr-FR';
import { toCardinal as cardinalAr } from 'n2words/ar-SA';

/**
 * @param {number|string} montant — montant numérique (ex. 100000 ou "100000.50")
 * @param {string} monnaie       — code monnaie ISO 4217 (ex. "MRU")
 * @param {string} langue        — "fr" ou "ar"
 * @returns {string}             — montant en lettres, monnaie incluse
 */
export function montantEnLettres(montant, monnaie, langue) {
  const n = Number(montant);
  if (!Number.isFinite(n) || n <= 0) return '';
  const langueNorm = (langue || 'fr').toLowerCase();
  const isAr = langueNorm.startsWith('ar');
  try {
    const entier = Math.floor(n);
    const centimes = Math.round((n - entier) * 100);
    let texte = isAr ? cardinalAr(entier) : cardinalFr(entier);
    if (centimes > 0) {
      const centimesTxt = isAr ? cardinalAr(centimes) : cardinalFr(centimes);
      texte += isAr ? ` و ${centimesTxt}` : ` et ${centimesTxt} centimes`;
    }
    if (monnaie) {
      texte = `${texte} ${monnaie}`;
    }
    return texte;
  } catch {
    return '';
  }
}
