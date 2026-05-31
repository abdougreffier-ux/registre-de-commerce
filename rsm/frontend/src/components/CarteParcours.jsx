import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Carte d'un parcours utilisateur (déposer, modifier, renouveler, …).
 *
 * Design strictement aligné sur la charte graphique RIM :
 *   - surface principale BLANCHE ;
 *   - liseré d'accent VERT (par défaut), ROUGE pour actions juridictionnelles,
 *     JAUNE pour signaux d'alerte ;
 *   - aucune couleur hors charte.
 *
 * Le composant ne porte aucune logique métier : il sert uniquement à
 * orienter l'utilisateur vers la route correspondante.
 */
export default function CarteParcours({
  to,
  icone,
  article,
  titre,
  description,
  cta,
  accent = 'vert', // 'vert' | 'rouge' | 'jaune'
}) {
  const classeAccent =
    accent === 'rouge' ? '--accent-rouge'
    : accent === 'jaune' ? '--accent-jaune'
    : '';
  return (
    <Link
      to={to}
      className={`rim-carte-parcours ${classeAccent}`.trim()}
      style={{ textDecoration: 'none', color: 'inherit' }}
    >
      <div className="rim-carte-parcours__icone">{icone}</div>
      {article && <div className="rim-carte-parcours__article">{article}</div>}
      <h3 className="rim-carte-parcours__titre">{titre}</h3>
      {description && (
        <p className="rim-carte-parcours__description">{description}</p>
      )}
      {cta && <span className="rim-carte-parcours__cta">{cta}</span>}
    </Link>
  );
}
