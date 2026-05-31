import React from 'react';
import { Alert, Card, Col, Row, Space, Tag, Typography } from 'antd';
import {
  BankOutlined, SafetyCertificateOutlined, ApiOutlined, AuditOutlined,
  LockOutlined, FileSearchOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../contexts/AuthContext';

const { Title, Paragraph, Text } = Typography;

/**
 * Page informative dédiée aux partenaires bancaires (fiche F15).
 *
 * Aucun endpoint actif : la page expose uniquement la procédure
 * d'agrément, le périmètre cible des API et les références juridiques.
 * Tant que ``systeme.interop_banques_mode !== 'active'``, les routes
 * /api/v1/banques/* sont absentes du backend.
 */
export default function PartenairesBancaires() {
  const { t } = useTranslation();
  const auth = useAuth();
  const mode = auth?.systeme?.interop_banques_mode || 'disabled';
  const actif = mode === 'active';

  return (
    <div>
      <Title level={2}>{t('partenaires.titre')}</Title>
      <Paragraph>{t('partenaires.introduction')}</Paragraph>

      <Alert
        type={actif ? 'success' : 'warning'}
        showIcon
        style={{ marginBottom: 16 }}
        message={
          actif ? t('partenaires.statut.actif')
                : t('partenaires.statut.en_preparation')
        }
        description={
          actif ? t('partenaires.statut.actif_desc')
                : t('partenaires.statut.en_preparation_desc')
        }
      />

      {/* ============= Cas d'usage cible ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre">{t('partenaires.cas_usage.titre')}</h2>
          <p className="rim-section__sous-titre">{t('partenaires.cas_usage.sous_titre')}</p>
        </div>

        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card>
              <Space direction="vertical" size={6}>
                <FileSearchOutlined style={{ fontSize: 22, color: 'var(--rim-vert-fonce)' }} />
                <Text strong>{t('partenaires.cas.pre_decision.titre')}</Text>
                <Text type="secondary">{t('partenaires.cas.pre_decision.description')}</Text>
                <Tag color="green">{t('partenaires.cas.conformite_94_96')}</Tag>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Space direction="vertical" size={6}>
                <AuditOutlined style={{ fontSize: 22, color: 'var(--rim-vert-fonce)' }} />
                <Text strong>{t('partenaires.cas.surveillance.titre')}</Text>
                <Text type="secondary">{t('partenaires.cas.surveillance.description')}</Text>
                <Tag color="green">{t('partenaires.cas.consentement')}</Tag>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Space direction="vertical" size={6}>
                <ApiOutlined style={{ fontSize: 22, color: 'var(--rim-vert-fonce)' }} />
                <Text strong>{t('partenaires.cas.depot_automatise.titre')}</Text>
                <Text type="secondary">{t('partenaires.cas.depot_automatise.description')}</Text>
                <Tag color="green">{t('partenaires.cas.canal_electronique')}</Tag>
              </Space>
            </Card>
          </Col>
        </Row>
      </section>

      {/* ============= Cas hors décret ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre --rouge">{t('partenaires.exclus.titre')}</h2>
        </div>
        <Alert
          type="error"
          showIcon
          message={t('partenaires.exclus.titre')}
          description={(
            <ul style={{ margin: '6px 0 0 0', paddingInlineStart: 20 }}>
              <li>{t('partenaires.exclus.notification_inverse')}</li>
              <li>{t('partenaires.exclus.statistiques_externes')}</li>
              <li>{t('partenaires.exclus.privilege_acces')}</li>
            </ul>
          )}
        />
      </section>

      {/* ============= Garanties ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre">{t('partenaires.garanties.titre')}</h2>
        </div>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card>
              <Space direction="vertical" size={6}>
                <LockOutlined style={{ fontSize: 22, color: 'var(--rim-vert-fonce)' }} />
                <Text strong>{t('partenaires.garanties.authentification.titre')}</Text>
                <Text type="secondary">{t('partenaires.garanties.authentification.description')}</Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card>
              <Space direction="vertical" size={6}>
                <SafetyCertificateOutlined style={{ fontSize: 22, color: 'var(--rim-vert-fonce)' }} />
                <Text strong>{t('partenaires.garanties.certificat.titre')}</Text>
                <Text type="secondary">{t('partenaires.garanties.certificat.description')}</Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card>
              <Space direction="vertical" size={6}>
                <AuditOutlined style={{ fontSize: 22, color: 'var(--rim-vert-fonce)' }} />
                <Text strong>{t('partenaires.garanties.audit.titre')}</Text>
                <Text type="secondary">{t('partenaires.garanties.audit.description')}</Text>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card>
              <Space direction="vertical" size={6}>
                <BankOutlined style={{ fontSize: 22, color: 'var(--rim-vert-fonce)' }} />
                <Text strong>{t('partenaires.garanties.reversibilite.titre')}</Text>
                <Text type="secondary">{t('partenaires.garanties.reversibilite.description')}</Text>
              </Space>
            </Card>
          </Col>
        </Row>
      </section>

      {/* ============= Procédure d'agrément ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre --jaune">{t('partenaires.procedure.titre')}</h2>
        </div>
        <Card>
          <ol style={{ paddingInlineStart: 20, lineHeight: 1.8 }}>
            <li>{t('partenaires.procedure.etape1')}</li>
            <li>{t('partenaires.procedure.etape2')}</li>
            <li>{t('partenaires.procedure.etape3')}</li>
            <li>{t('partenaires.procedure.etape4')}</li>
            <li>{t('partenaires.procedure.etape5')}</li>
          </ol>
        </Card>
      </section>

      {/* ============= Cadrage juridique ============= */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <h2 className="rim-section__titre">{t('partenaires.juridique.titre')}</h2>
        </div>
        <Card>
          <Space direction="vertical" size={6}>
            <Text>{t('partenaires.juridique.art94')}</Text>
            <Text>{t('partenaires.juridique.art96')}</Text>
            <Text>{t('partenaires.juridique.art97')}</Text>
            <Text>{t('partenaires.juridique.art82')}</Text>
            <Text>{t('partenaires.juridique.art83')}</Text>
            <Text>{t('partenaires.juridique.art79')}</Text>
          </Space>
          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            {t('partenaires.juridique.fiche')}
          </Paragraph>
        </Card>
      </section>
    </div>
  );
}
