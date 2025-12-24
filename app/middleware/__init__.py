"""Middleware modules for Ocean backend."""

from app.middleware.timing import QueryTimingMiddleware

__all__ = ["QueryTimingMiddleware"]
