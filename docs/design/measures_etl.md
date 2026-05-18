# System Context and Objective
You are an expert Data Engineer and Python developer. Your task is to build an ETL (Extract, Transform, Load) pipeline script to import the Estonian Information Security Standard (E-ITS) catalog data into a specific custom PostgreSQL database schema. 

Instead of an API, the single source of truth for the data is an official Excel file published by the Estonian Information System Authority (RIA).

## 1. Source Data & Extraction
* **Source URL:** `https://eits.ria.ee/api/2/article/asset/2024/E-ITS%202024_meetmete_tabel_CC.xlsx`
* **File Format:** `.xlsx` (Excel)
* **Action:** The Python ETL script must programmatically download this file (e.g., using the `requests` library), save it to a temporary directory (`tempfile` module), load it into memory using `pandas` and `openpyxl`, and then clean up the temporary file.

## 2. Target Database Schema Mapping
The target database is PostgreSQL. The ETL script must populate the following tables using standard `uuid` (UUIDv4) generation for primary keys.

### 2.1. eits_catalog_versions
* **Purpose:** Represents a specific year's standard (e.g., "E-ITS 2024").
* **Fields to populate:** `id` (UUID), `version` (string, e.g., '2024'), `source_name` (string, e.g., 'RIA Excel 2024'), `year` (string, '2024'), `name` (string, 'E-ITS 2024 Catalog'), `active` (boolean, default false), `is_active` (boolean, default false), `imported_at` (timestamp).

### 2.2. eits_modules
* **Purpose:** Represents standard modules (e.g., "ISMS.1", "APP.1.1").
* **Extraction:** Extract unique module codes and names from the Excel file rows.
* **Fields to populate:** `id` (UUID), `catalog_version_id` (UUID, FK to eits_catalog_versions), `code` (string), `name` (string), `category` (string), `description` (text), `module_group` (string).

### 2.3. eits_measures & eits_catalog_measures
* **Purpose:** Represents individual security measures (e.g., "ISMS.1.M1").
* **Mapping Measure Levels:** The Excel file contains Estonian terminology for measure levels. These MUST be mapped strictly to the database check constraint `ck_measure_level`:
  * "Põhimeede" (or similar base level indication) -> `BASE`
  * "Standardturve" or "Tuumikuturve" -> `STANDARD`
  * "Kõrgturve" -> `HIGH`
* **eits_measures Fields:** `id` (UUID), `catalog_version_id` (UUID), `code` (string), `title` (string), `description` (text), `measure_level` (string mapped to ENUM), `responsible_role` (string).
* **eits_catalog_measures Fields:** `id` (UUID), `module_id` (UUID, FK to eits_modules), `code` (string), `name` (string), `measure_level` (string), `description` (text), `responsible_role` (string).
* **Action:** Populate both tables. `eits_measures` acts as a global dictionary for the version, while `eits_catalog_measures` defines the specific instantiations under modules.

### 2.4. eits_module_measures (Many-to-Many Relationship)
* **Action:** Link the extracted modules and measures.
* **Fields to populate:** `id` (UUID), `module_id` (UUID, FK to eits_modules), `measure_id` (UUID, FK to eits_measures).

## 3. Transformation & Load Execution Steps

1. **Setup & Extract:** Download the `.xlsx` file, load into a pandas DataFrame.
2. **Transform:**
    * Iterate through the rows/DataFrames.
    * Identify distinct Modules and distinct Measures.
    * Map Estonian measure types to `BASE`, `STANDARD`, `HIGH` to comply with schema constraints.
    * Generate deterministic or random UUIDv4 identifiers. Ensure logic exists to handle idempotency (if the script runs twice for '2024', it should update or safely skip existing records, not duplicate them).
3. **Load (Database Transaction):**
    * Open a database session.
    * Begin Transaction.
    * Insert the `eits_catalog_versions` record.
    * Insert into `eits_modules`.
    * Insert into `eits_measures` and `eits_catalog_measures`.
    * Insert relationships into `eits_module_measures`.
    * Commit Transaction (Rollback immediately on failure).

## 4. Technical Requirements
* **Language:** Python 3.10+
* **Dependencies:** `requests`, `pandas`, `openpyxl` (for Excel parsing), `psycopg2` or `SQLAlchemy` (for database operations), `uuid`. Ensure a `requirements.txt` is generated.
* **Database Connection:** Must use environment variables for database credentials (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME`), do not hardcode.
* **Logging:** Implement robust logging (INFO for progress, WARNING for data mapping anomalies, ERROR for database/fetch failures).