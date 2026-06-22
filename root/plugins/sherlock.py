"""Sherlock — find social media accounts by username plugin."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_SHERLOCK_TRIGGERS = re.compile(
    r"(find|search|look\s+up|locate)\s+(social\s+(media\s+)?)?(accounts?|profiles?|username)\s+(\w+)",
    re.IGNORECASE,
)
_ALREADY = re.compile(r"^(sherlock|python\s+-m\s+sherlock)\b", re.IGNORECASE)


class SherlockPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="sherlock",
            description="Hunt social media accounts across 400+ networks by username",
            binary="sherlock",
            install_hint="pip install sherlock-project",
            homepage="https://github.com/sherlock-project/sherlock",
            enriches=["find username", "search accounts"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        stripped = command.strip()
        if _ALREADY.match(stripped):
            return None
        m = _SHERLOCK_TRIGGERS.search(stripped)
        if m:
            username = m.group(5)
            return f"sherlock {username}"
        return None


def plugin() -> SherlockPlugin:
    return SherlockPlugin()
