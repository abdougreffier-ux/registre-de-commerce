-- ============================================================
-- DONNÉES INITIALES - Registre du Commerce Mauritanie
-- ============================================================

-- ── Extension ─────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- ── Nationalités ──────────────────────────────────────────────────────────────
INSERT INTO nationalites (code, libelle_fr, libelle_ar) VALUES
  ('MR',  'Mauritanienne',    'موريتانية'),
  ('SN',  'Sénégalaise',      'سنغالية'),
  ('ML',  'Malienne',         'مالية'),
  ('MA',  'Marocaine',        'مغربية'),
  ('DZ',  'Algérienne',       'جزائرية'),
  ('TN',  'Tunisienne',       'تونسية'),
  ('EG',  'Égyptienne',       'مصرية'),
  ('LY',  'Libyenne',         'ليبية'),
  ('FR',  'Française',        'فرنسية'),
  ('CN',  'Chinoise',         'صينية'),
  ('IN',  'Indienne',         'هندية'),
  ('LB',  'Libanaise',        'لبنانية'),
  ('SY',  'Syrienne',         'سورية'),
  ('NG',  'Nigériane',        'نيجيرية'),
  ('GN',  'Guinéenne',        'غينية'),
  ('CI',  'Ivoirienne',       'إيفوارية'),
  ('AU',  'Autre',            'أخرى')
ON CONFLICT (code) DO NOTHING;

-- ── Formes Juridiques ──────────────────────────────────────────────────────────
INSERT INTO formes_juridiques (code, libelle_fr, libelle_ar, type_entite) VALUES
  -- Personnes Physiques
  ('EI',    'Entreprise Individuelle',                'مقاولة فردية',                     'PH'),
  -- Personnes Morales
  ('SARL',  'Société à Responsabilité Limitée',       'شركة ذات مسؤولية محدودة',           'PM'),
  ('SA',    'Société Anonyme',                        'شركة مساهمة',                       'PM'),
  ('SNC',   'Société en Nom Collectif',               'شركة التضامن',                      'PM'),
  ('SCS',   'Société en Commandite Simple',           'شركة التوصية البسيطة',              'PM'),
  ('SCA',   'Société en Commandite par Actions',      'شركة التوصية بالأسهم',              'PM'),
  ('GIE',   'Groupement d''Intérêt Économique',       'مجموعة ذات مصلحة اقتصادية',        'PM'),
  ('COOP',  'Coopérative',                            'تعاونية',                           'PM'),
  ('ASSO',  'Association',                            'جمعية',                             'PM'),
  ('ONG',   'Organisation Non Gouvernementale',       'منظمة غير حكومية',                 'PM'),
  ('FOND',  'Fondation',                              'مؤسسة',                             'PM'),
  ('EP',    'Établissement Public',                   'مؤسسة عمومية',                      'PM'),
  -- Succursales
  ('SUCC',  'Succursale de société étrangère',        'فرع شركة أجنبية',                   'SC')
ON CONFLICT (code) DO NOTHING;

-- ── Domaines d'activités ───────────────────────────────────────────────────────
INSERT INTO domaines_activites (code, libelle_fr, libelle_ar) VALUES
  ('AG',  'Agriculture, Élevage, Pêche',               'الزراعة والتربية والصيد'),
  ('MIN', 'Mines et Carrières',                        'المناجم والمحاجر'),
  ('IND', 'Industrie et Transformation',               'الصناعة والتحويل'),
  ('BTP', 'Bâtiment et Travaux Publics',               'البناء والأشغال العمومية'),
  ('COM', 'Commerce Général',                          'التجارة العامة'),
  ('IMP', 'Import / Export',                           'الاستيراد والتصدير'),
  ('TRN', 'Transport et Logistique',                   'النقل واللوجستيك'),
  ('TLM', 'Télécommunications et TIC',                 'الاتصالات وتكنولوجيا المعلومات'),
  ('FIN', 'Services Financiers et Assurances',         'الخدمات المالية والتأمين'),
  ('IMM', 'Immobilier et Promotion',                   'العقارات والترقية'),
  ('TOR', 'Tourisme et Hôtellerie',                    'السياحة والفندقة'),
  ('SAN', 'Santé et Pharmacie',                        'الصحة والصيدلة'),
  ('EDU', 'Éducation et Formation',                    'التعليم والتكوين'),
  ('CON', 'Conseil et Services aux Entreprises',       'الاستشارة وخدمات المؤسسات'),
  ('ENE', 'Énergie et Environnement',                  'الطاقة والبيئة'),
  ('ART', 'Artisanat et Arts',                         'الحرف والفنون'),
  ('AUT', 'Autres activités',                          'أنشطة أخرى')
ON CONFLICT (code) DO NOTHING;

-- ── Fonctions ─────────────────────────────────────────────────────────────────
INSERT INTO fonctions (code, libelle_fr, libelle_ar, type_entite) VALUES
  ('GER',    'Gérant',                          'مدير',              'PM'),
  ('GER2',   'Co-Gérant',                       'مدير مشترك',        'PM'),
  ('PDG',    'Président Directeur Général',     'الرئيس المدير العام','PM'),
  ('DG',     'Directeur Général',               'مدير عام',          'PM'),
  ('PCA',    'Président du Conseil d''Administration', 'رئيس مجلس الإدارة','PM'),
  ('ADM',    'Administrateur',                  'عضو مجلس الإدارة',  'PM'),
  ('DAF',    'Directeur Administratif et Financier', 'المدير الإداري والمالي','PM'),
  ('COM_SC', 'Commandité',                      'متضامن',            'PM'),
  ('REPR',   'Représentant légal',              'ممثل قانوني',       'SC'),
  ('DGS',    'Directeur Général de Succursale', 'مدير عام الفرع',    'SC'),
  ('COM_PH', 'Commerçant',                      'تاجر',              'PH')
ON CONFLICT (code) DO NOTHING;

-- ── Types de Documents ────────────────────────────────────────────────────────
INSERT INTO types_documents (code, libelle_fr, obligatoire, type_demande) VALUES
  ('CNI',        'Copie de la carte nationale d''identité',          TRUE,  'IMMAT'),
  ('PASSEPORT',  'Copie du passeport',                               FALSE, 'IMMAT'),
  ('ACTE_NAIS',  'Extrait d''acte de naissance',                     FALSE, 'IMMAT'),
  ('STAT',       'Statuts de la société',                            TRUE,  'IMMAT'),
  ('PV_CONST',   'PV de l''Assemblée Générale Constitutive',         TRUE,  'IMMAT'),
  ('PV_AG',      'Procès-verbal d''Assemblée Générale',              TRUE,  'DEPOT'),
  ('BILAN',      'Bilan et états financiers',                        TRUE,  'DEPOT'),
  ('CERTIF_BANQ','Certificat de blocage de fonds',                   FALSE, 'IMMAT'),
  ('LEGIS',      'Légalisation notariale',                           FALSE, 'IMMAT'),
  ('BAIL',       'Contrat de bail ou titre de propriété',            FALSE, 'IMMAT'),
  ('CAS_JUD',    'Casier judiciaire',                                TRUE,  'IMMAT'),
  ('DECL_FISC',  'Déclaration fiscale (NIF)',                        FALSE, 'IMMAT'),
  ('ACTE_CESS',  'Acte de cession authentique',                      TRUE,  'CESSION'),
  ('ACTE_MODIF', 'Acte de modification',                             TRUE,  'MODIF'),
  ('ACTE_DISS',  'Acte de dissolution',                              TRUE,  'RADIA'),
  ('DEC_RADIA',  'Déclaration de radiation',                         TRUE,  'RADIA'),
  ('PROC_VERBAL','Procès-verbal de liquidation',                     FALSE, 'RADIA')
ON CONFLICT (code) DO NOTHING;

-- ── Types de Demandes ─────────────────────────────────────────────────────────
INSERT INTO types_demandes (code, libelle_fr, libelle_ar, type_entite, delai_traitement) VALUES
  ('IMMAT_PH',   'Immatriculation Personne Physique',     'تسجيل شخص طبيعي',            'PH', 3),
  ('IMMAT_PM',   'Immatriculation Personne Morale',       'تسجيل شخص معنوي',            'PM', 5),
  ('IMMAT_SC',   'Immatriculation Succursale',            'تسجيل فرع',                  'SC', 7),
  ('MODIF_PH',   'Modification Personne Physique',        'تعديل بيانات شخص طبيعي',    'PH', 3),
  ('MODIF_PM',   'Modification Personne Morale',          'تعديل بيانات شخص معنوي',    'PM', 5),
  ('MODIF_SC',   'Modification Succursale',               'تعديل بيانات فرع',          'SC', 5),
  ('RADIA_PH',   'Radiation Personne Physique',           'شطب شخص طبيعي',             'PH', 3),
  ('RADIA_PM',   'Radiation Personne Morale',             'شطب شخص معنوي',             'PM', 5),
  ('RADIA_SC',   'Radiation Succursale',                  'شطب فرع',                   'SC', 5),
  ('CESS_FC',    'Cession Fonds de Commerce',             'تنازل على المحل التجاري',   'PH', 5),
  ('CESS_PS',    'Cession Parts Sociales',                'تنازل على الحصص',           'PM', 7),
  ('CESS_ACT',   'Cession d''Actions',                   'تنازل على الأسهم',          'PM', 7),
  ('DEPOT_AG',   'Dépôt PV Assemblée Générale',           'إيداع محضر الجمعية العامة', 'PM', 2),
  ('DEPOT_BILAN','Dépôt Bilan Annuel',                    'إيداع الميزانية السنوية',   'PM', 2)
ON CONFLICT (code) DO NOTHING;

-- ── Localités (Wilayas de Mauritanie) ─────────────────────────────────────────
INSERT INTO localites (code, libelle_fr, libelle_ar, type) VALUES
  ('NKC',  'Nouakchott',              'نواكشوط',        'WILAYA'),
  ('NDB',  'Nouadhibou',              'نواذيبو',        'WILAYA'),
  ('ROS',  'Rosso',                   'روصو',           'WILAYA'),
  ('KIF',  'Kiffa',                   'كيفة',           'WILAYA'),
  ('KAE',  'Kaédi',                   'كيهيدي',        'WILAYA'),
  ('ZOU',  'Zouerate',                'زويرات',         'WILAYA'),
  ('ATR',  'Atar',                    'آطار',           'WILAYA'),
  ('TIC',  'Tidjikja',               'تجكجة',          'WILAYA'),
  ('AIO',  'Aïoun el-Atrouss',       'عيون العتروس',   'WILAYA'),
  ('SEL',  'Sélibaby',               'سيليبابي',       'WILAYA'),
  ('NEM',  'Néma',                    'نعمة',           'WILAYA'),
  ('AKJ',  'Akjoujt',                'أكجوجت',         'WILAYA'),
  ('MOG',  'Maghama',                 'مقامة',          'WILAYA'),
  ('BAB',  'Bababe',                  'بابابي',         'WILAYA'),
  ('MAL',  'Mal',                     'مال',            'WILAYA')
ON CONFLICT (code) DO NOTHING;

-- ── Tarifs ────────────────────────────────────────────────────────────────────
INSERT INTO tarifs (code, libelle_fr, type_demande, montant, devise) VALUES
  ('IMM_PH',   'Immatriculation Personne Physique',    'IMMAT_PH',  5000,   'MRU'),
  ('IMM_PM',   'Immatriculation Personne Morale',      'IMMAT_PM',  20000,  'MRU'),
  ('IMM_SC',   'Immatriculation Succursale',           'IMMAT_SC',  50000,  'MRU'),
  ('MOD_PH',   'Modification Personne Physique',       'MODIF_PH',  3000,   'MRU'),
  ('MOD_PM',   'Modification Personne Morale',         'MODIF_PM',  5000,   'MRU'),
  ('RAD_PH',   'Radiation Personne Physique',          'RADIA_PH',  2000,   'MRU'),
  ('RAD_PM',   'Radiation Personne Morale',            'RADIA_PM',  5000,   'MRU'),
  ('CESS',     'Cession (tout type)',                  'CESS_FC',   10000,  'MRU'),
  ('DEP_BILAN','Dépôt bilan annuel',                   'DEPOT_BILAN',3000,  'MRU'),
  ('EXTRAIT',  'Extrait du Registre du Commerce',      NULL,         2000,  'MRU'),
  ('ATTESTAT', 'Attestation d''immatriculation',       NULL,         2000,  'MRU'),
  ('CERT_NEG', 'Certificat Négatif (Nom commercial)',  NULL,         3000,  'MRU')
ON CONFLICT (code) DO NOTHING;

-- ── Rôles ─────────────────────────────────────────────────────────────────────
-- Rôles alignés sur apps/core/permissions.py (GREFFIER / AGENT_GU / AGENT_TRIBUNAL)
-- Un superuser Django (is_superuser=True) est automatiquement traité comme GREFFIER.
INSERT INTO roles (code, libelle, libelle_ar, description) VALUES
  ('GREFFIER',       'Greffier',                 'كاتب الضبط',
   'Accès complet — validation, impression, paramétrage, gestion des utilisateurs'),
  ('AGENT_TRIBUNAL', 'Agent du Tribunal',        'عون المحكمة',
   'Accès à tous les modules métier (dossiers créés par lui uniquement)'),
  ('AGENT_GU',       'Agent Guichet Unique',     'عون الشباك الموحد',
   'Création des immatriculations uniquement (RC type IMMATRICULATION)')
ON CONFLICT (code) DO NOTHING;

-- ── Postes ────────────────────────────────────────────────────────────────────
INSERT INTO postes (code, libelle_fr, libelle_ar) VALUES
  ('GRF',  'Greffier',                            'كاتب الضبط'),
  ('GC',   'Greffier en Chef',                    'رئيس الكتابة'),
  ('AGT',  'Agent du Tribunal',                   'عون المحكمة'),
  ('AGU',  'Agent Guichet Unique',                'عون الشباك الموحد'),
  ('INFO', 'Informaticien',                       'تقني معلوماتي')
ON CONFLICT (code) DO NOTHING;

-- ── Séquences de numérotation ────────────────────────────────────────────────
INSERT INTO sequences_numerotation (code, prefixe, annee, dernier_num, nb_chiffres) VALUES
  ('RA',     'RA',  EXTRACT(YEAR FROM NOW()), 0, 6),
  ('CHRONO', 'RC',  EXTRACT(YEAR FROM NOW()), 0, 6),
  ('DMD',    'DMD', EXTRACT(YEAR FROM NOW()), 0, 6),
  ('DEP',    'DEP', EXTRACT(YEAR FROM NOW()), 0, 6),
  ('MOD',    'MOD', EXTRACT(YEAR FROM NOW()), 0, 6),
  ('RAD',    'RAD', EXTRACT(YEAR FROM NOW()), 0, 6),
  ('CES',    'CES', EXTRACT(YEAR FROM NOW()), 0, 6)
ON CONFLICT (code) DO NOTHING;

-- ── Utilisateur Greffier par défaut ──────────────────────────────────────────
-- Mot de passe : INUTILISABLE par défaut (marqueur Django "!")
-- Après le chargement, définir le mot de passe via :
--   python manage.py changepassword admin
-- ou depuis l'interface Django Admin (/admin/).
--
-- Colonnes Django (AbstractBaseUser + PermissionsMixin) :
--   password      → champ natif Django  (ex-"password_hash" du schema.sql brut)
--   is_staff      → requis pour l'accès à /admin/
--   is_superuser  → traité comme GREFFIER dans permissions.py (get_role)
INSERT INTO utilisateurs (nom, prenom, login, email, password, actif, is_staff, is_superuser)
SELECT 'Administrateur', 'Système', 'admin', 'admin@registre.mr',
       '!',   -- mot de passe inutilisable — à définir via manage.py changepassword
       TRUE, TRUE, TRUE
WHERE NOT EXISTS (SELECT 1 FROM utilisateurs WHERE login = 'admin');

-- Lier au rôle GREFFIER (accès complet — cohérent avec is_superuser=TRUE)
UPDATE utilisateurs u
SET role_id = r.id
FROM roles r
WHERE u.login = 'admin' AND r.code = 'GREFFIER' AND u.role_id IS NULL;

-- ── Message de confirmation ───────────────────────────────────────────────────
DO $$
BEGIN
  RAISE NOTICE '✅ Données initiales chargées avec succès.';
  RAISE NOTICE '   Greffier par défaut : login=admin';
  RAISE NOTICE '   ⚠️  Mot de passe non défini — exécuter : python manage.py changepassword admin';
END $$;
