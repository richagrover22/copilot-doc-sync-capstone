"""Unit tests for deterministic synchronization and conflict handling."""

from pathlib import Path

import pytest

from sync import SyncConflictError, SyncRule, apply_plan, build_plan


def _repository(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    source.write_text("Generated content\n", encoding="utf-8")
    target.write_text(
        "before\n<!-- docsync:START api -->\nold\n<!-- docsync:END api -->\nafter\n",
        encoding="utf-8",
    )
    return tmp_path, source, target


def test_build_and_apply_plan_preserves_content_outside_region(tmp_path: Path) -> None:
    root, source, target = _repository(tmp_path)
    plan = build_plan(root, [SyncRule(source, target, "api")])

    changed = apply_plan(plan)

    assert changed == (target,)
    assert target.read_text(encoding="utf-8") == (
        "before\n<!-- docsync:START api -->\nGenerated content\n"
        "<!-- docsync:END api -->\nafter\n"
    )


def test_apply_plan_rejects_stale_target(tmp_path: Path) -> None:
    root, source, target = _repository(tmp_path)
    plan = build_plan(root, [SyncRule(source, target, "api")])
    target.write_text("changed after preview", encoding="utf-8")

    with pytest.raises(SyncConflictError, match="Target changed after planning"):
        apply_plan(plan)


def test_build_plan_rejects_missing_region(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    source.write_text("source", encoding="utf-8")
    target.write_text("no markers", encoding="utf-8")

    with pytest.raises(SyncConflictError, match="region 'api'"):
        build_plan(tmp_path, [SyncRule(source, target, "api")])
