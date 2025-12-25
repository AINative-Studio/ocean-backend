"""
Unit Tests for Middleware Components

Tests timing middleware and other custom middleware.

Issue #20: Achieve 80%+ test coverage
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request, Response
from app.middleware.timing import QueryTimingMiddleware


class TestQueryTimingMiddleware:
    """Test QueryTimingMiddleware"""

    def test_middleware_init_sets_threshold(self):
        """Test that middleware initializes with threshold"""
        app_mock = MagicMock()
        middleware = QueryTimingMiddleware(app_mock, slow_query_threshold_ms=100.0)

        assert middleware.slow_query_threshold_ms == 100.0
        assert middleware.app == app_mock

    def test_middleware_init_default_threshold(self):
        """Test that middleware has default threshold"""
        app_mock = MagicMock()
        middleware = QueryTimingMiddleware(app_mock)

        assert middleware.slow_query_threshold_ms == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
