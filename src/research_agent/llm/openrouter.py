from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from research_agent.domain import SessionMessage


class OpenRouterChatClient:
    def __init__(self, api_key: str, model: str, system_prompt: str) -> None:
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt

    def generate_answer(
        self,
        conversation_history: list[SessionMessage],
        report: str,
        evaluation_score: int,
        evaluation_feedback: list[str],
        citations: list[str],
    ) -> str:
        if not self.api_key:
            raise ValueError("OPEN_ROUTER_API is not set.")

        history_lines = [
            f"{message.role.upper()}: {message.content}"
            for message in conversation_history[-10:]
        ]
        prompt = (
            "Use the conversation history, report, and evaluation notes to answer the user's question.\n\n"
            "Conversation history:\n"
            f"{chr(10).join(history_lines) or 'No prior conversation.'}\n\n"
            "Research report:\n"
            f"{report}\n\n"
            f"Evaluation score: {evaluation_score}/10\n"
            "Evaluation feedback:\n"
            f"{chr(10).join(f'- {item}' for item in evaluation_feedback)}\n\n"
            "Citations:\n"
            f"{chr(10).join(f'- {item}' for item in citations) or '- none'}\n\n"
            "Rules:\n"
            "- Answer the user's question directly. Do NOT ask clarifying questions.\n"
            "- Synthesize the report data into a clear, useful response.\n"
            "- If evidence is weak or missing, say so briefly, then give the best answer you can.\n"
            "- Do not reveal internal reasoning or chain-of-thought."
        )
        return self._generate_text(prompt)

    def _generate_text(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 2000,
        }
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=120) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter chat request failed: {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenRouter chat request failed: {exc.reason}") from exc

        return self._extract_text(response_payload)

    def _extract_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices", [])
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices. payload={payload}")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            parts = [item.get("text", "") for item in content if isinstance(item, dict)]
            content = "\n".join(part for part in parts if part)

        text = str(content).strip()
        if not text:
            raise RuntimeError("OpenRouter returned an empty text response.")
        return self._sanitize_response(text)

    def _sanitize_response(self, text: str) -> str:
        lines = [line.rstrip() for line in text.splitlines()]
        non_empty = [line.strip() for line in lines if line.strip()]
        if not non_empty:
            return text

        bullet_like = sum(
            1
            for line in non_empty
            if line.startswith(("*", "-", "•")) or line.endswith(":")
        )
        if bullet_like >= max(3, len(non_empty) // 2):
            for line in reversed(non_empty):
                if not line.startswith(("*", "-", "•")) and not line.endswith(":"):
                    return line

        return text
