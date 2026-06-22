import os
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

CONFIG_DIR = Path.home() / ".root"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULTS = {
    "backend": "ollama",
    "ollama": {
        "host": "http://localhost:11434",
        "model": "hf.co/albinab/Qwen-0.5B-Coder-El-Terminalo:latest",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "api_key": "",
    },
    "behavior": {
        "auto_run": False,
        "show_context": True,
        "mode": "cautious",  # cautious or turbo
        "auto_trust_safe_commands": True,
        "auto_trust_moderate_commands": False,
        "show_mode_indicator": True,
    },
    "memory": {
        "enabled": True,
        "learn_patterns": True,
        "learn_preferences": True,
        "max_history_days": 30,
        "session_learning": True,
        "pattern_confidence_threshold": 0.7,
    },
    "agent": {
        "self_aware": True,
        "identity_response": "I am Root, a native CLI micro agent",
        "show_capabilities": True,
    },
}


def load() -> dict:
    if not CONFIG_FILE.exists():
        return DEFAULTS.copy()
    with open(CONFIG_FILE, "rb") as f:
        user = tomllib.load(f)
    return _deep_merge(DEFAULTS.copy(), user)


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(cfg, f)


def init_defaults() -> None:
    if not CONFIG_FILE.exists():
        save(DEFAULTS.copy())


def _deep_merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
