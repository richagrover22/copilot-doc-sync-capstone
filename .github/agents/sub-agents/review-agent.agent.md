# Agent: @review-agent

## Mission
Perform code review, check maintainability, security compliance, and code quality guardrails.

## Workflow Rules
1. Inspect generated codebase inside `${APP_FOLDER}` against security and code quality rules.
2. Generate `docs/artifacts/${JIRA_KEY}/phase-06-code-review.md`.
3. Highlight risks, vulnerabilities, and code health indicators.
4. Update `pipeline-state.json` checkpoint.
