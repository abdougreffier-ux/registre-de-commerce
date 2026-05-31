"""
Classes de base d'administration Django — verrouillage juridique du RSM.

Motivations issues du TDR :

- § 4.1 — « Aucun administrateur, fonctionnel ou technique, n'a le
  pouvoir de créer, modifier ou supprimer une inscription dans le
  fichier du Registre. Les opérations d'exploitation s'effectuent sans
  accès utile aux contenus métier. »
- Article 79 — « Les informations régulièrement enregistrées sont
  conservées. »
- § 5.2 — « Le journal est protégé en écriture : aucune suppression ni
  modification rétroactive n'est possible. »

Défense en profondeur :

1. Triggers PostgreSQL (journal d'audit — interdiction UPDATE/DELETE).
2. Overrides ORM (``save``/``delete`` des modèles append-only).
3. Exception handler DRF (traduction des refus en 403).
4. **Ce module** — interdiction côté admin Django.

Aucun compte, pas même ``is_superuser``, ne peut contourner ces
protections : les méthodes ``has_*_permission`` sont déclarées en
dur dans les classes ci-dessous et priment sur la matrice de
permissions Django classique.

Trois intentions distinctes sont exprimées :

- :class:`LectureSeuleAdmin` — tout interdit. Destiné aux objets purement
  append-only (journal d'audit, snapshots, transitions, requêtes de
  recherche, extractions statistiques).
- :class:`ConsultationMetierAdmin` — alias sémantique de la précédente,
  destiné aux objets métier CRÉÉS uniquement par les services (Inscription,
  BienGreve, RoleInscriptionPartie, Partie, demandes M/R/Rad, Certificat,
  SequenceNumeroOrdre). L'intent est identique sur les permissions mais
  distinct à la lecture du code.
- :class:`EditionRestreinteAdmin` — add + change autorisés pour
  l'administrateur fonctionnel, delete interdit. Destiné aux
  référentiels bilingues et aux affectations de rôles (§ 4.1 TDR).
"""
from __future__ import annotations

from django.contrib import admin


class _BaseAdminRSM(admin.ModelAdmin):
    """
    Base commune à tous les admins du RSM.

    - ``actions = None`` : désactive les actions de masse. Aucune action
      par sélection multiple n'est proposée, quel que soit le modèle.
    - ``get_actions()`` renvoie un dictionnaire vide, garantissant
      l'absence complète d'actions même en cas d'extensions ultérieures.

    Toute sous-classe doit déclarer explicitement son intention via l'une
    des trois classes ci-dessous. L'héritage direct de ``_BaseAdminRSM``
    est réservé aux cas particuliers (ex. ``UserAdmin`` du module
    ``django.contrib.auth.admin``) et doit s'accompagner d'une
    déclaration explicite des ``has_*_permission``.
    """

    actions = None

    def get_actions(self, request):  # noqa: D401
        return {}


class LectureSeuleAdmin(_BaseAdminRSM):
    """
    Aucune édition possible — ni création, ni modification, ni suppression.

    Destiné aux objets strictement append-only au sens de l'article 79 et
    du § 5.2 du TDR :
    - ``EntreeAudit`` (journal d'audit chaîné) ;
    - ``TransitionStatut`` (historique des transitions § 4.3) ;
    - ``RequeteRecherche`` (traces des recherches art. 94-97) ;
    - ``SnapshotInscription`` (photographies canoniques art. 79) ;
    - ``ExtractionStatistique`` (sorties statistiques art. 82).
    """

    def has_add_permission(self, request):  # noqa: D401
        return False

    def has_change_permission(self, request, obj=None):  # noqa: D401
        return False

    def has_delete_permission(self, request, obj=None):  # noqa: D401
        return False


class ConsultationMetierAdmin(LectureSeuleAdmin):
    """
    Consultation seule des objets métier.

    Les objets métier (inscriptions, parties, biens, demandes M/R/Rad,
    certificats, séquence du n° d'ordre) sont créés et mutés
    EXCLUSIVEMENT par les services applicatifs (``apps.*.services``).
    L'admin Django ne doit jamais constituer un chemin d'écriture
    alternatif, conformément au § 4.1 du TDR (aucun administrateur
    n'a de pouvoir d'écriture sur le métier).
    """

    # Hérite de LectureSeuleAdmin — mêmes permissions, intent distinct.


class EditionRestreinteAdmin(_BaseAdminRSM):
    """
    Édition autorisée (add + change) mais suppression INTERDITE.

    Destiné aux entités dont l'administrateur fonctionnel a la charge
    (§ 4.1 TDR — « gère les utilisateurs, les rôles, les référentiels,
    les modèles de certificats ») mais qui restent soumises à la règle
    de conservation :
    - libellés des référentiels bilingues (types de sûretés, motifs de
      rejet, critères de recherche, types de certificats) ;
    - affectations de rôles (``AffectationRole``) — la révocation passe
      par ``actif=False``, pas par ``DELETE``.

    L'interdiction de suppression découle à la fois de l'article 79
    (conservation des informations régulièrement enregistrées) et de
    la nécessité de tracer toute modification d'habilitation.
    """

    def has_delete_permission(self, request, obj=None):  # noqa: D401
        return False
