import React, { useState } from 'react';
import {
  Alert, Button, Modal, Space, Typography,
} from 'antd';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';

import { useAuth, aUnRole } from '../contexts/AuthContext';

const { Paragraph } = Typography;

/**
 * Encart procédural / bouton de soumission conditionnel.
 *
 * - Si l'utilisateur est authentifié et porte l'un des rôles requis
 *   (par défaut : ``agent_saisie`` ou ``declarant_externe``), un bouton
 *   « Soumettre la demande » est activé et appelle la fonction
 *   ``onSoumettre(valeurs)`` fournie par le formulaire parent
 *   (le parent reste responsable de composer le payload et d'appeler
 *   l'endpoint métier protégé).
 * - Sinon, un bandeau procédural rappelle les voies officielles de dépôt
 *   (TDR § 4.1, art. 78) et propose un bouton de navigation vers la
 *   page ``/connexion``.
 *
 * Ce composant ne modifie aucune règle métier : il module uniquement la
 * visibilité et l'activation du bouton selon l'état d'authentification.
 */
export default function ProcedureDepot({
  canalRef,
  onSoumettre,
  enCours = false,
  rolesRequis = ['agent_saisie', 'declarant_externe'],
}) {
  const { t } = useTranslation();
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [soumissionEnCours, setSoumissionEnCours] = useState(false);

  const peutSoumettre = aUnRole(auth, rolesRequis);

  const ouvrirProcedure = () => {
    Modal.info({
      title: t('procedure.titre'),
      width: 620,
      content: (
        <Space direction="vertical" size={12}>
          <Paragraph style={{ marginBottom: 0 }}>
            {t('procedure.resume', { ref: canalRef })}
          </Paragraph>
          <Paragraph style={{ marginBottom: 0 }}>
            <strong>{t('procedure.voies.titre')}</strong>
          </Paragraph>
          <ul style={{ margin: 0, paddingInlineStart: 20 }}>
            <li>{t('procedure.voies.guichet')}</li>
            <li>{t('procedure.voies.portail')}</li>
          </ul>
          <Paragraph style={{ marginBottom: 0 }}>
            {t('procedure.reserve_mo')}
          </Paragraph>
        </Space>
      ),
      okText: t('soumission.fermer'),
    });
  };

  const allerConnexion = () => {
    navigate('/connexion', { state: { apres: location.pathname } });
  };

  // ---------- CAS 1 : utilisateur autorisé → bouton actif ------------------
  if (peutSoumettre && typeof onSoumettre === 'function') {
    return (
      <Space direction="vertical" style={{ width: '100%' }} size={12}>
        <Alert
          type="success"
          showIcon
          message={t('procedure.ok.titre')}
          description={t('procedure.ok.description', {
            roles: auth.roles.join(', '),
          })}
        />
        <Space>
          <Button
            type="primary"
            loading={enCours || soumissionEnCours}
            onClick={async () => {
              setSoumissionEnCours(true);
              try { await onSoumettre(); }
              finally { setSoumissionEnCours(false); }
            }}
          >
            {t('formulaire.commun.soumettre')}
          </Button>
          <Button type="default" onClick={ouvrirProcedure}>
            {t('procedure.bouton_voir')}
          </Button>
        </Space>
      </Space>
    );
  }

  // ---------- CAS 2 : utilisateur non authentifié ou rôle absent ----------
  const messageBandeau = auth.authentifie
    ? t('procedure.bandeau.description_sans_role', { ref: canalRef })
    : t('procedure.bandeau.description', { ref: canalRef });

  return (
    <Space direction="vertical" style={{ width: '100%' }} size={12}>
      <Alert
        type="warning"
        showIcon
        message={t('procedure.bandeau.titre')}
        description={messageBandeau}
      />
      <Space wrap>
        <Button type="primary" disabled>
          {t('procedure.bouton_desactive')}
        </Button>
        {!auth.authentifie && (
          <Button type="default" onClick={allerConnexion}>
            {t('auth.connexion')}
          </Button>
        )}
        <Button type="default" onClick={ouvrirProcedure}>
          {t('procedure.bouton_voir')}
        </Button>
      </Space>
    </Space>
  );
}
