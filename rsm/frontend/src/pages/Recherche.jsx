import React, { useState } from 'react';
import { Alert, Button, Card, Form, Input, List, Space, Typography } from 'antd';
import { useTranslation } from 'react-i18next';

import { rechercher } from '../api/client';
import { formatMessageErreur } from '../api/client';
import StatutBadge from '../components/StatutBadge';

const { Title, Paragraph, Text } = Typography;

/**
 * Formulaire de recherche publique — art. 94-97.
 *
 * Le contrôle « au moins deux critères » est dupliqué côté client pour
 * l'ergonomie, mais il reste AUTORITATIF côté serveur (apps.recherche.services).
 * Aucun critère hors liste limitative (art. 96) n'est proposé.
 */
export default function Recherche() {
  const { t } = useTranslation();
  const [resultats, setResultats] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [enCours, setEnCours] = useState(false);
  const [form] = Form.useForm();

  const onLancer = async (valeurs) => {
    setErreur(null);
    const renseignes = Object.values(valeurs).filter((v) => (v || '').toString().trim()).length;
    if (renseignes < 2) {
      setErreur(t('erreur.criteres_insuffisants'));
      return;
    }
    setEnCours(true);
    try {
      const rep = await rechercher(valeurs);
      setResultats(rep);
    } catch (e) {
      setErreur(formatMessageErreur(e, t));
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div>
      <Title level={2}>{t('recherche.titre')}</Title>
      <Paragraph>{t('recherche.introduction')}</Paragraph>

      <Card>
        <Form form={form} layout="vertical" onFinish={onLancer}>
          <Form.Item name="nom_constituant" label={t('recherche.critere.nom')}><Input /></Form.Item>
          <Form.Item name="numero_rc" label={t('recherche.critere.rc')}><Input /></Form.Item>
          <Form.Item name="numero_serie_bien" label={t('recherche.critere.numero_serie')}><Input /></Form.Item>
          <Form.Item name="numero_inscription" label={t('recherche.critere.numero_inscription')}><Input /></Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={enCours}>
              {t('recherche.bouton')}
            </Button>
          </Space>
        </Form>
      </Card>

      {erreur && <Alert type="error" message={erreur} style={{ marginTop: 16 }} />}

      {resultats && (
        <Card style={{ marginTop: 16 }}>
          <Paragraph>
            <Text strong>{t('recherche.instant')} :</Text> {resultats.instant}
          </Paragraph>
          <Paragraph>
            {t('recherche.resultat.nombre', { n: resultats.nombre_resultats })}
          </Paragraph>
          {resultats.nombre_resultats === 0 ? (
            <Text>{t('recherche.resultat.aucun')}</Text>
          ) : (
            <List
              dataSource={resultats.inscriptions || []}
              renderItem={(ins) => (
                <List.Item key={ins.reference_demande}>
                  <List.Item.Meta
                    title={
                      <Space size={8} wrap>
                        <span>{ins.numero_ordre || ins.reference_demande}</span>
                        <StatutBadge statut={ins.statut} />
                      </Space>
                    }
                    description={ins.nature_droit_libelle}
                  />
                </List.Item>
              )}
            />
          )}
        </Card>
      )}
    </div>
  );
}
