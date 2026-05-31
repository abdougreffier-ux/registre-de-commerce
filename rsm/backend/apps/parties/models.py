"""
Parties au sens du décret 2021-033 (articles 85, 88, 92).

Le texte distingue :
- le ou les **créanciers** garantis par la sûreté ;
- le ou les **constituants** (personnes consentant la sûreté) ;
- le ou les **débiteurs** ;
- le **requérant** (identité du déposant).

Points cardinaux du TDR :
- Les données d'identité sont juridiquement neutres vis-à-vis de la langue
  (§ 6.3). Un nom propre ne se traduit pas : il est écrit tel qu'inscrit
  dans la pièce d'identité.
- Pour les personnes physiques, l'article 85 exige la date et le lieu de
  naissance.
- Le nom du constituant est un critère d'indexation (art. 93).

Régime déclaratif (art. 86) : le système NE VÉRIFIE PAS l'identité ; il
se contente d'enregistrer les informations fournies par le requérant.
"""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import ActeurTrace, Horodatage


class TypePartie(models.TextChoices):
    PERSONNE_PHYSIQUE = "pp", _("Personne physique")
    PERSONNE_MORALE = "pm", _("Personne morale")


class TypeIdentifiantPP(models.TextChoices):
    """
    Type d'identifiant utilisé pour une personne physique (directive MO
    2026-05-31). Le NNI mauritanien (10 chiffres) cohabite avec le
    passeport (numéro libre, ≥ 4 caractères) pour les déclarants
    étrangers ou non titulaires de NNI.
    """

    NNI = "nni", _("NNI (numéro national d'identification)")
    PASSEPORT = "passeport", _("Numéro de passeport")


class RolePartie(models.TextChoices):
    CONSTITUANT = "constituant", _("Constituant (art. 85)")
    CREANCIER = "creancier", _("Créancier garanti (art. 85)")
    DEBITEUR = "debiteur", _("Débiteur (art. 85)")
    REQUERANT = "requerant", _("Requérant (art. 85)")
    AGENT_SURETE = "agent_surete", _(
        "Agent de sûreté (mandataire des créanciers, facultatif — décision MO)"
    )


class Partie(Horodatage, ActeurTrace):
    """
    Entité identifiée intervenant dans une inscription.

    Les champs transverses (``nom_complet``, ``denomination_sociale``) sont
    stockés tels que fournis, en un seul champ neutre — cf. § 6.3. Les
    transcriptions ou translittérations relèvent du déposant ; le greffe
    n'opère aucun contrôle (art. 86).
    """

    type_partie = models.CharField(
        _("Type de partie"), max_length=2, choices=TypePartie.choices,
    )

    # --- Personne physique ------------------------------------------------- #
    nom = models.CharField(_("Nom"), max_length=150, blank=True)
    prenom = models.CharField(_("Prénom(s)"), max_length=150, blank=True)
    date_naissance = models.DateField(_("Date de naissance"), null=True, blank=True)
    lieu_naissance = models.CharField(_("Lieu de naissance"), max_length=150, blank=True)
    type_identifiant = models.CharField(
        _("Type d'identifiant (personne physique)"),
        max_length=16, choices=TypeIdentifiantPP.choices,
        default=TypeIdentifiantPP.NNI, blank=True,
        help_text=_(
            "Détermine la nature de la valeur stockée dans ``nni`` : "
            "NNI mauritanien (10 chiffres) ou numéro de passeport "
            "(chaîne libre ≥ 4 caractères)."
        ),
    )
    nni = models.CharField(
        _("NNI / Numéro de passeport"),
        max_length=64, blank=True, db_index=True,
        help_text=_(
            "Valeur de l'identifiant. NNI : exactement 10 chiffres, "
            "non répétitifs. Passeport : numéro tel qu'il figure sur "
            "le document. Information déclarative (art. 86)."
        ),
    )

    # --- Personne morale --------------------------------------------------- #
    denomination_sociale = models.CharField(
        _("Dénomination sociale"), max_length=255, blank=True,
    )
    numero_rc = models.CharField(
        _("Numéro d'immatriculation au RC / NIF"),
        max_length=64, blank=True, db_index=True,
        help_text=_(
            "Article 96 — critère de recherche. Saisi tel que déclaré ; "
            "l'interconnexion avec le RCCM est GELÉE à ce stade. Peut "
            "également porter un numéro d'identification fiscale (NIF)."
        ),
    )
    siege_social = models.CharField(
        _("Siège social"), max_length=255, blank=True,
    )
    representant_legal = models.CharField(
        _("Représentant légal"), max_length=255, blank=True,
        help_text=_(
            "Nom du représentant légal pour la personne morale. "
            "Information déclarative."
        ),
    )

    # --- Commun ------------------------------------------------------------ #
    adresse = models.TextField(_("Adresse du domicile"), blank=True)
    adresse_electronique = models.EmailField(
        _("Adresse électronique (facultative, art. 85)"),
        blank=True,
        help_text=_(
            "Collectée sans obligation (art. 85 avant-dernier alinéa) ; "
            "utilisée uniquement pour notifications si fournie."
        ),
    )
    telephone = models.CharField(_("Téléphone"), max_length=32, blank=True)

    class Meta:
        verbose_name = _("Partie")
        verbose_name_plural = _("Parties")
        indexes = [
            models.Index(fields=["nom", "prenom"]),
            models.Index(fields=["denomination_sociale"]),
            models.Index(fields=["numero_rc"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(type_partie="pp", denomination_sociale="")
                    | models.Q(type_partie="pm")
                ),
                name="pp_sans_denomination",
            ),
        ]

    # -------- Helpers ------------------------------------------------------ #
    def libelle_indexation(self) -> str:
        """
        Clé textuelle pour l'indexation (art. 93).

        Retour : personne physique → ``"NOM PRENOM"`` ; personne morale →
        dénomination sociale. Normalisation de casse minimale (upper).
        """
        if self.type_partie == TypePartie.PERSONNE_PHYSIQUE:
            return f"{self.nom} {self.prenom}".strip().upper()
        return self.denomination_sociale.strip().upper()

    def save(self, *args, **kwargs):
        """
        Défense en profondeur : normalise systématiquement le nom en
        MAJUSCULES côté backend (directive MO 2026-05-31), même si le
        frontend a omis la transformation.
        """
        if self.nom:
            self.nom = self.nom.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return self.libelle_indexation() or f"Partie #{self.pk}"
