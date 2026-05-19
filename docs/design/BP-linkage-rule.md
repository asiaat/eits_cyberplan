### CRITICAL BUSINESS RULE UPDATE: Mandatory Business Process (BP) Linkage

To ensure E-ITS methodology compliance and correct protection need inheritance, I am adding a mandatory validation rule for Target Object modeling:

1. **Strict Dependency:** An Asset CANNOT be assigned an E-ITS module (cannot become a Target Object) unless it is already linked to at least one Business Process (BP) via the `process_assets` table.

2. **Backend Validation:**
   - In the `POST /api/tenants/{tenant_id}/assets/{asset_id}/modules` endpoint, you must implement a pre-check:
     - Query `process_assets` to see if `asset_id` exists.
     - If the count is 0, **ABORT** the operation and return `HTTP 409 Conflict` (or `400 Bad Request`) with the error message: *"Asset must be linked to a Business Process before it can be assigned an E-ITS module."*

3. **Database Integrity:**
   - While the database schema technically permits an `asset_module_mappings` record without a corresponding `process_assets` record, the **Application Service Layer MUST enforce this business rule**. 
   - This ensures that every generated IMR item (`imr_items`) is backed by a valid protection need inherited from a Business Process.

Please update your API implementation plan to include this explicit validation step before Action 1 (Mapping creation) and Action 2 (IMR generation).