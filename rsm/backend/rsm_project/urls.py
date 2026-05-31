"""URL routing racine du système RSM."""
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

# URLs non traduites : API technique et commutation de langue.
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/v1/", include("apps.core.api_urls")),
]

# URLs traduites : l'interface publique et les écrans internes doivent
# être servis dans les deux langues, avec préfixes /fr/ et /ar/.
urlpatterns += i18n_patterns(
    path(_("administration/"), admin.site.urls),
    path("", include("apps.core.urls")),
    prefix_default_language=True,
)
