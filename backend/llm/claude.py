"""Claude provider — Anthropic Claude API."""

from typing import Generator
from anthropic import Anthropic
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import LLMProviderFactory


@LLMProviderFactory.register("claude")
class ClaudeProvider(BaseLLMProvider):
    def __init__(self, config: dict):
        api_key = config.get("api_key", "")
        self.model = config.get("model", "claude-sonnet-4-6-20250514")

        if not api_key:
            raise ValueError("Claude API key is required. Set it in config.yaml or via Settings UI.")

        self._client = Anthropic(api_key=api_key)

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> str:
        messages = self._build_messages(history, user_message)
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
        )
        return resp.content[0].text

    def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        messages = self._build_messages(history, user_message)
        with self._client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _build_messages(self, history: list[dict] | None, user_message: str) -> list:
        messages = []
        if history:
            for h in history:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})
        return messages
