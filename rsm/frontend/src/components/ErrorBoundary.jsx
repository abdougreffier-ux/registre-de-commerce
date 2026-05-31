import React from 'react';
import { Button, Result } from 'antd';
import { withTranslation } from 'react-i18next';

/**
 * Garde-fou global contre toute erreur React non capturée.
 *
 * Capture toute exception non gérée et affiche un écran neutre bilingue
 * avec un bouton de retour à l'accueil. Indépendant du régime juridique.
 */
class ErrorBoundaryBase extends React.Component {
  constructor(props) {
    super(props);
    this.state = { erreur: null };
  }

  static getDerivedStateFromError(erreur) {
    return { erreur };
  }

  componentDidCatch(erreur, info) {
    // eslint-disable-next-line no-console
    console.error('[RSM] Erreur React interceptée :', erreur, info);
  }

  reinitialiser = () => {
    this.setState({ erreur: null });
    if (typeof window !== 'undefined') {
      window.location.assign('/');
    }
  };

  render() {
    const { t, children } = this.props;
    if (!this.state.erreur) return children;
    return (
      <Result
        status="error"
        title={t('erreur_fatale.titre')}
        subTitle={t('erreur_fatale.sous_titre')}
        extra={
          <Button type="primary" onClick={this.reinitialiser}>
            {t('erreur_fatale.retour_accueil')}
          </Button>
        }
      />
    );
  }
}

export default withTranslation()(ErrorBoundaryBase);
