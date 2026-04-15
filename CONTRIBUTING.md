# Contributing to ansifuzz

Contributions are welcome. Please follow the guidelines below.

## Development setup

```bash
git clone https://github.com/chrisvanmeer/ansifuzz
cd ansifuzz
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

## Code style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Type annotations on all public functions
- Run `ruff check .` before submitting a PR

## Submitting changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests where applicable
4. Commit with a clear message following [Conventional Commits](https://www.conventionalcommits.org/)
5. Push and open a Pull Request against `main`

## Reporting issues

Open an issue on GitHub and include:
- Your OS and Python version
- Your fzf version (`fzf --version`)
- The command you ran and the error output
