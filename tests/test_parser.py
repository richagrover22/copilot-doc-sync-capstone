"""Unit tests for Markdown parsing and file-access errors."""

from pathlib import Path

import pytest

from parser import ParseError, normalize_heading, parse_text, read_document


def test_parse_text_extracts_document_structure_and_ignores_fenced_code(tmp_path: Path) -> None:
    document = parse_text(
        """---
title: Example
---
# Introduction

[guide](guide.md#setup)

```markdown
# Not a heading
[fake](missing.md)
```

## Setup
Details.
""",
        tmp_path / "README.md",
        tmp_path,
    )

    assert document.front_matter == {"title": "Example"}
    assert [(heading.text, heading.level, heading.anchor) for heading in document.headings] == [
        ("Introduction", 1, "introduction"),
        ("Setup", 2, "setup"),
    ]
    assert len(document.links) == 1
    assert document.links[0].destination == "guide.md#setup"
    assert document.links[0].location.line == 6
    section = document.section("introduction")
    assert section is not None
    assert "[guide](guide.md#setup)" in section


def test_heading_normalization_is_deterministic() -> None:
    assert normalize_heading("  API *Reference* & Setup! ") == "api-reference-setup"


def test_read_document_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ParseError, match="Unable to read"):
        read_document(tmp_path / "missing.md", tmp_path)


def test_read_document_rejects_path_outside_repository(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.md"
    outside.write_text("# Outside", encoding="utf-8")

    with pytest.raises(ParseError, match="outside repository root"):
        read_document(outside, tmp_path)
