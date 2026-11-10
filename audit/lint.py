#!/usr/bin/env python3
"""Check the rule files for drift. Read-only; exit 1 when anything is found.

Rule files state current practice only. Dates, project IDs and incident
narrative belong in audit/findings.md and commit messages (see AGENTS.md).

Usage: python3 audit/lint.py
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FILES = [REPO / "SKILL.md", *sorted((REPO / "roles").glob("*.md")),
         *sorted((REPO / "references").glob("*.md"))]
MAX_LINES = 200
ID_ALLOW = {"UTF-8", "UTF-16"}

LINE_CHECKS = [
    ("date", re.compile(r"20\d\d-\d\d-\d\d|(?<![\w.-])(?:0?[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])(?![\w-])")),
    ("project-id", re.compile(r"\b[A-Z]{2,}-\d{2,}\b")),
    ("incident", re.compile(r"实测(?!结果)|起因|背景[（(：:]|更正[）)]|停用|问过|当时|本例")),
    ("patch-number", re.compile(r"^\s*\d+[a-z]\. ")),
]
# roles/ and the generic references must not assume one agent (AGENTS.md "改规则" 5).
AGENT = re.compile(r"claude|\bomp\b|cursor|codex|opencode|scratchpad|CronCreate", re.I)
AGENT_NEUTRAL = lambda rel: rel.parts[0] == "roles" or (
    rel.parts[0] == "references" and not rel.name.startswith(("claude-", "omp-", "cursor-")))
REF = re.compile(r"\b([CR])(\d+)(?:\.(\d+))?\b")


def defined_rules():
    """{'C4': {1, 2, ...}} from '## C4 …' headings and the numbered items under them."""
    rules = {}
    for name in ("conductor.md", "master.md"):
        section = None
        for line in (REPO / "roles" / name).read_text().splitlines():
            head = re.match(r"## ([CR]\d+)\b", line)
            if head:
                section = head.group(1)
                rules[section] = set()
            elif line.startswith("## "):
                section = None
            elif section and (item := re.match(r"(\d+)\. ", line)):
                rules[section].add(int(item.group(1)))
    return rules


def main():
    rules, problems = defined_rules(), []
    for path in FILES:
        lines = path.read_text().splitlines()
        rel = path.relative_to(REPO)
        if len(lines) > MAX_LINES:
            problems.append(f"{rel}: {len(lines)} lines (budget {MAX_LINES})")
        for n, line in enumerate(lines, 1):
            for kind, pattern in LINE_CHECKS:
                hit = pattern.search(line)
                if hit and hit.group(0) not in ID_ALLOW:
                    problems.append(f"{rel}:{n}: {kind}: {hit.group(0).strip()}")
            if AGENT_NEUTRAL(rel) and (hit := AGENT.search(line)) and "claude-usage.md" not in line:
                problems.append(f"{rel}:{n}: agent-specific: {hit.group(0)}")
            for prefix, sec, item in REF.findall(line):
                key = prefix + sec
                if key not in rules or (item and int(item) not in rules[key]):
                    problems.append(f"{rel}:{n}: dangling-ref: {key}{'.' + item if item else ''}")
    print("\n".join(problems) or "ok")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
