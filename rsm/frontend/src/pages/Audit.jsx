import React, { useEffect, useState } from 'react';
import { Alert, Table, Tag, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';

const { Title, Paragraph } = Typography;

export default function Audit() {
  const { t } = useTranslation();
  const [entrees, setEntrees] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await client.get('/audit/entrees/');
        setEntrees(data.results || data || []);
      } catch (e) {
        setErreur(formatMessageErreur(e, t));
      } finally {
        setChargement(false);
      }
    })();
  }, [t]);

  const colonnes = [
    { title: 'Instant', dataIndex: 'instant' },
    { title: 'Catégorie', dataIndex: 'categorie', render: (v) => <Tag>{v}</Tag> },
    { title: 'Action', dataIndex: 'action_cle' },
    { title: 'Acteur', dataIndex: 'acteur' },
    { title: 'Rôle', dataIndex: 'acteur_role' },
    { title: 'Objet', dataIndex: 'objet_reference' },
    { title: 'Résultat', dataIndex: 'resultat' },
  ];

  return (
    <div>
      <Title level={2}>{t('menu.audit')}</Title>
      <Paragraph>Lecture seule — tout ajout est irrévocable (article 79).</Paragraph>
      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}
      <Table dataSource={entrees} columns={colonnes} loading={chargement} rowKey="id" />
    </div>
  );
}
