# Note L11 — Cohérence frontend ↔ backend sur le parcours de dépôt

## Contexte

Lors d'une démonstration du 23 avril 2026, une incohérence a été
constatée sur le formulaire d'inscription (art. 85) : le frontend
appelait `POST /api/v1/inscriptions/` alors que le backend refuse toute
soumission non authentifiée (DRF `IsAuthenticated` + contrôle d'habilitation
§ 4.1 TDR `peut_enregistrer_demande`). Le message restitué à l'utilisateur
était le message générique « Une erreur est survenue. Veuillez réessayer. »,
insuffisant sur le plan fonctionnel et juridique.

## Décision de mise en cohérence — OPTION B

Conformément à l'instruction MO, et en l'absence d'un portail authentifié
externe exploitable en l'état, **OPTION B** est retenue :

- Le frontend **n'appelle plus** les endpoints protégés `/inscriptions/`,
  `/modifications/`, `/renouvellements/`, `/radiations/` depuis les écrans
  de formulaire publics.
- Le bouton de soumission est remplacé par un encart procédural bilingue
  (`ProcedureDepot.jsx`) rappelant les seules voies de dépôt valides :
  1. Guichet du Greffe — rôle applicatif « Agent de saisie » (TDR § 4.1,
     art. 78 al. 1).
  2. Portail électronique authentifié — rôle applicatif « Déclarant
     externe » (art. 78, 81, 84).

Le bouton primaire est visuellement désactivé (`disabled`) et porte le
libellé « Soumission réservée au portail authentifié » / « التقديم
محصور بالبوابة المصادَق عليها ». Un bouton secondaire « Voir la
procédure de dépôt » ouvre une modale détaillant la procédure.

Aucune modification backend n'a été effectuée : les endpoints et les
services restent en place pour l'administration interne authentifiée.

## Gestion des erreurs — suppression du message générique

Le helper `formatMessageErreur` (`src/api/client.js`) a été renforcé pour
garantir qu'**aucun message générique** n'est affiché. Chaque situation
reçoit un libellé fonctionnel précis, strictement identique en FR et AR :

| Situation | Libellé FR | Libellé AR (équivalence stricte) |
|---|---|---|
| Pas de réponse (backend éteint, ECONNREFUSED) | `erreur.reseau` | idem |
| 401 | `erreur.authentification_requise` | idem |
| 403 | `erreur.autorisation_refusee` (+ détail éventuel) | idem |
| 404 | `erreur.ressource_introuvable` | idem |
| 409 | `erreur.conflit_etat` | idem |
| 429 | `erreur.trop_de_demandes` | idem |
| 500-599 | `erreur.service_indisponible` | idem |
| 400 avec `{detail, article}` (ErreurMetierRSM) | detail + article | idem |
| 400 avec erreurs DRF field-level | `erreur.validation` + énumération des champs | idem |
| Autre code HTTP | `erreur.http_statut` avec le code | idem |

La clé `erreur.generique` a été **supprimée** du référentiel.

## Portée de la décision

- Appliquée aux **quatre** formulaires (`FormulaireInscription`,
  `FormulaireModification`, `FormulaireRenouvellement`,
  `FormulaireRadiation`) via le composant commun `ProcedureDepot`.
- Appliquée aux **trois** vues métier protégées (`Inscriptions`, `Audit`,
  `Recherche`) via `formatMessageErreur` renforcé.
- Strictement bilingue FR/AR — mêmes clés, mêmes effets, seule la
  direction d'écriture varie.
- Aucune modification du backend ni des règles juridiques.

## Levée de cette restriction

La restriction OPTION B sera levée dès que :
1. Les paramètres techniques de la fiche F2 (authentification forte) auront
   été transmis par le MO et un mécanisme d'authentification sera intégré
   au frontend ;
2. Le rôle « Déclarant externe » sera opérationnel pour les utilisateurs
   externes avec session cryptographiquement valide.

À cette date, les formulaires seront réactivés pour appel réel, et
`ProcedureDepot` pourra être désactivé par configuration, sans
modification du code métier.

## Référence à la décision mère

Cette note complète la décision n° 0001/2026 du 22 avril 2026
(cf. `decision_0001_2026.md`), qui a levé les zones gelées F1-F14 sur
le plan juridique tout en laissant en attente les paramètres
techniques. La présente note organise la continuité d'exploitation du
frontend en conformité stricte avec cet état technique.
