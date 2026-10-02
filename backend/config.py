"""Configuration loader — reads config.yaml and provides typed access."""

import os
from pathlib import Path
import yaml
from backend.storage import data_root, atomic_write


class Config:
    def __init__(self, config_path: Path | None = None):
        if config_path is None:
            config_path = Path(os.environ.get("R8D_CONFIG_FILE", str(data_root() / "config.yaml")))
            if not config_path.exists():
                source = Path(__file__).parent / "config.production.yaml"
                atomic_write(config_path, source.read_text(encoding="utf-8"))
        self._path = config_path
        self.reload()

    def reload(self):
        with open(self._path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    def save(self):
        atomic_write(self._path, yaml.safe_dump(self._data, allow_unicode=True, default_flow_style=False))

    @property
    def llm(self) -> dict:
        return self._data.get("llm", {})

    @property
    def llm_provider(self) -> str:
        return "api"

    def provider_config(self) -> dict:
        """Return the cloud API configuration.

        Environment variables (R8D_API_KEY, R8D_API_BASE, R8D_API_MODEL)
        take precedence over config.yaml values for the 'api' provider.
        This allows Docker / production deployments to inject secrets
        without modifying the config file.
        """
        cfg = dict(self.llm.get("api", {}))
        cfg["api_key"] = os.environ.get("R8D_API_KEY", cfg.get("api_key", ""))
        cfg["base_url"] = os.environ.get("R8D_API_BASE", cfg.get("base_url", ""))
        cfg["model"] = os.environ.get("R8D_API_MODEL", cfg.get("model", ""))
        return cfg

    @property
    def app(self) -> dict:
        return self._data.get("app", {})

    @property
    def interface_lang(self) -> str:
        return self.app.get("interface_lang", "zh")

    @property
    def report_lang(self) -> str:
        return self.app.get("report_lang", "zh")

    @property
    def report(self) -> dict:
        return self._data.get("report", {})

    def update_llm_provider(self, provider: str, settings: dict | None = None):
        """Update the only supported provider: a cloud API."""
        if provider != "api":
            raise ValueError("Only the cloud API provider is supported")
        existing = self._data.get("llm", {})
        existing["provider"] = "api"
        if settings:
            if provider not in existing:
                existing[provider] = {}
            existing[provider].update(settings)
        self._data["llm"] = existing
        self.save()

    def update_config(self, section: str, key: str, value):
        self._data[section][key] = value
        self.save()

_config_instance: Config | None = None


def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
