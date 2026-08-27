"""
Unit tests for LIA Phase 3 Web Search Tool
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pytest
except ImportError:
    pytest = None
from tools.search import perform_web_search, web_search



def test_perform_web_search_valid():
    result = perform_web_search("Python 3.12 release features", max_results=2)
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0
    assert "query was empty" not in result.lower()


def test_perform_web_search_empty():
    result = perform_web_search("")
    assert "empty" in result.lower()


def test_web_search_tanglish_query():
    result = perform_web_search("Chennai weather today in Tamil Nadu", max_results=2)
    assert result is not None
    assert len(result) > 0


def mark_asyncio(func):
    return pytest.mark.asyncio(func) if pytest else func

@mark_asyncio
async def test_async_web_search_tool():

    res = await web_search("latest AI news")
    assert isinstance(res, str)
    assert len(res) > 0


if __name__ == "__main__":
    print("Running synchronous search tests...")
    test_perform_web_search_valid()
    print("test_perform_web_search_valid passed!")
    test_perform_web_search_empty()
    print("test_perform_web_search_empty passed!")
    test_web_search_tanglish_query()
    print("test_web_search_tanglish_query passed!")

    print("Running async tool test...")
    asyncio.run(test_async_web_search_tool())
    print("test_async_web_search_tool passed!")

    print("\nALL SEARCH TESTS PASSED SUCCESSFULLY!")
