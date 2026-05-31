"""
Application d'une modification — articles 88, 90, 93.

Séquence stricte imposée par le TDR :

1. Vérifier la recevabilité (statut en cours, autorisations, non-vacuité).
2. Valider le diff (schéma strict — ``DiffModification``).
3. Ouvrir un SAVEPOINT (``sp_application``).
4. Produire un SNAPSHOT « AVANT » (art. 79 — conservation intégrale).
5. Appliquer les mutations :
   - désactivation des rôles et biens retirés (PAS de suppression) ;
   - création des rôles et biens ajoutés ;
   - mise à jour des scalaires modifiables.
6. Vérifier l'ÉTAT FINAL de l'inscription (art. 88 dernier alinéa) :
   - ≥ 1 constituant actif,
   - ≥ 1 créancier garanti actif,
   - ≥ 1 bien grevé actif.
   Si l'état final ne satisfait pas ces invariants, le SAVEPOINT est
   ROLLBACK (pas la transaction entière) → aucune modification partielle,
   aucun contournement par décomposition en plusieurs demandes
   successives. La demande est alors marquée REJETEE avec motif structuré,
   et une entrée d'audit ``modification.refuser`` est écrite.
7. Produire un SNAPSHOT « APRÈS ».
8. Effectuer la transition de statut (→ MODIFIEE).
9. Marquer la demande APPLIQUEE et tracer.

Règles spécifiques :
- Art. 90 al. 2 : la durée et la date d'expiration ne sont PAS
  modifiables ici (le schéma du diff les exclut).
- Art. 86 : aucune vérification au fond ; seuls les contrôles de forme
  prévus par le décret et par l'art. 88 sont exercés.
- Art. 78 / 90 al. 1 : la prise d'effet de la modification est à la
  saisie — horodatage applicatif (ZONE GELÉE § 5.1 pour l'opposabilité).

⚠️ Zone d'arbitrage MO — « Réutilisation d'une Partie existante » : le
diff ne permet QUE la création d'une nouvelle ``Partie`` (pas de
référencement d'une partie existante par identifiant). Cette décision
est en attente d'arbitrage et documentée dans L11 sous la référence
``L11/parties_reutilisation``.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.audit.middleware import contexte_courant
from apps.audit.models import CategorieAudit, ResultatAudit
from apps.audit.services import tracer
from apps.biens.models import BienGreve
from apps.core.exceptions import ModificationSansEffet
from apps.core.scellement import sceller
from apps.inscriptions.models import (
    Inscription,
    RoleInscriptionPartie,
)
from apps.modifications.diff import DiffModification
from apps.modifications.models import (
    DemandeModification,
    MotifRefusModification,
    SnapshotInscription,
    StatutDemandeModification,
)
from apps.modifications.serialisation import (
    encoder_canonique,
    serialiser_inscription,
)
from apps.parties.models import Partie, RolePartie
from apps.utilisateurs.habilitations import (
    AutorisationRefusee,
    peut_valider_demande,
)
from apps.workflow.services import appliquer_transition
from apps.workflow.statuts import (
    STATUTS_EN_COURS_DE_VALIDITE,
    StatutInscription,
)


# --------------------------------------------------------------------------- #
# Exceptions internes                                                          #
# --------------------------------------------------------------------------- #
class EtatFinalInvalide(ModificationSansEffet):
    """
    L'état final de l'inscription après application du diff ne satisfait
    pas les invariants de l'article 88 dernier alinéa.
    """

    def __init__(self, message: str, *, motif_code: str):
        super().__init__(message)
        self.motif_code = motif_code


# --------------------------------------------------------------------------- #
# Invariants d'état final                                                      #
# --------------------------------------------------------------------------- #
def _verifier_etat_final(inscription: Inscription) -> None:
    """
    Vérifie, APRÈS application du diff, que l'inscription conserve :
    - au moins un constituant actif ;
    - au moins un créancier garanti actif ;
    - au moins un bien grevé actif.

    Ce contrôle est positionné APRÈS application pour couvrir tout
    scénario de contournement (y compris l'addition de retraits et
    ajouts dans un même diff, et les cas où l'ajout et le retrait
    portent sur la même référence).
    """
    roles = set(
        inscription.roles_parties.filter(actif=True).values_list("role", flat=True)
    )

    if RolePartie.CONSTITUANT not in roles:
        raise EtatFinalInvalide(
            "Article 88 dernier alinéa — aucune partie constituante active "
            "après application : modification sans effet.",
            motif_code=MotifRefusModification.ETAT_FINAL_CONSTITUANT_ABSENT,
        )
    if RolePartie.CREANCIER not in roles:
        raise EtatFinalInvalide(
            "Article 88 dernier alinéa — aucun créancier garanti actif "
            "après application : modification sans effet.",
            motif_code=MotifRefusModification.ETAT_FINAL_CREANCIER_ABSENT,
        )
    if not inscription.biens.filter(actif=True).exists():
        raise EtatFinalInvalide(
            "Article 88 dernier alinéa — aucun bien grevé actif après "
            "application : modification sans effet.",
            motif_code=MotifRefusModification.ETAT_FINAL_BIEN_ABSENT,
        )


# --------------------------------------------------------------------------- #
# Application des mutations                                                    #
# --------------------------------------------------------------------------- #
def _creer_partie(donnees: dict, type_partie: str) -> Partie:
    """
    Crée une partie à partir des données fournies par le diff.

    ⚠️ ZONE D'ARBITRAGE MO — ``L11/parties_reutilisation`` :
    Le schéma actuel du diff ne permet QUE la création d'une nouvelle
    partie. L'option de référencer une ``Partie`` existante par
    identifiant n'est PAS implémentée et reste en attente d'arbitrage
    du maître d'ouvrage.

    Régime déclaratif (art. 86) : aucun rapprochement automatique avec
    des parties existantes n'est opéré ; le déposant est responsable
    des énonciations.
    """
    return Partie.objects.create(type_partie=type_partie, **donnees)


def _appliquer_retraits_roles(
    inscription: Inscription, ids: list[int], demande: DemandeModification,
) -> None:
    roles = RoleInscriptionPartie.objects.filter(
        inscription=inscription, id__in=ids, actif=True,
    )
    existants = {r.id for r in roles}
    manquants = set(ids) - existants
    if manquants:
        raise ValueError(
            f"Rôles à retirer inexistants ou déjà inactifs : {sorted(manquants)}"
        )
    maintenant = timezone.now()
    for lien in roles:
        lien.actif = False
        lien.date_fin_validite = maintenant
        lien.raison_fin = f"modification.demande#{demande.pk}"
        lien.save(update_fields=["actif", "date_fin_validite", "raison_fin"])


def _appliquer_retraits_biens(
    inscription: Inscription, ids: list[int], demande: DemandeModification,
) -> None:
    biens = BienGreve.objects.filter(
        inscription=inscription, id__in=ids, actif=True,
    )
    existants = {b.id for b in biens}
    manquants = set(ids) - existants
    if manquants:
        raise ValueError(
            f"Biens à retirer inexistants ou déjà inactifs : {sorted(manquants)}"
        )
    maintenant = timezone.now()
    for bien in biens:
        bien.actif = False
        bien.date_fin_validite = maintenant
        bien.raison_fin = f"modification.demande#{demande.pk}"
        bien.save(update_fields=["actif", "date_fin_validite", "raison_fin"])


def _appliquer_ajouts_parties(
    inscription: Inscription, diff: DiffModification,
) -> None:
    for ajout in diff.parties_ajouter:
        partie = _creer_partie(ajout.donnees, ajout.type_partie)
        RoleInscriptionPartie.objects.create(
            inscription=inscription, partie=partie, role=ajout.role,
            actif=True,
        )


def _appliquer_ajouts_biens(
    inscription: Inscription, diff: DiffModification, acteur,
) -> None:
    for ajout in diff.biens_ajouter:
        BienGreve.objects.create(
            inscription=inscription, actif=True,
            cree_par=acteur, modifie_par=acteur,
            **ajout.donnees,
        )


def _appliquer_scalaires(
    inscription: Inscription, scalaires: dict[str, Any], acteur,
) -> None:
    champs_update: dict[str, Any] = {}
    for cle, valeur in scalaires.items():
        if cle == "somme_garantie" and valeur is not None:
            valeur = Decimal(str(valeur))
        setattr(inscription, cle, valeur)
        champs_update[cle] = valeur
    if champs_update:
        inscription.modifie_par = acteur
        champs_update["modifie_par"] = acteur
        type(inscription).objects.filter(pk=inscription.pk).update(**champs_update)


# --------------------------------------------------------------------------- #
# Snapshot                                                                     #
# --------------------------------------------------------------------------- #
def _produire_snapshot(
    *,
    inscription: Inscription,
    evenement: str,
    demande: DemandeModification | None,
    acteur,
) -> SnapshotInscription:
    contenu = serialiser_inscription(inscription)
    empreinte = sceller(encoder_canonique(contenu)).empreinte_hex
    snap = SnapshotInscription(
        inscription=inscription,
        evenement=evenement,
        demande_modification=demande,
        instant=timezone.now(),
        contenu=contenu,
        empreinte=empreinte,
        acteur=acteur,
    )
    snap.save()
    return snap


# --------------------------------------------------------------------------- #
# Refus persistant — marquage REJETEE avec motif structuré                     #
# --------------------------------------------------------------------------- #
def _marquer_rejet(
    *,
    demande: DemandeModification,
    motif_code: str,
    detail: str,
) -> None:
    """
    Persiste le rejet : statut REJETEE, motif structuré (enum limitative),
    détail humain, et entrée d'audit ``modification.refuser``.

    Appelé APRÈS un savepoint_rollback : les mutations sur l'inscription
    sont annulées mais la demande conserve la trace du refus.
    """
    type(demande).objects.filter(pk=demande.pk).update(
        statut=StatutDemandeModification.REJETEE,
        motif_refus_code=motif_code,
        motif_refus=detail[:255],
    )
    demande.statut = StatutDemandeModification.REJETEE
    demande.motif_refus_code = motif_code
    demande.motif_refus = detail[:255]

    tracer(
        categorie=CategorieAudit.REJET,
        action_cle="modification.refuser",
        resultat=ResultatAudit.REJET,
        objet_type="demande_modification",
        objet_reference=str(demande.pk),
        details={
            "motif_code": motif_code,
            "detail": detail,
            "inscription_ref": (
                demande.inscription.numero_ordre
                or str(demande.inscription.reference_demande)
            ),
        },
        contexte=contexte_courant(),
    )


# --------------------------------------------------------------------------- #
# Service principal                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ResultatModification:
    demande: DemandeModification
    snapshot_avant: SnapshotInscription
    snapshot_apres: SnapshotInscription


@transaction.atomic
def appliquer_modification(
    *, demande: DemandeModification, acteur,
) -> ResultatModification:
    """
    Applique une demande de modification.

    En cas d'échec sur l'état final (art. 88 dernier alinéa), le
    savepoint est rollback → aucun changement structurel persisté,
    mais la demande est marquée REJETEE (motif structuré) et l'audit
    garde trace de la tentative.

    En cas d'échec sur un contrôle antérieur (statut, accords, diff
    invalide, diff vide), la demande est également marquée REJETEE
    avec le motif correspondant — aucun snapshot n'est produit dans ce
    cas (rien à annuler côté inscription).
    """
    inscription: Inscription = demande.inscription

    # -- 1. Recevabilité ---------------------------------------------------- #
    if demande.statut != StatutDemandeModification.RECUE:
        raise ModificationSansEffet(
            "La demande n'est plus à l'état « reçue » ; elle ne peut être "
            "appliquée une seconde fois."
        )
    if inscription.statut not in STATUTS_EN_COURS_DE_VALIDITE:
        _marquer_rejet(
            demande=demande,
            motif_code=MotifRefusModification.STATUT_INSCRIPTION_INCOMPATIBLE,
            detail="L'inscription n'est pas en cours de validité (§ 4.3 TDR).",
        )
        raise ModificationSansEffet(
            "L'inscription n'est pas en cours de validité : modification "
            "impossible (§ 4.3)."
        )
    if not peut_valider_demande(acteur, saisie_par=demande.cree_par):
        # Pas de marquage REJETEE : la demande n'a pas été évaluée sur
        # le fond, elle reste RECUE (un autre greffier pourra la valider).
        raise AutorisationRefusee(
            "Validation refusée (séparation stricte, § 4.1)."
        )
    if not (demande.accord_createur_confirme
            and demande.accord_constituant_confirme):
        _marquer_rejet(
            demande=demande,
            motif_code=MotifRefusModification.ACCORDS_MANQUANTS,
            detail="Art. 88 — accords du créancier et du constituant obligatoires.",
        )
        raise ModificationSansEffet(
            "Article 88 — les accords du créancier et du constituant sont "
            "obligatoires pour appliquer la modification."
        )

    # -- 2. Validation du schéma ------------------------------------------- #
    try:
        diff = DiffModification.depuis_dict(demande.diff_propose)
    except ValueError as exc:
        _marquer_rejet(
            demande=demande,
            motif_code=MotifRefusModification.DIFF_INVALIDE,
            detail=str(exc),
        )
        raise ModificationSansEffet(str(exc)) from exc
    if diff.est_vide:
        _marquer_rejet(
            demande=demande,
            motif_code=MotifRefusModification.DIFF_VIDE,
            detail="Aucune modification effective proposée.",
        )
        raise ModificationSansEffet(
            "Diff vide : aucune modification à appliquer."
        )

    # -- 3. Savepoint pour isoler l'application -------------------------- #
    sid = transaction.savepoint()

    try:
        # -- 4. Snapshot AVANT ------------------------------------------ #
        snap_avant = _produire_snapshot(
            inscription=inscription,
            evenement=SnapshotInscription.Evenement.MODIFICATION_AVANT,
            demande=demande,
            acteur=acteur,
        )

        # -- 5. Application des mutations ------------------------------- #
        if diff.parties_retirer:
            _appliquer_retraits_roles(inscription, diff.parties_retirer, demande)
        if diff.biens_retirer:
            _appliquer_retraits_biens(inscription, diff.biens_retirer, demande)
        _appliquer_ajouts_parties(inscription, diff)
        _appliquer_ajouts_biens(inscription, diff, acteur)
        if diff.scalaires:
            _appliquer_scalaires(inscription, diff.scalaires, acteur)

        inscription.refresh_from_db()

        # -- 6. Contrôle d'état final ----------------------------------- #
        _verifier_etat_final(inscription)

        # -- 7. Snapshot APRÈS ------------------------------------------ #
        snap_apres = _produire_snapshot(
            inscription=inscription,
            evenement=SnapshotInscription.Evenement.MODIFICATION_APRES,
            demande=demande,
            acteur=acteur,
        )

        # -- 8. Transition ---------------------------------------------- #
        appliquer_transition(
            numero_inscription=inscription.numero_ordre,
            statut_actuel=inscription.statut,
            statut_cible=StatutInscription.MODIFIEE,
            evenement="modification_art88",
            acteur=acteur,
            motif="Modification appliquée — art. 88 / 90.",
        )
        type(inscription).objects.filter(pk=inscription.pk).update(
            statut=StatutInscription.MODIFIEE, modifie_par=acteur,
        )
        inscription.statut = StatutInscription.MODIFIEE
        inscription.modifie_par = acteur

    except EtatFinalInvalide as exc:
        # Rollback du savepoint : les mutations structurelles (biens,
        # rôles, scalaires, snapshot AVANT) sont annulées.
        transaction.savepoint_rollback(sid)
        # Hors savepoint : persiste le statut REJETEE et trace l'audit.
        _marquer_rejet(
            demande=demande,
            motif_code=exc.motif_code,
            detail=str(exc),
        )
        raise ModificationSansEffet(str(exc)) from exc

    transaction.savepoint_commit(sid)

    # -- 9. Clôture de la demande + journal -------------------------------- #
    type(demande).objects.filter(pk=demande.pk).update(
        statut=StatutDemandeModification.APPLIQUEE,
        applique_le=timezone.now(),
    )
    demande.refresh_from_db()

    tracer(
        categorie=CategorieAudit.DEMANDE,
        action_cle="modification.appliquer",
        resultat=ResultatAudit.SUCCES,
        objet_type="inscription",
        objet_reference=inscription.numero_ordre or "",
        details={
            "demande_id": demande.pk,
            "snapshots": {
                "avant": snap_avant.pk,
                "apres": snap_apres.pk,
            },
            "diff_resume": {
                "parties_ajouter": len(diff.parties_ajouter),
                "parties_retirer": len(diff.parties_retirer),
                "biens_ajouter": len(diff.biens_ajouter),
                "biens_retirer": len(diff.biens_retirer),
                "scalaires_modifies": sorted(diff.scalaires.keys()),
            },
        },
        contexte=contexte_courant(),
    )

    return ResultatModification(
        demande=demande, snapshot_avant=snap_avant, snapshot_apres=snap_apres,
    )
