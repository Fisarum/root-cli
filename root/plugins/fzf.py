"""fzf — command-line fuzzy finder plugin."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_FD_OR_FIND = re.compile(
    r"^(find\s|ls\s|ls$|cat\s|grep\s|ps\s|git\s+branch|git\s+log)",
    re.IGNORECASE,
)

_FZF_PIPED_ALREADY = re.compile(r"\|\s*fzf", re.IGNORECASE)


class FzfPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="fzf",
            description="Fuzzy finder — interactively filter any list output",
            binary="fzf",
            install_hint="brew install fzf",
            homepage="https://github.com/junegunn/fzf",
            enriches=["find", "ls", "grep", "git branch", "git log", "ps"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        if _FZF_PIPED_ALREADY.search(command):
            return None
        stripped = command.strip()
        if _FD_OR_FIND.match(stripped):
            return f"{stripped} | fzf"
        return None


def plugin() -> FzfPlugin:
    return FzfPlugin()
