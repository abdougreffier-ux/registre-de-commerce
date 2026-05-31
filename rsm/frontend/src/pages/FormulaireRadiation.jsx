import React, { useState } from 'react';
import {
  Alert, Card, Col, Form, Input, Modal, Radio, Row, Space, Typography,
} from 'antd';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import ProcedureDepot from '../components/ProcedureDepot';

const { Title, Paragraph } = Typography;

export default function FormulaireRadiation() {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState(null);

  const soumettre = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      const valeurs = await form.validateFields();
      const { data } = await client.post('/radiations/', valeurs);
      Modal.success({
        title: t('soumission.succes.titre'),
        content: `${t('soumission.succes.contenu')} (# ${data.id || ''})`,
        okText: t('soumission.fermer'),
      });
      form.resetFields();
    } catch (e) {
      if (e?.errorFields) return;
      setErreur(formatMessageErreur(e, t));
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div>
      <Title level={2}>{t('formulaire.radiation.titre')}</Title>
      <Paragraph>{t('formulaire.radiation.introduction')}</Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      <Form form={form} layout="vertical">
        <Card title={t('formulaire.commun.section.identification')} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="inscription"
                label={t('formulaire.radiation.numero_inscription')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Input placeholder="UUID de l'inscription initiale" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item
                name="fondement"
                label={t('formulaire.radiation.fondement')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Radio.Group>
                  <Space direction="vertical">
                    <Radio value="consentement">{t('formulaire.radiation.fondement.consentement')}</Radio>
                    <Radio value="jugement">{t('formulaire.radiation.fondement.jugement')}</Radio>
                    <Radio value="requerant_original">{t('formulaire.radiation.fondement.requerant_original')}</Radio>
                  </Space>
                </Radio.Group>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title={t('formulaire.radiation.constituant.section')} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="nom_constituant" label={t('formulaire.radiation.constituant.nom')}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="prenom_constituant" label={t('formulaire.radiation.constituant.prenom')}><Input /></Form.Item></Col>
            <Col span={24}><Form.Item name="denomination_constituant" label={t('formulaire.radiation.constituant.denomination')}><Input /></Form.Item></Col>
            <Col span={24}><Form.Item name="adresse_constituant" label={t('formulaire.radiation.constituant.adresse')}><Input.TextArea rows={2} /></Form.Item></Col>
            <Col span={12}><Form.Item name="numero_rc_constituant" label={t('formulaire.radiation.constituant.numero_rc')}><Input /></Form.Item></Col>
          </Row>
        </Card>

        <ProcedureDepot
          canalRef={t('procedure.ref.radiation')}
          onSoumettre={soumettre}
          enCours={enCours}
        />
      </Form>
    </div>
  );
}
