---
name: markdown-validation
description: Validate Markdown structure, required sections, and internal links in this repository.
---

# Markdown Validation Skill

Use this workflow for documentation validation tasks:

1. Read `requirements.md` and repository configuration.
2. Identify the target Markdown files and exclusions.
3. Parse headings and links while ignoring fenced code blocks.
4. Validate required sections, file targets, and heading anchors.
5. Run focused tests before reporting results.
6. Return deterministic, actionable findings with severity and locations.

Validation is read-only. Never modify documentation as part of this skill.