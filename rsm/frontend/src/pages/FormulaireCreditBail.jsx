import React, { useEffect, useState } from 'react';
import {
  Alert, Card, Checkbox, Col, DatePicker, Divider, Form, Input, InputNumber,
  Row, Select, Space, Spin, Typography,
} from 'antd';
import {
  FileTextOutlined, UserOutlined, DollarOutlined, AppstoreOutlined,
  PaperClipOutlined, BankOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import ProcedureDepot from '../components/ProcedureDepot';
import { ListePartiesField, normaliserPartie } from '../components/formulaires/PartiesShared';
import { BienUnique, normaliserBienUnique } from '../components/formulaires/BienShared';
import PiecesJointesField from '../components/formulaires/PiecesJointesShared';
import { soumettreInscription } from '../components/formulaires/soumettreInscription';
import { reglesEmail } from '../lib/validation';
import { CANAL_SAISIE_DEFAUT, NATURE_DROIT_PAR_TYPE_SURETE } from '../lib/typeSurete';

const { Title, Paragraph } = Typography;

/**
 * Inscription du contrat de crédit-bail.
 *
 * Mapping métier ↔ entités RSM :
 *   - Crédit-bailleur (propriétaire) → créancier
 *   - Crédit-preneur (utilisateur)  → constituant + débiteur
 *   - Bien                          → unique
 */
export default function FormulaireCreditBail() {
  const { t, i18n } = useTranslation();
  const ar = (i18n.language || 'fr').toLowerCase().startsWith('ar');
  const [form] = Form.useForm();
  const [erreur, setErreur] = useState(null);
  const [enCours, setEnCours] = useState(false);
  const [categories, setCategories] = useState([]);
  const [chargementReferentiels, setChargementReferentiels] = useState(true);
  const [piecesJointes, setPiecesJointes] = useState([]);

  useEffect(() => {
    let actif = true;
    (async () => {
      try {
        const cats = await client.get('/categories-biens/?actif=1');
        if (!actif) return;
        setCategories(cats.data.results || cats.data || []);
      } catch (e) {
        if (actif) setErreur(formatMessageErreur(e, t));
      } finally {
        if (actif) setChargementReferentiels(false);
      }
    })();
    return () => { actif = false; };
  }, [t]);

  const soumettre = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      const v = await form.validateFields();
      const payload = {
        type_surete: 'credit_bail',
        // Canal implicite (registre 100% numérisé) et nature déduite
        // du type_surete (directive MO 2026-05-31).
        canal_saisie: CANAL_SAISIE_DEFAUT,
        nature_droit: NATURE_DROIT_PAR_TYPE_SURETE.credit_bail,
        somme_garantie: v.montant_total_loyers,
        monnaie: v.monnaie,
        duree_en_jours: v.duree_en_jours,
        adresse_electronique_notifications: v.adresse_electronique_notifications || '',
        debiteur_est_constituant: true,
        constituants: (v.constituants || []).map(normaliserPartie),
        creanciers: (v.creanciers || []).map(normaliserPartie),
        debiteurs: [],
        biens: v.bien ? [normaliserBienUnique(v.bien, ar)] : [],
        donnees_specifiques: {
          date_demande: dateOuNull(v.date_demande),
          date_contrat: dateOuNull(v.date_contrat),
          reference_contrat: v.reference_contrat || '',
          duree_contrat: v.duree_contrat || '',
          date_debut: dateOuNull(v.date_debut),
          date_fin: dateOuNull(v.date_fin),
          option_achat: !!v.option_achat,
          prix_levee_option: v.prix_levee_option || null,
          valeur_bien_finance: v.valeur_bien_finance || null,
          montant_total_loyers: v.montant_total_loyers || null,
          periodicite_loyers: v.periodicite_loyers || '',
          montant_loyer: v.montant_loyer || null,
          depot_garantie: v.depot_garantie || null,
          interets_frais_penalites: v.interets_frais_penalites || '',
          echeancier_joint: !!v.echeancier_joint,
          bien_remis_preneur: !!v.bien_remis_preneur,
          date_remise_bien: dateOuNull(v.date_remise_bien),
          conditions_restitution_defaut: v.conditions_restitution_defaut || '',
          date_naissance_creance: dateOuNull(v.date_naissance_creance),
          date_echeance: dateOuNull(v.date_echeance),
          declaration_exactitude: !!v.declaration_exactitude,
        },
      };

      await soumettreInscription({
        client, t, payload,
        fichiersPj: piecesJointes,
        formatErreur: (e) => formatMessageErreur(e, t),
        resetForm: () => form.resetFields(),
        resetFichiers: setPiecesJointes,
      });
    } catch (e) {
      if (e?.errorFields) return;
      setErreur(formatMessageErreur(e, t));
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div>
      <Title level={2}>{t('formulaire.credit_bail.titre')}</Title>
      <Paragraph>{t('formulaire.credit_bail.introduction')}</Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}
      {chargementReferentiels && (
        <Card style={{ marginBottom: 16 }}><Spin /> {t('formulaire.commun.chargement_referentiels')}</Card>
      )}

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          monnaie: 'MRU',
          constituants: [{ type_partie: 'pp' }],
          creanciers: [{ type_partie: 'pm' }],
          option_achat: false,
          echeancier_joint: false,
          bien_remis_preneur: false,
          declaration_exactitude: false,
        }}
      >
        {/* Identification */}
        <Card title={<Space><FileTextOutlined />{t('formulaire.commun.section.identification')}</Space>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item name="date_demande" label={t('formulaire.commun.date_demande')} rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="adresse_electronique_notifications"
                label={t('formulaire.inscription.email')}
                rules={reglesEmail(t)}
              >
                <Input placeholder="exemple@rsm.mr" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Contrat */}
        <Card title={<Space><BankOutlined />{t('formulaire.credit_bail.section.contrat')}</Space>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item name="date_contrat" label={t('formulaire.credit_bail.date_contrat')} rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item name="reference_contrat" label={t('formulaire.credit_bail.reference_contrat')} rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item name="duree_contrat" label={t('formulaire.credit_bail.duree_contrat')}>
                <Input placeholder={t('formulaire.credit_bail.duree_contrat_placeholder')} />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name="date_debut" label={t('formulaire.credit_bail.date_debut')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name="date_fin" label={t('formulaire.credit_bail.date_fin')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name="option_achat" valuePropName="checked">
                <Checkbox>{t('formulaire.credit_bail.option_achat')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name="prix_levee_option" label={t('formulaire.credit_bail.prix_levee_option')}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name="bien_remis_preneur" valuePropName="checked">
                <Checkbox>{t('formulaire.credit_bail.bien_remis_preneur')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name="date_remise_bien" label={t('formulaire.credit_bail.date_remise_bien')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item name="echeancier_joint" valuePropName="checked">
                <Checkbox>{t('formulaire.credit_bail.echeancier_joint')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="conditions_restitution_defaut" label={t('formulaire.credit_bail.conditions_restitution_defaut')}>
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Conditions financières */}
        <Card title={<Space><DollarOutlined />{t('formulaire.inscription.section.conditions_financieres')}</Space>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col xs={12} md={8}>
              <Form.Item name="valeur_bien_finance" label={t('formulaire.credit_bail.valeur_bien_finance')} rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={12} md={8}>
              <Form.Item name="montant_total_loyers" label={t('formulaire.credit_bail.montant_total_loyers')} rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={12} md={8}>
              <Form.Item name="periodicite_loyers" label={t('formulaire.credit_bail.periodicite_loyers')}>
                <Select allowClear placeholder={t('formulaire.credit_bail.periodicite_placeholder')} options={[
                  { value: 'mensuelle', label: t('formulaire.credit_bail.periodicite.mensuelle') },
                  { value: 'trimestrielle', label: t('formulaire.credit_bail.periodicite.trimestrielle') },
                  { value: 'semestrielle', label: t('formulaire.credit_bail.periodicite.semestrielle') },
                  { value: 'annuelle', label: t('formulaire.credit_bail.periodicite.annuelle') },
                ]} />
              </Form.Item>
            </Col>
            <Col xs={12} md={8}>
              <Form.Item name="montant_loyer" label={t('formulaire.credit_bail.montant_loyer')}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={12} md={8}>
              <Form.Item name="depot_garantie" label={t('formulaire.credit_bail.depot_garantie')}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={12} md={8}>
              <Form.Item name="monnaie" label={t('formulaire.inscription.monnaie')}>
                <Select options={[{ value: 'MRU', label: 'MRU' }, { value: 'EUR', label: 'EUR' }, { value: 'USD', label: 'USD' }]} />
              </Form.Item>
            </Col>
            <Col xs={12} md={8}>
              <Form.Item name="duree_en_jours" label={t('formulaire.inscription.duree')} rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
            <Col xs={12} md={8}>
              <Form.Item name="date_naissance_creance" label={t('formulaire.commun.date_naissance_creance')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={12} md={8}>
              <Form.Item name="date_echeance" label={t('formulaire.commun.date_echeance')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="interets_frais_penalites" label={t('formulaire.credit_bail.interets_frais_penalites')}>
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Parties */}
        <Card title={<Space><UserOutlined />{t('formulaire.inscription.section.parties')}</Space>} style={{ marginBottom: 16 }}>
          <ListePartiesField
            t={t} ar={ar} nom="creanciers"
            titre={t('formulaire.credit_bail.partie.bailleur.titre')}
            description={t('formulaire.credit_bail.partie.bailleur.description')}
            minimum={1}
            libelleAjouter={t('formulaire.credit_bail.partie.bailleur.ajouter')}
          />
          <Divider />
          <ListePartiesField
            t={t} ar={ar} nom="constituants"
            titre={t('formulaire.credit_bail.partie.preneur.titre')}
            description={t('formulaire.credit_bail.partie.preneur.description')}
            minimum={1}
            libelleAjouter={t('formulaire.credit_bail.partie.preneur.ajouter')}
          />
        </Card>

        {/* Bien */}
        <Card title={<Space><AppstoreOutlined />{t('formulaire.inscription.section.bien')}</Space>} style={{ marginBottom: 16 }}>
          <BienUnique t={t} ar={ar} categories={categories} prefixe="bien" />
        </Card>

        {/* PJ */}
        <Card title={<Space><PaperClipOutlined />{t('formulaire.inscription.section.pieces_jointes')}</Space>} style={{ marginBottom: 16 }}>
          <PiecesJointesField
            t={t} fichiers={piecesJointes} setFichiers={setPiecesJointes}
            aide={t('formulaire.credit_bail.pj.aide')}
          />
        </Card>

        {/* Déclaration */}
        <Card style={{ marginBottom: 16 }}>
          <Form.Item
            name="declaration_exactitude" valuePropName="checked"
            rules={[{ validator: (_, v) => v ? Promise.resolve() : Promise.reject(new Error(t('formulaire.commun.declaration_exactitude_requise'))) }]}
          >
            <Checkbox>{t('formulaire.commun.declaration_exactitude')}</Checkbox>
          </Form.Item>
        </Card>

        <ProcedureDepot
          canalRef={t('procedure.ref.inscription')}
          onSoumettre={soumettre}
          enCours={enCours}
        />
      </Form>
    </div>
  );
}

function dateOuNull(d) {
  if (!d) return null;
  if (typeof d === 'string') return d;
  if (d.format) return d.format('YYYY-MM-DD');
  return null;
}
