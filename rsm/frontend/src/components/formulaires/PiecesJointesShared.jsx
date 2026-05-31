/**
 * Composant partagé : zone d'upload de pièces jointes PDF.
 *
 * Contraintes (refonte MO 2026-05-30) :
 *   - format : PDF uniquement ;
 *   - taille : 10 Mo maximum par fichier ;
 *   - nombre : plusieurs fichiers possibles ;
 *   - suppression possible avant soumission.
 *
 * L'upload effectif est différé : les fichiers sont mis en file
 * d'attente locale et envoyés au backend après création de
 * l'inscription via POST /inscriptions/<reference>/pieces-jointes/.
 */
import React from 'react';
import { Button, List, Modal, Typography, Upload } from 'antd';
import {
  PlusOutlined, DeleteOutlined, FilePdfOutlined,
} from '@ant-design/icons';

const { Paragraph } = Typography;

export const PJ_TAILLE_MAX = 10 * 1024 * 1024; // 10 Mo
export const PJ_TYPES_AUTORISES = ['application/pdf'];

/**
 * @param {object} props
 * @param {function} props.t                  fonction i18n
 * @param {array}    props.fichiers           file d'attente (état parent)
 * @param {function} props.setFichiers        setter de la file d'attente
 * @param {string}   [props.aide]             texte d'aide (sinon i18n par défaut)
 * @param {string}   [props.libelleBouton]    libellé bouton (sinon i18n par défaut)
 */
export default function PiecesJointesField({
  t, fichiers, setFichiers, aide, libelleBouton,
}) {
  const onAvantUpload = (fichier) => {
    if (!PJ_TYPES_AUTORISES.includes(fichier.type)) {
      Modal.error({
        title: t('formulaire.inscription.pj.erreur.type.titre'),
        content: t('formulaire.inscription.pj.erreur.type.contenu'),
      });
      return Upload.LIST_IGNORE;
    }
    if (fichier.size > PJ_TAILLE_MAX) {
      Modal.error({
        title: t('formulaire.inscription.pj.erreur.taille.titre'),
        content: t('formulaire.inscription.pj.erreur.taille.contenu', { max: 10 }),
      });
      return Upload.LIST_IGNORE;
    }
    setFichiers((curr) => [...curr, fichier]);
    return false; // empêche l'upload immédiat — différé après création
  };

  const onRetirer = (uid) => {
    setFichiers((curr) => curr.filter((p) => p.uid !== uid));
  };

  return (
    <>
      <Paragraph type="secondary" style={{ marginBottom: 12 }}>
        {aide || t('formulaire.inscription.pj.aide')}
      </Paragraph>
      <Upload
        accept=".pdf"
        beforeUpload={onAvantUpload}
        showUploadList={false}
        multiple
      >
        <Button icon={<PlusOutlined />}>
          {libelleBouton || t('formulaire.inscription.pj.bouton_ajouter')}
        </Button>
      </Upload>
      {fichiers.length > 0 && (
        <List
          size="small"
          style={{ marginTop: 12 }}
          dataSource={fichiers}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  key="retirer"
                  size="small" danger type="text"
                  icon={<DeleteOutlined />}
                  onClick={() => onRetirer(item.uid)}
                >
                  {t('formulaire.inscription.pj.retirer')}
                </Button>,
              ]}
            >
              <List.Item.Meta
                avatar={<FilePdfOutlined style={{ fontSize: 22, color: 'var(--rim-rouge)' }} />}
                title={item.name}
                description={`${(item.size / 1024 / 1024).toFixed(2)} Mo`}
              />
            </List.Item>
          )}
        />
      )}
    </>
  );
}


/**
 * Envoi séquentiel des fichiers à l'endpoint PJ d'une inscription
 * après sa création. Renvoie la liste des erreurs (rejets éventuels).
 *
 * @param {object} options
 * @param {object} options.client     axios client
 * @param {string} options.reference  reference_demande de l'inscription
 * @param {array}  options.fichiers   file d'attente
 * @param {function} options.formatErreur formatteur d'erreur i18n
 * @returns {Promise<string[]>}       liste des messages d'erreur
 */
export async function envoyerPiecesJointes({ client, reference, fichiers, formatErreur }) {
  const erreurs = [];
  for (const pj of fichiers) {
    try {
      const fd = new FormData();
      fd.append('fichier', pj.originFileObj || pj);
      await client.post(
        `/inscriptions/${reference}/pieces-jointes/`,
        fd,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      );
    } catch (eu) {
      erreurs.push(`${pj.name} : ${formatErreur(eu)}`);
    }
  }
  return erreurs;
}
