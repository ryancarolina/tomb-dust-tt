"""OpenRouter API client (OpenAI-compatible)."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


def create_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment / .env")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def chat_completion(
    client: OpenAI,
    *,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] = "auto",
    max_tokens: int = 2048,
    temperature: float = 0.8,
) -> dict:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    response = client.chat.completions.create(**kwargs)
    choice = response.choices[0]
    message = choice.message

    result: dict[str, Any] = {
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [],
        "finish_reason": choice.finish_reason,
    }

    if message.tool_calls:
        for tc in message.tool_calls:
            result["tool_calls"].append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            })

    return result
