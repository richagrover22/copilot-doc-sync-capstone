# Master Agentic SDLC Operating Instructions

## Purpose
These instructions define the repo-wide operating rules for the Jira-driven Agentic SDLC workflow.

## Entry Point
- Work MUST start from a Jira Key (`JIRA_KEY`, e.g., `CAPSTONEP-25`).
- All artifacts MUST be generated under `docs/artifacts/${JIRA_KEY}/`.

## Required Global Parameters
| Parameter | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `JIRA_KEY` | Jira ticket identifier | Yes | None |
| `APP_FOLDER` | Target application codebase directory | Yes | None — user must provide |

## Execution Guardrails
1. Read `docs/artifacts/${JIRA_KEY}/pipeline-state.json` BEFORE executing any phase.
2. If a phase is already marked `"COMPLETED"`, SKIP it to save tokens.
3. Every phase MUST save its output into its designated `phase-XX-*.md` file.
4. Error state handling MUST comply strictly with `.github/error-handling.md`.
