import React from 'react';

/**
 * Sceau officiel de la République Islamique de Mauritanie.
 *
 * ⚠️ Intangibilité (charte graphique, mai 2020, p. 13) :
 * « Il n'est en aucun cas autorisé de modifier la forme et les
 * dimensions du sceau ».
 *
 * Ce composant se limite à restituer le fichier officiel déposé dans
 * ``public/assets/sceau_officiel.{jpg|png|svg}``. Aucune retouche
 * colorimétrique, aucun filtre, aucun recadrage. Le conteneur conserve
 * un rapport 1:1 strict (carré) pour préserver les proportions natives
 * du sceau circulaire.
 */
export default function SceauOfficiel({ taille = 96, titre = 'Sceau de la République Islamique de Mauritanie' }) {
  const sources = [
    '/assets/sceau_officiel.svg',
    '/assets/sceau_officiel.png',
    '/assets/sceau_officiel.jpg',
  ];

  const [index, setIndex] = React.useState(0);

  return (
    <div
      style={{
        width: taille,
        height: taille,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <img
        src={sources[index]}
        alt={titre}
        title={titre}
        onError={() => {
          if (index < sources.length - 1) setIndex(index + 1);
        }}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          display: 'block',
        }}
      />
    </div>
  );
}
