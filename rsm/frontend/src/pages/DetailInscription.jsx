import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Button, Card, Descriptions, Form, Input, List, Modal, Select,
  Space, Spin, Typography,
} from 'antd';
import { UndoOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';

import client, { formatMessageErreur } from '../api/client';
import { useAuth, aUnRole } from '../contexts/AuthContext';
import StatutBadge from '../components/StatutBadge';

const { Title, Paragraph, Text } = Typography;

/**
 * Détail d'une inscription — consultation et actions selon rôle.
 *
 * - Tous les rôles authentifiés peuvent consulter.
 * - Le rôle ``autorite_validation`` (Greffier) peut valider ou rejeter
 *   une demande en statut ``en_controle_forme`` (TDR § 4.2.1).
 *
 * Aucune règle métier n'est dupliquée côté client : les actions appellent
 * les endpoints `validation` / `rejet` du backend, lequel applique les
 * règles d'habilitation et de transition (workflow § 4.3).
 */
export default function DetailInscription() {
  const { t } = useTranslation();
  const auth = useAuth();
  const { reference } = useParams();
  const navigate = useNavigate();
  const [inscription, setInscription] = useState(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState(null);

  const recharger = useCallback(async () => {
    setErreur(null);
    setChargement(true);
    try {
      const { data } = await client.get(`/inscriptions/${reference}/`);
      setInscription(data);
    } catch (e) {
      setErreur(formatMessageErreur(e, t));
    } finally {
      setChargement(false);
    }
  }, [reference, t]);

  useEffect(() => { recharger(); }, [recharger]);

  const peutValider = aUnRole(auth, ['autorite_validation']);
  const enControleForme = inscription?.statut === 'en_controle_forme';
  const estRetournee = inscription?.statut === 'retournee';
  const estDeclarantProprietaire = inscription
    && inscription.cree_par
    && auth.utilisateur
    && (inscription.cree_par === auth.utilisateur.id
        || inscription.cree_par_id === auth.utilisateur.id);

  const valider = async () => {
    Modal.confirm({
      title: t('detail.valider.confirmation_titre'),
      content: t('detail.valider.confirmation_corps'),
      okText: t('detail.valider.bouton'),
      okType: 'primary',
      cancelText: t('soumission.fermer'),
      onOk: async () => {
        try {
          await client.post(`/inscriptions/${reference}/valider/`, {});
          await recharger();
        } catch (e) { setErreur(formatMessageErreur(e, t)); }
      },
    });
  };

  const retourner = () => {
    let formRetour;
    Modal.confirm({
      title: t('detail.retourner.titre'),
      width: 600,
      icon: <UndoOutlined style={{ color: 'var(--statut-attente-fg)' }} />,
      content: (
        <Form
          layout="vertical"
          ref={(f) => { formRetour = f; }}
          onValuesChange={() => {}}
        >
          <Paragraph type="secondary">
            {t('detail.retourner.aide')}
          </Paragraph>
          <Form.Item
            name="observation_fr"
            label={t('detail.retourner.observation_fr')}
            rules={[{ required: true, whitespace: true,
                      message: t('detail.retourner.observation_requise') }]}
          >
            <Input.TextArea rows={4} placeholder={t('detail.retourner.placeholder_fr')} />
          </Form.Item>
          <Form.Item
            name="observation_ar"
            label={t('detail.retourner.observation_ar')}
            rules={[{ required: true, whitespace: true,
                      message: t('detail.retourner.observation_requise') }]}
          >
            <Input.TextArea rows={4} dir="rtl" lang="ar"
              placeholder={t('detail.retourner.placeholder_ar')} />
          </Form.Item>
        </Form>
      ),
      okText: t('detail.retourner.bouton'),
      okButtonProps: { danger: false, type: 'primary' },
      cancelText: t('soumission.fermer'),
      onOk: async () => {
        try {
          const v = await formRetour.validateFields();
          await client.post(`/inscriptions/${reference}/retourner/`, {
            observation_fr: v.observation_fr,
            observation_ar: v.observation_ar,
          });
          await recharger();
        } catch (e) {
          if (e?.errorFields) {
            return Promise.reject();
          }
          setErreur(formatMessageErreur(e, t));
        }
        return undefined;
      },
    });
  };

  const resoumettre = () => {
    Modal.confirm({
      title: t('detail.resoumettre.titre'),
      content: t('detail.resoumettre.aide'),
      icon: <ArrowRightOutlined style={{ color: 'var(--rim-vert)' }} />,
      okText: t('detail.resoumettre.bouton'),
      okType: 'primary',
      cancelText: t('soumission.fermer'),
      onOk: async () => {
        try {
          await client.post(`/inscriptions/${reference}/resoumettre/`, {});
          await recharger();
        } catch (e) { setErreur(formatMessageErreur(e, t)); }
      },
    });
  };

  const rejeter = () => {
    let motifChoisi = 'informations_illisibles';
    Modal.confirm({
      title: t('detail.rejeter.confirmation_titre'),
      content: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Paragraph style={{ marginBottom: 0 }}>
            {t('detail.rejeter.confirmation_corps')}
          </Paragraph>
          <Select
            defaultValue={motifChoisi}
            style={{ width: '100%' }}
            onChange={(v) => { motifChoisi = v; }}
            options={[
              { value: 'canal_non_autorise', label: t('detail.rejeter.motif.canal_non_autorise') },
              { value: 'informations_illisibles', label: t('detail.rejeter.motif.informations_illisibles') },
              { value: 'informations_incomprehensibles', label: t('detail.rejeter.motif.informations_incomprehensibles') },
            ]}
          />
        </Space>
      ),
      okText: t('detail.rejeter.bouton'),
      okType: 'danger',
      cancelText: t('soumission.fermer'),
      onOk: async () => {
        try {
          await client.post(`/inscriptions/${reference}/rejeter/`, {
            motif: motifChoisi,
          });
          await recharger();
        } catch (e) { setErreur(formatMessageErreur(e, t)); }
      },
    });
  };

  if (chargement) {
    return <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>;
  }
  if (erreur && !inscription) {
    return (
      <div>
        <Title level={2}>{t('detail.titre')}</Title>
        <Alert type="error" message={erreur} style={{ marginTop: 16 }} />
        <Button onClick={() => navigate('/inscriptions')} style={{ marginTop: 16 }}>
          {t('detail.retour')}
        </Button>
      </div>
    );
  }
  if (!inscription) return null;

  return (
    <div>
      <Title level={2}>{t('detail.titre')}</Title>
      <Paragraph>
        <Text strong>{t('detail.reference')} :</Text>{' '}
        <Text code>{inscription.reference_demande}</Text>
        {inscription.numero_ordre && (
          <span> · <StatutBadge variante="info" libelle={inscription.numero_ordre} pastille={false} /></span>
        )}
      </Paragraph>

      {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label={t('detail.champ.statut')}>
            <StatutBadge statut={inscription.statut} />
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.fichier')}>
            {inscription.fichier_actuel}
            {inscription.mention_radiee && (
              <span style={{ marginInlineStart: 8 }}>
                <StatutBadge statut="radiee" />
              </span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.canal')}>
            {inscription.canal_saisie_libelle}
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.nature')}>
            {inscription.nature_droit_libelle}
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.somme')}>
            {inscription.somme_garantie} {inscription.monnaie}
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.duree')}>
            {inscription.duree_en_jours}
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.arrivee')}>
            {inscription.instant_arrivee}
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.saisie_opposable')}>
            {inscription.instant_saisie_opposable || '—'}
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.expiration')}>
            {inscription.date_expiration || '—'}
          </Descriptions.Item>
          <Descriptions.Item label={t('detail.champ.email')}>
            {inscription.adresse_electronique_notifications || '—'}
          </Descriptions.Item>
          {inscription.motif_rejet && (
            <Descriptions.Item label={t('detail.champ.motif_rejet')} span={2}>
              <StatutBadge
                variante="rejet"
                libelle={inscription.motif_rejet_libelle || inscription.motif_rejet}
              />
              <div>{inscription.commentaire_rejet_fr}</div>
              <div lang="ar" dir="rtl">{inscription.commentaire_rejet_ar}</div>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* Historique des observations de retour (lecture seule) */}
      {Array.isArray(inscription.observations_retour)
        && inscription.observations_retour.length > 0 && (
        <Card
          title={(
            <Space>
              <UndoOutlined style={{ color: 'var(--statut-attente-fg)' }} />
              {t('detail.observations.titre')}
            </Space>
          )}
          style={{ marginBottom: 16 }}
        >
          <List
            dataSource={inscription.observations_retour}
            renderItem={(obs, idx) => (
              <List.Item key={obs.id}>
                <List.Item.Meta
                  title={(
                    <Space size={12} wrap>
                      <Text strong>
                        {t('detail.observations.numero')} {idx + 1}
                      </Text>
                      <Text type="secondary">{obs.cree_le}</Text>
                      <Text>{obs.cree_par_nom}</Text>
                      {obs.instant_resoumission && (
                        <StatutBadge
                          variante="succes"
                          libelle={t('detail.observations.resolue')}
                        />
                      )}
                    </Space>
                  )}
                  description={(
                    <div>
                      <Paragraph style={{ marginBottom: 4 }}>
                        <Text strong>FR : </Text>
                        {obs.observation_fr}
                      </Paragraph>
                      <Paragraph dir="rtl" lang="ar" style={{ marginBottom: 0 }}>
                        <Text strong>AR : </Text>
                        {obs.observation_ar}
                      </Paragraph>
                      {obs.instant_resoumission && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {t('detail.observations.resoumise_par')} {obs.resoumis_par_nom}
                          {' — '}{obs.instant_resoumission}
                        </Text>
                      )}
                    </div>
                  )}
                />
              </List.Item>
            )}
          />
        </Card>
      )}

      {/* Actions greffier : Valider / Retourner / Rejeter */}
      {peutValider && enControleForme && (
        <Card title={t('detail.actions.titre')} style={{ marginBottom: 16 }}>
          <Space wrap>
            <Button type="primary" onClick={valider}>
              {t('detail.valider.bouton')}
            </Button>
            <Button icon={<UndoOutlined />} onClick={retourner}>
              {t('detail.retourner.bouton')}
            </Button>
            <Button danger onClick={rejeter}>
              {t('detail.rejeter.bouton')}
            </Button>
          </Space>
          <Paragraph style={{ marginTop: 12, marginBottom: 0 }}>
            <Text type="secondary">{t('detail.actions.note')}</Text>
          </Paragraph>
        </Card>
      )}

      {/* Action déclarant : Modifier et renvoyer après retour */}
      {estRetournee && estDeclarantProprietaire && (
        <Card
          title={(
            <Space>
              <ArrowRightOutlined style={{ color: 'var(--rim-vert)' }} />
              {t('detail.resoumettre.titre_section')}
            </Space>
          )}
          style={{ marginBottom: 16 }}
        >
          <Paragraph>{t('detail.resoumettre.aide_section')}</Paragraph>
          <Space>
            <Button type="primary" icon={<ArrowRightOutlined />} onClick={resoumettre}>
              {t('detail.resoumettre.bouton')}
            </Button>
          </Space>
        </Card>
      )}

      <Button onClick={() => navigate('/inscriptions')}>
        {t('detail.retour')}
      </Button>
    </div>
  );
}
