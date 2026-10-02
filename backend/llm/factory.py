"""LLM Provider factory — creates provider instances from config."""

from backend.config import Config
from backend.llm.base import BaseLLMProvider


class LLMProviderFactory:
    _registry: dict[str, type[BaseLLMProvider]] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(provider_cls):
            cls._registry[name] = provider_cls
            return provider_cls
        return decorator

    @classmethod
    def create(cls, config: Config) -> BaseLLMProvider:
        provider_name = config.llm_provider
        provider_config = config.provider_config()

        # Import only the two cloud API protocols supported by the launch version.
        import backend.llm.openai_compat  # noqa
        import backend.llm.claude  # noqa

        if provider_name != "api":
            raise ValueError("Only the cloud API provider is supported")
        base_url = provider_config.get("base_url", "").lower()
        actual_provider = "claude" if "anthropic" in base_url else "openai_compat"

        if actual_provider not in cls._registry:
            raise ValueError(
                f"Unknown LLM provider: {actual_provider}. Available: {list(cls._registry.keys())}"
            )

        print(f"[LLM] Using provider: {provider_name} → {actual_provider}")
        return cls._registry[actual_provider](provider_config)
