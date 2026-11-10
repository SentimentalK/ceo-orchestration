#!/usr/bin/env python3
"""Check that a commit is on the target branch and CI finished green for it. Read-only.

Usage: verify.py <repo path> <sha> <target branch> [--base <sha> --allow <glob> ...]
With --base and --allow, also list files changed in base..sha outside the allowed
globs (the ticket's writable paths). Exit 0 only when every check passes. A repo without CI runs for the SHA fails
the CI check; say so in the ticket instead of treating it as passed.
"""
import fnmatch
import json
import subprocess
import sys


def run(repo, *cmd):
    return subprocess.run(cmd, cwd=repo, capture_output=True, text=True)


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    repo, sha, branch, *rest = sys.argv[1:]
    base = rest[rest.index("--base") + 1] if "--base" in rest else None
    allow = rest[rest.index("--allow") + 1:] if "--allow" in rest else []
    ok = True

    run(repo, "git", "fetch", "--quiet", "origin", branch)
    full = run(repo, "git", "rev-parse", "--verify", f"{sha}^{{commit}}").stdout.strip()
    on_branch = bool(full) and run(
        repo, "git", "merge-base", "--is-ancestor", full, f"origin/{branch}").returncode == 0
    print(f"on origin/{branch}: {'yes' if on_branch else 'NO'}")
    ok &= on_branch

    gh = run(repo, "gh", "run", "list", "--commit", full or sha, "--json",
             "workflowName,status,conclusion")
    if gh.returncode != 0:
        print(f"ci: could not query ({gh.stderr.strip().splitlines()[-1] if gh.stderr.strip() else 'gh failed'})")
        ok = False
    else:
        runs = json.loads(gh.stdout or "[]")
        if not runs:
            print("ci: no runs for this SHA")
            ok = False
        for r in runs:
            state = r["conclusion"] if r["status"] == "completed" else r["status"]
            print(f"ci: {r['workflowName']}: {state}")
            ok &= state == "success"
    if base and allow:
        changed = run(repo, "git", "diff", "--name-only", f"{base}..{full or sha}").stdout.split()
        outside = [f for f in changed if not any(fnmatch.fnmatch(f, g) for g in allow)]
        print(f"scope: {len(changed)} files changed, {len(outside)} outside the allowed paths")
        for f in outside:
            print(f"  outside: {f}")
        ok &= not outside
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
