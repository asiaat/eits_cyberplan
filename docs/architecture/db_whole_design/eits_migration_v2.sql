-- ============================================================
-- E-ITS CyberPlan Database Migration v2
-- Täiendused vastavalt E-ITS rakendusjuhendile 2025,
-- KOV profiilile v1.2, Haridus- ja Kaugkütte profiilidele,
-- ISMS nõuetele (v2025) ja Auditeerimisjuhendile
-- ============================================================
-- NB: Olemasolevaid tabeleid ei kustutata.
-- Lisatakse uued tabelid ja täiendatakse olemasolevaid.
-- ============================================================

-- ============================================
-- TIER A: KESKNE E-ITS ETALONTURBE KATALOOG
-- (ühine kõigile tenantidele)
-- ============================================

-- 1. Kataloogi versioonihaldus
-- RIA annab igal aastal välja uue E-ITS versiooni.
-- Üks versioon on korraga aktiivne.
CREATE TABLE IF NOT EXISTS catalog_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year VARCHAR(4) NOT NULL UNIQUE,          -- nt '2024', '2025'
    name VARCHAR(100),                        -- nt 'E-ITS 2025'
    is_active BOOLEAN DEFAULT false,
    released_at DATE,
    created_at TIMESTAMP DEFAULT now()
);

-- 2. E-ITS Moodulid (etalonturbe kataloogi moodulid)
-- Protsessimoodulid: ISMS, ORP, CON, OPS, DER (rakendatakse ALATI)
-- Süsteemimoodulid: INF, NET, SYS, APP, IND (rakendatakse kui sihtobjekt on kaitsealas)
CREATE TABLE IF NOT EXISTS eits_modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID NOT NULL REFERENCES catalog_versions(id) ON DELETE CASCADE,
    code VARCHAR(30) NOT NULL,                -- nt 'SYS.1.1', 'ORP.1', 'ISMS.1'
    name VARCHAR(255) NOT NULL,               -- nt 'Server üldiselt', 'Infoturbe korraldus'
    module_group VARCHAR(10) NOT NULL,        -- 'ISMS','ORP','CON','OPS','DER','INF','NET','SYS','APP','IND'
    module_type VARCHAR(20) NOT NULL          -- 'PROCESS' (protsessimoodul) | 'SYSTEM' (süsteemimoodul)
        CHECK (module_type IN ('PROCESS', 'SYSTEM')),
    description TEXT,
    UNIQUE (version_id, code)
);

COMMENT ON COLUMN eits_modules.module_type IS
  'PROCESS = protsessimoodul (ISMS,ORP,CON,OPS,DER) – rakendatakse alati; '
  'SYSTEM = süsteemimoodul (INF,NET,SYS,APP,IND) – rakendatakse kui sihtobjekt on kaitsealas';

-- 3. Turvameetmed (E-ITS meetmete kataloog)
-- Iga meede kuulub moodulisse ja on liigitatud tasemega: põhi/standard/kõrg
CREATE TABLE IF NOT EXISTS eits_catalog_measures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_id UUID NOT NULL REFERENCES eits_modules(id) ON DELETE CASCADE,
    code VARCHAR(30) NOT NULL,                -- nt 'SYS.1.1.M22', 'ORP.1.M8'
    name TEXT NOT NULL,                       -- meetme nimetus
    measure_level VARCHAR(10) NOT NULL        -- E-ITS protection mode level
        CHECK (measure_level IN ('BASE', 'STANDARD', 'HIGH')),
    description TEXT,
    responsible_role VARCHAR(100),            -- nt 'Infoturbejuht', 'IT-juht'
    UNIQUE (module_id, code)
);

COMMENT ON COLUMN eits_catalog_measures.measure_level IS
  'BASE = põhimeede (rakendatakse põhiturbe ja standardturbe korral); '
  'STANDARD = standardmeede (rakendatakse standardturbe korral); '
  'HIGH = kõrgmeede (rakendatakse kõrgendatud kaitsetarbe korral)';

-- 4. Alusohud (E-ITS ohtude kataloog)
-- RIA annab igal aastal välja uuendatud ohtude kataloogi
CREATE TABLE IF NOT EXISTS eits_threats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID NOT NULL REFERENCES catalog_versions(id) ON DELETE CASCADE,
    code VARCHAR(30) NOT NULL,                -- nt 'O.SYS.01'
    category VARCHAR(100),                    -- nt '2 - Tegevuslik', '1 - Loomulik'
    impact_area VARCHAR(100),                 -- mõjuala
    name VARCHAR(255) NOT NULL,
    description TEXT,
    UNIQUE (version_id, code)
);

-- 5. Ohtude seos moodulitega
-- Iga mooduli juures on kirjeldatud moodulipõhised ohud
CREATE TABLE IF NOT EXISTS module_threats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_id UUID NOT NULL REFERENCES eits_modules(id) ON DELETE CASCADE,
    threat_id UUID NOT NULL REFERENCES eits_threats(id) ON DELETE CASCADE,
    relevance_note TEXT,
    UNIQUE (module_id, threat_id)
);

-- 6. Kahjustsenaariumid (KS1–KS6, fikseeritud)
-- E-ITS rakendusjuhend Lisa B
CREATE TABLE IF NOT EXISTS damage_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(10) NOT NULL UNIQUE,         -- 'KS1'..'KS6'
    name VARCHAR(255) NOT NULL,
    description TEXT
);

-- Eeltäidetavad kahjustsenaariumid (E-ITS rakendusjuhend + KOV profiil)
INSERT INTO damage_scenarios (code, name, description) VALUES
('KS1', 'Õigusaktide, eeskirjade või lepingute rikkumine',
 'Seaduste, määruste, lepingute, andmekaitse-eeskirjade rikkumisest tulenev kahju'),
('KS2', 'Teabelise enesemääramisõiguse rikkumine',
 'Isikuandmete töötlemise rikkumisest ja privaatsuse kaost tulenev kahju'),
('KS3', 'Füüsiline kahju',
 'Inimeste elule, tervisele ja keskkonnale tekitatav kahju'),
('KS4', 'Ülesannete täitmise võime kahjustamine',
 'Organisatsiooni protsesside ja ülesannete täitmise häirumisest tulenev kahju'),
('KS5', 'Negatiivsed sisemised või välised toimed',
 'Maine kahjustamine, usaldusväärsuse langus sihtrühmade, töötajate ja partnerite silmis'),
('KS6', 'Rahalised tagajärjed',
 'Otsesed ja kaudsed rahalised kahjud, kahjunõuded, trahvid')
ON CONFLICT (code) DO NOTHING;


-- ============================================
-- TIER B: TENANDIPÕHISED TÄIENDUSED
-- ============================================

-- -----------------------------------------------
-- 7. Protection mode selection (organizational level)
-- E-ITS ISMS nõuded p 6.2.3(c)
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS security_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    catalog_version_id UUID REFERENCES catalog_versions(id),
    security_approach VARCHAR(20) NOT NULL    -- protection mode
        CHECK (security_approach IN ('BASIC', 'STANDARD', 'CORE')),
    approved_by UUID REFERENCES local_users(id),
    approved_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE (tenant_id, catalog_version_id)
);

COMMENT ON COLUMN security_profiles.security_approach IS
  'BASIC = põhiturve (ainult põhimeetmed); '
  'STANDARD = standardturve (põhi + standardmeetmed); '
  'CORE = tuumikuturve (organisatsiooni ise defineeritud meetmete komplekt)';


-- -----------------------------------------------
-- 8. Valdkonnad / äriprotsessid – TÄIENDUSED
-- E-ITS kasutab mõistet "valdkond" = äriprotsess
-- Lisa puuduvad väljad olemasolevale tabelile
-- -----------------------------------------------
ALTER TABLE business_processes
    ADD COLUMN IF NOT EXISTS process_type VARCHAR(20) DEFAULT 'OPERATIVE'
        CHECK (process_type IN ('OPERATIVE', 'SUPPORTING')),
    ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 2
        CHECK (priority BETWEEN 1 AND 3);

COMMENT ON COLUMN business_processes.process_type IS
  'OPERATIVE = operatiivvaldkond (aitab kaasa organisatsiooni eesmärkide saavutamisele); '
  'SUPPORTING = toetav valdkond (IT-haldus, kantselei, finants jne)';

COMMENT ON COLUMN business_processes.priority IS
  'E-ITS kaitseala modelleerimise prioriteet: 1=P1 (esmajärjekorras), 2=P2 (järgmisena), 3=P3 (viimaks)';


-- -----------------------------------------------
-- 9. Kaitsetarbe määramine (kahjuanalüüs)
-- E-ITS rakendusjuhend Samm 4 – igale valdkonnale
-- iga kahjustsenaariumi (KS) kohta C/I/A hinnang
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS damage_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    business_process_id UUID NOT NULL REFERENCES business_processes(id) ON DELETE CASCADE,
    damage_scenario_id UUID NOT NULL REFERENCES damage_scenarios(id),

    -- Kahjukategooria hinnang igale CIA dimensioonile
    -- Väärtused: 0=Tühine, 1=Piiratud, 2=Tõsine, 3=Katastroofiline
    availability_impact INTEGER DEFAULT 0
        CHECK (availability_impact BETWEEN 0 AND 3),
    confidentiality_impact INTEGER DEFAULT 0
        CHECK (confidentiality_impact BETWEEN 0 AND 3),
    integrity_impact INTEGER DEFAULT 0
        CHECK (integrity_impact BETWEEN 0 AND 3),

    -- Tuletatud kahjukategooria = MAX(C, I, A)
    damage_category INTEGER GENERATED ALWAYS AS (
        GREATEST(availability_impact, confidentiality_impact, integrity_impact)
    ) STORED,

    justification TEXT,                       -- põhjendus (audiitorkontroll!)
    assessed_by UUID REFERENCES local_users(id),
    assessed_at TIMESTAMP DEFAULT now(),

    UNIQUE (tenant_id, business_process_id, damage_scenario_id)
);

COMMENT ON TABLE damage_assessments IS
  'Kahjuanalüüsi tabel – iga valdkonna (äriprotsessi) ja kahjustsenaariumi (KS1-KS6) kohta '
  'hinnatakse mõju käideldavusele, konfidentsiaalsusele ja terviklusele. '
  'Kahjukategooria tuleneb kõrgeimast hinnangust. Vt E-ITS rakendusjuhend Lisa B.';


-- -----------------------------------------------
-- 10. Valdkonna kaitsetarbe koondtabel
-- Tuletub damage_assessments hinnangutest
-- Kõrgeim kahjukategooria üle kõigi stsenaariumite
-- määrab kaitsetarbe taseme
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS protection_need_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    business_process_id UUID NOT NULL REFERENCES business_processes(id) ON DELETE CASCADE,

    -- Koond-kaitsetarve: NORMAL / HIGH / VERY_HIGH
    protection_need VARCHAR(20) NOT NULL DEFAULT 'NORMAL'
        CHECK (protection_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')),

    -- Per-dimensiooni kaitsetarve (vajadusel detailsemaks)
    confidentiality_need VARCHAR(20) DEFAULT 'NORMAL'
        CHECK (confidentiality_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')),
    integrity_need VARCHAR(20) DEFAULT 'NORMAL'
        CHECK (integrity_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')),
    availability_need VARCHAR(20) DEFAULT 'NORMAL'
        CHECK (availability_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')),

    justification TEXT,                       -- koondpõhjendus
    approved_by UUID REFERENCES local_users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),

    UNIQUE (tenant_id, business_process_id)
);

COMMENT ON TABLE protection_need_summaries IS
  'Valdkonna koond-kaitsetarve, mis tuleneb kahjuanalüüsi (damage_assessments) tulemustest. '
  'Kategooria: NORMAL ≤ kahjukategooria 1; HIGH = kahjukategooria 2; VERY_HIGH = kahjukategooria 3. '
  'See kaitsetarve "pärandatakse" edasi sihtobjektidele.';


-- -----------------------------------------------
-- 11. SIHTOBJEKTID (Assets) – ÜMBER DISAINITUD
-- Varad = sihtobjektid E-ITS mõistes
-- -----------------------------------------------

-- Sihtobjektide tüüpide klassifikaator (T, V, I, R, A)
CREATE TABLE IF NOT EXISTS asset_type_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(5) NOT NULL UNIQUE,          -- 'T','V','I','R','A'
    name VARCHAR(100) NOT NULL,
    description TEXT
);

INSERT INTO asset_type_categories (code, name, description) VALUES
('T', 'Taristu',                'Hooned, ruumid, tehnosüsteemid'),
('V', 'Võrgukomponendid',      'LAN, WAN, WLAN, VPN, tulemüür, ruuterid'),
('I', 'IT-süsteemid',          'Serverid, klientarvutid, sülearvutid, mobiilseadmed, printerid'),
('R', 'Rakendused',            'Tarkvararakendused, andmebaasid, veebiteenused, e-post'),
('A', 'Tööstusautomaatika',    'PLC, SCADA, ICS kontrollerid')
ON CONFLICT (code) DO NOTHING;

-- Täiendame olemasolevat assets tabelit E-ITS spetsiifiliste väljadega
ALTER TABLE assets
    ADD COLUMN IF NOT EXISTS asset_index VARCHAR(10),        -- unikaalne indeks, nt 'T001', 'V003', 'I005'
    ADD COLUMN IF NOT EXISTS asset_category VARCHAR(5)       -- viide: 'T','V','I','R','A'
        REFERENCES asset_type_categories(code),
    ADD COLUMN IF NOT EXISTS location VARCHAR(255),          -- asukoht
    ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1,     -- kogus (nt '25 sülearvutit')
    ADD COLUMN IF NOT EXISTS group_name VARCHAR(255),        -- rühmitamise nimi (nt 'Kõik Windowsi sülearvutid')
    ADD COLUMN IF NOT EXISTS is_grouped BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS protection_need VARCHAR(20) DEFAULT 'NORMAL'
        CHECK (protection_need IN ('NORMAL', 'HIGH', 'VERY_HIGH')),
    ADD COLUMN IF NOT EXISTS protection_need_justification TEXT,  -- pärandamise põhjendus
    ADD COLUMN IF NOT EXISTS protection_source_process_ids UUID[];  -- millistest valdkondadest pärandatud

COMMENT ON COLUMN assets.asset_index IS
  'E-ITS sihtobjekti unikaalne indeks (nt T001, V003). Vt kaitseala profiilid.';

COMMENT ON COLUMN assets.protection_need IS
  'Sihtobjektile "pärandatud" kaitsetarve. Mitut valdkonda teenindavale sihtobjektile '
  'määratakse kõrgeima kaitsetarbega valdkonna tase (maksimumprintsiip).';

COMMENT ON COLUMN assets.is_grouped IS
  'Sarnased sihtobjektid rühmitatakse (nt kõik kasutajate arvutid). '
  'Rühmitamine lihtsustab meetmete rakendamist.';


-- -----------------------------------------------
-- 12. Sihtobjektide modelleerimine
-- E-ITS Samm 7: vastendamine moodulitega
-- Üks sihtobjekt → 1..N moodulit
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS asset_module_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES eits_modules(id),
    justification TEXT,                       -- miks see moodul rakendub
    modeled_by UUID REFERENCES local_users(id),
    modeled_at TIMESTAMP DEFAULT now(),
    UNIQUE (tenant_id, asset_id, module_id)
);

COMMENT ON TABLE asset_module_mappings IS
  'E-ITS modelleerimine: iga sihtobjekt vastentatakse etalonturbe kataloogi '
  'ühe või mitme mooduliga. Nt macOS sülearvutile → SYS.2.1 + SYS.2.4 + SYS.3.1 + APP.1.2';


-- -----------------------------------------------
-- 13. INFOTURBE MEETMETE RAKENDUSPLAAN (IMR)
-- Täielikult E-ITS-konformne PEARO mudeliga
-- -----------------------------------------------

-- Kustutame vana implementation_plan_items tabeli polümorfsuse
-- ja loome uue, mis on seotud konkreetselt asset→module→measure ahelaga.
-- NB: Vana tabelit ei kustutata, loome uue kõrvale.

CREATE TABLE IF NOT EXISTS imr_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,

    -- Seos: millise sihtobjekti millise mooduli milline meede
    asset_module_mapping_id UUID REFERENCES asset_module_mappings(id) ON DELETE CASCADE,
    measure_id UUID NOT NULL REFERENCES eits_catalog_measures(id),

    -- Alternatiivne seos: protsessimooduli meede (ei seostu konkreetse varaga)
    -- Protsessimoodulid (ISMS, ORP, CON, OPS, DER) rakendatakse organisatsiooni tasemel
    is_process_module_measure BOOLEAN DEFAULT false,

    -- PEARO staatus (E-ITS rakendusjuhend)
    pearo_status VARCHAR(1) NOT NULL DEFAULT 'E'
        CHECK (pearo_status IN ('P', 'E', 'A', 'R', 'O')),

    -- Rakendamise kirjeldus (auditi nõue 5.6.4)
    implementation_description TEXT,

    -- Mitterakendamise põhjendus (auditi nõue 5.6.5)
    non_implementation_justification TEXT,

    -- Osalise rakendamise täpsustus (auditi nõue 5.6.6)
    partial_scope_description TEXT,

    -- Vastutaja (auditi nõue 5.6.7)
    responsible_user_id UUID REFERENCES local_users(id),

    -- Tähtaeg (auditi nõue 5.6.8)
    due_date DATE,
    next_review_date DATE,

    -- Prioriteet ja teostusjärjekord
    priority VARCHAR(5) DEFAULT 'P2'
        CHECK (priority IN ('P1', 'P2', 'P3')),

    -- Juhtkonna kinnitus aktsepteeritud riskile (PEARO 'A')
    risk_acceptance_approved_by UUID REFERENCES local_users(id),
    risk_acceptance_date TIMESTAMP,

    -- Tõendusmaterjal / verification
    verification_method TEXT,
    last_verified_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

COMMENT ON COLUMN imr_items.pearo_status IS
  'P = Pole asjakohane (meetme teostamine pole vajalik); '
  'E = Ei ole (veel) rakendatud (vajab rakendamist); '
  'A = Aktsepteeritud risk (juhtkonna kinnitus); '
  'R = Rakendatud (täielikult, tõhusalt ja otstarbekalt); '
  'O = Osaliselt rakendatud';

COMMENT ON COLUMN imr_items.priority IS
  'P1 = esmajärjekorras (tõhusa turbeprotsessi alus); '
  'P2 = järgmisena (jätkusuutlik turve); '
  'P3 = viimaks (soovitud turbetaseme saavutamine)';

CREATE INDEX IF NOT EXISTS idx_imr_items_tenant ON imr_items(tenant_id);
CREATE INDEX IF NOT EXISTS idx_imr_items_pearo ON imr_items(tenant_id, pearo_status);
CREATE INDEX IF NOT EXISTS idx_imr_items_due ON imr_items(tenant_id, due_date);


-- -----------------------------------------------
-- 14. RISKID – täiendused vastavalt E-ITS riskimaatriksile
-- E-ITS rakendusjuhend Samm 8
-- -----------------------------------------------

-- Riskimaatriks: 4x4 (mõju × võimalikkus)
-- Mõju: Tühine, Piiratud, Tõsine, Katastroofiline (0-3)
-- Võimalikkus: Harv, Keskmine, Sage, Väga sage (0-3)

ALTER TABLE risks
    ADD COLUMN IF NOT EXISTS threat_id UUID REFERENCES eits_threats(id),
    ADD COLUMN IF NOT EXISTS asset_id UUID REFERENCES assets(id),
    ADD COLUMN IF NOT EXISTS business_process_id UUID REFERENCES business_processes(id),
    ADD COLUMN IF NOT EXISTS likelihood_score INTEGER
        CHECK (likelihood_score BETWEEN 0 AND 3),
    ADD COLUMN IF NOT EXISTS impact_score INTEGER
        CHECK (impact_score BETWEEN 0 AND 3),
    ADD COLUMN IF NOT EXISTS risk_score INTEGER
        GENERATED ALWAYS AS (likelihood_score * impact_score) STORED,
    ADD COLUMN IF NOT EXISTS risk_rating VARCHAR(20),        -- Madal, Keskmine, Kõrge, Väga kõrge
    ADD COLUMN IF NOT EXISTS treatment_type VARCHAR(30)
        CHECK (treatment_type IN ('MITIGATE', 'ACCEPT', 'TRANSFER', 'AVOID')),
    ADD COLUMN IF NOT EXISTS residual_risk_level VARCHAR(20),
    ADD COLUMN IF NOT EXISTS accepted_by UUID REFERENCES local_users(id),
    ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP;

COMMENT ON COLUMN risks.likelihood_score IS
  '0=Harv, 1=Keskmine, 2=Sage, 3=Väga sage';
COMMENT ON COLUMN risks.impact_score IS
  '0=Tühine, 1=Piiratud, 2=Tõsine, 3=Katastroofiline (ähvardab organisatsiooni olemasolu)';


-- -----------------------------------------------
-- 15. Riski → meetme seos
-- Riskianalüüsi tulemusena lisatud lisameetmed
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS risk_measure_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    risk_id UUID NOT NULL REFERENCES risks(id) ON DELETE CASCADE,
    imr_item_id UUID REFERENCES imr_items(id) ON DELETE SET NULL,
    measure_id UUID REFERENCES eits_catalog_measures(id),  -- null = organisatsiooni enda lisameetme
    custom_measure_name VARCHAR(255),         -- kui ei ole E-ITS kataloogist
    custom_measure_description TEXT,
    created_at TIMESTAMP DEFAULT now()
);


-- -----------------------------------------------
-- 16. Kaitsetarbe piirid (organisatsioonispetsiifilised)
-- KOV profiili Tabel 9 – igal organisatsioonil oma piirid
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS damage_category_thresholds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    damage_scenario_id UUID NOT NULL REFERENCES damage_scenarios(id),

    -- Kahjukategooria piiri kirjeldus igale raskusastmele
    negligible_description TEXT,              -- 0 = Tühine
    limited_description TEXT,                 -- 1 = Piiratud
    serious_description TEXT,                 -- 2 = Tõsine
    catastrophic_description TEXT,            -- 3 = Katastroofiline

    approved_by UUID REFERENCES local_users(id),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),

    UNIQUE (tenant_id, damage_scenario_id)
);

COMMENT ON TABLE damage_category_thresholds IS
  'Organisatsioonipõhised kahjukategooriate piirid iga kahjustsenaariumi (KS1-KS6) jaoks. '
  'Tippjuhtkond peab veenduma, et need vastavad konkreetse organisatsiooni vajadustele.';


-- -----------------------------------------------
-- 17. Tõendid (evidences) – lisa seos IMR-iga
-- Auditeerimisjuhend p 12.4.9
-- -----------------------------------------------
ALTER TABLE evidence_links
    ADD COLUMN IF NOT EXISTS link_type VARCHAR(50) DEFAULT 'general';
    -- Võimaldab: 'imr_item', 'risk', 'asset', 'process', 'general'


-- -----------------------------------------------
-- 18. Protsessimoodulite rakendamine (organisatsiooni tasemel)
-- ISMS, ORP, CON, OPS, DER – ei seostu konkreetse sihtobjektiga
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS process_module_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES app_tenants(id) ON DELETE CASCADE,
    module_id UUID NOT NULL REFERENCES eits_modules(id),
    is_applicable BOOLEAN DEFAULT true,
    non_applicability_justification TEXT,      -- miks moodul ei kohaldu
    assigned_by UUID REFERENCES local_users(id),
    assigned_at TIMESTAMP DEFAULT now(),
    UNIQUE (tenant_id, module_id)
);

COMMENT ON TABLE process_module_assignments IS
  'Protsessimoodulite (ISMS, ORP, CON, OPS, DER) rakendamine organisatsiooni tasemel. '
  'Kõik protsessimoodulid kaasatakse; mooduli käsitlemata jätmine peab olema põhjendatud. '
  'Vt ISMS nõuded 7.2.3';


-- ============================================
-- INDEKSID täienduste jaoks
-- ============================================
CREATE INDEX IF NOT EXISTS idx_eits_modules_version ON eits_modules(version_id);
CREATE INDEX IF NOT EXISTS idx_eits_modules_group ON eits_modules(module_group);
CREATE INDEX IF NOT EXISTS idx_catalog_measures_module ON eits_catalog_measures(module_id);
CREATE INDEX IF NOT EXISTS idx_catalog_measures_level ON eits_catalog_measures(measure_level);
CREATE INDEX IF NOT EXISTS idx_eits_threats_version ON eits_threats(version_id);
CREATE INDEX IF NOT EXISTS idx_damage_assessments_tenant ON damage_assessments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_damage_assessments_process ON damage_assessments(business_process_id);
CREATE INDEX IF NOT EXISTS idx_protection_needs_tenant ON protection_need_summaries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_asset_module_mappings_tenant ON asset_module_mappings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_asset_module_mappings_asset ON asset_module_mappings(asset_id);
CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(asset_category);
CREATE INDEX IF NOT EXISTS idx_assets_protection ON assets(tenant_id, protection_need);
CREATE INDEX IF NOT EXISTS idx_risk_measure_links_risk ON risk_measure_links(risk_id);
CREATE INDEX IF NOT EXISTS idx_process_module_assignments_tenant ON process_module_assignments(tenant_id);


-- ============================================
-- VAATED (Views) aruandluse jaoks
-- ============================================

-- IMR koondstatistika tenandi lõikes (juhtkonna aruandlus, ISMS nõuded p 8.6)
CREATE OR REPLACE VIEW v_imr_summary AS
SELECT
    i.tenant_id,
    i.pearo_status,
    cm.measure_level,
    COUNT(*) AS measure_count,
    COUNT(*) FILTER (WHERE i.due_date < CURRENT_DATE AND i.pearo_status IN ('E','O')) AS overdue_count
FROM imr_items i
JOIN eits_catalog_measures cm ON cm.id = i.measure_id
GROUP BY i.tenant_id, i.pearo_status, cm.measure_level;

-- Sihtobjektide kaitsetarbe ülevaade
CREATE OR REPLACE VIEW v_asset_protection_overview AS
SELECT
    a.tenant_id,
    a.id AS asset_id,
    a.asset_index,
    a.name AS asset_name,
    a.asset_category,
    a.protection_need,
    COUNT(DISTINCT amm.module_id) AS mapped_module_count,
    COUNT(DISTINCT i.id) AS imr_item_count,
    COUNT(DISTINCT i.id) FILTER (WHERE i.pearo_status = 'R') AS implemented_count,
    COUNT(DISTINCT i.id) FILTER (WHERE i.pearo_status = 'E') AS not_implemented_count
FROM assets a
LEFT JOIN asset_module_mappings amm ON amm.asset_id = a.id
LEFT JOIN imr_items i ON i.asset_module_mapping_id = amm.id
GROUP BY a.tenant_id, a.id, a.asset_index, a.name, a.asset_category, a.protection_need;

-- Riskimaatriks – riskide jaotus mõju × võimalikkuse lõikes
CREATE OR REPLACE VIEW v_risk_matrix AS
SELECT
    r.tenant_id,
    r.impact_score,
    r.likelihood_score,
    COUNT(*) AS risk_count,
    ARRAY_AGG(r.title) AS risk_titles
FROM risks r
WHERE r.impact_score IS NOT NULL AND r.likelihood_score IS NOT NULL
GROUP BY r.tenant_id, r.impact_score, r.likelihood_score;
