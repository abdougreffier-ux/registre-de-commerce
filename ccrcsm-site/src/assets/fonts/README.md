# Polices auto-hébergées

Les fichiers suivants doivent être placés ici avant la mise en production :

- `inter-var.woff2` — Inter Variable (latin étendu)
  - Source : https://github.com/rsms/inter
  - Licence : SIL Open Font License 1.1
- `noto-naskh-arabic-var.woff2` — Noto Naskh Arabic Variable (arabe)
  - Source : https://fonts.google.com/noto/specimen/Noto+Naskh+Arabic
  - Licence : SIL Open Font License 1.1

## Subset recommandé

Utiliser `pyftsubset` pour produire des versions allégées :

```bash
# Inter — latin + latin étendu + ponctuation
pyftsubset Inter-Var.ttf \
  --unicodes="U+0020-007E,U+00A0-00FF,U+0100-017F,U+2010-2019,U+2022" \
  --flavor=woff2 --output-file=inter-var.woff2

# Noto Naskh Arabic — arabe + diacritiques + chiffres
pyftsubset NotoNaskhArabic-Var.ttf \
  --unicodes="U+0600-06FF,U+0750-077F,U+FB50-FDFF,U+FE70-FEFF,U+0020-007E" \
  --flavor=woff2 --output-file=noto-naskh-arabic-var.woff2
```

Les déclarations `@font-face` se trouvent dans [`../css/main.css`](../css/main.css) (section à
ajouter au moment de l'installation effective des polices) ou, mieux, dans un fichier dédié
`fonts.css` pré-chargé.

## Déclarations @font-face à ajouter à main.css

```css
@font-face {
  font-family: "Inter";
  src: url("/assets/fonts/inter-var.woff2") format("woff2-variations"),
       url("/assets/fonts/inter-var.woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Noto Naskh Arabic";
  src: url("/assets/fonts/noto-naskh-arabic-var.woff2") format("woff2-variations"),
       url("/assets/fonts/noto-naskh-arabic-var.woff2") format("woff2");
  font-weight: 400 700;
  font-style: normal;
  font-display: swap;
  unicode-range: U+0600-06FF, U+0750-077F, U+FB50-FDFF, U+FE70-FEFF;
}
```

En l'absence de ces fichiers, le navigateur utilisera les polices de repli définies dans les
variables `--font-sans-latin` et `--font-sans-arabic` de [`../css/main.css`](../css/main.css).
