"""yt-dlp — YouTube and multi-site video/audio downloader plugin."""

from __future__ import annotations

import re
from typing import Optional

from root.plugins.base import BasePlugin, PluginInfo

_YTDLP_TRIGGERS = re.compile(
    r"(download|save|grab|get)\s+(video|audio|music|song|youtube|yt)\b",
    re.IGNORECASE,
)
_URL_PRESENT = re.compile(r"https?://\S+")
_ALREADY = re.compile(r"^yt-dlp\b", re.IGNORECASE)


class YtDlpPlugin(BasePlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="yt-dlp",
            description="Download video/audio from YouTube and 1000+ other sites",
            binary="yt-dlp",
            install_hint="brew install yt-dlp  OR  pip install yt-dlp",
            homepage="https://github.com/yt-dlp/yt-dlp",
            enriches=["download video", "download audio"],
        )

    def enrich(self, command: str, context: dict) -> Optional[str]:
        stripped = command.strip()
        if _ALREADY.match(stripped):
            return None
        url_match = _URL_PRESENT.search(stripped)
        if _YTDLP_TRIGGERS.search(stripped):
            if url_match:
                url = url_match.group(0)
                if "audio" in stripped.lower() or "music" in stripped.lower() or "song" in stripped.lower():
                    return f'yt-dlp -x --audio-format mp3 "{url}"'
                return f'yt-dlp "{url}"'
            return 'yt-dlp "<paste URL here>"'
        return None


def plugin() -> YtDlpPlugin:
    return YtDlpPlugin()
