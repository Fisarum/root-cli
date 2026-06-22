"""bat — cat clone with syntax highlighting and Git integration."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_CAT_PATTERN = re.compile(r"^cat\s+(\S.*)", re.IGNORECASE)
_ALREADY_BAT = re.compile(r"\|\s*bat\b", re.IGNORECASE)

_TEXT_EXTENSIONS = (
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".c", ".cpp", ".h",
    ".java", ".rb", ".php", ".sh", ".bash", ".zsh", ".fish", ".toml", ".yaml",
    ".yml", ".json", ".md", ".txt", ".ini", ".cfg", ".conf", ".env", ".xml",
    ".html", ".css", ".sql",
)


def _looks_like_text_file(target: str) -> bool:
    t = target.lower().split()[0]
    return any(t.endswith(ext) for ext in _TEXT_EXTENSIONS)


class BatPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="bat",
            description="cat with syntax highlighting, line numbers, and Git diff indicators",
            binary="bat",
            install_hint="brew install bat",
            homepage="https://github.com/sharkdp/bat",
            enriches=["cat"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        if _ALREADY_BAT.search(command):
            return None
        m = _CAT_PATTERN.match(command.strip())
        if m:
            target = m.group(1)
            if _looks_like_text_file(target):
                return f"bat {target}"
        return None


def plugin() -> BatPlugin:
    return BatPlugin()
