"""
Moteur de recherche publique — articles 94 à 97.

Règles IMPÉRATIVES mises en œuvre :

1. Au moins DEUX critères parmi les QUATRE critères LIMITATIFS de l'art. 96 :
   - nom/prénom ou dénomination sociale du constituant ;
   - numéro d'immatriculation au RC du constituant ;
   - numéro de série d'un bien grevé ;
   - numéro de l'inscription initiale ou de la modification.

2. La recherche porte EXCLUSIVEMENT sur le fichier public
   (``STATUTS_FICHIER_PUBLIC``) — § 4.2.5.

3. Lorsque le nom est utilisé, le résultat est EXHAUSTIF des homonymes
   avec adresse et date de naissance (art. 97 alinéa 2).

4. L'instant de la recherche est enregistré et la photographie rendue
   correspond à l'état du fichier public à cet instant. Toute cohérence
   différée entre résultat et certificat constitue un risque juridique
   majeur (§ 4.2.5 point critique).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from django.db.models import Q
from django.utils import timezone

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.core.enums import CritereRecherche
from apps.core.exceptions import RechercheCriteresInsuffisants
from apps.inscriptions.models import Inscription, RoleInscriptionPartie
from apps.parties.models import RolePartie
from apps.recherche.models import RequeteRecherche
from apps.workflow.statuts import STATUTS_FICHIER_PUBLIC

NB_MIN_CRITERES = 2  # Article 96.


@dataclass(frozen=True)
class CriteresRecherche:
    nom_constituant: str = ""
    numero_rc: str = ""
    numero_serie_bien: str = ""
    numero_inscription: str = ""

    def a_renseignes(self) -> list[str]:
        utilises = []
        if self.nom_constituant.strip():
            utilises.append(CritereRecherche.NOM_CONSTITUANT)
        if self.numero_rc.strip():
            utilises.append(CritereRecherche.NUMERO_RC)
        if self.numero_serie_bien.strip():
            utilises.append(CritereRecherche.NUMERO_SERIE_BIEN)
        if self.numero_inscription.strip():
            utilises.append(CritereRecherche.NUMERO_INSCRIPTION)
        return utilises


@dataclass
class ResultatRecherche:
    instant: "timezone.datetime"
    criteres_utilises: list[str]
    inscriptions: list[Inscription] = field(default_factory=list)
    #: Pour chaque inscription, liste des parties « Constituant » (art. 97 al. 2).
    homonymes_par_inscription: dict[int, list[dict]] = field(default_factory=dict)
    requete_id: int | None = None


def _queryset_fichier_public() -> "models.QuerySet":
    return Inscription.objects.filter(statut__in=list(STATUTS_FICHIER_PUBLIC))


def rechercher(criteres: CriteresRecherche) -> ResultatRecherche:
    critere_renseignes = criteres.a_renseignes()
    if len(critere_renseignes) < NB_MIN_CRITERES:
        raise RechercheCriteresInsuffisants(
            "La recherche exige au moins deux critères parmi la liste "
            "limitative de l'article 96."
        )

    qs = _queryset_fichier_public()

    # 1. Constituant par nom / dénomination.
    if criteres.nom_constituant.strip():
        nom = criteres.nom_constituant.strip().upper()
        ids_par_nom = RoleInscriptionPartie.objects.filter(
            role=RolePartie.CONSTITUANT,
        ).filter(
            Q(partie__nom__iexact=nom.split()[0] if nom.split() else "")
            | Q(partie__denomination_sociale__icontains=nom)
            | Q(partie__nom__icontains=nom)
        ).values_list("inscription_id", flat=True)
        qs = qs.filter(pk__in=list(ids_par_nom))

    # 2. N° RC du constituant.
    if criteres.numero_rc.strip():
        ids_par_rc = RoleInscriptionPartie.objects.filter(
            role=RolePartie.CONSTITUANT,
            partie__numero_rc=criteres.numero_rc.strip(),
        ).values_list("inscription_id", flat=True)
        qs = qs.filter(pk__in=list(ids_par_rc))

    # 3. Numéro de série d'un bien grevé.
    if criteres.numero_serie_bien.strip():
        qs = qs.filter(biens__numero_serie=criteres.numero_serie_bien.strip()).distinct()

    # 4. Numéro de l'inscription initiale ou de la modification.
    if criteres.numero_inscription.strip():
        qs = qs.filter(numero_ordre=criteres.numero_inscription.strip())

    instant = timezone.now()
    inscriptions = list(qs.order_by("-instant_saisie_opposable"))

    # Homonymes (art. 97 alinéa 2) pour chaque inscription, uniquement si la
    # recherche utilise le nom du constituant.
    homonymes: dict[int, list[dict]] = {}
    if criteres.nom_constituant.strip():
        for ins in inscriptions:
            parties = ins.roles_parties.filter(role=RolePartie.CONSTITUANT)
            homonymes[ins.pk] = [
                {
                    "nom": p.partie.nom,
                    "prenom": p.partie.prenom,
                    "denomination": p.partie.denomination_sociale,
                    "adresse": p.partie.adresse,
                    "date_naissance": (
                        p.partie.date_naissance.isoformat()
                        if p.partie.date_naissance else None
                    ),
                }
                for p in parties
            ]

    # Trace de la requête.
    contexte = contexte_courant()
    requete = RequeteRecherche(
        instant=instant,
        criteres_soumis={
            "nom_constituant": criteres.nom_constituant,
            "numero_rc": criteres.numero_rc,
            "numero_serie_bien": criteres.numero_serie_bien,
            "numero_inscription": criteres.numero_inscription,
        },
        nombre_resultats=len(inscriptions),
        adresse_ip=contexte.adresse_ip,
        user_agent=contexte.user_agent,
    )
    # .save() direct via Model pour contourner le garde-fou (création admise).
    super(RequeteRecherche, requete).save()

    tracer(
        categorie=CategorieAudit.RECHERCHE,
        action_cle="recherche.lancer",
        resultat=ResultatAudit.SUCCES,
        objet_type="recherche",
        objet_reference=str(requete.pk),
        details={
            "criteres_utilises": critere_renseignes,
            "nombre_resultats": len(inscriptions),
        },
        contexte=contexte,
    )

    return ResultatRecherche(
        instant=instant,
        criteres_utilises=critere_renseignes,
        inscriptions=inscriptions,
        homonymes_par_inscription=homonymes,
        requete_id=requete.pk,
    )
