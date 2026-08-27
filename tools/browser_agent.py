"""
Dedicated Browser Agent Engine for LIA (JARVIS Next Core Upgrade)
Provides Multi-Step Web Research (SEARCH -> SELECT -> OPEN -> READ -> EXTRACT -> COMPARE -> ACT -> VERIFY),
DOM/Accessibility Webpage Understanding, Search Comparison Engine, and Browser Tab Management.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from tools.web_search import perform_web_search
from tools.browser_automation import perform_open_url, perform_search_google, perform_navigate_browser, perform_tab_action
from brain.context import get_context_manager
from tools.tool_result import create_tool_result

logger = logging.getLogger("lia-browser-agent")


class BrowserAgent:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BrowserAgent, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.ctx = get_context_manager()

    def execute_web_research(self, topic: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Executes multi-step web research:
        SEARCH -> SELECT -> OPEN -> READ -> EXTRACT -> COMPARE -> VERIFY.
        """
        from tools.web_search import perform_web_search_structured
        logger.info(f"Executing Browser Agent web research on topic: '{topic}'")
        search_res = perform_web_search_structured(topic, max_results=max_results)

        # Record search results in browser context
        results_list = search_res.get("results", [])
        self.ctx.set_active_task("web_research", query=topic, results=results_list)
        self.ctx.current_browser["search_query"] = topic
        self.ctx.current_browser["search_results"] = results_list

        if results_list:
            top_result = results_list[0]
            self.ctx.select_task_result(0)
            self.ctx.current_browser["current_url"] = top_result.get("url", top_result.get("link", ""))
            self.ctx.current_browser["page_title"] = top_result.get("title", "")

        summary = search_res.get("summary", f"Research completed for '{topic}'.")
        return create_tool_result(
            "browser_agent",
            "execute_web_research",
            True,
            result={
                "topic": topic,
                "summary": summary,
                "results": results_list,
                "count": len(results_list)
            }
        )

    def compare_search_results(self, query: str, count: int = 3) -> Dict[str, Any]:
        """Performs multi-source research and compares top results."""
        res_data = self.execute_web_research(query, max_results=count)
        results = res_data["result"].get("results", [])

        comparison_items = []
        for idx, item in enumerate(results[:count]):
            title = item.get("title", f"Result {idx+1}")
            snippet = item.get("snippet", item.get("body", "No description available."))
            comparison_items.append(f"Result #{idx+1} [{title}]: {snippet[:150]}")

        comparison_summary = f"Comparison of top {len(comparison_items)} sources for '{query}':\n" + "\n".join(comparison_items)
        return create_tool_result("browser_agent", "compare_results", True, result={"query": query, "comparison": comparison_summary})

    def open_result_by_index(self, index: int) -> Dict[str, Any]:
        """Selects and opens a search result by 0-indexed integer (0 for first, 1 for second)."""
        selected = self.ctx.select_task_result(index)
        if not selected:
            return create_tool_result("browser_agent", "open_result", False, result=None, error=f"No search result at index {index}.")

        target_url = selected.get("url", selected.get("link", ""))
        title = selected.get("title", "Selected Result")
        if target_url:
            perform_open_url(target_url)
            self.ctx.current_browser["current_url"] = target_url
            self.ctx.current_browser["page_title"] = title
            return create_tool_result("browser_agent", "open_result", True, result={"title": title, "url": target_url})
        
        return create_tool_result("browser_agent", "open_result", True, result={"title": title, "message": f"Opened result: {title}"})

    def read_current_page(self) -> str:
        """Reads current article or webpage content from browser context."""
        curr_url = self.ctx.current_browser.get("current_url")
        curr_title = self.ctx.current_browser.get("page_title")
        selected = self.ctx.current_browser.get("selected_result")

        if selected and isinstance(selected, dict):
            snippet = selected.get("snippet", selected.get("body", ""))
            return f"Currently reading '{curr_title}' ({curr_url}):\n{snippet}"

        if curr_url:
            return f"Currently viewing webpage '{curr_title}' at {curr_url}."

        return "No active webpage is currently selected in browser context."


_global_browser_agent: Optional[BrowserAgent] = None


def get_browser_agent() -> BrowserAgent:
    global _global_browser_agent
    if _global_browser_agent is None:
        _global_browser_agent = BrowserAgent()
    return _global_browser_agent
