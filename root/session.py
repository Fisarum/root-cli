import sys
import time

from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.rule import Rule
from rich.padding import Padding

from root import __version__
from root import context
from root import config as cfg
from root.theme import ACCENT, ACCENT_DIM, ACCENT_SOFT, WARNING, ERROR, FG_DIM, FG_MUTED, CWD, SHELL_LABEL

console = Console()

BANNER = f"""\
  [bold {ACCENT}]root[/bold {ACCENT}] [dim]v{__version__} by Fisarum[/dim]
  [{FG_DIM}]Type your request in plain English. Type [bold]exit[/bold] or press Ctrl+C to quit.[/{FG_DIM}]
"""

SESSION_COMMANDS = {"exit", "quit", "q", ":q", "bye"}


def start() -> None:
    """Start an interactive root session (REPL)."""
    console.print()
    console.print(BANNER)
    console.rule(style=FG_DIM)
    console.print()

    conf = cfg.load()
    
    # Initialize memory and start session tracking
    session_id = None
    if conf.get('memory', {}).get('enabled', True):
        from root.memory import get_memory_manager
        memory = get_memory_manager()
        mode = conf.get('behavior', {}).get('mode', 'cautious')
        session_id = memory.start_session(mode)
        
        # Show mode indicator if enabled
        if conf.get('behavior', {}).get('show_mode_indicator', True):
            mode_color = 'green' if mode == 'turbo' else 'yellow'
            console.print(f"  [{mode_color}]Mode: {mode.upper()}[/{mode_color}]\n")

    try:
        while True:
            ctx = context.detect()
            prompt = _build_prompt(ctx, conf)

            try:
                console.print(prompt, end="")
                query = input().strip()
            except (KeyboardInterrupt, EOFError):
                _farewell(session_id, conf)
                break

            if not query:
                continue

            if query.lower() in SESSION_COMMANDS:
                _farewell(session_id, conf)
                break

            # In-session meta commands
            if query.lower() in ("help", "?"):
                _print_help(conf)
                continue

            if query.lower() == "clear":
                console.clear()
                console.print(BANNER)
                console.rule(style=FG_DIM)
                if conf.get('behavior', {}).get('show_mode_indicator', True):
                    mode = conf.get('behavior', {}).get('mode', 'cautious')
                    mode_color = 'green' if mode == 'turbo' else 'yellow'
                    console.print(f"  [{mode_color}]Mode: {mode.upper()}[/{mode_color}]\n")
                console.print()
                continue
            
            # Mode switching commands
            if query.lower() in ("mode cautious", "cautious"):
                _switch_mode("cautious", conf, session_id)
                continue
            
            if query.lower() in ("mode turbo", "turbo"):
                _switch_mode("turbo", conf, session_id)
                continue
            
            if query.lower() == "status":
                _show_status(session_id, conf)
                continue

            _handle_query(query, ctx, conf, session_id)
            console.print()
    
    except Exception as e:
        console.print(f"\n  [{ERROR}]Session error: {e}[/{ERROR}]\n")
        if session_id:
            _farewell(session_id, conf, show_message=False)


def _handle_query(query: str, ctx: dict, conf: dict, session_id: int = None) -> None:
    from root import translate, executor

    # Detect query intent for spinner selection
    spinner, spinner_text = _pick_spinner(query)

    with console.status(f"  [dim]{spinner_text}[/dim]", spinner=spinner):
        try:
            command = translate.translate(query, ctx)
        except Exception as e:
            console.print(f"\n  [bold {ERROR}]Error:[/bold {ERROR}] {e}\n")
            return

    if not command:
        console.print(f"  [{WARNING}]No command generated. Try rephrasing.[/{WARNING}]")
        return

    # Store the query in memory before execution
    if session_id and conf.get('memory', {}).get('enabled', True):
        from root.memory import get_memory_manager, CommandHistory
        memory = get_memory_manager()
        
        # Get risk assessment for memory storage
        from root.risk import get_risk_assessor
        risk_assessor = get_risk_assessor()
        risk_level, _ = risk_assessor.assess_risk(command)
        
        history = CommandHistory(
            query=query,
            command=command,
            context=ctx,
            success=False,  # Will be updated after execution
            execution_time=0.0,  # Will be updated after execution
            timestamp=time.time(),
            risk_level=risk_level
        )
        memory.store_command(history)

    executor.present_and_act(
        command,
        ctx,
        conf,
        session_id
    )


def _pick_spinner(query: str) -> tuple[str, str]:
    """Choose spinner style and label based on what the query is asking for."""
    q = query.lower()

    if any(w in q for w in ("find", "search", "look", "locate", "where", "list")):
        return "dots2", "Searching…"

    if any(w in q for w in ("install", "download", "pull", "clone", "get")):
        return "bouncingBar", "Preparing…"

    if any(w in q for w in ("delete", "remove", "clean", "kill", "stop", "terminate")):
        return "noise", "Thinking…"

    if any(w in q for w in ("show", "display", "print", "cat", "read", "open")):
        return "dots8", "Reading…"

    if any(w in q for w in ("move", "copy", "rename", "zip", "tar", "compress")):
        return "line", "Working…"

    if any(w in q for w in ("git", "commit", "push", "pull", "merge", "branch")):
        return "dots12", "Git…"

    if any(w in q for w in ("run", "start", "launch", "execute", "deploy")):
        return "arrow3", "Launching…"

    return "dots", "Thinking…"


def _build_prompt(ctx: dict, conf: dict = None) -> Text:
    t = Text()
    t.append("\n  ", style="")
    t.append(ctx["cwd"].replace(f"/Users/{_username()}", "~"), style=f"bold {CWD}")
    t.append("  ", style="")
    t.append(ctx["shell"], style=SHELL_LABEL)
    
    # Add mode indicator to prompt if enabled
    if conf and conf.get('behavior', {}).get('show_mode_indicator', True):
        mode = conf.get('behavior', {}).get('mode', 'cautious')
        mode_symbol = "⚡" if mode == 'turbo' else "⚠"
        mode_color = 'green' if mode == 'turbo' else 'yellow'
        t.append(f"  [{mode_color}]{mode_symbol}[/{mode_color}]", style="")
    
    t.append("\n  ", style="")
    t.append("› ", style=f"bold {ACCENT}")
    return t


def _username() -> str:
    import os
    return os.environ.get("USER", "")


def _print_help(conf: dict = None) -> None:
    console.print()
    console.print("  [bold]Session commands:[/bold]\n")
    console.print(f"  [bold {ACCENT}]exit[/bold {ACCENT}] [{FG_DIM}]/ quit / Ctrl+C[/{FG_DIM}]   End the session")
    console.print(f"  [bold {ACCENT}]clear[/bold {ACCENT}]                  Clear the screen")
    console.print(f"  [bold {ACCENT}]help[/bold {ACCENT}]                   Show this message")
    console.print(f"  [bold {ACCENT}]status[/bold {ACCENT}]                 Show session status")
    
    if conf:
        current_mode = conf.get('behavior', {}).get('mode', 'cautious')
        other_mode = 'turbo' if current_mode == 'cautious' else 'cautious'
        console.print(f"  [bold {ACCENT}]{other_mode}[/bold {ACCENT}]                   Switch to {other_mode} mode")
    
    console.print()
    console.print("  [bold]Query examples:[/bold]\n")
    console.print(f"  [{FG_DIM}]find all log files older than 7 days[/{FG_DIM}]")
    console.print(f"  [{FG_DIM}]show disk usage of current folder[/{FG_DIM}]")
    console.print(f"  [{FG_DIM}]undo last git commit[/{FG_DIM}]")
    console.print(f"  [{FG_DIM}]kill the process on port 3000[/{FG_DIM}]")
    console.print(f"  [{FG_DIM}]what are you[/{FG_DIM}]                 Ask about Root's identity")
    console.print()


def _farewell(session_id: int = None, conf: dict = None, show_message: bool = True) -> None:
    if show_message:
        console.print()
        
        # Show session summary if memory is enabled
        if session_id and conf and conf.get('memory', {}).get('enabled', True):
            from root.memory import get_memory_manager
            memory = get_memory_manager()
            summary = memory.get_session_summary(session_id)
            
            if summary:
                console.print(f"  [{FG_DIM}]Session summary:[/{FG_DIM}]")
                console.print(f"  [{FG_DIM}]Commands executed: {summary['commands_executed']}[/{FG_DIM}]")
                console.print(f"  [{FG_DIM}]Success rate: {summary['success_rate']:.1%}[/{FG_DIM}]")
                console.print(f"  [{FG_DIM}]Mode: {summary['mode']}[/{FG_DIM}]")
                console.print()
        
        console.print(f"  [{FG_DIM}]Goodbye.[/{FG_DIM}]\n")


def _switch_mode(new_mode: str, conf: dict, session_id: int = None) -> None:
    """Switch between cautious and turbo modes."""
    old_mode = conf.get('behavior', {}).get('mode', 'cautious')
    
    if old_mode == new_mode:
        console.print(f"  [{FG_DIM}]Already in {new_mode} mode.[/{FG_DIM}]\n")
        return
    
    # Update config
    conf['behavior']['mode'] = new_mode
    cfg.save(conf)
    
    # Update session if memory is enabled
    if session_id and conf.get('memory', {}).get('enabled', True):
        from root.memory import get_memory_manager
        memory = get_memory_manager()
        # Note: This would require updating the session_stats table to allow mode changes
        # For now, we'll just show the change
    
    mode_color = 'green' if new_mode == 'turbo' else 'yellow'
    console.print(f"  [{mode_color}]Switched to {new_mode.upper()} mode[/{mode_color}]\n")
    
    if new_mode == 'turbo':
        console.print(f"  [{FG_DIM}]All commands will now auto-run.[/{FG_DIM}]\n")
    else:
        console.print(f"  [{FG_DIM}]Dangerous commands will require confirmation.[/{FG_DIM}]\n")


def _show_status(session_id: int = None, conf: dict = None) -> None:
    """Show current session status."""
    console.print()
    console.print(f"  [bold]Root Status[/bold]\n")
    
    if conf:
        mode = conf.get('behavior', {}).get('mode', 'cautious')
        memory_enabled = conf.get('memory', {}).get('enabled', True)
        learning_enabled = conf.get('memory', {}).get('learn_patterns', True)
        
        mode_color = 'green' if mode == 'turbo' else 'yellow'
        console.print(f"  [{FG_MUTED}]Mode:[/{FG_MUTED}]           [{mode_color}]{mode.upper()}[/{mode_color}]")
        console.print(f"  [{FG_MUTED}]Memory:[/{FG_MUTED}]          {'enabled' if memory_enabled else 'disabled'}")
        console.print(f"  [{FG_MUTED}]Learning:[/{FG_MUTED}]         {'enabled' if learning_enabled else 'disabled'}")
    
    if session_id and conf and conf.get('memory', {}).get('enabled', True):
        from root.memory import get_memory_manager
        memory = get_memory_manager()
        summary = memory.get_session_summary(session_id)
        
        if summary:
            console.print(f"  [{FG_MUTED}]Commands run:[/{FG_MUTED}]     {summary['commands_executed']}")
            console.print(f"  [{FG_MUTED}]Success rate:[/{FG_MUTED}]    {summary['success_rate']:.1%}")
    
    console.print()
