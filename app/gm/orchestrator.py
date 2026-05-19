"""GM Orchestrator: turn loop connecting player input → LLM → tools → narration."""

from __future__ import annotations

import json
from typing import Any

from gm.bridge import GameBridge
from gm.openrouter import create_client, chat_completion
from gm.system_prompt import SYSTEM_PROMPT
from gm.tools import TOOLS
from gm.context import build_state_context, build_messages
from gm.logger import (
    log_player_input, log_gm_narration, log_tool_call,
    log_llm_request, log_llm_response, log_error,
)


class Orchestrator:
    """Manages the GM turn loop."""

    def __init__(self, config: dict):
        self.config = config
        llm_cfg = config.get("llm", {})
        self.model = llm_cfg.get("model", "anthropic/claude-sonnet-4")
        self.max_tokens = llm_cfg.get("max_tokens", 2048)
        self.temperature = llm_cfg.get("temperature", 0.8)

        self.client = create_client()
        self.bridge = GameBridge()
        self.history: list[dict[str, str]] = []
        self._last_content = ""

    def get_status(self) -> dict:
        return self.bridge.status()

    def setup_new_game(self, campaign_slug: str = "salt-road") -> dict:
        """Set up a new campaign + session for first play."""
        self.bridge.init()
        result = self.bridge.campaign_new(campaign_slug, campaign_slug.replace("-", " ").title())
        if not result.get("ok"):
            return result
        session = self.bridge.session_start(campaign_slug)
        return session

    def process_turn(self, player_input: str) -> str:
        """Process a player turn and return GM narration text."""
        log_player_input(player_input)

        lower = player_input.lower().strip()
        if lower in ("new game", "start", "new"):
            result = self.setup_new_game()
            if not result.get("ok"):
                log_error("setup_new_game", result.get("error", "unknown"))
                return f"Could not start game: {result.get('error', 'unknown')}"
            player_input = (
                "I just arrived. Describe where I am and what I see. "
                "Ask me about my character — name, class, background."
            )
        elif lower in ("continue", "resume"):
            result = self.bridge.session_resume()
            if not result.get("ok"):
                log_error("session_resume", result.get("error", "unknown"))
                return f"Could not resume: {result.get('error', 'unknown')}. Try 'new game' instead."
            player_input = "I'm back. Remind me where I was and what's happening."

        status = self.bridge.status()
        state_context = build_state_context(status)

        messages = build_messages(
            SYSTEM_PROMPT,
            state_context,
            self.history,
            player_input,
        )

        narration = self._llm_loop(messages)
        log_gm_narration(narration)

        self.history.append({"role": "user", "content": player_input})
        self.history.append({"role": "assistant", "content": narration})

        if len(self.history) > 40:
            self.history = self.history[-30:]

        return narration

    def _llm_loop(self, messages: list[dict[str, Any]], depth: int = 0) -> str:
        """Call LLM, execute tool calls, loop until we get narration text."""
        if depth > 4:
            log_error("llm_loop", f"depth limit reached ({depth}), last_content={bool(self._last_content)}")
            last_content = self._last_content
            if last_content:
                return last_content
            return "The dust settles. You stand at the crossroads, uncertain. What do you do?"

        log_llm_request(len(messages), self.model, depth)

        try:
            response = chat_completion(
                self.client,
                model=self.model,
                messages=messages,
                tools=TOOLS if depth < 3 else None,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        except Exception as exc:
            log_error("chat_completion", str(exc))
            if self._last_content:
                return self._last_content
            return f"The GM falters. (API error: {exc})"

        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        finish_reason = response.get("finish_reason", "")

        log_llm_response(content, tool_calls, finish_reason)

        self._last_content = content or self._last_content

        if not tool_calls:
            return content or self._last_content or "The GM regards you silently. Try again."

        messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": tool_calls,
        })

        all_failed = True
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}

            result = self._execute_tool(fn_name, args)
            log_tool_call(fn_name, args, result)
            if result.get("ok", False):
                all_failed = False
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, default=str),
            })

        if all_failed and content:
            log_error("llm_loop", f"all tools failed at depth {depth}, returning content")
            return content

        if all_failed and depth >= 2:
            log_error("llm_loop", f"all tools failed at depth {depth}, injecting no-tools directive")
            messages.append({
                "role": "user",
                "content": "[System: Tools are returning errors. Respond with narration text only — do not call more tools.]",
            })

        return self._llm_loop(messages, depth + 1)

    def _execute_tool(self, name: str, args: dict) -> dict:
        """Route a tool call to the appropriate bridge method."""
        try:
            if name == "roll_d20":
                return self.bridge.roll_d20(**args)
            elif name == "process_beat":
                return self.bridge.process_beat(**args)
            elif name == "world_travel":
                return self.bridge.world_travel(**args)
            elif name == "world_where":
                return self.bridge.world_where()
            elif name == "world_exits":
                return self.bridge.world_exits()
            elif name == "site_enter":
                return self.bridge.site_enter(**args)
            elif name == "site_move":
                return self.bridge.site_move(**args)
            elif name == "start_combat":
                return self.bridge.start_combat(**args)
            elif name == "combat_attack":
                return self.bridge.combat_attack(**args)
            elif name == "combat_end":
                return self.bridge.combat_end()
            elif name == "get_status":
                return self.bridge.status()
            elif name == "character_create":
                return self.bridge.character_create(**args)
            elif name == "memory_recall":
                return self.bridge.memory_recall(**args)
            else:
                return {"ok": False, "error": f"Unknown tool: {name}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
