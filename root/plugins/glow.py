"""glow — Charm Bracelet markdown renderer for the terminal."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_CAT_MD = re.compile(
    r"^(cat|less|more|open)\s+(\S+\.md)\s*(2>/dev/null)?$",
    re.IGNORECASE,
)
_ALREADY_GLOW = re.compile(r"^glow\b", re.IGNORECASE)


class GlowPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="glow",
            description="Charm Glow — beautiful markdown rendering in the terminal",
            binary="glow",
            install_hint="brew install glow",
            homepage="https://github.com/charmbracelet/glow",
            enriches=["cat *.md", "less *.md"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        stripped = command.strip()
        if _ALREADY_GLOW.match(stripped):
            return None
        m = _CAT_MD.match(stripped)
        if m:
            md_file = m.group(2)
            return f"glow {md_file}"
        return None


def plugin() -> GlowPlugin:
    return GlowPlugin()
