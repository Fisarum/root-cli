"""fd — fast file finder, drop-in replacement for find."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_FIND_NAME = re.compile(
    r"^find\s+\.\s+-name\s+['\"]?\*?\.?(\w+)['\"]?\s*(2>/dev/null)?$",
    re.IGNORECASE,
)
_FIND_TYPE_F = re.compile(
    r"^find\s+\.\s+-type\s+f\s*(2>/dev/null)?$",
    re.IGNORECASE,
)
_ALREADY_FD = re.compile(r"^fd\b", re.IGNORECASE)


class FdPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="fd",
            description="Fast file finder — 10–20× faster than find, respects .gitignore",
            binary="fd",
            install_hint="brew install fd",
            homepage="https://github.com/sharkdp/fd",
            enriches=["find"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        stripped = command.strip()
        if _ALREADY_FD.match(stripped):
            return None

        m = _FIND_NAME.match(stripped)
        if m:
            ext = m.group(1)
            if ext and ext != "null":
                return f"fd --extension {ext}"

        if _FIND_TYPE_F.match(stripped):
            return "fd"

        return None


def plugin() -> FdPlugin:
    return FdPlugin()
