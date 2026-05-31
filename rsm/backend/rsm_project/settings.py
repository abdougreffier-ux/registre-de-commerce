"""
Configuration Django — Système informatique du Registre des Sûretés Mobilières (RSM).

Fondé sur le chapitre IV (articles 76–97) du décret 2021-033 relatif au
Registre du commerce et des Sûretés Mobilières.

Règles impératives rappelées :
- Bilinguisme strict français / arabe, sans divergence (§ 7 du TDR).
- Une seule logique métier, un seul modèle de données (§ 6.3).
- Aucune suppression de donnée régulièrement enregistrée (art. 79).
- Horodatage à la seconde, source de temps fiable (art. 78, § 5.1).
- Zones GELÉES : signature électronique, scellement cryptographique,
  horodatage opposable définitif, génération probante des certificats,
  paiement, interconnexions externes.
"""
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# Le proxy de développement React (Create React App) réécrit l'en-tête
# ``Origin`` à l'origine du backend. En développement, on autorise les
# origines locales standard. À durcir en production.
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3100",
    "http://127.0.0.1:3100",
]
_csrf_origins_env = config("DJANGO_CSRF_TRUSTED_ORIGINS", default="")
if _csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins_env.split(",") if o.strip()]

# --------------------------------------------------------------------------- #
# Applications                                                                 #
# --------------------------------------------------------------------------- #
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
    "corsheaders",
]

LOCAL_APPS = [
    # Transverses
    "apps.core",
    "apps.audit",
    "apps.referentiels",
    "apps.utilisateurs",
    "apps.workflow",
    # Métier
    "apps.parties",
    "apps.biens",
    "apps.inscriptions",
    "apps.modifications",
    "apps.renouvellements",
    "apps.radiations",
    "apps.rejets",
    "apps.recherche",
    "apps.certificats",
    "apps.statistiques",
    "apps.administration",
    # Prévision F15 — interopérabilité bancaire. Aucun endpoint exposé
    # tant que ``RSM_INTEROP_BANQUES_MODE != "active"``.
    "apps.interconnexions",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --------------------------------------------------------------------------- #
# Middleware                                                                   #
# --------------------------------------------------------------------------- #
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # La langue doit être résolue tôt — l'ensemble de l'UI en dépend.
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middleware projet : capte l'acteur courant pour le journal d'audit.
    "apps.audit.middleware.CurrentActorMiddleware",
]

ROOT_URLCONF = "rsm_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "rsm_project.wsgi.application"

# --------------------------------------------------------------------------- #
# Base de données                                                              #
# --------------------------------------------------------------------------- #
# PostgreSQL est obligatoire : contraintes d'intégrité, index full-text FR/AR,
# triggers de protection du journal d'audit (append-only).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="rsm"),
        "USER": config("DB_USER", default="rsm"),
        "PASSWORD": config("DB_PASSWORD", default="rsm"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# --------------------------------------------------------------------------- #
# Authentification                                                             #
# --------------------------------------------------------------------------- #
# NOTE — GELÉ : MFA, signature électronique et authentification forte ne sont
# pas implémentés à ce stade (§ 5.1 du TDR, en attente d'arbitrages
# institutionnels sur la PKI nationale / l'identité numérique).
AUTH_USER_MODEL = "utilisateurs.Utilisateur"

# --------------------------------------------------------------------------- #
# Internationalisation — FR/AR obligatoires, équivalents juridiquement         #
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = config("DEFAULT_LANGUAGE", default="fr")
TIME_ZONE = config("TIME_ZONE", default="Africa/Nouakchott")
USE_I18N = True
USE_TZ = True

# Aucune langue additionnelle ne doit être activée sans accord du maître
# d'ouvrage : le système est un registre officiel bilingue FR/AR uniquement.
from django.utils.translation import gettext_lazy as _  # noqa: E402

LANGUAGES = [
    ("fr", _("Français")),
    ("ar", _("العربية")),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# --------------------------------------------------------------------------- #
# Fichiers statiques et médias                                                 #
# --------------------------------------------------------------------------- #
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------- #
# REST framework                                                               #
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # Variante qui désactive le contrôle CSRF lorsque RSM_MODE_TEST=true.
        # En production (RSM_MODE_TEST=false), comportement standard DRF.
        "apps.utilisateurs.auth.SessionAuthSansCSRFEnTest",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    # Transforme les exceptions métier typées en réponses HTTP cohérentes.
    "EXCEPTION_HANDLER": "apps.core.exception_handler.rsm_exception_handler",
}

# --------------------------------------------------------------------------- #
# Paramètres RSM (zones gelées — valeurs stub)                                 #
# --------------------------------------------------------------------------- #
# Les paramètres ci-dessous matérialisent, dans le code, les points en attente
# d'arbitrage. Toute utilisation effective doit générer une alerte.
RSM_TIMESOURCE_MODE = config("RSM_TIMESOURCE_MODE", default="local_stub")
RSM_SEAL_MODE = config("RSM_SEAL_MODE", default="disabled")
RSM_ESIGN_MODE = config("RSM_ESIGN_MODE", default="disabled")
RSM_MFA_MODE = config("RSM_MFA_MODE", default="disabled")

# Mode TEST / RECETTE : permet la traversée fonctionnelle complète des
# parcours métier (dépôt, validation, modification, renouvellement,
# radiation, consultation) avec mécanismes probants simulés
# (horodatage technique, signature simulée, certificats marqués
# « TEST / NON OPPOSABLE »). À désactiver impérativement en production.
RSM_MODE_TEST = config("RSM_MODE_TEST", default="true").lower() in ("1", "true", "yes")

# --------------------------------------------------------------------------- #
# Interopérabilité bancaire — fiche F15 (prévision uniquement).
# Tant que ``RSM_INTEROP_BANQUES_MODE != "active"``, aucun endpoint
# /api/v1/banques/* n'est exposé : seuls les modèles d'agrément, de
# consentement et de journal d'accès existent en base. La bascule à
# ``"active"`` requiert la décision MO formelle (cf. F15 #1 à #12).
RSM_INTEROP_BANQUES_MODE = config("RSM_INTEROP_BANQUES_MODE", default="disabled")

# --------------------------------------------------------------------------- #
# Journal d'audit — protection append-only                                     #
# --------------------------------------------------------------------------- #
# Tout ajout au journal d'audit est irrévocable (art. 79, § 5.2).
# Les opérations de suppression / modification sont interdites au niveau
# applicatif et seront renforcées par des contraintes SQL (triggers).
AUDIT_ALLOW_DELETE = False
AUDIT_ALLOW_UPDATE = False
