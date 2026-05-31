/**
 * Composants réutilisables pour la saisie des parties dans les
 * formulaires d'inscription (toutes variantes : depot_surete,
 * privilege_vendeur, reserve_propriete, credit_bail).
 *
 * Garde-fous (TDR + post-bascule MO) :
 *   - intégrité : aucune logique métier, uniquement présentation ;
 *   - parité FR/AR : tous les libellés via i18n ;
 *   - mono-langue par écran : l'affichage suit la langue active.
 */
import React from 'react';
import {
  Button, Card, Col, DatePicker, Form, Input, Row, Select, Typography,
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

/**
 * Liste dynamique de parties (créancier / constituant / débiteur / agent).
 *
 * @param {object} props
 * @param {function} props.t          fonction i18n
 * @param {boolean}  props.ar         langue active arabe
 * @param {string}   props.nom        nom du Form.List (ex: "creanciers")
 * @param {string}   props.titre      titre de la sous-section
 * @param {string}   [props.description] description optionnelle
 * @param {number}   [props.minimum=0] nombre minimum d'éléments (bouton "retirer" caché en-deçà)
 * @param {string}   [props.libelleAjouter] libellé du bouton d'ajout
 */
export function ListePartiesField({
  t, ar, nom, titre, description, minimum = 0, libelleAjouter,
}) {
  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <Text strong>{titre}</Text>
        {description && (
          <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12.5 }}>
            {description}
          </Paragraph>
        )}
      </div>

      <Form.List name={nom}>
        {(fields, { add, remove }) => (
          <>
            {fields.map((field, idx) => (
              <PartieFieldset
                key={field.key}
                t={t} ar={ar}
                listName={nom}
                name={field.name}
                index={idx}
                onRetirer={fields.length > minimum ? () => remove(field.name) : null}
              />
            ))}
            <Button
              type="dashed"
              onClick={() => add({ type_partie: 'pp' })}
              icon={<PlusOutlined />}
              style={{ width: '100%', marginTop: 8 }}
            >
              {libelleAjouter || t('formulaire.inscription.partie.ajouter')}
            </Button>
          </>
        )}
      </Form.List>
    </div>
  );
}


/**
 * Card de saisie d'une partie unique avec bascule PP/PM.
 */
export function PartieFieldset({ t, ar, listName, name, index, onRetirer }) {
  return (
    <Card
      type="inner"
      size="small"
      title={`${t('formulaire.inscription.partie.numero')} ${index + 1}`}
      extra={onRetirer && (
        <Button
          size="small" danger type="text"
          icon={<DeleteOutlined />}
          onClick={onRetirer}
        >
          {t('formulaire.inscription.partie.retirer')}
        </Button>
      )}
      style={{ marginBottom: 12 }}
    >
      <Form.Item
        name={[name, 'type_partie']}
        label={t('formulaire.inscription.partie.type')}
        rules={[{ required: true, message: t('formulaire.commun.requis') }]}
      >
        <Select
          options={[
            { value: 'pp', label: t('formulaire.inscription.partie.type.pp') },
            { value: 'pm', label: t('formulaire.inscription.partie.type.pm') },
          ]}
        />
      </Form.Item>

      <ChampsConditionnelsPartie t={t} listName={listName} name={name} />
    </Card>
  );
}


/**
 * Affichage conditionnel des champs selon le type de partie.
 */
export function ChampsConditionnelsPartie({ t, listName, name }) {
  return (
    <Form.Item noStyle shouldUpdate={(prev, cur) => {
      const a = prev?.[listName]?.[name]?.type_partie;
      const b = cur?.[listName]?.[name]?.type_partie;
      return a !== b;
    }}>
      {({ getFieldValue }) => {
        const type = getFieldValue([listName, name, 'type_partie']);
        const estPm = type === 'pm';
        return (
          <>
            {!estPm && (
              <Row gutter={12}>
                <Col xs={12} md={8}>
                  <Form.Item name={[name, 'nom']} label={t('formulaire.inscription.partie.nom')}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col xs={12} md={8}>
                  <Form.Item name={[name, 'prenom']} label={t('formulaire.inscription.partie.prenom')}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col xs={12} md={8}>
                  <Form.Item name={[name, 'nni']} label={t('formulaire.inscription.partie.nni')}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col xs={12} md={8}>
                  <Form.Item name={[name, 'date_naissance']} label={t('formulaire.inscription.partie.date_naissance')}>
                    <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
                  </Form.Item>
                </Col>
                <Col xs={12} md={16}>
                  <Form.Item name={[name, 'lieu_naissance']} label={t('formulaire.inscription.partie.lieu_naissance')}>
                    <Input />
                  </Form.Item>
                </Col>
              </Row>
            )}
            {estPm && (
              <Row gutter={12}>
                <Col xs={24} md={12}>
                  <Form.Item name={[name, 'denomination_sociale']} label={t('formulaire.inscription.partie.denomination_sociale')}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col xs={12} md={6}>
                  <Form.Item name={[name, 'numero_rc']} label={t('formulaire.inscription.partie.numero_rc')}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col xs={12} md={6}>
                  <Form.Item name={[name, 'representant_legal']} label={t('formulaire.inscription.partie.representant_legal')}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col xs={24}>
                  <Form.Item name={[name, 'siege_social']} label={t('formulaire.inscription.partie.siege_social')}>
                    <Input />
                  </Form.Item>
                </Col>
              </Row>
            )}
            <Row gutter={12}>
              <Col xs={24} md={12}>
                <Form.Item name={[name, 'adresse']} label={t('formulaire.inscription.partie.adresse')}>
                  <Input.TextArea rows={2} />
                </Form.Item>
              </Col>
              <Col xs={12} md={6}>
                <Form.Item name={[name, 'telephone']} label={t('formulaire.inscription.partie.telephone')}>
                  <Input />
                </Form.Item>
              </Col>
              <Col xs={12} md={6}>
                <Form.Item name={[name, 'adresse_electronique']} label={t('formulaire.inscription.partie.email')}>
                  <Input type="email" />
                </Form.Item>
              </Col>
            </Row>
          </>
        );
      }}
    </Form.Item>
  );
}


/**
 * Normalisation d'une partie avant envoi (dates dayjs → ISO, blancs).
 */
export function normaliserPartie(p) {
  if (!p) return p;
  const out = { ...p };
  if (out.date_naissance && out.date_naissance.format) {
    out.date_naissance = out.date_naissance.format('YYYY-MM-DD');
  }
  if (out.type_partie === 'pp') {
    out.denomination_sociale = '';
    out.numero_rc = '';
    out.siege_social = '';
    out.representant_legal = '';
  } else if (out.type_partie === 'pm') {
    out.nom = '';
    out.prenom = '';
    out.date_naissance = null;
    out.lieu_naissance = '';
    out.nni = '';
  }
  return out;
}
