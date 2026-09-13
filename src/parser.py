"""Markdown parsing primitives for the documentation sync engine.

The parser deliberately treats repository content as data. It extracts a small,
stable document model without rendering Markdown or evaluating front matter.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterator


class ParseError(ValueError):
    """Raised when a Markdown document cannot be safely read or parsed."""


@dataclass(frozen=True)
class SourceLocation:
    """One-based source position."""

    line: int
    column: int = 1


@dataclass(frozen=True)
class Heading:
    """A Markdown heading and its source location."""

    text: str
    level: int
    location: SourceLocation
    anchor: str


@dataclass(frozen=True)
class Link:
    """A Markdown link destination and its source location."""

    label: str
    destination: str
    location: SourceLocation


@dataclass(frozen=True)
class Document:
    """Parsed Markdown content retained for validation and synchronization."""

    path: Path
    relative_path: Path
    text: str
    headings: tuple[Heading, ...]
    links: tuple[Link, ...]
    front_matter: dict[str, str]
    newline: str
    has_bom: bool

    def section(self, heading: str) -> tuple[str, ...] | None:
        """Return the content under the first matching heading, if present."""
        normalized = normalize_heading(heading)
        for index, current in enumerate(self.headings):
            if current.anchor != normalized:
                continue
            end = len(self.text.splitlines())
            for following in self.headings[index + 1 :]:
                if following.level <= current.level:
                    end = following.location.line - 1
                    break
            lines = self.text.splitlines()[current.location.line : end]
            return tuple(lines)
        return None


def normalize_heading(text: str) -> str:
    """Apply a deterministic GitHub-like heading anchor normalization."""
    lowered = text.strip().casefold()
    lowered = re.sub(r"[`*_~]", "", lowered)
    lowered = re.sub(r"[^\w\s-]", "", lowered, flags=re.UNICODE)
    return re.sub(r"[\s-]+", "-", lowered).strip("-")


def _parse_front_matter(lines: list[str]) -> tuple[dict[str, str], int]:
    if not lines or lines[0].strip() not in {"---", "+++"}:
        return {}, 0
    delimiter = lines[0].strip()
    for index in range(1, len(lines)):
        if lines[index].strip() == delimiter:
            values: dict[str, str] = {}
            for line in lines[1:index]:
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if ":" not in line and "=" not in line:
                    raise ParseError(f"Invalid front matter at line {index + 1}")
                separator = ":" if ":" in line else "="
                key, value = line.split(separator, 1)
                key = key.strip()
                if not key:
                    raise ParseError(f"Empty front matter key at line {index + 1}")
                values[key] = value.strip().strip('"\'')
            return values, index + 1
    raise ParseError("Unterminated front matter block")


def _iter_content_lines(text: str, front_matter_lines: int) -> Iterator[tuple[int, str]]:
    fenced = False
    fence: str | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line_number <= front_matter_lines:
            continue
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)[0]
            if not fenced:
                fenced = True
                fence = marker
            elif marker == fence:
                fenced = False
                fence = None
            continue
        if not fenced:
            yield line_number, line


def parse_text(text: str, path: Path, root: Path) -> Document:
    """Parse Markdown text into a location-aware immutable document model."""
    lines = text.splitlines()
    front_matter, front_matter_lines = _parse_front_matter(lines)
    headings: list[Heading] = []
    links: list[Link] = []
    for line_number, line in _iter_content_lines(text, front_matter_lines):
        heading_match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading_match:
            heading_text = heading_match.group(2).strip()
            headings.append(
                Heading(
                    heading_text,
                    len(heading_match.group(1)),
                    SourceLocation(line_number, line.find(heading_text) + 1),
                    normalize_heading(heading_text),
                )
            )
        for link_match in re.finditer(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+[^)]*)?\)", line):
            links.append(
                Link(
                    link_match.group(1),
                    link_match.group(2),
                    SourceLocation(line_number, link_match.start(2) + 1),
                )
            )
    newline = "\r\n" if "\r\n" in text else "\n"
    relative_path = path.resolve().relative_to(root.resolve())
    return Document(
        path.resolve(), relative_path, text, tuple(headings), tuple(links), front_matter, newline, text.startswith("\ufeff")
    )


def read_document(path: Path, root: Path, max_bytes: int = 10 * 1024 * 1024) -> Document:
    """Read and parse a UTF-8 Markdown file contained by ``root``."""
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ParseError(f"Path is outside repository root: {path}") from exc
    try:
        size = resolved_path.stat().st_size
        if size > max_bytes:
            raise ParseError(f"File exceeds configured size limit: {path}")
        raw = resolved_path.read_bytes()
        text = raw.decode("utf-8-sig")
    except OSError as exc:
        raise ParseError(f"Unable to read {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ParseError(f"File is not valid UTF-8: {path}") from exc
    return parse_text(text, resolved_path, resolved_root)
