import React, { useState } from 'react';
import {
  Alert, Card, Checkbox, Col, Form, Input, Modal, Row, Typography,
} from 'antd';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import ProcedureDepot from '../components/ProcedureDepot';
import HorodatageDemandeField from '../components/formulaires/HorodatageDemandeField';

const { Title, Paragraph } = Typography;

export default function FormulaireRenouvellement() {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState(null);

  const soumettre = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      const valeurs = await form.validateFields();
      const { data } = await client.post('/renouvellements/', {
        inscription: valeurs.inscription,
      });
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
      <Title level={2}>{t('formulaire.renouvellement.titre')}</Title>
      <Paragraph>{t('formulaire.renouvellement.introduction')}</Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      <Form form={form} layout="vertical">
        <Card title={t('formulaire.commun.section.identification')} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <HorodatageDemandeField t={t} />
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="inscription"
                label={t('formulaire.renouvellement.numero_inscription')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Input placeholder="UUID de l'inscription initiale" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card style={{ marginBottom: 16 }}>
          <Form.Item
            name="confirmation_delai"
            valuePropName="checked"
            rules={[{ required: true, message: t('formulaire.commun.requis') }]}
          >
            <Checkbox>{t('formulaire.renouvellement.confirmation')}</Checkbox>
          </Form.Item>
        </Card>

        <ProcedureDepot
          canalRef={t('procedure.ref.renouvellement')}
          onSoumettre={soumettre}
          enCours={enCours}
        />
      </Form>
    </div>
  );
}
