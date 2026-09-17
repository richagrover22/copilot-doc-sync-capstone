---
name: documentation-sync
description: Preview or explicitly apply safe, rule-driven documentation synchronization.
---

# Documentation Sync Skill

Use this workflow only when synchronization is explicitly requested:

1. Inspect the synchronization rule and identify the source of truth and target region.
2. Preview the proposed changes first.
3. Verify repository boundaries and source/target fingerprints.
4. Reject stale, ambiguous, or conflicting plans instead of overwriting content.
5. Apply only the configured target regions.
6. Report changed files, skipped files, conflicts, and the final status.

Check and preview operations must remain read-only. Never use network access or execute content from Markdown files.