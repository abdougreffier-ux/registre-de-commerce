-- ============================================================
-- SCHEMA PostgreSQL - Registre du Commerce (RC)
-- Mauritanie
-- ============================================================

-- Extension pour UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- ============================================================
-- TABLES DE PARAMETRAGE
-- ============================================================

CREATE TABLE nationalites (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(5) UNIQUE NOT NULL,
    libelle_fr  VARCHAR(100) NOT NULL,
    libelle_ar  VARCHAR(100),
    actif       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE formes_juridiques (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    libelle_fr  VARCHAR(150) NOT NULL,
    libelle_ar  VARCHAR(150),
    type_entite VARCHAR(20) CHECK (type_entite IN ('PH','PM','SC','ALL')) DEFAULT 'ALL',
    actif       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE domaines_activites (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    libelle_fr  VARCHAR(200) NOT NULL,
    libelle_ar  VARCHAR(200),
    actif       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fonctions (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    libelle_fr  VARCHAR(100) NOT NULL,
    libelle_ar  VARCHAR(100),
    type_entite VARCHAR(20) CHECK (type_entite IN ('PH','PM','SC','ALL')) DEFAULT 'ALL',
    actif       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE types_documents (
    id            SERIAL PRIMARY KEY,
    code          VARCHAR(30) UNIQUE NOT NULL,
    libelle_fr    VARCHAR(200) NOT NULL,
    libelle_ar    VARCHAR(200),
    type_demande  VARCHAR(20),  -- IMMAT, MODIF, RADIA, CESSION, DEPOT
    obligatoire   BOOLEAN DEFAULT FALSE,
    actif         BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE types_demandes (
    id            SERIAL PRIMARY KEY,
    code          VARCHAR(30) UNIQUE NOT NULL,
    libelle_fr    VARCHAR(200) NOT NULL,
    libelle_ar    VARCHAR(200),
    type_entite   VARCHAR(20) CHECK (type_entite IN ('PH','PM','SC','ALL')) DEFAULT 'ALL',
    delai_traitement INTEGER DEFAULT 5,  -- jours ouvrables
    actif         BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tarifs (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(30) UNIQUE NOT NULL,
    libelle_fr      VARCHAR(200) NOT NULL,
    type_demande    VARCHAR(30),
    montant         NUMERIC(12,2) NOT NULL DEFAULT 0,
    devise          VARCHAR(5) DEFAULT 'MRU',
    date_effet      DATE DEFAULT CURRENT_DATE,
    date_fin        DATE,
    actif           BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE localites (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    libelle_fr  VARCHAR(150) NOT NULL,
    libelle_ar  VARCHAR(150),
    type        VARCHAR(20) CHECK (type IN ('WILAYA','MOUGHATAA','COMMUNE')) DEFAULT 'WILAYA',
    parent_id   INTEGER REFERENCES localites(id),
    actif       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE champs_modif (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(50) UNIQUE NOT NULL,
    libelle_fr      VARCHAR(200) NOT NULL,
    libelle_ar      VARCHAR(200),
    table_cible     VARCHAR(100),
    champ_cible     VARCHAR(100),
    type_entite     VARCHAR(20) DEFAULT 'ALL',
    actif           BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- GESTION DES UTILISATEURS
-- ============================================================

CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(30) UNIQUE NOT NULL,
    libelle     VARCHAR(100) NOT NULL,
    description TEXT,
    actif       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE permissions (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50) UNIQUE NOT NULL,
    libelle     VARCHAR(100) NOT NULL,
    module      VARCHAR(50),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE roles_permissions (
    role_id       INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE postes (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(30) UNIQUE NOT NULL,
    libelle_fr  VARCHAR(150) NOT NULL,
    libelle_ar  VARCHAR(150),
    actif       BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE utilisateurs (
    id              SERIAL PRIMARY KEY,
    uuid            UUID DEFAULT uuid_generate_v4() UNIQUE,
    matricule       VARCHAR(30) UNIQUE,
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100),
    login           VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    email           VARCHAR(150) UNIQUE,
    telephone       VARCHAR(20),
    role_id         INTEGER REFERENCES roles(id),
    poste_id        INTEGER REFERENCES postes(id),
    localite_id     INTEGER REFERENCES localites(id),
    actif           BOOLEAN DEFAULT TRUE,
    derniere_cnx    TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ENTITES PRINCIPALES
-- ============================================================

-- Personne Physique (commerçant individuel)
CREATE TABLE personnes_physiques (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    nni                 VARCHAR(20) UNIQUE,              -- Numéro National d'Identification
    nom                 VARCHAR(150) NOT NULL,
    prenom              VARCHAR(150),
    nom_ar              VARCHAR(150),
    prenom_ar           VARCHAR(150),
    date_naissance      DATE,
    lieu_naissance      VARCHAR(200),
    sexe                CHAR(1) CHECK (sexe IN ('M','F')),
    nationalite_id      INTEGER REFERENCES nationalites(id),
    adresse             TEXT,
    adresse_ar          TEXT,
    ville               VARCHAR(100),
    localite_id         INTEGER REFERENCES localites(id),
    telephone           VARCHAR(20),
    email               VARCHAR(150),
    profession          VARCHAR(150),
    situation_matrimoniale VARCHAR(20),
    nom_pere            VARCHAR(150),
    nom_mere            VARCHAR(150),
    num_passeport       VARCHAR(50),
    num_carte_identite  VARCHAR(50),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- Personne Morale (société, association, etc.)
CREATE TABLE personnes_morales (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    denomination        VARCHAR(300) NOT NULL,
    denomination_ar     VARCHAR(300),
    sigle               VARCHAR(50),
    forme_juridique_id  INTEGER REFERENCES formes_juridiques(id),
    capital_social      NUMERIC(15,2),
    devise_capital      VARCHAR(5) DEFAULT 'MRU',
    duree_societe       INTEGER,               -- années
    date_constitution   DATE,
    date_ag             DATE,                  -- date assemblée générale
    siege_social        TEXT,
    siege_social_ar     TEXT,
    ville               VARCHAR(100),
    localite_id         INTEGER REFERENCES localites(id),
    telephone           VARCHAR(20),
    fax                 VARCHAR(20),
    email               VARCHAR(150),
    site_web            VARCHAR(200),
    bp                  VARCHAR(50),           -- boîte postale
    nb_associes         INTEGER DEFAULT 0,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- Succursale
CREATE TABLE succursales (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    pm_mere_id          INTEGER REFERENCES personnes_morales(id),  -- maison mère en Mauritanie
    denomination        VARCHAR(300) NOT NULL,
    denomination_ar     VARCHAR(300),
    pays_origine        VARCHAR(100),
    capital_affecte     NUMERIC(15,2),
    devise              VARCHAR(5) DEFAULT 'MRU',
    siege_social        TEXT,
    ville               VARCHAR(100),
    localite_id         INTEGER REFERENCES localites(id),
    telephone           VARCHAR(20),
    email               VARCHAR(150),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- ============================================================
-- REGISTRES PRINCIPAUX
-- ============================================================

-- Registre Analytique (RA) - un enregistrement par commerçant
CREATE TABLE registre_analytique (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    numero_ra           VARCHAR(30) UNIQUE NOT NULL,    -- numéro analytique
    type_entite         VARCHAR(10) NOT NULL CHECK (type_entite IN ('PH','PM','SC')),
    ph_id               INTEGER REFERENCES personnes_physiques(id),
    pm_id               INTEGER REFERENCES personnes_morales(id),
    sc_id               INTEGER REFERENCES succursales(id),
    numero_rc           VARCHAR(30),                    -- numéro RC final
    date_immatriculation DATE,
    statut              VARCHAR(20) DEFAULT 'EN_COURS'
                        CHECK (statut IN ('EN_COURS','IMMATRICULE','RADIE','SUSPENDU','ANNULE')),
    date_radiation      DATE,
    motif_radiation     TEXT,
    localite_id         INTEGER REFERENCES localites(id),  -- greffe
    observations        TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    validated_at        TIMESTAMP,
    validated_by        INTEGER REFERENCES utilisateurs(id),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- Registre Chronologique (RC) - chronologie des actes
CREATE TABLE registre_chronologique (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    numero_chrono       VARCHAR(30) UNIQUE NOT NULL,
    ra_id               INTEGER REFERENCES registre_analytique(id),
    type_acte           VARCHAR(30) NOT NULL,           -- IMMAT, MODIF, RADIA, DEPOT, CESSION
    date_acte           DATE NOT NULL DEFAULT CURRENT_DATE,
    date_enregistrement DATE DEFAULT CURRENT_DATE,
    description         TEXT,
    description_ar      TEXT,
    statut              VARCHAR(20) DEFAULT 'EN_INSTANCE'
                        CHECK (statut IN ('EN_INSTANCE','VALIDE','REJETE','ANNULE')),
    observations        TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    validated_at        TIMESTAMP,
    validated_by        INTEGER REFERENCES utilisateurs(id),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- ============================================================
-- DEMANDES
-- ============================================================

CREATE TABLE demandes (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    numero_dmd          VARCHAR(30) UNIQUE NOT NULL,
    type_demande_id     INTEGER REFERENCES types_demandes(id),
    ra_id               INTEGER REFERENCES registre_analytique(id),
    type_entite         VARCHAR(10) CHECK (type_entite IN ('PH','PM','SC')),
    ph_id               INTEGER REFERENCES personnes_physiques(id),
    pm_id               INTEGER REFERENCES personnes_morales(id),
    sc_id               INTEGER REFERENCES succursales(id),
    date_demande        DATE DEFAULT CURRENT_DATE,
    date_limite         DATE,
    statut              VARCHAR(20) DEFAULT 'SAISIE'
                        CHECK (statut IN ('SAISIE','SOUMISE','EN_TRAITEMENT','VALIDEE','REJETEE','ANNULEE')),
    motif_rejet         TEXT,
    observations        TEXT,
    canal               VARCHAR(20) DEFAULT 'GUICHET' CHECK (canal IN ('GUICHET','EN_LIGNE')),
    montant_paye        NUMERIC(12,2) DEFAULT 0,
    reference_paiement  VARCHAR(100),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    submitted_at        TIMESTAMP,
    validated_at        TIMESTAMP,
    validated_by        INTEGER REFERENCES utilisateurs(id),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- Lignes de demande (checklist des pièces)
CREATE TABLE lignes_demande (
    id              SERIAL PRIMARY KEY,
    demande_id      INTEGER REFERENCES demandes(id) ON DELETE CASCADE,
    type_doc_id     INTEGER REFERENCES types_documents(id),
    libelle         VARCHAR(200),
    present         BOOLEAN DEFAULT FALSE,
    conforme        BOOLEAN DEFAULT FALSE,
    observations    TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- DÉPÔTS D'ACTES
-- ============================================================

CREATE TABLE depots (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    numero_depot        VARCHAR(30) UNIQUE NOT NULL,
    ra_id               INTEGER REFERENCES registre_analytique(id),
    type_depot          VARCHAR(50),               -- ACTE_CONSTITUTION, COMPTE_ANNUEL, PV_AG, etc.
    annee_exercice      INTEGER,
    date_depot          DATE DEFAULT CURRENT_DATE,
    description         TEXT,
    statut              VARCHAR(20) DEFAULT 'EN_ATTENTE'
                        CHECK (statut IN ('EN_ATTENTE','ENREGISTRE','REJETE','ANNULE')),
    observations        TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    validated_at        TIMESTAMP,
    validated_by        INTEGER REFERENCES utilisateurs(id),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- ============================================================
-- DOCUMENTS NUMERISES
-- ============================================================

CREATE TABLE documents (
    id              SERIAL PRIMARY KEY,
    uuid            UUID DEFAULT uuid_generate_v4() UNIQUE,
    nom_fichier     VARCHAR(255) NOT NULL,
    chemin_fichier  VARCHAR(500) NOT NULL,
    type_doc_id     INTEGER REFERENCES types_documents(id),
    taille_ko       INTEGER,
    mime_type       VARCHAR(100),
    ra_id           INTEGER REFERENCES registre_analytique(id),
    demande_id      INTEGER REFERENCES demandes(id),
    depot_id        INTEGER REFERENCES depots(id),
    chrono_id       INTEGER REFERENCES registre_chronologique(id),
    description     TEXT,
    date_scan       DATE DEFAULT CURRENT_DATE,
    created_at      TIMESTAMP DEFAULT NOW(),
    created_by      INTEGER REFERENCES utilisateurs(id)
);

-- ============================================================
-- ASSOCIES / ACTIONNAIRES
-- ============================================================

CREATE TABLE associes (
    id                  SERIAL PRIMARY KEY,
    ra_id               INTEGER REFERENCES registre_analytique(id) ON DELETE CASCADE,
    type_associe        VARCHAR(10) CHECK (type_associe IN ('PH','PM')) DEFAULT 'PH',
    ph_id               INTEGER REFERENCES personnes_physiques(id),
    pm_id               INTEGER REFERENCES personnes_morales(id),
    nom_associe         VARCHAR(200),          -- si non enregistré au RC
    nationalite_id      INTEGER REFERENCES nationalites(id),
    nombre_parts        INTEGER DEFAULT 0,
    valeur_parts        NUMERIC(12,2) DEFAULT 0,
    pourcentage         NUMERIC(5,2),
    type_part           VARCHAR(50),           -- ORDINAIRE, PRIVILEGIEE
    date_entree         DATE,
    date_sortie         DATE,
    actif               BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- GÉRANTS / DIRIGEANTS
-- ============================================================

CREATE TABLE gerants (
    id                  SERIAL PRIMARY KEY,
    ra_id               INTEGER REFERENCES registre_analytique(id) ON DELETE CASCADE,
    type_gerant         VARCHAR(10) CHECK (type_gerant IN ('PH','PM')) DEFAULT 'PH',
    ph_id               INTEGER REFERENCES personnes_physiques(id),
    pm_id               INTEGER REFERENCES personnes_morales(id),
    nom_gerant          VARCHAR(200),          -- si non enregistré
    nationalite_id      INTEGER REFERENCES nationalites(id),
    fonction_id         INTEGER REFERENCES fonctions(id),
    date_debut          DATE,
    date_fin            DATE,
    pouvoirs            TEXT,
    actif               BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- DOMAINES D'ACTIVITÉS (liés au RA)
-- ============================================================

CREATE TABLE ra_domaines (
    id              SERIAL PRIMARY KEY,
    ra_id           INTEGER REFERENCES registre_analytique(id) ON DELETE CASCADE,
    domaine_id      INTEGER REFERENCES domaines_activites(id),
    principal       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- MODIFICATIONS AU RC
-- ============================================================

CREATE TABLE modifications (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    numero_modif        VARCHAR(30) UNIQUE NOT NULL,
    ra_id               INTEGER REFERENCES registre_analytique(id),
    chrono_id           INTEGER REFERENCES registre_chronologique(id),
    demande_id          INTEGER REFERENCES demandes(id),
    date_modif          DATE DEFAULT CURRENT_DATE,
    statut              VARCHAR(20) DEFAULT 'EN_COURS'
                        CHECK (statut IN ('EN_COURS','VALIDEE','REJETEE','ANNULEE')),
    observations        TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    validated_at        TIMESTAMP,
    validated_by        INTEGER REFERENCES utilisateurs(id),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

CREATE TABLE lignes_modification (
    id              SERIAL PRIMARY KEY,
    modif_id        INTEGER REFERENCES modifications(id) ON DELETE CASCADE,
    champ_modif_id  INTEGER REFERENCES champs_modif(id),
    code_champ      VARCHAR(50),
    libelle_champ   VARCHAR(200),
    ancienne_valeur TEXT,
    nouvelle_valeur TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- RADIATIONS
-- ============================================================

CREATE TABLE radiations (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    numero_radia        VARCHAR(30) UNIQUE NOT NULL,
    ra_id               INTEGER REFERENCES registre_analytique(id),
    chrono_id           INTEGER REFERENCES registre_chronologique(id),
    demande_id          INTEGER REFERENCES demandes(id),
    date_radiation      DATE DEFAULT CURRENT_DATE,
    motif               VARCHAR(100),          -- CESSATION, DISSOLUTION, LIQUIDATION, etc.
    description         TEXT,
    statut              VARCHAR(20) DEFAULT 'EN_COURS'
                        CHECK (statut IN ('EN_COURS','VALIDEE','REJETEE','ANNULEE')),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    validated_at        TIMESTAMP,
    validated_by        INTEGER REFERENCES utilisateurs(id),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- ============================================================
-- CESSIONS
-- ============================================================

CREATE TABLE cessions (
    id                  SERIAL PRIMARY KEY,
    uuid                UUID DEFAULT uuid_generate_v4() UNIQUE,
    numero_cession      VARCHAR(30) UNIQUE NOT NULL,
    ra_id               INTEGER REFERENCES registre_analytique(id),
    chrono_id           INTEGER REFERENCES registre_chronologique(id),
    demande_id          INTEGER REFERENCES demandes(id),
    date_cession        DATE DEFAULT CURRENT_DATE,
    type_cession        VARCHAR(50),           -- FONDS_COMMERCE, PARTS_SOCIALES, ACTIONS
    cedant_ph_id        INTEGER REFERENCES personnes_physiques(id),
    cedant_pm_id        INTEGER REFERENCES personnes_morales(id),
    cessionnaire_ph_id  INTEGER REFERENCES personnes_physiques(id),
    cessionnaire_pm_id  INTEGER REFERENCES personnes_morales(id),
    prix_cession        NUMERIC(15,2),
    description         TEXT,
    statut              VARCHAR(20) DEFAULT 'EN_COURS'
                        CHECK (statut IN ('EN_COURS','VALIDEE','REJETEE','ANNULEE')),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    validated_at        TIMESTAMP,
    validated_by        INTEGER REFERENCES utilisateurs(id),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- ============================================================
-- BREVETS / MARQUES
-- ============================================================

CREATE TABLE brevets (
    id                  SERIAL PRIMARY KEY,
    ra_id               INTEGER REFERENCES registre_analytique(id),
    type_brevet         VARCHAR(50),           -- MARQUE, BREVET, MODELE
    numero_brevet       VARCHAR(100),
    description         VARCHAR(300),
    date_depot          DATE,
    date_expiration     DATE,
    actif               BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- BÉNÉFICIAIRES EFFECTIFS (BE)
-- ============================================================

CREATE TABLE beneficiaires_effectifs (
    id                  SERIAL PRIMARY KEY,
    ra_id               INTEGER REFERENCES registre_analytique(id) ON DELETE CASCADE,
    type_be             VARCHAR(10) CHECK (type_be IN ('PH','PM')) DEFAULT 'PH',
    ph_id               INTEGER REFERENCES personnes_physiques(id),
    pm_id               INTEGER REFERENCES personnes_morales(id),
    nom_be              VARCHAR(200),
    nationalite_id      INTEGER REFERENCES nationalites(id),
    pourcentage_detention NUMERIC(5,2),
    mode_controle       VARCHAR(100),
    date_debut          DATE,
    actif               BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- DÉCLARATIONS
-- ============================================================

CREATE TABLE declarations (
    id                  SERIAL PRIMARY KEY,
    ra_id               INTEGER REFERENCES registre_analytique(id),
    type_declaration    VARCHAR(50),
    date_declaration    DATE DEFAULT CURRENT_DATE,
    description         TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    created_by          INTEGER REFERENCES utilisateurs(id)
);

-- ============================================================
-- AUDIT / HISTORIQUE
-- ============================================================

CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    table_name  VARCHAR(100),
    record_id   INTEGER,
    action      VARCHAR(20) CHECK (action IN ('INSERT','UPDATE','DELETE','SELECT')),
    old_data    JSONB,
    new_data    JSONB,
    user_id     INTEGER REFERENCES utilisateurs(id),
    ip_address  INET,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SÉQUENCES POUR NUMÉROTATION AUTOMATIQUE
-- ============================================================

CREATE TABLE sequences_numerotation (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(50) UNIQUE NOT NULL,  -- RA, CHRONO, DMD, DEPOT, MODIF, RADIA, CESSION
    prefixe     VARCHAR(20),
    annee       INTEGER DEFAULT EXTRACT(YEAR FROM NOW()),
    dernier_num INTEGER DEFAULT 0,
    nb_chiffres INTEGER DEFAULT 6,
    localite_id INTEGER REFERENCES localites(id),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEX POUR PERFORMANCE
-- ============================================================

CREATE INDEX idx_ra_type ON registre_analytique(type_entite);
CREATE INDEX idx_ra_statut ON registre_analytique(statut);
CREATE INDEX idx_ra_numero ON registre_analytique(numero_ra);
CREATE INDEX idx_ra_numero_rc ON registre_analytique(numero_rc);
CREATE INDEX idx_ph_nni ON personnes_physiques(nni);
CREATE INDEX idx_ph_nom ON personnes_physiques USING gin(to_tsvector('simple', nom || ' ' || COALESCE(prenom,'')));
CREATE INDEX idx_pm_denomination ON personnes_morales USING gin(to_tsvector('simple', denomination));
CREATE INDEX idx_chrono_numero ON registre_chronologique(numero_chrono);
CREATE INDEX idx_demande_numero ON demandes(numero_dmd);
CREATE INDEX idx_demande_statut ON demandes(statut);
CREATE INDEX idx_depot_numero ON depots(numero_depot);
CREATE INDEX idx_audit_table ON audit_log(table_name, record_id);

-- ============================================================
-- FONCTION POUR GÉNÉRER LES NUMÉROS AUTOMATIQUEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION generer_numero(p_code VARCHAR, p_localite_id INTEGER DEFAULT NULL)
RETURNS VARCHAR AS $$
DECLARE
    v_seq        sequences_numerotation%ROWTYPE;
    v_annee      INTEGER;
    v_num        INTEGER;
    v_resultat   VARCHAR;
BEGIN
    v_annee := EXTRACT(YEAR FROM NOW());

    SELECT * INTO v_seq
    FROM sequences_numerotation
    WHERE code = p_code
    AND (localite_id = p_localite_id OR (localite_id IS NULL AND p_localite_id IS NULL))
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Séquence % non trouvée', p_code;
    END IF;

    IF v_seq.annee != v_annee THEN
        UPDATE sequences_numerotation
        SET annee = v_annee, dernier_num = 1, updated_at = NOW()
        WHERE code = p_code;
        v_num := 1;
    ELSE
        v_num := v_seq.dernier_num + 1;
        UPDATE sequences_numerotation
        SET dernier_num = v_num, updated_at = NOW()
        WHERE code = p_code;
    END IF;

    v_resultat := COALESCE(v_seq.prefixe, '') ||
                  v_annee::TEXT ||
                  LPAD(v_num::TEXT, v_seq.nb_chiffres, '0');
    RETURN v_resultat;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- VUE REGISTRE ANALYTIQUE COMPLET
-- ============================================================

CREATE VIEW v_registre_analytique AS
SELECT
    ra.id,
    ra.uuid,
    ra.numero_ra,
    ra.numero_rc,
    ra.type_entite,
    ra.statut,
    ra.date_immatriculation,
    ra.date_radiation,
    CASE ra.type_entite
        WHEN 'PH' THEN ph.nom || ' ' || COALESCE(ph.prenom, '')
        WHEN 'PM' THEN pm.denomination
        WHEN 'SC' THEN sc.denomination
    END AS denomination,
    CASE ra.type_entite
        WHEN 'PH' THEN ph.nni
        ELSE NULL
    END AS nni,
    CASE ra.type_entite
        WHEN 'PM' THEN fj.libelle_fr
        ELSE NULL
    END AS forme_juridique,
    CASE ra.type_entite
        WHEN 'PM' THEN pm.capital_social::TEXT
        WHEN 'SC' THEN sc.capital_affecte::TEXT
        ELSE NULL
    END AS capital,
    CASE ra.type_entite
        WHEN 'PH' THEN ph.telephone
        WHEN 'PM' THEN pm.telephone
        WHEN 'SC' THEN sc.telephone
    END AS telephone,
    CASE ra.type_entite
        WHEN 'PH' THEN ph.email
        WHEN 'PM' THEN pm.email
        WHEN 'SC' THEN sc.email
    END AS email,
    l.libelle_fr AS localite,
    ra.created_at,
    ra.updated_at
FROM registre_analytique ra
LEFT JOIN personnes_physiques ph ON ra.ph_id = ph.id AND ra.type_entite = 'PH'
LEFT JOIN personnes_morales pm ON ra.pm_id = pm.id AND ra.type_entite = 'PM'
LEFT JOIN succursales sc ON ra.sc_id = sc.id AND ra.type_entite = 'SC'
LEFT JOIN formes_juridiques fj ON pm.forme_juridique_id = fj.id
LEFT JOIN localites l ON ra.localite_id = l.id;

-- ============================================================
-- VUE DEMANDES COMPLÈTES
-- ============================================================

CREATE VIEW v_demandes AS
SELECT
    d.id,
    d.uuid,
    d.numero_dmd,
    td.libelle_fr AS type_demande,
    d.type_entite,
    d.statut,
    d.date_demande,
    d.date_limite,
    d.canal,
    d.montant_paye,
    ra.numero_ra,
    ra.numero_rc,
    CASE d.type_entite
        WHEN 'PH' THEN ph.nom || ' ' || COALESCE(ph.prenom, '')
        WHEN 'PM' THEN pm.denomination
        WHEN 'SC' THEN sc.denomination
    END AS denomination,
    u.nom || ' ' || COALESCE(u.prenom, '') AS agent,
    d.created_at,
    d.updated_at
FROM demandes d
LEFT JOIN types_demandes td ON d.type_demande_id = td.id
LEFT JOIN registre_analytique ra ON d.ra_id = ra.id
LEFT JOIN personnes_physiques ph ON d.ph_id = ph.id
LEFT JOIN personnes_morales pm ON d.pm_id = pm.id
LEFT JOIN succursales sc ON d.sc_id = sc.id
LEFT JOIN utilisateurs u ON d.created_by = u.id;
