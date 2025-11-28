# Repository Guidelines

This project is a Streamlit application that converts SQL DDL into Chen-style ER diagrams.

## Project Structure & Module Organization

- `app.py`: main application, including SQL parsing, data models, ER generation, and Streamlit UI.
- `requirements.txt`: Python dependencies (Streamlit, sqlparse, graphviz).
- `*.png`: generated ER diagram images for ad hoc testing; avoid committing large collections of test outputs.

Future modules (e.g., `sql_parser.py`, `er_renderer.py`) should live in the repository root or a `src/` package. Keep pure parsing/graph logic separate from UI code.

## Build, Test, and Development Commands

- Use Python 3.10+ and create a virtual environment: `python -m venv .venv` then activate it.
- Install dependencies: `pip install -r requirements.txt`.
- Run the app locally: `streamlit run app.py` (opens in a browser at `http://localhost:8501`).
- Optional linting/type checks (if tools are installed): `ruff check` and `mypy app.py`.

## Coding Style & Naming Conventions

Follow PEP 8 with 4-space indentation and type hints throughout.

- Functions and variables: `snake_case`.
- Classes/dataclasses: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Keep parsing logic pure and side-effect free; Streamlit code should stay in top-level layout/interaction functions.
- Prefer small helpers over large functions, especially in SQL parsing and relationship extraction.

## Testing Guidelines

There are currently no automated tests. When adding them:

- Use `pytest` and place tests under a `tests/` directory.
- Name test files `test_*.py` and test functions `test_*`.
- Focus on unit tests for SQL preprocessing, table parsing, and relationship inference given representative DDL snippets.
- Run tests from the repository root using `pytest`.

## Commit & Pull Request Guidelines

There is no existing Git history; adopt clear, imperative commit messages (e.g., `Add relationship cardinality detection`).

- Keep one logical change per commit; reference issue IDs when applicable (e.g., `#12`).
- Pull requests should include: a brief summary, before/after behavior (screenshots of ER diagrams for UI changes), and testing notes (`pytest`, manual SQL samples used).

## Architecture Overview

Core flow: clean SQL → parse tables/columns/relationships → build an in-memory model → render an ER diagram with Graphviz → display via Streamlit.

When extending functionality, prefer adding parser/renderer helpers over modifying Streamlit callbacks directly, to keep UI and logic cleanly separated.

