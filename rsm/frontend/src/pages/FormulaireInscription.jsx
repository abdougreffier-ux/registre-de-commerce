import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert, Button, Card, Checkbox, Col, DatePicker, Divider, Form, Input,
  InputNumber, List, Modal, Row, Select, Space, Spin, Typography, Upload,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, UserOutlined,
  FileTextOutlined, DollarOutlined, AppstoreOutlined,
  SafetyCertificateOutlined, PaperClipOutlined, FilePdfOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import ProcedureDepot from '../components/ProcedureDepot';
import HorodatageDemandeField from '../components/formulaires/HorodatageDemandeField';
import { montantEnLettres } from '../lib/montantEnLettres';
import {
  reglesEmail, reglesNom, reglesNNI, reglesPasseport, reglesTelephone,
  normaliserNom,
} from '../lib/validation';
import { CANAL_SAISIE_DEFAUT } from '../lib/typeSurete';

const { Title, Paragraph, Text } = Typography;

const PJ_TAILLE_MAX = 10 * 1024 * 1024; // 10 Mo
const PJ_TYPES_AUTORISES = ['application/pdf'];

/**
 * Dépôt d'inscription de sûreté mobilière (art. 85) — refonte fonctionnelle
 * + module Agent de sûreté + pièces jointes PDF.
 *
 * Organisation en 6 sections claires :
 *   1. Identification de la demande
 *   2. Conditions financières (somme + monnaie + durée + montant en lettres
 *      dans la LANGUE ACTIVE uniquement — pas de duplication FR/AR)
 *   3. Titre constitutif (convention + date)
 *   4. Parties (constituants / débiteurs / créanciers + agent de sûreté
 *      facultatif, dynamiques)
 *   5. Biens grevés (dynamiques, basés sur les catégories paramétrables,
 *      description dans la LANGUE ACTIVE uniquement)
 *   6. Pièces jointes PDF (multipart, 10 Mo max, multiple)
 *
 * Principe mono-langue (directive MO 2026-05-31) :
 *   UNE langue active = UN seul ensemble de champs. Aucune duplication
 *   FR/AR dans le même écran. Le backend continue de stocker en
 *   bilingue (montant en lettres calculé dans les deux langues, mais
 *   description du bien dans la seule langue de saisie).
 *
 * Garde-fous (post-bascule MO du 2026-05-30) :
 *   - intégrité : aucune mutation directe — submit via /inscriptions/ ;
 *   - traçabilité : chaque sous-création et chaque PJ tracées côté backend ;
 *   - parité FR/AR : les écrans FR et AR sont structurellement identiques.
 */
export default function FormulaireInscription() {
  const { t, i18n } = useTranslation();
  const ar = (i18n.language || 'fr').toLowerCase().startsWith('ar');
  const [form] = Form.useForm();
  const [erreur, setErreur] = useState(null);
  const [enCours, setEnCours] = useState(false);

  const [naturesDroit, setNaturesDroit] = useState([]);
  const [categories, setCategories] = useState([]);
  const [chargementReferentiels, setChargementReferentiels] = useState(true);

  // File d'attente locale des PJ — envoyées après création de l'inscription.
  const [piecesJointes, setPiecesJointes] = useState([]);

  // Chargement parallèle des référentiels (natures de droit + catégories de biens).
  useEffect(() => {
    let actif = true;
    (async () => {
      try {
        const [natures, cats] = await Promise.all([
          client.get('/referentiels/natures-droit/'),
          client.get('/categories-biens/?actif=1'),
        ]);
        if (!actif) return;
        const listeNatures = natures.data.results || natures.data || [];
        const listeCats = cats.data.results || cats.data || [];
        setNaturesDroit(listeNatures);
        setCategories(listeCats);
      } catch (e) {
        if (actif) setErreur(formatMessageErreur(e, t));
      } finally {
        if (actif) setChargementReferentiels(false);
      }
    })();
    return () => { actif = false; };
  }, [t]);

  // Observation temps réel de la somme garantie et de la monnaie pour
  // calcul instantané du montant en lettres (langue active uniquement).
  const sommeWatch = Form.useWatch('somme_garantie', form);
  const monnaieWatch = Form.useWatch('monnaie', form);
  const debiteurEstConstituantWatch = Form.useWatch('debiteur_est_constituant', form);
  const presenceAgentWatch = Form.useWatch('presence_agent_surete', form);

  // Conversion dans la langue active (affichée). La langue inactive
  // est recalculée côté backend par num2words pour persistance.
  const lettresActive = useMemo(
    () => montantEnLettres(sommeWatch, monnaieWatch || '', ar ? 'ar' : 'fr'),
    [sommeWatch, monnaieWatch, ar],
  );

  const soumettre = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      const valeurs = await form.validateFields();

      // Normalisation du payload pour le backend.
      const payload = {
        // Canal implicite : registre 100% numérisé (directive MO 2026-05-31).
        canal_saisie: CANAL_SAISIE_DEFAUT,
        nature_droit: valeurs.nature_droit,
        somme_garantie: valeurs.somme_garantie,
        monnaie: valeurs.monnaie,
        duree_en_jours: valeurs.duree_en_jours,
        adresse_electronique_notifications: valeurs.adresse_electronique_notifications || '',
        // Le backend recalcule autoritativement le montant en lettres FR + AR.
        // Le frontend transmet ce qu'il a affiché pour traçabilité, mais
        // n'est pas autoritatif.
        montant_en_lettres_fr: ar ? '' : lettresActive,
        montant_en_lettres_ar: ar ? lettresActive : '',
        nature_convention: valeurs.nature_convention || '',
        date_convention: valeurs.date_convention
          ? valeurs.date_convention.format('YYYY-MM-DD')
          : null,
        debiteur_est_constituant: !!valeurs.debiteur_est_constituant,
        constituants: (valeurs.constituants || []).map(normaliserPartie),
        creanciers: (valeurs.creanciers || []).map(normaliserPartie),
        debiteurs: valeurs.debiteur_est_constituant
          ? []
          : (valeurs.debiteurs || []).map(normaliserPartie),
        agents_surete: valeurs.presence_agent_surete
          ? (valeurs.agents_surete || []).map(normaliserAgent)
          : [],
        biens: (valeurs.biens || []).map((b) => normaliserBien(b, ar)),
      };

      const { data } = await client.post('/inscriptions/', payload);

      // Upload des pièces jointes (séquentiel pour éviter de saturer le réseau).
      const reference = data.reference_demande;
      const pjErreurs = [];
      for (const pj of piecesJointes) {
        try {
          const fd = new FormData();
          fd.append('fichier', pj.originFileObj || pj);
          await client.post(
            `/inscriptions/${reference}/pieces-jointes/`,
            fd,
            { headers: { 'Content-Type': 'multipart/form-data' } },
          );
        } catch (eu) {
          pjErreurs.push(`${pj.name} : ${formatMessageErreur(eu, t)}`);
        }
      }

      const contenu = [
        `${t('soumission.succes.contenu')} (${reference || ''})`,
        pjErreurs.length
          ? `\n\n${t('formulaire.inscription.pj.erreurs')} :\n${pjErreurs.join('\n')}`
          : '',
      ].join('');

      Modal.success({
        title: t('soumission.succes.titre'),
        content: contenu,
        okText: t('soumission.fermer'),
      });
      form.resetFields();
      setPiecesJointes([]);
    } catch (e) {
      if (e?.errorFields) return; // erreur de validation formulaire AntD
      setErreur(formatMessageErreur(e, t));
    } finally {
      setEnCours(false);
    }
  };

  // ====== Validation locale d'une PJ avant ajout à la file ======
  const onAvantUpload = (fichier) => {
    if (!PJ_TYPES_AUTORISES.includes(fichier.type)) {
      Modal.error({
        title: t('formulaire.inscription.pj.erreur.type.titre'),
        content: t('formulaire.inscription.pj.erreur.type.contenu'),
      });
      return Upload.LIST_IGNORE;
    }
    if (fichier.size > PJ_TAILLE_MAX) {
      Modal.error({
        title: t('formulaire.inscription.pj.erreur.taille.titre'),
        content: t('formulaire.inscription.pj.erreur.taille.contenu', { max: 10 }),
      });
      return Upload.LIST_IGNORE;
    }
    setPiecesJointes((curr) => [...curr, fichier]);
    return false; // empêche l'upload immédiat — fait par soumettre()
  };

  const onRetirerPj = (uid) => {
    setPiecesJointes((curr) => curr.filter((p) => p.uid !== uid));
  };

  return (
    <div>
      <Title level={2}>{t('formulaire.inscription.titre')}</Title>
      <Paragraph>{t('formulaire.inscription.introduction')}</Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}
      {chargementReferentiels && (
        <Card style={{ marginBottom: 16 }}><Spin /> {t('formulaire.commun.chargement_referentiels')}</Card>
      )}

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          monnaie: 'MRU',
          debiteur_est_constituant: false,
          presence_agent_surete: false,
          constituants: [{ type_partie: 'pp' }],
          creanciers: [{ type_partie: 'pp' }],
          debiteurs: [],
          agents_surete: [],
          biens: [{}],
        }}
      >
        {/* ============ Section 1 — Identification de la demande ============ */}
        <Card
          title={(
            <Space>
              <FileTextOutlined />
              {t('formulaire.commun.section.identification')}
            </Space>
          )}
        >
          <Row gutter={20}>
            <Col xs={24} md={12}>
              <HorodatageDemandeField t={t} />
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="nature_droit"
                label={t('formulaire.inscription.nature_droit')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Select
                  showSearch
                  optionFilterProp="label"
                  placeholder={t('formulaire.inscription.nature_droit_placeholder')}
                  options={naturesDroit.map((n) => ({
                    value: n.cle,
                    label: ar ? n.libelle_ar : n.libelle_fr,
                  }))}
                />
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

        {/* ============ Section 2 — Parties ============ */}
        <Card
          title={(
            <Space>
              <UserOutlined />
              {t('formulaire.inscription.section.parties')}
            </Space>
          )}
        >
          <ListePartiesField
            t={t} ar={ar}
            nom="constituants"
            titre={t('formulaire.inscription.partie.constituants.titre')}
            description={t('formulaire.inscription.partie.constituants.description')}
            minimum={1}
          />

          <Divider />

          <Form.Item
            name="debiteur_est_constituant"
            valuePropName="checked"
            style={{ marginBottom: 12 }}
          >
            <Checkbox>{t('formulaire.inscription.partie.debiteur_est_constituant')}</Checkbox>
          </Form.Item>

          {!debiteurEstConstituantWatch && (
            <ListePartiesField
              t={t} ar={ar}
              nom="debiteurs"
              titre={t('formulaire.inscription.partie.debiteurs.titre')}
              description={t('formulaire.inscription.partie.debiteurs.description')}
              minimum={0}
            />
          )}

          <Divider />

          <ListePartiesField
            t={t} ar={ar}
            nom="creanciers"
            titre={t('formulaire.inscription.partie.creanciers.titre')}
            description={t('formulaire.inscription.partie.creanciers.description')}
            minimum={1}
          />

          <Divider />

          {/* Agent de sûreté (FACULTATIF) */}
          <Form.Item
            name="presence_agent_surete"
            valuePropName="checked"
            style={{ marginBottom: 12 }}
          >
            <Checkbox>
              <Space size={4}>
                <SafetyCertificateOutlined />
                {t('formulaire.inscription.agent_surete.checkbox')}
              </Space>
            </Checkbox>
          </Form.Item>

          {presenceAgentWatch && (
            <ListeAgentsSureteField t={t} ar={ar} form={form} />
          )}
        </Card>

        {/* ============ Section 3 — Biens grevés ============ */}
        <Card
          title={(
            <Space>
              <AppstoreOutlined />
              {t('formulaire.inscription.section.biens')}
            </Space>
          )}
        >
          <Paragraph type="secondary" style={{ marginBottom: 12 }}>
            {t('formulaire.inscription.biens.description')}
          </Paragraph>
          <ListeBiensField t={t} ar={ar} categories={categories} />
        </Card>

        {/* ============ Section 4 — Titre constitutif ============ */}
        <Card
          title={(
            <Space>
              <FileTextOutlined />
              {t('formulaire.inscription.section.titre_constitutif')}
            </Space>
          )}
        >
          <Row gutter={20}>
            <Col xs={24} md={12}>
              <Form.Item
                name="nature_convention"
                label={t('formulaire.inscription.nature_convention')}
              >
                <Select
                  allowClear
                  placeholder={t('formulaire.inscription.nature_convention_placeholder')}
                  options={[
                    { value: 'notariee', label: t('formulaire.inscription.nature_convention.notariee') },
                    { value: 'sous_seing_prive', label: t('formulaire.inscription.nature_convention.sous_seing_prive') },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="date_convention"
                label={t('formulaire.inscription.date_convention')}
              >
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* ============ Section 5 — Conditions financières ============ */}
        <Card
          title={(
            <Space>
              <DollarOutlined />
              {t('formulaire.inscription.section.conditions_financieres')}
            </Space>
          )}
        >
          <Row gutter={20}>
            <Col xs={24} md={12}>
              <Form.Item name="somme_garantie" label={t('formulaire.inscription.somme_garantie')}>
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  step={1000}
                  formatter={(v) => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
                  parser={(v) => `${v}`.replace(/\s/g, '')}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item name="monnaie" label={t('formulaire.inscription.monnaie')}>
                <Select
                  options={[
                    { value: 'MRU', label: 'MRU' },
                    { value: 'EUR', label: 'EUR' },
                    { value: 'USD', label: 'USD' },
                  ]}
                />
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
              {/* Espace réservé pour aligner avec « Durée en jours ». */}
            </Col>
            <Col xs={24}>
              {/* Montant en lettres : pleine largeur, langue active uniquement. */}
              <Form.Item label={t('formulaire.inscription.montant_lettres')}>
                <Input
                  value={lettresActive}
                  readOnly
                  dir={ar ? 'rtl' : 'ltr'}
                  lang={ar ? 'ar' : 'fr'}
                  placeholder={t('formulaire.inscription.montant_lettres_placeholder')}
                  style={{ background: 'var(--gris-50)' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* ============ Section 6 — Pièces jointes ============ */}
        <Card
          title={(
            <Space>
              <PaperClipOutlined />
              {t('formulaire.inscription.section.pieces_jointes')}
            </Space>
          )}
        >
          <Paragraph type="secondary" style={{ marginBottom: 12 }}>
            {t('formulaire.inscription.pj.aide')}
          </Paragraph>
          <Upload
            accept=".pdf"
            beforeUpload={onAvantUpload}
            showUploadList={false}
            multiple
          >
            <Button icon={<PlusOutlined />}>
              {t('formulaire.inscription.pj.bouton_ajouter')}
            </Button>
          </Upload>
          {piecesJointes.length > 0 && (
            <List
              size="small"
              style={{ marginTop: 12 }}
              dataSource={piecesJointes}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      key="retirer"
                      size="small" danger type="text"
                      icon={<DeleteOutlined />}
                      onClick={() => onRetirerPj(item.uid)}
                    >
                      {t('formulaire.inscription.pj.retirer')}
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={<FilePdfOutlined style={{ fontSize: 22, color: 'var(--rim-rouge)' }} />}
                    title={item.name}
                    description={`${(item.size / 1024 / 1024).toFixed(2)} Mo`}
                  />
                </List.Item>
              )}
            />
          )}
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


/* =========================================================================
 * Composant Liste de parties (constituant / débiteur / créancier)
 * ========================================================================= */
function ListePartiesField({ t, ar, nom, titre, description, minimum = 0 }) {
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
              {t('formulaire.inscription.partie.ajouter')}
            </Button>
          </>
        )}
      </Form.List>
    </div>
  );
}


/* =========================================================================
 * Fieldset d'une partie unique (avec bascule PP / PM)
 * ========================================================================= */
function PartieFieldset({ t, ar, listName, name, index, onRetirer }) {
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


/* --- Affichage conditionnel selon le type de partie (PP / PM) --- */
function ChampsConditionnelsPartie({ t, listName, name }) {
  return (
    <Form.Item noStyle shouldUpdate={(prev, cur) => {
      const a = prev[listName]?.[name]?.type_partie;
      const b = cur[listName]?.[name]?.type_partie;
      return a !== b;
    }}>
      {({ getFieldValue }) => {
        const type = getFieldValue([listName, name, 'type_partie']);
        const estPm = type === 'pm';
        return (
          <>
            {!estPm && (
              <Row gutter={12}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={[name, 'nom']}
                    label={t('formulaire.inscription.partie.nom')}
                    normalize={normaliserNom}
                    rules={reglesNom(t, { required: false })}
                  >
                    <Input placeholder={t('formulaire.inscription.partie.nom_placeholder')} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name={[name, 'prenom']} label={t('formulaire.inscription.partie.prenom')}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name={[name, 'type_identifiant']}
                    label={t('formulaire.inscription.partie.type_identifiant')}
                    initialValue="nni"
                    rules={[{ required: true, message: t('formulaire.commun.requis') }]}
                  >
                    <Select
                      options={[
                        { value: 'nni', label: t('formulaire.inscription.partie.type_identifiant.nni') },
                        { value: 'passeport', label: t('formulaire.inscription.partie.type_identifiant.passeport') },
                      ]}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item noStyle shouldUpdate={(prev, cur) => {
                    const a = prev?.[listName]?.[name]?.type_identifiant;
                    const b = cur?.[listName]?.[name]?.type_identifiant;
                    return a !== b;
                  }}>
                    {({ getFieldValue: getF }) => {
                      const ti = getF([listName, name, 'type_identifiant']) || 'nni';
                      if (ti === 'passeport') {
                        return (
                          <Form.Item
                            name={[name, 'nni']}
                            label={t('formulaire.inscription.partie.passeport')}
                            rules={reglesPasseport(t, { required: false })}
                          >
                            <Input placeholder={t('formulaire.inscription.partie.passeport_placeholder')} />
                          </Form.Item>
                        );
                      }
                      return (
                        <Form.Item
                          name={[name, 'nni']}
                          label={t('formulaire.inscription.partie.nni')}
                          rules={reglesNNI(t, { required: false })}
                        >
                          <Input
                            maxLength={10}
                            placeholder={t('formulaire.inscription.partie.nni_placeholder')}
                          />
                        </Form.Item>
                      );
                    }}
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name={[name, 'date_naissance']} label={t('formulaire.inscription.partie.date_naissance')}>
                    <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
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
                <Col xs={24} md={12}>
                  <Form.Item name={[name, 'numero_rc']} label={t('formulaire.inscription.partie.numero_rc')}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
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
              <Col xs={24}>
                <Form.Item name={[name, 'adresse']} label={t('formulaire.inscription.partie.adresse')}>
                  <Input.TextArea rows={2} />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  name={[name, 'telephone']}
                  label={t('formulaire.inscription.partie.telephone')}
                  rules={reglesTelephone(t)}
                  extra={t('formulaire.inscription.partie.telephone_aide')}
                >
                  <Input placeholder="+222 2XXXXXXX" />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item
                  name={[name, 'adresse_electronique']}
                  label={t('formulaire.inscription.partie.email')}
                  rules={reglesEmail(t)}
                >
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


/* =========================================================================
 * Composant Liste d'agents de sûreté (avec pioche créancier)
 * ========================================================================= */
function ListeAgentsSureteField({ t, ar, form }) {
  // Observation des créanciers déjà saisis pour proposer la pioche.
  const creanciers = Form.useWatch('creanciers', form) || [];

  const optionsCreanciers = creanciers
    .map((c, idx) => ({ idx, partie: c }))
    .filter(({ partie }) => partie && (
      partie.nom || partie.prenom || partie.denomination_sociale
    ))
    .map(({ idx, partie }) => ({
      value: idx,
      label: partie.type_partie === 'pm'
        ? `${partie.denomination_sociale} (PM)`
        : `${partie.nom || ''} ${partie.prenom || ''}`.trim() + ' (PP)',
    }));

  // Quand on choisit "reprendre un créancier", on recopie ses valeurs
  // pour affichage en lecture seule. La pioche reste prioritaire côté
  // backend via le champ from_creancier_index.
  const onChoisirCreancier = (idxAgent, valeur) => {
    const liste = form.getFieldValue('agents_surete') || [];
    const courant = { ...(liste[idxAgent] || {}) };
    if (valeur === undefined || valeur === null) {
      courant.from_creancier_index = null;
    } else {
      courant.from_creancier_index = valeur;
      const source = creanciers[valeur] || {};
      // Recopie pour visualisation (champ technique reste le pivot).
      Object.assign(courant, {
        type_partie: source.type_partie,
        nom: source.nom, prenom: source.prenom,
        nni: source.nni,
        date_naissance: source.date_naissance,
        lieu_naissance: source.lieu_naissance,
        denomination_sociale: source.denomination_sociale,
        numero_rc: source.numero_rc,
        siege_social: source.siege_social,
        representant_legal: source.representant_legal,
        adresse: source.adresse,
        telephone: source.telephone,
        adresse_electronique: source.adresse_electronique,
      });
    }
    const nouveau = [...liste];
    nouveau[idxAgent] = courant;
    form.setFieldsValue({ agents_surete: nouveau });
  };

  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <Text strong>{t('formulaire.inscription.agent_surete.titre')}</Text>
        <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12.5 }}>
          {t('formulaire.inscription.agent_surete.description')}
        </Paragraph>
      </div>

      <Form.List name="agents_surete">
        {(fields, { add, remove }) => (
          <>
            {fields.map((field, idx) => (
              <Card
                key={field.key}
                type="inner"
                size="small"
                title={`${t('formulaire.inscription.agent_surete.numero')} ${idx + 1}`}
                extra={(
                  <Button
                    size="small" danger type="text"
                    icon={<DeleteOutlined />}
                    onClick={() => remove(field.name)}
                  >
                    {t('formulaire.inscription.agent_surete.retirer')}
                  </Button>
                )}
                style={{ marginBottom: 12 }}
              >
                <Form.Item
                  name={[field.name, 'from_creancier_index']}
                  label={t('formulaire.inscription.agent_surete.reprendre_creancier')}
                  tooltip={t('formulaire.inscription.agent_surete.reprendre_creancier_aide')}
                >
                  <Select
                    allowClear
                    placeholder={t('formulaire.inscription.agent_surete.reprendre_creancier_placeholder')}
                    options={optionsCreanciers}
                    onChange={(v) => onChoisirCreancier(field.name, v)}
                  />
                </Form.Item>

                <Form.Item noStyle shouldUpdate={(prev, cur) => {
                  const a = prev.agents_surete?.[field.name]?.from_creancier_index;
                  const b = cur.agents_surete?.[field.name]?.from_creancier_index;
                  return a !== b;
                }}>
                  {({ getFieldValue }) => {
                    const reprend = getFieldValue([
                      'agents_surete', field.name, 'from_creancier_index',
                    ]);
                    if (reprend !== undefined && reprend !== null) {
                      // En mode pioche : on rappelle ce qui a été repris,
                      // sans permettre d'édition. Champ d'identité résumé.
                      const source = creanciers[reprend] || {};
                      const resume = source.type_partie === 'pm'
                        ? `${source.denomination_sociale || ''} — RC ${source.numero_rc || '—'}`
                        : `${source.nom || ''} ${source.prenom || ''}`.trim();
                      return (
                        <Alert
                          type="info"
                          showIcon
                          message={t('formulaire.inscription.agent_surete.reprise_active')}
                          description={resume}
                        />
                      );
                    }
                    // Sinon : saisie manuelle complète.
                    return (
                      <>
                        <Form.Item
                          name={[field.name, 'type_partie']}
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
                        <ChampsConditionnelsPartie t={t} listName="agents_surete" name={field.name} />
                      </>
                    );
                  }}
                </Form.Item>
              </Card>
            ))}
            <Button
              type="dashed"
              onClick={() => add({ type_partie: 'pp' })}
              icon={<PlusOutlined />}
              style={{ width: '100%', marginTop: 8 }}
            >
              {t('formulaire.inscription.agent_surete.ajouter')}
            </Button>
          </>
        )}
      </Form.List>
    </div>
  );
}


/* =========================================================================
 * Composant Liste de biens (dynamique)
 * ========================================================================= */
function ListeBiensField({ t, ar, categories }) {
  return (
    <Form.List name="biens">
      {(fields, { add, remove }) => (
        <>
          {fields.map((field, idx) => (
            <BienFieldset
              key={field.key}
              t={t} ar={ar}
              categories={categories}
              name={field.name}
              index={idx}
              onRetirer={fields.length > 1 ? () => remove(field.name) : null}
            />
          ))}
          <Button
            type="dashed"
            onClick={() => add({})}
            icon={<PlusOutlined />}
            style={{ width: '100%', marginTop: 8 }}
          >
            {t('formulaire.inscription.bien.ajouter')}
          </Button>
        </>
      )}
    </Form.List>
  );
}


/* --- Fieldset d'un bien unique (description mono-langue) --- */
function BienFieldset({ t, ar, categories, name, index, onRetirer }) {
  return (
    <Card
      type="inner"
      size="small"
      title={`${t('formulaire.inscription.bien.numero')} ${index + 1}`}
      extra={onRetirer && (
        <Button size="small" danger type="text" icon={<DeleteOutlined />} onClick={onRetirer}>
          {t('formulaire.inscription.bien.retirer')}
        </Button>
      )}
      style={{ marginBottom: 12 }}
    >
      <Row gutter={12}>
        <Col xs={24} md={12}>
          <Form.Item
            name={[name, 'categorie_cle']}
            label={t('formulaire.inscription.bien.categorie')}
            rules={[{ required: true, message: t('formulaire.commun.requis') }]}
          >
            <Select
              showSearch
              optionFilterProp="label"
              placeholder={t('formulaire.inscription.bien.categorie_placeholder')}
              options={categories.map((c) => ({
                value: c.cle,
                label: ar ? c.libelle_ar : c.libelle_fr,
              }))}
            />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name={[name, 'numero_serie']} label={t('formulaire.inscription.bien.numero_serie')}>
            <Input />
          </Form.Item>
        </Col>
        {/* Description : MONO-LANGUE (active). Backend stocke dans description_fr ou _ar
            selon la langue de saisie. */}
        <Col xs={24}>
          <Form.Item name={[name, 'description']} label={t('formulaire.inscription.bien.description_label')}>
            <Input.TextArea rows={2} dir={ar ? 'rtl' : 'ltr'} />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name={[name, 'marque']} label={t('formulaire.inscription.bien.marque')}>
            <Input />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name={[name, 'modele']} label={t('formulaire.inscription.bien.modele')}>
            <Input />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name={[name, 'annee']} label={t('formulaire.inscription.bien.annee')}>
            <InputNumber style={{ width: '100%' }} min={1900} max={new Date().getFullYear() + 1} />
          </Form.Item>
        </Col>
        <Col xs={24}>
          <Form.Item name={[name, 'observations']} label={t('formulaire.inscription.bien.observations')}>
            <Input.TextArea rows={2} />
          </Form.Item>
        </Col>
      </Row>
    </Card>
  );
}


/* =========================================================================
 * Normalisations avant envoi
 * ========================================================================= */
function normaliserPartie(p) {
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

function normaliserAgent(a) {
  if (!a) return a;
  // Si l'agent reprend un créancier, on n'envoie que l'index. Le backend
  // réutilise la même Partie côté serveur — pas de duplication d'entité.
  if (a.from_creancier_index !== undefined && a.from_creancier_index !== null) {
    return { from_creancier_index: a.from_creancier_index, type_partie: 'pp' };
  }
  return normaliserPartie(a);
}

function normaliserBien(b, ar) {
  if (!b) return b;
  // Description mono-langue : mappage selon la langue active.
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
