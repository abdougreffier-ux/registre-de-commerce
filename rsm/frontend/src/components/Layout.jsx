import React from 'react';
import { Layout, Menu, Button, Dropdown, Space, Tag } from 'antd';
import { UserOutlined, LogoutOutlined, LoginOutlined, KeyOutlined } from '@ant-design/icons';
import { Link, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import BandeauModeTest from './BandeauModeTest';
import EnTeteOfficiel from './EnTeteOfficiel';
import PiedDePageOfficiel from './PiedDePageOfficiel';
import { useAuth, aUnRole } from '../contexts/AuthContext';
import { LANGUES_DISPONIBLES } from '../i18n';

const { Content } = Layout;

/**
 * Gabarit principal — refonte UX/UI institutionnelle (mai 2026).
 *
 * Architecture verticale :
 *   1. Bandeau MODE TEST (filet rouge discret, affiché seulement en TEST).
 *   2. En-tête officiel COMPACT mono-ligne (~76 px, sceau + mentions).
 *   3. Barre de navigation applicative (sticky, aérée, max 1320 px).
 *   4. Conteneur principal centré (max 1320 px) avec avertissement
 *      « paramètres en attente » discret et les pages.
 *   5. Pied de page institutionnel (sobre, devise nationale).
 *
 * Garde-fous inviolables :
 *   - intégrité du registre (rien de logique métier ici) ;
 *   - traçabilité (toutes les actions remontent au backend) ;
 *   - parité juridique FR/AR (toute la couche d'affichage est i18n).
 */
export default function RsmLayout() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const auth = useAuth();

  const basculerLangue = () => {
    const autre = i18n.language === 'ar' ? 'fr' : 'ar';
    i18n.changeLanguage(autre);
  };

  const peutGreffer = aUnRole(auth, ['autorite_validation', 'agent_saisie', 'auditeur']);
  const peutAdminCat = aUnRole(auth, ['autorite_validation', 'admin_fonctionnel']);

  // Garde « mot de passe initial » : tant que ce drapeau est posé, l'usager
  // est redirigé vers la page de changement obligatoire — sauf s'il s'y
  // trouve déjà ou s'il est sur la page de connexion / déconnexion.
  const cheminsAutorisesMdpInitial = ['/changer-mot-de-passe', '/connexion'];
  const doitChangerMdp = auth.authentifie
    && auth.motDePasseInitial
    && !cheminsAutorisesMdpInitial.includes(location.pathname);

  const items = [
    { key: '/', label: <Link to="/">{t('menu.accueil')}</Link> },
    { key: '/recherche', label: <Link to="/recherche">{t('menu.recherche')}</Link> },
    auth.authentifie && {
      key: '/mon-espace',
      label: <Link to="/mon-espace">{t('menu.mon_espace')}</Link>,
    },
    peutGreffer && {
      key: '/tableau-de-bord-greffe',
      label: <Link to="/tableau-de-bord-greffe">{t('menu.tableau_greffe')}</Link>,
    },
    peutAdminCat && {
      key: '/admin/categories-biens',
      label: <Link to="/admin/categories-biens">{t('menu.categories_biens')}</Link>,
    },
    { key: '/inscriptions', label: <Link to="/inscriptions">{t('menu.inscriptions')}</Link> },
    { key: '/audit', label: <Link to="/audit">{t('menu.audit')}</Link> },
    { key: '/statistiques', label: <Link to="/statistiques">{t('menu.statistiques')}</Link> },
    { key: '/partenaires-bancaires', label: <Link to="/partenaires-bancaires">{t('menu.partenaires')}</Link> },
    {
      key: '/formulaires',
      label: t('menu.formulaires'),
      children: [
        { key: '/formulaires/inscription', label: <Link to="/formulaires/inscription">{t('menu.formulaire.inscription')}</Link> },
        { key: '/formulaires/modification', label: <Link to="/formulaires/modification">{t('menu.formulaire.modification')}</Link> },
        { key: '/formulaires/renouvellement', label: <Link to="/formulaires/renouvellement">{t('menu.formulaire.renouvellement')}</Link> },
        { key: '/formulaires/radiation', label: <Link to="/formulaires/radiation">{t('menu.formulaire.radiation')}</Link> },
      ],
    },
  ].filter(Boolean);

  const seDeconnecter = async () => {
    await auth.seDeconnecter();
    navigate('/');
  };

  const menuUtilisateur = {
    items: [
      {
        key: 'roles',
        label: (
          <div style={{ maxWidth: 280, whiteSpace: 'normal' }}>
            <div style={{ fontWeight: 600 }}>{t('auth.mes_roles')}</div>
            <div style={{ marginTop: 4 }}>
              {auth.roles.length === 0 ? (
                <span>{t('auth.aucun_role')}</span>
              ) : (
                <Space size={[4, 4]} wrap>
                  {auth.roles.map((r) => (
                    <Tag key={r} color="green">{r}</Tag>
                  ))}
                </Space>
              )}
            </div>
          </div>
        ),
      },
      { type: 'divider' },
      {
        key: 'changer-mot-de-passe',
        icon: <KeyOutlined />,
        label: <Link to="/changer-mot-de-passe">{t('mdp.lien_menu')}</Link>,
      },
      {
        key: 'deconnexion',
        icon: <LogoutOutlined />,
        label: t('auth.deconnexion'),
        onClick: seDeconnecter,
      },
    ],
  };

  const afficherConnexion = !auth.authentifie;

  if (doitChangerMdp) {
    return (
      <Navigate
        to="/changer-mot-de-passe"
        replace
        state={{ apres: location.pathname }}
      />
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: 'var(--gris-50)' }}>
      <BandeauModeTest />
      <EnTeteOfficiel />

      <div className="rim-menu">
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={items}
          style={{ flex: 1, minWidth: 0, borderBottom: 'none' }}
        />
        {afficherConnexion ? (
          <Button
            type="primary"
            icon={<LoginOutlined />}
            onClick={() => navigate('/connexion', { state: { apres: location.pathname } })}
          >
            {t('auth.connexion')}
          </Button>
        ) : (
          <Dropdown menu={menuUtilisateur} placement="bottomRight">
            <Button icon={<UserOutlined />}>
              {auth.utilisateur?.nom_affichage || auth.utilisateur?.username}
            </Button>
          </Dropdown>
        )}
        <Button onClick={basculerLangue} size="middle">
          {t('langue.basculer')}
        </Button>
      </div>

      <Content>
        <div className="rim-conteneur">
          <div className="rim-bandeau-attente" role="note">
            <span className="rim-bandeau-attente__pastille" aria-hidden="true" />
            <div>
              <span className="rim-bandeau-attente__titre">
                {t('avertissement.parametres_en_attente.titre')}
              </span>
              <span>{t('avertissement.parametres_en_attente.introduction_breve')}</span>
            </div>
          </div>
          <Outlet />
        </div>
      </Content>

      <PiedDePageOfficiel />
    </Layout>
  );
}

export { LANGUES_DISPONIBLES };
