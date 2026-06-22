"""Base interface every Root plugin must implement."""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PluginInfo:
    name: str
    description: str
    binary: str
    install_hint: str
    homepage: str
    enriches: list[str] = field(default_factory=list)


class BasePlugin(ABC):
    """All Root plugins inherit from this."""

    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Return static metadata about this plugin."""

    def is_available(self) -> bool:
        """Return True if the plugin binary is on PATH."""
        return shutil.which(self.info.binary) is not None

    def enrich(self, command: str, context: dict) -> Optional[str]:
        """
        Optionally rewrite *command* to use this plugin.
        Return the rewritten command string, or None to leave it unchanged.
        Only called when is_available() is True.
        """
        return None

    def run_interactive(self, args: list[str], context: dict) -> None:
        """
        Launch the tool interactively (replaces the current process).
        Default implementation uses subprocess.
        """
        import subprocess, os
        binary = shutil.which(self.info.binary)
        if not binary:
            raise RuntimeError(f"{self.info.binary} is not installed. {self.info.install_hint}")
        subprocess.run([binary] + args, cwd=context.get("cwd"))
