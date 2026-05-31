/**
 * Composant partagé : saisie d'un bien grevé unique (description
 * monodonnée + champs structurés). Utilisé par les 3 nouveaux
 * formulaires d'inscription (privilege_vendeur, reserve_propriete,
 * credit_bail) qui visent typiquement un bien individualisé.
 *
 * Le formulaire historique depot_surete utilise une liste de biens
 * (Form.List "biens") ; ces nouveaux parcours utilisent un objet
 * unique sous la clé "bien".
 */
import React from 'react';
import { Col, Form, Input, InputNumber, Row, Select } from 'antd';

export function BienUnique({ t, ar, categories, prefixe = 'bien' }) {
  return (
    <Row gutter={12}>
      <Col xs={24} md={12}>
        <Form.Item
          name={[prefixe, 'categorie_cle']}
          label={t('formulaire.inscription.bien.categorie')}
          rules={[{ required: true, message: t('formulaire.commun.requis') }]}
        >
          <Select
            showSearch
            optionFilterProp="label"
            placeholder={t('formulaire.inscription.bien.categorie_placeholder')}
            options={(categories || []).map((c) => ({
              value: c.cle,
              label: ar ? c.libelle_ar : c.libelle_fr,
            }))}
          />
        </Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Form.Item name={[prefixe, 'numero_serie']} label={t('formulaire.inscription.bien.numero_serie_chassis')}>
          <Input />
        </Form.Item>
      </Col>
      <Col xs={24}>
        <Form.Item
          name={[prefixe, 'description']}
          label={t('formulaire.inscription.bien.description_precise')}
          rules={[{ required: true, message: t('formulaire.commun.requis') }]}
        >
          <Input.TextArea rows={2} dir={ar ? 'rtl' : 'ltr'} />
        </Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Form.Item name={[prefixe, 'marque']} label={t('formulaire.inscription.bien.marque')}>
          <Input />
        </Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Form.Item name={[prefixe, 'modele']} label={t('formulaire.inscription.bien.modele')}>
          <Input />
        </Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Form.Item name={[prefixe, 'annee']} label={t('formulaire.inscription.bien.annee')}>
          <InputNumber style={{ width: '100%' }} min={1900} max={new Date().getFullYear() + 1} />
        </Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Form.Item name={[prefixe, 'localisation']} label={t('formulaire.inscription.bien.localisation')}>
          <Input.TextArea rows={2} />
        </Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Form.Item name={[prefixe, 'valeur_estimative']} label={t('formulaire.inscription.bien.valeur_estimative')}>
          <InputNumber
            style={{ width: '100%' }}
            min={0}
            step={1000}
            formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(v) => `${v}`.replace(/\s/g, '')}
          />
        </Form.Item>
      </Col>
    </Row>
  );
}

/**
 * Normalisation d'un bien unique avant envoi.
 * Mappe la description vers description_fr ou description_ar selon
 * la langue active. Conserve les attributs spécifiques tels quels.
 */
export function normaliserBienUnique(b, ar) {
  if (!b) return null;
  const description = b.description || '';
  return {
    categorie_cle: b.categorie_cle,
    description_fr: ar ? '' : description,
    description_ar: ar ? description : '',
    marque: b.marque || '',
    modele: b.modele || '',
    annee: b.annee || null,
    numero_serie: b.numero_serie || '',
    attributs_specifiques: b.attributs_specifiques || {},
    observations: b.observations || '',
  };
}
