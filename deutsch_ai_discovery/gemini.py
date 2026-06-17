from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str = "gemini-2.5-flash"
    base_url: str = DEFAULT_BASE_URL

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is required for Gemini runs.")
        return cls(
            api_key=api_key,
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            base_url=os.getenv("GEMINI_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        )


class GeminiClient:
    def __init__(self, config: GeminiConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        prompt = "\n\n".join(f"{message['role'].upper()}:\n{message['content']}" for message in messages)
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }
        request = urllib.request.Request(
            url=f"{self.config.base_url}/models/{self.config.model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.config.api_key,
            },
            method="POST",
        )
        data = _open_json_with_retries(request, provider="Gemini")

        return _extract_text(data)


def _extract_text(data: dict[str, Any]) -> str:
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(str(part.get("text", "")) for part in parts)
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"Unexpected Gemini response shape: {data}") from error


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
