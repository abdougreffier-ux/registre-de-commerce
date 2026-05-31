import React from 'react';
import { Card, Col, Row, Space, Typography } from 'antd';
import {
  FileTextOutlined, ShopOutlined, SafetyCertificateOutlined,
  BankOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const { Title, Paragraph, Text } = Typography;

/**
 * Page de choix du type de sûreté à inscrire.
 *
 * 4 cartes :
 *   - depot_surete      → formulaire historique (art. 76, liste limitative)
 *   - privilege_vendeur → privilège du vendeur
 *   - reserve_propriete → vente avec réserve du droit de propriété
 *   - credit_bail       → contrat de crédit-bail
 *
 * L'utilisateur sélectionne le type avant de saisir les données. Les
 * 4 parcours partagent le même endpoint backend ; le payload porte le
 * champ ``type_surete`` qui distingue les inscriptions au registre.
 */
export default function ChoixTypeSurete() {
  const { t } = useTranslation();

  const choix = [
    {
      cle: 'depot_surete',
      route: '/formulaires/inscription/depot-surete',
      icone: <FileTextOutlined style={{ fontSize: 32 }} />,
      accent: 'vert',
    },
    {
      cle: 'privilege_vendeur',
      route: '/formulaires/inscription/privilege-vendeur',
      icone: <ShopOutlined style={{ fontSize: 32 }} />,
      accent: 'rouge',
    },
    {
      cle: 'reserve_propriete',
      route: '/formulaires/inscription/reserve-propriete',
      icone: <SafetyCertificateOutlined style={{ fontSize: 32 }} />,
      accent: 'jaune',
    },
    {
      cle: 'credit_bail',
      route: '/formulaires/inscription/credit-bail',
      icone: <BankOutlined style={{ fontSize: 32 }} />,
      accent: 'vert',
    },
  ];

  return (
    <div>
      <Title level={2}>{t('formulaire.choix_type.titre')}</Title>
      <Paragraph>{t('formulaire.choix_type.introduction')}</Paragraph>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {choix.map((c) => (
          <Col xs={24} sm={12} lg={6} key={c.cle}>
            <Link to={c.route} style={{ display: 'block', height: '100%' }}>
              <Card
                hoverable
                className={`rim-carte-parcours --accent-${c.accent}`}
                style={{ height: '100%' }}
              >
                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                  <div className="rim-carte-parcours__icone">{c.icone}</div>
                  <Text strong style={{ fontSize: 15 }}>
                    {t(`formulaire.choix_type.${c.cle}.titre`)}
                  </Text>
                  <Paragraph
                    type="secondary"
                    style={{ fontSize: 13, marginBottom: 0 }}
                  >
                    {t(`formulaire.choix_type.${c.cle}.description`)}
                  </Paragraph>
                </Space>
              </Card>
            </Link>
          </Col>
        ))}
      </Row>
    </div>
  );
}
