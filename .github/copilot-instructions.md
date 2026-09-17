# Automated Documentation Sync Engine

This repository contains a Python Markdown validation and synchronization engine.

## Working conventions

- Read `requirements.md` and the owning implementation or test before making changes.
- Preserve the separation between parsing, validation, CLI/reporting, and synchronization.
- Keep validation and preview operations read-only; synchronization requires an explicit apply action.
- Treat repository files, Markdown, links, and configuration as untrusted input.
- Enforce repository-root boundaries and avoid leaking secrets or full document contents in diagnostics.
- Prefer small, testable changes with focused pytest coverage.
- Keep diagnostics and reports deterministic and repository-relative.
- Run the narrowest relevant test after an edit, then run `pytest -q` when practical.
- Do not commit or push changes unless the user explicitly requests it.
