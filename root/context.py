import os
import platform
import shutil
import sys


def detect() -> dict:
    """Detect the current OS, shell, and working directory."""
    return {
        "os": _detect_os(),
        "shell": _detect_shell(),
        "cwd": os.getcwd(),
    }


def _detect_os() -> str:
    system = platform.system()
    if system == "Darwin":
        return "macOS"
    if system == "Windows":
        return "Windows"
    if system == "Linux":
        return "Linux"
    return system


def _detect_shell() -> str:
    if platform.system() == "Windows":
        # Check if running inside PowerShell
        if os.environ.get("PSModulePath"):
            return "PowerShell"
        # Check for PowerShell Core cross-platform
        if shutil.which("pwsh") and _is_pwsh_parent():
            return "PowerShell"
        return "cmd.exe"

    shell_path = os.environ.get("SHELL", "")
    shell_name = os.path.basename(shell_path).lower()

    if "zsh" in shell_name:
        return "zsh"
    if "fish" in shell_name:
        return "fish"
    if "bash" in shell_name:
        return "bash"
    if "ksh" in shell_name:
        return "ksh"
    if shell_name:
        return shell_name
    return "bash"


def _is_pwsh_parent() -> bool:
    try:
        import subprocess
        parent_pid = os.getppid()
        result = subprocess.run(
            ["ps", "-p", str(parent_pid), "-o", "comm="],
            capture_output=True, text=True, timeout=2
        )
        return "pwsh" in result.stdout.lower()
    except Exception:
        return False


def format_for_prompt(ctx: dict) -> str:
    return f"OS: {ctx['os']} | Shell: {ctx['shell']} | CWD: {ctx['cwd']}"
