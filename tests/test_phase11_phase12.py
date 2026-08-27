"""
Integration & Unit Test Suite for Phase 11 (Advanced Context Engine) & Phase 12 (Coding Agent)
Validates Natural Reference Resolution, Entity Tracking, Confidence Rating, Context Reset,
Project Discovery, Secret Redaction, Automated Fix Loop Execution, and Coding Action Orchestration.
"""

import os
import pytest
from brain.context import get_context_manager, LIAContextManager
from brain.reference_resolver import ReferenceResolver
from brain.orchestrator import LIAOrchestrator, IntentType
from tools.coding import get_coding_agent, LIACodingAgent


@pytest.fixture(autouse=True)
def reset_context_engine():
    ctx = get_context_manager()
    ctx.clear_all()
    yield ctx


def test_entity_tracking_and_confidence_rating(reset_context_engine):
    """Test entity registry tracking and confidence evaluation."""
    ctx = reset_context_engine
    ctx.track_entity(category="applications", name="Chrome", metadata={"browser": "desktop"})
    ctx.track_entity(category="files", name="orchestrator.py", metadata={"path": "brain/orchestrator.py"})
    
    assert len(ctx.entity_registry["applications"]) == 1
    assert ctx.entity_registry["applications"][0]["name"] == "Chrome"
    assert len(ctx.entity_registry["files"]) == 1

    resolver = ReferenceResolver(ctx)
    resolver.resolve("Open it")
    assert ctx.resolution_confidence in ["HIGH", "MEDIUM", "LOW"]


def test_context_reset_command(reset_context_engine):
    """Test context reset command clears short-term state without throwing errors."""
    ctx = reset_context_engine
    ctx.set_active_task("search_task", query="test query", results=["a", "b"])
    ctx.track_entity("files", "test.py")

    resolver = ReferenceResolver(ctx)
    res = resolver.resolve("LIA, forget what we're doing")
    
    assert res["intent_override"] == "context_reset"
    assert ctx.active_task["name"] == "none"
    assert len(ctx.entity_registry["files"]) == 0


def test_coding_agent_project_discovery():
    """Test Coding Agent discovers project type, framework, and top folders."""
    agent = get_coding_agent()
    proj = agent.discover_project(".")
    
    assert "project_type" in proj
    assert "framework" in proj
    assert "root" in proj
    assert proj["package_manager"] in ["npm", "pip", "maven", "gradle"]


def test_coding_agent_secret_redaction():
    """Test secret redaction strips API keys, passwords, and tokens from code content."""
    agent = get_coding_agent()
    raw_code = 'GOOGLE_API_KEY = "AIzaSyDummySecretKeyForTestVerification123"\nDB_PASSWORD = "secret_password_123"'
    redacted = agent.redact_secrets(raw_code)
    
    assert "AIzaSyDummySecretKeyForTestVerification123" not in redacted
    assert "secret_password_123" not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_coding_agent_dev_command_execution():
    """Test Coding Agent executes safe git status and python dev commands."""
    agent = get_coding_agent()
    res = agent.run_dev_command("git status")
    assert res["tool"] == "run_dev_command"
    assert "success" in res


def test_coding_agent_automated_fix_loop():
    """Test automated 10-step fix loop execution."""
    agent = get_coding_agent()
    res = agent.execute_fix_loop("Test error: missing route handler")
    
    assert res["success"] is True
    assert "diagnosis" in res["result"]
    assert "verification" in res["result"]


@pytest.mark.asyncio
async def test_orchestrator_coding_intent_routing():
    """Test Central Orchestrator classifies and routes coding prompts to Coding Agent."""
    orchestrator = LIAOrchestrator()
    intent = orchestrator.classify_intent("LIA, understand this project")
    assert intent["primary_intent"] == IntentType.CODING_ACTION

    res = await orchestrator.process_request("LIA, understand this project")
    assert res.get("status") == "success"
    assert "Project Map" in res.get("message", "") or "Coding Agent" in res.get("message", "")
