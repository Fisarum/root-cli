"""Plugin registry — loads all built-in plugins and exposes them."""

from __future__ import annotations

from typing import Optional
from root.plugins.base import BasePlugin


_PLUGIN_MODULES = [
    "root.plugins.fzf",
    "root.plugins.bat",
    "root.plugins.fd",
    "root.plugins.lazygit",
    "root.plugins.gh",
    "root.plugins.gum",
    "root.plugins.glow",
    "root.plugins.ytdlp",
    "root.plugins.sherlock",
]

_registry: Optional["PluginRegistry"] = None


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}
        self._load_all()

    def _load_all(self) -> None:
        import importlib
        for mod_path in _PLUGIN_MODULES:
            try:
                mod = importlib.import_module(mod_path)
                plugin: BasePlugin = mod.plugin()
                self._plugins[plugin.info.name] = plugin
            except Exception:
                pass

    def all(self) -> list[BasePlugin]:
        return list(self._plugins.values())

    def available(self) -> list[BasePlugin]:
        return [p for p in self._plugins.values() if p.is_available()]

    def get(self, name: str) -> Optional[BasePlugin]:
        return self._plugins.get(name)

    def enrich_command(self, command: str, context: dict) -> str:
        """
        Pass command through each available plugin's enrich() method in order.
        Returns the (possibly rewritten) command.
        """
        for plugin in self.available():
            result = plugin.enrich(command, context)
            if result and result != command:
                return result
        return command


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry
