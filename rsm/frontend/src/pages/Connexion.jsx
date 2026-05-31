import React, { useState } from 'react';
import {
  Alert, Button, Card, Form, Input, Space, Typography,
} from 'antd';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import { formatMessageErreur } from '../api/client';

const { Title, Paragraph } = Typography;

/**
 * Page de connexion applicative — session Django / DRF.
 *
 * Ce formulaire est la seule porte d'entrée pour les rôles applicatifs
 * (TDR § 4.1). Aucun stockage local de mot de passe n'est effectué :
 * seule la session Django (cookie ``sessionid``) fait foi.
 *
 * Les fiches F2 (authentification forte) et F3 (signature électronique)
 * restent en attente des paramètres techniques ; lorsqu'elles seront
 * transmises, cette page s'enrichira sans modification du parcours
 * fonctionnel.
 */
export default function Connexion() {
  const { t } = useTranslation();
  const { seConnecter, authentifie } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [erreur, setErreur] = useState(null);
  const [enCours, setEnCours] = useState(false);

  const destination = location.state?.apres || '/';

  if (authentifie) {
    navigate(destination, { replace: true });
  }

  const onFinish = async (valeurs) => {
    setErreur(null);
    setEnCours(true);
    try {
      const rep = await seConnecter(valeurs);
      if (rep.ok) {
        navigate(destination, { replace: true });
      } else {
        setErreur(t('connexion.erreur.echec'));
      }
    } catch (e) {
      setErreur(formatMessageErreur(e, t));
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div style={{ maxWidth: 460, margin: '24px auto' }}>
      <Title level={2}>{t('connexion.titre')}</Title>
      <Paragraph>{t('connexion.introduction')}</Paragraph>

      <Card>
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item
            name="username"
            label={t('connexion.champ.identifiant')}
            rules={[{ required: true, message: t('formulaire.commun.requis') }]}
          >
            <Input autoComplete="username" />
          </Form.Item>
          <Form.Item
            name="password"
            label={t('connexion.champ.motdepasse')}
            rules={[{ required: true, message: t('formulaire.commun.requis') }]}
          >
            <Input.Password autoComplete="current-password" />
          </Form.Item>

          {erreur && (
            <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />
          )}

          <Space>
            <Button type="primary" htmlType="submit" loading={enCours}>
              {t('connexion.bouton.se_connecter')}
            </Button>
          </Space>

          <Alert
            type="info"
            showIcon
            style={{ marginTop: 16 }}
            message={t('connexion.note.f2.titre')}
            description={t('connexion.note.f2.description')}
          />
        </Form>
      </Card>
    </div>
  );
}
