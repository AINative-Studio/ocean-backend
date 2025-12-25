"""
Unit Tests for Configuration Module

Tests configuration loading and validation.

Issue #20: Achieve 80%+ test coverage
"""

import pytest
from app.config import Settings


class TestSettings:
    """Test Settings configuration"""

    def test_settings_loads_successfully(self):
        """Test that Settings can be instantiated"""
        settings = Settings()

        # Verify core attributes exist
        assert hasattr(settings, 'PROJECT_NAME')
        assert hasattr(settings, 'API_V1_STR')
        assert hasattr(settings, 'DEBUG')
        assert hasattr(settings, 'BACKEND_CORS_ORIGINS')

    def test_api_v1_str_has_correct_prefix(self):
        """Test that API_V1_STR has the correct format"""
        settings = Settings()

        assert settings.API_V1_STR.startswith('/api/v')

    def test_backend_cors_origins_is_list(self):
        """Test that BACKEND_CORS_ORIGINS is a list"""
        settings = Settings()

        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)

    def test_project_name_is_non_empty(self):
        """Test that PROJECT_NAME is set"""
        settings = Settings()

        assert settings.PROJECT_NAME
        assert len(settings.PROJECT_NAME) > 0

    def test_debug_is_boolean(self):
        """Test that DEBUG is a boolean"""
        settings = Settings()

        assert isinstance(settings.DEBUG, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
