import React from 'react';
import { Button, Space } from 'antd';
import {
  FileAddOutlined, EditOutlined, ReloadOutlined, StopOutlined,
  SearchOutlined, AuditOutlined, BookOutlined, SafetyCertificateOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import CarteParcours from '../components/CarteParcours';
import { useAuth, aUnRole } from '../contexts/AuthContext';

/**
 * Page d'accueil — landing institutionnel.
 *
 * Hiérarchie visuelle (charte RIM, palette : vert / rouge / jaune / blanc) :
 *   1. HERO institutionnel (surtitre, accroche, CTA principaux).
 *   2. PARCOURS USAGER — 4 cartes (dépôt, modification, renouvellement, radiation).
 *   3. PARCOURS PUBLIC — recherche & journal d'audit (auditeur).
 *   4. ESPACE GREFFIER — affiché uniquement si l'utilisateur dispose du
 *      rôle ``autorite_validation`` (TDR § 4.1).
 *
 * Aucune règle métier dans cette page. Aucune couleur hors charte.
 */
export default function Accueil() {
  const { t } = useTranslation();
  const auth = useAuth();
  const estGreffier = aUnRole(auth, ['autorite_validation']);
  const estAuditeur = aUnRole(auth, ['auditeur']);

  return (
    <div>
      {/* ------------------------------------------------------------ */}
      {/* HERO INSTITUTIONNEL                                          */}
      {/* ------------------------------------------------------------ */}
      <section className="rim-hero">
        <span className="rim-hero__surtitre">
          {t('accueil.hero.surtitre')}
        </span>
        <h1 className="rim-hero__titre">
          {t('accueil.hero.titre.avant')}{' '}
          <strong>{t('accueil.hero.titre.fort')}</strong>
        </h1>
        <p className="rim-hero__sous-titre">{t('accueil.hero.description')}</p>
        <div className="rim-hero__cta">
          <Link to="/recherche">
            <Button type="primary" size="large" icon={<SearchOutlined />}>
              {t('accueil.hero.cta_recherche')}
            </Button>
          </Link>
          {!auth.authentifie && (
            <Link to="/connexion">
              <Button size="large">
                {t('accueil.hero.cta_connexion')}
              </Button>
            </Link>
          )}
          {auth.authentifie && (
            <Link to="/formulaires/inscription">
              <Button size="large">
                {t('accueil.hero.cta_deposer')}
              </Button>
            </Link>
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------ */}
      {/* PARCOURS USAGER — 4 cartes principales                       */}
      {/* ------------------------------------------------------------ */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <div>
            <h2 className="rim-section__titre">
              {t('accueil.parcours.titre')}
            </h2>
            <p className="rim-section__sous-titre">
              {t('accueil.parcours.sous_titre')}
            </p>
          </div>
        </div>

        <div className="rim-parcours-grille">
          <CarteParcours
            to="/formulaires/inscription"
            icone={<FileAddOutlined />}
            article={t('accueil.parcours.inscription.article')}
            titre={t('accueil.parcours.inscription.titre')}
            description={t('accueil.parcours.inscription.description')}
            cta={t('accueil.parcours.acceder')}
          />
          <CarteParcours
            to="/formulaires/modification"
            icone={<EditOutlined />}
            article={t('accueil.parcours.modification.article')}
            titre={t('accueil.parcours.modification.titre')}
            description={t('accueil.parcours.modification.description')}
            cta={t('accueil.parcours.acceder')}
          />
          <CarteParcours
            to="/formulaires/renouvellement"
            icone={<ReloadOutlined />}
            article={t('accueil.parcours.renouvellement.article')}
            titre={t('accueil.parcours.renouvellement.titre')}
            description={t('accueil.parcours.renouvellement.description')}
            cta={t('accueil.parcours.acceder')}
          />
          <CarteParcours
            to="/formulaires/radiation"
            icone={<StopOutlined />}
            article={t('accueil.parcours.radiation.article')}
            titre={t('accueil.parcours.radiation.titre')}
            description={t('accueil.parcours.radiation.description')}
            cta={t('accueil.parcours.acceder')}
            accent="rouge"
          />
        </div>
      </section>

      {/* ------------------------------------------------------------ */}
      {/* PARCOURS PUBLIC                                              */}
      {/* ------------------------------------------------------------ */}
      <section className="rim-section">
        <div className="rim-section__entete">
          <div>
            <h2 className="rim-section__titre">
              {t('accueil.public.titre')}
            </h2>
            <p className="rim-section__sous-titre">
              {t('accueil.public.sous_titre')}
            </p>
          </div>
        </div>
        <div className="rim-parcours-grille">
          <CarteParcours
            to="/recherche"
            icone={<SearchOutlined />}
            article={t('accueil.public.recherche.article')}
            titre={t('accueil.public.recherche.titre')}
            description={t('accueil.public.recherche.description')}
            cta={t('accueil.public.recherche.cta')}
          />
          <CarteParcours
            to="/inscriptions"
            icone={<BookOutlined />}
            article={t('accueil.public.liste.article')}
            titre={t('accueil.public.liste.titre')}
            description={t('accueil.public.liste.description')}
            cta={t('accueil.public.liste.cta')}
            accent="jaune"
          />
        </div>
      </section>

      {/* ------------------------------------------------------------ */}
      {/* ESPACE GREFFIER — visible uniquement si rôle ad hoc          */}
      {/* ------------------------------------------------------------ */}
      {estGreffier && (
        <section className="rim-section">
          <div className="rim-section__entete">
            <div>
              <h2 className="rim-section__titre --rouge">
                {t('accueil.greffier.titre')}
              </h2>
              <p className="rim-section__sous-titre">
                {t('accueil.greffier.sous_titre')}
              </p>
            </div>
          </div>
          <div className="rim-bloc-greffier">
            <div className="rim-bloc-greffier__titre">
              {t('accueil.greffier.bloc_titre')}
            </div>
            <p style={{ margin: '0 0 12px', color: 'var(--rim-texte-doux)' }}>
              {t('accueil.greffier.bloc_description')}
            </p>
            <Space wrap>
              <Link to="/inscriptions">
                <Button type="primary" icon={<SafetyCertificateOutlined />}>
                  {t('accueil.greffier.bouton_traiter')}
                </Button>
              </Link>
              {estAuditeur && (
                <Link to="/audit">
                  <Button icon={<AuditOutlined />}>
                    {t('accueil.greffier.bouton_audit')}
                  </Button>
                </Link>
              )}
            </Space>
          </div>
        </section>
      )}

      {/* ------------------------------------------------------------ */}
      {/* JOURNAL D'AUDIT — visible si auditeur                        */}
      {/* ------------------------------------------------------------ */}
      {estAuditeur && !estGreffier && (
        <section className="rim-section">
          <div className="rim-section__entete">
            <div>
              <h2 className="rim-section__titre --rouge">
                {t('accueil.audit.titre')}
              </h2>
              <p className="rim-section__sous-titre">
                {t('accueil.audit.sous_titre')}
              </p>
            </div>
          </div>
          <div className="rim-bloc-greffier">
            <p style={{ margin: '0 0 12px' }}>
              {t('accueil.audit.description')}
            </p>
            <Link to="/audit">
              <Button type="primary" icon={<AuditOutlined />}>
                {t('accueil.audit.bouton')}
              </Button>
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
