"""
Comprehensive Unit & Integration Test Suite for LIA Context Engine (Phase 10)
Covers Context Tracking, Pronoun & Demonstrative Resolution, Ordinals, Follow-up Commands,
Browser Context, Media Context, Device Context, Person Context, Language Context,
Correction Handling, Interruption Handling, Retries, Context TTL Expiration, Memory Separation,
Security Validation, and Real-World Multi-Turn Test Scenarios (1-4).
"""

import pytest
import time
from brain.context import get_context_manager, LIAContextManager
from brain.reference_resolver import ReferenceResolver
from brain.orchestrator import LIAOrchestrator, IntentType


@pytest.fixture(autouse=True)
def reset_context():
    """Resets the singleton context manager before each test."""
    ctx = get_context_manager()
    ctx.clear_all()
    yield ctx


@pytest.mark.asyncio
async def test_basic_context_tracking(reset_context):
    ctx = reset_context
    ctx.add_turn("user", "Hello LIA")
    ctx.add_turn("assistant", "Hello! How can I assist you today?")
    
    recent = ctx.get_recent_turns(5)
    assert len(recent) == 2
    assert recent[0]["role"] == "user"
    assert recent[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_pronoun_and_demonstrative_resolution(reset_context):
    ctx = reset_context
    resolver = ReferenceResolver(ctx)

    # Person resolution
    ctx.set_person_context(name="Arun")
    res_person = resolver.resolve("Tell him I'll call later")
    assert res_person["person_target"] == "Arun"
    assert "Arun" in res_person["resolved_prompt"]

    # Media resolution
    ctx.set_media_context(title="Enodu Nee Irundhaal", status="playing")
    res_media = resolver.resolve("Make it louder")
    assert res_media["resolved_entity"] == "Enodu Nee Irundhaal"

    # Browser article resolution
    ctx.current_browser["selected_result"] = "AI Multimodal Breakthroughs 2026"
    res_browser = resolver.resolve("Summarize it")
    assert res_browser["resolved_entity"] == "AI Multimodal Breakthroughs 2026"


@pytest.mark.asyncio
async def test_ordinal_resolution(reset_context):
    ctx = reset_context
    resolver = ReferenceResolver(ctx)

    results = [
        {"title": "Result 1: AI News Today"},
        {"title": "Result 2: Future of Generative Models"},
        {"title": "Result 3: Quantum Machine Learning"}
    ]
    ctx.set_active_task(name="news_search", query="AI news", results=results)

    # First one
    res1 = resolver.resolve("Open the first result")
    assert res1["selected_index"] == 0
    assert res1["resolved_entity"]["title"] == "Result 1: AI News Today"

    # Second one
    res2 = resolver.resolve("Open the second one")
    assert res2["selected_index"] == 1
    assert res2["resolved_entity"]["title"] == "Result 2: Future of Generative Models"

    # Last one
    res3 = resolver.resolve("Open the last one")
    assert res3["selected_index"] == -1
    assert res3["resolved_entity"]["title"] == "Result 3: Quantum Machine Learning"


@pytest.mark.asyncio
async def test_correction_handling(reset_context):
    ctx = reset_context
    resolver = ReferenceResolver(ctx)

    results = ["Option A", "Option B", "Option C"]
    ctx.set_active_task(name="options", query="test", results=results)

    res = resolver.resolve("No, the second one")
    assert res["is_correction"] is True
    assert res["selected_index"] == 1
    assert res["resolved_entity"] == "Option B"


@pytest.mark.asyncio
async def test_retry_context(reset_context):
    ctx = reset_context
    resolver = ReferenceResolver(ctx)

    ctx.set_last_error(tool="web_search", message="Network Timeout", step_text="search recent AI news")

    res = resolver.resolve("LIA, try again")
    assert res["is_retry"] is True
    assert res["resolved_prompt"] == "search recent AI news"


@pytest.mark.asyncio
async def test_device_context(reset_context):
    ctx = reset_context
    resolver = ReferenceResolver(ctx)

    res_desk = resolver.resolve("Open Chrome on my laptop")
    assert res_desk["device_target"] == "desktop"

    res_mob = resolver.resolve("What is my phone battery?")
    assert res_mob["device_target"] == "mobile"


@pytest.mark.asyncio
async def test_language_context(reset_context):
    ctx = reset_context
    ctx.add_turn("user", "What's today's AI news?")
    assert ctx.current_language == "English"

    ctx.add_turn("user", "Idha Tamil la sollu")
    assert ctx.current_language in ["Tamil", "Tanglish"]


@pytest.mark.asyncio
async def test_context_expiration(reset_context):
    ctx = reset_context
    ctx.ttl_seconds = 0.1  # Short TTL for test
    ctx.set_active_task(name="active_search", query="test", results=["a", "b"])

    time.sleep(0.15)
    ctx.check_expiration()

    assert ctx.active_task["name"] == "none"
    assert len(ctx.active_task["results"]) == 0


@pytest.mark.asyncio
async def test_memory_vs_context_separation(reset_context):
    ctx = reset_context
    orchestrator = LIAOrchestrator()

    # Short term context
    await orchestrator.process_request("Open YouTube")
    assert ctx.current_application == "YouTube"

    # Memory storage
    mem_res = await orchestrator.process_request("Remember that my preferred language is Tamil")
    assert mem_res["status"] == "success"
    # Verify passwords / credentials are not in context summary
    summary = ctx.get_summary()
    assert "password" not in json_safe_str(summary)


def json_safe_str(obj):
    return str(obj).lower()


# =====================================================================
# REAL-WORLD MULTI-TURN CONVERSATION SCENARIOS (TEST 1 - TEST 4)
# =====================================================================

@pytest.mark.asyncio
async def test_real_world_scenario_1(reset_context):
    """
    TEST 1:
    1. "LIA, open Google."
    2. "Search today's AI news."
    3. "Open the second result."
    4. "Summarize it."
    5. "Tell me the important point."
    """
    orchestrator = LIAOrchestrator()

    step1 = await orchestrator.process_request("LIA, open Google.")
    assert step1["status"] == "success"

    step2 = await orchestrator.process_request("Search today's AI news.")
    assert step2["status"] == "success"
    assert len(step2["search_results"]) > 0

    step3 = await orchestrator.process_request("Open the second result.")
    assert step3["status"] == "success"
    assert "result #2" in step3["message"].lower() or "opened" in step3["message"].lower()

    step4 = await orchestrator.process_request("Summarize it.")
    assert step4["status"] == "success"
    assert "Summary & Key Points" in step4["message"]

    step5 = await orchestrator.process_request("Tell me the important point.")
    assert step5["status"] == "success"
    assert "Summary & Key Points" in step5["message"]


@pytest.mark.asyncio
async def test_real_world_scenario_2(reset_context):
    """
    TEST 2:
    1. "LIA, open YouTube."
    2. "Search Tamil songs."
    3. "Play the second one."
    4. "Make it louder."
    5. "Pause."
    """
    orchestrator = LIAOrchestrator()

    step1 = await orchestrator.process_request("LIA, open YouTube.")
    assert step1["status"] == "success"
    assert reset_context.current_application == "YouTube"

    step2 = await orchestrator.process_request("Search Tamil songs.")
    assert step2["status"] == "success"

    step3 = await orchestrator.process_request("Play the second one.")
    assert step3["status"] == "success"
    assert "Playing" in step3["message"]

    step4 = await orchestrator.process_request("Make it louder.")
    assert step4["status"] == "success"
    assert "volume" in step4["message"].lower()

    step5 = await orchestrator.process_request("Pause.")
    assert step5["status"] == "success"
    assert "Paused" in step5["message"]


@pytest.mark.asyncio
async def test_real_world_scenario_3(reset_context):
    """
    TEST 3:
    1. "LIA, check my phone battery."
    2. "What about my computer?"
    """
    orchestrator = LIAOrchestrator()

    step1 = await orchestrator.process_request("LIA, check my phone battery.")
    assert step1["status"] == "success"
    assert "phone battery" in step1["message"].lower()

    step2 = await orchestrator.process_request("What about my computer?")
    assert step2["status"] == "success"
    assert "desktop" in step2["message"].lower() or "computer" in step2["message"].lower()


@pytest.mark.asyncio
async def test_real_world_scenario_4_person_context_and_security(reset_context):
    """
    TEST 4:
    1. "LIA, open WhatsApp."
    2. "Message Arun."
    3. "Tell him I'll call later."
    VERIFY: Does NOT send message automatically; prepares message and applies safety confirmation guard.
    """
    orchestrator = LIAOrchestrator()

    step1 = await orchestrator.process_request("LIA, open WhatsApp.")
    assert step1["status"] == "success"

    step2 = await orchestrator.process_request("Message Arun.")
    assert step2["status"] == "success"
    assert reset_context.current_person["name"] == "Arun"

    step3 = await orchestrator.process_request("Tell him I'll call later.")
    assert step3["status"] == "success"
    assert step3.get("requires_confirmation") is True
    assert "Safety Confirmation Required" in step3["message"]
    assert "Arun" in step3["message"]
    assert "I'll call later" in step3["message"]
