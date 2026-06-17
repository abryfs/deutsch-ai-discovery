from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str
    base_url: str = DEFAULT_BASE_URL
    app_name: str = "deutsch-ai-discovery"

    @classmethod
    def from_env(cls) -> "OpenRouterConfig":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for real model runs.")
        return cls(
            api_key=api_key,
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            base_url=os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            app_name=os.getenv("OPENROUTER_APP_NAME", "deutsch-ai-discovery"),
        )


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
        }
        request = urllib.request.Request(
            url=f"{self.config.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/abryfs/deutsch-ai-discovery",
                "X-Title": self.config.app_name,
            },
            method="POST",
        )
        data = _open_json_with_retries(request, provider="OpenRouter")

        return _extract_content(data)


def _extract_content(data: dict[str, Any]) -> str:
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"Unexpected OpenRouter response shape: {data}") from error


def _open_json_with_retries(request: urllib.request.Request, provider: str) -> dict[str, Any]:
    max_retries = int(os.getenv("MODEL_HTTP_RETRIES", "2"))
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            if attempt < max_retries and error.code in {500, 502, 503, 504}:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"{provider} request failed: HTTP {error.code}: {body}") from error
        except urllib.error.URLError as error:
            if attempt < max_retries:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"{provider} request failed: {error.reason}") from error
    raise RuntimeError(f"{provider} request failed after retries.")
