# L1 — Note de cadrage

**Projet** : Système informatique du Registre des Sûretés Mobilières (RSM)
**Maître d'ouvrage** : Tribunal de commerce de Nouakchott — Greffe du RSM
**Cadre légal** : Chapitre IV (articles 76 à 97) du décret 2021-033 relatif au Registre du commerce et des Sûretés Mobilières.
**Référence contraignante** : TDR version 1.0, Nouakchott 2026.
**État de la note** : version initiale — amorce produite en parallèle du démarrage du développement, dans le périmètre explicitement autorisé par le maître d'ouvrage.

---

## 1. Compréhension du besoin

Le RSM est un **registre officiel à valeur juridique** ayant pour finalités (art. 76) :

- la **publicité** des sûretés mobilières et des droits dont l'inscription est légalement requise ;
- leur **pleine opposabilité aux tiers**.

Il est **entièrement informatisé** (art. 77). Sa base de données est logiquement décomposée en :

- un **fichier public** (inscriptions en cours de validité) ;
- un **fichier général** (ensemble des informations actuelles et conservées).

L'article 79 impose la **conservation pérenne** : aucune information régulièrement enregistrée ne peut être supprimée.

## 2. Principes directeurs (§ 1.3 du TDR)

1. **Validité juridique** — chaque fonction repose sur une disposition explicite du texte.
2. **Opposabilité** — la prise d'effet est déterminée par l'horodatage de saisie dans la base.
3. **Chronologie** — ordre strict d'arrivée des demandes.
4. **Intégrité** — aucune altération silencieuse ; toute modification est tracée.
5. **Preuve** — les certificats produits sont admissibles en justice.

## 3. Architecture retenue

### 3.1 Stack

- **Backend** : Django 4.2 LTS + Django REST Framework, PostgreSQL 14+.
- **Frontend** : React 18 + Ant Design + i18next + react-router.
- **Génération documentaire** : reportlab + arabic-reshaper + python-bidi (structurels).
- **Exploitation** : gunicorn + nginx (à confirmer par l'exploitant).

Justification au regard du TDR :

- non-captivité technologique, code intégralement cessible (art. 83, § 6.3) ;
- cohérence avec l'écosystème du Tribunal de commerce (projet RCCM voisin
  repose sur la même base technologique) ;
- i18n natif robuste pour le bilinguisme strict FR/AR (§ 7) ;
- support PostgreSQL des triggers, contraintes et index nécessaires à
  l'inaltérabilité du journal d'audit (§ 5.2).

### 3.2 Séparation des responsabilités (§ 6.2, § 4.1)

Modules logiques indépendants :

| Couche | Rôle |
|--------|------|
| Noyau du Registre (PostgreSQL) | Stockage unique, fichier public + fichier général. |
| Moteur d'horodatage (`apps.core.horodatage`) | Produit le numéro d'ordre horodaté (art. 78). **Mode STUB.** |
| Moteur de workflow (`apps.workflow`) | Statuts et transitions (§ 4.3). |
| Moteur de règles de validation (`apps.*.services`) | Règles art. 80, 85, 88, 91, 92. |
| Module de scellement (`apps.core.scellement`) | Empreintes cryptographiques. **Mode STUB.** |
| Journal d'audit (`apps.audit`) | Append-only, chaîné, protégé par triggers PostgreSQL. |
| Module de recherche (`apps.recherche`) | Règle des deux critères, portée fichier public (art. 94-97). |
| Module de rôles (`apps.utilisateurs`) | 7 rôles applicatifs § 4.1, séparation stricte. |
| Module de certificats (`apps.certificats`) | Structure + aperçu non opposable (art. 97). **Gelé.** |
| Module de statistiques (`apps.statistiques`) | Monopole du greffe (art. 82). |

### 3.3 Bilinguisme (§ 7)

Principes implémentés :

- **Une seule** logique métier, **un seul** modèle de données.
- Champs catégorisés en **neutres linguistiquement** (identités, numéros,
  dates, montants) vs **multilingues** (descriptions libres, motifs de
  refus). Voir `apps.core.models.Bilingue` et `DescriptionBilingue`.
- Référentiels gérés par l'administrateur fonctionnel : types de droits,
  motifs de rejet, critères de recherche, types de certificats.
- Direction d'écriture (LTR/RTL) pilotée par la langue active, sans
  duplication ni logique spécifique par composant.
- Journal d'audit indépendant de la langue (§ 7.6).

## 4. Chantier ouvert — périmètre du développement déjà engagé

Conformément à l'autorisation explicite du MO, les composants suivants
sont en cours de développement :

- modèle de données métier complet (parties, biens, inscriptions,
  modifications, renouvellements, radiations) ;
- machine d'états et transitions (§ 4.3) ;
- moteur de workflow et traçabilité logique ;
- structure des rôles et habilitations (sans authentification finale) ;
- support structurel du bilinguisme FR/AR ;
- interfaces fonctionnelles (saisie, contrôle, recherche, consultation)
  hors mécanismes de signature, scellement et paiement.

## 5. Zones gelées — signalées dans le code et la documentation

| Zone | Localisation | Statut |
|------|--------------|--------|
| Horodatage opposable | `apps.core.horodatage` (mode `local_stub`) | GELÉ — arbitrage source de temps à tenir |
| Scellement cryptographique | `apps.core.scellement` (mode `disabled`) | GELÉ — arbitrage HSM/PKI à tenir |
| Signature électronique | `apps.modifications.DemandeModification.accord_*` | GELÉ — régime art. 88 à préciser |
| Certificats probants (art. 97) | `apps.certificats.services.preparer_certificat` | GELÉ — rendu stub non opposable |
| Paiement électronique | non démarré | GELÉ |
| Interconnexions externes (RCCM, identité nationale) | non démarré | GELÉ |
| Authentification forte / MFA | `AUTH_USER_MODEL` structurel uniquement | GELÉ |

Chacune de ces zones est accompagnée, dans le code, d'un commentaire `ZONE GELÉE` et d'une levée d'avertissement Python à l'exécution.

## 6. Points de droit encore ouverts (signalés au TDR)

- A1. Arrêté d'application art. 8, 81, 84 — procédure dématérialisée.
- A2. Régime de signature électronique pour le canal électronique.
- A3. Durée maximale d'inscription — non plafonnée par le texte.
- A4. Politique d'indisponibilité et rang chronologique.
- A5. Articulation art. 94 (retrait copie / certificat négatif ou
  affirmatif) ↔ art. 97 (certificat de recherche).
- A6. Glossaire bilingue juridique validé.
- A7. Politique tarifaire.
- A8. Cahier des charges art. 83 si tenue déléguée.

Ces points sont portés au **registre des hypothèses** (livrable L11).

## 7. Plan d'étapes

| # | Étape | Statut |
|---|-------|--------|
| E1 | Charpente backend (apps, modèles, services, workflow, audit) | **En cours** |
| E2 | Charpente frontend (i18n, routes, composants) | **En cours** |
| E3 | Génération des migrations + amorce jeux d'essai | À planifier |
| E4 | Couverture art. 80/85/88/91/92 par des tests automatisés | À planifier |
| E5 | Livrables L1/L11 tenus à jour | **Amorcé** |
| E6 | Arbitrages MO (zones gelées, glossaire) | En attente |
| E7 | Activation progressive des zones gelées | Conditionné par E6 |
| E8 | Recette bilingue et conformité (§ 10 TDR) | Fin de chaîne |

## 8. Procédure d'installation (environnement de développement)

```bash
# Backend
cd rsm/backend
python -m venv venv && source venv/Scripts/activate   # (Windows)
pip install -r requirements.txt
cp .env.example .env                                  # ajuster les variables
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

# Frontend
cd ../frontend
npm install
npm start
```

Le backend n'est pas exécutable tant que la base PostgreSQL et les
migrations ne sont pas provisionnées. Aucune preview browser des
interfaces n'est possible avant cette étape.

---

*Version initiale ; à compléter à chaque arbitrage institutionnel.*
