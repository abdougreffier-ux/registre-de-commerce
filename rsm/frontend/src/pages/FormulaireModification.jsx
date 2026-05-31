import React, { useState } from 'react';
import {
  Alert, Card, Col, Form, Input, Modal, Row, Switch, Typography,
} from 'antd';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import ProcedureDepot from '../components/ProcedureDepot';

const { Title, Paragraph } = Typography;

export default function FormulaireModification() {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState(null);

  const parseJsonOuObjetVide = (valeur) => {
    if (!valeur) return {};
    try { return JSON.parse(valeur); } catch { return {}; }
  };

  const soumettre = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      const valeurs = await form.validateFields();
      const payload = {
        inscription: valeurs.inscription,
        objet_modification_fr: valeurs.objet_modification_fr,
        objet_modification_ar: valeurs.objet_modification_ar,
        diff_propose: {
          parties: parseJsonOuObjetVide(valeurs.diff?.parties),
          biens: parseJsonOuObjetVide(valeurs.diff?.biens),
          scalaires: parseJsonOuObjetVide(valeurs.diff?.scalaires),
        },
        accord_createur_confirme: !!valeurs.accord_createur_confirme,
        accord_constituant_confirme: !!valeurs.accord_constituant_confirme,
      };
      const { data } = await client.post('/modifications/', payload);
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
      <Title level={2}>{t('formulaire.modification.titre')}</Title>
      <Paragraph>{t('formulaire.modification.introduction')}</Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      <Form form={form} layout="vertical">
        <Card title={t('formulaire.commun.section.identification')} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="inscription"
                label={t('formulaire.modification.numero_inscription')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Input placeholder="UUID de l'inscription initiale" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="objet_modification_fr"
                label={t('formulaire.modification.objet_fr')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Input.TextArea rows={3} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="objet_modification_ar"
                label={t('formulaire.modification.objet_ar')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Input.TextArea rows={3} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title={t('formulaire.modification.diff_section')} style={{ marginBottom: 16 }}>
          <Form.Item name={['diff', 'parties']} label={t('formulaire.modification.diff_parties')}>
            <Input.TextArea rows={3} placeholder='{"ajouter": [], "modifier": [], "retirer": []}' />
          </Form.Item>
          <Form.Item name={['diff', 'biens']} label={t('formulaire.modification.diff_biens')}>
            <Input.TextArea rows={3} placeholder='{"ajouter": [], "modifier": [], "retirer": []}' />
          </Form.Item>
          <Form.Item name={['diff', 'scalaires']} label={t('formulaire.modification.diff_scalaires')}>
            <Input.TextArea rows={3} placeholder='{"duree_en_jours": null, "monnaie": null, "somme_garantie": null, "adresse_electronique_notifications": null}' />
          </Form.Item>
        </Card>

        <Card title={t('formulaire.commun.section.signatures')} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="accord_createur_confirme"
                label={t('formulaire.modification.accord_createur')}
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="accord_constituant_confirme"
                label={t('formulaire.modification.accord_constituant')}
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <ProcedureDepot
          canalRef={t('procedure.ref.modification')}
          onSoumettre={soumettre}
          enCours={enCours}
        />
      </Form>
    </div>
  );
}
