from root import config as cfg
from root.backends import ollama, openai

SYSTEM_PROMPT = """\
You are a shell command translator for the Root CLI by Fisarum.
Your ONLY job: convert a natural language request into ONE shell command.

STRICT OUTPUT RULES:
- Output ONLY the raw shell command. One line. No prose, no markdown, no backticks, no comments.
- NEVER output "CLARIFY", "REFUSE", or any English text unless the REFUSE rule applies.
- NEVER ask a question. NEVER say you need more information. Just produce the best command.
- If the request is not a shell task (e.g. "what are you", "what type of project is this"), output: echo "I only translate requests into shell commands. Try: list files, show disk usage, find large files."
- Only output REFUSE if the command would do catastrophic irreversible damage: rm -rf /, fork bomb, wipe disk, rm system files, escalate privileges without cause.
- Creating folders, listing files, showing info, git commands, finding files — these are ALL safe. Never refuse them.

COMMAND RULES:
- Use the correct syntax for the OS and shell shown in the context below.
- For filesystem scans (find, du, ls -R, locate), always append 2>/dev/null.
- To list files in current folder: ls -la
- To find files by name: find . -name "*.ext" 2>/dev/null
- To find files by size: find . -size +100M 2>/dev/null
- To find files with more than N lines: find . -name "*.ext" 2>/dev/null | xargs wc -l 2>/dev/null | awk '$1 > N' | sort -rn
- To create a folder: mkdir -p <path>
- To show project type: ls -la && cat README.md 2>/dev/null || ls -la

EXAMPLES:
request: list the files in this folder
command: ls -la

request: find all json files
command: find . -name "*.json" 2>/dev/null

request: find json files with over 70 lines
command: find . -name "*.json" 2>/dev/null | xargs wc -l 2>/dev/null | awk '$1 > 70 {print $2}' | sort

request: create a folder named Test1 on the desktop
command: mkdir -p ~/Desktop/Test1

request: show disk usage of current folder
command: du -sh .

request: what type of project is this
command: echo "$(ls -1 | head -20)" && cat README.md 2>/dev/null | head -10

request: show git status
command: git status
"""


def _plugin_hints() -> str:
    """Build a short hint block listing installed plugin tools for the system prompt."""
    try:
        from root.plugins import get_registry
        available = [p.info.binary for p in get_registry().available()]
        if not available:
            return ""
        tools = ", ".join(available)
        lines = [
            f"\nINSTALLED POWER TOOLS (prefer these when appropriate): {tools}",
            "- If fd is installed, prefer: fd --extension <ext>  over  find . -name",
            "- If bat is installed, prefer: bat <file>  over  cat <file>  for text files",
            "- If fzf is installed, you may pipe list/find output through fzf for interactive selection",
            "- If glow is installed, prefer: glow <file>.md  over  cat <file>.md",
            "- If yt-dlp is installed, use it for video/audio download requests",
            "- If sherlock is installed, use it for social media username lookups",
        ]
        return "\n".join(lines)
    except Exception:
        return ""


def translate(query: str, context: dict) -> str:
    """Translate a natural language query into a shell command."""
    conf = cfg.load()
    
    # Check for self-awareness queries first
    if _is_identity_query(query):
        return _generate_identity_response(conf, query)
    
    # Check for learned patterns
    if conf.get('memory', {}).get('learn_patterns', True):
        learned_command = _check_learned_patterns(query, context)
        if learned_command:
            return learned_command

    system = SYSTEM_PROMPT + _plugin_hints() + f"\n{_format_context(context)}"
    prompt = f"request: {query.strip()}\ncommand:"

    backend = conf.get("backend", "ollama")

    if backend == "ollama":
        raw = ollama.generate(
            host=conf["ollama"]["host"],
            model=conf["ollama"]["model"],
            prompt=prompt,
            system=system,
        )
        return _clean(raw)

    if backend == "openai":
        api_key = conf["openai"].get("api_key") or ""
        if not api_key:
            raise ValueError(
                "OpenAI API key not set.\n"
                "Add it to ~/.root/config.toml under [openai] api_key = \"sk-...\""
            )
        raw = openai.generate(
            base_url=conf["openai"]["base_url"],
            model=conf["openai"]["model"],
            api_key=api_key,
            prompt=prompt,
            system=system,
        )
        return _clean(raw)

    raise ValueError(f"Unknown backend '{backend}'. Use 'ollama' or 'openai'.")


def _clean(raw: str) -> str:
    """Strip markdown, echoed prefixes, and leading/trailing whitespace."""
    text = raw.strip()
    # Strip code fences
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            l for l in lines
            if not l.startswith("```")
        ).strip()
    # Strip inline backticks
    text = text.strip("`")
    # Strip echoed "command:" prefix the model sometimes emits
    if text.lower().startswith("command:"):
        text = text[len("command:"):].strip()
    # Take only the first line if model produced multiple lines of prose
    # (but keep pipelines and multi-part commands on one line)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        text = lines[0]
    return text


def _format_context(ctx: dict) -> str:
    return f"OS: {ctx['os']} | Shell: {ctx['shell']} | CWD: {ctx['cwd']}"


def _is_identity_query(query: str) -> bool:
    """Check if the query is asking about the agent's identity or is conversational."""
    identity_patterns = [
        "what are you",
        "who are you", 
        "what is root",
        "describe yourself",
        "what can you do",
        "what is your purpose",
        "what are your capabilities",
        "tell me about yourself",
        "what kind of agent are you",
        "are you an ai",
        "are you a bot",
        "what is this tool",
        "what is this program",
        # Conversational patterns
        "hello",
        "hi",
        "hey",
        "greetings",
        "how are you",
        "settings",  # Handle this as conversational
        "help me",
        "what can you help with",
        "introduce yourself",
    ]
    
    query_lower = query.lower().strip()
    return any(pattern in query_lower for pattern in identity_patterns)


def _generate_identity_response(config: dict, query: str = "") -> str:
    """Generate an identity response based on configuration and query type."""
    identity = config.get('agent', {}).get('identity_response', 'I am Root, a native CLI micro agent')
    mode = config.get('behavior', {}).get('mode', 'cautious')
    show_capabilities = config.get('agent', {}).get('show_capabilities', True)
    
    query_lower = query.lower().strip()
    
    # Handle basic greetings
    if query_lower in ["hello", "hi", "hey", "greetings"]:
        return f'echo "Hello! I\'m Root, your CLI assistant. Try asking me to do something like \'list files\' or ask \'what are you?\'"'
    
    # Handle "how are you"
    if "how are you" in query_lower:
        return f'echo "I\'m working perfectly! Ready to help you with shell commands. Currently in {mode} mode."'
    
    # Handle "settings" as conversational
    if query_lower == "settings":
        return f'echo "I\'m Root, your CLI assistant! You can check my settings with: root config. Change modes with: root mode <cautious|turbo>"'
    
    # Handle "help me" or similar
    if "help me" in query_lower or "what can you help with" in query_lower:
        return f'echo "I can help you with shell commands! Try: list files, find large files, show disk usage, or ask \'what are you?\'"'
    
    # Default identity response
    response_parts = [f'echo "{identity}"']
    
    if show_capabilities:
        capabilities = [
            "I translate natural language to shell commands",
            f"Currently in {mode} mode",
            "I learn from your interactions",
            "I assess command risk levels"
        ]
        capabilities_text = " | ".join(capabilities)
        response_parts.append(f'echo "Capabilities: {capabilities_text}"')
    
    return " && ".join(response_parts)


def _check_learned_patterns(query: str, context: dict) -> str:
    """Check if we have a learned pattern for this query."""
    try:
        from root.memory import get_memory_manager
        memory = get_memory_manager()
        pattern = memory.get_best_pattern(query, context)
        
        if pattern:
            # Apply context variables to the template
            command = pattern.command_template
            
            # Simple template substitution - can be enhanced
            if '{cwd}' in command:
                command = command.replace('{cwd}', context.get('cwd', '.'))
            if '{user}' in command:
                import os
                command = command.replace('{user}', os.environ.get('USER', 'user'))
                
            return command
    except Exception:
        # If memory fails, fall back to normal translation
        pass
    
    return None
