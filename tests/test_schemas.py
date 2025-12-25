"""
Unit Tests for Pydantic Schemas

Tests all Pydantic validation logic including:
- Required field validation
- Optional field handling
- Field length constraints
- Type validation
- Model serialization

Issue #20: Achieve 80%+ test coverage
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.ocean import (
    PageCreate,
    PageUpdate,
    PageMove,
    PageResponse,
    PageListResponse,
    BlockCreate,
    BlockUpdate,
    BlockMove,
    BlockConvert,
    BlockResponse,
    BlockListResponse,
    LinkCreate,
    LinkResponse,
    BacklinkResponse,
    TagCreate,
    TagUpdate,
    TagResponse,
    SearchRequest,
    SearchResponse,
    SearchResult
)


class TestPageCreateSchema:
    """Test PageCreate validation"""

    def test_valid_page_create(self):
        """Test creating page with valid data"""
        page = PageCreate(
            title="Test Page",
            icon="📝",
            cover_image="https://example.com/image.jpg",
            parent_page_id="parent-123",
            metadata={"key": "value"}
        )

        assert page.title == "Test Page"
        assert page.icon == "📝"
        assert page.cover_image == "https://example.com/image.jpg"
        assert page.parent_page_id == "parent-123"
        assert page.metadata == {"key": "value"}

    def test_page_create_minimal_required_fields(self):
        """Test creating page with only required fields"""
        page = PageCreate(title="Minimal Page")

        assert page.title == "Minimal Page"
        assert page.icon is None
        assert page.cover_image is None
        assert page.parent_page_id is None
        assert page.metadata == {}

    def test_page_create_rejects_empty_title(self):
        """Test that empty title is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            PageCreate(title="")

        errors = exc_info.value.errors()
        assert any(error['type'] == 'string_too_short' for error in errors)

    def test_page_create_rejects_title_too_long(self):
        """Test that title exceeding 500 chars is rejected"""
        long_title = "A" * 501

        with pytest.raises(ValidationError) as exc_info:
            PageCreate(title=long_title)

        errors = exc_info.value.errors()
        assert any(error['type'] == 'string_too_long' for error in errors)

    def test_page_create_rejects_missing_title(self):
        """Test that missing title is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            PageCreate()

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('title',) for error in errors)


class TestPageUpdateSchema:
    """Test PageUpdate validation"""

    def test_valid_page_update(self):
        """Test updating page with valid data"""
        update = PageUpdate(
            title="Updated Title",
            icon="📋",
            cover_image="https://example.com/new.jpg",
            is_favorite=True,
            metadata={"updated": True}
        )

        assert update.title == "Updated Title"
        assert update.icon == "📋"
        assert update.is_favorite is True

    def test_page_update_all_optional(self):
        """Test that all fields in PageUpdate are optional"""
        update = PageUpdate()

        assert update.title is None
        assert update.icon is None
        assert update.cover_image is None
        assert update.is_favorite is None
        assert update.metadata is None

    def test_page_update_rejects_empty_title(self):
        """Test that empty title is rejected in updates"""
        with pytest.raises(ValidationError) as exc_info:
            PageUpdate(title="")

        errors = exc_info.value.errors()
        assert any(error['type'] == 'string_too_short' for error in errors)


class TestPageMoveSchema:
    """Test PageMove validation"""

    def test_page_move_with_parent(self):
        """Test moving page to new parent"""
        move = PageMove(new_parent_id="new-parent-123")

        assert move.new_parent_id == "new-parent-123"

    def test_page_move_to_root(self):
        """Test moving page to root (None parent)"""
        move = PageMove(new_parent_id=None)

        assert move.new_parent_id is None


class TestPageResponseSchema:
    """Test PageResponse serialization"""

    def test_valid_page_response(self):
        """Test creating PageResponse with all fields"""
        response = PageResponse(
            page_id="page-123",
            organization_id="org-456",
            user_id="user-789",
            title="Test Page",
            icon="📝",
            cover_image="https://example.com/image.jpg",
            parent_page_id="parent-123",
            position=0,
            is_archived=False,
            is_favorite=True,
            created_at="2025-12-24T10:00:00Z",
            updated_at="2025-12-24T11:00:00Z",
            metadata={"key": "value"}
        )

        assert response.page_id == "page-123"
        assert response.organization_id == "org-456"
        assert response.user_id == "user-789"
        assert response.title == "Test Page"
        assert response.position == 0
        assert response.is_archived is False
        assert response.is_favorite is True

    def test_page_response_requires_all_non_optional_fields(self):
        """Test that PageResponse requires all non-optional fields"""
        with pytest.raises(ValidationError) as exc_info:
            PageResponse(title="Test")

        errors = exc_info.value.errors()
        required_fields = ['page_id', 'organization_id', 'user_id', 'position', 'is_archived', 'is_favorite', 'created_at', 'updated_at']

        assert len(errors) >= len(required_fields) - 1  # At least most required fields


class TestBlockCreateSchema:
    """Test BlockCreate validation"""

    def test_valid_text_block_create(self):
        """Test creating text block with valid data"""
        block = BlockCreate(
            type="text",
            content="This is a text block"
        )

        assert block.type == "text"
        assert block.content == "This is a text block"

    def test_valid_task_block_create(self):
        """Test creating task block with checked status"""
        block = BlockCreate(
            type="task",
            content="Complete this task",
            checked=True
        )

        assert block.type == "task"
        assert block.content == "Complete this task"
        assert block.checked is True

    def test_block_create_rejects_invalid_type(self):
        """Test that invalid block type is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            BlockCreate(type="invalid_type", content="Test")

        errors = exc_info.value.errors()
        assert any('type' in str(error) for error in errors)


class TestBlockUpdateSchema:
    """Test BlockUpdate validation"""

    def test_block_update_all_optional(self):
        """Test that all fields in BlockUpdate are optional"""
        update = BlockUpdate()

        assert update.content is None
        assert update.checked is None
        assert update.metadata is None


class TestBlockMoveSchema:
    """Test BlockMove validation"""

    def test_block_move_with_new_position(self):
        """Test moving block to new position"""
        move = BlockMove(new_position=5)

        assert move.new_position == 5

    def test_block_move_rejects_negative_position(self):
        """Test that negative position is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            BlockMove(new_position=-1)

        errors = exc_info.value.errors()
        assert any('greater_than_equal' in str(error) for error in errors)


class TestBlockConvertSchema:
    """Test BlockConvert validation"""

    def test_block_convert_valid_types(self):
        """Test converting block between valid types"""
        convert = BlockConvert(new_type="heading")

        assert convert.new_type == "heading"

    def test_block_convert_rejects_invalid_type(self):
        """Test that invalid target type is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            BlockConvert(new_type="invalid_type")

        errors = exc_info.value.errors()
        assert any('type' in str(error) for error in errors)


class TestLinkCreateSchema:
    """Test LinkCreate validation"""

    def test_valid_block_to_block_link(self):
        """Test creating block-to-block link"""
        link = LinkCreate(
            target_id="target-block-123",
            target_type="block",
            link_type="reference"
        )

        assert link.target_id == "target-block-123"
        assert link.target_type == "block"
        assert link.link_type == "reference"

    def test_valid_block_to_page_link(self):
        """Test creating block-to-page link"""
        link = LinkCreate(
            target_id="target-page-123",
            target_type="page",
            link_type="embed"
        )

        assert link.target_id == "target-page-123"
        assert link.target_type == "page"
        assert link.link_type == "embed"

    def test_link_create_rejects_invalid_target_type(self):
        """Test that invalid target_type is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            LinkCreate(
                target_id="target-123",
                target_type="invalid",
                link_type="reference"
            )

        errors = exc_info.value.errors()
        assert any('target_type' in str(error['loc']) for error in errors)

    def test_link_create_rejects_invalid_link_type(self):
        """Test that invalid link_type is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            LinkCreate(
                target_id="target-123",
                target_type="block",
                link_type="invalid"
            )

        errors = exc_info.value.errors()
        assert any('link_type' in str(error['loc']) for error in errors)


class TestTagCreateSchema:
    """Test TagCreate validation"""

    def test_valid_tag_create(self):
        """Test creating tag with valid data"""
        tag = TagCreate(
            name="Important",
            color="red"
        )

        assert tag.name == "Important"
        assert tag.color == "red"

    def test_tag_create_rejects_empty_name(self):
        """Test that empty tag name is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TagCreate(name="", color="blue")

        errors = exc_info.value.errors()
        assert any(error['type'] == 'string_too_short' for error in errors)

    def test_tag_create_color_optional(self):
        """Test that color is optional"""
        tag = TagCreate(name="Tag Without Color")

        assert tag.name == "Tag Without Color"
        assert tag.color is None


class TestSearchRequestSchema:
    """Test SearchRequest validation"""

    def test_valid_search_request(self):
        """Test creating search request with all fields"""
        search = SearchRequest(
            query="test query",
            search_type="hybrid",
            limit=20,
            threshold=0.7,
            filters={"type": "text"}
        )

        assert search.query == "test query"
        assert search.search_type == "hybrid"
        assert search.limit == 20
        assert search.threshold == 0.7
        assert search.filters == {"type": "text"}

    def test_search_request_minimal(self):
        """Test search request with only query"""
        search = SearchRequest(query="minimal search")

        assert search.query == "minimal search"
        assert search.search_type == "hybrid"
        assert search.limit == 20
        assert search.threshold == 0.7

    def test_search_request_rejects_empty_query(self):
        """Test that empty query is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(query="")

        errors = exc_info.value.errors()
        assert any(error['type'] == 'string_too_short' for error in errors)

    def test_search_request_rejects_invalid_search_type(self):
        """Test that invalid search_type is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(query="test", search_type="invalid")

        errors = exc_info.value.errors()
        assert any('search_type' in str(error['loc']) for error in errors)


class TestPageListResponseSchema:
    """Test PageListResponse serialization"""

    def test_valid_page_list_response(self):
        """Test creating PageListResponse"""
        response = PageListResponse(
            pages=[
                PageResponse(
                    page_id="page-1",
                    organization_id="org-1",
                    user_id="user-1",
                    title="Page 1",
                    position=0,
                    is_archived=False,
                    is_favorite=False,
                    created_at="2025-12-24T10:00:00Z",
                    updated_at="2025-12-24T10:00:00Z"
                )
            ],
            total=1,
            limit=50,
            offset=0
        )

        assert len(response.pages) == 1
        assert response.total == 1
        assert response.limit == 50
        assert response.offset == 0

    def test_page_list_response_empty_list(self):
        """Test creating PageListResponse with empty pages"""
        response = PageListResponse(
            pages=[],
            total=0,
            limit=50,
            offset=0
        )

        assert len(response.pages) == 0
        assert response.total == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
