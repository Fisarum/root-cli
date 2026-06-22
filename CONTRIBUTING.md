# Contributing to Root

Thank you for your interest in contributing to Root! This guide will help you get started.

## Ways to contribute

- **Report bugs** or **request features** via [GitHub Issues](https://github.com/fisarum/root-cli/issues).
- **Improve documentation**, fix typos, or clarify the README.
- **Submit bug fixes or new features** via [Pull Requests](https://github.com/fisarum/root-cli/pulls).
- **Share feedback and ideas** in [GitHub Discussions](https://github.com/fisarum/root-cli/discussions).

## Development setup

1. Clone the repository:
   ```bash
   git clone https://github.com/fisarum/root-cli.git
   cd root-cli
   ```
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install Root in editable mode:
   ```bash
   pip install -e .
   ```
4. Verify the installation:
   ```bash
   root --help
   ```

## Code style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- Keep changes focused and minimal.
- Add or update tests for new behavior when possible.
- Write clear, descriptive commit messages.

## Pull request process

1. **Open an issue first** for significant changes or new features.
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make focused commits** with clear messages.
4. **Ensure the package still installs** and `root --help` works.
5. **Fill out the PR template** when opening your pull request.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## Questions?

Join the conversation in [GitHub Discussions](https://github.com/fisarum/root-cli/discussions) or reach out at hello@fisarum.com.
