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
 * Longueur maximale AUTORISÉE À LA SAISIE (chiffres) selon l'indicatif.
 * Directive MO (2026-07-08) : contrainte stricte pour la Mauritanie ;
 * flexible pour les pays étrangers (borne haute générique 15 chiffres).
 */
export const LONGUEUR_MAX_PAR_CODE = {
  '+222': 8,   // Mauritanie : exactement 8 chiffres, préfixe 2/3/4.
  '+221': 9,   // Sénégal : 9 chiffres.
  '+223': 8,   // Mali : 8 chiffres.
  '+212': 9,   // Maroc.
  '+213': 9,   // Algérie.
  '+216': 8,   // Tunisie.
  '+20':  10,  // Égypte.
  '+966': 9,   // Arabie Saoudite.
  '+971': 9,   // ÉAU.
  '+33':  9,   // France (sans le 0).
  '+34':  9,   // Espagne.
  '+44':  10,  // Royaume-Uni.
  '+49':  11,  // Allemagne.
  '+1':   10,  // États-Unis / Canada.
};

/** Longueur de secours (max international UIT-T E.164 : 15 chiffres). */
const LONGUEUR_MAX_DEFAUT = 15;

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

  // Longueur maximale (chiffres) selon l'indicatif courant.
  const maxDigits = LONGUEUR_MAX_PAR_CODE[code] ?? LONGUEUR_MAX_DEFAUT;

  const nettoyerEtBorner = (brut, longueurMax) => {
    return String(brut || '')
      .replace(/[^\d]/g, '')   // supprime tout caractère non numérique
      .slice(0, longueurMax);  // tronque à la longueur maximale autorisée
  };

  const emettre = (nouveauCode, nouveauLocal) => {
    const nettoye = nettoyerEtBorner(
      nouveauLocal,
      LONGUEUR_MAX_PAR_CODE[nouveauCode] ?? LONGUEUR_MAX_DEFAUT,
    );
    onChange?.(nettoye ? `${nouveauCode}${nettoye}` : '');
  };

  // Quand l'indicatif change, on retronque le numéro local si nécessaire
  // (ex. passage +33 → +222 : on garde au plus 8 chiffres).
  const onChangeIndicatif = (nouveauCode) => {
    const longueurCible = LONGUEUR_MAX_PAR_CODE[nouveauCode] ?? LONGUEUR_MAX_DEFAUT;
    const localTronque = nettoyerEtBorner(local, longueurCible);
    setCode(nouveauCode);
    setLocal(localTronque);
    emettre(nouveauCode, localTronque);
  };

  const onChangeNumero = (e) => {
    // Filtre non-numérique + borne max en temps réel : la saisie n'accepte
    // physiquement pas de caractère au-delà de la limite du pays choisi.
    const propre = nettoyerEtBorner(e.target.value, maxDigits);
    setLocal(propre);
    emettre(code, propre);
  };

  const onKeyDownNumero = (e) => {
    // Blocage clavier : refuser tout caractère non chiffre en dehors des
    // touches de contrôle (Backspace, arrows, Tab, etc.).
    const controle = [
      'Backspace', 'Delete', 'Tab', 'Enter', 'Escape',
      'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
      'Home', 'End',
    ];
    if (controle.includes(e.key)) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return; // laisse Ctrl+C/V/A
    if (!/^\d$/.test(e.key)) e.preventDefault();
  };

  const onPasteNumero = (e) => {
    // Coller : on assainit le presse-papier avant insertion.
    e.preventDefault();
    const colle = (e.clipboardData || window.clipboardData).getData('text');
    const propre = nettoyerEtBorner(local + colle, maxDigits);
    setLocal(propre);
    emettre(code, propre);
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
        onChange={onChangeIndicatif}
        options={options}
        placeholder={t('telephone.indicatif_placeholder')}
      />
      <Input
        value={local}
        onChange={onChangeNumero}
        onKeyDown={onKeyDownNumero}
        onPaste={onPasteNumero}
        placeholder={placeholder || t('telephone.numero_placeholder')}
        style={{ flex: 1 }}
        inputMode="numeric"
        maxLength={maxDigits}
      />
    </Space.Compact>
  );
}
