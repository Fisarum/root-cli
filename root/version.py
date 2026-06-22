import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import httpx

from root import __version__

PYPI_URL = "https://pypi.org/pypi/root-cli/json"
GITHUB_RELEASES_URL = "https://api.github.com/repos/fisarum/root-cli/releases/latest"
GITHUB_TAGS_URL = "https://api.github.com/repos/fisarum/root-cli/tags"

VERSION_DIR = Path.home() / ".root"
VERSION_CHECK_FILE = VERSION_DIR / "version.json"
VERSION_LOG_FILE = VERSION_DIR / "version.log"
CHECK_INTERVAL_SECONDS = 7 * 24 * 60 * 60


def _ensure_version_dir() -> None:
    VERSION_DIR.mkdir(parents=True, exist_ok=True)


def _load_check_data() -> dict:
    if VERSION_CHECK_FILE.exists():
        try:
            return json.loads(VERSION_CHECK_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_check_data(data: dict) -> None:
    _ensure_version_dir()
    VERSION_CHECK_FILE.write_text(json.dumps(data, indent=2))


def _append_log(message: str) -> None:
    _ensure_version_dir()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with VERSION_LOG_FILE.open("a") as f:
        f.write(f"{timestamp} - {message}\n")


def get_installed_version() -> str:
    return __version__


def _is_newer(latest: str, current: str) -> bool:
    try:
        from packaging import version

        return version.parse(latest) > version.parse(current)
    except Exception:
        try:
            return tuple(int(p) for p in latest.split(".")) > tuple(
                int(p) for p in current.split(".")
            )
        except Exception:
            return latest != current


def fetch_latest_version() -> Optional[str]:
    try:
        r = httpx.get(PYPI_URL, timeout=10, follow_redirects=True)
        if r.status_code == 200:
            version = r.json().get("info", {}).get("version")
            if version:
                return version
    except Exception:
        pass

    try:
        r = httpx.get(
            GITHUB_RELEASES_URL,
            timeout=10,
            follow_redirects=True,
            headers={"Accept": "application/vnd.github+json"},
        )
        if r.status_code == 200:
            tag = r.json().get("tag_name", "")
            return tag.lstrip("v") if tag else None
    except Exception:
        pass

    try:
        r = httpx.get(
            GITHUB_TAGS_URL,
            timeout=10,
            follow_redirects=True,
            headers={"Accept": "application/vnd.github+json"},
        )
        if r.status_code == 200:
            tags = r.json()
            if tags:
                first = tags[0].get("name", "")
                return first.lstrip("v") if first else None
    except Exception:
        pass

    return None


def check_for_update(force: bool = False) -> dict:
    data = _load_check_data()
    now = time.time()
    last_check = data.get("last_check", 0)
    latest_cached = data.get("latest_version")
    current = get_installed_version()

    if (
        not force
        and latest_cached
        and (now - last_check) < CHECK_INTERVAL_SECONDS
    ):
        return {
            "checked": False,
            "current": current,
            "latest": latest_cached,
            "update_available": _is_newer(latest_cached, current),
        }

    latest = fetch_latest_version()
    checked = latest is not None

    if checked:
        update_available = _is_newer(latest, current)
        data["last_check"] = now
        data["latest_version"] = latest
        _save_check_data(data)
        if update_available:
            _append_log(f"update available - current: {current}, latest: {latest}")
        else:
            _append_log(f"up to date - current: {current}, latest: {latest}")
    else:
        update_available = False
        _append_log(f"version check failed - current: {current}")

    return {
        "checked": checked,
        "current": current,
        "latest": latest,
        "update_available": update_available,
    }


def _get_distribution_version() -> str:
    try:
        from importlib.metadata import version

        return version("root-cli")
    except Exception:
        return __version__


def run_update() -> Tuple[bool, str]:
    current = _get_distribution_version()
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "root-cli"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        if result.returncode != 0:
            return False, current
        new_version = _get_distribution_version()
        return True, new_version
    except Exception:
        return False, current
