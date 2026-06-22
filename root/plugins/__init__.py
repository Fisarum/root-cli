"""Root plugin system — discovery, loading, and pipeline enrichment."""

from root.plugins.registry import PluginRegistry, get_registry

__all__ = ["PluginRegistry", "get_registry"]
