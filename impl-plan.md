# Automated Documentation Sync Engine Implementation Plan

## 1. Delivery strategy

Implement the engine as a modular monolith with a read-only validation path and a separately gated synchronization path. Work is ordered by dependency: stable contracts and safety policies come before components that consume them, and no file-writing capability is introduced until planning and conflict checks are tested.

Priority meanings:

- **P0:** required foundation or safety control; blocks dependent implementation.
- **P1:** required product capability for the first usable release.
- **P2:** required hardening, portability, or operational capability.
- **P3:** optimization or follow-up capability that can be added without changing core contracts.

## 2. Dependency gates and blocked work

| Gate | Must be complete before | Why it blocks work |
| --- | --- | --- |
| G1: Product and contract decisions | All implementation | Configuration keys, diagnostic fields, error categories, exit codes, supported encodings, and front-matter format must be stable before APIs and tests are built. |
| G2: Repository/package foundation | Runtime components | The package layout, dependency constraints, test runner, and quality checks are needed for every module. |
| G3: Read-only core | CLI check, reports, synchronization planning | Discovery, parsing, models, repository indexing, and validation produce the inputs consumed by application orchestration and planning. |
| G4: Synchronization safety | `sync apply` | Planning, fingerprints, conflict policy, atomic write behavior, and multi-file failure semantics must be implemented and tested before any mutation is exposed. |
| G5: Cross-platform and operational hardening | Release/CI adoption | Portability, logging, dependency scanning, performance, and packaging provide the release confidence required by developer and CI workflows. |

**Explicitly blocked tasks:**

- Validation rules are blocked by the document model, configuration schema, and parser location contract.
- Link validation is blocked by parser output and the repository index/anchor normalization policy.
- Drift planning is blocked by validated configuration, parsed source/target documents, and stable region-selection rules.
- Synchronization execution is blocked by planner fingerprints, conflict handling, atomic-write design, and the multi-file commit policy.
- The public CLI is blocked by application result contracts and the exit-code table.
- CI integration is blocked by deterministic reports, stable exit codes, packaging, and the test suite.

## 3. Phase 0: Resolve design decisions and contracts

### 0.1 Select supported formats and policies (P0)

**Tasks**

- Select TOML as the documented configuration format and define the configuration filename and discovery rules.
- Select one front-matter format and parser. Recommended initial scope: YAML front matter parsed as data with safe loading only.
- Define UTF-8 decoding, BOM handling, newline detection/preservation, and behavior for invalid or mixed encodings.
- Define maximum file size and behavior for oversized files.
- Define Markdown anchor normalization and heading matching rules.
- Define configuration precedence among defaults, repository configuration, environment variables, and CLI options.

**Acceptance checks**

- A written policy exists for every ambiguous format or portability choice.
- Malformed, unsupported, or ambiguous input has a defined diagnostic and does not cause silent rewriting.

### 0.2 Define public contracts (P0)

**Tasks**

- Define typed models for configuration, document, source location, diagnostic, report, synchronization rule, synchronization plan, audit record, and operation result.
- Define stable diagnostic fields: rule ID, severity, message, path, line, column, remediation, and optional safe context.
- Define error categories for configuration, validation, filesystem, synchronization conflict, report output, and unexpected internal failure.
- Define numeric exit codes and precedence when multiple categories occur.
- Define JSON report schema version, ordering, timestamps, tool version, configuration identity, and empty-scope status.
- Define redaction rules and prohibit credentials, environment secrets, and full file contents in diagnostics, reports, and logs.

**Acceptance checks**

- Contract tests can construct and serialize representative results without parsing console text.
- The CLI and library can distinguish findings from execution failures.

### 0.3 Decide synchronization transaction semantics (P0)

**Tasks**

- Define an immutable plan identity containing repository root identity, configuration hash, tool/ruleset version, source fingerprints, target fingerprints, and affected regions.
- Choose all-or-nothing staging/commit behavior for multi-file apply, or document and test partial-commit recovery. Recommended: stage all files, validate all preconditions, then commit in deterministic order with recovery records.
- Define behavior when an external edit occurs between planning and applying.
- Define symlink policy and immediate pre-write containment/file-identity checks.

**Acceptance checks**

- A plan created from a changed repository or configuration is rejected.
- A failed precondition cannot overwrite a target.
- Multi-file failure behavior is observable and documented.

## 4. Phase 1: Repository and package foundation

### 1.1 Establish package structure and dependencies (P0)

**Tasks**

- Create the `src/` package layout from the architecture: CLI, configuration, models, parsers, validators, sync, and utilities.
- Add `pyproject.toml`, Python 3.11+ constraints, console entry point, dependency bounds, and development dependencies.
- Configure pytest, coverage, Ruff, and the selected type checker.
- Add a minimal test fixture helper for temporary repositories and controlled file permissions.

**Depends on:** 0.1.

**Acceptance checks:** clean install in a fresh environment; lint, type check, and empty test suite run successfully.

### 1.2 Add shared utilities and typed models (P0)

**Tasks**

- Implement immutable models and enums for severities, operation modes, error categories, and statuses.
- Implement deterministic sorting helpers for paths, locations, rule IDs, and messages.
- Implement repository-root discovery and normalized relative-path utilities.
- Implement containment checks using resolved paths and the selected symlink policy.
- Add unit tests for Windows-style paths, traversal attempts, symlink escapes, and path normalization.

**Depends on:** 0.2, 0.3, 1.1.

**Acceptance checks:** models serialize to the planned JSON shape; unsafe paths are rejected consistently.

## 5. Phase 2: Read-only document pipeline

### 2.1 Implement configuration loading and validation (P0)

**Tasks**

- Load TOML with `tomllib` and map it into typed configuration models.
- Reject malformed TOML, unknown keys, invalid types, invalid severity values, invalid paths, and contradictory synchronization settings.
- Normalize configuration before computing a stable identity hash.
- Return structured configuration errors with safe locations and remediation.
- Add tests for defaults, precedence, malformed values, unknown keys, and invalid repository boundaries.

**Depends on:** 0.1, 0.2, 1.2.

**Acceptance checks:** invalid configuration stops before file scanning or mutation; equivalent normalized configurations produce the same identity.

### 2.2 Implement target discovery (P1)

**Tasks**

- Support individual files, directories, glob patterns, repository-relative paths, configured defaults, and exclusions.
- Discover `.md` and `.markdown` files deterministically.
- Detect missing, duplicated, unreadable, unsupported, and out-of-root targets.
- Define and test empty-scope behavior.

**Depends on:** 2.1 and path utilities from 1.2.

**Acceptance checks:** the same repository/configuration produces the same sorted target set; all discovery failures become structured diagnostics.

### 2.3 Implement Markdown and front-matter parsing (P1)

**Tasks**

- Parse headings, links, destinations, fenced code blocks, source locations, and selected front matter with the chosen maintained parser.
- Exclude Markdown-like syntax inside fenced code blocks from document structure.
- Capture encoding and newline metadata needed for safe synchronization.
- Avoid evaluating templates, code blocks, or front matter content.
- Define parser diagnostics for malformed Markdown, malformed front matter, decoding failures, and size limits.

**Depends on:** 0.1, 1.2, 2.2.

**Acceptance checks:** fixtures cover headings, links, anchors, code fences, front matter, malformed input, BOMs, and line endings.

### 2.4 Build the repository index and link resolver (P1)

**Tasks**

- Index parsed documents by normalized repository-relative path.
- Store heading anchors using the documented normalization policy.
- Resolve relative file links and anchors without network access.
- Classify external schemes, placeholders, and configured exclusions without fetching them.
- Reject out-of-bound targets before index lookup.

**Depends on:** 2.2 and 2.3.

**Acceptance checks:** broken files, missing anchors, code-fence links, external links, and path traversal cases produce correct results.

## 6. Phase 3: Validation and reporting

### 3.1 Implement validation rule engine (P1)

**Tasks**

- Implement required-section and heading matching rules.
- Implement duplicate-section and hierarchy rules.
- Implement front-matter presence, allowed-value, and basic-type rules.
- Implement internal file-link and anchor rules.
- Implement configurable severity mapping and rule enablement.
- Ensure rules are pure/read-only and emit typed diagnostics only.
- Sort diagnostics deterministically after all rules complete.

**Depends on:** 0.2, 2.1, 2.3, 2.4.

**Acceptance checks:** each diagnostic category has unit tests with stable IDs, locations, remediation, and severity behavior.

### 3.2 Implement result aggregation and reports (P1)

**Tasks**

- Aggregate scope, timestamp, version, configuration identity, scanned/changed files, counts, diagnostics, and overall status.
- Implement deterministic human-readable console output.
- Implement versioned JSON output with stable field names and ordering where applicable.
- Support stdout, stderr, and file destinations with clear output-write failures.
- Apply redaction and snippet limits consistently.

**Depends on:** 0.2, 3.1.

**Acceptance checks:** JSON contract tests pass; reports contain no secrets or full file content; output failures produce the defined error category.

### 3.3 Implement application service (P1)

**Tasks**

- Coordinate configuration, discovery, parsing, indexing, validation, aggregation, and report rendering.
- Keep check mode read-only by construction.
- Apply error-category precedence and map results to documented exit codes.
- Support empty scope and configurable warning pass/fail behavior.
- Add structured logging with safe fields and configurable levels.

**Depends on:** 2.1-2.4, 3.1, 3.2, and 0.2.

**Acceptance checks:** end-to-end library tests validate success, findings, configuration failure, filesystem failure, report failure, and unexpected failure handling.

## 7. Phase 4: Synchronization planning and safe execution

### 4.1 Implement explicit synchronization rule parsing (P1)

**Tasks**

- Validate source-of-truth paths, target files/sections, transformation/replacement policy, and conflict policy.
- Reject overlapping or ambiguous target regions unless explicitly supported.
- Define deterministic region matching and preserve non-target content.

**Depends on:** 2.1, 2.3, 2.4, and 0.3.

**Acceptance checks:** invalid, ambiguous, stale, and conflicting rules produce plan diagnostics without writes.

### 4.2 Implement synchronization planner and preview (P1)

**Tasks**

- Compare configured source and target regions.
- Generate immutable plans with source/target fingerprints, configuration identity, tool/ruleset version, proposed content, and audit data.
- Report no-op/idempotent operations separately from changes.
- Render preview output without invoking write APIs.

**Depends on:** 4.1, 3.2, and the complete read-only pipeline.

**Acceptance checks:** preview is byte-for-byte read-only; repeated planning without source changes is idempotent; stale inputs are rejected.

### 4.3 Implement staged atomic executor (P0)

**Tasks**

- Require explicit apply mode and an approved, repository/configuration-bound plan.
- Recheck path containment, file identity, source/target fingerprints, encoding, and region boundaries immediately before staging.
- Stage all target contents in destination directories, preserving encoding and newline style.
- Validate every staged result before committing any replacement.
- Commit in deterministic order using atomic replacement where supported.
- Record changed, skipped, conflicted, and failed rules.
- Clean temporary files and provide recovery information if a multi-file commit cannot complete.

**Depends on:** 0.3, 1.2, 4.2, and 3.2.

**Acceptance checks:** no write occurs in check/preview; conflicts prevent overwrite; unchanged files remain byte-identical; failure behavior matches the selected transaction policy; repeated apply is idempotent.

### 4.4 Add synchronization integration tests (P1)

**Tasks**

- Test single-file and multi-file updates.
- Test external edits between preview and apply.
- Test symlink/path replacement attempts and out-of-root targets.
- Test invalid encodings, BOMs, CRLF/LF preservation, permissions, and write failures.
- Test partial-commit/recovery behavior on supported platforms or through an injected filesystem abstraction.

**Depends on:** 4.3.

**Acceptance checks:** all review findings related to mutation safety have regression coverage.

## 8. Phase 5: CLI, packaging, and operational hardening

### 5.1 Implement CLI commands (P1)

**Tasks**

- Add `check`, `config validate`, `sync preview`, and `sync apply` commands.
- Support explicit targets, report format/destination, quiet mode, severity policy, and configuration path options.
- Require an explicit apply action for mutation and provide clear confirmation semantics.
- Keep stdout suitable for reports and stderr suitable for diagnostics/logging according to the output policy.
- Map typed results to stable exit codes.

**Depends on:** 3.3, 4.2, and 4.3.

**Acceptance checks:** CLI contract tests cover every command, option class, output mode, and exit-code category.

### 5.2 Add public library API and documentation (P1)

**Tasks**

- Expose configuration loading, scanning, validation, report generation, and synchronization-plan application through typed APIs.
- Document exceptions/results and mutation guarantees.
- Document configuration, rules, reports, exit codes, safety limits, troubleshooting, and compatibility policy.

**Depends on:** 3.3, 4.2, 4.3, and 5.1 contracts.

**Acceptance checks:** API examples run against temporary repositories and never require console parsing.

### 5.3 Add cross-platform and security hardening (P2)

**Tasks**

- Run CI on Windows, Linux, and macOS or an equivalent supported matrix.
- Test path separators, newline conventions, encodings, permissions, and exit behavior.
- Add dependency vulnerability scanning and dependency update policy.
- Add logging/redaction tests and verify no network access is required for core validation.
- Add tests for file-size and memory limits.

**Depends on:** 5.1, 5.2, and 4.4.

**Acceptance checks:** supported-platform matrix passes; security checks detect no release-blocking issues.

### 5.4 Performance and incremental operation (P2/P3)

**Tasks**

- Benchmark 1,000 Markdown files and 100 MB of content against the 30-second requirement.
- Profile memory usage and adjust indexing/raw-content retention.
- Add changed-file/incremental target selection for pre-commit and CI use.
- Consider parallel parsing only after deterministic ordering and shared-resource behavior are proven.

**Depends on:** 3.3 and 5.3.

**Acceptance checks:** baseline performance target is measured and documented; parallel or incremental behavior does not alter findings.

## 9. Release gates

The first release is ready only when:

1. Configuration, diagnostic, report, error, and exit-code contracts are documented and tested.
2. Check mode validates selected Markdown files and is demonstrably read-only.
3. Required sections, metadata, internal links, anchors, and fenced-code behavior are covered by tests.
4. Preview produces deterministic synchronization plans without writing.
5. Apply requires explicit authorization, rechecks fingerprints and containment, preserves encoding/newlines, and follows the documented multi-file transaction policy.
6. Reports are available in console and JSON formats without leaking sensitive content.
7. Library and CLI APIs return structured results and documented failures.
8. Cross-platform, dependency, performance, and packaging checks pass at the agreed release level.

## 10. Suggested execution order

Implement in this order for shortest safe path to a usable product:

1. Resolve decisions and contracts: 0.1-0.3.
2. Establish package, models, and path safety: 1.1-1.2.
3. Build configuration, discovery, parser, and repository index: 2.1-2.4.
4. Build rules, reports, application service, and read-only integration tests: 3.1-3.3.
5. Build synchronization rule parsing and preview: 4.1-4.2.
6. Build and test the staged executor: 4.3-4.4.
7. Expose CLI and library APIs: 5.1-5.2.
8. Complete cross-platform, security, performance, and release hardening: 5.3-5.4.

Parallel work is appropriate only within a phase after its shared contracts are stable. For example, structural-rule tests and report-renderer tests can proceed in parallel after the model and diagnostic contracts exist; executor implementation must remain blocked until the planner and transaction decisions are complete.
