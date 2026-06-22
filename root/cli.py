import sys
import time

import click
from rich.console import Console
from rich.padding import Padding
from rich.text import Text

from root import __version__
from root import config as cfg
from root import context
from root.backends import ollama
from root.theme import ACCENT, ACCENT_DIM, SUCCESS, WARNING, ERROR, FG_DIM, FG_MUTED

console = Console()

MODEL_DEFAULT = "hf.co/albinab/Qwen-0.5B-Coder-El-Terminalo:latest"
OLLAMA_INSTALL_URL = "https://ollama.com"


class RootGroup(click.Group):
    """Custom group that treats unknown subcommands as natural language queries."""

    def parse_args(self, ctx, args):
        # Handle -p / --prompt flag: root -p find python files
        cleaned = list(args)
        if cleaned and cleaned[0] in ("-p", "--prompt"):
            cleaned.pop(0)
            ctx.meta["raw_args"] = cleaned
            ctx.meta["is_query"] = True
            return []

        # Bare unquoted usage: root find python files
        # Route to query if first token isn't a known flag or subcommand
        ctx.meta["raw_args"] = list(args)
        if cleaned and not cleaned[0].startswith("-") and cleaned[0] not in self.commands:
            ctx.meta["is_query"] = True
            return []

        return super().parse_args(ctx, args)

    def invoke(self, ctx):
        if ctx.meta.get("is_query"):
            raw = ctx.meta.get("raw_args", [])
            if raw:
                _translate_and_act(" ".join(raw))
            else:
                console.print("\n  [yellow]No query provided.[/yellow]  Try:  root find python files\n")
            return
        super().invoke(ctx)


@click.group(cls=RootGroup, invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version and exit.")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """Root — type plain English, get the right shell command.\n
    \b
    Usage:
      root                          start interactive session
      root find files over 100MB    one-shot query, no quotes needed
      root -p setup the git config  use -p for reserved words
      root setup                    first-time setup
      root config                   view/edit config
    """
    if version:
        console.print(f"root v{__version__} by Fisarum")
        return

    if ctx.invoked_subcommand is None and not ctx.meta.get("is_query"):
        from root.session import start
        start()


@main.command()
def setup() -> None:
    """Check dependencies and pull the model. Run this once after installing."""
    console.print()
    console.print(f"  [bold]Root Setup[/bold]  by [bold {ACCENT}]Fisarum[/bold {ACCENT}]\n")

    conf = cfg.load()
    host = conf["ollama"]["host"]
    model = conf["ollama"]["model"]

    # Step 1: Check ollama
    console.print(f"  [{FG_DIM}]1/2[/{FG_DIM}]  Checking Ollama…", end=" ")
    if ollama.is_available(host):
        console.print(f"[bold {SUCCESS}]✓[/bold {SUCCESS}]  Running")
    else:
        console.print(f"[bold {ERROR}]✗[/bold {ERROR}]  Not found\n")
        console.print(
            f"  [{WARNING}]Ollama is not running or not installed.[/{WARNING}]\n"
            f"  Install it from [link={OLLAMA_INSTALL_URL}]{OLLAMA_INSTALL_URL}[/link]\n"
            f"  Then run: [bold]ollama serve[/bold]\n"
        )
        sys.exit(1)

    # Step 2: Check / pull model
    console.print(f"  [{FG_DIM}]2/2[/{FG_DIM}]  Checking model [{ACCENT_DIM}]{model}[/{ACCENT_DIM}]…", end=" ")
    existing = ollama.list_models(host)

    model_present = any(
        m == model or m.startswith(model.split(":")[0])
        for m in existing
    )

    if model_present:
        console.print(f"[bold {SUCCESS}]✓[/bold {SUCCESS}]  Already downloaded")
    else:
        console.print(f"[{WARNING}]not found[/{WARNING}]  — pulling now…\n")
        console.print(
            f"  [{FG_DIM}]Downloading {model} (~500MB). This is a one-time step.[/{FG_DIM}]\n"
        )
        try:
            import subprocess, shutil
            if not shutil.which("ollama"):
                raise RuntimeError("ollama binary not in PATH")
            console.print("  ", end="")
            subprocess.run(["ollama", "pull", model], check=True)
            console.print()
        except Exception as e:
            console.print(f"\n  [{ERROR}]Failed to pull model: {e}[/{ERROR}]")
            console.print(
                f"  Try manually:  [bold]ollama pull {model}[/bold]\n"
            )
            sys.exit(1)

    cfg.init_defaults()

    console.print()
    console.print(f"  [bold {SUCCESS}]✓  Setup complete.[/bold {SUCCESS}]  You're ready to go.\n")
    console.print(f"  Try it:  [bold {ACCENT}]root[/bold {ACCENT}]  to start a session\n")


@main.command("config")
@click.option("--backend", type=click.Choice(["ollama", "openai"]), help="Set backend.")
@click.option("--model", help="Set model name.")
@click.option("--api-key", help="Set OpenAI-compatible API key.")
@click.option("--show", is_flag=True, help="Print current config.")
def config_cmd(backend: str, model: str, api_key: str, show: bool) -> None:
    """View or update Root configuration."""
    conf = cfg.load()

    if show or (not backend and not model and not api_key):
        _print_config(conf)
        return

    if backend:
        conf["backend"] = backend
        console.print(f"  Backend set to [{ACCENT_DIM}]{backend}[/{ACCENT_DIM}]")

    if model:
        active = conf.get("backend", "ollama")
        conf[active]["model"] = model
        console.print(f"  Model set to [{ACCENT_DIM}]{model}[/{ACCENT_DIM}]")

    if api_key:
        conf["openai"]["api_key"] = api_key
        console.print(f"  OpenAI API key saved.")

    cfg.save(conf)
    console.print(f"  [{FG_DIM}]Config saved to ~/.root/config.toml[/{FG_DIM}]")


@main.command("mode")
@click.argument("mode_name", type=click.Choice(["cautious", "turbo"]))
def mode_cmd(mode_name: str) -> None:
    """Switch between cautious and turbo modes."""
    conf = cfg.load()
    current_mode = conf.get("behavior", {}).get("mode", "cautious")
    
    if current_mode == mode_name:
        console.print(f"  [{FG_DIM}]Already in {mode_name} mode.[/{FG_DIM}]")
        return
    
    conf["behavior"]["mode"] = mode_name
    cfg.save(conf)
    
    mode_color = "green" if mode_name == "turbo" else "yellow"
    console.print(f"  [{mode_color}]Switched to {mode_name.upper()} mode[/{mode_color}]")
    
    if mode_name == "turbo":
        console.print(f"  [{FG_DIM}]All commands will now auto-run.[/{FG_DIM}]")
    else:
        console.print(f"  [{FG_DIM}]Dangerous commands will require confirmation.[/{FG_DIM}]")


@main.command("memory")
@click.option("--clear", is_flag=True, help="Clear all memory data.")
@click.option("--stats", is_flag=True, help="Show memory statistics.")
@click.option("--disable", is_flag=True, help="Disable memory system.")
@click.option("--enable", is_flag=True, help="Enable memory system.")
def memory_cmd(clear: bool, stats: bool, disable: bool, enable: bool) -> None:
    """Manage Root's memory and learning system."""
    conf = cfg.load()
    
    if clear:
        try:
            from root.memory import get_memory_manager
            memory = get_memory_manager()
            # Clear memory by deleting the database file
            import os
            from root.memory import MEMORY_DB
            if MEMORY_DB.exists():
                os.remove(MEMORY_DB)
                console.print(f"  [{SUCCESS}]Memory cleared successfully.[/{SUCCESS}]")
            else:
                console.print(f"  [{FG_DIM}]No memory data to clear.[/{FG_DIM}]")
        except Exception as e:
            console.print(f"  [{ERROR}]Failed to clear memory: {e}[/{ERROR}]")
        return
    
    if disable:
        conf["memory"]["enabled"] = False
        cfg.save(conf)
        console.print(f"  [{WARNING}]Memory system disabled.[/{WARNING}]")
        return
    
    if enable:
        conf["memory"]["enabled"] = True
        cfg.save(conf)
        console.print(f"  [{SUCCESS}]Memory system enabled.[/{SUCCESS}]")
        return
    
    if stats:
        try:
            from root.memory import get_memory_manager
            memory = get_memory_manager()
            
            # Get basic stats (would need to implement these methods)
            console.print(f"  [bold]Memory Statistics[/bold]\n")
            console.print(f"  [{FG_MUTED}]Status:[/{FG_MUTED}]         {'enabled' if conf.get('memory', {}).get('enabled', True) else 'disabled'}")
            console.print(f"  [{FG_MUTED}]Learning:[/{FG_MUTED}]        {'enabled' if conf.get('memory', {}).get('learn_patterns', True) else 'disabled'}")
            console.print(f"  [{FG_MUTED}]Database file:[/{FG_MUTED}]   ~/.root/memory.db")
            console.print()
        except Exception as e:
            console.print(f"  [{ERROR}]Failed to get memory stats: {e}[/{ERROR}]")
        return
    
    # Show current memory configuration
    console.print()
    console.print(f"  [bold]Memory Configuration[/bold]  [{FG_DIM}](~/.root/config.toml)[/{FG_DIM}]\n")
    
    memory_conf = conf.get("memory", {})
    console.print(f"  [{FG_MUTED}]enabled[/{FG_MUTED}]           [{'green' if memory_conf.get('enabled', True) else 'red'}]{memory_conf.get('enabled', True)}[/{'green' if memory_conf.get('enabled', True) else 'red'}]")
    console.print(f"  [{FG_MUTED}]learn_patterns[/{FG_MUTED}]     [{'green' if memory_conf.get('learn_patterns', True) else 'red'}]{memory_conf.get('learn_patterns', True)}[/{'green' if memory_conf.get('learn_patterns', True) else 'red'}]")
    console.print(f"  [{FG_MUTED}]learn_preferences[/{FG_MUTED}]  [{'green' if memory_conf.get('learn_preferences', True) else 'red'}]{memory_conf.get('learn_preferences', True)}[/{'green' if memory_conf.get('learn_preferences', True) else 'red'}]")
    console.print(f"  [{FG_MUTED}]max_history_days[/{FG_MUTED}]   {memory_conf.get('max_history_days', 30)}")
    console.print()
    console.print("  Use --stats to see usage statistics")
    console.print("  Use --clear to clear all memory data")


@main.command("plugins")
@click.option("--install", is_flag=True, help="Show install commands for missing plugins.")
def plugins_cmd(install: bool) -> None:
    """List available plugins and their status."""
    from root.plugins import get_registry
    registry = get_registry()
    all_plugins = registry.all()

    console.print()
    console.print(f"  [bold]Root Plugins[/bold]  [{FG_DIM}]({len(all_plugins)} registered)[/{FG_DIM}]\n")

    for p in all_plugins:
        available = p.is_available()
        status_color = "green" if available else "red"
        status_icon = "✓" if available else "✗"
        enriches = ", ".join(p.info.enriches) if p.info.enriches else "—"

        console.print(
            f"  [{status_color}]{status_icon}[/{status_color}]  "
            f"[bold]{p.info.name}[/bold]  [{FG_DIM}]{p.info.description}[/{FG_DIM}]"
        )
        if p.info.enriches:
            console.print(f"     [{FG_MUTED}]enriches:[/{FG_MUTED}] {enriches}")
        if not available and install:
            console.print(f"     [{WARNING}]install:[/{WARNING}] {p.info.install_hint}")

    available_count = len(registry.available())
    console.print()
    console.print(
        f"  [{FG_DIM}]{available_count}/{len(all_plugins)} installed  ·  "
        f"Run [bold]root plugins --install[/bold] to see install commands.[/{FG_DIM}]\n"
    )


def _print_config(conf: dict) -> None:
    console.print()
    console.print(f"  [bold]Root Config[/bold]  [{FG_DIM}](~/.root/config.toml)[/{FG_DIM}]\n")

    backend = conf.get("backend", "ollama")
    console.print(f"  [{FG_MUTED}]backend[/{FG_MUTED}]   [{ACCENT_DIM}]{backend}[/{ACCENT_DIM}]")

    if backend == "ollama":
        console.print(f"  [{FG_MUTED}]host[/{FG_MUTED}]      [{FG_DIM}]{conf['ollama']['host']}[/{FG_DIM}]")
        console.print(f"  [{FG_MUTED}]model[/{FG_MUTED}]     [bold {ACCENT}]{conf['ollama']['model']}[/bold {ACCENT}]")
    else:
        console.print(f"  [{FG_MUTED}]base_url[/{FG_MUTED}]  [{FG_DIM}]{conf['openai']['base_url']}[/{FG_DIM}]")
        console.print(f"  [{FG_MUTED}]model[/{FG_MUTED}]     [bold {ACCENT}]{conf['openai']['model']}[/bold {ACCENT}]")
        key = conf["openai"].get("api_key", "")
        masked = (key[:6] + "…") if len(key) > 6 else (f"[{FG_DIM}]not set[/{FG_DIM}]")
        console.print(f"  [{FG_MUTED}]api_key[/{FG_MUTED}]   {masked}")

    # Show behavior settings
    behavior = conf.get("behavior", {})
    mode = behavior.get("mode", "cautious")
    mode_color = "green" if mode == "turbo" else "yellow"
    console.print(f"  [{FG_MUTED}]mode[/{FG_MUTED}]       [{mode_color}]{mode.upper()}[/{mode_color}]")
    console.print(f"  [{FG_MUTED}]auto_trust_safe[/{FG_MUTED}]   [{'green' if behavior.get('auto_trust_safe_commands', True) else 'red'}]{behavior.get('auto_trust_safe_commands', True)}[/{'green' if behavior.get('auto_trust_safe_commands', True) else 'red'}]")
    console.print(f"  [{FG_MUTED}]auto_trust_moderate[/{FG_MUTED}] [{'green' if behavior.get('auto_trust_moderate_commands', False) else 'red'}]{behavior.get('auto_trust_moderate_commands', False)}[/{'green' if behavior.get('auto_trust_moderate_commands', False) else 'red'}]")
    
    # Show memory settings
    memory = conf.get("memory", {})
    console.print(f"  [{FG_MUTED}]memory_enabled[/{FG_MUTED}] [{'green' if memory.get('enabled', True) else 'red'}]{memory.get('enabled', True)}[/{'green' if memory.get('enabled', True) else 'red'}]")
    console.print(f"  [{FG_MUTED}]learning_enabled[/{FG_MUTED}] [{'green' if memory.get('learn_patterns', True) else 'red'}]{memory.get('learn_patterns', True)}[/{'green' if memory.get('learn_patterns', True) else 'red'}]")

    console.print()
    console.print("  Change backend:  root config --backend openai")
    console.print("  Change model:    root config --model <name>")
    console.print("  Switch mode:     root mode <cautious|turbo>")
    console.print("  Manage memory:   root memory [--stats|--clear]")


def _translate_and_act(query: str) -> None:
    from root import translate
    from root import executor

    conf = cfg.load()
    ctx = context.detect()
    
    # Initialize memory if enabled
    session_id = None
    if conf.get('memory', {}).get('enabled', True):
        from root.memory import get_memory_manager
        memory = get_memory_manager()
        mode = conf.get('behavior', {}).get('mode', 'cautious')
        session_id = memory.start_session(mode)

    with console.status(f"  [{FG_DIM}]Thinking…[/{FG_DIM}]", spinner="dots"):
        try:
            command = translate.translate(query, ctx)
        except Exception as e:
            console.print(f"\n  [{ERROR}]Error:[/{ERROR}] {e}\n")
            _suggest_setup(conf)
            sys.exit(1)

    if not command:
        console.print(f"\n  [{WARNING}]No command generated. Try rephrasing.[/{WARNING}]\n")
        return

    # Store command in memory if enabled
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


def _suggest_setup(conf: dict) -> None:
    if conf.get("backend", "ollama") == "ollama":
        console.print(
            "  [dim]If this is your first time, run:[/dim]  [bold]root setup[/bold]\n"
        )
