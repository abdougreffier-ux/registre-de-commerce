import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert, Button, Col, Empty, Row, Space, Spin, Table, Typography,
} from 'antd';
import {
  FileAddOutlined, EditOutlined, ReloadOutlined, StopOutlined,
  EyeOutlined, ClockCircleOutlined, CheckCircleOutlined, KeyOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import KpiCarte from '../components/KpiCarte';
import StatutBadge from '../components/StatutBadge';

const { Title, Paragraph, Text } = Typography;

/**
 * Espace personnel d'un déclarant — synthèse de ses inscriptions et
 * échéances.
 *
 * Le filtrage est effectué côté client à partir du résultat de
 * ``/api/v1/inscriptions/`` ; il s'agit d'une présentation, pas d'une
 * règle métier (l'autorisation d'accès aux données reste du ressort
 * du backend).
 */
export default function MonEspace() {
  const { t } = useTranslation();
  const auth = useAuth();
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);
  const [inscriptions, setInscriptions] = useState([]);

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur(null);
    try {
      const { data } = await client.get('/inscriptions/');
      setInscriptions(data.results || data || []);
    } catch (e) {
      setErreur(formatMessageErreur(e, t));
    } finally {
      setChargement(false);
    }
  }, [t]);

  useEffect(() => { if (auth.authentifie) charger(); else setChargement(false); }, [charger, auth.authentifie]);

  // Filtrage : les inscriptions du déclarant connecté.
  const userId = auth.utilisateur?.id;
  const mesInscriptions = useMemo(
    () => inscriptions.filter((i) => i.cree_par == null || i.cree_par === userId),
    [inscriptions, userId],
  );

  const enAttente = mesInscriptions.filter((i) => i.statut === 'en_controle_forme');
  const retournees = mesInscriptions.filter((i) => i.statut === 'retournee');
  const inscritesActives = mesInscriptions.filter((i) => i.statut === 'inscrite');
  const radiees = mesInscriptions.filter((i) => i.statut === 'radiee');
  const rejetees = mesInscriptions.filter((i) => i.statut === 'rejetee');

  // Échéances proches : inscriptions actives expirant dans 90 jours.
  const aujourdhui = new Date();
  const dans90j = new Date();
  dans90j.setDate(dans90j.getDate() + 90);
  const echeancesProches = inscritesActives.filter((i) => {
    if (!i.date_expiration) return false;
    const exp = new Date(i.date_expiration);
    return exp >= aujourdhui && exp <= dans90j;
  });

  if (!auth.authentifie) {
    return (
      <div>
        <Title level={2}>{t('mon_espace.titre')}</Title>
        <Alert
          type="info"
          showIcon
          message={t('mon_espace.connexion_requise.titre')}
          description={t('mon_espace.connexion_requise.description')}
        />
        <Space style={{ marginTop: 16 }}>
          <Link to="/connexion"><Button type="primary">{t('auth.connexion')}</Button></Link>
        </Space>
      </div>
    );
  }

  if (chargement) return <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>;

  return (
    <div>
      <Title level={2}>
        {t('mon_espace.titre')}
        {auth.utilisateur && (
          <Text type="secondary" style={{ fontSize: 16, marginLeft: 12 }}>
            — {auth.utilisateur.nom_affichage || auth.utilisateur.username}
          </Text>
        )}
      </Title>
      <Paragraph>{t('mon_espace.introduction')}</Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      {/* ============= KPI personnels ============= */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} md={6}>
          <KpiCarte
            icone={<CheckCircleOutlined />}
            libelle={t('mon_espace.kpi.actives')}
            valeur={inscritesActives.length}
            hint={t('mon_espace.kpi.actives_hint')}
          />
        </Col>
        <Col xs={12} md={6}>
          <KpiCarte
            icone={<ClockCircleOutlined />} accent="jaune"
            libelle={t('mon_espace.kpi.attente')}
            valeur={enAttente.length}
            hint={t('mon_espace.kpi.attente_hint')}
          />
        </Col>
        <Col xs={12} md={6}>
          <KpiCarte
            icone={<ReloadOutlined />} accent="rouge"
            libelle={t('mon_espace.kpi.a_corriger')}
            valeur={retournees.length}
            hint={t('mon_espace.kpi.a_corriger_hint')}
          />
        </Col>
        <Col xs={12} md={6}>
          <KpiCarte
            icone={<StopOutlined />} accent="rouge"
            libelle={t('mon_espace.kpi.radiees')}
            valeur={radiees.length}
            hint={`${rejetees.length} ${t('mon_espace.kpi.rejetees_hint')}`}
          />
        </Col>
      </Row>

      {/* ============= Demandes à corriger (RETOURNEES) ============= */}
      {retournees.length > 0 && (
        <section className="rim-section">
          <div className="rim-section__entete">
            <h2 className="rim-section__titre --rouge">
              {t('mon_espace.a_corriger.titre')}
            </h2>
            <p className="rim-section__sous-titre">
              {t('mon_espace.a_corriger.sous_titre')}
            </p>
          </div>
          <Table
            dataSource={retournees}
            rowKey={(r) => r.reference_demande}
            pagination={false}
            columns={[
              {
                title: t('greffe.col.reference'),
                dataIndex: 'numero_ordre',
                render: (v, r) => v || (
                  <Text code>{String(r.reference_demande).slice(0, 8)}…</Text>
                ),
              },
              { title: t('greffe.col.nature'), dataIndex: 'nature_droit_libelle' },
              { title: t('greffe.col.arrivee'), dataIndex: 'instant_arrivee' },
              {
                title: '', key: 'actions',
                render: (_, r) => (
                  <Link to={`/inscriptions/${r.reference_demande}`}>
                    <Button type="primary" size="small">
                      {t('mon_espace.a_corriger.bouton')}
                    </Button>
                  </Link>
                ),
              },
            ]}
          />
        </section>
      )}

      {/* ============= Démarches rapides ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre">{t('mon_espace.actions.titre')}</h2>
        </div>
        <Space wrap>
          <Link to="/formulaires/inscription">
            <Button type="primary" icon={<FileAddOutlined />} size="large">
              {t('menu.formulaire.inscription')}
            </Button>
          </Link>
          <Link to="/formulaires/modification">
            <Button icon={<EditOutlined />} size="large">
              {t('menu.formulaire.modification')}
            </Button>
          </Link>
          <Link to="/formulaires/renouvellement">
            <Button icon={<ReloadOutlined />} size="large">
              {t('menu.formulaire.renouvellement')}
            </Button>
          </Link>
          <Link to="/formulaires/radiation">
            <Button icon={<StopOutlined />} size="large" danger>
              {t('menu.formulaire.radiation')}
            </Button>
          </Link>
        </Space>
        <div style={{ marginTop: 18 }}>
          <Link to="/changer-mot-de-passe">
            <Button icon={<KeyOutlined />}>
              {t('mdp.lien_menu')}
            </Button>
          </Link>
        </div>
      </section>

      {/* ============= Échéances proches ============= */}
      {echeancesProches.length > 0 && (
        <section className="rim-section">
          <div className="rim-section__entete">
            <h2 className="rim-section__titre --jaune">{t('mon_espace.echeances.titre')}</h2>
            <p className="rim-section__sous-titre">{t('mon_espace.echeances.sous_titre')}</p>
          </div>
          <Table
            dataSource={echeancesProches}
            rowKey={(r) => r.reference_demande}
            pagination={false}
            columns={[
              { title: t('greffe.col.reference'), dataIndex: 'numero_ordre',
                render: (v, r) => v || <Text code>{String(r.reference_demande).slice(0, 8)}…</Text> },
              { title: t('greffe.col.nature'), dataIndex: 'nature_droit_libelle' },
              { title: t('mon_espace.col.expiration'), dataIndex: 'date_expiration' },
              {
                title: '', key: 'actions',
                render: (_, r) => (
                  <Link to={`/inscriptions/${r.reference_demande}`}>
                    <Button size="small" icon={<EyeOutlined />}>
                      {t('inscriptions.consulter')}
                    </Button>
                  </Link>
                ),
              },
            ]}
          />
        </section>
      )}

      {/* ============= Mes inscriptions ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre">{t('mon_espace.liste.titre')}</h2>
        </div>
        {mesInscriptions.length === 0 ? (
          <Empty description={t('mon_espace.liste.vide')} />
        ) : (
          <Table
            dataSource={mesInscriptions}
            rowKey={(r) => r.reference_demande}
            columns={[
              { title: t('greffe.col.reference'), dataIndex: 'numero_ordre',
                render: (v, r) => v || <Text code>{String(r.reference_demande).slice(0, 8)}…</Text> },
              { title: t('greffe.col.nature'), dataIndex: 'nature_droit_libelle' },
              { title: t('detail.champ.statut'), dataIndex: 'statut',
                render: (v) => <StatutBadge statut={v} /> },
              { title: t('greffe.col.arrivee'), dataIndex: 'instant_arrivee' },
              {
                title: '', key: 'actions',
                render: (_, r) => (
                  <Link to={`/inscriptions/${r.reference_demande}`}>
                    <Button size="small">{t('inscriptions.consulter')}</Button>
                  </Link>
                ),
              },
            ]}
          />
        )}
      </section>
    </div>
  );
}
