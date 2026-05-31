import React, { useEffect, useState } from 'react';
import {
  Alert, Card, Checkbox, Col, DatePicker, Divider, Form, Input, InputNumber,
  Row, Select, Space, Spin, Typography,
} from 'antd';
import {
  FileTextOutlined, UserOutlined, DollarOutlined, AppstoreOutlined,
  PaperClipOutlined, SafetyCertificateOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import ProcedureDepot from '../components/ProcedureDepot';
import { ListePartiesField, normaliserPartie } from '../components/formulaires/PartiesShared';
import { BienUnique, normaliserBienUnique } from '../components/formulaires/BienShared';
import PiecesJointesField from '../components/formulaires/PiecesJointesShared';
import { soumettreInscription } from '../components/formulaires/soumettreInscription';
import HorodatageDemandeField from '../components/formulaires/HorodatageDemandeField';
import { reglesEmail } from '../lib/validation';
import { CANAL_SAISIE_DEFAUT, NATURE_DROIT_PAR_TYPE_SURETE } from '../lib/typeSurete';

const { Title, Paragraph } = Typography;

/**
 * Inscription de la vente avec réserve du droit de propriété.
 *
 * La clause de réserve suspend le transfert de propriété jusqu'au
 * paiement complet du prix par l'acquéreur.
 *
 * Mapping métier ↔ entités RSM :
 *   - Vendeur   → créancier
 *   - Acquéreur → constituant + débiteur
 *   - Bien      → unique
 */
export default function FormulaireReserveProprete() {
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
        // Seul le référentiel des catégories de biens est nécessaire pour
        // ce parcours : la nature du droit est dérivée du type_surete et
        // le canal de saisie est implicite (registre 100% numérisé).
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
        type_surete: 'reserve_propriete',
        // Canal implicite (registre 100% numérisé) et nature déduite
        // du type de sûreté (directive MO 2026-05-31).
        canal_saisie: CANAL_SAISIE_DEFAUT,
        nature_droit: NATURE_DROIT_PAR_TYPE_SURETE.reserve_propriete,
        somme_garantie: v.montant_creance,
        monnaie: v.monnaie,
        duree_en_jours: v.duree_en_jours,
        adresse_electronique_notifications: v.adresse_electronique_notifications || '',
        debiteur_est_constituant: true,
        constituants: (v.constituants || []).map(normaliserPartie),
        creanciers: (v.creanciers || []).map(normaliserPartie),
        debiteurs: [],
        biens: v.bien ? [normaliserBienUnique(v.bien, ar)] : [],
        donnees_specifiques: {
          // ``date_demande`` n'est plus collecté : l'horodatage autoritatif
          // est ``Inscription.instant_arrivee`` (timezone.now() côté backend).
          date_contrat: dateOuNull(v.date_contrat),
          reference_contrat: v.reference_contrat || '',
          prix_total: v.prix_total || null,
          montant_paye: v.montant_paye || null,
          solde_restant: v.solde_restant || null,
          date_limite_paiement: dateOuNull(v.date_limite_paiement),
          modalites_paiement: v.modalites_paiement || '',
          clause_reserve_propriete: !!v.clause_reserve_propriete,
          texte_clause_reserve: v.texte_clause_reserve || '',
          date_acceptation_clause: dateOuNull(v.date_acceptation_clause),
          bien_remis_acquereur: !!v.bien_remis_acquereur,
          acquereur_en_possession: !!v.acquereur_en_possession,
          propriete_conservee_par_vendeur: !!v.propriete_conservee_par_vendeur,
          localisation_actuelle_bien: v.localisation_actuelle_bien || '',
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
      <Title level={2}>{t('formulaire.reserve_propriete.titre')}</Title>
      <Paragraph>{t('formulaire.reserve_propriete.introduction')}</Paragraph>

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
          creanciers: [{ type_partie: 'pp' }],
          clause_reserve_propriete: true,
          propriete_conservee_par_vendeur: true,
          declaration_exactitude: false,
        }}
      >
        {/* Identification */}
        <Card title={<Space><FileTextOutlined />{t('formulaire.commun.section.identification')}</Space>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <HorodatageDemandeField t={t} />
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

        {/* Contrat de vente */}
        <Card title={<Space><SafetyCertificateOutlined />{t('formulaire.reserve_propriete.section.contrat')}</Space>} style={{ marginBottom: 16 }}>
          <Alert
            type="info" showIcon style={{ marginBottom: 12 }}
            message={t('formulaire.reserve_propriete.contexte')}
          />
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item name="date_contrat" label={t('formulaire.reserve_propriete.date_contrat')} rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="reference_contrat" label={t('formulaire.reserve_propriete.reference_contrat')} rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="date_limite_paiement" label={t('formulaire.reserve_propriete.date_limite_paiement')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="clause_reserve_propriete" valuePropName="checked">
                <Checkbox>{t('formulaire.reserve_propriete.clause_existe')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="bien_remis_acquereur" valuePropName="checked">
                <Checkbox>{t('formulaire.reserve_propriete.bien_remis')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="acquereur_en_possession" valuePropName="checked">
                <Checkbox>{t('formulaire.reserve_propriete.acquereur_en_possession')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="propriete_conservee_par_vendeur" valuePropName="checked">
                <Checkbox>{t('formulaire.reserve_propriete.propriete_conservee')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="texte_clause_reserve" label={t('formulaire.reserve_propriete.texte_clause')}>
                <Input.TextArea rows={3} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="date_acceptation_clause" label={t('formulaire.reserve_propriete.date_acceptation_clause')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="modalites_paiement" label={t('formulaire.reserve_propriete.modalites_paiement')}>
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item name="localisation_actuelle_bien" label={t('formulaire.reserve_propriete.localisation_actuelle_bien')}>
                <Input.TextArea rows={2} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Conditions financières */}
        <Card title={<Space><DollarOutlined />{t('formulaire.inscription.section.conditions_financieres')}</Space>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item name="prix_total" label={t('formulaire.reserve_propriete.prix_total')} rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="montant_paye" label={t('formulaire.reserve_propriete.montant_paye')}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="solde_restant" label={t('formulaire.reserve_propriete.solde_restant')}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="montant_creance" label={t('formulaire.commun.montant_creance')} rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="monnaie" label={t('formulaire.inscription.monnaie')}>
                <Select options={[{ value: 'MRU', label: 'MRU' }, { value: 'EUR', label: 'EUR' }, { value: 'USD', label: 'USD' }]} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="duree_en_jours" label={t('formulaire.inscription.duree')} rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="date_naissance_creance" label={t('formulaire.commun.date_naissance_creance')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="date_echeance" label={t('formulaire.commun.date_echeance')}>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Parties */}
        <Card title={<Space><UserOutlined />{t('formulaire.inscription.section.parties')}</Space>} style={{ marginBottom: 16 }}>
          <ListePartiesField
            t={t} ar={ar} nom="creanciers"
            titre={t('formulaire.reserve_propriete.partie.vendeur.titre')}
            description={t('formulaire.reserve_propriete.partie.vendeur.description')}
            minimum={1}
            libelleAjouter={t('formulaire.reserve_propriete.partie.vendeur.ajouter')}
          />
          <Divider />
          <ListePartiesField
            t={t} ar={ar} nom="constituants"
            titre={t('formulaire.reserve_propriete.partie.acquereur.titre')}
            description={t('formulaire.reserve_propriete.partie.acquereur.description')}
            minimum={1}
            libelleAjouter={t('formulaire.reserve_propriete.partie.acquereur.ajouter')}
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
            aide={t('formulaire.reserve_propriete.pj.aide')}
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
