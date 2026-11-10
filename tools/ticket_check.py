#!/usr/bin/env python3
"""Check a Ticket file before it is closed. Read-only; exit 1 when something is missing.

Usage: ticket_check.py <ticket.md> [--repo <target repo> --branch <target branch>]

Checks what roles/conductor.md C2.2, C5.5 and C6 ask for. With --repo and --branch,
every commit SHA cited in the ticket that exists in the repo must be on the branch.
The ticket format itself belongs to the memory repo's rules/tasks.md.
"""
import re
import subprocess
import sys
from pathlib import Path

PENDING = re.compile(r"待用户审核|待审核|待审|待用户决定|待用户确认")


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        sys.exit(__doc__)
    opts = dict(zip(args[1::2], args[2::2]))
    lines = Path(args[0]).read_text().splitlines()
    text, out = "\n".join(lines), []

    if not any(re.match(r"#+ .*(验收|完成定义)", l) for l in lines):
        out.append("没有验收或完成定义段")
    open_boxes = [l.strip() for l in lines if re.match(r"\s*- \[ \]", l)]
    out += [f"未勾选：{l[:80]}" for l in open_boxes]
    out += [f"待用户处理的项不是清单（第 {n} 行）：{l.strip()[:60]}"
            for n, l in enumerate(lines, 1)
            if PENDING.search(l) and not re.match(r"\s*- \[[ x]\]", l) and not l.startswith("#")]

    shas = sorted(set(re.findall(r"(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])", text)))
    repo, branch = opts.get("--repo"), opts.get("--branch")
    if repo and branch:
        git = lambda *c: subprocess.run(("git", "-C", repo) + c, capture_output=True).returncode == 0
        known = [s for s in shas if git("cat-file", "-e", f"{s}^{{commit}}")]
        if not known:
            out.append("票里没有目标仓库里存在的 commit SHA")
        out += [f"commit 不在 {branch} 上：{s}" for s in known
                if not git("merge-base", "--is-ancestor", s, branch)]
    elif not shas:
        out.append("票里没有 commit SHA")

    print("\n".join(out) or "ok")
    sys.exit(1 if out else 0)


if __name__ == "__main__":
    main()
