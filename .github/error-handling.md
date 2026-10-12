# Error Handling Specification

## Recovery Procedures

### By Error Type

#### Network/API Failures
- Retry automatically up to 3 times with exponential backoff.
- Skip with justification if non-critical.
- Escalate to HITL if persistent.

#### Authentication Failures
- Log error without sensitive data.
- Check credential configuration.
- Escalate to HITL immediately with setup instructions and wait for user retry signal.

#### Test Failures
- Capture test output and logs in `phase-07-verification.md`.
- Attempt auto-fix if simple (e.g., import fixes or snapshot update).
- If auto-fix is not possible:
  a. Record failure status in `pipeline-state.json`.
  b. Escalate to HITL with options: [Fix Code, Retry Test, Skip Step].
