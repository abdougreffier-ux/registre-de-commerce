# Actifs officiels RIM — charte graphique (mai 2020)

Ce dossier accueille les actifs graphiques officiels de la République
Islamique de Mauritanie. **Aucun de ces fichiers n'est redistribué
dans le dépôt** : ils doivent être téléchargés depuis la plateforme
officielle `https://kennach.gov.mr` et déposés ici, conformément aux
règles de propriété intellectuelle et d'intangibilité des symboles
nationaux.

## Fichiers attendus

```
public/assets/
├── sceau_officiel.svg            # Sceau de la République Islamique de Mauritanie
└── fonts/
    ├── Mauritanie.woff2          # Police « Mauritanie »
    ├── Mauritanie.woff
    ├── Ouguiya-Regular.woff2     # Police « Ouguiya » — textes FR
    ├── Ouguiya-Regular.woff
    ├── Ouguiya-Bold.woff2
    ├── Ouguiya-Bold.woff
    ├── Louguiya-Regular.woff2    # Police « Louguiya » — textes AR et titres
    ├── Louguiya-Regular.woff
    ├── Louguiya-Bold.woff2
    └── Louguiya-Bold.woff
```

## Comportement en l'absence des fichiers officiels

- **Sceau** : un emplacement circulaire neutre aux couleurs officielles
  (rouge/jaune/blanc) est rendu par `SceauOfficiel.jsx`, avec la mention
  « Sceau à téléverser ». **Aucune reproduction stylisée du sceau
  officiel** n'est dessinée, conformément à l'interdiction posée par la
  charte (p. 13).
- **Polices** : les empilements de secours définis dans `charte.css`
  s'appliquent (Segoe UI / Arial / Noto Naskh Arabic / Amiri). Couleurs
  et mises en page restent strictement conformes ; seule la physionomie
  typographique exacte des polices officielles est approximée.

## Pourquoi ne sont-ils pas commités ?

Les symboles nationaux et les polices officielles relèvent de la
souveraineté institutionnelle. Leur diffusion est encadrée par la
plateforme `kennach.gov.mr`. Pour assurer la conformité et la
traçabilité, le téléchargement doit s'opérer à partir de la plateforme
officielle, par la personne habilitée, et faire l'objet d'une entrée
dans le registre L11.
