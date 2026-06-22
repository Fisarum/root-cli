# Security Policy

## Supported versions

We support the latest published release on PyPI and the current `main` branch of this repository.

## Reporting a vulnerability

If you discover a security vulnerability in Root, please report it privately rather than opening a public issue.

- Email **hello@fisarum.com** with the subject `[root-cli] Security issue`.
- Include a clear description of the vulnerability and the steps to reproduce it, if possible.
- Allow us reasonable time to investigate and address the issue before disclosing it publicly.

We will respond as soon as possible and coordinate a fix and disclosure timeline with you.

## What to report

- Code execution vulnerabilities triggered by malicious user input.
- Leaks of sensitive data (API keys, local files, environment variables) through model prompts or logging.
- Weaknesses in the risk assessment or command execution flow that could lead to unsafe commands being run without confirmation.

## Safe default behavior

Root is designed to run a local model and execute commands on your machine. Always review commands before running them, especially in `turbo` mode or when using a remote backend.
