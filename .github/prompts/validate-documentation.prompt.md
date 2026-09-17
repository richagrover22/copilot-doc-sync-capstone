---
description: Validate repository Markdown and summarize actionable findings.
agent: implementation-engineer
---

Run the repository's documentation validation workflow in read-only mode.

1. Inspect the configured Markdown targets and required sections.
2. Check internal file links and heading anchors, excluding links inside fenced code blocks.
3. Run the focused test suite for the parser and CLI.
4. Summarize findings by severity, including file and line references.
5. Report the exact validation command and exit status.

Do not apply synchronization changes.