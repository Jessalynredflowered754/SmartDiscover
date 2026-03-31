from __future__ import annotations

import httpx

from app.config import settings


class PromptStore:
    def __init__(self) -> None:
        self._url = settings.supabase_url.rstrip("/")
        self._api_key = settings.supabase_api_key.strip()
        self._table = settings.supabase_prompt_table.strip() or "prompt_logs"

    @property
    def enabled(self) -> bool:
        return bool(self._url and self._api_key)

    async def save_prompt(
        self,
        *,
        prompt_text: str,
        target_count: int | None,
        source: str,
        client_ip: str | None,
        user_agent: str | None,
    ) -> bool:
        if not self.enabled:
            return False

        endpoint = f"{self._url}/rest/v1/{self._table}"
        payload = {
            "prompt_text": prompt_text,
            "target_count": target_count,
            "source": source,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }
        headers = {
            "apikey": self._api_key,
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()

        return True
