"""OpenRouter API client for script generation."""

from __future__ import annotations

import os
from typing import Any

import httpx


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-haiku-4-5-20251001"


class AIClient:
    """Async OpenRouter wrapper with model switching via environment variable."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = os.getenv("AI_MODEL", DEFAULT_MODEL)
        self.fallback_model = os.getenv("AI_FALLBACK_MODEL", "").strip()
        self.site_name = os.getenv("OPENROUTER_SITE_NAME", "Synthera World")
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "http://localhost")
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "4096"))
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.1"))

    async def _one_call(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
            if response.status_code >= 400:
                details = response.text.strip()
                raise RuntimeError(
                    f"OpenRouter request failed with {response.status_code}: {details}"
                )
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {data}")

        message = choices[0].get("message", {})
        content = message.get("content")
        refusal = message.get("refusal")
        finish_reason = choices[0].get("finish_reason")

        if isinstance(content, list):
            # Some providers return multimodal content chunks; keep text chunks only.
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            content = "\n".join([p for p in text_parts if p])

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(
                "OpenRouter returned empty/non-text content. "
                f"model={model}, finish_reason={finish_reason}, refusal={refusal}"
            )

        usage = data.get("usage", {})
        return {"script": content, "usage": usage, "model": model}

    async def complete(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """General chat completion helper for non-script tasks."""
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
            if response.status_code >= 400:
                raise RuntimeError(
                    f"OpenRouter request failed with {response.status_code}: {response.text.strip()}"
                )
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {data}")
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            content = "\n".join([p for p in text_parts if p])
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenRouter returned empty/non-text content for chat.")
        return {"content": content.strip(), "usage": data.get("usage", {}), "model": self.model}

    async def generate_script(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Generate script text from prompts with optional model fallback."""
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        errors: list[str] = []
        models = [self.model]
        if self.fallback_model and self.fallback_model not in models:
            models.append(self.fallback_model)

        for model in models:
            try:
                return await self._one_call(
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            except Exception as exc:
                errors.append(f"{model}: {exc}")

        raise RuntimeError("All model attempts failed. " + " | ".join(errors))
