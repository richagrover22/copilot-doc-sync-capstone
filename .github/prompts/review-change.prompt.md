---
description: Review a documentation-sync change for regressions and missing tests.
agent: architecture-reviewer
---

Review the current working-tree changes for the Documentation Sync Engine.

Prioritize, in order:

- data loss or unsafe synchronization;
- path traversal, symlink, encoding, and secret-disclosure risks;
- incorrect validation or report behavior;
- broken CLI/API contracts;
- missing or inadequate tests.

List findings first with severity and file references. Then list assumptions, residual risks, and a brief summary. Do not modify files.