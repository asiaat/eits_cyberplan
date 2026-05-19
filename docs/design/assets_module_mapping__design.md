# UI & Logic Implementation Guide: Asset to Target Modeling (Module Assignment)

## 1. Context & Business Logic
The user is in the "Assets" (Varad) view. We need to allow them to assign an E-ITS Module to an Asset, effectively turning it into a "Target Object" (Sihtobjekt) and triggering the automated Implementation Plan (IMR) generation.

**CRITICAL RULE: The Business Process (BP) Dependency**
In E-ITS methodology, an asset must be linked to a Business Process to inherit its `protection_need` (NORMAL, HIGH, VERY_HIGH). The backend IMR generation logic relies on this exact field to determine if `HIGH` measure levels should be included.

## 2. Frontend / UI Requirements (Assets View)
Modify the Asset Details view or Asset List view to support "Modeling" (Assigning an E-ITS Module):

* **Action Button:** "Assign Module" / "Modelleeri" visible on an Asset record.
* **Pre-Condition Validation & Warning:** * Check if the asset has a linked Business Process (i.e., exists in `process_assets` relation).
    * *Warning UI:* If no BP is linked, display a prominent warning banner in the assignment modal: "Warning: This asset is not linked to any Business Process. Default protection needs (NORMAL) will be applied. It is highly recommended to link it to a Business Process first to inherit correct protection requirements."
* **Module Assignment Modal/Drawer:**
    * **Module Search:** A dropdown/search component fetching from `eits_modules` (e.g., search by code "SYS.2.1" or name).
    * **Justification (Optional):** A text area for `justification` (to be stored in `asset_module_mappings`).
    * **Confirmation:** Submitting this form calls the atomic backend endpoint `POST /api/tenants/{tenant_id}/assets/{asset_id}/modules` we defined previously.

## 3. Backend Verification
Ensure the `POST /api/tenants/{tenant_id}/assets/{asset_id}/modules` endpoint handles the BP dependency correctly:
* Before generating `imr_items`, read the `protection_need` of the specific Asset.
* If no BP is linked, ensure the `protection_need` acts as `'NORMAL'` and the query to `eits_module_measures` only pulls `BASE` and `STANDARD` measures.
* Return the created mapping and the count of generated IMR items so the UI can display a success toast (e.g., "Module SYS.2.1 mapped successfully. 14 implementation tasks generated.").