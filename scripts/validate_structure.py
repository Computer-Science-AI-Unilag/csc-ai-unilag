#!/usr/bin/env python3
"""Validate the Markdown-first CSE AI UNILAG archive without dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROOT_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "LICENSE",
    "AGENTS.md",
    ".gitignore",
)
REQUIRED_PATHS = (
    "years/2026-2027/README.md",
    "years/2026-2027/curriculum.md",
    "years/2026-2027/instructors.md",
    "years/2026-2027/recordings.md",
    "years/2026-2027/projects.md",
    "years/2026-2027/courses/artificial-intelligence/README.md",
    "years/2026-2027/courses/artificial-intelligence/syllabus.md",
    "years/2026-2027/courses/artificial-intelligence/resources.md",
    "years/2026-2027/courses/artificial-intelligence/modules/01-ai-foundations/README.md",
    "years/2026-2027/courses/artificial-intelligence/modules/01-ai-foundations/week-01/README.md",
    "years/2026-2027/courses/artificial-intelligence/modules/01-ai-foundations/week-02/README.md",
    "resources/README.md",
    "projects/README.md",
    "projects/project-template.md",
)
WEEK_METADATA = (
    "**Academic session:**",
    "**Course:**",
    "**Module:**",
    "**Lecturer:**",
    "**Date:**",
    "**Status:**",
)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def link_target(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    target = target.split(maxsplit=1)[0].strip()
    if not target or target.startswith("#"):
        return None
    lowered = target.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
        return None
    return unquote(target.split("#", 1)[0])


def check_path(path: Path, label: str, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing {label}: {path.relative_to(ROOT).as_posix()}")


def validate_links(markdown: Path, errors: list[str]) -> None:
    text = markdown.read_text(encoding="utf-8")
    for raw in LINK_RE.findall(text):
        target = link_target(raw)
        if target is None:
            continue
        candidate = (markdown.parent / target).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{markdown.relative_to(ROOT)} links outside repository: {raw}")
            continue
        if not candidate.exists():
            errors.append(
                f"{markdown.relative_to(ROOT)} has missing local link: {raw}"
            )


def main() -> int:
    errors: list[str] = []

    for name in REQUIRED_ROOT_FILES:
        check_path(ROOT / name, "core file", errors)
    for relative in REQUIRED_PATHS:
        check_path(ROOT / relative, "required archive file", errors)

    years = ROOT / "years"
    if not years.is_dir():
        errors.append("missing years/ directory")
    else:
        for session in years.iterdir():
            if session.is_dir() and not re.fullmatch(r"\d{4}-\d{4}", session.name):
                errors.append(f"invalid academic-session directory: years/{session.name}")
            if session.is_dir() and not (session / "README.md").is_file():
                errors.append(f"session has no README: years/{session.name}")

    for week_readme in ROOT.glob("years/*/courses/*/modules/*/week-*/README.md"):
        text = week_readme.read_text(encoding="utf-8")
        for metadata in WEEK_METADATA:
            if metadata not in text:
                errors.append(
                    f"{week_readme.relative_to(ROOT)} is missing metadata {metadata}"
                )
        if "## Overview" not in text:
            errors.append(f"{week_readme.relative_to(ROOT)} is missing an Overview section")

    for markdown in ROOT.rglob("*.md"):
        # Templates contain deliberately unresolved example paths. They become
        # valid only after a maintainer copies them into an academic archive.
        if markdown.is_relative_to(ROOT / "templates"):
            continue
        validate_links(markdown, errors)

    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Documentation validation passed.")
    print(f"Checked {len(list(ROOT.rglob('*.md')))} Markdown files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
