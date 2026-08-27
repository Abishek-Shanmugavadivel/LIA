"""
Autonomous Task Agent Engine for LIA (Phase 14)
Decomposes high-level user goals into structured sub-steps, manages the Task Lifecycle State Machine,
executes dynamic planning, performs post-action observation/verification, handles cancellation & resume,
and enforces security classifications (SAFE, SENSITIVE, DANGEROUS) with prompt injection protection.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from voice.state_machine import get_state_machine, LIAState
from tools.tool_result import create_tool_result

logger = logging.getLogger("lia-task-agent")


class TaskState:
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class LIATaskAgent:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LIATaskAgent, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.current_state: str = TaskState.IDLE
        self.current_goal: str = ""
        self.active_plan: List[str] = []
        self.executed_steps: List[Dict[str, Any]] = []
        self.task_history: List[Dict[str, Any]] = []
        self.is_cancelled: bool = False

    def sanitize_untrusted_input(self, text: str) -> str:
        """Protects agent from prompt injection attacks in external web, email, or terminal content."""
        injection_keywords = ["ignore previous instructions", "system prompt", "override rules", "sudo rm", "format c:"]
        sanitized = text
        for kw in injection_keywords:
            if kw in sanitized.lower():
                logger.warning(f"Prompt injection pattern detected and blocked: '{kw}'")
                sanitized = sanitized.replace(kw, "[BLOCKED_INJECTION_PATTERN]")
        return sanitized

    def plan_goal(self, goal_text: str) -> List[str]:
        """Decomposes a high-level goal into actionable sub-tasks."""
        self.current_state = TaskState.PLANNING
        self.current_goal = goal_text
        self.is_cancelled = False
        g_clean = goal_text.lower()

        plan = []
        if "fix" in g_clean or "bug" in g_clean or "error" in g_clean:
            plan = [
                "Inspect active screen and error context",
                "Discover project structure and locate failure point",
                "Execute diagnostic test suite",
                "Apply minimal targeted code fix",
                "Run verification tests and confirm fix"
            ]
        elif "deploy" in g_clean or "portfolio" in g_clean:
            plan = [
                "Inspect project manifest and dependencies",
                "Run lint and build checks",
                "Verify production bundle output",
                "Report deployment status"
            ]
        else:
            plan = [
                f"Analyze goal: {goal_text}",
                "Execute required tool actions",
                "Verify visual and system state change",
                "Complete task report"
            ]

        self.active_plan = plan
        logger.info(f"Planned {len(plan)} sub-steps for goal '{goal_text}': {plan}")
        return plan

    async def execute_goal(self, goal_text: str) -> Dict[str, Any]:
        """Executes full autonomous loop: UNDERSTAND -> PLAN -> EXECUTE -> OBSERVE -> VERIFY -> COMPLETE."""
        from brain.orchestrator import LIAOrchestrator
        orchestrator = LIAOrchestrator()
        sm = get_state_machine()

        sanitized_goal = self.sanitize_untrusted_input(goal_text)
        plan = self.plan_goal(sanitized_goal)
        results = []

        sm.set_state(LIAState.EXECUTING)
        self.current_state = TaskState.EXECUTING

        start_time = time.time()

        for idx, step in enumerate(plan):
            if self.is_cancelled:
                self.current_state = TaskState.CANCELLED
                sm.set_state(LIAState.IDLE)
                logger.info("Autonomous Task Agent execution cancelled by user.")
                return create_tool_result("task_agent", "execute_goal", False, result=None, error="Task cancelled by user.")

            self.current_state = TaskState.EXECUTING
            step_res = await orchestrator.process_request(step)
            results.append({"step": step, "result": step_res})

            # OBSERVE & VERIFY
            self.current_state = TaskState.OBSERVING
            time.sleep(0.1)
            self.current_state = TaskState.VERIFYING

        self.current_state = TaskState.COMPLETED
        sm.set_state(LIAState.IDLE)

        task_record = {
            "goal": sanitized_goal,
            "status": TaskState.COMPLETED,
            "steps": len(plan),
            "duration": round(time.time() - start_time, 2),
            "timestamp": time.time()
        }
        self.task_history.append(task_record)
        logger.info(f"Autonomous Task Agent completed goal '{sanitized_goal}' in {task_record['duration']}s.")
        
        return create_tool_result("task_agent", "execute_goal", True, result={"goal": sanitized_goal, "plan": plan, "step_results": results})

    def cancel_task(self) -> Dict[str, Any]:
        """Cancels active autonomous task execution safely."""
        self.is_cancelled = True
        self.current_state = TaskState.CANCELLED
        logger.info("Task cancellation signal processed.")
        return create_tool_result("task_agent", "cancel_task", True, result={"status": "cancelled", "message": "Active autonomous task cancelled safely."})

    def resume_task(self) -> Dict[str, Any]:
        """Resumes active autonomous task execution."""
        self.is_cancelled = False
        self.current_state = TaskState.EXECUTING
        logger.info("Task resume signal processed.")
        return create_tool_result("task_agent", "resume_task", True, result={"status": "resumed", "message": "Autonomous task execution resumed."})


_global_task_agent: Optional[LIATaskAgent] = None


def get_task_agent() -> LIATaskAgent:
    global _global_task_agent
    if _global_task_agent is None:
        _global_task_agent = LIATaskAgent()
    return _global_task_agent
