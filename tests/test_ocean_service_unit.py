"""
Unit Tests for OceanService

These tests verify the business logic of OceanService methods using mocking
to avoid external dependencies on ZeroDB. Tests focus on:
- Input validation
- Data transformation
- Error handling
- Multi-tenant isolation logic

Issue #20: Achieve 80%+ test coverage
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from app.services.ocean_service import OceanService


class TestOceanServiceInit:
    """Test OceanService initialization"""

    def test_init_sets_correct_attributes(self):
        """Test that __init__ properly sets all required attributes"""
        service = OceanService(
            api_url="https://api.example.com/",
            api_key="test-key-123",
            project_id="project-456"
        )

        assert service.api_url == "https://api.example.com"
        assert service.api_key == "test-key-123"
        assert service.project_id == "project-456"
        assert service.table_name == "ocean_pages"
        assert service.tags_table_name == "ocean_tags"
        assert service.blocks_table_name == "ocean_blocks"
        assert service.links_table_name == "ocean_block_links"
        assert service.headers == {
            "Authorization": "Bearer test-key-123",
            "Content-Type": "application/json"
        }

    def test_init_strips_trailing_slash(self):
        """Test that __init__ removes trailing slash from api_url"""
        service = OceanService(
            api_url="https://api.example.com///",
            api_key="test-key",
            project_id="test-project"
        )

        assert service.api_url == "https://api.example.com"


class TestPageCreationValidation:
    """Test page creation input validation"""

    @pytest.fixture
    def service(self):
        """Create OceanService instance for testing"""
        return OceanService(
            api_url="https://api.example.com",
            api_key="test-key",
            project_id="test-project"
        )

    @pytest.mark.asyncio
    async def test_create_page_validates_org_id(self, service):
        """Test that create_page raises ValueError for missing org_id"""
        with pytest.raises(ValueError, match="organization_id and user_id are required"):
            await service.create_page(
                org_id="",  # Empty org_id
                user_id="user-123",
                page_data={"title": "Test Page"}
            )

    @pytest.mark.asyncio
    async def test_create_page_validates_user_id(self, service):
        """Test that create_page raises ValueError for missing user_id"""
        with pytest.raises(ValueError, match="organization_id and user_id are required"):
            await service.create_page(
                org_id="org-123",
                user_id="",  # Empty user_id
                page_data={"title": "Test Page"}
            )

    @pytest.mark.asyncio
    async def test_create_page_validates_title(self, service):
        """Test that create_page raises ValueError for missing title"""
        with pytest.raises(ValueError, match="title is required"):
            await service.create_page(
                org_id="org-123",
                user_id="user-123",
                page_data={}  # No title
            )

    @pytest.mark.asyncio
    async def test_create_page_validates_title_not_empty(self, service):
        """Test that create_page raises ValueError for empty title"""
        with pytest.raises(ValueError, match="title is required"):
            await service.create_page(
                org_id="org-123",
                user_id="user-123",
                page_data={"title": ""}  # Empty title
            )


class TestBlockCreationValidation:
    """Test block creation input validation"""

    @pytest.fixture
    def service(self):
        """Create OceanService instance for testing"""
        return OceanService(
            api_url="https://api.example.com",
            api_key="test-key",
            project_id="test-project"
        )

    @pytest.mark.asyncio
    async def test_create_block_validates_org_id(self, service):
        """Test that create_block raises ValueError for missing org_id"""
        with pytest.raises(ValueError, match="organization_id and user_id are required"):
            await service.create_block(
                org_id="",  # Empty org_id
                user_id="user-123",
                block_data={"page_id": "page-123", "type": "text", "content": "Test"}
            )

    @pytest.mark.asyncio
    async def test_create_block_validates_user_id(self, service):
        """Test that create_block raises ValueError for missing user_id"""
        with pytest.raises(ValueError, match="organization_id and user_id are required"):
            await service.create_block(
                org_id="org-123",
                user_id="",  # Empty user_id
                block_data={"page_id": "page-123", "type": "text", "content": "Test"}
            )

    @pytest.mark.asyncio
    async def test_create_block_validates_page_id(self, service):
        """Test that create_block raises ValueError for missing page_id"""
        with pytest.raises(ValueError, match="page_id is required"):
            await service.create_block(
                org_id="org-123",
                user_id="user-123",
                block_data={"type": "text", "content": "Test"}  # No page_id
            )

    @pytest.mark.asyncio
    async def test_create_block_validates_block_type(self, service):
        """Test that create_block raises ValueError for missing type"""
        with pytest.raises(ValueError, match="type is required"):
            await service.create_block(
                org_id="org-123",
                user_id="user-123",
                block_data={"page_id": "page-123", "content": "Test"}  # No type
            )


class TestTagCreationValidation:
    """Test tag creation input validation"""

    @pytest.fixture
    def service(self):
        """Create OceanService instance for testing"""
        return OceanService(
            api_url="https://api.example.com",
            api_key="test-key",
            project_id="test-project"
        )

    @pytest.mark.asyncio
    async def test_create_tag_validates_org_id(self, service):
        """Test that create_tag raises ValueError for missing org_id"""
        with pytest.raises(ValueError, match="organization_id is required"):
            await service.create_tag(
                org_id="",  # Empty org_id
                tag_data={"name": "TestTag", "color": "blue"}
            )

    @pytest.mark.asyncio
    async def test_create_tag_validates_name(self, service):
        """Test that create_tag raises ValueError for missing name"""
        with pytest.raises(ValueError, match="name is required"):
            await service.create_tag(
                org_id="org-123",
                tag_data={"color": "blue"}  # No name
            )

    @pytest.mark.asyncio
    async def test_create_tag_validates_name_not_empty(self, service):
        """Test that create_tag raises ValueError for empty name"""
        with pytest.raises(ValueError, match="name is required"):
            await service.create_tag(
                org_id="org-123",
                tag_data={"name": "", "color": "blue"}  # Empty name
            )


class TestLinkCreationValidation:
    """Test link creation input validation"""

    @pytest.fixture
    def service(self):
        """Create OceanService instance for testing"""
        return OceanService(
            api_url="https://api.example.com",
            api_key="test-key",
            project_id="test-project"
        )

    @pytest.mark.asyncio
    async def test_create_link_validates_org_id(self, service):
        """Test that create_link raises ValueError for missing org_id"""
        with pytest.raises(ValueError, match="organization_id is required"):
            await service.create_link(
                org_id="",  # Empty org_id
                link_data={
                    "source_block_id": "block-123",
                    "target_id": "block-456",
                    "target_type": "block",
                    "link_type": "reference"
                }
            )

    @pytest.mark.asyncio
    async def test_create_link_validates_source_block_id(self, service):
        """Test that create_link raises ValueError for missing source_block_id"""
        with pytest.raises(ValueError, match="source_block_id is required"):
            await service.create_link(
                org_id="org-123",
                link_data={
                    "target_id": "block-456",
                    "target_type": "block",
                    "link_type": "reference"
                }  # No source_block_id
            )

    @pytest.mark.asyncio
    async def test_create_link_validates_target_id(self, service):
        """Test that create_link raises ValueError for missing target_id"""
        with pytest.raises(ValueError, match="target_id is required"):
            await service.create_link(
                org_id="org-123",
                link_data={
                    "source_block_id": "block-123",
                    "target_type": "block",
                    "link_type": "reference"
                }  # No target_id
            )

    @pytest.mark.asyncio
    async def test_create_link_validates_target_type(self, service):
        """Test that create_link raises ValueError for missing target_type"""
        with pytest.raises(ValueError, match="target_type is required"):
            await service.create_link(
                org_id="org-123",
                link_data={
                    "source_block_id": "block-123",
                    "target_id": "block-456",
                    "link_type": "reference"
                }  # No target_type
            )

    @pytest.mark.asyncio
    async def test_create_link_validates_link_type(self, service):
        """Test that create_link raises ValueError for missing link_type"""
        with pytest.raises(ValueError, match="link_type is required"):
            await service.create_link(
                org_id="org-123",
                link_data={
                    "source_block_id": "block-123",
                    "target_id": "block-456",
                    "target_type": "block"
                }  # No link_type
            )


class TestServiceHelperMethods:
    """Test private helper methods"""

    @pytest.fixture
    def service(self):
        """Create OceanService instance for testing"""
        return OceanService(
            api_url="https://api.example.com",
            api_key="test-key",
            project_id="test-project"
        )

    def test_build_query_filter_with_org_id_only(self, service):
        """Test _build_query_filter with only org_id"""
        result = service._build_query_filter("org-123")

        assert result == {"organization_id": "org-123"}

    def test_build_query_filter_with_additional_filters(self, service):
        """Test _build_query_filter with additional filters"""
        result = service._build_query_filter(
            "org-123",
            {"is_archived": False, "title": "Test"}
        )

        assert result == {
            "organization_id": "org-123",
            "is_archived": False,
            "title": "Test"
        }

    def test_validate_uuid_with_valid_uuid(self, service):
        """Test _validate_uuid with valid UUID string"""
        valid_uuid = str(uuid.uuid4())
        result = service._validate_uuid(valid_uuid)

        assert result is True

    def test_validate_uuid_with_invalid_uuid(self, service):
        """Test _validate_uuid with invalid UUID string"""
        result = service._validate_uuid("not-a-uuid")

        assert result is False

    def test_validate_uuid_with_empty_string(self, service):
        """Test _validate_uuid with empty string"""
        result = service._validate_uuid("")

        assert result is False

    def test_sanitize_metadata_removes_sensitive_fields(self, service):
        """Test _sanitize_metadata removes sensitive information"""
        metadata = {
            "password": "secret123",
            "api_key": "key-456",
            "public_field": "visible"
        }

        result = service._sanitize_metadata(metadata)

        assert "password" not in result
        assert "api_key" not in result
        assert result["public_field"] == "visible"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
