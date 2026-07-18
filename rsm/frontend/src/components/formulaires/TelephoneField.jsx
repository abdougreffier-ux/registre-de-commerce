/**
 * Composant partagé : saisie d'un numéro de téléphone en 2 parties :
 * indicatif pays (Select) + numéro local (Input).
 *
 * Directive MO (2026-07-08) :
 *   - Aucun indicatif n'est saisi manuellement.
 *   - Cas Mauritanie (+222) : 8 chiffres, commençant par 2, 3 ou 4.
 *   - Cas étranger : 6-15 chiffres numériques.
 *   - Stockage uniforme au format international ``+[code][numéro]``.
 *
 * Utilisation :
 *   <Form.Item name="telephone" label={t('...')} rules={reglesTelephone(t)}>
 *     <TelephoneField />
 *   </Form.Item>
 *
 * Le composant est CONTRÔLÉ par Form.Item : il accepte une valeur
 * concaténée en entrée et émet la même forme en sortie via onChange.
 * La validation stricte est déjà portée par ``reglesTelephone`` (regex
 * Mauritanie + regex générique international) — inchangée par ce composant.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { Input, Select, Space } from 'antd';
import { useTranslation } from 'react-i18next';

/**
 * Liste des indicatifs proposés. L'ordre place la Mauritanie en tête
 * (usage majoritaire), puis les pays limitrophes / Maghreb, puis les
 * pays fréquents en pratique commerciale.
 */
export const INDICATIFS_PAYS = [
  { code: '+222', cle: 'mr' },
  { code: '+221', cle: 'sn' },
  { code: '+223', cle: 'ml' },
  { code: '+212', cle: 'ma' },
  { code: '+213', cle: 'dz' },
  { code: '+216', cle: 'tn' },
  { code: '+20',  cle: 'eg' },
  { code: '+966', cle: 'sa' },
  { code: '+971', cle: 'ae' },
  { code: '+33',  cle: 'fr' },
  { code: '+34',  cle: 'es' },
  { code: '+44',  cle: 'gb' },
  { code: '+49',  cle: 'de' },
  { code: '+1',   cle: 'us_ca' },
];

/**
 * Parse une valeur concaténée `+[code][numéro]` en {code, local}.
 * Si la valeur ne commence par aucun indicatif connu, on retombe sur
 * Mauritanie et on considère la totalité comme numéro local.
 */
function parserTelephone(value) {
  const trimmed = String(value || '').replace(/\s/g, '');
  if (!trimmed || !trimmed.startsWith('+')) {
    return { code: '+222', local: trimmed.replace(/^\+/, '') };
  }
  // Trier par longueur décroissante pour matcher les indicatifs longs en premier.
  const tries = [...INDICATIFS_PAYS].sort((a, b) => b.code.length - a.code.length);
  for (const { code } of tries) {
    if (trimmed.startsWith(code)) {
      return { code, local: trimmed.slice(code.length) };
    }
  }
  return { code: '+222', local: trimmed.replace(/^\+/, '') };
}

/**
 * @param {object} props
 * @param {string} [props.value]       — valeur contrôlée (Form.Item)
 * @param {function} [props.onChange]  — émetteur (Form.Item)
 * @param {string} [props.placeholder] — placeholder du numéro local
 */
export default function TelephoneField({ value, onChange, placeholder }) {
  const { t } = useTranslation();

  const parsed = useMemo(() => parserTelephone(value), [value]);
  const [code, setCode] = useState(parsed.code);
  const [local, setLocal] = useState(parsed.local);

  // Synchronisation depuis Form.Item quand la valeur externe change.
  // (Volontairement pas de dépendance sur ``code`` / ``local`` internes
  // — on ne réagit qu'aux changements externes issus de la value contrôlée.)
  useEffect(() => {
    if (parsed.code !== code) setCode(parsed.code);
    if (parsed.local !== local) setLocal(parsed.local);
  }, [parsed.code, parsed.local]);  // dépendances externes uniquement

  const emettre = (nouveauCode, nouveauLocal) => {
    const nettoye = String(nouveauLocal || '').replace(/[^\d]/g, '');
    onChange?.(nettoye ? `${nouveauCode}${nettoye}` : '');
  };

  const options = INDICATIFS_PAYS.map(({ code: c, cle }) => ({
    value: c,
    label: `${c} ${t(`telephone.pays.${cle}`)}`,
  }));

  return (
    <Space.Compact style={{ width: '100%' }}>
      <Select
        value={code}
        showSearch
        optionFilterProp="label"
        style={{ width: 220, flex: '0 0 auto' }}
        onChange={(v) => { setCode(v); emettre(v, local); }}
        options={options}
        placeholder={t('telephone.indicatif_placeholder')}
      />
      <Input
        value={local}
        onChange={(e) => { setLocal(e.target.value); emettre(code, e.target.value); }}
        placeholder={placeholder || t('telephone.numero_placeholder')}
        style={{ flex: 1 }}
        inputMode="numeric"
      />
    </Space.Compact>
  );
}
