# Repository Guidelines

## Project Structure & Module Organization
This repository centers on the LangGraph workflow defined in `graph.py`, `state.py`, and `services.py`. Specialized agents live in `agents/` (e.g., `supervisor.py`, `graph_generator.py`, `validator.py`) and orchestrate CASE/UCO conversions. FastAPI endpoints originate in `main.py` and `routes.py`, share data contracts from `schemas.py`, and rely on configuration helpers in `config.py` and `tools.py`. The Streamlit client (`app.py`) consumes the backend, while reusable prompts and task briefs sit in `prompt` and `tasks/`. Persist runtime artifacts in `sessions/`, keep regression fixtures under `tests/`, and place scenario or data-heavy suites under the legacy `test/` tree.

## Build, Test, and Development Commands
- `pip install -r requirements.txt` — install runtime and agent dependencies.
- `python main.py` — launch the FastAPI server on `localhost:9000` with auto-reload.
- `streamlit run app.py` — start the analyst UI on `localhost:8501`.
- `PYTHONPATH=. python -m tests.offline_graph_generator_test` — execute the deterministic offline graph regression.
- `PYTHONPATH=. python tests/run_production_agent.py` — call the streaming endpoint (defaults to `localhost:8000`; update if the server port changes).

## Coding Style & Naming Conventions
Target Python 3.10+ and follow PEP 8 (4-space indentation, snake_case functions, PascalCase classes, ALL_CAPS constants). Keep each agent module focused on one capability, mirroring the existing file naming. Run `black` with an 88-character limit and `ruff` if available; otherwise, ensure imports stay ordered and docstrings summarize agent responsibilities before implementation details.

## Testing Guidelines
Use `tests/` for focused regression harnesses (`test_prompt.py`, `offline_graph_generator_test.py`) and `test/` for broader scenario or data-driven suites (`test_end_to_end_flow.py`, `guardrail_test.py`). Add new modules with the `test_*.py` pattern and run them via `PYTHONPATH=. python -m tests.<module>` or `PYTHONPATH=. python test.<module>`. Maintain coverage of the supervisor-to-validator flow and include sample artifacts or expected JSON-LD outputs with any new ontology facets. Use `tests/run_production_agent.py` for end-to-end verification against the live API.

## Commit & Pull Request Guidelines
Adopt Conventional Commits (`feat:`, `fix:`, `chore:`) as seen in `feat: expand state for dynamic UUID planner` and avoid vague summaries like `changes`. PRs should link the motivating issue, outline which agents or services were touched, and attach screenshots or JSON snippets whenever graph structure changes. Flag new environment variables or dependencies in the description and confirm the command list above was executed.

## Agent Workflow Notes
When adding an agent, register it in `graph.py`, expose configuration through `config.py`, and document any ontology references in the `prompt` file. Provide mock artifacts or plan outputs in either `tests/` or `test/` so collaborators can reproduce the new behavior end-to-end. Finally, "use maximum reasoning effort" when coordinating complex workflows.
