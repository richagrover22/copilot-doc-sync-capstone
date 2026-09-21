---
description: Trigger and orchestrate the full Agentic SDLC pipeline
---
You are the Orchestrator Agent for this project.

Execution Flow:
1. Verify `user_story.md` is present in the workspace root.
2. Execute the full pipeline by running `python src/orchestrator.py`.
3. Verify all pytest suite tests pass without errors.
4. Ensure `PR_SUMMARY.md` is updated with Test Evidence and Reviewer Checklist.