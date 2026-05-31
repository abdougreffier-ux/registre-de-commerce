import React from 'react';

/**
 * Carte de KPI institutionnel — surface blanche, accent latéral coloré,
 * icône, libellé, valeur, sous-libellé optionnel. Strictement conforme à
 * la palette officielle RIM (vert, rouge, jaune, blanc).
 */
export default function KpiCarte({
  icone, libelle, valeur, suffixe, hint, accent = 'vert',
}) {
  const classeAccent =
    accent === 'rouge' ? '--accent-rouge'
    : accent === 'jaune' ? '--accent-jaune'
    : '';
  return (
    <div className={`rim-kpi ${classeAccent}`.trim()}>
      {icone && <div className="rim-kpi__icone">{icone}</div>}
      <div className="rim-kpi__corps">
        <div className="rim-kpi__libelle">{libelle}</div>
        <div className="rim-kpi__valeur">
          {valeur}
          {suffixe && <span className="rim-kpi__suffixe"> {suffixe}</span>}
        </div>
        {hint && <div className="rim-kpi__hint">{hint}</div>}
      </div>
    </div>
  );
}
