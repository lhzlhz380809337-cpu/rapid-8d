"""OpenAI-compatible provider — covers OpenAI, DeepSeek, 豆包, etc."""

from typing import Generator
from openai import OpenAI
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import LLMProviderFactory


@LLMProviderFactory.register("openai_compat")
class OpenAICompatProvider(BaseLLMProvider):
    def __init__(self, config: dict):
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-4o")

        if not api_key:
            raise ValueError("OpenAI API key is required. Set it in config.yaml or via Settings UI.")

        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=90.0, max_retries=0)

    def _build_messages(self, system_prompt: str, user_message: str, history: list[dict] | None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": user_message})
        return messages

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> str:
        messages = self._build_messages(system_prompt, user_message, history)
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        messages = self._build_messages(system_prompt, user_message, history)
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
