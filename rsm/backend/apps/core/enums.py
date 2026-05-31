"""
Énumérations partagées — directement issues du TDR.

Toute valeur ajoutée à ces énumérations DOIT être fondée sur une disposition
explicite du décret 2021-033 ou, à défaut, signalée comme hypothèse par le
maître d'ouvrage. Aucune valeur « fourre-tout » (« autre », « divers ») n'est
autorisée.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class CanalSaisie(models.TextChoices):
    """Article 78 alinéa 1 — deux canaux équivalents."""

    GUICHET_PAPIER = "guichet_papier", _("Bordereau papier au guichet (art. 78)")
    PORTAIL_ELECTRONIQUE = "portail_electronique", _("Voie électronique (art. 78)")


class NaturesDroitInscrit(models.TextChoices):
    """
    Natures de sûretés et droits pouvant faire l'objet d'une inscription
    au RSM (article 76 — liste limitative).
    """

    NANTISSEMENT_OUTILLAGE = "nant_outillage", _(
        "Nantissement de l'outillage, du matériel ou du matériel professionnel"
    )
    NANTISSEMENT_DROITS_ASSOCIES = "nant_droits_associes", _(
        "Nantissement des droits d'associés, parts sociales, valeurs mobilières et comptes de titres financiers"
    )
    NANTISSEMENT_FONDS_COMMERCE = "nant_fonds_commerce", _(
        "Nantissement du fonds de commerce"
    )
    PRIVILEGE_VENDEUR_FONDS = "priv_vendeur_fonds", _(
        "Privilège du vendeur de fonds de commerce"
    )
    NANTISSEMENT_STOCKS = "nant_stocks", _("Nantissement des stocks")
    PRIVILEGE_TRESOR = "priv_tresor", _("Privilège du Trésor")
    PRIVILEGE_FISCAL = "priv_fiscal", _("Privilège des services fiscaux")
    PRIVILEGE_DOUANES = "priv_douanes", _(
        "Privilège de l'administration des douanes"
    )
    PRIVILEGE_PREVOYANCE = "priv_prevoyance", _(
        "Privilège des organismes de prévoyance sociale"
    )
    NANTISSEMENT_CREANCE = "nant_creance", _("Nantissement de créance")
    NANTISSEMENT_COMPTE_BANCAIRE = "nant_compte_bancaire", _(
        "Nantissement de compte bancaire"
    )
    NANTISSEMENT_PI = "nant_pi", _(
        "Nantissement des droits de propriété intellectuelle"
    )


class MotifRejet(models.TextChoices):
    """
    Motifs LIMITATIFS de rejet — article 80.

    Aucun motif de rejet hors de ces valeurs ne peut être invoqué sans
    contrevenir au régime déclaratif de l'article 86.
    """

    CANAL_NON_AUTORISE = "canal_non_autorise", _(
        "Demande soumise par un canal non autorisé (art. 80)"
    )
    INFORMATIONS_ILLISIBLES = "informations_illisibles", _(
        "Informations illisibles (art. 80)"
    )
    INFORMATIONS_INCOMPREHENSIBLES = "informations_incomprehensibles", _(
        "Informations incompréhensibles (art. 80)"
    )


class TypeCertificat(models.TextChoices):
    """Types de certificats prévus par le TDR (§ 3.1, § 6.2)."""

    INSCRIPTION = "inscription", _("Certificat d'inscription (art. 78, 86)")
    MODIFICATION = "modification", _("Certificat de modification (art. 88-90)")
    RENOUVELLEMENT = "renouvellement", _("Certificat de renouvellement (art. 91)")
    RADIATION = "radiation", _("Certificat de radiation (art. 92)")
    RECHERCHE = "recherche", _("Certificat de recherche (art. 97)")


class CritereRecherche(models.TextChoices):
    """
    Critères de recherche — LISTE LIMITATIVE de l'article 96.

    La recherche exige au moins deux critères parmi ces quatre.
    """

    NOM_CONSTITUANT = "nom_constituant", _(
        "Nom et prénom / dénomination sociale du constituant (art. 96)"
    )
    NUMERO_RC = "numero_rc", _(
        "Numéro d'immatriculation au registre du commerce (art. 96)"
    )
    NUMERO_SERIE_BIEN = "numero_serie_bien", _("Numéro de série du bien (art. 96)")
    NUMERO_INSCRIPTION = "numero_inscription", _(
        "Numéro de l'inscription initiale ou de la modification (art. 96)"
    )


class TypeSurete(models.TextChoices):
    """
    Type de sûreté objet de l'inscription — distinction au sens des
    pratiques juridiques mauritaniennes (art. 76 + corpus civil).

    - ``depot_surete`` : sûreté générique de l'article 76 (nantissement,
      privilèges, etc.) — formulaire historique du RSM.
    - ``privilege_vendeur`` : privilège du vendeur de fonds ou de biens
      mobiliers (art. 76 § 3 + droit civil).
    - ``reserve_propriete`` : clause de réserve de propriété — le
      transfert de propriété est suspendu jusqu'au paiement intégral.
    - ``credit_bail`` : contrat de crédit-bail mobilier — le bien
      demeure propriété du crédit-bailleur pendant l'exécution.

    La distinction est portée par l'utilisateur au stade du dépôt.
    Le système conserve la valeur sous ``Inscription.type_surete`` et
    indexe les éventuelles données spécifiques dans
    ``Inscription.donnees_specifiques`` (JSON).
    """

    DEPOT_SURETE = "depot_surete", _("Déposer une sûreté (générique)")
    PRIVILEGE_VENDEUR = "privilege_vendeur", _("Privilège du vendeur")
    RESERVE_PROPRIETE = "reserve_propriete", _(
        "Vente avec réserve du droit de propriété"
    )
    CREDIT_BAIL = "credit_bail", _("Contrat de crédit-bail")


class NatureConvention(models.TextChoices):
    """
    Nature de la convention constitutive de la sûreté (titre constitutif).

    Distinction usuelle en droit civil : acte authentique passé devant
    notaire vs. acte sous seing privé. Aucune autre catégorie n'est
    admise. Le texte du décret n'impose pas explicitement cette
    distinction au stade de l'inscription (art. 85 énumère le contenu
    sans typer le titre) ; l'information est collectée à titre
    déclaratif (art. 86) pour les besoins probatoires et statistiques.
    """

    NOTARIEE = "notariee", _("Convention notariée")
    SOUS_SEING_PRIVE = "sous_seing_prive", _("Convention sous seing privé")


class FichierRegistre(models.TextChoices):
    """
    Décomposition logique de la base (article 77).
    Le fichier public contient les inscriptions en cours de validité ;
    le fichier général contient l'ensemble des informations actuelles et conservées.
    """

    PUBLIC = "public", _("Fichier accessible au public (art. 77)")
    GENERAL = "general", _("Fichier général (art. 77, 79)")
