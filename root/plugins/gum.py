"""gum — Charm Bracelet interactive shell script styling tool."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_GUM_ALREADY = re.compile(r"^gum\b", re.IGNORECASE)

_CHOOSE_PATTERN = re.compile(
    r"^(choose|pick|select)\s+(from|between|one of)\s+(.+)", re.IGNORECASE
)
_CONFIRM_PATTERN = re.compile(
    r"^(ask|confirm|prompt)\s+(to|user)?\s*(.+)", re.IGNORECASE
)
_INPUT_PATTERN = re.compile(
    r"^(read|input|get)\s+(user\s+)?(input|text|value)", re.IGNORECASE
)


class GumPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="gum",
            description="Charm Gum — style shell scripts with interactive inputs, spinners, colors",
            binary="gum",
            install_hint="brew install gum",
            homepage="https://github.com/charmbracelet/gum",
            enriches=["choose", "confirm", "input"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        stripped = command.strip()
        if _GUM_ALREADY.match(stripped):
            return None
        m = _CHOOSE_PATTERN.match(stripped)
        if m:
            options = m.group(3).replace(",", " ").split()
            return "gum choose " + " ".join(f'"{o.strip()}"' for o in options)
        if _INPUT_PATTERN.match(stripped):
            return 'gum input --placeholder "Enter value..."'
        if _CONFIRM_PATTERN.match(stripped):
            question = _CONFIRM_PATTERN.match(stripped).group(3)
            return f'gum confirm "{question}"'
        return None


def plugin() -> GumPlugin:
    return GumPlugin()
