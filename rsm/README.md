# Registre des Sûretés Mobilières (RSM) — Mauritanie

Système informatique bilingue français / arabe, tenu par le Greffe du
Tribunal de commerce de Nouakchott, fondé sur le chapitre IV (articles 76
à 97) du décret 2021-033 relatif au Registre du commerce et des Sûretés
Mobilières.

**Référence unique contraignante** : TDR version 1.0 — Nouakchott 2026.

## Organisation du dépôt

```
rsm/
├── backend/    Django 4.2 + DRF + PostgreSQL
├── frontend/   React 18 + Ant Design + i18next (FR/AR + RTL)
└── docs/
    ├── L1_note_de_cadrage.md                 # cadrage initial (§ 8 TDR)
    ├── L2_index.md                           # index du livrable L2 (fonctionnel)
    ├── L2_1_formulaires_bilingues.md         # formulaires art. 85, 88, 91, 92, 96, 80
    ├── L2_2_regles_validation.md             # règles de validation article par article
    ├── L2_3_matrice_statuts_transitions.md   # statuts × transitions × messages système
    ├── L2_4_roles_operations.md              # matrice rôles × opérations (7 rôles)
    ├── L2_5_messages_systeme.md              # catalogue complet des messages système (~89 messages)
    ├── L2_6_scenarios_fonctionnels.md        # 8 scénarios fonctionnels bout-en-bout
    ├── L3_index.md                           # index du livrable L3 (technique)
    ├── L3_1_modele_donnees.md                # modèle de données consolidé
    ├── L3_2_architecture_modulaire.md        # architecture, flux, défense en profondeur
    ├── L3_3_horodatage_scellement.md         # politique horodatage/scellement (zones gelées)
    ├── L3_4_dictionnaire_api.md              # dictionnaire API (endpoints, serializers, exceptions)
    ├── L3_5_securite_integrite.md            # dispositifs de sécurité et d'intégrité (4 remparts)
    ├── L3_6_matrice_bilingue.md              # matrice de conformité bilingue FR/AR
    ├── L11_tracabilite_articles_76_97.md     # traçabilité article par article + risques
    └── fiches_mo/                            # fiches de décision MO pour les zones gelées
        ├── index.md                          # index du dossier
        ├── F1_glossaire_bilingue.md          # L11/A6 — Glossaire juridique bilingue
        ├── F2_authentification_forte.md      # L11/MFA — Authentification forte
        ├── F3_signature_electronique.md      # L11/A2 — Signature électronique art. 88
        ├── F4_charte_documentaire_certificats.md  # L11/A5 — Charte documentaire (art. 97)
        ├── F5_source_de_temps.md             # L11/horodatage — Source de temps (art. 78)
        ├── F6_scellement_cryptographique.md  # L11/A5 volet scellement (§ 6.3)
        ├── F7_distinction_horodatages.md     # A9 — Horodatage arrivée / saisie
        ├── F8_politique_indisponibilite.md   # A4 — Politique d'indisponibilité (§ 5.3)
        ├── F9_arrete_application.md          # A1 — Arrêté d'application (art. 8, 81, 84)
        ├── F10_duree_maximale.md             # A3 — Durée maximale d'inscription
        ├── F11_politique_tarifaire.md        # A7 — Politique tarifaire / paiement
        ├── F12_cahier_charges_art83.md       # A8 — Cahier des charges art. 83
        ├── F13_interconnexions_externes.md   # L11/interconnexions — RCCM + identité
        ├── F14_reutilisation_partie.md       # L11/parties_reutilisation — Diff art. 88
        └── comparatif_F1_F3_F4_F5.md         # Aide à la décision MO — nœud cardinal d'opposabilité
```

## Démarrage rapide (développement)

### Backend

```bash
cd backend
python -m venv venv && source venv/Scripts/activate   # Windows
pip install -r requirements.txt
cp .env.example .env                                  # ajuster si nécessaire
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm start
```

### Tâche d'expiration automatique

```bash
python manage.py expirer_inscriptions
```

À planifier quotidiennement en production.

### Registre des arbitrages MO en attente

```bash
python manage.py lister_arbitrages_mo
```

Produit `backend/tests/arbitrages_mo_en_attente.txt` — liste des tests
désactivés faute d'arbitrage, chacun référencé à L11 avec le
comportement attendu à l'activation.

## Zones gelées (en attente d'arbitrage)

1. Horodatage opposable (art. 78) — source de temps officielle.
2. Scellement cryptographique (art. 97, § 5.1 TDR) — HSM / PKI.
3. Signature électronique des parties (art. 88).
4. Certificats probants (art. 97) — rendu PDF signé bilingue.
5. Paiement électronique (art. 85).
6. Interconnexions externes (RCCM, identité numérique).
7. Authentification forte multi-facteurs.

Chaque zone gelée est signalée explicitement dans le code par un
commentaire `ZONE GELÉE` et par une levée d'avertissement à l'exécution.

## Règles non négociables

- **Pas d'invention fonctionnelle** : aucune fonction non prévue par le TDR.
- **Pas de simplification juridique** : aucune règle n'est assouplie.
- **Bilinguisme strict** : toute divergence FR/AR = non-conformité majeure.
- **Traçabilité totale** : toute action est consignée au journal d'audit
  inaltérable (append-only, chaîné).
- **Séparation stricte** : saisie et validation ne peuvent être exercées
  par le même acteur sur la même demande.

## Contact

Maître d'ouvrage : Tribunal de commerce de Nouakchott — Greffe du RSM.
