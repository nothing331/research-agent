from __future__ import annotations

import json
from typing import Any
from urllib import error, request


class OpenRouterEmbeddingClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def embed_texts(self, texts: list[str], title: str | None = None) -> list[list[float]]:
        if not self.api_key:
            raise ValueError("OPEN_ROUTER_API is required for vector embeddings.")
        if not texts:
            return []

        payload = {
            "model": self.model,
            "input": texts,
        }
        if title:
            payload["encoding_format"] = "float"
        response_payload = self._post_json(payload)
        embeddings = response_payload.get("data", [])
        return [item.get("embedding", []) for item in embeddings]

    def embed_query(self, query: str) -> list[float]:
        if not self.api_key:
            raise ValueError("OPEN_ROUTER_API is required for vector embeddings.")
        payload = {
            "model": self.model,
            "input": query,
        }
        response_payload = self._post_json(payload)
        data = response_payload.get("data", [])
        if not data:
            return []
        return data[0].get("embedding", [])

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            "https://openrouter.ai/api/v1/embeddings",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter embedding request failed: {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenRouter embedding request failed: {exc.reason}") from exc
