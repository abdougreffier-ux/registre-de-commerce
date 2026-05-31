/**
 * Helper de soumission unifié pour tous les formulaires d'inscription.
 *
 * Crée l'inscription via POST /inscriptions/, puis envoie en séquence
 * les pièces jointes locales si présentes. Affiche un Modal de
 * confirmation listant les éventuels rejets PJ.
 *
 * Garde-fous :
 *   - intégrité : un seul appel POST métier ; les PJ sont liées à
 *     l'inscription créée (pas avant) ;
 *   - traçabilité : chaque appel est tracé côté backend ;
 *   - rétro-compat : payload reste rétro-compatible avec depot_surete.
 */
import { Modal } from 'antd';

import { envoyerPiecesJointes } from './PiecesJointesShared';

export async function soumettreInscription({
  client, t, payload, fichiersPj, formatErreur,
  resetForm, resetFichiers,
}) {
  const { data } = await client.post('/inscriptions/', payload);
  const reference = data.reference_demande;

  const pjErreurs = await envoyerPiecesJointes({
    client,
    reference,
    fichiers: fichiersPj || [],
    formatErreur,
  });

  const contenu = [
    `${t('soumission.succes.contenu')} (${reference || ''})`,
    pjErreurs.length
      ? `\n\n${t('formulaire.inscription.pj.erreurs')} :\n${pjErreurs.join('\n')}`
      : '',
  ].join('');

  Modal.success({
    title: t('soumission.succes.titre'),
    content: contenu,
    okText: t('soumission.fermer'),
  });
  if (resetForm) resetForm();
  if (resetFichiers) resetFichiers([]);
}
