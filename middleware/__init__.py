"""Middleware package — single import surface for all agent middleware.

Usage in main.py:
    from middleware import log_tool_calls
"""

from middleware.logging_middleware import log_tool_calls

__all__ = ["log_tool_calls"]
