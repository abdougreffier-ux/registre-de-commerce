"""
Services métier des inscriptions — articles 78, 80, 85, 86, 87.

Ces services sont les SEULS points d'écriture sur ``Inscription``. Toute
mutation directe en base (via l'admin, un shell ou une vue) sans passer
par ces services est interdite en pratique : le moteur de workflow
(``apps.workflow.services``) et le journal d'audit (``apps.audit.services``)
sont intégrés ici pour garantir traçabilité et chronologie.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Sequence

from django.db import transaction
from django.utils import timezone

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.biens.models import BienGreve, CategorieBien
from apps.core.enums import (
    CanalSaisie,
    FichierRegistre,
    MotifRejet,
    NatureConvention,
    TypeSurete,
)
from apps.referentiels.models import LibelleNatureDroit
from apps.core.exceptions import RejetForme
from apps.core.horodatage import (
    ResultatHorodatage,
    format_numero_ordre,
    maintenant_opposable,
)
from apps.inscriptions.models import (
    Inscription,
    ObservationRetour,
    RoleInscriptionPartie,
    SequenceNumeroOrdre,
)
from apps.parties.models import Partie, RolePartie, TypePartie
from apps.utilisateurs.habilitations import (
    peut_enregistrer_demande,
    peut_valider_demande,
)
from apps.workflow.services import appliquer_transition
from apps.workflow.statuts import StatutInscription


# --------------------------------------------------------------------------- #
# 1. Réception d'une demande                                                   #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DonneesDemandeInscription:
    """
    Structure d'entrée du service de création.

    Les champs ``constituants``, ``debiteurs``, ``creanciers`` et ``biens``
    sont des listes de dictionnaires conformes aux serializers
    ``PartieDeposeeSerializer`` / ``BienDeposeSerializer``. Le service ne
    leur impose pas de cardinalité minimale (rétro-compatibilité avec les
    tests existants et le seed démo) ; la stricte exigence (≥ 1 constituant,
    ≥ 1 créancier, ≥ 1 bien) est portée par le formulaire frontend
    refondu.
    """

    canal_saisie: str
    nature_droit: str
    somme_garantie: Decimal | None
    monnaie: str
    duree_en_jours: int
    adresse_electronique_notifications: str = ""
    # Type de sûreté et données spécifiques au parcours
    # (depot_surete / privilege_vendeur / reserve_propriete / credit_bail).
    type_surete: str = "depot_surete"
    donnees_specifiques: dict = field(default_factory=dict)
    # Montant en lettres (FR + AR), calculé par le service (le serializer
    # peut en transmettre une version frontend à titre indicatif, le
    # service recalcule pour être autoritatif).
    montant_en_lettres_fr: str = ""
    montant_en_lettres_ar: str = ""
    # Titre constitutif
    nature_convention: str = ""
    date_convention: date | None = None
    # Parties et biens (dictionnaires bruts validés en amont par le serializer)
    debiteur_est_constituant: bool = False
    constituants: tuple = field(default_factory=tuple)
    debiteurs: tuple = field(default_factory=tuple)
    creanciers: tuple = field(default_factory=tuple)
    # Agents de sûreté (facultatifs) : peuvent contenir un champ
    # ``from_creancier_index`` qui désigne une entrée du tableau
    # ``creanciers`` ci-dessus à réutiliser.
    agents_surete: tuple = field(default_factory=tuple)
    biens: tuple = field(default_factory=tuple)


def _creer_partie(payload: dict, *, acteur) -> Partie:
    """
    Crée une nouvelle ``Partie`` à partir d'un dictionnaire validé par le
    serializer. Pas de dédoublonnage (régime déclaratif, art. 86).
    """
    p = Partie.objects.create(
        type_partie=payload["type_partie"],
        nom=payload.get("nom", ""),
        prenom=payload.get("prenom", ""),
        date_naissance=payload.get("date_naissance"),
        lieu_naissance=payload.get("lieu_naissance", ""),
        type_identifiant=payload.get("type_identifiant") or "nni",
        nni=payload.get("nni", ""),
        denomination_sociale=payload.get("denomination_sociale", ""),
        numero_rc=payload.get("numero_rc", ""),
        siege_social=payload.get("siege_social", ""),
        representant_legal=payload.get("representant_legal", ""),
        adresse=payload.get("adresse", ""),
        adresse_electronique=payload.get("adresse_electronique", ""),
        telephone=payload.get("telephone", ""),
        cree_par=acteur,
        modifie_par=acteur,
    )
    tracer(
        categorie=CategorieAudit.DEMANDE,
        action_cle="partie.creer",
        resultat=ResultatAudit.SUCCES,
        objet_type="partie",
        objet_reference=str(p.pk),
        details={"type": p.type_partie, "libelle": p.libelle_indexation()},
        contexte=contexte_courant(),
    )
    return p


def _attacher_role(inscription: Inscription, partie: Partie, role: str, ordre: int):
    RoleInscriptionPartie.objects.create(
        inscription=inscription,
        partie=partie,
        role=role,
        ordre=ordre,
        actif=True,
    )


def _creer_bien(inscription: Inscription, payload: dict, *, acteur) -> BienGreve:
    """
    Crée un ``BienGreve`` rattaché à l'inscription. La version active du
    schéma de catégorie est figée dans ``categorie_version_snapshot``
    (non-rétroactivité — art. 79).
    """
    cle = payload["categorie_cle"]
    categorie = (
        CategorieBien.objects.filter(cle=cle, actif=True).first()
    )
    version_snapshot = categorie.version if categorie else 0
    bien = BienGreve.objects.create(
        inscription=inscription,
        description_fr=payload.get("description_fr", ""),
        description_ar=payload.get("description_ar", ""),
        marque=payload.get("marque", ""),
        modele=payload.get("modele", ""),
        annee=payload.get("annee"),
        numero_serie=payload.get("numero_serie", ""),
        categorie_cle=cle,
        categorie_version_snapshot=version_snapshot,
        attributs_specifiques=payload.get("attributs_specifiques") or {},
        observations=payload.get("observations", ""),
        actif=True,
        cree_par=acteur,
        modifie_par=acteur,
    )
    tracer(
        categorie=CategorieAudit.DEMANDE,
        action_cle="bien.creer",
        resultat=ResultatAudit.SUCCES,
        objet_type="bien_greve",
        objet_reference=str(bien.pk),
        details={
            "categorie_cle": cle,
            "categorie_version": version_snapshot,
            "numero_serie": bien.numero_serie,
        },
        contexte=contexte_courant(),
    )
    return bien


def _calculer_montant_lettres(somme: Decimal | None, monnaie: str, langue: str) -> str:
    """
    Conversion du montant en lettres via la bibliothèque ``num2words``.

    Retourne une chaîne vide si la somme est nulle ou si la bibliothèque
    n'est pas installée (graceful degradation). Le frontend conserve sa
    propre conversion temps réel via ``n2words``.
    """
    if somme is None or somme == 0:
        return ""
    try:
        from num2words import num2words  # type: ignore
    except ImportError:
        return ""
    try:
        # On arrondit au cent près pour éviter les longues décimales.
        entier = int(somme)
        cents = int(round((somme - entier) * 100))
        if langue == "ar":
            txt = num2words(entier, lang="ar")
        else:
            txt = num2words(entier, lang="fr")
        if cents:
            if langue == "ar":
                txt += f" و {num2words(cents, lang='ar')}"
            else:
                txt += f" et {num2words(cents, lang='fr')} centimes"
        if monnaie:
            txt = f"{txt} {monnaie}"
        return txt
    except (NotImplementedError, ValueError):
        return ""


@transaction.atomic
def creer_demande(
    *,
    donnees: DonneesDemandeInscription,
    acteur,
) -> Inscription:
    """
    Reçoit une demande complète art. 85 et la place en statut « Reçue »
    (§ 4.2.1).

    Orchestre dans une transaction atomique :
      - création de l'``Inscription`` ;
      - création des ``Partie`` constituants / débiteurs / créanciers ;
      - duplication automatique constituant → débiteur si
        ``debiteur_est_constituant`` ;
      - création des ``BienGreve`` rattachés ;
      - traçage à chaque étape au journal d'audit ;
      - transition automatique Reçue → En contrôle de forme.

    Garde-fous (TDR § garde-fous inviolables) :
      - intégrité : append-only, pas de mutation directe ;
      - traçabilité : ``tracer()`` à chaque sous-création ;
      - parité FR/AR : libellés résolus depuis i18n et référentiels.
    """
    if not peut_enregistrer_demande(acteur):
        from apps.utilisateurs.habilitations import AutorisationRefusee
        raise AutorisationRefusee(
            "Cet utilisateur n'est pas habilité à déposer une demande."
        )
    if donnees.canal_saisie not in dict(CanalSaisie.choices):
        # Seul motif limitatif de rejet au stade de la réception.
        raise RejetForme("Canal de saisie non autorisé (art. 80).")
    # Validation contre le référentiel paramétrable (non rétroactif) : la
    # nature doit être ACTIVE au moment du dépôt. Les inscriptions
    # existantes pointant sur une nature ensuite désactivée restent
    # juridiquement valides (art. 79 — conservation pérenne).
    #
    # Baseline garantie : les 12 natures du décret (art. 76, liste
    # limitative) sont TOUJOURS acceptées indépendamment du référentiel.
    # Le référentiel paramétrable étend cette baseline avec les natures
    # ajoutées par le MO (admin natures-droit) ou les data migrations
    # (reserve_propriete, credit_bail).
    from apps.core.enums import NaturesDroitInscrit
    cles_decret = {v for v, _ in NaturesDroitInscrit.choices}
    cles_referentiel = set(
        LibelleNatureDroit.objects.filter(actif=True).values_list("cle", flat=True)
    )
    cles_actives = cles_decret | cles_referentiel
    if donnees.nature_droit not in cles_actives:
        raise RejetForme(
            "Nature de droit inconnue ou désactivée au moment du dépôt."
        )
    if (
        donnees.nature_convention
        and donnees.nature_convention not in dict(NatureConvention.choices)
    ):
        raise RejetForme("Nature de convention non admise.")
    # Le type de sûreté est limité aux 4 valeurs supportées par le système.
    if donnees.type_surete not in dict(TypeSurete.choices):
        raise RejetForme(
            "Type de sûreté inconnu (parcours non supporté par le système)."
        )

    # Calcul autoritatif du montant en lettres côté serveur.
    montant_fr = _calculer_montant_lettres(
        donnees.somme_garantie, donnees.monnaie or "", "fr",
    )
    montant_ar = _calculer_montant_lettres(
        donnees.somme_garantie, donnees.monnaie or "", "ar",
    )

    inscription = Inscription.objects.create(
        canal_saisie=donnees.canal_saisie,
        instant_arrivee=timezone.now(),
        statut=StatutInscription.RECUE,
        type_surete=donnees.type_surete,
        donnees_specifiques=donnees.donnees_specifiques or {},
        nature_droit=donnees.nature_droit,
        somme_garantie=donnees.somme_garantie,
        monnaie=donnees.monnaie,
        duree_en_jours=donnees.duree_en_jours,
        fichier_actuel=FichierRegistre.PUBLIC,
        adresse_electronique_notifications=donnees.adresse_electronique_notifications,
        montant_en_lettres_fr=montant_fr,
        montant_en_lettres_ar=montant_ar,
        nature_convention=donnees.nature_convention or "",
        date_convention=donnees.date_convention,
        debiteur_est_constituant=donnees.debiteur_est_constituant,
        cree_par=acteur,
        modifie_par=acteur,
    )
    tracer(
        categorie=CategorieAudit.DEMANDE,
        action_cle="inscription.deposer",
        resultat=ResultatAudit.SUCCES,
        objet_type="inscription",
        objet_reference=str(inscription.reference_demande),
        details={
            "type_surete": donnees.type_surete,
            "canal": donnees.canal_saisie,
            "nature_droit": donnees.nature_droit,
            "duree_en_jours": donnees.duree_en_jours,
            "nb_constituants": len(donnees.constituants),
            "nb_debiteurs": len(donnees.debiteurs),
            "nb_creanciers": len(donnees.creanciers),
            "nb_biens": len(donnees.biens),
            "debiteur_est_constituant": donnees.debiteur_est_constituant,
            "nb_donnees_specifiques": len(donnees.donnees_specifiques or {}),
        },
        contexte=contexte_courant(),
    )

    # Création des constituants
    constituants_objs: list[Partie] = []
    for idx, payload in enumerate(donnees.constituants):
        partie = _creer_partie(payload, acteur=acteur)
        _attacher_role(inscription, partie, RolePartie.CONSTITUANT, idx)
        constituants_objs.append(partie)

    # Création des créanciers — on conserve les objets pour pouvoir les
    # réutiliser comme agents de sûreté (cas paramétrable).
    creanciers_objs: list[Partie] = []
    for idx, payload in enumerate(donnees.creanciers):
        partie = _creer_partie(payload, acteur=acteur)
        _attacher_role(inscription, partie, RolePartie.CREANCIER, idx)
        creanciers_objs.append(partie)

    # Création des débiteurs :
    # - si ``debiteur_est_constituant`` → on rattache les constituants déjà
    #   créés sous le rôle DEBITEUR (réutilisation, pas de duplication d'entité,
    #   pour garantir la cohérence des identités) ;
    # - sinon → on crée de nouvelles parties à partir des données fournies.
    if donnees.debiteur_est_constituant:
        for idx, partie in enumerate(constituants_objs):
            _attacher_role(inscription, partie, RolePartie.DEBITEUR, idx)
    else:
        for idx, payload in enumerate(donnees.debiteurs):
            partie = _creer_partie(payload, acteur=acteur)
            _attacher_role(inscription, partie, RolePartie.DEBITEUR, idx)

    # Agents de sûreté (facultatif) : peuvent reprendre un créancier
    # existant via ``from_creancier_index``. Quand c'est le cas, on
    # rattache la même Partie sous le rôle AGENT_SURETE plutôt que d'en
    # créer une nouvelle — cohérence d'identité et économie de saisie.
    for idx, payload in enumerate(donnees.agents_surete):
        index_creancier = payload.get("from_creancier_index")
        if (
            index_creancier is not None
            and 0 <= index_creancier < len(creanciers_objs)
        ):
            partie = creanciers_objs[index_creancier]
            _attacher_role(inscription, partie, RolePartie.AGENT_SURETE, idx)
            tracer(
                categorie=CategorieAudit.DEMANDE,
                action_cle="agent_surete.reprendre_creancier",
                resultat=ResultatAudit.SUCCES,
                objet_type="partie",
                objet_reference=str(partie.pk),
                details={"index_creancier": index_creancier},
                contexte=contexte_courant(),
            )
        else:
            partie = _creer_partie(payload, acteur=acteur)
            _attacher_role(inscription, partie, RolePartie.AGENT_SURETE, idx)

    # Création des biens grevés
    for payload in donnees.biens:
        _creer_bien(inscription, payload, acteur=acteur)

    # Transition automatique : Reçue → En contrôle de forme.
    appliquer_transition(
        numero_inscription=str(inscription.reference_demande),
        statut_actuel=StatutInscription.RECUE,
        statut_cible=StatutInscription.EN_CONTROLE_FORME,
        evenement="prise_en_charge",
        acteur=acteur,
        motif="Prise en charge automatique.",
    )
    inscription.statut = StatutInscription.EN_CONTROLE_FORME
    super(Inscription, inscription).save(update_fields=["statut"])
    return inscription


# --------------------------------------------------------------------------- #
# 2. Rejet motivé — article 80                                                 #
# --------------------------------------------------------------------------- #
@transaction.atomic
def prononcer_rejet(
    *,
    inscription: Inscription,
    motif: str,
    commentaire_fr: str = "",
    commentaire_ar: str = "",
    acteur,
) -> Inscription:
    """Prononce un rejet pour l'un des motifs LIMITATIFS de l'article 80."""
    if motif not in dict(MotifRejet.choices):
        raise RejetForme(
            "Motif de rejet invalide : seuls les motifs de l'article 80 sont admissibles."
        )
    if not peut_valider_demande(acteur, saisie_par=inscription.cree_par):
        from apps.utilisateurs.habilitations import AutorisationRefusee
        raise AutorisationRefusee(
            "Cet utilisateur ne peut pas prononcer ce rejet (séparation stricte, § 4.1)."
        )
    appliquer_transition(
        numero_inscription=str(inscription.reference_demande),
        statut_actuel=inscription.statut,
        statut_cible=StatutInscription.REJETEE,
        evenement="rejet_art80",
        acteur=acteur,
        motif=f"Rejet art. 80 : {motif}",
    )
    inscription.statut = StatutInscription.REJETEE
    inscription.motif_rejet = motif
    inscription.commentaire_rejet_fr = commentaire_fr
    inscription.commentaire_rejet_ar = commentaire_ar
    inscription.instant_rejet = timezone.now()
    inscription.modifie_par = acteur
    super(Inscription, inscription).save(
        update_fields=[
            "statut", "motif_rejet", "commentaire_rejet_fr",
            "commentaire_rejet_ar", "instant_rejet", "modifie_par",
        ]
    )
    tracer(
        categorie=CategorieAudit.REJET,
        action_cle="inscription.rejeter",
        resultat=ResultatAudit.REJET,
        objet_type="inscription",
        objet_reference=str(inscription.reference_demande),
        details={"motif": motif, "commentaire_fr": commentaire_fr,
                 "commentaire_ar": commentaire_ar},
        contexte=contexte_courant(),
    )
    return inscription


# --------------------------------------------------------------------------- #
# 3. Validation — attribution du numéro d'ordre et prise d'effet (art. 78, 87) #
# --------------------------------------------------------------------------- #
@transaction.atomic
def attribuer_numero_ordre(instant: "timezone.datetime | None" = None) -> tuple[str, ResultatHorodatage]:
    """
    Attribue un nouveau numéro d'ordre unique horodaté à la seconde.

    - Verrou exclusif sur la ligne de séquence (SELECT ... FOR UPDATE).
    - Horodatage pris à la source de temps officielle
      (``maintenant_opposable``). ⚠️ STUB en zone gelée.
    """
    seq = SequenceNumeroOrdre.objects.select_for_update().get_or_create(pk=1)[0]
    ordre = seq.prochaine_valeur
    seq.prochaine_valeur = ordre + 1
    # save() privé : contourne le garde-fou applicatif (légitime ici).
    super(SequenceNumeroOrdre, seq).save(update_fields=["prochaine_valeur"])

    h = maintenant_opposable() if instant is None else ResultatHorodatage(
        instant=instant, source="externe", opposable=False,
    )
    numero = format_numero_ordre(h.instant, ordre)
    return numero, h


@transaction.atomic
def valider_inscription(
    *, inscription: Inscription, acteur,
) -> Inscription:
    """
    Valide une inscription en contrôle de forme (§ 4.2.1) :
    - attribue le numéro d'ordre (art. 78 alinéa 4) ;
    - fixe l'instant de saisie opposable (art. 78 alinéa 3 — ZONE GELÉE
      pour l'opposabilité définitive) ;
    - calcule la date d'expiration à partir de la durée déclarée ;
    - applique la transition vers « Inscrite ».

    ⚠️ La génération du certificat probant art. 97 et le scellement sont
    GELÉS et ne sont PAS déclenchés par ce service.
    """
    if not peut_valider_demande(acteur, saisie_par=inscription.cree_par):
        from apps.utilisateurs.habilitations import AutorisationRefusee
        raise AutorisationRefusee(
            "Validation refusée (rôle manquant ou cumul interdit, § 4.1)."
        )
    if inscription.statut != StatutInscription.EN_CONTROLE_FORME:
        raise RejetForme(
            "Seule une demande en contrôle de forme peut être validée."
        )

    numero, horodatage = attribuer_numero_ordre()
    inscription.numero_ordre = numero
    inscription.instant_saisie_opposable = horodatage.instant
    inscription.date_expiration = (
        horodatage.instant.date() + timedelta(days=inscription.duree_en_jours)
    )
    inscription.statut = StatutInscription.INSCRITE
    inscription.modifie_par = acteur
    super(Inscription, inscription).save(
        update_fields=[
            "numero_ordre", "instant_saisie_opposable",
            "date_expiration", "statut", "modifie_par",
        ]
    )

    appliquer_transition(
        numero_inscription=numero,
        statut_actuel=StatutInscription.EN_CONTROLE_FORME,
        statut_cible=StatutInscription.INSCRITE,
        evenement="validation_greffier",
        acteur=acteur,
        motif=(
            "Validation du greffier — conditions de l'article 85 réunies. "
            "⚠️ Certificat probant (art. 97) et scellement GELÉS."
        ),
    )
    tracer(
        categorie=CategorieAudit.VALIDATION,
        action_cle="inscription.valider",
        resultat=ResultatAudit.SUCCES,
        objet_type="inscription",
        objet_reference=numero,
        details={
            "horodatage_source": horodatage.source,
            "horodatage_opposable": horodatage.opposable,
            "date_expiration": inscription.date_expiration.isoformat(),
        },
        contexte=contexte_courant(),
    )
    return inscription


# --------------------------------------------------------------------------- #
# 4. Retour au déclarant pour correction (workflow MO 2026-05-31)            #
# --------------------------------------------------------------------------- #
@transaction.atomic
def retourner_demande(
    *,
    inscription: Inscription,
    observation_fr: str,
    observation_ar: str,
    acteur,
) -> ObservationRetour:
    """
    Retourne une demande au déclarant avec une observation OBLIGATOIRE
    bilingue FR + AR. La demande passe en statut ``RETOURNEE`` et reste
    réversible (réversibilité gérée par ``resoumettre_demande``).

    Garde-fous :
      - Séparation stricte : le retour ne peut être prononcé par
        l'auteur de la saisie initiale (cohérent avec le rejet art. 80).
      - Statut source impératif : ``EN_CONTROLE_FORME`` (toute autre
        situation lève ``RejetForme``).
      - Observation bilingue obligatoire (parité juridique FR/AR).
      - Append-only : l'observation créée ne pourra plus être modifiée.

    Le journal d'audit reçoit une entrée ``inscription.retourner`` avec
    catégorie ``RETOUR_CORRECTION`` et résultat ``RETOUR_POUR_CORRECTION``.
    """
    if not peut_valider_demande(acteur, saisie_par=inscription.cree_par):
        from apps.utilisateurs.habilitations import AutorisationRefusee
        raise AutorisationRefusee(
            "Retour refusé (rôle manquant ou séparation stricte, § 4.1)."
        )
    if inscription.statut != StatutInscription.EN_CONTROLE_FORME:
        raise RejetForme(
            "Seule une demande en contrôle de forme peut être retournée "
            "pour correction."
        )
    if not (observation_fr or "").strip() or not (observation_ar or "").strip():
        raise RejetForme(
            "Observation obligatoire en FR et AR (parité juridique)."
        )

    observation = ObservationRetour.objects.create(
        inscription=inscription,
        observation_fr=observation_fr.strip(),
        observation_ar=observation_ar.strip(),
        cree_par=acteur,
        statut_au_moment=inscription.statut,
    )

    # Transition de workflow EN_CONTROLE_FORME → RETOURNEE
    appliquer_transition(
        numero_inscription=str(inscription.reference_demande),
        statut_actuel=inscription.statut,
        statut_cible=StatutInscription.RETOURNEE,
        evenement="retour_observation",
        acteur=acteur,
        motif=(
            "Retour au déclarant avec observation obligatoire FR/AR."
        ),
    )
    inscription.statut = StatutInscription.RETOURNEE
    inscription.modifie_par = acteur
    super(Inscription, inscription).save(
        update_fields=["statut", "modifie_par"]
    )

    tracer(
        categorie=CategorieAudit.RETOUR_CORRECTION,
        action_cle="inscription.retourner",
        resultat=ResultatAudit.RETOUR_POUR_CORRECTION,
        objet_type="inscription",
        objet_reference=str(inscription.reference_demande),
        details={
            "observation_id": observation.pk,
            "observation_fr": observation.observation_fr,
            "observation_ar": observation.observation_ar,
            "statut_avant": StatutInscription.EN_CONTROLE_FORME,
            "statut_apres": StatutInscription.RETOURNEE,
        },
        contexte=contexte_courant(),
    )
    return observation


# --------------------------------------------------------------------------- #
# 5. Resoumission par le déclarant après correction                          #
# --------------------------------------------------------------------------- #
@transaction.atomic
def resoumettre_demande(
    *,
    inscription: Inscription,
    acteur,
) -> Inscription:
    """
    Le déclarant resoumet sa demande après correction. La demande
    repasse en ``EN_CONTROLE_FORME`` pour réexamen par le greffier.

    Garde-fous :
      - Seul le créateur initial de la demande peut resoumettre.
      - Statut source impératif : ``RETOURNEE``.
      - La dernière ``ObservationRetour`` non encore résolue est
        marquée comme résolue (``instant_resoumission`` + ``resoumis_par``).
    """
    if inscription.cree_par_id and inscription.cree_par_id != acteur.pk:
        from apps.utilisateurs.habilitations import AutorisationRefusee
        raise AutorisationRefusee(
            "Seul le déclarant initial peut resoumettre cette demande."
        )
    if inscription.statut != StatutInscription.RETOURNEE:
        raise RejetForme(
            "Seule une demande retournée peut être resoumise."
        )

    # Marquer la dernière observation comme résolue (append-only :
    # un seul renseignement définitif).
    derniere_observation = (
        ObservationRetour.objects
        .filter(inscription=inscription, instant_resoumission__isnull=True)
        .order_by("-cree_le")
        .first()
    )
    if derniere_observation is not None:
        derniere_observation.instant_resoumission = timezone.now()
        derniere_observation.resoumis_par = acteur
        super(ObservationRetour, derniere_observation).save(
            update_fields=["instant_resoumission", "resoumis_par"]
        )

    appliquer_transition(
        numero_inscription=str(inscription.reference_demande),
        statut_actuel=inscription.statut,
        statut_cible=StatutInscription.EN_CONTROLE_FORME,
        evenement="resoumission_declarant",
        acteur=acteur,
        motif="Resoumission par le déclarant après correction.",
    )
    inscription.statut = StatutInscription.EN_CONTROLE_FORME
    inscription.modifie_par = acteur
    super(Inscription, inscription).save(
        update_fields=["statut", "modifie_par"]
    )

    tracer(
        categorie=CategorieAudit.DEMANDE,
        action_cle="inscription.resoumettre",
        resultat=ResultatAudit.SUCCES,
        objet_type="inscription",
        objet_reference=str(inscription.reference_demande),
        details={
            "observation_levee_id": (
                derniere_observation.pk if derniere_observation else None
            ),
            "statut_avant": StatutInscription.RETOURNEE,
            "statut_apres": StatutInscription.EN_CONTROLE_FORME,
        },
        contexte=contexte_courant(),
    )
    return inscription
