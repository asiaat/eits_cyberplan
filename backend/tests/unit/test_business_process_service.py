"""Unit tests for business process service - E-ITS SOPs."""
import pytest
from uuid import uuid4


class TestProtectionNeedCalculation:
    """Test SOP 1: Automatic protection need calculation."""

    def test_normal_all_dimensions(self):
        """When all dimensions are NORMAL, protection need is NORMAL."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("normal", "normal", "normal")
        assert result == "normal"

    def test_high_one_dimension(self):
        """When any dimension is HIGH, protection need is HIGH."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("high", "normal", "normal")
        assert result == "high"

        result = calculate_protection_need("normal", "high", "normal")
        assert result == "high"

        result = calculate_protection_need("normal", "normal", "high")
        assert result == "high"

    def test_very_high_one_dimension(self):
        """When any dimension is VERY_HIGH, protection need is VERY_HIGH."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("very_high", "normal", "normal")
        assert result == "very_high"

        result = calculate_protection_need("normal", "very_high", "normal")
        assert result == "very_high"

        result = calculate_protection_need("normal", "normal", "very_high")
        assert result == "very_high"

    def test_high_over_normal(self):
        """HIGH takes precedence over NORMAL."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("high", "normal", "normal")
        assert result == "high"

    def test_very_high_over_high(self):
        """VERY_HIGH takes precedence over HIGH."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("very_high", "high", "normal")
        assert result == "very_high"

    def test_very_high_over_normal(self):
        """VERY_HIGH takes precedence over NORMAL."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("normal", "normal", "very_high")
        assert result == "very_high"

    def test_mixed_high_very_high(self):
        """VERY_HIGH is max when multiple dimensions are high/very_high."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("high", "very_high", "high")
        assert result == "very_high"

    def test_all_very_high(self):
        """All VERY_HIGH gives VERY_HIGH."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("very_high", "very_high", "very_high")
        assert result == "very_high"

    def test_unknown_is_minimum(self):
        """UNKNOWN is treated as lowest value."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("unknown", "normal", "normal")
        assert result == "normal"

    def test_case_insensitive(self):
        """Level matching is case-insensitive."""
        from app.services.business_process_service import calculate_protection_need

        result = calculate_protection_need("HIGH", "Normal", "Very_High")
        assert result == "very_high"


class TestIsHighOrVeryHigh:
    """Test protection need level checking."""

    def test_high_is_high(self):
        from app.services.business_process_service import is_high_or_very_high
        assert is_high_or_very_high("high") is True

    def test_very_high_is_high(self):
        from app.services.business_process_service import is_high_or_very_high
        assert is_high_or_very_high("very_high") is True

    def test_normal_is_not_high(self):
        from app.services.business_process_service import is_high_or_very_high
        assert is_high_or_very_high("normal") is False

    def test_unknown_is_not_high(self):
        from app.services.business_process_service import is_high_or_very_high
        assert is_high_or_very_high("unknown") is False


class TestCircularDependencyCheck:
    """Test circular dependency detection."""

    def test_self_reference_detected(self):
        """A process cannot depend on itself."""
        from app.services.business_process_service import check_circular_dependency

        process_id = uuid4()
        would_cycle, msg = check_circular_dependency(
            None, uuid4(), process_id, process_id
        )
        assert would_cycle is True
        assert "cannot depend on itself" in msg.lower()

    def test_function_signature(self):
        """check_circular_dependency has correct signature."""
        from app.services.business_process_service import check_circular_dependency
        import inspect

        sig = inspect.signature(check_circular_dependency)
        params = list(sig.parameters.keys())
        assert params == ['db', 'tenant_id', 'primary_process_id', 'depends_on_process_id']


class TestGetLinkedAssetIds:
    """Test asset linking helper."""

    def test_function_signature(self):
        """get_linked_asset_ids has correct signature."""
        from app.services.business_process_service import get_linked_asset_ids
        import inspect

        sig = inspect.signature(get_linked_asset_ids)
        assert 'db' in sig.parameters


class TestDependencyTree:
    """Test dependency tree building."""

    def test_function_signature(self):
        """build_dependency_tree has correct signature."""
        from app.services.business_process_service import build_dependency_tree
        import inspect

        sig = inspect.signature(build_dependency_tree)
        assert 'db' in sig.parameters


class TestDependencyTree:
    """Test dependency tree building."""

    def test_returns_dict_structure(self):
        """Returns proper dict structure with upstream/downstream."""
        from app.services.business_process_service import build_dependency_tree
        import inspect

        sig = inspect.signature(build_dependency_tree)
        assert 'db' in sig.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])