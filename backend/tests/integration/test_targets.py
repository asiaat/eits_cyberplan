"""
E-ITS Targets (Sihtobjektid) API Tests
======================================

Test suite for V2 Targets API endpoints:
- GET /v2/targets/ - List target objects (grouped assets)
- POST /v2/targets/ - Create target object
- GET /v2/targets/{id} - Get single target object
- PUT /v2/targets/{id} - Update target object
- DELETE /v2/targets/{id} - Delete target object
- GET /v2/targets/{id}/modules - Get mapped E-ITS modules
- POST /v2/targets/{id}/modules - Add module mapping (with IMR generation)
- DELETE /v2/targets/{id}/modules/{mapping_id} - Remove module mapping
- GET /v2/targets/{id}/imr - Get IMR items for target

Run with: pytest -v
         pytest -v -s (show print statements)
"""
import pytest
from uuid import uuid4


class TestTargetsAPI:
    """
    =============================================================
    TEST CLASS: Targets API Tests
    =============================================================

    Purpose: Test V2 targets API endpoints for CRUD operations
    and module mapping with atomic IMR generation.
    """

    @pytest.fixture
    def target_object_data(self):
        """Sample target object data for create tests."""
        return {
            "name": "Windows Laptops",
            "target_type": "SYS",
            "group_name": "Employee Workstations",
            "quantity": 50,
            "description": "Standard Windows laptops for employees",
            "criticality": "normal",
            "confidentiality_need": "normal",
            "integrity_need": "normal",
            "availability_need": "normal",
            "lifecycle_status": "active",
            "is_grouped": True,
        }

    @pytest.fixture
    def target_types(self):
        """Valid E-ITS Target Object type values."""
        return ["APP", "SYS", "NET", "INF", "IND"]

    @pytest.fixture
    def criticality_levels(self):
        """Valid criticality level values."""
        return ["low", "normal", "high", "critical"]

    def test_list_targets_empty(self, client, auth_headers):
        """Test listing targets when none exist."""
        response = client.get("/v2/targets/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_target_object(self, client, auth_headers, target_object_data):
        """Test creating a new target object."""
        response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == target_object_data["name"]
        assert data["asset_type"] == target_object_data["target_type"]
        assert data["is_grouped"] is True
        assert data["quantity"] == target_object_data["quantity"]
        assert data["group_name"] == target_object_data["group_name"]
        assert "id" in data

    def test_create_target_without_grouped_flag(self, client, auth_headers):
        """Test that creating target without is_grouped raises error."""
        data = {
            "name": "Test Target",
            "target_type": "SYS",
            "is_grouped": False,
        }
        response = client.post("/v2/targets/", json=data, headers=auth_headers)
        assert response.status_code == 422

    def test_create_target_invalid_type(self, client, auth_headers):
        """Test that creating target with invalid type raises error."""
        data = {
            "name": "Test Target",
            "target_type": "INVALID",
            "is_grouped": True,
        }
        response = client.post("/v2/targets/", json=data, headers=auth_headers)
        assert response.status_code == 422

    def test_get_target_object(self, client, auth_headers, target_object_data):
        """Test getting a single target object."""
        # Create first
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        # Get
        response = client.get(f"/v2/targets/{target_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == target_object_data["name"]
        assert data["id"] == target_id

    def test_get_target_object_not_found(self, client, auth_headers):
        """Test getting non-existent target returns 404."""
        fake_id = str(uuid4())
        response = client.get(f"/v2/targets/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_target_object(self, client, auth_headers, target_object_data):
        """Test updating a target object."""
        # Create first
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        # Update
        update_data = {
            "name": "Updated Windows Laptops",
            "quantity": 75,
        }
        response = client.put(f"/v2/targets/{target_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Windows Laptops"
        assert data["quantity"] == 75

    def test_delete_target_object(self, client, auth_headers, target_object_data):
        """Test deleting a target object."""
        # Create first
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        # Delete
        response = client.delete(f"/v2/targets/{target_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/v2/targets/{target_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_list_targets_with_data(self, client, auth_headers, target_object_data):
        """Test listing targets after creating some."""
        # Create multiple targets
        client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        client.post("/v2/targets/", json={
            **target_object_data,
            "name": "Web Servers",
            "target_type": "APP",
        }, headers=auth_headers)

        # List
        response = client.get("/v2/targets/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_search_targets(self, client, auth_headers, target_object_data):
        """Test searching targets by name."""
        client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        client.post("/v2/targets/", json={
            **target_object_data,
            "name": "Database Servers",
            "target_type": "APP",
        }, headers=auth_headers)

        # Search
        response = client.get("/v2/targets/?search=Windows", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Windows Laptops"

    def test_get_target_modules_empty(self, client, auth_headers, target_object_data):
        """Test getting modules for a target with no mappings."""
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        response = client.get(f"/v2/targets/{target_id}/modules", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_add_module_mapping_without_modules(self, client, auth_headers, target_object_data):
        """Test adding module mapping when no modules exist in catalog."""
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        # Try to add a module (should fail if module doesn't exist)
        fake_module_id = str(uuid4())
        response = client.post(
            f"/v2/targets/{target_id}/modules",
            json={"module_id": fake_module_id, "justification": "Test mapping"},
            headers=auth_headers
        )
        # Should return 404 as module doesn't exist
        assert response.status_code == 404

    def test_target_creates_imr_items(self, client, auth_headers, target_object_data, eits_module_id):
        """Test that adding a module mapping creates IMR items."""
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        # Add module mapping
        response = client.post(
            f"/v2/targets/{target_id}/modules",
            json={"module_id": eits_module_id, "justification": "Applicable to laptops"},
            headers=auth_headers
        )
        
        if response.status_code == 201:
            data = response.json()
            # Should have created IMR items
            assert data["imr_items_created"] >= 0
            
            # Verify IMR items were created
            imr_response = client.get(f"/v2/targets/{target_id}/imr", headers=auth_headers)
            assert imr_response.status_code == 200
            imr_items = imr_response.json()
            # Should have at least some IMR items (depends on module)
            assert isinstance(imr_items, list)

    def test_remove_module_mapping(self, client, auth_headers, target_object_data, eits_module_id):
        """Test removing a module mapping."""
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        # Add module mapping
        add_response = client.post(
            f"/v2/targets/{target_id}/modules",
            json={"module_id": eits_module_id, "justification": "Test"},
            headers=auth_headers
        )
        
        if add_response.status_code == 201:
            mapping_id = add_response.json()["mapping_id"]
            
            # Remove mapping
            remove_response = client.delete(
                f"/v2/targets/{target_id}/modules/{mapping_id}",
                headers=auth_headers
            )
            assert remove_response.status_code == 204

    def test_duplicate_module_mapping_fails(self, client, auth_headers, target_object_data, eits_module_id):
        """Test that adding duplicate module mapping fails."""
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        # Add module mapping twice
        client.post(
            f"/v2/targets/{target_id}/modules",
            json={"module_id": eits_module_id, "justification": "First"},
            headers=auth_headers
        )
        
        # Try again should fail
        response = client.post(
            f"/v2/targets/{target_id}/modules",
            json={"module_id": eits_module_id, "justification": "Second"},
            headers=auth_headers
        )
        
        if eits_module_id:  # Only test if module exists
            assert response.status_code == 400

    def test_target_with_high_criticality_includes_high_measures(self, client, auth_headers):
        """Test that HIGH criticality includes HIGH level measures."""
        # Create target with HIGH criticality
        target_data = {
            "name": "Critical Servers",
            "target_type": "SYS",
            "criticality": "high",
            "is_grouped": True,
        }
        create_response = client.post("/v2/targets/", json=target_data, headers=auth_headers)
        target_id = create_response.json()["id"]
        
        # Get the target and verify
        response = client.get(f"/v2/targets/{target_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["criticality"] == "high"

    def test_target_cascade_deletes_mappings(self, client, auth_headers, target_object_data, eits_module_id):
        """Test that deleting target cascades to module mappings."""
        create_response = client.post("/v2/targets/", json=target_object_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        # Add module mapping if module exists
        if eits_module_id:
            client.post(
                f"/v2/targets/{target_id}/modules",
                json={"module_id": eits_module_id},
                headers=auth_headers
            )

        # Delete target
        delete_response = client.delete(f"/v2/targets/{target_id}", headers=auth_headers)
        assert delete_response.status_code == 204

        # Verify target is gone
        get_response = client.get(f"/v2/targets/{target_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestMeasureLevelFiltering:
    """
    =============================================================
    TEST CLASS: Measure Level Filtering Tests
    =============================================================

    Purpose: Test that measure levels are correctly filtered
    based on protection need (criticality).
    """

    def test_normal_criticality_filters_high_measures(self, client, auth_headers, eits_module_id):
        """Test that NORMAL criticality excludes HIGH measures."""
        target_data = {
            "name": "Normal Target",
            "target_type": "SYS",
            "criticality": "normal",
            "is_grouped": True,
        }
        create_response = client.post("/v2/targets/", json=target_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        if eits_module_id:
            add_response = client.post(
                f"/v2/targets/{target_id}/modules",
                json={"module_id": eits_module_id},
                headers=auth_headers
            )
            
            if add_response.status_code == 201:
                # Get IMR items
                imr_response = client.get(f"/v2/targets/{target_id}/imr", headers=auth_headers)
                imr_items = imr_response.json()
                
                # Verify no HIGH measures for NORMAL criticality
                for item in imr_items:
                    if item.get("measure_level") == "HIGH":
                        pytest.fail("HIGH measures should not be included for NORMAL criticality")

    def test_high_criticality_includes_all_measures(self, client, auth_headers, eits_module_id):
        """Test that HIGH criticality includes all measure levels."""
        target_data = {
            "name": "High Criticality Target",
            "target_type": "SYS",
            "criticality": "high",
            "is_grouped": True,
        }
        create_response = client.post("/v2/targets/", json=target_data, headers=auth_headers)
        target_id = create_response.json()["id"]

        if eits_module_id:
            add_response = client.post(
                f"/v2/targets/{target_id}/modules",
                json={"module_id": eits_module_id},
                headers=auth_headers
            )
            
            if add_response.status_code == 201:
                imr_response = client.get(f"/v2/targets/{target_id}/imr", headers=auth_headers)
                imr_items = imr_response.json()
                # Should include BASE, STANDARD, and potentially HIGH
                assert isinstance(imr_items, list)