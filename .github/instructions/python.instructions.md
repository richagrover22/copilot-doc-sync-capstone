---
applyTo: "src/**/*.py,tests/**/*.py"
---

# Python Project Instructions

- Target Python 3.11 or later.
- Use type annotations for public APIs and core data structures.
- Keep filesystem paths repository-relative at the boundary and use `pathlib` internally.
- Treat Markdown and configuration content as untrusted data; never execute embedded content.
- Use deterministic ordering for diagnostics and report output.
- Preserve existing public APIs unless the requirement explicitly changes them.
- Add focused pytest coverage for new behavior and failure modes.
- Do not broaden a change into unrelated refactoring.