import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Button, Card, Descriptions, Modal, Select, Space, Spin, Typography,
} from 'antd';
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

      {peutValider && enControleForme && (
        <Card title={t('detail.actions.titre')} style={{ marginBottom: 16 }}>
          <Space>
            <Button type="primary" onClick={valider}>
              {t('detail.valider.bouton')}
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

      <Button onClick={() => navigate('/inscriptions')}>
        {t('detail.retour')}
      </Button>
    </div>
  );
}
