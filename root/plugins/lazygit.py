"""lazygit — simple terminal UI for Git operations."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_LAZYGIT_TRIGGERS = re.compile(
    r"^(lazygit|git\s+(ui|tui|visual|open|gui|dashboard))$",
    re.IGNORECASE,
)


class LazygitPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="lazygit",
            description="Visual TUI for Git — commit, branch, merge, rebase interactively",
            binary="lazygit",
            install_hint="brew install lazygit",
            homepage="https://github.com/jesseduffield/lazygit",
            enriches=["git ui", "git tui"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        if _LAZYGIT_TRIGGERS.match(command.strip()):
            return "lazygit"
        return None


def plugin() -> LazygitPlugin:
    return LazygitPlugin()
