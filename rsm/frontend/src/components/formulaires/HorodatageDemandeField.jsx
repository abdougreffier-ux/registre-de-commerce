/**
 * Affichage en lecture seule de l'horodatage courant pour les
 * formulaires d'inscription.
 *
 * Directive MO (2026-05-31) :
 *   - L'horodatage de la demande est généré AUTOMATIQUEMENT côté
 *     serveur (Inscription.instant_arrivee, ``timezone.now()``).
 *   - L'utilisateur ne peut ni saisir, ni modifier cette valeur.
 *   - L'UI doit afficher un retour visuel cohérent (date + heure +
 *     seconde à la précision indiquée par l'article 78).
 *
 * Ce composant n'envoie aucune valeur dans le payload : le backend
 * fait foi (instant_arrivee). Le tick frontend sert uniquement à
 * informer l'utilisateur que l'horodatage est suivi en temps réel.
 *
 * Format affiché : ``YYYY-MM-DD HH:MM:SS`` (précision seconde).
 */
import React, { useEffect, useState } from 'react';
import { Form, Input, Typography } from 'antd';
import { ClockCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

function formaterHorodatage(d) {
  if (!d) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} `
    + `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  );
}

/**
 * @param {object} props
 * @param {function} props.t   fonction i18n
 * @param {string} [props.label] libellé optionnel (sinon clé par défaut)
 * @param {string} [props.aide]  texte d'aide optionnel
 */
export default function HorodatageDemandeField({ t, label, aide }) {
  const [maintenant, setMaintenant] = useState(() => new Date());

  // Tick à la seconde — ré-aligné chaque tour sur l'horloge locale.
  useEffect(() => {
    const id = setInterval(() => setMaintenant(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <Form.Item
      label={label || t('formulaire.commun.horodatage_demande')}
      tooltip={aide || t('formulaire.commun.horodatage_demande_aide')}
    >
      <Input
        value={formaterHorodatage(maintenant)}
        readOnly
        prefix={<ClockCircleOutlined style={{ color: 'var(--gris-500)' }} />}
        style={{ background: 'var(--gris-50)', fontVariantNumeric: 'tabular-nums' }}
      />
      <Text type="secondary" style={{ fontSize: 11.5, marginTop: 4, display: 'block' }}>
        {t('formulaire.commun.horodatage_demande_legende')}
      </Text>
    </Form.Item>
  );
}
