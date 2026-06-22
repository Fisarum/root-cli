"""gh — GitHub CLI plugin."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_GH_ALREADY = re.compile(r"^gh\b", re.IGNORECASE)

_OPEN_PR = re.compile(
    r"^(open|show|view|list)\s+(pull\s+request|pr)s?", re.IGNORECASE
)
_LIST_ISSUES = re.compile(
    r"^(open|show|view|list)\s+issues?", re.IGNORECASE
)
_CREATE_PR = re.compile(
    r"^(create|open|make)\s+(a\s+)?(pull\s+request|pr)", re.IGNORECASE
)
_REPO_STATUS = re.compile(
    r"^(show|view|open)\s+(repo|repository)\s+(status|info|details)?", re.IGNORECASE
)


class GhPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="gh",
            description="GitHub CLI — manage repos, PRs, issues, workflows from terminal",
            binary="gh",
            install_hint="brew install gh",
            homepage="https://cli.github.com",
            enriches=["pr", "issues", "repo"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        stripped = command.strip()
        if _GH_ALREADY.match(stripped):
            return None
        if _OPEN_PR.match(stripped):
            return "gh pr list"
        if _LIST_ISSUES.match(stripped):
            return "gh issue list"
        if _CREATE_PR.match(stripped):
            return "gh pr create"
        if _REPO_STATUS.match(stripped):
            return "gh repo view"
        return None


def plugin() -> GhPlugin:
    return GhPlugin()
