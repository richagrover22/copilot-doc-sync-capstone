"""CLI behavior tests for successful and failing validation paths."""

from pathlib import Path

from cli import EXIT_CONFIGURATION, EXIT_FINDINGS, EXIT_OK, main


def test_check_happy_path_returns_success(capsys, tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Overview\n\n[guide](guide.md)\n", encoding="utf-8")
    (tmp_path / "guide.md").write_text("# Guide\n", encoding="utf-8")

    exit_code = main(["check", "README.md", "--root", str(tmp_path), "--require", "overview"])

    captured = capsys.readouterr()
    assert exit_code == EXIT_OK
    assert '"status":' not in captured.out
    assert "Scanned 1 Markdown file(s): passed" in captured.out


def test_check_reports_missing_file_and_broken_anchor(capsys, tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Overview\n\n[missing file](missing.md)\n[missing anchor](guide.md#does-not-exist)\n",
        encoding="utf-8",
    )
    (tmp_path / "guide.md").write_text("# Guide\n", encoding="utf-8")

    exit_code = main(["check", "--root", str(tmp_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == EXIT_FINDINGS
    assert "Broken internal link: missing.md" in captured.out
    assert "Missing heading anchor: guide.md#does-not-exist" in captured.out


def test_check_does_not_validate_links_inside_fenced_code(capsys, tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "```markdown\n[not active](missing.md#anchor)\n```\n", encoding="utf-8"
    )

    assert main(["check", "--root", str(tmp_path), "--json"]) == EXIT_OK
    assert "missing.md" not in capsys.readouterr().out


def test_config_validate_rejects_missing_and_malformed_toml(capsys, tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    malformed = tmp_path / "malformed.toml"
    malformed.write_text("targets = [", encoding="utf-8")

    assert main(["config-validate", str(missing)]) == EXIT_CONFIGURATION
    assert "Configuration error" in capsys.readouterr().err
    assert main(["config-validate", str(malformed)]) == EXIT_CONFIGURATION
    assert "Configuration error" in capsys.readouterr().err


def test_config_validate_accepts_valid_toml(capsys, tmp_path: Path) -> None:
    config = tmp_path / "docsync.toml"
    config.write_text('targets = ["docs"]\n', encoding="utf-8")

    assert main(["config-validate", str(config)]) == EXIT_OK
    assert "Configuration is valid" in capsys.readouterr().out
