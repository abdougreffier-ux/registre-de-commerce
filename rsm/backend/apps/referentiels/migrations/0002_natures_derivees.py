"""
Data migration : ajoute deux natures de droit paramétrables dérivées
des nouveaux parcours d'inscription contextuels (refonte MO du
2026-05-31).

Le décret 2021-033 (art. 76) liste 12 natures limitatives. Les
parcours « réserve de propriété » et « crédit-bail » ne disposent
pas d'équivalent direct dans cette liste, mais le référentiel
``LibelleNatureDroit`` est désormais paramétrable par le greffier
(directive MO du 2026-05-30). Cette migration ajoute deux entrées
paramétrables pour que les formulaires contextuels puissent
référencer une nature sans imposer à l'utilisateur de la choisir.

Le parcours « privilège du vendeur » réutilise la clé existante
``priv_vendeur_fonds``.

Non rétroactif : si une entrée existe déjà (cle = cible), on ne
l'écrase pas.
"""
from django.db import migrations


NATURES_DERIVES = [
    {
        "cle": "reserve_propriete",
        "libelle_fr": "Vente avec réserve du droit de propriété",
        "libelle_ar": "البيع مع الاحتفاظ بحق الملكية",
        "description_fr": (
            "Sûreté dérivée du parcours « vente avec réserve du droit de "
            "propriété ». Le vendeur conserve la propriété jusqu'au "
            "paiement intégral du prix par l'acquéreur."
        ),
        "description_ar": (
            "ضمان مشتق من مسار « البيع مع الاحتفاظ بحق الملكية ». "
            "يحتفظ البائع بالملكية حتى السداد الكامل للثمن من قبل المشتري."
        ),
        "ordre": 100,
    },
    {
        "cle": "credit_bail",
        "libelle_fr": "Contrat de crédit-bail",
        "libelle_ar": "عقد الإيجار التمويلي",
        "description_fr": (
            "Sûreté dérivée du parcours « contrat de crédit-bail ». Le "
            "crédit-bailleur conserve la propriété du bien pendant "
            "l'exécution du contrat."
        ),
        "description_ar": (
            "ضمان مشتق من مسار « عقد الإيجار التمويلي ». يحتفظ المؤجر "
            "التمويلي بملكية المال أثناء تنفيذ العقد."
        ),
        "ordre": 101,
    },
]


def seed_natures_derivees(apps, schema_editor):
    LibelleNatureDroit = apps.get_model("referentiels", "LibelleNatureDroit")
    for n in NATURES_DERIVES:
        LibelleNatureDroit.objects.get_or_create(
            cle=n["cle"],
            defaults={
                "libelle_fr": n["libelle_fr"],
                "libelle_ar": n["libelle_ar"],
                "description_fr": n["description_fr"],
                "description_ar": n["description_ar"],
                "ordre": n["ordre"],
                "actif": True,
            },
        )


def remove_natures_derivees(apps, schema_editor):
    LibelleNatureDroit = apps.get_model("referentiels", "LibelleNatureDroit")
    LibelleNatureDroit.objects.filter(
        cle__in=[n["cle"] for n in NATURES_DERIVES]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("referentiels", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_natures_derivees, remove_natures_derivees),
    ]
