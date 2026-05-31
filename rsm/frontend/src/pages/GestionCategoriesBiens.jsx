import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Button, Card, Col, Drawer, Empty, Form, Input, Modal, Row,
  Select, Space, Spin, Switch, Table, Tag, Tooltip, Typography,
} from 'antd';
import {
  PlusOutlined, EditOutlined, ReloadOutlined, LockOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import { useAuth, aUnRole } from '../contexts/AuthContext';

const { Title, Paragraph, Text } = Typography;

const TYPES_CHAMPS = [
  { value: 'texte', label_fr: 'Texte court', label_ar: 'نص قصير' },
  { value: 'texte_long', label_fr: 'Texte long', label_ar: 'نص طويل' },
  { value: 'nombre', label_fr: 'Nombre', label_ar: 'عدد' },
  { value: 'montant', label_fr: 'Montant', label_ar: 'مبلغ' },
  { value: 'date', label_fr: 'Date', label_ar: 'تاريخ' },
  { value: 'booleen', label_fr: 'Booléen', label_ar: 'منطقي' },
];

/**
 * Page admin — gestion des catégories de biens.
 *
 * Réservée aux rôles ``admin_fonctionnel`` et ``autorite_validation``.
 * Permet de :
 * - lister les catégories actives + versions historiques ;
 * - publier une nouvelle version (= incrémente la version) ;
 * - modifier une version NON UTILISÉE (sinon 409 + propose la publication).
 */
export default function GestionCategoriesBiens() {
  const { t, i18n } = useTranslation();
  const ar = (i18n.language || 'fr').toLowerCase().startsWith('ar');
  const auth = useAuth();
  const peut = aUnRole(auth, ['autorite_validation', 'admin_fonctionnel']);

  const [items, setItems] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);
  const [drawerOuvert, setDrawerOuvert] = useState(false);
  const [drawerMode, setDrawerMode] = useState('publier'); // 'publier' | 'modifier'
  const [drawerCategorie, setDrawerCategorie] = useState(null);
  const [form] = Form.useForm();

  const charger = useCallback(async () => {
    setChargement(true); setErreur(null);
    try {
      const { data } = await client.get('/categories-biens/?actif=1');
      setItems(data.results || data);
    } catch (e) {
      setErreur(formatMessageErreur(e, t));
    } finally {
      setChargement(false);
    }
  }, [t]);

  useEffect(() => { if (peut) charger(); else setChargement(false); }, [charger, peut]);

  const ouvrirPublier = () => {
    setDrawerMode('publier');
    setDrawerCategorie(null);
    form.resetFields();
    form.setFieldsValue({ schema_champs: [], affichage_observations: true });
    setDrawerOuvert(true);
  };

  const ouvrirModifier = (cat) => {
    setDrawerMode('modifier');
    setDrawerCategorie(cat);
    form.resetFields();
    form.setFieldsValue({
      cle: cat.cle,
      libelle_fr: cat.libelle_fr, libelle_ar: cat.libelle_ar,
      description_fr: cat.description_fr, description_ar: cat.description_ar,
      affichage_observations: cat.affichage_observations,
      schema_champs: cat.schema_champs || [],
    });
    setDrawerOuvert(true);
  };

  const soumettre = async () => {
    try {
      const valeurs = await form.validateFields();
      if (drawerMode === 'publier') {
        await client.post('/categories-biens/publier/', valeurs);
        Modal.success({ title: t('cat_admin.succes.publication'), okText: t('soumission.fermer') });
      } else {
        await client.patch(`/categories-biens/${drawerCategorie.id}/modifier/`, valeurs);
        Modal.success({ title: t('cat_admin.succes.modification'), okText: t('soumission.fermer') });
      }
      setDrawerOuvert(false);
      await charger();
    } catch (e) {
      if (e?.errorFields) return; // erreur AntD validation
      Modal.error({
        title: t('cat_admin.echec.titre'),
        content: formatMessageErreur(e, t),
        okText: t('soumission.fermer'),
      });
    }
  };

  if (!peut) {
    return (
      <div>
        <Title level={2}>{t('cat_admin.titre')}</Title>
        <Alert
          type="warning" showIcon
          message={t('greffe.acces_refuse.titre')}
          description={t('cat_admin.acces_refuse')}
        />
      </div>
    );
  }

  if (chargement) return <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>;

  return (
    <div>
      <Title level={2}>{t('cat_admin.titre')}</Title>
      <Paragraph>{t('cat_admin.introduction')}</Paragraph>

      <Alert
        type="info" showIcon
        style={{ marginBottom: 16 }}
        message={t('cat_admin.note.versionnage_titre')}
        description={t('cat_admin.note.versionnage')}
      />

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={ouvrirPublier}>
          {t('cat_admin.bouton.publier')}
        </Button>
        <Button icon={<ReloadOutlined />} onClick={charger}>
          {t('cat_admin.bouton.recharger')}
        </Button>
      </Space>

      {items.length === 0 ? (
        <Empty description={t('cat_admin.vide')} />
      ) : (
        <Table
          dataSource={items}
          rowKey="id"
          columns={[
            { title: t('cat_admin.col.cle'), dataIndex: 'cle' },
            { title: t('cat_admin.col.libelle'),
              render: (_, c) => ar ? c.libelle_ar : c.libelle_fr },
            { title: t('cat_admin.col.version'),
              dataIndex: 'version', render: (v) => <Tag color="green">v{v}</Tag> },
            { title: t('cat_admin.col.observations'),
              dataIndex: 'affichage_observations',
              render: (v) => v ? <Tag>OUI</Tag> : <Tag>NON</Tag> },
            { title: t('cat_admin.col.champs'),
              render: (_, c) => c.schema_champs?.length || 0 },
            { title: t('cat_admin.col.utilisation'),
              dataIndex: 'est_utilisee',
              render: (v) => v
                ? <Tag color="orange" icon={<LockOutlined />}>{t('cat_admin.utilisee')}</Tag>
                : <Tag color="blue">{t('cat_admin.non_utilisee')}</Tag>,
            },
            {
              title: '', key: 'actions',
              render: (_, c) => (
                <Tooltip
                  title={c.est_utilisee ? t('cat_admin.tooltip.publier_nouvelle') : ''}
                >
                  <Button
                    size="small"
                    icon={<EditOutlined />}
                    onClick={() => c.est_utilisee ? ouvrirPublier() : ouvrirModifier(c)}
                  >
                    {c.est_utilisee
                      ? t('cat_admin.bouton.publier_nouvelle')
                      : t('cat_admin.bouton.modifier')}
                  </Button>
                </Tooltip>
              ),
            },
          ]}
        />
      )}

      <Drawer
        open={drawerOuvert}
        onClose={() => setDrawerOuvert(false)}
        title={drawerMode === 'publier'
          ? t('cat_admin.drawer.titre_publier')
          : t('cat_admin.drawer.titre_modifier')}
        width={720}
        extra={(
          <Space>
            <Button onClick={() => setDrawerOuvert(false)}>
              {t('soumission.fermer')}
            </Button>
            <Button type="primary" onClick={soumettre}>
              {t('cat_admin.drawer.valider')}
            </Button>
          </Space>
        )}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                name="cle"
                label={t('cat_admin.champ.cle')}
                tooltip={t('cat_admin.champ.cle_aide')}
                rules={[
                  { required: true, message: t('formulaire.commun.requis') },
                  { pattern: /^[a-z0-9_]+$/, message: t('cat_admin.champ.cle_format') },
                ]}
              >
                <Input disabled={drawerMode === 'modifier'} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="affichage_observations"
                         label={t('cat_admin.champ.observations')}
                         valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="libelle_fr" label={t('cat_admin.champ.libelle_fr')}
                         rules={[{ required: true, message: t('formulaire.commun.requis') }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="libelle_ar" label={t('cat_admin.champ.libelle_ar')}
                         rules={[{ required: true, message: t('formulaire.commun.requis') }]}>
                <Input dir="rtl" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="description_fr" label={t('cat_admin.champ.description_fr')}>
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="description_ar" label={t('cat_admin.champ.description_ar')}>
                <Input.TextArea rows={2} dir="rtl" />
              </Form.Item>
            </Col>
          </Row>

          <Card size="small" title={t('cat_admin.champs.titre')} style={{ marginTop: 8 }}>
            <Form.List name="schema_champs">
              {(fields, { add, remove }) => (
                <>
                  {fields.map((field, idx) => (
                    <Card
                      key={field.key} size="small" style={{ marginBottom: 8 }}
                      title={`${t('cat_admin.champs.entree')} ${idx + 1}`}
                      extra={<Button danger size="small" onClick={() => remove(field.name)}>
                        {t('cat_admin.champs.supprimer')}
                      </Button>}
                    >
                      <Row gutter={8}>
                        <Col xs={24} md={8}>
                          <Form.Item {...field} name={[field.name, 'cle']}
                                     label={t('cat_admin.champs.cle')}
                                     rules={[
                                       { required: true, message: t('formulaire.commun.requis') },
                                       { pattern: /^[a-z0-9_]+$/, message: t('cat_admin.champ.cle_format') },
                                     ]}>
                            <Input />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={8}>
                          <Form.Item {...field} name={[field.name, 'type']}
                                     label={t('cat_admin.champs.type')}
                                     rules={[{ required: true, message: t('formulaire.commun.requis') }]}>
                            <Select options={TYPES_CHAMPS.map((t) => ({
                              value: t.value, label: ar ? t.label_ar : t.label_fr,
                            }))} />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={8}>
                          <Form.Item {...field} name={[field.name, 'obligatoire']}
                                     label={t('cat_admin.champs.obligatoire')}
                                     valuePropName="checked"
                                     initialValue={false}>
                            <Switch />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item {...field} name={[field.name, 'libelle_fr']}
                                     label={t('cat_admin.champs.libelle_fr')}
                                     rules={[{ required: true, message: t('formulaire.commun.requis') }]}>
                            <Input />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item {...field} name={[field.name, 'libelle_ar']}
                                     label={t('cat_admin.champs.libelle_ar')}
                                     rules={[{ required: true, message: t('formulaire.commun.requis') }]}>
                            <Input dir="rtl" />
                          </Form.Item>
                        </Col>
                      </Row>
                    </Card>
                  ))}
                  <Button type="dashed" block icon={<PlusOutlined />}
                          onClick={() => add({ obligatoire: false, type: 'texte' })}>
                    {t('cat_admin.champs.ajouter')}
                  </Button>
                </>
              )}
            </Form.List>
          </Card>

          {drawerMode === 'modifier' && drawerCategorie?.est_utilisee && (
            <Alert
              type="warning" showIcon
              style={{ marginTop: 16 }}
              message={t('cat_admin.alerte.deja_utilisee_titre')}
              description={t('cat_admin.alerte.deja_utilisee')}
            />
          )}
        </Form>
      </Drawer>
    </div>
  );
}
