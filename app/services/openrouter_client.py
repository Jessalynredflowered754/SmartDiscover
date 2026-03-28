import json
import re
from typing import Any

import httpx

from app.config import settings


class OpenRouterClient:
    def __init__(self) -> None:
        self.base_url = settings.openrouter_base_url.rstrip("/")
        self.model = settings.openrouter_model
        self.api_key = settings.openrouter_api_key

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def health_check(self) -> dict[str, Any]:
        if not self.enabled:
            return {
                "status": "disabled",
                "ok": False,
                "details": "OPENROUTER_API_KEY belum diisi.",
            }

        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Reply with the word ok."},
                    {"role": "user", "content": "health check"},
                ],
                "max_tokens": 8,
                "temperature": 0,
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
            if resp.status_code != 200:
                return {
                    "status": "openrouter-error",
                    "ok": False,
                    "details": f"OpenRouter returned {resp.status_code}",
                }
            return {
                "status": "ok",
                "ok": True,
                "details": "OpenRouter reachable.",
            }
        except Exception as exc:
            return {
                "status": "openrouter-exception",
                "ok": False,
                "details": str(exc),
            }

    async def chat_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 700) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
            if resp.status_code != 200:
                return None

            body = resp.json()
            content = (
                body.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return self._parse_json_content(content)
        except Exception:
            return None

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "SmartDiscover",
        }

    def _parse_json_content(self, content: str) -> dict[str, Any] | None:
        text = content.strip()
        if not text:
            return None

        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass

        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if fenced:
            try:
                parsed = json.loads(fenced.group(1))
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None

        # Last attempt: first JSON object substring.
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(text[start : end + 1])
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None
        return None
