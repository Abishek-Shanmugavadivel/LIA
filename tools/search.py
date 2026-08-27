"""
Search Tool re-export module for backward compatibility
Imports and re-exports perform_web_search and web_search from tools.web_search
"""

from tools.web_search import perform_web_search, web_search

__all__ = ["perform_web_search", "web_search"]
