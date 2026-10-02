"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Generator


class BaseLLMProvider(ABC):
    """All LLM providers must implement this interface."""

    @abstractmethod
    def chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Send a chat request and return the full response."""
        ...

    @abstractmethod
    def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """Send a chat request and yield response tokens."""
        ...
