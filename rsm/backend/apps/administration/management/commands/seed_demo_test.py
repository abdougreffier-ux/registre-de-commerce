"""
Commande de peuplement d'un environnement de TEST FONCTIONNEL.

    python manage.py seed_demo_test [--reset]

⚠️ ENVIRONNEMENT DE TEST UNIQUEMENT.

Les comptes, mots de passe et données produits par cette commande
sont strictement destinés à la démonstration et aux tests fonctionnels.
AUCUNE donnée créée n'est juridiquement opposable :
- les horodatages sont produits par le STUB local (L11/horodatage GELÉ) ;
- les empreintes SHA-256 sont non signées (L11/A5 GELÉ) ;
- les flags de signature électronique art. 88 sont fictifs (L11/A2 GELÉ) ;
- l'authentification est celle des sessions Django en développement.

Cette commande :
1. Charge les référentiels bilingues (`seed_referentiels`).
2. Crée 5 comptes de test couvrant les rôles applicatifs § 4.1 TDR.
3. Crée quelques parties (PP et PM) représentatives.
4. Produit plusieurs inscriptions à des états distincts :
   - une `INSCRITE` complète avec constituant, créancier, débiteur, bien ;
   - une `MODIFIEE` (après application d'une modification conforme) ;
   - une `RENOUVELEE` ;
   - une `RADIEE` (avec mention art. 92 al. 2) ;
   - une `REJETEE` (motif limitatif art. 80) ;
   - une `EN_CONTROLE_FORME` (en attente de validation).
5. Produit une demande de modification REJETEE pour l'art. 88 al. 4
   (démonstration du contrôle d'état final).

L'option `--reset` vide les tables métier avant de peupler
(⚠️ N'UTILISER QU'EN ENVIRONNEMENT DE TEST vide).
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.audit.services import ContexteAudit
from apps.biens.models import BienGreve
from apps.core.enums import CanalSaisie, MotifRejet, NaturesDroitInscrit
from apps.inscriptions.models import (
    Inscription,
    RoleInscriptionPartie,
)
from apps.inscriptions.services import (
    DonneesDemandeInscription,
    creer_demande,
    prononcer_rejet,
    valider_inscription,
)
from apps.modifications.models import (
    DemandeModification,
    MotifRefusModification,
    SnapshotInscription,
    StatutDemandeModification,
)
from apps.modifications.services import appliquer_modification
from apps.parties.models import Partie, RolePartie, TypePartie
from apps.radiations.models import (
    DemandeRadiation,
    FondementRadiation,
)
from apps.radiations.services import appliquer_radiation
from apps.renouvellements.models import DemandeRenouvellement
from apps.renouvellements.services import appliquer_renouvellement
from apps.utilisateurs.models import (
    AffectationRole,
    RoleApplicatif,
    Utilisateur,
)


# --------------------------------------------------------------------------- #
# Comptes de test — mots de passe FIXES pour démo. NON OPPOSABLES.             #
# --------------------------------------------------------------------------- #
COMPTES_TEST = [
    {
        "username": "admin_technique",
        "password": "test-rsm-admin-2026",
        "email": "admin.technique@test.rsm",
        "nom_affichage": "Administrateur Technique (TEST)",
        "is_staff": True,
        "is_superuser": True,
        "roles": [RoleApplicatif.ADMIN_TECHNIQUE],
    },
    {
        "username": "admin_fonctionnel",
        "password": "test-rsm-admin-2026",
        "email": "admin.fonctionnel@test.rsm",
        "nom_affichage": "Administrateur Fonctionnel (TEST)",
        "is_staff": True,
        "is_superuser": False,
        "roles": [RoleApplicatif.ADMIN_FONCTIONNEL],
    },
    {
        "username": "greffier",
        "password": "test-rsm-greffier-2026",
        "email": "greffier@test.rsm",
        "nom_affichage": "Greffier / Autorité de validation (TEST)",
        "is_staff": False,
        "is_superuser": False,
        "roles": [RoleApplicatif.AUTORITE_VALIDATION],
    },
    {
        "username": "agent_saisie",
        "password": "test-rsm-agent-2026",
        "email": "agent.saisie@test.rsm",
        "nom_affichage": "Agent de saisie (TEST)",
        "is_staff": False,
        "is_superuser": False,
        "roles": [RoleApplicatif.AGENT_SAISIE],
    },
    {
        "username": "auditeur",
        "password": "test-rsm-auditeur-2026",
        "email": "auditeur@test.rsm",
        "nom_affichage": "Auditeur / Contrôleur (TEST)",
        "is_staff": True,  # pour accéder à /api/v1/audit/* via _PermissionLectureAudit
        "is_superuser": False,
        "roles": [RoleApplicatif.AUDITEUR],
    },
    {
        "username": "declarant_externe",
        "password": "test-rsm-declarant-2026",
        "email": "declarant.externe@test.rsm",
        "nom_affichage": "Déclarant externe (TEST)",
        "is_staff": False,
        "is_superuser": False,
        "roles": [RoleApplicatif.DECLARANT_EXTERNE],
    },
    {
        "username": "prod_stats",
        "password": "test-rsm-stats-2026",
        "email": "prod.stats@test.rsm",
        "nom_affichage": "Producteur de statistiques (TEST)",
        "is_staff": False,
        "is_superuser": False,
        "roles": [RoleApplicatif.PROD_STATS],
    },
]


class Command(BaseCommand):
    help = (
        "Peuple un environnement de TEST FONCTIONNEL. "
        "NE PAS UTILISER EN PRODUCTION."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Purge les inscriptions et demandes de test avant de peupler.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write(self.style.WARNING(
                "⚠️  DJANGO_DEBUG=False — vérifier qu'il s'agit bien d'un "
                "environnement de test avant de continuer."
            ))

        if options.get("reset"):
            self._reset_donnees_test()

        # 1. Référentiels bilingues FR/AR (idempotent)
        self.stdout.write("→ Chargement des référentiels bilingues…")
        call_command("seed_referentiels")

        # 2. Comptes de test
        self.stdout.write("→ Création des comptes de test…")
        utilisateurs = self._creer_utilisateurs()

        # 3. Données métier
        self.stdout.write("→ Création des données métier (parties + biens)…")
        catalogue_parties = self._creer_parties()

        self.stdout.write("→ Production des inscriptions à différents statuts…")
        self._produire_inscriptions(utilisateurs, catalogue_parties)

        self.stdout.write(self.style.SUCCESS("\n✅ Environnement de test peuplé."))
        self._afficher_recapitulatif(utilisateurs)

    # ---------------------------------------------------------------- #
    def _reset_donnees_test(self):
        self.stdout.write(self.style.WARNING(
            "→ Purge des données métier (mode --reset)…"
        ))
        # Suppression physique autorisée UNIQUEMENT en mode reset test,
        # via l'ORM bas-niveau (contourne volontairement les gardes).
        from django.db import connection
        tables_test = [
            "modifications_snapshotinscription",
            "modifications_demandemodification",
            "renouvellements_demanderenouvellement",
            "radiations_demanderadiation",
            "inscriptions_piecejointe",
            "inscriptions_roleinscriptionpartie",
            "biens_biengreve",
            "inscriptions_inscription",
            "parties_partie",
        ]
        with connection.cursor() as cur:
            for t in tables_test:
                cur.execute(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE;")
        # La séquence du n° d'ordre est réinitialisée.
        from apps.inscriptions.models import SequenceNumeroOrdre
        SequenceNumeroOrdre.objects.filter(pk=1).delete()

    # ---------------------------------------------------------------- #
    def _creer_utilisateurs(self) -> dict[str, Utilisateur]:
        crees = {}
        for cfg in COMPTES_TEST:
            user, cree = Utilisateur.objects.get_or_create(
                username=cfg["username"],
                defaults={
                    "email": cfg["email"],
                    "nom_affichage": cfg["nom_affichage"],
                    "is_staff": cfg["is_staff"],
                    "is_superuser": cfg["is_superuser"],
                    "compte_actif": True,
                },
            )
            user.set_password(cfg["password"])
            user.is_staff = cfg["is_staff"]
            user.is_superuser = cfg["is_superuser"]
            user.compte_actif = True
            user.nom_affichage = cfg["nom_affichage"]
            user.email = cfg["email"]
            user.save()

            # Rôles applicatifs
            for role in cfg["roles"]:
                AffectationRole.objects.update_or_create(
                    utilisateur=user, role=role,
                    defaults={"actif": True, "motif_affectation": "Peuplement TEST"},
                )
            crees[cfg["username"]] = user
            self.stdout.write(
                f"   • {cfg['username']} ({', '.join(cfg['roles'])})"
            )
        return crees

    # ---------------------------------------------------------------- #
    def _creer_parties(self) -> dict[str, Partie]:
        """Crée un catalogue minimal de parties représentatives."""
        parties = {
            "constituant_sarl": Partie.objects.create(
                type_partie=TypePartie.PERSONNE_MORALE,
                denomination_sociale="Établissements Ould Ahmed SARL",
                numero_rc="RC/NKT/2024/0001",
                adresse="BP 123, Avenue du Roi Fayçal, Nouakchott",
                adresse_electronique="contact@ould-ahmed.test",
            ),
            "creancier_banque": Partie.objects.create(
                type_partie=TypePartie.PERSONNE_MORALE,
                denomination_sociale="Banque Mauritanienne de Commerce SA",
                numero_rc="RC/NKT/2010/0042",
                adresse="Immeuble BMC, Nouakchott",
                adresse_electronique="credit@bmc.test",
            ),
            "debiteur_pp": Partie.objects.create(
                type_partie=TypePartie.PERSONNE_PHYSIQUE,
                nom="MOHAMED",
                prenom="Sidi Ahmed",
                date_naissance=date(1980, 5, 12),
                lieu_naissance="Kiffa",
                adresse="Ilot K n°45, Nouakchott",
            ),
            "requerant_notaire": Partie.objects.create(
                type_partie=TypePartie.PERSONNE_PHYSIQUE,
                nom="SALL",
                prenom="Fatimata",
                date_naissance=date(1975, 3, 20),
                lieu_naissance="Rosso",
                adresse="Étude notariale, Nouakchott",
                adresse_electronique="fsall.notaire@test.rsm",
            ),
            # Homonymes pour la démonstration de l'art. 97 al. 2.
            "homonyme_1": Partie.objects.create(
                type_partie=TypePartie.PERSONNE_PHYSIQUE,
                nom="DUPONT", prenom="Pierre",
                date_naissance=date(1985, 1, 1),
                lieu_naissance="Nouakchott",
                adresse="Quartier Tevragh-Zeina, Nouakchott",
            ),
            "homonyme_2": Partie.objects.create(
                type_partie=TypePartie.PERSONNE_PHYSIQUE,
                nom="DUPONT", prenom="Paul",
                date_naissance=date(1990, 6, 15),
                lieu_naissance="Nouakchott",
                adresse="Quartier Tevragh-Zeina, Nouakchott",
            ),
        }
        return parties

    # ---------------------------------------------------------------- #
    def _peupler_roles_et_bien(
        self, inscription: Inscription, parties: dict, acteur,
    ):
        RoleInscriptionPartie.objects.create(
            inscription=inscription, partie=parties["constituant_sarl"],
            role=RolePartie.CONSTITUANT,
        )
        RoleInscriptionPartie.objects.create(
            inscription=inscription, partie=parties["creancier_banque"],
            role=RolePartie.CREANCIER,
        )
        RoleInscriptionPartie.objects.create(
            inscription=inscription, partie=parties["debiteur_pp"],
            role=RolePartie.DEBITEUR,
        )
        inscription.requerant = parties["requerant_notaire"]
        type(inscription).objects.filter(pk=inscription.pk).update(
            requerant=parties["requerant_notaire"],
        )
        BienGreve.objects.create(
            inscription=inscription,
            description_fr="Lot d'outillage industriel — atelier de Nouakchott",
            description_ar="مجموعة من العدة الصناعية — ورشة نواكشوط",
            marque="ACME", modele="X-100", numero_serie="SN-TEST-0001",
            annee=2022,
            cree_par=acteur, modifie_par=acteur,
        )

    @transaction.atomic
    def _produire_inscriptions(self, users, parties):
        agent = users["agent_saisie"]
        greffier = users["greffier"]

        # -- 1. Inscription INSCRITE simple ---------------------------- #
        d1 = creer_demande(
            donnees=DonneesDemandeInscription(
                canal_saisie=CanalSaisie.GUICHET_PAPIER,
                nature_droit=NaturesDroitInscrit.NANTISSEMENT_OUTILLAGE,
                somme_garantie=Decimal("1500000.00"),
                monnaie="MRU",
                duree_en_jours=365,
                adresse_electronique_notifications="contact@ould-ahmed.test",
            ),
            acteur=agent,
        )
        self._peupler_roles_et_bien(d1, parties, agent)
        inscription_1 = valider_inscription(inscription=d1, acteur=greffier)
        self.stdout.write(
            f"   • Inscription INSCRITE : {inscription_1.numero_ordre}"
        )

        # -- 2. Inscription MODIFIEE (modification art. 88 appliquée) -- #
        d2 = creer_demande(
            donnees=DonneesDemandeInscription(
                canal_saisie=CanalSaisie.GUICHET_PAPIER,
                nature_droit=NaturesDroitInscrit.NANTISSEMENT_FONDS_COMMERCE,
                somme_garantie=Decimal("3000000.00"),
                monnaie="MRU", duree_en_jours=730,
            ),
            acteur=agent,
        )
        self._peupler_roles_et_bien(d2, parties, agent)
        inscription_2 = valider_inscription(inscription=d2, acteur=greffier)
        dem_mod = DemandeModification.objects.create(
            inscription=inscription_2,
            objet_modification_fr="Augmentation de la somme garantie",
            objet_modification_ar="زيادة المبلغ المضمون",
            diff_propose={"scalaires": {"somme_garantie": "4500000.00"}},
            accord_createur_confirme=True,
            accord_constituant_confirme=True,
            cree_par=agent, modifie_par=agent,
        )
        appliquer_modification(demande=dem_mod, acteur=greffier)
        self.stdout.write(
            f"   • Inscription MODIFIEE : {inscription_2.numero_ordre}"
        )

        # -- 3. Inscription RENOUVELEE -------------------------------- #
        d3 = creer_demande(
            donnees=DonneesDemandeInscription(
                canal_saisie=CanalSaisie.GUICHET_PAPIER,
                nature_droit=NaturesDroitInscrit.NANTISSEMENT_STOCKS,
                somme_garantie=Decimal("500000.00"),
                monnaie="MRU", duree_en_jours=180,
            ),
            acteur=agent,
        )
        self._peupler_roles_et_bien(d3, parties, agent)
        inscription_3 = valider_inscription(inscription=d3, acteur=greffier)
        dem_ren = DemandeRenouvellement.objects.create(
            inscription=inscription_3, cree_par=agent, modifie_par=agent,
        )
        appliquer_renouvellement(demande=dem_ren, acteur=greffier)
        self.stdout.write(
            f"   • Inscription RENOUVELEE : {inscription_3.numero_ordre}"
        )

        # -- 4. Inscription RADIEE ------------------------------------- #
        d4 = creer_demande(
            donnees=DonneesDemandeInscription(
                canal_saisie=CanalSaisie.GUICHET_PAPIER,
                nature_droit=NaturesDroitInscrit.NANTISSEMENT_CREANCE,
                somme_garantie=Decimal("250000.00"),
                monnaie="MRU", duree_en_jours=365,
            ),
            acteur=agent,
        )
        self._peupler_roles_et_bien(d4, parties, agent)
        inscription_4 = valider_inscription(inscription=d4, acteur=greffier)
        dem_rad = DemandeRadiation.objects.create(
            inscription=inscription_4,
            fondement=FondementRadiation.CONSENTEMENT,
            nom_constituant="",
            denomination_constituant="Établissements Ould Ahmed SARL",
            adresse_constituant="BP 123, Nouakchott",
            numero_rc_constituant="RC/NKT/2024/0001",
            cree_par=agent, modifie_par=agent,
        )
        appliquer_radiation(demande=dem_rad, acteur=greffier)
        self.stdout.write(
            f"   • Inscription RADIEE : {inscription_4.numero_ordre}"
        )

        # -- 5. Inscription REJETEE (motif art. 80) -------------------- #
        d5 = creer_demande(
            donnees=DonneesDemandeInscription(
                canal_saisie=CanalSaisie.GUICHET_PAPIER,
                nature_droit=NaturesDroitInscrit.NANTISSEMENT_COMPTE_BANCAIRE,
                somme_garantie=Decimal("100000.00"),
                monnaie="MRU", duree_en_jours=90,
            ),
            acteur=agent,
        )
        # Pas de peuplement complet — la demande est rejetée au contrôle de forme.
        prononcer_rejet(
            inscription=d5,
            motif=MotifRejet.INFORMATIONS_ILLISIBLES,
            commentaire_fr="Document scanné de qualité insuffisante (TEST).",
            commentaire_ar="الوثيقة الممسوحة ضوئيا ذات جودة غير كافية (اختبار).",
            acteur=greffier,
        )
        self.stdout.write(
            f"   • Inscription REJETEE (motif art. 80) : {d5.reference_demande}"
        )

        # -- 6. Inscription EN_CONTROLE_FORME (en attente de validation) #
        d6 = creer_demande(
            donnees=DonneesDemandeInscription(
                canal_saisie=CanalSaisie.PORTAIL_ELECTRONIQUE,
                nature_droit=NaturesDroitInscrit.NANTISSEMENT_DROITS_ASSOCIES,
                somme_garantie=Decimal("750000.00"),
                monnaie="MRU", duree_en_jours=540,
            ),
            acteur=users["declarant_externe"],
        )
        # Peuplement complet mais sans validation — attend le greffier.
        self._peupler_roles_et_bien(d6, parties, users["declarant_externe"])
        self.stdout.write(
            f"   • Inscription EN_CONTROLE_FORME : {d6.reference_demande} "
            f"(à valider par le greffier via POST /valider/)"
        )

        # -- 7. Démonstration — demande de modification REJETEE art. 88 al. 4 #
        # On tente de retirer le dernier constituant actif de inscription_1 :
        # l'état final serait 0 constituant → REJETEE avec motif structuré.
        lien_constituant = RoleInscriptionPartie.objects.filter(
            inscription=inscription_1, role=RolePartie.CONSTITUANT, actif=True,
        ).first()
        if lien_constituant:
            dem_rejet = DemandeModification.objects.create(
                inscription=inscription_1,
                objet_modification_fr=(
                    "Tentative de retrait du dernier constituant "
                    "(démonstration du contrôle art. 88 dernier alinéa)"
                ),
                objet_modification_ar=(
                    "محاولة إزالة آخر منشئ (اختبار لمراقبة المادة 88 الفقرة الأخيرة)"
                ),
                diff_propose={"parties": {"retirer": [lien_constituant.pk]}},
                accord_createur_confirme=True,
                accord_constituant_confirme=True,
                cree_par=agent, modifie_par=agent,
            )
            try:
                appliquer_modification(demande=dem_rejet, acteur=greffier)
            except Exception as exc:  # ModificationSansEffet attendu
                pass
            self.stdout.write(
                f"   • Modification REJETEE art. 88 al. 4 : demande #{dem_rejet.pk} "
                f"(motif {MotifRefusModification.ETAT_FINAL_CONSTITUANT_ABSENT})"
            )

    # ---------------------------------------------------------------- #
    def _afficher_recapitulatif(self, users):
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("=" * 70))
        self.stdout.write(self.style.HTTP_INFO(" COMPTES DE TEST — NON OPPOSABLES"))
        self.stdout.write(self.style.HTTP_INFO("=" * 70))
        self.stdout.write(
            f"{'Utilisateur':<22} {'Mot de passe':<30} Rôle applicatif"
        )
        self.stdout.write("-" * 70)
        for cfg in COMPTES_TEST:
            self.stdout.write(
                f"{cfg['username']:<22} {cfg['password']:<30} "
                f"{', '.join(cfg['roles'])}"
            )
        self.stdout.write(self.style.HTTP_INFO("=" * 70))
        self.stdout.write(
            "\n⚠️  Ces mots de passe sont des VALEURS DE TEST FIXES.\n"
            "    Ne JAMAIS les utiliser en production.\n"
            "\n"
            "→ Admin Django  : /fr/administration/  ou  /ar/administration/\n"
            "→ API racine    : /api/v1/\n"
            "→ Sonde santé   : /fr/sante/\n"
        )
