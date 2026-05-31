"""Vues minimalistes de cadrage — accueil bilingue et sonde de santé."""
from django.http import JsonResponse
from django.utils.translation import get_language
from django.views.generic import TemplateView


class AccueilView(TemplateView):
    template_name = "core/accueil.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["langue_courante"] = get_language()
        return ctx


class SanteView(TemplateView):
    """
    Sonde de santé applicative (supervision § 5.3).
    Ne divulgue aucune donnée métier ; renvoie l'état d'instance et la
    langue résolue, utile pour détecter les erreurs de routage i18n.
    """

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {
                "etat": "ok",
                "langue_resolue": get_language(),
                # Les zones gelées sont publiées en clair : tout auditeur doit
                # pouvoir constater que l'opposabilité n'est pas encore active.
                "zones_gelees": {
                    "horodatage_opposable": False,
                    "scellement_cryptographique": False,
                    "signature_electronique": False,
                    "certificats_probants": False,
                    "paiement": False,
                    "interconnexions_externes": False,
                },
            }
        )
