import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert, Button, Card, Col, DatePicker, Empty, Row, Select, Space, Spin,
  Statistic, Table, Tag, Typography,
} from 'antd';
import { useTranslation } from 'react-i18next';

import client, { formatMessageErreur } from '../api/client';
import KpiCarte from '../components/KpiCarte';

const { Title, Paragraph, Text } = Typography;
const { RangePicker } = DatePicker;

const NATURES_DROIT = [
  'nant_outillage', 'nant_droits_associes', 'nant_fonds_commerce',
  'priv_vendeur_fonds', 'nant_stocks', 'priv_tresor', 'priv_fiscal',
  'priv_douanes', 'priv_prevoyance', 'nant_creance',
  'nant_compte_bancaire', 'nant_pi',
];

const STATUTS = [
  'recue', 'en_controle_forme', 'rejetee', 'inscrite',
  'modifiee', 'renouvelee', 'radiee', 'expiree', 'archivee',
];

/**
 * Vue de consultation statistique — lecture seule.
 *
 * Toutes les valeurs viennent de l'API ``/api/v1/statistiques/indicateurs/``.
 * Aucune valeur n'est inventée côté client : si le backend signale qu'un
 * axe n'est pas modélisé, l'écran affiche un encart explicite (note +
 * raison technique).
 */
export default function Statistiques() {
  const { t, i18n } = useTranslation();
  const [donnees, setDonnees] = useState(null);
  const [pme, setPme] = useState(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);
  const [filtres, setFiltres] = useState({});

  const charger = useCallback(async () => {
    setChargement(true);
    setErreur(null);
    try {
      const [r1, r2] = await Promise.all([
        client.get('/statistiques/indicateurs/', { params: filtres }),
        client.get('/statistiques/financement-pme/', { params: filtres }),
      ]);
      setDonnees(r1.data);
      setPme(r2.data);
    } catch (e) {
      setErreur(formatMessageErreur(e, t));
    } finally {
      setChargement(false);
    }
  }, [filtres, t]);

  useEffect(() => { charger(); }, [charger]);

  const formaterNombre = (n) => {
    if (n === null || n === undefined) return '—';
    if (typeof n === 'number') {
      try { return n.toLocaleString(i18n.language === 'ar' ? 'ar-MR' : 'fr-FR'); }
      catch { return String(n); }
    }
    return String(n);
  };

  const formaterMontant = (n, monnaie) => {
    if (n === null || n === undefined) return '—';
    const v = formaterNombre(typeof n === 'number' ? Math.round(n) : n);
    return monnaie ? `${v} ${monnaie}` : v;
  };

  const onChangePeriode = (dates) => {
    setFiltres((f) => ({
      ...f,
      date_debut: dates?.[0]?.format('YYYY-MM-DD') || undefined,
      date_fin: dates?.[1]?.format('YYYY-MM-DD') || undefined,
    }));
  };

  if (chargement && !donnees) {
    return <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>;
  }
  if (erreur && !donnees) {
    return (
      <div>
        <Title level={2}>{t('statistiques.titre')}</Title>
        <Alert type="error" message={erreur} />
      </div>
    );
  }
  if (!donnees) return null;

  const { totaux, axes } = donnees;

  return (
    <div>
      <Title level={2}>{t('statistiques.titre')}</Title>
      <Paragraph>{t('statistiques.introduction')}</Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      {/* ==================================================== */}
      {/*                   FILTRES                            */}
      {/* ==================================================== */}
      <Card title={t('statistiques.filtres.titre')} style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={24} md={10}>
            <div style={{ marginBottom: 6 }}>
              <Text type="secondary">{t('statistiques.filtres.periode')}</Text>
            </div>
            <RangePicker style={{ width: '100%' }} onChange={onChangePeriode} />
          </Col>
          <Col xs={24} md={5}>
            <div style={{ marginBottom: 6 }}>
              <Text type="secondary">{t('statistiques.filtres.nature_droit')}</Text>
            </div>
            <Select
              allowClear
              style={{ width: '100%' }}
              placeholder="—"
              options={NATURES_DROIT.map((v) => ({ value: v, label: v }))}
              onChange={(v) => setFiltres((f) => ({ ...f, nature_droit: v }))}
            />
          </Col>
          <Col xs={24} md={5}>
            <div style={{ marginBottom: 6 }}>
              <Text type="secondary">{t('statistiques.filtres.canal_saisie')}</Text>
            </div>
            <Select
              allowClear
              style={{ width: '100%' }}
              placeholder="—"
              options={[
                { value: 'guichet_papier', label: t('formulaire.inscription.canal.guichet_papier') },
                { value: 'portail_electronique', label: t('formulaire.inscription.canal.portail_electronique') },
              ]}
              onChange={(v) => setFiltres((f) => ({ ...f, canal_saisie: v }))}
            />
          </Col>
          <Col xs={24} md={4}>
            <div style={{ marginBottom: 6 }}>
              <Text type="secondary">{t('statistiques.filtres.statut')}</Text>
            </div>
            <Select
              allowClear
              style={{ width: '100%' }}
              placeholder="—"
              options={STATUTS.map((s) => ({ value: s, label: t(`inscription.statut.${s}`) }))}
              onChange={(v) => setFiltres((f) => ({ ...f, statut: v }))}
            />
          </Col>
        </Row>
        <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
          <Text strong>{t('statistiques.instant_calcul')} :</Text> {donnees.instant_calcul}
        </Paragraph>
      </Card>

      {/* ==================================================== */}
      {/*                   KPI PRINCIPAUX                     */}
      {/* ==================================================== */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} md={6}>
          <Card><Statistic title={t('statistiques.kpi.inscriptions')} value={formaterNombre(totaux.inscriptions)} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card><Statistic title={t('statistiques.kpi.modifications')} value={formaterNombre(totaux.demandes_modification)} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card><Statistic title={t('statistiques.kpi.renouvellements')} value={formaterNombre(totaux.demandes_renouvellement)} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card><Statistic title={t('statistiques.kpi.radiations')} value={formaterNombre(totaux.demandes_radiation)} /></Card>
        </Col>
      </Row>

      {/* ==================================================== */}
      {/*  ENCART : ACCÈS AU FINANCEMENT DES PME (proxy)       */}
      {/* ==================================================== */}
      {pme && (
        <SectionAxe titre={t('financement_pme.titre')}>
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            message={t('financement_pme.proxy.titre')}
            description={t('financement_pme.proxy.description')}
          />
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={12} md={6}>
              <KpiCarte
                libelle={t('financement_pme.kpi.productives')}
                valeur={formaterNombre(pme.totaux.inscriptions_productives)}
                hint={`${pme.ratios.part_productives_pct}% ${t('financement_pme.kpi.du_total')}`}
              />
            </Col>
            <Col xs={12} md={6}>
              <KpiCarte
                libelle={t('financement_pme.kpi.constituants_pm')}
                valeur={formaterNombre(pme.totaux.constituants_pm_productifs)}
                hint={t('financement_pme.kpi.constituants_pm_hint')}
              />
            </Col>
            <Col xs={12} md={6}>
              <KpiCarte
                libelle={t('financement_pme.kpi.somme_productive')}
                valeur={formaterMontant(pme.montants_productifs.somme_totale)}
                hint={t('financement_pme.kpi.somme_productive_hint')}
              />
            </Col>
            <Col xs={12} md={6}>
              <KpiCarte
                libelle={t('financement_pme.kpi.duree_moyenne')}
                valeur={pme.montants_productifs.duree_moyenne_jours
                  ? Math.round(pme.montants_productifs.duree_moyenne_jours)
                  : '—'}
                suffixe={t('statistiques.kpi.suffixe_jours')}
                hint={t('financement_pme.kpi.duree_moyenne_hint')}
              />
            </Col>
            <Col xs={12} md={6}>
              <KpiCarte
                accent="rouge"
                libelle={t('financement_pme.kpi.taux_radiation')}
                valeur={`${pme.ratios.taux_radiation_pct}%`}
                hint={t('financement_pme.kpi.taux_radiation_hint')}
              />
            </Col>
            <Col xs={12} md={6}>
              <KpiCarte
                accent="jaune"
                libelle={t('financement_pme.kpi.echeances_90j')}
                valeur={formaterNombre(pme.totaux.echeances_90_jours)}
                hint={t('financement_pme.kpi.echeances_90j_hint')}
              />
            </Col>
            <Col xs={24} md={12}>
              <BlocBarres
                titre={t('financement_pme.familles_productives')}
                donnees={pme.familles_productives}
                libellesT={(cle) => t(`statistiques.famille.${cle}`)}
              />
            </Col>
            <Col xs={24} md={12}>
              <BlocNote
                titre={t('financement_pme.lecture.titre')}
                note={t('financement_pme.lecture.note')}
              />
            </Col>
          </Row>
        </SectionAxe>
      )}

      {/* ==================================================== */}
      {/*  AXE F — DURÉE & MONTANTS (mis en avant)             */}
      {/* ==================================================== */}
      <SectionAxe titre={t('statistiques.axes.duree_montants.titre')}>
        {axes.duree_montants.disponible ? (
          <Row gutter={[16, 16]}>
            <Col xs={12} md={6}>
              <Card>
                <Statistic
                  title={t('statistiques.kpi.duree_moyenne_jours')}
                  value={axes.duree_montants.duree_moyenne_jours
                    ? Math.round(axes.duree_montants.duree_moyenne_jours)
                    : '—'}
                  suffix={axes.duree_montants.duree_moyenne_jours
                    ? t('statistiques.kpi.suffixe_jours') : ''}
                />
              </Card>
            </Col>
            <Col xs={12} md={9}>
              <Card>
                <Statistic
                  title={t('statistiques.kpi.somme_totale')}
                  value={formaterMontant(axes.duree_montants.somme_garantie_totale)}
                />
              </Card>
            </Col>
            <Col xs={24} md={9}>
              <Card>
                <Statistic
                  title={t('statistiques.kpi.somme_moyenne')}
                  value={formaterMontant(axes.duree_montants.somme_garantie_moyenne)}
                />
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <BlocBarres
                titre={t('statistiques.axes.duree_montants.tranches')}
                donnees={axes.duree_montants.par_tranche_duree}
                libellesT={(cle) => t(`statistiques.tranche.${cle}`)}
              />
            </Col>
            <Col xs={24} md={12}>
              <BlocBarres
                titre={t('statistiques.axes.duree_montants.par_monnaie')}
                donnees={axes.duree_montants.par_monnaie}
                libellesT={(cle) => cle}
              />
            </Col>
          </Row>
        ) : <BlocIndisponible axe={axes.duree_montants} />}
      </SectionAxe>

      {/* ==================================================== */}
      {/*  AXE D — BIENS GREVÉS                                */}
      {/* ==================================================== */}
      <SectionAxe titre={t('statistiques.axes.biens.titre')}>
        {axes.biens.disponible ? (
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <BlocBarres
                titre={t('statistiques.axes.biens.par_famille')}
                donnees={axes.biens.par_famille_bien}
                libellesT={(cle) => t(`statistiques.famille.${cle}`)}
              />
            </Col>
            <Col xs={24} md={12}>
              <BlocBarres
                titre={t('statistiques.axes.biens.par_nature')}
                donnees={axes.biens.par_nature_droit}
                libellesT={(cle) => cle}
              />
            </Col>
            <Col xs={24}>
              <Card>
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title={t('statistiques.kpi.biens_total')}
                      value={formaterNombre(axes.biens.biens_total)}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title={t('statistiques.kpi.biens_avec_serie')}
                      value={formaterNombre(axes.biens.biens_avec_numero_serie)}
                    />
                  </Col>
                </Row>
              </Card>
            </Col>
            <Col xs={24}>
              <BlocNote note={axes.biens.note} />
            </Col>
          </Row>
        ) : <BlocIndisponible axe={axes.biens} />}
      </SectionAxe>

      {/* ==================================================== */}
      {/*  AXE E — DYNAMIQUE                                   */}
      {/* ==================================================== */}
      <SectionAxe titre={t('statistiques.axes.dynamique.titre')}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <BlocBarres
              titre={t('statistiques.axes.dynamique.par_statut')}
              donnees={axes.dynamique.par_statut}
              libellesT={(cle) => t(`inscription.statut.${cle}`)}
            />
          </Col>
          <Col xs={24} md={12}>
            <BlocBarres
              titre={t('statistiques.axes.dynamique.par_canal')}
              donnees={axes.dynamique.par_canal_saisie}
              libellesT={(cle) => t(`formulaire.inscription.canal.${cle}`, cle)}
            />
          </Col>
        </Row>
      </SectionAxe>

      {/* ==================================================== */}
      {/*  AXE B — CRÉANCIERS                                  */}
      {/* ==================================================== */}
      <SectionAxe titre={t('statistiques.axes.creanciers.titre')}>
        {axes.creanciers.disponible ? (
          <>
            <Row gutter={[16, 16]}>
              <Col xs={12} md={8}>
                <Card>
                  <Statistic
                    title={t('statistiques.kpi.creanciers_distincts')}
                    value={formaterNombre(axes.creanciers.nombre_creanciers_distincts)}
                  />
                </Card>
              </Col>
              <Col xs={24} md={16}>
                <BlocBarres
                  titre={t('statistiques.axes.creanciers.par_type_personne')}
                  donnees={axes.creanciers.par_type_personne}
                  libellesT={(cle) => t(`statistiques.type_personne.${cle}`)}
                />
              </Col>
            </Row>
            {axes.creanciers.note_typologie && (
              <BlocNote
                titre={t('statistiques.indisponibilite.titre_typologie')}
                note={axes.creanciers.note_typologie}
                niveau="warning"
              />
            )}
          </>
        ) : <BlocIndisponible axe={axes.creanciers} />}
      </SectionAxe>

      {/* ==================================================== */}
      {/*  AXE C — CONSTITUANTS / DÉBITEURS                    */}
      {/* ==================================================== */}
      <SectionAxe titre={t('statistiques.axes.constituants.titre')}>
        {axes.constituants.disponible ? (
          <>
            <Row gutter={[16, 16]}>
              <Col xs={12} md={8}>
                <Card>
                  <Statistic
                    title={t('statistiques.kpi.constituants_distincts')}
                    value={formaterNombre(axes.constituants.nombre_constituants_distincts)}
                  />
                </Card>
              </Col>
              <Col xs={24} md={16}>
                <BlocBarres
                  titre={t('statistiques.axes.constituants.par_type_personne')}
                  donnees={axes.constituants.par_type_personne}
                  libellesT={(cle) => t(`statistiques.type_personne.${cle}`)}
                />
              </Col>
            </Row>
            {axes.constituants.note_secteur && (
              <BlocNote
                titre={t('statistiques.indisponibilite.titre_secteur')}
                note={axes.constituants.note_secteur}
                niveau="warning"
              />
            )}
          </>
        ) : <BlocIndisponible axe={axes.constituants} />}
      </SectionAxe>

      {/* ==================================================== */}
      {/*  AXE A — TERRITORIAL                                 */}
      {/* ==================================================== */}
      <SectionAxe titre={t('statistiques.axes.territorial.titre')}>
        <BlocIndisponible axe={axes.territorial} />
      </SectionAxe>

      <Button onClick={charger} style={{ marginTop: 24 }} loading={chargement}>
        {t('statistiques.recharger')}
      </Button>
    </div>
  );
}

/* ====================================================================== */
/*  Composants utilitaires                                                  */
/* ====================================================================== */

function SectionAxe({ titre, children }) {
  return (
    <section className="rim-section">
      <div className="rim-section__entete">
        <h2 className="rim-section__titre">{titre}</h2>
      </div>
      {children}
    </section>
  );
}

function BlocIndisponible({ axe }) {
  const { t } = useTranslation();
  const cleRaison = axe?.raison_indisponibilite;
  return (
    <Alert
      type="info"
      showIcon
      message={t('statistiques.indisponibilite.titre')}
      description={(
        <div>
          {cleRaison && (
            <div>
              <Text strong>{t('statistiques.indisponibilite.code')} :</Text>{' '}
              <Tag color="orange">{cleRaison}</Tag>
            </div>
          )}
          {axe?.note && <p style={{ marginTop: 6, marginBottom: 0 }}>{axe.note}</p>}
        </div>
      )}
    />
  );
}

function BlocNote({ titre, note, niveau = 'info' }) {
  return (
    <Alert
      type={niveau}
      showIcon
      message={titre}
      description={note}
      style={{ marginTop: 12 }}
    />
  );
}

function BlocBarres({ titre, donnees, libellesT }) {
  const entrees = useMemo(() => {
    const pairs = Object.entries(donnees || {})
      .filter(([, v]) => typeof v === 'number')
      .sort((a, b) => b[1] - a[1]);
    const max = pairs.reduce((acc, [, v]) => Math.max(acc, v), 0);
    return pairs.map(([cle, valeur]) => ({
      cle, valeur, ratio: max > 0 ? Math.max(valeur / max, 0.04) : 0,
    }));
  }, [donnees]);

  if (!entrees.length) {
    return <Card title={titre}><Empty description="—" /></Card>;
  }

  return (
    <Card title={titre} size="small">
      <div className="rim-stat-barres">
        {entrees.map((e) => (
          <div className="rim-stat-barre" key={e.cle}>
            <div className="rim-stat-barre__libelle">{libellesT(e.cle)}</div>
            <div className="rim-stat-barre__piste">
              <div
                className="rim-stat-barre__remplissage"
                style={{ width: `${Math.round(e.ratio * 100)}%` }}
              />
              <div className="rim-stat-barre__valeur">{e.valeur}</div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
