from django.apps import AppConfig


class InterconnexionsConfig(AppConfig):
    """
    App de prévision pour l'interopérabilité RSM ↔ partenaires externes.

    Toutes les routes HTTP restent inactives tant que ``RSM_INTEROP_BANQUES_MODE``
    n'est pas placé à ``"active"`` par décision MO (fiche F15).
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.interconnexions"
    verbose_name = "Interopérabilité externe (F15)"
