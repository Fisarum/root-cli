# root

**Type plain English in any terminal. Get the right shell command.**

Built by [Fisarum](https://fisarum.com). Works on macOS, Linux, and Windows.

```
$ root find all python files modified in the last 3 days

  ✓  Risk level: safe

  find . -name "*.py" -mtime -3

  [r]un  [q]uit  >
```

No cloud. No API key. Runs entirely on your machine using a small local model (~500MB).

## 🚀 New: Intelligent CLI Agent

Root is now an intelligent CLI agent that learns from your interactions and adapts to your workflow.

### Key Features

- **Memory & Learning**: Remembers successful commands and learns your preferences
- **Risk Assessment**: Automatically evaluates command danger levels (safe/moderate/dangerous)
- **Dual Modes**: Cautious mode for safety, Turbo mode for speed
- **Self-Aware**: Responds to identity queries like "what are you?"
- **Session Intelligence**: Tracks success rates and adapts to your patterns

---

## Install

```bash
pip install root-cli
```

Then run setup once (downloads the model via [Ollama](https://ollama.com)):

```bash
root setup
```

---

## Usage

```bash
root list all files bigger than 100MB
root kill the process using port 3000
root show disk usage sorted by size
root create a tar.gz of the src folder
root undo the last git commit but keep changes
```

Or use the `-p` flag when your query starts with a word that could conflict:

```bash
root -p setup my git config with my name and email
root -p config nginx to redirect http to https
```

After translation you get simplified choices:

| Key | Action |
|-----|--------|
| `r` | Run the command immediately |
| `q` | Abort |

**Risk Assessment**: Root automatically evaluates command risk levels:
- ✓ **Safe**: Common read-only commands (ls, cat, find, etc.)
- ⚠ **Moderate**: Commands that modify files or use sudo
- ⚡ **Dangerous**: Destructive commands (rm -rf, format, etc.)

---

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com) installed and running (`ollama serve`)

First-time setup pulls the model automatically:

```bash
root setup
```

---

## Configuration

```bash
root config           # view current config
root config --backend openai --model gpt-4o-mini
root config --api-key sk-...
```

### Mode Management

```bash
root mode cautious    # switch to cautious mode (default)
root mode turbo       # switch to turbo mode (auto-run all commands)
```

**Cautious Mode**: Asks for permission on dangerous commands
**Turbo Mode**: Auto-runs all commands without confirmation

### Memory Management

```bash
root memory            # view memory configuration
root memory --stats    # show learning statistics
root memory --clear    # clear all learning data
root memory --disable  # disable learning system
root memory --enable   # enable learning system
```

### Session Commands

When in interactive mode, you can use:

```bash
help                  # show help and available commands
status                # show current session status
cautious / turbo      # switch modes instantly
clear                 # clear the screen
exit / quit           # end the session
```

Config is stored at `~/.root/config.toml`.

### Switch to OpenAI (or any compatible API)

```toml
backend = "openai"

[openai]
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
api_key = "sk-..."
```

Works with any OpenAI-compatible endpoint (Groq, Together, Mistral, local llama-server, etc.).

---

## How it works

1. **Context Detection**: Detects your OS, shell, and current directory automatically
2. **Self-Awareness**: Checks if you're asking about Root's identity
3. **Pattern Learning**: Looks for learned patterns from your previous commands
4. **Translation**: Sends your query + context to a local 0.5B model via Ollama
5. **Risk Assessment**: Evaluates command danger level automatically
6. **Memory Storage**: Stores successful commands for future learning
7. **Smart Execution**: Auto-runs safe commands or asks for confirmation based on mode

The model never sends data anywhere. Everything runs locally, including your memory and learning data.

### Self-Awareness

Root can identify itself and explain its capabilities:

```bash
$ root what are you

I am Root, a native CLI micro agent
Capabilities: I translate natural language to shell commands | Currently in cautious mode | I learn from your interactions | I assess command risk levels
```

### Learning System

Root learns from your interactions:

- **Command Patterns**: Remembers successful command patterns for similar queries
- **User Preferences**: Adapts to your preferred command styles
- **Risk Awareness**: Learns which commands you consider safe vs dangerous
- **Session Statistics**: Tracks success rates and provides insights

---

## Contributing

Root is an open-source project by [Fisarum](https://fisarum.com). Contributions are welcome.

- Read the [Contributing Guide](CONTRIBUTING.md) to get started.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).
- Report security issues privately per the [Security Policy](.github/SECURITY.md).
- Use [GitHub Issues](https://github.com/fisarum/root-cli/issues) for bugs and feature requests.
- Join [GitHub Discussions](https://github.com/fisarum/root-cli/discussions) for questions and feedback.

---

## License

MIT — see [LICENSE](LICENSE)

---

*root is an open-source project by [Fisarum](https://fisarum.com)*
