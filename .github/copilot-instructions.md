# Agentic SDLC & Documentation Sync Guidelines

- **Architecture Rules:** Python 3.10+ standard CLI application structure. Follow modular design inside `src/`.
- **Workflow Instructions:** 
  1. Read requirements and user stories directly from local `.md` or `.txt` input files in workspace root.
  2. Parse file inputs safely without hardcoding API credentials or secrets.
  3. Automatically generate and update `requirements.md`, `architecture.md`, `impl-plan.md`, and `PR_SUMMARY.md`.
- **Quality Gates:** Always write pytest unit tests under `tests/` before marking tasks as complete. Ensure 100% execution pass rate.
## Orchestration Pipeline Rules
- **Execution Controller**: `src/orchestrator.py` governs the SDLC pipeline execution order.
- **Strict Quality Gate**: Do not commit code or generate PR summaries if `pytest tests/` fails.
- **Input Rule**: Always parse requirements from local workspace files (`user_story.md` / `requirements.md`).