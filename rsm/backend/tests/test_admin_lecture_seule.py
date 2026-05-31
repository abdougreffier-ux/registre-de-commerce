"""
Verrouillage juridique de l'administration Django — TDR § 4.1, art. 79.

Vérifications, pour chaque modèle enregistré à l'admin :
- TOUTES les actions de masse sont désactivées (``get_actions`` vide) ;
- les permissions add / change / delete correspondent à l'intent
  déclaré par la classe (``LectureSeuleAdmin``,
  ``ConsultationMetierAdmin``, ``EditionRestreinteAdmin``, ou
  ``UtilisateurAdmin`` qui restreint uniquement le delete) ;
- aucun utilisateur — pas même ``is_superuser=True`` — ne peut
  contourner la restriction : les méthodes ``has_*_permission`` sont
  déclarées en dur dans les classes de base.

Les tests sont indépendants du reste du système : ils utilisent un
``RequestFactory`` et n'exécutent aucune vue.
"""
from __future__ import annotations

from django.contrib import admin as django_admin
from django.test import RequestFactory, TestCase

from apps.audit.models import EntreeAudit
from apps.biens.models import BienGreve
from apps.certificats.models import Certificat
from apps.core.admin_base import (
    ConsultationMetierAdmin,
    EditionRestreinteAdmin,
    LectureSeuleAdmin,
)
from apps.inscriptions.models import (
    Inscription,
    PieceJointe,
    RoleInscriptionPartie,
    SequenceNumeroOrdre,
)
from apps.modifications.models import DemandeModification, SnapshotInscription
from apps.parties.models import Partie
from apps.radiations.models import DemandeRadiation
from apps.recherche.models import RequeteRecherche
from apps.referentiels.models import (
    LibelleCanalSaisie,
    LibelleCritereRecherche,
    LibelleMotifRejet,
    LibelleNatureDroit,
    LibelleTypeCertificat,
)
from apps.renouvellements.models import DemandeRenouvellement
from apps.statistiques.models import ExtractionStatistique
from apps.utilisateurs.models import AffectationRole, Utilisateur


# --------------------------------------------------------------------------- #
# Intents attendus par modèle                                                  #
# --------------------------------------------------------------------------- #
MODELES_APPEND_ONLY = [
    EntreeAudit,
    RequeteRecherche,
    SnapshotInscription,
    ExtractionStatistique,
    SequenceNumeroOrdre,
]

MODELES_METIER_CONSULTATION = [
    Inscription,
    RoleInscriptionPartie,
    PieceJointe,
    Partie,
    BienGreve,
    DemandeModification,
    DemandeRenouvellement,
    DemandeRadiation,
    Certificat,
]

MODELES_REFERENTIELS = [
    LibelleNatureDroit,
    LibelleMotifRejet,
    LibelleCanalSaisie,
    LibelleCritereRecherche,
    LibelleTypeCertificat,
]

MODELES_EDITION_RESTREINTE_TRACEE = [
    AffectationRole,
]

#: Modèle traité à part : ``Utilisateur`` conserve un ``UserAdmin``
#: fonctionnel (création / modification autorisées) mais interdit la
#: suppression et les actions de masse.
MODELE_UTILISATEUR = Utilisateur


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
class _SuperuserRequest:
    """Simule une requête venant d'un ``is_superuser=True``."""

    @staticmethod
    def creer(factory: RequestFactory, methode: str = "get", chemin: str = "/"):
        req = getattr(factory, methode)(chemin)
        req.user = Utilisateur.objects.create_superuser(
            username=f"super_{methode}_{id(req)}",
            email="super@exemple.mr", password="motdepasse-dev",
        )
        return req


# --------------------------------------------------------------------------- #
# Action mass désactivée pour TOUS les admins enregistrés                      #
# --------------------------------------------------------------------------- #
class AdminActionsDeMasseTests(TestCase):
    """La désactivation des actions doit couvrir TOUS les modèles enregistrés."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_aucune_action_de_masse_sur_aucun_admin(self):
        request = _SuperuserRequest.creer(self.factory)
        non_conformes = []
        for modele, admin_instance in django_admin.site._registry.items():
            actions = admin_instance.get_actions(request)
            if actions:
                non_conformes.append(
                    f"{modele.__module__}.{modele.__name__} — actions: "
                    f"{sorted(actions)}"
                )
        self.assertEqual(
            non_conformes, [],
            f"Admins exposant des actions de masse : {non_conformes}",
        )


# --------------------------------------------------------------------------- #
# Append-only — aucune permission d'édition                                    #
# --------------------------------------------------------------------------- #
class AdminAppendOnlyVerrouilleTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = _SuperuserRequest.creer(self.factory)

    def test_tous_les_modeles_append_only_herited_de_lectureseuleadmin(self):
        for modele in MODELES_APPEND_ONLY:
            admin_instance = django_admin.site._registry.get(modele)
            self.assertIsNotNone(
                admin_instance, f"{modele.__name__} non enregistré à l'admin.",
            )
            self.assertIsInstance(
                admin_instance, LectureSeuleAdmin,
                f"{modele.__name__} ne dérive pas de LectureSeuleAdmin.",
            )

    def test_aucune_operation_d_ecriture_sur_append_only(self):
        for modele in MODELES_APPEND_ONLY:
            admin_instance = django_admin.site._registry[modele]
            self.assertFalse(
                admin_instance.has_add_permission(self.request),
                f"has_add_permission doit être False sur {modele.__name__}.",
            )
            self.assertFalse(
                admin_instance.has_change_permission(self.request),
                f"has_change_permission doit être False sur {modele.__name__}.",
            )
            self.assertFalse(
                admin_instance.has_delete_permission(self.request),
                f"has_delete_permission doit être False sur {modele.__name__}.",
            )


# --------------------------------------------------------------------------- #
# Métier (consultation seule — mutations par services uniquement)              #
# --------------------------------------------------------------------------- #
class AdminMetierConsultationSeuleTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = _SuperuserRequest.creer(self.factory)

    def test_tous_les_modeles_metier_en_consultation_seule(self):
        for modele in MODELES_METIER_CONSULTATION:
            admin_instance = django_admin.site._registry.get(modele)
            self.assertIsNotNone(
                admin_instance, f"{modele.__name__} non enregistré à l'admin.",
            )
            self.assertIsInstance(
                admin_instance, ConsultationMetierAdmin,
                f"{modele.__name__} ne dérive pas de ConsultationMetierAdmin.",
            )

    def test_aucune_operation_d_ecriture_sur_metier(self):
        for modele in MODELES_METIER_CONSULTATION:
            admin_instance = django_admin.site._registry[modele]
            self.assertFalse(
                admin_instance.has_add_permission(self.request),
                f"has_add_permission doit être False sur {modele.__name__}.",
            )
            self.assertFalse(
                admin_instance.has_change_permission(self.request),
                f"has_change_permission doit être False sur {modele.__name__}.",
            )
            self.assertFalse(
                admin_instance.has_delete_permission(self.request),
                f"has_delete_permission doit être False sur {modele.__name__}.",
            )


# --------------------------------------------------------------------------- #
# Référentiels — édition des libellés OK, add/delete interdits                #
# --------------------------------------------------------------------------- #
class AdminReferentielsEditionRestreinteTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = _SuperuserRequest.creer(self.factory)

    def test_referentiels_utilisent_edition_restreinte(self):
        for modele in MODELES_REFERENTIELS:
            admin_instance = django_admin.site._registry.get(modele)
            self.assertIsInstance(
                admin_instance, EditionRestreinteAdmin,
                f"{modele.__name__} ne dérive pas de EditionRestreinteAdmin.",
            )

    def test_referentiels_change_oui_add_et_delete_non(self):
        for modele in MODELES_REFERENTIELS:
            admin_instance = django_admin.site._registry[modele]
            self.assertFalse(
                admin_instance.has_add_permission(self.request),
                f"Ajout autorisé à tort sur {modele.__name__}.",
            )
            self.assertFalse(
                admin_instance.has_delete_permission(self.request),
                f"Suppression autorisée à tort sur {modele.__name__}.",
            )
            # La modification des libellés reste possible pour l'admin fonctionnel.
            self.assertTrue(
                admin_instance.has_change_permission(self.request),
                f"Modification doit rester possible sur {modele.__name__}.",
            )

    def test_cle_technique_en_readonly(self):
        for modele in MODELES_REFERENTIELS:
            admin_instance = django_admin.site._registry[modele]
            self.assertIn(
                "cle", admin_instance.readonly_fields,
                f"La clé technique de {modele.__name__} doit être en "
                "readonly (liste limitative du décret).",
            )


# --------------------------------------------------------------------------- #
# Utilisateurs et rôles                                                        #
# --------------------------------------------------------------------------- #
class AdminUtilisateursRolesTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = _SuperuserRequest.creer(self.factory)

    def test_utilisateur_suppression_interdite(self):
        admin_instance = django_admin.site._registry[MODELE_UTILISATEUR]
        self.assertFalse(
            admin_instance.has_delete_permission(self.request),
            "La suppression d'un Utilisateur doit être interdite (art. 79).",
        )

    def test_utilisateur_actions_de_masse_desactivees(self):
        admin_instance = django_admin.site._registry[MODELE_UTILISATEUR]
        self.assertEqual(admin_instance.get_actions(self.request), {})

    def test_affectation_role_non_supprimable(self):
        admin_instance = django_admin.site._registry[AffectationRole]
        self.assertIsInstance(admin_instance, EditionRestreinteAdmin)
        self.assertFalse(admin_instance.has_delete_permission(self.request))


# --------------------------------------------------------------------------- #
# Défense en profondeur : overrides ORM + admin alignés                        #
# --------------------------------------------------------------------------- #
class AdminDefensEnProfondeurTests(TestCase):
    """
    Alignement entre les interdictions ORM (``save``/``delete`` override)
    et les interdictions admin. Assure qu'il n'existe pas de modèle
    append-only dont le delete ORM est refusé mais dont l'admin
    autoriserait encore des opérations d'écriture.
    """

    def setUp(self):
        self.factory = RequestFactory()
        self.request = _SuperuserRequest.creer(self.factory)

    def test_modeles_append_only_coherents(self):
        """
        Pour chaque modèle dont ``delete()`` ORM lève ``PermissionError``,
        l'admin correspondant doit être en lecture seule totale.
        """
        modeles_avec_delete_ormbloque = MODELES_APPEND_ONLY + [
            Inscription, RoleInscriptionPartie, BienGreve,
        ]
        for modele in modeles_avec_delete_ormbloque:
            admin_instance = django_admin.site._registry.get(modele)
            if admin_instance is None:
                continue  # ex. SequenceNumeroOrdre peut être hors périmètre
            self.assertFalse(
                admin_instance.has_delete_permission(self.request),
                f"{modele.__name__} bloque delete côté ORM mais pas côté admin.",
            )
