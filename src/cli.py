"""Command-line interface for the documentation sync engine."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Sequence

from parser import Document, ParseError, normalize_heading, read_document
from sync import SyncConflictError, SyncError, SyncRule, apply_plan, build_plan


EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CONFIGURATION = 2
EXIT_EXECUTION = 3


def _repository_root(value: str | None) -> Path:
    return Path(value or ".").resolve()


def _documents(root: Path, targets: list[str]) -> tuple[list[Document], list[str]]:
    paths: set[Path] = set()
    failures: list[str] = []
    requested = targets or ["."]
    for target in requested:
        candidate = (root / target).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            failures.append(f"Path is outside repository root: {target}")
            continue
        if candidate.is_dir():
            paths.update(path for path in candidate.rglob("*") if path.suffix.lower() in {".md", ".markdown"})
        elif candidate.is_file() and candidate.suffix.lower() in {".md", ".markdown"}:
            paths.add(candidate)
        else:
            failures.append(f"Markdown target does not exist: {target}")
    documents: list[Document] = []
    for path in sorted(paths):
        try:
            documents.append(read_document(path, root))
        except ParseError as exc:
            failures.append(str(exc))
    return documents, failures


def _check(args: argparse.Namespace) -> int:
    root = _repository_root(args.root)
    documents, failures = _documents(root, args.targets)
    diagnostics: list[dict[str, object]] = []
    for message in failures:
        diagnostics.append({"rule_id": "DOCSYNC-IO", "severity": "error", "message": message})
    for document in documents:
        for required in args.require:
            if not any(heading.text.casefold() == required.casefold() for heading in document.headings):
                diagnostics.append(
                    {
                        "rule_id": "DOCSYNC-SECTION",
                        "severity": "error",
                        "message": f"Missing required section: {required}",
                        "file": str(document.relative_path),
                    }
                )
        for link in document.links:
            if "://" in link.destination or link.destination.startswith(("mailto:", "#")):
                continue
            destination = link.destination.split("#", 1)[0]
            target = (document.path.parent / destination).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                diagnostics.append(
                    {
                        "rule_id": "DOCSYNC-PATH",
                        "severity": "error",
                        "message": f"Link escapes repository: {link.destination}",
                        "file": str(document.relative_path),
                        "line": link.location.line,
                    }
                )
                continue
            if destination and not target.exists():
                diagnostics.append(
                    {
                        "rule_id": "DOCSYNC-LINK",
                        "severity": "error",
                        "message": f"Broken internal link: {link.destination}",
                        "file": str(document.relative_path),
                        "line": link.location.line,
                    }
                )
                continue
            if "#" in link.destination:
                anchor = link.destination.split("#", 1)[1]
                target_document = next((item for item in documents if item.path == target), None)
                if target_document is not None and not any(
                    heading.anchor == normalize_heading(anchor) for heading in target_document.headings
                ):
                    diagnostics.append(
                        {
                            "rule_id": "DOCSYNC-ANCHOR",
                            "severity": "error",
                            "message": f"Missing heading anchor: {link.destination}",
                            "file": str(document.relative_path),
                            "line": link.location.line,
                        }
                    )
    diagnostics.sort(key=lambda item: (str(item.get("file", "")), int(item.get("line", 0)), str(item["rule_id"])))
    result = {"status": "failed" if diagnostics else "passed", "files_scanned": len(documents), "diagnostics": diagnostics}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Scanned {len(documents)} Markdown file(s): {result['status']}")
        for diagnostic in diagnostics:
            location = f"{diagnostic.get('file', '')}:{diagnostic.get('line', '')}"
            print(f"{location} {diagnostic['rule_id']}: {diagnostic['message']}", file=sys.stderr)
    return EXIT_FINDINGS if diagnostics else EXIT_OK


def _validate_config(args: argparse.Namespace) -> int:
    try:
        import tomllib

        with Path(args.config).open("rb") as stream:
            tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return EXIT_CONFIGURATION
    print(f"Configuration is valid: {args.config}")
    return EXIT_OK


def _sync(args: argparse.Namespace, apply: bool) -> int:
    root = _repository_root(args.root)
    rule = SyncRule((root / args.source).resolve(), (root / args.target).resolve(), args.region)
    try:
        plan = build_plan(root, [rule])
        if not apply:
            print(json.dumps({"changes": [asdict(change) for change in plan.changes]}, default=str, indent=2))
            return EXIT_OK
        changed = apply_plan(plan)
        print(f"Applied {len(changed)} synchronization change(s).")
        return EXIT_OK
    except SyncConflictError as exc:
        print(f"Synchronization conflict: {exc}", file=sys.stderr)
        return EXIT_EXECUTION
    except SyncError as exc:
        print(f"Synchronization error: {exc}", file=sys.stderr)
        return EXIT_EXECUTION


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without performing filesystem work."""
    parser = argparse.ArgumentParser(prog="docsync", description="Validate and synchronize Markdown documentation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Validate Markdown files without writing.")
    check.add_argument("targets", nargs="*", help="Files or directories relative to the repository root.")
    check.add_argument("--root", default=".", help="Repository root.")
    check.add_argument("--require", action="append", default=[], help="Required heading text.")
    check.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    config = subparsers.add_parser("config-validate", help="Validate a TOML configuration file.")
    config.add_argument("config", help="Path to the TOML configuration file.")

    for name, help_text in (("sync-preview", "Preview a synchronization change."), ("sync-apply", "Apply a synchronization change.")):
        sync_parser = subparsers.add_parser(name, help=help_text)
        sync_parser.add_argument("source", help="Source file relative to the repository root.")
        sync_parser.add_argument("target", help="Target file relative to the repository root.")
        sync_parser.add_argument("region", help="Named marker region in the target.")
        sync_parser.add_argument("--root", default=".", help="Repository root.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return a process exit code."""
    args = build_parser().parse_args(argv)
    if args.command == "check":
        return _check(args)
    if args.command == "config-validate":
        return _validate_config(args)
    return _sync(args, args.command == "sync-apply")


if __name__ == "__main__":
    raise SystemExit(main())
