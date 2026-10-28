# Phase 01: Requirements Specification

## Source and Confidence

- Jira key: `MDP-7` (verified live via Atlassian MCP, see `jira_snapshot.json`)
- Summary: "Build Task Manager Application with Agentic SDLC Sync paste karein" (trailing "paste karein" appears to be template residue)
- Description: "Implement enterprise-grade task manager application with automated SDLC documentation sync"
- Type / Status / Priority: Idea / Parking lot / Medium
- Acceptance criteria in Jira: none. Criteria below are derived and need approval.
- Scope confidence: Medium. The ticket is two lines; details are inferred from the ticket intent plus the previously user-authorized task-manager scope.

## Scope

A task manager application plus automated synchronization of SDLC documentation (phase artifacts) with requirements and phase results.

## Functional Requirements

1. Create, view, edit, and delete tasks.
2. Each task has a status and a priority; tasks can be filtered by either.
3. The pipeline accepts a Jira key and an application folder, and writes artifacts under `docs/artifacts/${JIRA_KEY}/`.
4. SDLC documentation (phase artifacts, `pipeline-state.json`) is generated and updated automatically from the Jira requirements and phase results (the "SDLC sync").
5. Completed phases are skipped on resume.
6. Each phase requires human approval before the next begins.

## Non-Functional Requirements

1. "Enterprise-grade" is interpreted as: input validation, clear error handling, automated tests, and maintainable structure. No SSO, multi-tenancy or HA is assumed.
2. Single-user, local persistence for the MVP.
3. Artifacts are persisted in the repository.

## Acceptance Criteria (derived)

- Given the app is running, when a task is submitted, then it appears in the list.
- Given a task exists, when it is edited or deleted, then the list reflects the change.
- Given mixed tasks, when filtering by status or priority, then only matching tasks are shown.
- Given a valid Jira key and app folder, when the pipeline runs, then phase artifacts are written and state is recorded.
- Given a completed phase, when the pipeline resumes, then that phase is skipped.
- Given verification runs, then test results are recorded in `phase-07-verification.md`.

## Out of Scope

- Accounts, authentication, shared multi-user lists.
- Fields beyond status and priority (due dates, tags) unless added later.
- Syncing application README or API docs from source changes.

## Open Questions for HITL

| # | Question | Working assumption |
| --- | --- | --- |
| 1 | Is "paste karein" in the summary template residue? | Yes, ignored |
| 2 | What does "enterprise-grade" require concretely? | Validation, error handling, tests (see NFR 1) |
| 3 | Should "SDLC sync" cover only pipeline artifacts, or also app docs? | Pipeline artifacts only |
| 4 | Approve the derived acceptance criteria, since Jira has none? | Pending |

## Status

Phase 01 complete pending human approval. Phases 02-08 not started.
