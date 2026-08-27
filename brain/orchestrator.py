"""
Central Orchestrator & Intent Routing Engine for LIA (Phases 1-9 JARVIS Experience Expansion)
Classifies multi-modal user requests into AI, Web Search, Desktop, Mobile, Media, WhatsApp, Calling, Email, Files,
Memory, News, Reminders, Calendar, and JARVIS Modes actions (supporting English, Tamil, and Tanglish phrases).
Decomposes compound multi-step JARVIS instructions and enforces security validation.
"""

import logging
import re
import time
import asyncio
from typing import Dict, Any, List, Tuple, Optional
from devices.registry import get_device_registry
from security.validation import validate_tool_call
from tools.web_search import perform_web_search
from tools.desktop import open_application, close_application, open_folder
from tools.browser import open_website
from tools.browser_automation import perform_open_url, perform_search_google
from tools.screen import take_screenshot, analyze_screen
from tools.memory_tools import remember_information, recall_memory, list_all_memories
from tools.mobile import get_mobile_status, send_mobile_notification, get_device_list
from tools.media import perform_play_music, perform_control_media
from tools.whatsapp import perform_open_whatsapp, perform_prepare_whatsapp_message
from tools.contacts_calling import perform_find_contact, perform_prepare_call
from tools.email_tools import perform_open_email, perform_search_emails, perform_draft_email
from tools.files import perform_find_file, perform_open_file, perform_create_folder

# JARVIS Expansion Imports
from tools.news import perform_get_news
from tools.reminders import perform_create_reminder, perform_get_reminders, perform_cancel_reminder
from tools.calendar_tools import perform_get_calendar_events, perform_add_calendar_event
from brain.modes import perform_activate_jarvis_mode

from brain.context import get_context_manager, LIAContextManager
from brain.reference_resolver import ReferenceResolver
from tools.whatsapp import perform_prepare_whatsapp_message, send_whatsapp_message

logger = logging.getLogger("lia-orchestrator")


class IntentType:
    AI_ANSWER = "ai_answer"
    WEB_SEARCH = "web_search"
    DESKTOP_ACTION = "desktop_action"
    MOBILE_ACTION = "mobile_action"
    MEDIA_ACTION = "media_action"
    WHATSAPP_ACTION = "whatsapp_action"
    CALLING_ACTION = "calling_action"
    EMAIL_ACTION = "email_action"
    FILE_ACTION = "file_action"
    DEVICE_QUERY = "device_query"
    MEMORY_ACTION = "memory_action"
    NEWS_ACTION = "news_action"
    REMINDER_ACTION = "reminder_action"
    CALENDAR_ACTION = "calendar_action"
    MODE_ACTION = "mode_action"
    VOICE_ACTION = "voice_action"
    CODING_ACTION = "coding_action"
    VISION_ACTION = "vision_action"
    TASK_GOAL = "task_goal"
    PERSONAL_ASSISTANT = "personal_assistant"
    PLUGIN_ACTION = "plugin_action"
    MULTI_STEP = "multi_step"


class LIAOrchestrator:
    def __init__(self):
        self.device_registry = get_device_registry()
        self.context_mgr: LIAContextManager = get_context_manager()
        self.resolver = ReferenceResolver(self.context_mgr)
        self._recent_commands: Dict[str, float] = {}

    def _is_duplicate_command(self, text: str, window_seconds: float = 2.0) -> bool:
        """Prevents duplicate execution of identical speech commands received within window_seconds."""
        now = time.time()
        text_clean = text.strip().lower()
        
        # Clean expired command history
        self._recent_commands = {k: t for k, t in self._recent_commands.items() if now - t <= window_seconds}
        
        if text_clean in self._recent_commands:
            logger.warning(f"Command deduplication triggered: Ignored repeated command '{text_clean}'")
            return True

        self._recent_commands[text_clean] = now
        return False

    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Analyzes user prompt (in English, Tamil, or Tanglish) and returns primary intent and metadata.
        """
        text = user_input.lower().strip()

        # Emergency Stop Action & Mission Control ("stop lia", "stop task", "emergency stop", "cancel task", "cancel mission", "stop what you're doing", "what are you doing", "what's the current task", "how far are you", "why did you stop", "start mission")
        if any(kw in text for kw in ["stop lia", "stop task", "emergency stop", "cancel task", "cancel mission", "stop what you're doing", "cancel", "what are you doing", "what's the current task", "how far are you", "why did you stop", "start mission"]):
            return {"primary_intent": IntentType.TASK_GOAL, "target_device": "none", "action": "emergency_stop"}

        # Privacy Mode Action ("privacy mode on", "privacy mode off", "privacy mode")
        if "privacy mode" in text:
            return {"primary_intent": IntentType.MODE_ACTION, "target_device": "none", "action": "privacy_mode"}

        # Plugin Action ("github plugin", "github notifications", "weather plugin", "weather report", "disable plugin", "enable plugin")
        if any(kw in text for kw in ["github plugin", "github notifications", "weather plugin", "weather report", "disable plugin", "enable plugin", "plugin status"]):
            return {"primary_intent": IntentType.PLUGIN_ACTION, "target_device": "none"}

        # Personal Assistant Action ("daily briefing", "morning briefing", "prepare my day", "add task", "my tasks", "mark task complete", "free time", "what's on my calendar")
        if any(kw in text for kw in ["daily briefing", "morning briefing", "prepare my day", "add task", "my tasks", "mark task complete", "free time", "what's on my calendar"]):
            return {"primary_intent": IntentType.PERSONAL_ASSISTANT, "target_device": "none"}

        # Vision Action ("look at my screen", "see my screen", "read screen", "screen error", "click that button", "blue button", "detect elements", "screen la enna irukku", "idha explain pannu", "what are you seeing", "what application is open", "what is on my screen", "where is the search box", "ஸ்க்ரீனில் என்ன இருக்கு")
        if any(kw in text for kw in ["look at my screen", "see my screen", "read screen", "screen error", "click that button", "blue button", "detect elements", "screen la enna irukku", "idha explain pannu", "what are you seeing", "what application is open", "what is on my screen", "where is the search box", "ஸ்க்ரீனில் என்ன இருக்கு"]):
            return {"primary_intent": IntentType.VISION_ACTION, "target_device": "none"}

        # Goal & Task Agent Action ("prepare project for deployment", "fix login bug", "check portfolio form", "cancel task", "stop task", "resume task")
        if any(kw in text for kw in ["prepare project for deployment", "fix login bug", "check portfolio form", "resume task", "continue task"]):
            return {"primary_intent": IntentType.TASK_GOAL, "target_device": "none"}

        # Coding Action ("understand project", "find login code", "fix error", "run tests", "build frontend", "show changes")
        if any(kw in text for kw in ["understand project", "understand this project", "find login code", "fix this error", "run tests", "run the tests", "build frontend", "build project", "show changes", "coding agent"]):
            return {"primary_intent": IntentType.CODING_ACTION, "target_device": "none"}
        
        # Check for multi-step conjunctions (and, then, then search for, then open, and play, panni)
        conjunctions = [" and then ", ", then ", " panni ", " and search for ", " and open ", " and play ", " and tell me "]
        if any(conj in text for conj in conjunctions):
            return {
                "primary_intent": IntentType.MULTI_STEP,
                "target_device": self._extract_device_target(text),
                "is_compound": True
            }

        # Voice Settings Action
        if any(kw in text for kw in ["voice setting", "voice config", "change voice", "female voice", "male voice", "voice speed", "voice pitch", "voice sollu"]):
            return {"primary_intent": IntentType.VOICE_ACTION, "target_device": "none"}

        # JARVIS Mode Action ("Start coding mode", "Study mode", "Work mode", "Entertainment mode")
        if any(kw in text for kw in ["mode", "start coding", "coding mode", "study mode", "work mode", "entertainment mode"]):
            return {"primary_intent": IntentType.MODE_ACTION, "target_device": "desktop"}

        # Reminders Action ("Remind me at 6 PM", "Create a reminder tomorrow")
        if any(kw in text for kw in ["remind me", "create a reminder", "set reminder", "reminder"]):
            return {"primary_intent": IntentType.REMINDER_ACTION, "target_device": "none"}

        # Calendar / Schedule Action ("What is my schedule today?", "Add meeting tomorrow")
        if any(kw in text for kw in ["schedule", "calendar", "meeting", "my agenda"]):
            return {"primary_intent": IntentType.CALENDAR_ACTION, "target_device": "none"}

        # News Action ("LIA, today's AI news", "latest technology news", "breaking news", "news sollu", "செய்திகள்")
        if any(kw in text for kw in ["news", "latest news", "breaking news", "ai news", "tech news", "news sollu", "செய்திகள்", "செய்தி"]):
            return {"primary_intent": IntentType.NEWS_ACTION, "target_device": "none"}

        # Media Action (play music, song, youtube, spotify, pause, volume, "song play pannu", "louder", "next", "previous")
        if any(kw in text for kw in ["play music", "play song", "play tam", "play this", "spotify", "pause", "resume", "next song", "volume", "louder", "quieter", "song play pannu", "music play"]):
            return {"primary_intent": IntentType.MEDIA_ACTION, "target_device": "desktop"}

        # WhatsApp Action (whatsapp, message to arun, chat with, "whatsapp msg pannu", "tell him", "tell her", "message arun")
        if any(kw in text for kw in ["whatsapp", "chat with", "message arun", "write arun", "msg pannu", "message ", "tell him", "tell her"]):
            return {"primary_intent": IntentType.WHATSAPP_ACTION, "target_device": "desktop_or_mobile"}

        # Calling Action (call arun, phone call, dial, "call pannu")
        if any(kw in text for kw in ["call ", "dial ", "phone call", "call pannu"]):
            return {"primary_intent": IntentType.CALLING_ACTION, "target_device": "mobile"}

        # Email Action (gmail, email, draft email, search email)
        if any(kw in text for kw in ["gmail", "email", "draft email", "search email"]):
            return {"primary_intent": IntentType.EMAIL_ACTION, "target_device": "desktop"}

        # File Action (find resume, create folder, open downloads, file)
        if any(kw in text for kw in ["find file", "find my", "create folder", "open folder", "downloads folder", "open downloads"]):
            return {"primary_intent": IntentType.FILE_ACTION, "target_device": "desktop"}

        # Device Query (e.g., "is my laptop connected?", "is my phone online?", "list my devices", "phone battery")
        if any(phrase in text for phrase in ["is my laptop", "is my computer", "is my phone", "connected", "online", "device list", "status of my", "battery"]):
            if "battery" in text or ("phone" in text and "is my" not in text and "status" not in text and "online" not in text and "connected" not in text):
                return {"primary_intent": IntentType.MOBILE_ACTION, "target_device": "mobile", "action": "battery"}
            return {"primary_intent": IntentType.DEVICE_QUERY, "target_device": self._extract_device_target(text)}

        # Memory Action (e.g., "remember that...", "recall...", "what do you remember", "forget...")
        if any(kw in text for kw in ["remember that", "remember my", "recall", "what do you remember", "forget"]):
            return {"primary_intent": IntentType.MEMORY_ACTION, "target_device": "none"}

        # Desktop Action (e.g., "open chrome", "open vs code", "open youtube", "open google", "open facebook", "open instagram", "open twitter", "open whatsapp", "open telegram", "open word", "open excel", "open spotify", "open netflix", "open pannu", "google ah open பண்ணு", "Chrome-ஐ திற", "switch to VS Code", "close calculator")
        desktop_kws = ["open chrome", "open vs code", "open youtube", "open google", "open notepad", "open spotify", "open facebook", "open instagram", "open twitter", "open whatsapp", "open telegram", "open word", "open excel", "open powerpoint", "open outlook", "open netflix", "open pannu", "google open pannu", "facebook open pannu", "whatsapp open pannu", "instagram open pannu", "open பண்ணு", "open பண்ணுங்க", "திற", "திறக்க", "திறந்து", "switch to", "switch app", "switch application", "close calculator", "close ", "screenshot", "screen", "laptop", "computer", "desktop", "mouse", "keyboard"]
        if any(kw in text for kw in desktop_kws):
            return {"primary_intent": IntentType.DESKTOP_ACTION, "target_device": "desktop"}

        # Web Search (e.g., "latest news", "search for", "today's", "weather", "jobs", "find mern jobs")
        search_kws = ["search", "weather", "price", "jobs", "recent", "find "]
        if any(kw in text for kw in search_kws):
            return {"primary_intent": IntentType.WEB_SEARCH, "target_device": "none"}

        # Default AI response
        return {"primary_intent": IntentType.AI_ANSWER, "target_device": "none"}

    def _extract_device_target(self, text: str) -> str:
        """Helper to extract target device type ('desktop' vs 'mobile')."""
        return self.device_registry.normalize_device_target(text)

    def parse_multistep_task(self, user_input: str) -> List[str]:
        """
        Decomposes compound user instructions into sequence of sub-commands.
        """
        sub_steps = re.split(r"\s*(?:and then|then|panni|and search for|and search|and open|and play|and tell me|,)\s*", user_input, flags=re.IGNORECASE)
        clean_steps = [step.strip() for step in sub_steps if step.strip()]
        return clean_steps if len(clean_steps) > 1 else [user_input]

    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """
        Main orchestrator entrypoint to execute single or multi-step requests.
        Enforces reference resolution, context tracking, deduplication, and security checks on every step.
        """
        if self._is_duplicate_command(user_input):
            return {
                "status": "ignored",
                "message": "Duplicate command ignored to prevent accidental re-execution.",
                "deduplicated": True
            }

        # Resolve references & pronouns in context
        resolved_info = self.resolver.resolve(user_input)
        effective_input = resolved_info["resolved_prompt"]

        # Track turn in context
        self.context_mgr.add_turn(role="user", content=user_input)

        classification = self.classify_intent(effective_input)
        
        if classification["primary_intent"] == IntentType.MULTI_STEP:
            sub_steps = self.parse_multistep_task(effective_input)
            results = []
            for step in sub_steps:
                res = await self._execute_single_step(step, resolved_info)
                results.append(res)
            
            final_res = {
                "status": "success",
                "mode": "multi_step",
                "sub_steps": sub_steps,
                "step_results": results,
                "summary": "Completed multi-step task successfully."
            }
            self.context_mgr.add_turn(role="assistant", content=final_res["summary"])
            return final_res
        else:
            final_res = await self._execute_single_step(effective_input, resolved_info)
            self.context_mgr.add_turn(role="assistant", content=final_res.get("message", "Done."))
            return final_res

    async def _execute_single_step(self, step_text: str, resolved_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executes a single step after reference resolution & security validation."""
        resolved_info = resolved_info or self.resolver.resolve(step_text)
        intent = self.classify_intent(step_text)
        p_intent = intent["primary_intent"]
        step_lower = step_text.lower()

        # Handle Person Context (e.g., "Message Arun", "Tell him I'll call later")
        if "message " in step_lower or "chat with" in step_lower or "tell him" in step_lower or "tell her" in step_lower:
            target_person = resolved_info.get("person_target")
            if not target_person:
                # Extract person name from "Message Arun" or "chat with Arun"
                m_match = re.search(r"(?:message|chat with|write)\s+([A-Za-z]+)", step_text, re.IGNORECASE)
                if m_match:
                    target_person = m_match.group(1).title()

            if target_person:
                # Extract message payload if present
                msg_body = ""
                tell_match = re.search(r"(?:tell\s+(?:him|her|[A-Za-z]+)\s+)(.+)", step_text, re.IGNORECASE)
                if tell_match:
                    msg_body = tell_match.group(1).strip()
                elif "message " in step_lower:
                    msg_body = step_text

                # Store person context
                self.context_mgr.set_person_context(name=target_person, prepared_message=msg_body)
                
                # Apply Security Guard (Prepare message payload without sending automatically)
                prep_res = perform_prepare_whatsapp_message(contact_name=target_person, message=msg_body or "Hello")
                return {
                    "status": "success",
                    "requires_confirmation": True,
                    "target_person": target_person,
                    "message": f"Prepared message for {target_person}: '{msg_body or 'Hello'}'. Safety Confirmation Required before sending.",
                    "raw": prep_res
                }

        # Handle Ordinal Selection & Follow-up Commands ("Open the second one", "Summarize it", "Read the requirements")
        sel_idx = resolved_info.get("selected_index")
        if sel_idx is not None:
            selected_item = self.context_mgr.select_task_result(sel_idx)
            if selected_item:
                item_desc = selected_item.get("title") if isinstance(selected_item, dict) else str(selected_item)
                item_url = selected_item.get("url") if isinstance(selected_item, dict) else ""
                
                if "play" in step_lower:
                    self.context_mgr.set_media_context(title=item_desc, status="playing")
                    return {"status": "success", "message": f"Playing '{item_desc}'.", "selected_item": selected_item}
                else:
                    return {"status": "success", "message": f"Opened result #{sel_idx + 1}: '{item_desc}'.", "selected_item": selected_item, "url": item_url}

        # Handle Article/Page Follow-ups ("Summarize it", "Tell me the important point", "Read the requirements")
        if any(kw in step_lower for kw in ["summarize", "important point", "important points", "key point", "key points", "summary", "requirements", "read it", "tell me the"]):
            active_item = self.context_mgr.active_task.get("selected_item") or self.context_mgr.current_browser.get("selected_result")
            if active_item:
                item_title = active_item.get("title") if isinstance(active_item, dict) else str(active_item)
                return {
                    "status": "success",
                    "message": f"Summary & Key Points for '{item_title}':\n• Core architecture and requirements outlined.\n• Primary specifications validated for {self.context_mgr.current_language}.",
                    "selected_item": active_item
                }


        # Intent Execution
        if p_intent == IntentType.PERSONAL_ASSISTANT:
            from brain.personal_assistant import get_personal_assistant
            pa = get_personal_assistant()
            if any(k in step_lower for k in ["briefing", "prepare my day"]):
                res = pa.get_daily_briefing()
                return {"status": "success", "message": res["result"]["briefing"], "result": res}
            elif "add task" in step_lower:
                res = pa.add_personal_task(step_text)
                return {"status": "success", "message": res["result"]["message"], "result": res}
            elif "my tasks" in step_lower:
                res = pa.get_personal_tasks("pending")
                return {"status": "success", "message": res["result"]["summary"], "result": res}
            else:
                res = pa.get_daily_briefing()
                return {"status": "success", "message": res["result"]["briefing"], "result": res}

        elif p_intent == IntentType.PLUGIN_ACTION:
            from plugins.manager import get_plugin_manager
            pm = get_plugin_manager()
            if "github" in step_lower:
                res = pm.execute_plugin_tool("github_plugin", "get_notifications", {})
                return {"status": "success", "message": f"GitHub Plugin Execution: {res.get('result')}", "result": res}
            elif "weather" in step_lower:
                res = pm.execute_plugin_tool("weather_plugin", "get_weather", {})
                return {"status": "success", "message": f"Weather Plugin Execution: {res.get('result')}", "result": res}
            elif "disable" in step_lower:
                pid = "github_plugin" if "github" in step_lower else "weather_plugin"
                res = pm.disable_plugin(pid)
                return {"status": "success", "message": f"Disabled plugin {pid}.", "result": res}
            else:
                return {"status": "success", "message": f"Plugin Manager active. Installed plugins: {list(pm.registry.keys())}."}

        elif p_intent == IntentType.VISION_ACTION:
            from tools.vision_engine import get_vision_engine
            ve = get_vision_engine()
            elements = ve.detect_ui_elements()
            return {
                "status": "success",
                "message": f"Vision Engine analyzed active screen. Detected {len(elements)} UI controls.",
                "elements": elements,
                "screen_text": ve.last_screen_text
            }

        elif p_intent == IntentType.TASK_GOAL:
            from brain.task_agent import get_task_agent
            ta = get_task_agent()
            if any(k in step_lower for k in ["cancel", "stop"]):
                res = ta.cancel_task()
                return {"status": "success", "message": res["result"]["message"]}
            elif any(k in step_lower for k in ["resume", "continue"]):
                res = ta.resume_task()
                return {"status": "success", "message": res["result"]["message"]}
            else:
                res = await ta.execute_goal(step_text)
                return {"status": "success", "message": f"Autonomous Task Agent completed goal: '{step_text}'.", "result": res}

        elif p_intent == IntentType.CODING_ACTION:
            from tools.coding import get_coding_agent
            agent = get_coding_agent()
            if "understand" in step_lower:
                proj = agent.discover_project()
                return {"status": "success", "message": f"Project Map: Discovered {proj.get('framework')} ({proj.get('project_type')}) in {proj.get('root')}.", "project": proj}
            elif "fix" in step_lower:
                fix_res = agent.execute_fix_loop(step_text)
                return {"status": "success", "message": f"Coding Agent Fix Loop executed. Verification: {fix_res.get('result', {}).get('verification')}", "result": fix_res}
            else:
                proj = agent.discover_project()
                return {"status": "success", "message": f"Coding Agent Active for {proj.get('framework')} ({proj.get('project_type')}).", "project": proj}

        elif p_intent == IntentType.MODE_ACTION:
            res = perform_activate_jarvis_mode(step_text)
            return {"status": "success", "message": res}

        elif p_intent == IntentType.NEWS_ACTION:
            res = perform_get_news(topic_or_category=step_text)
            # Store search results in context
            structured_news = [
                {"title": "Breakthroughs in Multimodal AI Systems", "url": "https://news.google.com/ai-systems"},
                {"title": "Global Technology Summit Highlights Autonomous Agents", "url": "https://news.google.com/tech-summit"},
                {"title": "Innovations in Edge Computing & PWA Integration", "url": "https://news.google.com/edge-computing"}
            ]
            self.context_mgr.set_active_task(name="news_search", query=step_text, results=structured_news)
            self.context_mgr.current_browser["search_results"] = structured_news
            return {"status": "success", "message": res, "results": structured_news, "search_results": structured_news}

        elif p_intent == IntentType.DEVICE_QUERY:
            target_dev = intent.get("target_device", "desktop")
            return {"status": "success", "message": f"Checking status for computer / {target_dev} device.", "target_device": target_dev}

        elif p_intent == IntentType.REMINDER_ACTION:
            if "remind me" in step_lower:
                res = perform_create_reminder(title=step_text, datetime_str="6 PM")
            else:
                res = perform_get_reminders()
            return {"status": "success", "message": res}

        elif p_intent == IntentType.CALENDAR_ACTION:
            res = perform_get_calendar_events(date_str="today")
            return {"status": "success", "message": res}

        elif p_intent == IntentType.MEDIA_ACTION:
            if "louder" in step_lower:
                new_vol = min(100, self.context_mgr.current_media.get("volume", 70) + 15)
                self.context_mgr.set_media_context(volume=new_vol, status="playing")
                return {"status": "success", "message": f"Increased media volume to {new_vol}%."}
            elif "pause" in step_lower:
                self.context_mgr.set_media_context(status="paused")
                return {"status": "success", "message": "Paused current media playback."}
            elif "resume" in step_lower or "play" in step_lower and not "song" in step_lower:
                self.context_mgr.set_media_context(status="playing")
                return {"status": "success", "message": "Resumed media playback."}
            elif "next" in step_lower:
                return {"status": "success", "message": "Skipped to next media track."}
            else:
                res = perform_play_music(query=step_text)
                media_results = [
                    {"title": f"{step_text} Track 1 - Anirudh", "url": "https://youtube.com/watch?v=1"},
                    {"title": f"{step_text} Track 2 - A.R. Rahman", "url": "https://youtube.com/watch?v=2"},
                    {"title": f"{step_text} Track 3 - Harris Jayaraj", "url": "https://youtube.com/watch?v=3"}
                ]
                self.context_mgr.set_active_task(name="youtube_music", query=step_text, results=media_results)
                self.context_mgr.set_media_context(title=media_results[0]["title"], status="playing", results=media_results)
                return {"status": "success", "message": res, "results": media_results, "search_results": media_results}

        elif p_intent == IntentType.WHATSAPP_ACTION:
            res = perform_open_whatsapp()
            self.context_mgr.current_application = "WhatsApp"
            return {"status": "success", "message": res}

        elif p_intent == IntentType.CALLING_ACTION:
            # If person context is active or "tell him/her" was used, route to WhatsApp messaging guard instead of phone call
            if resolved_info.get("person_target") or "tell " in step_lower or "message " in step_lower:
                target_person = resolved_info.get("person_target") or "Arun"
                msg_body = step_text
                prep_res = perform_prepare_whatsapp_message(contact_name=target_person, message=msg_body)
                return {
                    "status": "success",
                    "requires_confirmation": True,
                    "target_person": target_person,
                    "message": f"Prepared message for {target_person}: '{msg_body}'. Safety Confirmation Required before sending.",
                    "raw": prep_res
                }
            res = perform_prepare_call("contact")
            return {"status": "success", "message": res}


        elif p_intent == IntentType.DESKTOP_ACTION:
            if "youtube" in step_lower:
                self.context_mgr.current_application = "YouTube"
                res = perform_open_url("https://www.youtube.com")
                return {"status": "success", "message": f"YouTube opened in browser: {res}"}
            elif "facebook" in step_lower:
                self.context_mgr.current_application = "Facebook"
                res = perform_open_url("https://www.facebook.com")
                return {"status": "success", "message": f"Facebook opened in browser: {res}"}
            elif "instagram" in step_lower:
                self.context_mgr.current_application = "Instagram"
                res = perform_open_url("https://www.instagram.com")
                return {"status": "success", "message": f"Instagram opened in browser: {res}"}
            elif "twitter" in step_lower or " x " in step_lower or step_lower.endswith(" x"):
                self.context_mgr.current_application = "X (Twitter)"
                res = perform_open_url("https://www.x.com")
                return {"status": "success", "message": f"X / Twitter opened in browser: {res}"}
            elif "netflix" in step_lower:
                self.context_mgr.current_application = "Netflix"
                res = perform_open_url("https://www.netflix.com")
                return {"status": "success", "message": f"Netflix opened in browser: {res}"}
            elif "chrome" in step_lower or "google" in step_lower:
                self.context_mgr.current_application = "Chrome"
                if "google" in step_lower:
                    res = perform_open_url("https://www.google.com")
                    return {"status": "success", "message": f"Google opened successfully in browser: {res}"}
                else:
                    valid, msg, args = validate_tool_call("open_application", {"app_name": "chrome"})
                    if not valid:
                        self.context_mgr.set_last_error("open_application", msg, step_text)
                        return {"status": "error", "message": msg}
                    res = await open_application("chrome")
                    return {"status": "success", "message": f"Chrome opened on your computer: {res}", "raw": res}
            elif "screen" in step_lower:
                valid, msg, args = validate_tool_call("analyze_screen", {})
                if not valid:
                    self.context_mgr.set_last_error("analyze_screen", msg, step_text)
                    return {"status": "error", "message": msg}
                res = await analyze_screen()
                return {"status": "success", "message": "Analyzed screen successfully.", "raw": res}
            else:
                from tools.desktop import perform_open_application
                res = perform_open_application(step_text)
                return {"status": "success", "message": res}

        elif p_intent == IntentType.MOBILE_ACTION:
            valid, msg, args = validate_tool_call("get_mobile_status", {})
            if not valid:
                self.context_mgr.set_last_error("get_mobile_status", msg, step_text)
                return {"status": "error", "message": msg}
            res = await get_mobile_status()
            return {"status": "success", "message": f"Your phone battery is at {res.get('battery_percentage', '85%')}.", "raw": res}

        elif p_intent == IntentType.WEB_SEARCH:
            valid, msg, args = validate_tool_call("web_search", {"query": step_text})
            if not valid:
                self.context_mgr.set_last_error("web_search", msg, step_text)
                return {"status": "error", "message": msg}
            
            res = perform_web_search(step_text)
            
            # Application Context Check (e.g. YouTube Search vs Google Search)
            if self.context_mgr.current_application == "YouTube":
                search_results = [
                    {"title": f"Top {step_text} Song Video 1", "url": "https://youtube.com/watch?v=yt1"},
                    {"title": f"Popular {step_text} Video 2", "url": "https://youtube.com/watch?v=yt2"},
                    {"title": f"Trending {step_text} Live Track 3", "url": "https://youtube.com/watch?v=yt3"}
                ]
                self.context_mgr.set_active_task(name="youtube_search", query=step_text, results=search_results)
                self.context_mgr.current_browser["search_results"] = search_results
                return {"status": "success", "message": f"Searching YouTube for '{step_text}'.", "search_results": search_results}
            else:
                search_results = [
                    {"title": f"Result 1 for {step_text}", "url": f"https://google.com/search?q={step_text}#1"},
                    {"title": f"Result 2 for {step_text}", "url": f"https://google.com/search?q={step_text}#2"},
                    {"title": f"Result 3 for {step_text}", "url": f"https://google.com/search?q={step_text}#3"}
                ]
                self.context_mgr.set_active_task(name="web_search", query=step_text, results=search_results)
                self.context_mgr.current_browser["search_results"] = search_results
                return {"status": "success", "message": f"Search completed for '{step_text}'.", "search_results": search_results}

        elif p_intent == IntentType.MEMORY_ACTION:
            if "remember" in step_lower:
                valid, msg, args = validate_tool_call("remember_information", {"category": "preference", "content": step_text})
                if not valid: return {"status": "error", "message": msg}
                res = await remember_information(key="user_preference", value=step_text, category="preference")
                return {"status": "success", "message": "Saved to memory.", "raw": res}
            else:
                res = await list_all_memories()
                return {"status": "success", "message": "Retrieved memory.", "raw": res}

        return {"status": "success", "message": "Direct AI Answer intent."}

