import React, { useEffect, useState } from 'react';
import {
  Alert, Card, Checkbox, Col, DatePicker, Divider, Form, Input, InputNumber,
  Row, Select, Space, Spin, Typography,
} from 'antd';
import {
  FileTextOutlined, UserOutlined, DollarOutlined, AppstoreOutlined,
  PaperClipOutlined, ShopOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import ProcedureDepot from '../components/ProcedureDepot';
import {
  ListePartiesField, normaliserPartie,
} from '../components/formulaires/PartiesShared';
import { BienUnique, normaliserBienUnique } from '../components/formulaires/BienShared';
import PiecesJointesField from '../components/formulaires/PiecesJointesShared';
import { soumettreInscription } from '../components/formulaires/soumettreInscription';
import HorodatageDemandeField from '../components/formulaires/HorodatageDemandeField';
import { reglesEmail } from '../lib/validation';
import { CANAL_SAISIE_DEFAUT, NATURE_DROIT_PAR_TYPE_SURETE } from '../lib/typeSurete';

const { Title, Paragraph } = Typography;

/**
 * Inscription du privilège du vendeur.
 *
 * Mapping métier ↔ entités RSM :
 *   - Vendeur   → créancier (il conserve un privilège sur le bien)
 *   - Acheteur  → constituant + débiteur (case "débiteur = constituant"
 *                 cochée par défaut pour ce parcours)
 *   - Bien      → unique (description précise + numéro de série)
 *
 * Champs spécifiques persistés dans Inscription.donnees_specifiques.
 *
 * Garde-fous (post-bascule MO) :
 *   - intégrité : un seul POST métier puis upload PJ ;
 *   - traçabilité : audit backend ;
 *   - mono-langue : description du bien dans la langue active.
 */
export default function FormulairePrivilegeVendeur() {
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
        type_surete: 'privilege_vendeur',
        // Canal implicite (registre 100% numérisé) et nature déduite
        // du type_surete (directive MO 2026-05-31).
        canal_saisie: CANAL_SAISIE_DEFAUT,
        nature_droit: NATURE_DROIT_PAR_TYPE_SURETE.privilege_vendeur,
        somme_garantie: v.montant_creance,
        monnaie: v.monnaie,
        duree_en_jours: v.duree_en_jours,
        adresse_electronique_notifications: v.adresse_electronique_notifications || '',
        debiteur_est_constituant: true, // l'acheteur joue les deux rôles
        constituants: (v.constituants || []).map(normaliserPartie),
        creanciers: (v.creanciers || []).map(normaliserPartie),
        debiteurs: [],
        biens: v.bien ? [normaliserBienUnique(v.bien, ar)] : [],
        donnees_specifiques: {
          // ``date_demande`` n'est plus collecté : l'horodatage autoritatif
          // est ``Inscription.instant_arrivee`` (timezone.now() côté backend).
          date_contrat_vente: dateOuNull(v.date_contrat_vente),
          reference_contrat_vente: v.reference_contrat_vente || '',
          prix_total_vente: v.prix_total_vente || null,
          montant_paye: v.montant_paye || null,
          montant_restant_du: v.montant_restant_du || null,
          date_livraison: dateOuNull(v.date_livraison),
          bien_livre: !!v.bien_livre,
          acheteur_en_possession: !!v.acheteur_en_possession,
          date_naissance_creance: dateOuNull(v.date_naissance_creance),
          date_echeance: dateOuNull(v.date_echeance),
          clause_privilege: v.clause_privilege || '',
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
      <Title level={2}>{t('formulaire.privilege_vendeur.titre')}</Title>
      <Paragraph>{t('formulaire.privilege_vendeur.introduction')}</Paragraph>

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
          declaration_exactitude: false,
        }}
      >
        {/* Section 1 : Identification de la demande */}
        <Card
          title={<Space><FileTextOutlined />{t('formulaire.commun.section.identification')}</Space>}
          style={{ marginBottom: 16 }}
        >
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

        {/* Section 2 : Contrat de vente */}
        <Card
          title={<Space><ShopOutlined />{t('formulaire.privilege_vendeur.section.contrat')}</Space>}
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                name="date_contrat_vente"
                label={t('formulaire.privilege_vendeur.date_contrat_vente')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="reference_contrat_vente"
                label={t('formulaire.privilege_vendeur.reference_contrat_vente')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="date_livraison"
                label={t('formulaire.privilege_vendeur.date_livraison')}
              >
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="bien_livre" valuePropName="checked">
                <Checkbox>{t('formulaire.privilege_vendeur.bien_livre')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="acheteur_en_possession" valuePropName="checked">
                <Checkbox>{t('formulaire.privilege_vendeur.acheteur_en_possession')}</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24}>
              <Form.Item
                name="clause_privilege"
                label={t('formulaire.privilege_vendeur.clause_privilege')}
                tooltip={t('formulaire.privilege_vendeur.clause_privilege_aide')}
              >
                <Input.TextArea rows={3} />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* Section 3 : Conditions financières */}
        <Card
          title={<Space><DollarOutlined />{t('formulaire.inscription.section.conditions_financieres')}</Space>}
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                name="prix_total_vente"
                label={t('formulaire.privilege_vendeur.prix_total_vente')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <InputNumber style={{ width: '100%' }} min={0} step={1000}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                  parser={(v) => `${v}`.replace(/\s/g, '')} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="montant_paye" label={t('formulaire.privilege_vendeur.montant_paye')}>
                <InputNumber style={{ width: '100%' }} min={0} step={1000}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                  parser={(v) => `${v}`.replace(/\s/g, '')} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="montant_restant_du"
                label={t('formulaire.privilege_vendeur.montant_restant_du')}
              >
                <InputNumber style={{ width: '100%' }} min={0} step={1000}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                  parser={(v) => `${v}`.replace(/\s/g, '')} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="montant_creance"
                label={t('formulaire.commun.montant_creance')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <InputNumber style={{ width: '100%' }} min={0} step={1000}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                  parser={(v) => `${v}`.replace(/\s/g, '')} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="monnaie" label={t('formulaire.inscription.monnaie')}>
                <Select options={[
                  { value: 'MRU', label: 'MRU' }, { value: 'EUR', label: 'EUR' }, { value: 'USD', label: 'USD' },
                ]} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="duree_en_jours"
                label={t('formulaire.inscription.duree')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
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

        {/* Section 4 : Parties */}
        <Card
          title={<Space><UserOutlined />{t('formulaire.inscription.section.parties')}</Space>}
          style={{ marginBottom: 16 }}
        >
          <ListePartiesField
            t={t} ar={ar}
            nom="creanciers"
            titre={t('formulaire.privilege_vendeur.partie.vendeur.titre')}
            description={t('formulaire.privilege_vendeur.partie.vendeur.description')}
            minimum={1}
            libelleAjouter={t('formulaire.privilege_vendeur.partie.vendeur.ajouter')}
          />
          <Divider />
          <ListePartiesField
            t={t} ar={ar}
            nom="constituants"
            titre={t('formulaire.privilege_vendeur.partie.acheteur.titre')}
            description={t('formulaire.privilege_vendeur.partie.acheteur.description')}
            minimum={1}
            libelleAjouter={t('formulaire.privilege_vendeur.partie.acheteur.ajouter')}
          />
        </Card>

        {/* Section 5 : Bien */}
        <Card
          title={<Space><AppstoreOutlined />{t('formulaire.inscription.section.bien')}</Space>}
          style={{ marginBottom: 16 }}
        >
          <BienUnique t={t} ar={ar} categories={categories} prefixe="bien" />
        </Card>

        {/* Section 6 : Pièces jointes */}
        <Card
          title={<Space><PaperClipOutlined />{t('formulaire.inscription.section.pieces_jointes')}</Space>}
          style={{ marginBottom: 16 }}
        >
          <PiecesJointesField
            t={t}
            fichiers={piecesJointes}
            setFichiers={setPiecesJointes}
            aide={t('formulaire.privilege_vendeur.pj.aide')}
          />
        </Card>

        {/* Déclaration */}
        <Card style={{ marginBottom: 16 }}>
          <Form.Item
            name="declaration_exactitude"
            valuePropName="checked"
            rules={[{
              validator: (_, v) => v
                ? Promise.resolve()
                : Promise.reject(new Error(t('formulaire.commun.declaration_exactitude_requise'))),
            }]}
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
