# Contributing

Thanks for your interest in improving this project. This file explains how to set up a development environment and run tests.

## Development setup

1. Create a virtual environment and install pinned dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.pinned.txt
```

2. Run the CLI to make sure everything is working:

```bash
python cli.py --keyword Tesla --num-articles 5
```

## Tests

Add tests to the `tests/` directory and run them with `pytest`:

```bash
pip install pytest
pytest
```

## Style

- Keep functions small and focused.
- Use logging rather than print statements.
- Avoid committing secret keys. Use `.env` for local testing and CI secrets for automated workflows.

## Submitting changes

- Fork the repository, create a feature branch, make changes, and submit a pull request.
- Include tests for new behavior where feasible.
