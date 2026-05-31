"""Exceptions métier du RSM, typées selon les règles du décret 2021-033."""
from django.utils.translation import gettext_lazy as _


class ErreurMetierRSM(Exception):
    """Erreur métier générique, toujours porteuse d'une référence à l'article."""

    article: str = ""

    def __init__(self, message: str | None = None, *, article: str | None = None):
        self.message = message or self.__class__.__doc__ or ""
        if article:
            self.article = article
        super().__init__(self.message)


class TransitionInterdite(ErreurMetierRSM):
    """La transition de statut demandée n'est pas autorisée (§ 4.3 du TDR)."""


class RejetForme(ErreurMetierRSM):
    """Rejet pour motif limitatif de l'article 80."""
    article = "80"


class ModificationSansEffet(ErreurMetierRSM):
    """
    Modification visant à supprimer l'ensemble des constituants, créanciers
    garantis ou biens grevés sans en désigner de nouveaux (art. 88 dernier
    alinéa). Ce type de modification est sans effet.
    """
    article = "88"


class RenouvellementHorsDelai(ErreurMetierRSM):
    """Renouvellement sollicité après la date d'expiration (art. 91)."""
    article = "91"


class RechercheCriteresInsuffisants(ErreurMetierRSM):
    """
    Recherche présentée avec moins de deux critères parmi la liste limitative
    de l'article 96.
    """
    article = "96"


class RegimeDeclaratifViole(ErreurMetierRSM):
    """
    Une tentative a été faite d'appliquer un contrôle équivalent à la
    vérification des énonciations, prohibée par l'article 86.
    """
    article = "86"
