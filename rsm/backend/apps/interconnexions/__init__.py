"""
Interopérabilité du RSM avec des partenaires externes (banques,
microfinance, IFI, …).

⚠️ Cette application n'expose AUCUN endpoint HTTP de production tant
que l'arbitrage MO de la fiche F15 n'a pas été rendu (cf.
``docs/L11_decisions_mo/note_interoperabilite_bancaire.md`` et
``docs/fiches_mo/F15_interoperabilite_banques.md``).

Les modèles ci-dessous matérialisent la prévision architecturale :
table d'agrément des partenaires, registre des consentements,
journal d'accès append-only. Aucune logique d'authentification, de
recherche ou de dépôt par API n'est câblée à ce stade.
"""
