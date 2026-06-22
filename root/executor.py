import os
import platform
import subprocess
import tempfile
import time

import pyperclip
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

from root.theme import ACCENT, ACCENT_DIM, ACCENT_SOFT, SUCCESS, WARNING, ERROR, REFUSE, FG_DIM, FG_MUTED
from root.risk import get_risk_assessor

console = Console()

REFUSE_TOKEN = "REFUSE"

# Phrases the model emits when it refuses or gets confused
_REFUSE_PREFIXES = ("refuse", "clarify", "i cannot", "i can't", "i'm unable", "i am unable")


def _looks_like_command(text: str) -> bool:
    """Return False if the model returned prose instead of a shell command."""
    t = text.strip().lower()
    # Multi-line prose or starts with a known refusal phrase
    if t.startswith(_REFUSE_PREFIXES):
        return False
    # Has spaces but no shell-typical tokens — heuristic: real commands contain
    # at least one of: / . - | > $ ( letters followed immediately by space+flag
    lines = text.strip().splitlines()
    if len(lines) > 3:
        return False
    return True


def present_and_act(command: str, context: dict, config: dict, session_id: int = None) -> None:
    """Display the translated command and prompt the user for an action."""
    cmd = command.strip()
    
    # Get risk assessment
    risk_assessor = get_risk_assessor()
    risk_level, risk_reason = risk_assessor.assess_risk(cmd)
    
    # Check if we should auto-run based on mode and risk
    mode = config.get('behavior', {}).get('mode', 'cautious')
    should_auto_run = risk_assessor.should_auto_run(cmd, mode, config)
    
    if cmd.upper() == REFUSE_TOKEN or cmd.lower().startswith(_REFUSE_PREFIXES):
        console.print(
            f"\n  [bold {REFUSE}]⚠[/bold {REFUSE}]  Root refused to generate this command — "
            f"it appears destructive or dangerous.\n"
        )
        return

    if not _looks_like_command(cmd):
        console.print(f"\n  [{WARNING}]The model returned an unclear response. Try rephrasing.[/{WARNING}]\n")
        return

    # Transparent plugin enrichment — upgrade command if a plugin can improve it
    try:
        from root.plugins import get_registry
        enriched = get_registry().enrich_command(cmd, context)
        if enriched != cmd:
            cmd = enriched
            risk_level, risk_reason = risk_assessor.assess_risk(cmd)
    except Exception:
        pass

    _print_command(cmd, risk_level, risk_assessor)
    
    # Store command in memory with risk assessment
    if session_id and config.get('memory', {}).get('enabled', True):
        from root.memory import get_memory_manager, CommandHistory
        memory = get_memory_manager()
        history = CommandHistory(
            query="",  # Will be filled by caller
            command=cmd,
            context=context,
            success=False,  # Will be updated after execution
            execution_time=0.0,  # Will be updated after execution
            timestamp=time.time(),
            risk_level=risk_level
        )
        # Store without query first, will be updated by caller
        
    if should_auto_run:
        if mode == 'turbo':
            console.print(f"  [{FG_DIM}]Turbo mode: Auto-running...[/{FG_DIM}]\n")
        else:
            console.print(f"  [{FG_DIM}]Auto-running trusted command...[/{FG_DIM}]\n")
        _run(cmd, context, session_id, config)
        return

    _interactive_prompt(cmd, context, risk_level, risk_assessor, session_id, config)


def _print_command(command: str, risk_level: str, risk_assessor) -> None:
    console.print()
    
    # Show risk indicator if enabled
    from root import config as cfg
    conf = cfg.load()
    if conf.get('behavior', {}).get('show_mode_indicator', True):
        risk_symbol = risk_assessor.get_risk_symbol(risk_level)
        risk_color = risk_assessor.get_risk_color(risk_level)
        console.print(f"  [{risk_color}]{risk_symbol}[/{risk_color}]  Risk level: {risk_level}\n")
    
    syntax = Syntax(
        command,
        "bash",
        theme="monokai",
        background_color="default",
        word_wrap=True,
    )
    console.print("  ", syntax, end="")
    console.print()


def _interactive_prompt(command: str, context: dict, risk_level: str, risk_assessor, session_id: int, config: dict) -> None:
    options = Text()
    options.append("  [", style="dim")
    options.append("r", style=f"bold {ACCENT}")
    options.append("]un  [", style="dim")
    options.append("q", style=f"{FG_MUTED}")
    options.append("]uit  ", style="dim")
    options.append("> ", style=f"{ACCENT}")

    console.print(options, end="")

    try:
        choice = input().strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print("\n")
        return

    if choice == "r":
        _run(command, context, session_id, config)
    elif choice == "q" or choice == "":
        console.print()
    else:
        console.print(f"\n  [dim]Unknown option '{choice}'. Aborted.[/dim]\n")


def _pick_run_spinner(command: str) -> tuple[str, str]:
    c = command.lower()
    if any(w in c for w in ("find ", "locate ", "grep ", "ls ", "du ")):
        return "dots2", "Searching…"
    if any(w in c for w in ("git ", "npm ", "pip ", "brew ", "apt ", "cargo ")):
        return "dots12", "Running…"
    if any(w in c for w in ("rm ", "kill ", "pkill ", "rmdir ")):
        return "noise", "Running…"
    if any(w in c for w in ("curl ", "wget ", "ssh ", "ping ")):
        return "bouncingBar", "Connecting…"
    if any(w in c for w in ("tar ", "zip ", "gzip ", "unzip ")):
        return "line", "Compressing…"
    return "dots", "Running…"


def _run(command: str, context: dict, session_id: int = None, config: dict = None) -> None:
    start_time = time.time()
    spinner, label = _pick_run_spinner(command)
    shell = context.get("shell", "bash")
    cwd = context.get("cwd", None)

    if platform.system() == "Windows":
        if shell == "PowerShell":
            args = ["pwsh", "-NoProfile", "-Command", command]
        else:
            args = ["cmd.exe", "/c", command]
    else:
        shell_bin = _resolve_shell_bin(shell)
        args = [shell_bin, "-c", command]

    with console.status(f"  [dim]{label}[/dim]", spinner=spinner):
        result = subprocess.run(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    execution_time = time.time() - start_time
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    success = result.returncode == 0

    _render_output(stdout, stderr, command)
    
    # Update memory with execution results
    if session_id and config and config.get('memory', {}).get('enabled', True):
        from root.memory import get_memory_manager, CommandHistory
        memory = get_memory_manager()
        # Update the last command with execution results
        memory.update_session_stats(session_id, successful=success)
        
        # Store complete command history
        risk_assessor = get_risk_assessor()
        risk_level, _ = risk_assessor.assess_risk(command)
        history = CommandHistory(
            query="",  # Will be updated by caller
            command=command,
            context=context,
            success=success,
            execution_time=execution_time,
            timestamp=time.time(),
            risk_level=risk_level
        )
        memory.store_command(history)


def _resolve_shell_bin(shell: str) -> str:
    import shutil
    candidates = {
        "zsh": ["zsh"],
        "bash": ["bash"],
        "fish": ["fish"],
        "ksh": ["ksh"],
    }
    for bin_name in candidates.get(shell, ["bash"]):
        path = shutil.which(bin_name)
        if path:
            return path
    return "/bin/sh"


def _render_output(stdout: str, stderr: str, command: str) -> None:
    # Filter out permission-denied noise from stderr
    real_errors = [
        line for line in stderr.splitlines()
        if line and "Operation not permitted" not in line
        and "Permission denied" not in line
    ]

    if not stdout:
        if real_errors:
            console.print(f"  [bold {ERROR}]Error:[/bold {ERROR}] {real_errors[0]}\n")
        else:
            console.print(f"  [{FG_DIM}]Done — no output.[/{FG_DIM}]\n")
        return

    lines = stdout.splitlines()

    # Detect file listing output (paths, one per line)
    is_file_list = _looks_like_file_list(lines)

    if is_file_list:
        _render_file_list(lines)
    elif len(lines) == 1:
        console.print(f"  {lines[0]}\n")
    elif len(lines) <= 20:
        for line in lines:
            console.print(f"  {line}")
        console.print()
    else:
        # Long output: show first 15 lines + summary
        for line in lines[:15]:
            console.print(f"  {line}")
        console.print(f"\n  [{FG_DIM}]… and {len(lines) - 15} more lines.[/{FG_DIM}]\n")

    if real_errors:
        console.print(f"  [bold {WARNING}]Warning:[/bold {WARNING}] {real_errors[0]}\n")


def _looks_like_file_list(lines: list[str]) -> bool:
    if not lines:
        return False
    path_like = sum(
        1 for l in lines[:10]
        if l.startswith("/") or l.startswith("./") or l.startswith("~")
    )
    return path_like >= min(2, len(lines))


def _render_file_list(lines: list[str]) -> None:
    count = len(lines)
    console.print(
        f"  [bold {SUCCESS}]Found {count} file{'s' if count != 1 else ''}:[/bold {SUCCESS}]\n"
    )
    show = lines[:10]
    for path in show:
        # Show just filename bold + dimmed parent path
        parts = path.rsplit("/", 1)
        if len(parts) == 2:
            console.print(f"  [{FG_MUTED}]{parts[0]}/[/{FG_MUTED}][bold {ACCENT_SOFT}]{parts[1]}[/bold {ACCENT_SOFT}]")
        else:
            console.print(f"  [bold {ACCENT_SOFT}]{path}[/bold {ACCENT_SOFT}]")
    if count > 10:
        console.print(f"\n  [{FG_DIM}]… and {count - 10} more.[/{FG_DIM}]")
    console.print()


