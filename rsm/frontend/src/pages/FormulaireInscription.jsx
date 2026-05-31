import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert, Button, Card, Checkbox, Col, DatePicker, Divider, Form, Input,
  InputNumber, Modal, Row, Select, Space, Spin, Typography,
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, UserOutlined, BankOutlined,
  FileTextOutlined, DollarOutlined, AppstoreOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import ProcedureDepot from '../components/ProcedureDepot';
import { montantEnLettres } from '../lib/montantEnLettres';

const { Title, Paragraph, Text } = Typography;

/**
 * Dépôt d'inscription de sûreté mobilière (art. 85) — refonte fonctionnelle.
 *
 * Organisation en 5 sections claires :
 *   1. Identification de la demande
 *   2. Conditions financières (somme + monnaie + durée + montant en lettres FR/AR)
 *   3. Titre constitutif (convention + date)
 *   4. Parties (constituants / débiteurs / créanciers, dynamiques)
 *   5. Biens grevés (dynamiques, basés sur les catégories paramétrables)
 *
 * Garde-fous (post-bascule MO du 2026-05-30) :
 *   - intégrité : aucune mutation directe — submit via /inscriptions/ ;
 *   - traçabilité : chaque sous-création tracée côté backend ;
 *   - parité FR/AR : libellés résolus via i18n, dynamiques selon la langue active.
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
  // calcul instantané du montant en lettres FR + AR.
  const sommeWatch = Form.useWatch('somme_garantie', form);
  const monnaieWatch = Form.useWatch('monnaie', form);
  const debiteurEstConstituantWatch = Form.useWatch('debiteur_est_constituant', form);

  const lettresFr = useMemo(
    () => montantEnLettres(sommeWatch, monnaieWatch || '', 'fr'),
    [sommeWatch, monnaieWatch],
  );
  const lettresAr = useMemo(
    () => montantEnLettres(sommeWatch, monnaieWatch || '', 'ar'),
    [sommeWatch, monnaieWatch],
  );

  const soumettre = async () => {
    setErreur(null);
    setEnCours(true);
    try {
      const valeurs = await form.validateFields();

      // Normalisation du payload pour le backend.
      const payload = {
        ...valeurs,
        // DatePicker → "YYYY-MM-DD"
        date_convention: valeurs.date_convention
          ? valeurs.date_convention.format('YYYY-MM-DD')
          : null,
        montant_en_lettres_fr: lettresFr,
        montant_en_lettres_ar: lettresAr,
        // Si débiteur = constituant, on n'envoie pas de débiteurs (le backend duplique).
        debiteurs: valeurs.debiteur_est_constituant ? [] : (valeurs.debiteurs || []),
        constituants: valeurs.constituants || [],
        creanciers: valeurs.creanciers || [],
        // Normalisation des biens : date du DatePicker éventuel des attributs
        // spécifiques (laissé tel quel pour l'instant — le backend stocke en JSON).
        biens: (valeurs.biens || []).map((b) => ({
          categorie_cle: b.categorie_cle,
          description_fr: b.description_fr || '',
          description_ar: b.description_ar || '',
          marque: b.marque || '',
          modele: b.modele || '',
          annee: b.annee || null,
          numero_serie: b.numero_serie || '',
          attributs_specifiques: b.attributs_specifiques || {},
          observations: b.observations || '',
        })),
        // Normalisation parties (dates de naissance)
        constituants: (valeurs.constituants || []).map(normaliserPartie),
        creanciers: (valeurs.creanciers || []).map(normaliserPartie),
      };
      if (!valeurs.debiteur_est_constituant) {
        payload.debiteurs = (valeurs.debiteurs || []).map(normaliserPartie);
      }

      const { data } = await client.post('/inscriptions/', payload);
      Modal.success({
        title: t('soumission.succes.titre'),
        content: `${t('soumission.succes.contenu')} (${data.reference_demande || ''})`,
        okText: t('soumission.fermer'),
      });
      form.resetFields();
    } catch (e) {
      if (e?.errorFields) return; // erreur de validation formulaire AntD
      setErreur(formatMessageErreur(e, t));
    } finally {
      setEnCours(false);
    }
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
          canal_saisie: 'portail_electronique',
          monnaie: 'MRU',
          debiteur_est_constituant: false,
          constituants: [{ type_partie: 'pp' }],
          creanciers: [{ type_partie: 'pp' }],
          debiteurs: [],
          biens: [{}],
        }}
      >
        {/* ============ Section 1 — Identification ============ */}
        <Card
          title={(
            <Space>
              <FileTextOutlined />
              {t('formulaire.commun.section.identification')}
            </Space>
          )}
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                name="canal_saisie"
                label={t('formulaire.inscription.canal')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <Select
                  options={[
                    { value: 'guichet_papier', label: t('formulaire.inscription.canal.guichet_papier') },
                    { value: 'portail_electronique', label: t('formulaire.inscription.canal.portail_electronique') },
                  ]}
                />
              </Form.Item>
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
            <Col xs={24}>
              <Form.Item
                name="adresse_electronique_notifications"
                label={t('formulaire.inscription.email')}
              >
                <Input placeholder="exemple@rsm.mr" />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* ============ Section 2 — Conditions financières ============ */}
        <Card
          title={(
            <Space>
              <DollarOutlined />
              {t('formulaire.inscription.section.conditions_financieres')}
            </Space>
          )}
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col xs={12} md={8}>
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
            <Col xs={12} md={8}>
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
            <Col xs={24} md={8}>
              <Form.Item
                name="duree_en_jours"
                label={t('formulaire.inscription.duree')}
                rules={[{ required: true, message: t('formulaire.commun.requis') }]}
              >
                <InputNumber style={{ width: '100%' }} min={1} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item label={t('formulaire.inscription.montant_lettres_fr')}>
                <Input
                  value={lettresFr}
                  readOnly
                  placeholder={t('formulaire.inscription.montant_lettres_placeholder')}
                  style={{ background: 'var(--gris-50)' }}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label={t('formulaire.inscription.montant_lettres_ar')}>
                <Input
                  value={lettresAr}
                  readOnly
                  dir="rtl"
                  lang="ar"
                  placeholder={t('formulaire.inscription.montant_lettres_placeholder')}
                  style={{ background: 'var(--gris-50)' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        {/* ============ Section 3 — Titre constitutif ============ */}
        <Card
          title={(
            <Space>
              <FileTextOutlined />
              {t('formulaire.inscription.section.titre_constitutif')}
            </Space>
          )}
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16}>
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

        {/* ============ Section 4 — Parties ============ */}
        <Card
          title={(
            <Space>
              <UserOutlined />
              {t('formulaire.inscription.section.parties')}
            </Space>
          )}
          style={{ marginBottom: 16 }}
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
        </Card>

        {/* ============ Section 5 — Biens grevés ============ */}
        <Card
          title={(
            <Space>
              <AppstoreOutlined />
              {t('formulaire.inscription.section.biens')}
            </Space>
          )}
          style={{ marginBottom: 16 }}
        >
          <Paragraph type="secondary">
            {t('formulaire.inscription.biens.description')}
          </Paragraph>
          <ListeBiensField t={t} ar={ar} categories={categories} />
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
function PartieFieldset({ t, ar, name, index, onRetirer }) {
  const form = Form.useFormInstance();
  // Récupère le chemin du parent Form.List : on observe via watch
  // (le chemin complet est inconnu ici, donc on lit côté form via getFieldValue
  // en pratique, on s'appuie sur le nom relatif passé par Form.List).
  const typePartiePath = (parent) => [parent, name, 'type_partie'];

  // On ne connaît pas le nom de la liste parente ici ; on contourne en
  // observant les champs via le name local et la valeur courante.
  // Ant Design supporte la lecture relative via le `name` du fieldset.
  // Trick : on utilise un Form.Item name=["type_partie"] dans un sous-Form,
  // mais c'est plus simple de juste lire depuis form.getFieldValue avec un
  // chemin dynamique. Pour simplifier ici, on rend les deux groupes de
  // champs et on les masque via shouldUpdate.

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

      <Form.Item shouldUpdate noStyle>
        {() => {
          // Sécurité : on lit la valeur via le path actuel,
          // sans connaître la liste parente, en utilisant Form.useWatch global.
          // Workaround : on cherche le type via le state du formulaire.
          // Comme le name est dans une Form.List, le path complet est résolu
          // côté Ant Design ; pour rester portable, on utilise un BadgeRef
          // via dépend du form parent.
          // Implémentation : on utilise une dépendance via shouldUpdate
          // et on lit avec Form.getFieldValue en se basant sur la
          // racine du formulaire (path inconnu) — alternative : on
          // récupère le type via la prop `dependencies` du Form.Item
          // englobant. Pour rester simple, on rend les deux blocs et on
          // n'oblige rien : la validation backend filtre selon le type.
          return null;
        }}
      </Form.Item>

      {/* Champs personne physique */}
      <Form.Item shouldUpdate noStyle>
        {({ getFieldValue }) => {
          // ARTUCE : on accède au type via le path RELATIF connu.
          // Form.List passe `name` qui correspond au sous-index. Le
          // path complet en dépend ; on utilise un getter sur le state.
          // Le `getFieldValue([nom_liste, name, 'type_partie'])` ne marche
          // pas sans connaître nom_liste. On utilise donc un sentinel :
          // on rend toujours les deux blocs, et le backend ignore les
          // champs vides selon `type_partie`. Cette approche est
          // robuste (zéro JS) et n'introduit aucune divergence FR/AR.
          return null;
        }}
      </Form.Item>

      <PartiePhysiqueChamps t={t} name={name} />
      <PartieMoraleChamps t={t} ar={ar} name={name} />

      {/* Champs communs */}
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
    </Card>
  );
}


/* --- Champs Personne Physique (affichés conditionnellement) --- */
function PartiePhysiqueChamps({ t, name }) {
  return (
    <Form.Item noStyle shouldUpdate={(prev, cur) => prev !== cur}>
      {({ getFieldValue }) => {
        // On accède au type via le path absolu : Form.List enveloppe
        // les noms dans son tableau. Comme `name` est relatif, on
        // utilise une astuce : on lit via le getter de Form sur tous
        // les chemins probables (constituants/debiteurs/creanciers).
        const type = (
          getFieldValue(['constituants', name, 'type_partie'])
          ?? getFieldValue(['debiteurs', name, 'type_partie'])
          ?? getFieldValue(['creanciers', name, 'type_partie'])
        );
        if (type === 'pm') return null;
        return (
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
        );
      }}
    </Form.Item>
  );
}

/* --- Champs Personne Morale (affichés conditionnellement) --- */
function PartieMoraleChamps({ t, ar, name }) {
  return (
    <Form.Item noStyle shouldUpdate={(prev, cur) => prev !== cur}>
      {({ getFieldValue }) => {
        const type = (
          getFieldValue(['constituants', name, 'type_partie'])
          ?? getFieldValue(['debiteurs', name, 'type_partie'])
          ?? getFieldValue(['creanciers', name, 'type_partie'])
        );
        if (type !== 'pm') return null;
        return (
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
        );
      }}
    </Form.Item>
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


/* --- Fieldset d'un bien unique --- */
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
        <Col xs={24} md={12}>
          <Form.Item name={[name, 'description_fr']} label={t('formulaire.inscription.bien.description_fr')}>
            <Input.TextArea rows={2} />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name={[name, 'description_ar']} label={t('formulaire.inscription.bien.description_ar')}>
            <Input.TextArea rows={2} dir="rtl" />
          </Form.Item>
        </Col>
        <Col xs={8} md={6}>
          <Form.Item name={[name, 'marque']} label={t('formulaire.inscription.bien.marque')}>
            <Input />
          </Form.Item>
        </Col>
        <Col xs={8} md={6}>
          <Form.Item name={[name, 'modele']} label={t('formulaire.inscription.bien.modele')}>
            <Input />
          </Form.Item>
        </Col>
        <Col xs={8} md={6}>
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
 * Normalisation d'une partie avant envoi (dates dayjs → ISO, blancs, etc.)
 * ========================================================================= */
function normaliserPartie(p) {
  if (!p) return p;
  const out = { ...p };
  if (out.date_naissance && out.date_naissance.format) {
    out.date_naissance = out.date_naissance.format('YYYY-MM-DD');
  }
  // Selon le type de partie, on nettoie les champs non pertinents
  // pour éviter d'envoyer du bruit ; le backend les accepte mais on
  // reste propre.
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
