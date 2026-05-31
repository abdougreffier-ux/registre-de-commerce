import React, { useEffect, useState } from 'react';
import { Alert, Button, Table, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import StatutBadge from '../components/StatutBadge';

const { Title } = Typography;

export default function Inscriptions() {
  const { t } = useTranslation();
  const [lignes, setLignes] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await client.get('/inscriptions/');
        setLignes(data.results || data || []);
      } catch (e) {
        setErreur(formatMessageErreur(e, t));
      } finally {
        setChargement(false);
      }
    })();
  }, [t]);

  const colonnes = [
    {
      title: t('inscription.colonne.numero'),
      dataIndex: 'numero_ordre',
      render: (v, r) => v || (
        <Link to={`/inscriptions/${r.reference_demande}`}>
          {String(r.reference_demande).slice(0, 8)}…
        </Link>
      ),
    },
    { title: t('inscription.colonne.nature'), dataIndex: 'nature_droit_libelle' },
    {
      title: t('inscription.colonne.statut'),
      dataIndex: 'statut',
      render: (s) => <StatutBadge statut={s} />,
    },
    { title: t('inscription.colonne.arrivee'), dataIndex: 'instant_arrivee' },
    { title: t('inscription.colonne.expiration'), dataIndex: 'date_expiration' },
    {
      title: '',
      key: 'actions',
      render: (_, r) => (
        <Link to={`/inscriptions/${r.reference_demande}`}>
          <Button size="small">{t('inscriptions.consulter')}</Button>
        </Link>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>{t('menu.inscriptions')}</Title>
      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}
      <Table
        dataSource={lignes}
        columns={colonnes}
        loading={chargement}
        rowKey={(r) => r.reference_demande}
      />
    </div>
  );
}
