I’ll review `architecture.md` against the stated requirements, concentrating on failure modes, security boundaries, and error contracts. I’ll return findings first, ordered by severity, followed by decisions and residual risks.

Read 

Read , lines 1 to 280

The review found several architectural gaps despite the strong separation of validation and mutation: the current design does not fully define atomicity across multiple files, symlink race handling, report redaction, encoding/line-ending failure behavior, or the public error/exit-code contract. I’m checking the exact locations of those statements now so the findings are actionable and traceable.

Searched for regex `atomic|recheck|fingerprint|symlink|report|error|exit code|encoding|line-ending|parallel` (`**/architecture.md`), 38 results

Searched for regex `NFR-003|NFR-009|NFR-011|NFR-017|NFR-021|FR-027|FR-034|FR-038` (`**/requirements.md`), 8 results

# Architecture Review

## Findings

### High: Multi-file synchronization is not transaction-safe

The executor guarantees atomic replacement per file, but not atomicity across a synchronization operation involving multiple files. If file 1 is replaced successfully and file 2 fails a precondition or write, the repository is left partially synchronized.

References: `architecture.md:91`, `architecture.md:109`, `architecture.md:179`

**Required decision:** Stage and validate all proposed changes before committing any replacement. Either provide rollback/recovery semantics or explicitly define partial-commit behavior and report it as a synchronization failure.

### High: Path validation remains vulnerable to TOCTOU races

Resolving paths with `realpath` during discovery does not prevent a symlink or target-file replacement between validation and execution. The executor may write to a different location than the one originally checked.

Reference: `architecture.md:180`

**Required decision:** Revalidate containment immediately before writing and use platform-appropriate secure file-opening techniques where possible. At minimum, compare file identity and resolved path immediately before replacement.

### Medium: Synchronization approval is underspecified

The architecture mentions an “approved plan” and fingerprints, but does not define how approval is represented or how a plan is bound to its repository root, configuration identity, tool version, and synchronization rules.

Reference: `architecture.md:90-93`

**Required decision:** Require an immutable plan containing repository identity, configuration hash, source/target fingerprints, rule version, and explicit apply confirmation. Reject plans created from a different repository state or configuration.

### Medium: Error and exit-code contracts are not concrete enough

The architecture says errors become structured results and exit codes are deterministic, but it does not define the exception/result taxonomy, precedence rules, or numeric exit-code mapping.

References: `architecture.md:39`, `architecture.md:97`, `architecture.md:110`

This leaves ambiguity for callers handling configuration errors, validation failures, filesystem failures, conflicts, report-output failures, and unexpected internal errors.

**Required decision:** Document a stable error model and exit-code table, including whether multiple failure categories can coexist and which category determines the final exit code.

### Medium: Encoding and line-ending failure behavior is incomplete

The document promises preservation “whenever possible,” but does not specify supported encodings, BOM handling, invalid byte behavior, newline detection, or what happens when preservation is impossible.

Reference: `architecture.md:67`

**Required decision:** Define an explicit encoding policy, preferably UTF-8 with documented BOM behavior. Refuse synchronization when decoding or preservation is ambiguous rather than silently rewriting content.

### Medium: Report redaction requirements are too vague

“Include paths and snippets only when needed” is not an enforceable secret-handling policy. Diagnostics may expose sensitive repository paths, link destinations, or source content.

References: `architecture.md:69`, `requirements.md:224`

**Required decision:** Define report redaction rules, maximum snippet lengths, path normalization behavior, and a guarantee that credentials, environment values, and full file contents are never emitted.

### Medium: Front-matter technology choice is unresolved

The architecture lists `python-frontmatter` or a custom YAML/TOML adapter without selecting one. This affects supported syntax, dependency security, malformed-input behavior, and configuration documentation.

Reference: `architecture.md:24`

**Required decision:** Select one supported front-matter format and parser, pin or constrain the dependency, and define behavior for unsupported or malformed metadata.

### Medium: Observability is missing from the component design

The requirements call for configurable logging sufficient to diagnose failures without leaking sensitive content, but the architecture does not define a logging component or logging policy.

Reference: `requirements.md:244`

**Required decision:** Add structured logging around configuration loading, discovery, parsing, planning, and execution. Keep diagnostics/report output separate from logs and default logs to stderr.

### Low: Resource bounds are not operationally defined

The architecture says to define a maximum file size and avoid retaining all raw content, but does not specify the limit or how repository indexing balances memory use against link and anchor validation.

Reference: `architecture.md:184`, `requirements.md:207-211`

**Required decision:** Define file-size limits, memory expectations, and whether large files are rejected, streamed, or processed with reduced features.

## Decisions

- Retain the modular-monolith architecture and the separation between parser, validator, planner, and executor.
- Keep check and preview strictly read-only.
- Make synchronization plans immutable, configuration-bound, and fingerprint-checked.
- Treat multi-file synchronization as a transaction or provide explicit rollback/recovery behavior.
- Define stable typed errors and numeric exit codes before implementing the CLI.
- Select and document one front-matter format and parser.
- Add structured logging with mandatory secret redaction.
- Make encoding, newline preservation, file-size limits, and symlink behavior explicit cross-platform contracts.

## Residual Risks

- Atomic replacement semantics and file locking differ across Windows, Linux, and macOS.
- Concurrent external edits cannot be fully prevented; fingerprint checks reduce but do not eliminate race windows.
- Markdown anchor normalization may differ between documentation platforms and should be covered by compatibility tests.
- Dependency vulnerabilities remain an operational concern and require CI scanning as specified by the requirements.