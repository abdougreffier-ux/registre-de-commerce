"""
Admin — référentiels bilingues.

§ 4.1 TDR — « Administrateur fonctionnel : gère les utilisateurs, les
rôles, les référentiels… ». L'édition des libellés FR/AR et des
descriptions est donc autorisée pour un administrateur fonctionnel,
mais :

- la clé technique (``cle``) est en lecture seule : elle correspond
  EXACTEMENT à l'énumération limitative du décret (``apps.core.enums``) ;
- la suppression est interdite : toute entrée correspond à un motif
  limitatif du décret, qu'aucun administrateur ne peut retirer. La
  désactivation éventuelle passe par le champ ``actif=False``.
- l'ajout est interdit côté admin : la liste des clés est fermée, la
  génération initiale se fait via ``python manage.py seed_referentiels``.
"""
from django.contrib import admin

from apps.core.admin_base import EditionRestreinteAdmin
from apps.referentiels import models as M


class _LibelleAdmin(EditionRestreinteAdmin):
    list_display = (
        "cle", "libelle_fr", "libelle_ar",
        "langue_faisant_foi", "actif", "ordre",
    )
    list_filter = ("actif", "langue_faisant_foi")
    search_fields = ("cle", "libelle_fr", "libelle_ar")
    ordering = ("ordre", "cle")
    readonly_fields = ("cle",)

    def has_add_permission(self, request):  # noqa: D401
        # L'ajout est réservé au seeding officiel (liste limitative
        # du décret) ; aucun administrateur ne peut ajouter une clé.
        return False


for modele in (
    M.LibelleNatureDroit,
    M.LibelleMotifRejet,
    M.LibelleCanalSaisie,
    M.LibelleCritereRecherche,
    M.LibelleTypeCertificat,
):
    admin.site.register(modele, _LibelleAdmin)
