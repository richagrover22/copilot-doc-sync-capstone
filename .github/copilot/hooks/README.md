# Copilot Hook Contract

This directory reserves the project hook location for agentic SDLC automation.

Before adding an automated hook, document:

- the lifecycle event that invokes it;
- the command and required working directory;
- files and environment variables it can access;
- timeout and failure behavior;
- whether it is read-only or may modify files; and
- the tests that prove it is safe and deterministic.

The documentation validation workflow is intentionally invoked explicitly for now. No hook is enabled until a supported hook runner and its event contract are selected.