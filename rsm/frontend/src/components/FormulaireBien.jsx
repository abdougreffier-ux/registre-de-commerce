import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert, Card, Col, DatePicker, Form, Input, InputNumber, Row,
  Select, Spin, Switch, Typography,
} from 'antd';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';

const { Text, Paragraph } = Typography;

/**
 * Formulaire dynamique de saisie d'un bien grevé.
 *
 * - Charge la liste des catégories actives via /api/v1/categories-biens/.
 * - Au choix d'une catégorie, n'affiche QUE les champs du schéma de la
 *   catégorie sélectionnée + les champs communs (description, valeur,
 *   quantité, localisation, état) + le champ Observations si la
 *   catégorie le requiert.
 * - Utilise les libellés FR ou AR selon ``i18n.language``.
 *
 * Les champs sont préfixés par leur clé technique afin que le payload
 * envoyé au backend respecte exactement le schéma de la catégorie+version.
 *
 * Le composant ne porte aucune règle métier : la validation autoritative
 * reste serveur (``apps.biens.services.valider_attributs``).
 */
export default function FormulaireBien({
  prefixe = ['biens', 0],
  titre,
}) {
  const { t, i18n } = useTranslation();
  const ar = (i18n.language || 'fr').toLowerCase().startsWith('ar');
  const [categories, setCategories] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);
  const form = Form.useFormInstance();

  useEffect(() => {
    (async () => {
      try {
        const { data } = await client.get('/categories-biens/?actif=1');
        setCategories(data.results || data);
      } catch (e) {
        setErreur(formatMessageErreur(e, t));
      } finally {
        setChargement(false);
      }
    })();
  }, [t]);

  const categorieIdSelectionnee = Form.useWatch([...prefixe, 'categorie_id'], form);
  const categorieSelectionnee = useMemo(
    () => categories.find((c) => c.id === categorieIdSelectionnee) || null,
    [categories, categorieIdSelectionnee],
  );

  const renduChamp = (descripteur) => {
    const cle = descripteur.cle;
    const lib = ar ? descripteur.libelle_ar : descripteur.libelle_fr;
    const obligatoire = !!descripteur.obligatoire;
    const rules = obligatoire ? [{ required: true, message: t('formulaire.commun.requis') }] : [];
    const path = [...prefixe, 'attributs_specifiques', cle];
    switch (descripteur.type) {
      case 'texte':
        return (
          <Form.Item key={cle} name={path} label={lib} rules={rules}>
            <Input />
          </Form.Item>
        );
      case 'texte_long':
        return (
          <Form.Item key={cle} name={path} label={lib} rules={rules}>
            <Input.TextArea rows={3} />
          </Form.Item>
        );
      case 'nombre':
        return (
          <Form.Item key={cle} name={path} label={lib} rules={rules}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        );
      case 'montant':
        return (
          <Form.Item key={cle} name={path} label={lib} rules={rules}>
            <InputNumber style={{ width: '100%' }} min={0} step={1000} />
          </Form.Item>
        );
      case 'date':
        return (
          <Form.Item key={cle} name={path} label={lib} rules={rules}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        );
      case 'booleen':
        return (
          <Form.Item key={cle} name={path} label={lib} valuePropName="checked">
            <Switch />
          </Form.Item>
        );
      default:
        return null;
    }
  };

  if (chargement) {
    return <Card><Spin /></Card>;
  }

  return (
    <Card title={titre || t('bien.section.titre')}>
      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item
            name={[...prefixe, 'categorie_id']}
            label={t('bien.champ.categorie')}
            tooltip={t('bien.champ.categorie_aide')}
            rules={[{ required: true, message: t('formulaire.commun.requis') }]}
          >
            <Select
              showSearch
              placeholder={t('bien.champ.categorie_placeholder')}
              optionFilterProp="label"
              options={categories.map((c) => ({
                value: c.id,
                label: `${ar ? c.libelle_ar : c.libelle_fr} (v${c.version})`,
              }))}
            />
          </Form.Item>
        </Col>
        {categorieSelectionnee && (
          <Col xs={24} md={12}>
            <Alert
              type="info"
              showIcon
              message={t('bien.version_active', { version: categorieSelectionnee.version })}
              description={ar ? categorieSelectionnee.description_ar : categorieSelectionnee.description_fr}
            />
          </Col>
        )}
      </Row>

      {categorieSelectionnee && (
        <>
          <Paragraph style={{ marginTop: 8 }}>
            <Text type="secondary">{t('bien.section.commune')}</Text>
          </Paragraph>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                name={[...prefixe, 'description_fr']}
                label={t('bien.commune.description_fr')}
              >
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name={[...prefixe, 'description_ar']}
                label={t('bien.commune.description_ar')}
              >
                <Input.TextArea rows={2} dir="rtl" />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item
                name={[...prefixe, 'numero_serie']}
                label={t('bien.commune.numero_serie')}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name={[...prefixe, 'marque']} label={t('bien.commune.marque')}>
                <Input />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name={[...prefixe, 'modele']} label={t('bien.commune.modele')}>
                <Input />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name={[...prefixe, 'annee']} label={t('bien.commune.annee')}>
                <InputNumber style={{ width: '100%' }} min={1900} max={new Date().getFullYear() + 1} />
              </Form.Item>
            </Col>
          </Row>

          <Paragraph style={{ marginTop: 8 }}>
            <Text type="secondary">{t('bien.section.specifiques')}</Text>
          </Paragraph>
          <Row gutter={16}>
            {categorieSelectionnee.schema_champs.map((d) => (
              <Col xs={24} md={12} key={d.cle}>{renduChamp(d)}</Col>
            ))}
          </Row>

          {categorieSelectionnee.affichage_observations && (
            <Form.Item
              name={[...prefixe, 'observations']}
              label={t('bien.commune.observations')}
            >
              <Input.TextArea rows={2} />
            </Form.Item>
          )}
        </>
      )}
    </Card>
  );
}
