"""
Fabriques de données pour les tests.

Chaque helper est construit de manière à produire un objet conforme aux
règles minimales du décret ; les tests peuvent ensuite faire varier un
seul champ pour vérifier une règle particulière.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from apps.core.enums import CanalSaisie, NaturesDroitInscrit
from apps.inscriptions.models import Inscription
from apps.inscriptions.services import (
    DonneesDemandeInscription,
    creer_demande,
    valider_inscription,
)
from apps.parties.models import Partie, RolePartie, TypePartie
from apps.utilisateurs.models import AffectationRole, RoleApplicatif, Utilisateur


# --------------------------------------------------------------------------- #
# Utilisateurs et rôles                                                        #
# --------------------------------------------------------------------------- #
def creer_utilisateur(
    *, username: str, roles: list[str] | None = None,
) -> Utilisateur:
    user = Utilisateur.objects.create_user(
        username=username, password="motdepasse-dev",
    )
    for role in roles or []:
        AffectationRole.objects.create(utilisateur=user, role=role, actif=True)
    return user


def creer_agent_saisie(username: str = "agent_saisie") -> Utilisateur:
    return creer_utilisateur(
        username=username, roles=[RoleApplicatif.AGENT_SAISIE]
    )


def creer_greffier(username: str = "greffier") -> Utilisateur:
    return creer_utilisateur(
        username=username, roles=[RoleApplicatif.AUTORITE_VALIDATION]
    )


# --------------------------------------------------------------------------- #
# Parties                                                                      #
# --------------------------------------------------------------------------- #
def creer_partie_pp(nom: str = "Ould Mohamed", prenom: str = "Ahmed") -> Partie:
    return Partie.objects.create(
        type_partie=TypePartie.PERSONNE_PHYSIQUE,
        nom=nom, prenom=prenom,
        date_naissance=date(1980, 1, 1), lieu_naissance="Nouakchott",
        adresse="BP 123, Nouakchott",
    )


def creer_partie_pm(
    denomination: str = "Société Commerciale de Nouakchott",
    numero_rc: str = "RC/NKT/2024/0001",
) -> Partie:
    return Partie.objects.create(
        type_partie=TypePartie.PERSONNE_MORALE,
        denomination_sociale=denomination, numero_rc=numero_rc,
        adresse="Nouakchott",
    )


# --------------------------------------------------------------------------- #
# Inscriptions                                                                 #
# --------------------------------------------------------------------------- #
def deposer_demande_standard(
    *, acteur, duree_jours: int = 365,
) -> Inscription:
    """Crée une demande conforme aux champs obligatoires de l'art. 85."""
    return creer_demande(
        donnees=DonneesDemandeInscription(
            canal_saisie=CanalSaisie.GUICHET_PAPIER,
            nature_droit=NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
            somme_garantie=Decimal("1000000.00"),
            monnaie="MRU",
            duree_en_jours=duree_jours,
        ),
        acteur=acteur,
    )


def valider_avec_greffier(inscription: Inscription, greffier) -> Inscription:
    return valider_inscription(inscription=inscription, acteur=greffier)


def peupler_inscription_complete(inscription: Inscription, *, acteur=None):
    """
    Ajoute à l'inscription le minimum requis par l'article 85 :
    un constituant, un créancier garanti, un débiteur et un bien grevé.

    Utilisé avant une modification pour que le contrôle d'état final
    (art. 88 dernier alinéa) ait une référence valide.
    """
    from apps.biens.models import BienGreve
    from apps.inscriptions.models import RoleInscriptionPartie

    constituant = creer_partie_pm("Constituant SARL", "RC/NKT/2024/1001")
    creancier = creer_partie_pm("Banque Créancière", "RC/NKT/2024/1002")
    debiteur = creer_partie_pp("Debiteur", "Ahmed")

    lien_c = RoleInscriptionPartie.objects.create(
        inscription=inscription, partie=constituant,
        role=RolePartie.CONSTITUANT,
    )
    lien_cr = RoleInscriptionPartie.objects.create(
        inscription=inscription, partie=creancier,
        role=RolePartie.CREANCIER,
    )
    lien_d = RoleInscriptionPartie.objects.create(
        inscription=inscription, partie=debiteur,
        role=RolePartie.DEBITEUR,
    )

    bien = BienGreve.objects.create(
        inscription=inscription,
        description_fr="Outillage industriel",
        description_ar="معدات صناعية",
        marque="ACME", modele="X-100", numero_serie="SN-001",
        cree_par=acteur, modifie_par=acteur,
    )

    return {
        "constituant": constituant, "lien_constituant": lien_c,
        "creancier": creancier, "lien_creancier": lien_cr,
        "debiteur": debiteur, "lien_debiteur": lien_d,
        "bien": bien,
    }


def preparer_inscription_prete_a_modifier(
    *, duree_jours: int = 365,
):
    """
    Fabrique une inscription VALIDÉE (statut ``INSCRITE``) avec
    constituant, créancier, débiteur et bien. Retourne
    ``(inscription, objets_peuples, agent, greffier)``.
    """
    agent = creer_agent_saisie()
    greffier = creer_greffier()
    demande = deposer_demande_standard(acteur=agent, duree_jours=duree_jours)
    peuple = peupler_inscription_complete(demande, acteur=agent)
    inscription = valider_avec_greffier(demande, greffier)
    inscription.refresh_from_db()
    return inscription, peuple, agent, greffier


def creer_demande_modification(
    inscription: Inscription, diff: dict, *, acteur,
    accord_createur: bool = True, accord_constituant: bool = True,
):
    """Construit une ``DemandeModification`` prête à appliquer."""
    from apps.modifications.models import DemandeModification

    return DemandeModification.objects.create(
        inscription=inscription,
        objet_modification_fr="Modification de test",
        objet_modification_ar="تعديل للاختبار",
        diff_propose=diff,
        accord_createur_confirme=accord_createur,
        accord_constituant_confirme=accord_constituant,
        cree_par=acteur, modifie_par=acteur,
    )
