from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from research_agent.domain import SessionMessage


class GeminiClient:
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
            raise ValueError("GEMINI_API_KEY is not set.")

        history_lines = [
            f"{message.role.upper()}: {message.content}"
            for message in conversation_history[-10:]
        ]
        prompt = (
            "Use the conversation history, report, and evaluation notes to answer the user.\n\n"
            "Conversation history:\n"
            f"{chr(10).join(history_lines) or 'No prior conversation.'}\n\n"
            "Research report:\n"
            f"{report}\n\n"
            f"Evaluation score: {evaluation_score}/10\n"
            "Evaluation feedback:\n"
            f"{chr(10).join(f'- {item}' for item in evaluation_feedback)}\n\n"
            "Citations:\n"
            f"{chr(10).join(f'- {item}' for item in citations) or '- none'}\n\n"
            "Respond like a helpful chatbot. If the tools are stubbed or evidence is weak, say that clearly.\n"
            "Return only the final user-facing answer.\n"
            "Do not reveal chain-of-thought, scratchpad notes, internal analysis, or planning."
        )
        return self._generate_text(prompt)

    def _generate_text(self, prompt: str) -> str:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": self.system_prompt,
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 1000,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=60) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API request failed: {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Gemini API request failed: {exc.reason}") from exc

        return self._extract_text(response_payload)

    def _extract_text(self, payload: dict[str, Any]) -> str:
        candidates = payload.get("candidates", [])
        if not candidates:
            prompt_feedback = payload.get("promptFeedback")
            raise RuntimeError(f"Gemini returned no candidates. promptFeedback={prompt_feedback}")

        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if "text" in part]
        text = "\n".join(item for item in text_parts if item).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty text response.")
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
