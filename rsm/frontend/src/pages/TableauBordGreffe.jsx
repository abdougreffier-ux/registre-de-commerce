import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert, Button, Col, Empty, Row, Space, Spin, Table, Tag, Typography,
} from 'antd';
import {
  CheckCircleOutlined, ClockCircleOutlined, FileSearchOutlined,
  FormOutlined, ReloadOutlined, StopOutlined, AuditOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import { useAuth, aUnRole } from '../contexts/AuthContext';
import KpiCarte from '../components/KpiCarte';

const { Title, Paragraph, Text } = Typography;

/**
 * Tableau de bord du greffe — vue opérationnelle des demandes en attente.
 *
 * Visible uniquement pour les rôles ``autorite_validation`` ou
 * ``agent_saisie``. Les autres utilisateurs voient un message
 * fonctionnel renvoyant vers leur espace.
 */
export default function TableauBordGreffe() {
  const { t } = useTranslation();
  const auth = useAuth();
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);
  const [inscriptions, setInscriptions] = useState([]);
  const [modifications, setModifications] = useState([]);
  const [renouvellements, setRenouvellements] = useState([]);
  const [radiations, setRadiations] = useState([]);

  const peutAcceder = aUnRole(auth, ['autorite_validation', 'agent_saisie', 'auditeur']);

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur(null);
    try {
      const [insR, modR, renR, radR] = await Promise.all([
        client.get('/inscriptions/').catch(() => ({ data: { results: [] } })),
        client.get('/modifications/').catch(() => ({ data: { results: [] } })),
        client.get('/renouvellements/').catch(() => ({ data: { results: [] } })),
        client.get('/radiations/').catch(() => ({ data: { results: [] } })),
      ]);
      setInscriptions(insR.data.results || insR.data || []);
      setModifications(modR.data.results || modR.data || []);
      setRenouvellements(renR.data.results || renR.data || []);
      setRadiations(radR.data.results || radR.data || []);
    } catch (e) {
      setErreur(formatMessageErreur(e, t));
    } finally {
      setChargement(false);
    }
  }, [t]);

  useEffect(() => { if (peutAcceder) charger(); else setChargement(false); }, [charger, peutAcceder]);

  const fileEnInstance = useMemo(
    () => inscriptions.filter((i) => i.statut === 'en_controle_forme'),
    [inscriptions],
  );
  // Alias rétro-compatible (utilisé par des sections plus bas)
  const fileControleForme = fileEnInstance;
  const fileRetournees = useMemo(
    () => inscriptions.filter((i) => i.statut === 'retournee'),
    [inscriptions],
  );
  const fileInscrites = useMemo(
    () => inscriptions.filter((i) => i.statut === 'inscrite'),
    [inscriptions],
  );
  const fileRejetees = useMemo(
    () => inscriptions.filter((i) => i.statut === 'rejetee'),
    [inscriptions],
  );

  if (!peutAcceder) {
    return (
      <div>
        <Title level={2}>{t('greffe.titre')}</Title>
        <Alert
          type="warning"
          showIcon
          message={t('greffe.acces_refuse.titre')}
          description={t('greffe.acces_refuse.description')}
        />
        <Link to="/" style={{ marginTop: 16, display: 'inline-block' }}>
          <Button>{t('detail.retour')}</Button>
        </Link>
      </div>
    );
  }

  if (chargement) return <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>;

  return (
    <div>
      <Title level={2}>{t('greffe.titre')}</Title>
      <Paragraph>{t('greffe.introduction')}</Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      {/* ============= KPI principaux ============= */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} md={6}>
          <KpiCarte
            icone={<ClockCircleOutlined />} accent="jaune"
            libelle={t('greffe.kpi.demandes_en_instance')}
            valeur={fileEnInstance.length}
            hint={t('greffe.kpi.demandes_en_instance_hint')}
          />
        </Col>
        <Col xs={12} md={6}>
          <KpiCarte
            icone={<ClockCircleOutlined />} accent="rouge"
            libelle={t('greffe.kpi.retournees')}
            valeur={fileRetournees.length}
            hint={t('greffe.kpi.retournees_hint')}
          />
        </Col>
        <Col xs={12} md={6}>
          <KpiCarte
            icone={<FormOutlined />}
            libelle={t('greffe.kpi.modifications_attente')}
            valeur={modifications.filter((m) => m.statut === 'recue').length}
            hint={`${modifications.length} ${t('greffe.kpi.total_suffixe')}`}
          />
        </Col>
        <Col xs={12} md={6}>
          <KpiCarte
            icone={<StopOutlined />} accent="rouge"
            libelle={t('greffe.kpi.radiations_attente')}
            valeur={radiations.filter((r) => r.statut === 'recue').length}
            hint={`${radiations.length} ${t('greffe.kpi.total_suffixe')}`}
          />
        </Col>
      </Row>

      {/* ============= Demandes en instance (en_controle_forme) ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre --jaune">
            {t('greffe.file_en_instance.titre')}
          </h2>
          <p className="rim-section__sous-titre">
            {t('greffe.file_en_instance.sous_titre')}
          </p>
        </div>
        {fileEnInstance.length === 0 ? (
          <Empty description={t('greffe.file_en_instance.vide')} />
        ) : (
          <Table
            dataSource={fileEnInstance}
            rowKey={(r) => r.reference_demande}
            pagination={false}
            columns={[
              {
                title: t('greffe.col.reference'),
                dataIndex: 'reference_demande',
                render: (v) => <Text code>{String(v).slice(0, 8)}…</Text>,
              },
              { title: t('greffe.col.nature'), dataIndex: 'nature_droit_libelle' },
              {
                title: t('greffe.col.canal'), dataIndex: 'canal_saisie',
                render: (v) => <Tag>{t(`formulaire.inscription.canal.${v}`, v)}</Tag>,
              },
              { title: t('greffe.col.arrivee'), dataIndex: 'instant_arrivee' },
              {
                title: '', key: 'actions',
                render: (_, r) => (
                  <Link to={`/inscriptions/${r.reference_demande}`}>
                    <Button type="primary" size="small" icon={<CheckCircleOutlined />}>
                      {t('greffe.col.bouton_traiter')}
                    </Button>
                  </Link>
                ),
              },
            ]}
          />
        )}
      </section>

      {/* ============= Demandes retournées (en attente déclarant) ============= */}
      {fileRetournees.length > 0 && (
        <section className="rim-section">
          <div className="rim-section__entete">
            <h2 className="rim-section__titre --rouge">
              {t('greffe.file_retournees.titre')}
            </h2>
            <p className="rim-section__sous-titre">
              {t('greffe.file_retournees.sous_titre')}
            </p>
          </div>
          <Table
            dataSource={fileRetournees}
            rowKey={(r) => r.reference_demande}
            pagination={false}
            columns={[
              {
                title: t('greffe.col.reference'),
                dataIndex: 'reference_demande',
                render: (v) => <Text code>{String(v).slice(0, 8)}…</Text>,
              },
              { title: t('greffe.col.nature'), dataIndex: 'nature_droit_libelle' },
              { title: t('greffe.col.arrivee'), dataIndex: 'instant_arrivee' },
              {
                title: '', key: 'actions',
                render: (_, r) => (
                  <Link to={`/inscriptions/${r.reference_demande}`}>
                    <Button size="small">
                      {t('greffe.col.bouton_consulter')}
                    </Button>
                  </Link>
                ),
              },
            ]}
          />
        </section>
      )}

      {/* ============= Aperçu des autres files ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre">
            {t('greffe.apercus.titre')}
          </h2>
        </div>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <KpiCarte
              icone={<FileSearchOutlined />}
              libelle={t('greffe.apercus.inscrites')}
              valeur={fileInscrites.length}
              hint={t('greffe.apercus.inscrites_hint')}
            />
          </Col>
          <Col xs={24} md={12}>
            <KpiCarte
              icone={<AuditOutlined />} accent="rouge"
              libelle={t('greffe.apercus.rejetees')}
              valeur={fileRejetees.length}
              hint={t('greffe.apercus.rejetees_hint')}
            />
          </Col>
        </Row>
      </section>

      <Space style={{ marginTop: 24 }}>
        <Link to="/inscriptions"><Button>{t('greffe.lien_liste_complete')}</Button></Link>
        <Link to="/audit"><Button icon={<AuditOutlined />}>{t('menu.audit')}</Button></Link>
        <Link to="/statistiques"><Button>{t('menu.statistiques')}</Button></Link>
      </Space>
    </div>
  );
}
