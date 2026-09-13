"""Safe, deterministic documentation synchronization primitives."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import tempfile


class SyncError(RuntimeError):
    """Base class for synchronization failures."""


class SyncConflictError(SyncError):
    """Raised when a source or target changed after planning."""


@dataclass(frozen=True)
class SyncRule:
    """A rule replacing a marked region in a target with source content."""

    source: Path
    target: Path
    region: str

    @property
    def start_marker(self) -> str:
        return f"<!-- docsync:START {self.region} -->"

    @property
    def end_marker(self) -> str:
        return f"<!-- docsync:END {self.region} -->"


@dataclass(frozen=True)
class PlannedChange:
    """One guarded target replacement."""

    rule: SyncRule
    source_fingerprint: str
    target_fingerprint: str
    proposed_text: str


@dataclass(frozen=True)
class SyncPlan:
    """Immutable synchronization plan that can be previewed or applied."""

    repository_root: Path
    changes: tuple[PlannedChange, ...]

    @property
    def has_changes(self) -> bool:
        return any(change.proposed_text != change.rule.target.read_text(encoding="utf-8") for change in self.changes)


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _replace_region(target: str, rule: SyncRule, source: str) -> str:
    start = target.find(rule.start_marker)
    end = target.find(rule.end_marker)
    if start < 0 or end < 0 or end < start:
        raise SyncConflictError(
            f"Target region {rule.region!r} is missing or malformed in {rule.target}"
        )
    content_start = start + len(rule.start_marker)
    newline = "\r\n" if "\r\n" in target else "\n"
    source_body = source.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)
    return target[:content_start] + newline + source_body.rstrip("\r\n") + newline + target[end:]


def build_plan(root: Path, rules: list[SyncRule]) -> SyncPlan:
    """Create a plan after validating paths, inputs, and target regions."""
    resolved_root = root.resolve()
    changes: list[PlannedChange] = []
    for rule in sorted(rules, key=lambda item: (str(item.target), item.region)):
        source = rule.source.resolve()
        target = rule.target.resolve()
        for path in (source, target):
            try:
                path.relative_to(resolved_root)
            except ValueError as exc:
                raise SyncError(f"Synchronization path is outside repository root: {path}") from exc
        try:
            source_text = source.read_text(encoding="utf-8")
            target_text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise SyncError(f"Unable to read synchronization input: {exc}") from exc
        proposed = _replace_region(target_text, rule, source_text)
        changes.append(PlannedChange(rule, _fingerprint(source_text), _fingerprint(target_text), proposed))
    return SyncPlan(resolved_root, tuple(changes))


def apply_plan(plan: SyncPlan) -> tuple[Path, ...]:
    """Apply a plan after checking all preconditions, using atomic replacements."""
    staged: list[tuple[Path, Path]] = []
    try:
        for change in plan.changes:
            source = change.rule.source.resolve()
            target = change.rule.target.resolve()
            try:
                source.relative_to(plan.repository_root)
                target.relative_to(plan.repository_root)
            except ValueError as exc:
                raise SyncConflictError(f"Path escaped repository root: {target}") from exc
            current_source = source.read_text(encoding="utf-8")
            current_target = target.read_text(encoding="utf-8")
            if _fingerprint(current_source) != change.source_fingerprint:
                raise SyncConflictError(f"Source changed after planning: {source}")
            if _fingerprint(current_target) != change.target_fingerprint:
                raise SyncConflictError(f"Target changed after planning: {target}")
            if change.proposed_text == current_target:
                continue
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".docsync.tmp", dir=target.parent
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            temporary_path.write_text(change.proposed_text, encoding="utf-8", newline="")
            staged.append((temporary_path, target))
        for temporary_path, target in staged:
            os.replace(temporary_path, target)
    except (OSError, UnicodeError) as exc:
        raise SyncError(f"Synchronization failed: {exc}") from exc
    finally:
        for temporary_path, _ in staged:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return tuple(target for _, target in staged)
