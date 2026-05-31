import React, { useState } from 'react';
import { Alert, Button, Card, Form, Input, Space, Typography } from 'antd';
import { LockOutlined, KeyOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import { formatMessageErreur } from '../api/client';

const { Title, Paragraph, Text } = Typography;

/**
 * Page de gestion autonome du mot de passe.
 *
 * Deux modes d'usage :
 *   1. **Changement forcé** — l'utilisateur est arrivé ici parce que
 *      ``mot_de_passe_initial = true`` (compte créé par l'admin avec
 *      mot de passe temporaire). Tant qu'il n'a pas changé son mot de
 *      passe, le ``Layout`` redirige toutes les routes ici.
 *   2. **Changement volontaire** — accès depuis le menu utilisateur ou
 *      depuis « Mon espace ». L'utilisateur conserve son accès courant
 *      après changement (rafraîchissement de la session via Django
 *      ``update_session_auth_hash``).
 *
 * Aucune entrée d'audit métier n'est produite (art. 79).
 */
export default function ChangerMotDePasse() {
  const { t } = useTranslation();
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form] = Form.useForm();
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState(null);
  const [succes, setSucces] = useState(false);

  const force = !!auth.motDePasseInitial;
  const destination = location.state?.apres || '/';

  if (!auth.authentifie) {
    return (
      <div>
        <Title level={2}>{t('mdp.titre')}</Title>
        <Alert
          type="info"
          showIcon
          message={t('mon_espace.connexion_requise.titre')}
          description={t('mon_espace.connexion_requise.description')}
        />
      </div>
    );
  }

  const onFinish = async (valeurs) => {
    setErreur(null);
    setSucces(false);
    setEnCours(true);
    try {
      await auth.changerMotDePasse(valeurs);
      setSucces(true);
      form.resetFields();
      // Si l'utilisateur sort du mode forcé, on le redirige vers sa page d'arrivée.
      if (force) {
        setTimeout(() => navigate(destination, { replace: true }), 1200);
      }
    } catch (e) {
      setErreur(formatMessageErreur(e, t));
    } finally {
      setEnCours(false);
    }
  };

  return (
    <div style={{ maxWidth: 520, margin: '24px auto' }}>
      <Title level={2}>{t('mdp.titre')}</Title>

      {force ? (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={t('mdp.force.titre')}
          description={t('mdp.force.description')}
        />
      ) : (
        <Paragraph>{t('mdp.introduction')}</Paragraph>
      )}

      <Card>
        <Form form={form} layout="vertical" onFinish={onFinish} autoComplete="off">
          <Form.Item
            name="ancien"
            label={t('mdp.champ.ancien')}
            rules={[{ required: true, message: t('formulaire.commun.requis') }]}
          >
            <Input.Password
              prefix={<KeyOutlined />}
              autoComplete="current-password"
            />
          </Form.Item>
          <Form.Item
            name="nouveau"
            label={t('mdp.champ.nouveau')}
            rules={[{ required: true, message: t('formulaire.commun.requis') }]}
            hasFeedback
          >
            <Input.Password
              prefix={<LockOutlined />}
              autoComplete="new-password"
            />
          </Form.Item>
          <Form.Item
            name="confirmation"
            label={t('mdp.champ.confirmation')}
            dependencies={['nouveau']}
            hasFeedback
            rules={[
              { required: true, message: t('formulaire.commun.requis') },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('nouveau') === value) return Promise.resolve();
                  return Promise.reject(new Error(t('mdp.erreur.confirmation_differente')));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              autoComplete="new-password"
            />
          </Form.Item>

          {erreur && <Alert type="error" message={erreur} style={{ marginBottom: 16 }} />}
          {succes && (
            <Alert
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
              message={t('mdp.succes.titre')}
              description={force ? t('mdp.succes.redirection') : t('mdp.succes.description')}
            />
          )}

          <Space>
            <Button type="primary" htmlType="submit" loading={enCours}>
              {t('mdp.bouton.valider')}
            </Button>
            {!force && (
              <Button onClick={() => navigate('/mon-espace')}>
                {t('detail.retour')}
              </Button>
            )}
          </Space>

          <Alert
            type="info"
            showIcon
            style={{ marginTop: 16 }}
            message={t('mdp.note.titre')}
            description={t('mdp.note.description')}
          />
        </Form>
      </Card>
    </div>
  );
}
