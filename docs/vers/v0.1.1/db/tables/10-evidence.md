# Evidence Management

Tables for evidence storage, linking evidence to various target entities, and support for review cycles.

---

## `evidences`

Evidence/document records. Supports soft delete. Each evidence entry represents an uploaded file, URL reference, or other proof of implementation.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `title` | VARCHAR(255) | NOT NULL | — | Evidence title |
| `evidence_type` | VARCHAR(50) | NOT NULL | — | Type (e.g., `file`, `url`, `text_note`) |
| `storage_uri` | VARCHAR(500) | YES | — | URI in S3/MinIO storage |
| `external_url` | VARCHAR(500) | YES | — | External URL reference |
| `file_hash` | VARCHAR(64) | YES | — | SHA-256 hash of file content (INDEX) |
| `version` | VARCHAR(20) | YES | — | Version identifier |
| `owner_user_id` | UUID | YES, FK → `local_users.id` | — | Evidence owner |
| `valid_from` | TIMESTAMP | YES | — | Validity start date |
| `valid_until` | TIMESTAMP | YES | — | Validity end date |
| `review_due_date` | TIMESTAMP | YES | — | Deadline for reviewing this evidence |
| `file_size` | BIGINT | YES | — | File size in bytes |
| `mime_type` | VARCHAR(100) | YES | — | MIME type of uploaded file |
| `download_count` | INTEGER | YES | `0` | Number of times downloaded |
| `created_at` | TIMESTAMP | YES | `now()` | Creation timestamp |
| `deleted_at` | TIMESTAMP | YES | — | Soft delete timestamp |
| `deleted_by` | UUID | YES | — | Who deleted this record |

**Soft Delete:** Yes

**Relationships:**
- `owner_user` → `LocalUser`
- `links` → `EvidenceLink` (links to target entities)

---

## `evidence_links`

Polymorphic junction table linking evidence to various target entities (IMR items, risks, business processes, assets, measures).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | PK | `uuid4` | Primary key |
| `tenant_id` | UUID | NOT NULL, FK → `app_tenants.id` | — | Tenant (INDEX) |
| `evidence_id` | UUID | NOT NULL, FK → `evidences.id` | — | Evidence record |
| `target_type` | VARCHAR(50) | NOT NULL | — | Type of linked entity (e.g., `imr_item`, `risk`, `business_process`, `asset`, `measure`) |
| `target_id` | UUID | NOT NULL | — | ID of the linked entity |
| `link_type` | VARCHAR(50) | YES | `'general'` | Type of link (INDEX) |

**Relationships:**
- `evidence` → `Evidence`
