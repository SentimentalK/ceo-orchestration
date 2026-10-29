#!/usr/bin/env python3
"""Collect read-only audit data for ceo-orchestration runs.

Joins Orca's orchestration.db with each agent's local transcripts by Dispatch ID
and prints one JSON document. Missing data stays null; nothing is written.

Usage: python3 audit/audit.py --since <commit|ISO time> [--until <commit|ISO time>]
"""

import argparse
import json
import re
import sqlite3
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parent.parent
ORCA_DB = HOME / ".config/orca/orchestration.db"
CLAUDE_DIR = HOME / ".claude/projects"
OMP_DIR = HOME / ".omp/agent/sessions"
CURSOR_DIR = HOME / ".cursor/chats"
ID_RE = re.compile(rb"ctx_[0-9a-f]{12}")
HEARTBEAT_MIN_GAP = 30  # roles/conductor.md C3.3a
LAUNCH_SLACK_S = 600


def to_epoch(ref):
    """Commit-ish (in this repo) or ISO time -> epoch seconds (naive time = UTC)."""
    out = subprocess.run(["git", "-C", str(REPO), "show", "-s", "--format=%ct", ref, "--"],
                         capture_output=True, text=True)
    if out.returncode == 0 and out.stdout.strip():
        return float(out.stdout.strip())
    try:
        dt = datetime.fromisoformat(ref.replace("Z", "+00:00"))
    except ValueError:
        raise SystemExit(f"not a commit or ISO time: {ref}")
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).timestamp()


def db_epoch(value):
    """Orca stores 'YYYY-MM-DD HH:MM:SS' (UTC) or ISO with Z."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00").replace(" ", "T")).replace(
        tzinfo=timezone.utc).timestamp()


def iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat(timespec="seconds") if epoch else None


def load_orca(db_path, since, until):
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    dispatches = []
    for row in db.execute("""
        select c.*, t.task_title, t.display_name, t.status as task_status, w.start_options
        from dispatch_contexts c
        left join tasks t on t.id = c.task_id
        left join worker_dispatches w on w.dispatch_id = c.id"""):
        start = db_epoch(row["dispatched_at"] or row["created_at"])
        if start is None or start < since or start >= until:
            continue
        opts = json.loads(row["start_options"] or "{}")
        launch = opts.get("launch") or {}
        req, eff = launch.get("requested") or {}, launch.get("effective") or {}
        dispatches.append({
            "dispatch_id": row["id"],
            "run_id": row["run_id"],
            "task_id": row["task_id"],
            "title": row["display_name"] or row["task_title"],
            "depth": row["depth"],
            "role": {1: "master", 2: "worker"}.get(row["depth"], "violation"),
            "creator_dispatch_id": row["creator_dispatch_id"],
            "agent": eff.get("agent") or req.get("agent") or opts.get("agent"),
            "model_requested": req.get("model"),
            "model_effective": eff.get("model"),
            "effort": eff.get("effort") or req.get("effort"),
            "status": row["status"],
            "failure_count": row["failure_count"],
            "last_failure": row["last_failure"],
            "termination_reason": row["termination_reason"],
            "retry_of": row["retry_of_dispatch_id"],
            "dispatched_at": iso(start),
            "completed_at": row["completed_at"],
            "duration_min": round((db_epoch(row["completed_at"]) - start) / 60, 1)
            if row["completed_at"] else None,
            "assignee_handle": row["assignee_handle"],
        })
    by_id = {d["dispatch_id"]: d for d in dispatches}
    run_ids = {d["run_id"] for d in dispatches}

    beats, questions = defaultdict(list), Counter()
    msg_types = Counter()
    by_handle = {(d["run_id"], d["assignee_handle"]): d for d in dispatches}
    for m in db.execute("select run_id, from_handle, to_handle, type, created_at from messages"):
        t = db_epoch(m["created_at"])
        if m["run_id"] not in run_ids or t is None or t < since or t >= until:
            continue
        msg_types[m["type"]] += 1
        sender = by_handle.get((m["run_id"], m["from_handle"]))
        if sender and m["type"] == "heartbeat":
            beats[sender["dispatch_id"]].append(t)
        if sender and m["type"] == "question":
            questions[sender["dispatch_id"]] += 1
    for d in dispatches:
        ts = sorted(beats[d["dispatch_id"]])
        gaps = [(b - a) / 60 for a, b in zip(ts, ts[1:])]
        d["heartbeats"] = len(ts)
        d["median_heartbeat_gap_min"] = round(statistics.median(gaps), 1) if gaps else None
        d["questions"] = questions[d["dispatch_id"]]

    unreleased = [dict(r) for r in db.execute(
        "select owner_dispatch_id, terminal_handle, release_state, ownership_state, retained_reason "
        "from worker_terminal_resources where release_state != 'released'")
        if r["owner_dispatch_id"] in by_id]
    runs = [dict(r) for r in db.execute(
        "select id, objective, coordinator_handle, created_at from runs") if r["id"] in run_ids]
    return dispatches, runs, msg_types, unreleased


def scan(paths, since, wanted):
    """Map each wanted ID to files containing it; note IDs in the first user turn (the owner)."""
    hits, owners = defaultdict(list), {}
    for p in paths:
        try:
            if p.stat().st_mtime < since:
                continue
            data = p.read_bytes()
        except OSError:
            continue
        found = set(ID_RE.findall(data)) & wanted
        for i in found:
            hits[i].append(p)
        if found and p.suffix == ".jsonl":
            first = first_user_turn(data)
            for i in set(ID_RE.findall(first)) & found:
                owners[i] = p
    return hits, owners


def first_user_turn(data):
    for line in data.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("type") == "user" or (row.get("message") or {}).get("role") == "user":
            return line
    return b""


def first_mention(path, needle):
    for line in path.read_text(errors="ignore").splitlines():
        if needle in line:
            try:
                return db_epoch(json.loads(line).get("timestamp"))
            except ValueError:
                return None
    return None


def claude_usage(path):
    usage, models = {}, Counter()
    for line in path.read_text(errors="ignore").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        msg = row.get("message") or {}
        if row.get("type") != "assistant" or "usage" not in msg:
            continue
        u = msg["usage"]
        usage[msg.get("id") or row.get("uuid")] = (
            u.get("input_tokens", 0), u.get("output_tokens", 0),
            u.get("cache_read_input_tokens", 0), u.get("cache_creation_input_tokens", 0))
        if msg.get("model") != "<synthetic>":
            models[msg.get("model")] += 1
    tot = [sum(x) for x in zip(*usage.values())] or [0, 0, 0, 0]
    return {"input": tot[0], "output": tot[1], "cache_read": tot[2], "cache_write": tot[3],
            "cost_usd": None}, [m for m, _ in models.most_common() if m]


def omp_usage(path):
    tot, cost, models = Counter(), 0.0, Counter()
    for line in path.read_text(errors="ignore").splitlines():
        try:
            msg = json.loads(line).get("message") or {}
        except ValueError:
            continue
        u = msg.get("usage")
        if msg.get("role") != "assistant" or not u:
            continue
        tot.update(input=u.get("input", 0), output=u.get("output", 0),
                   cache_read=u.get("cacheRead", 0), cache_write=u.get("cacheWrite", 0))
        cost += (u.get("cost") or {}).get("total", 0)
        models[f'{msg.get("provider")}/{msg.get("model")}'] += 1
    return {**{k: tot[k] for k in ("input", "output", "cache_read", "cache_write")},
            "cost_usd": round(cost, 4)}, [m for m, _ in models.most_common()]


def attach_transcripts(dispatches, since):
    wanted = {d["dispatch_id"].encode() for d in dispatches}
    claude = list(CLAUDE_DIR.glob("*/*.jsonl"))
    omp = list(OMP_DIR.glob("*/*.jsonl"))
    cursor = list(CURSOR_DIR.glob("*/*/store.db"))
    c_hits, c_own = scan(claude, since, wanted)
    o_hits, o_own = scan(omp, since, wanted)
    k_hits, _ = scan(cursor, since, wanted)

    owned = set()
    for d in dispatches:
        key = d["dispatch_id"].encode()
        path, reader = None, None
        if key in c_own:
            path, reader = c_own[key], claude_usage
        elif key in o_own:
            path, reader = o_own[key], omp_usage
        elif key in k_hits and len(k_hits[key]) == 1:
            path = k_hits[key][0]
        d["transcript"] = str(path) if path else None
        d["tokens"], d["model_seen"] = (reader(path) if reader else (None, []))
        if path:
            owned.add(path)

    # The Conductor is the unowned Claude session that saw a Master's Dispatch ID at launch time
    # (worker-start output); later mentions, e.g. an audit session, do not count.
    conductors = {}
    for m in (d for d in dispatches if d["role"] == "master"):
        launched = to_epoch(m["dispatched_at"])
        for p in c_hits.get(m["dispatch_id"].encode(), []):
            if p in owned or p in conductors:
                continue
            seen = first_mention(p, m["dispatch_id"])
            if seen is None or abs(seen - launched) > LAUNCH_SLACK_S:
                continue
            tokens, models = claude_usage(p)
            conductors[p] = {"run_id": m["run_id"], "transcript": str(p), "tokens": tokens,
                             "model_seen": models,
                             "note": "whole session; may include work outside this window"}
    conductors = list(conductors.values())
    return conductors


def summarize(dispatches, conductors, msg_types, unreleased):
    def add(acc, tokens):
        for k, v in (tokens or {}).items():
            if v is not None:
                acc[k] = round(acc.get(k, 0) + v, 4)

    by_role, by_model = defaultdict(dict), defaultdict(dict)
    for d in dispatches:
        add(by_role[d["role"]], d["tokens"])
        model = (d["model_seen"] or [d["model_effective"] or d["model_requested"]])[0]
        add(by_model[f'{d["agent"]} / {model}'], d["tokens"])
    for c in conductors:
        add(by_role["conductor"], c["tokens"])
    return {
        "dispatches": len(dispatches),
        "by_role": Counter(d["role"] for d in dispatches),
        "by_status": Counter(d["status"] for d in dispatches),
        "by_agent_model": Counter(
            f'{d["agent"]} / {(d["model_seen"] or [d["model_effective"] or d["model_requested"]])[0]}'
            for d in dispatches),
        "retries": sum(1 for d in dispatches if d["retry_of"]),
        "messages": msg_types,
        "tokens_by_role": by_role,
        "tokens_by_agent_model": by_model,
        "no_transcript": sum(1 for d in dispatches if not d["transcript"]),
        "unreleased_terminals": len(unreleased),
    }


def flags(dispatches, unreleased):
    out = []
    for d in dispatches:
        if d["role"] == "violation":
            out.append({"kind": "depth>=3", "dispatch_id": d["dispatch_id"],
                        "detail": f'depth {d["depth"]}, created by {d["creator_dispatch_id"]}'})
        gap = d["median_heartbeat_gap_min"]
        if d["role"] == "master" and gap is not None and gap < HEARTBEAT_MIN_GAP and d["heartbeats"] > 3:
            out.append({"kind": "heartbeat_too_frequent", "dispatch_id": d["dispatch_id"],
                        "detail": f'{d["heartbeats"]} heartbeats, median gap {gap} min'})
        if d["status"] == "failed":
            out.append({"kind": "failed", "dispatch_id": d["dispatch_id"],
                        "detail": d["termination_reason"] or d["last_failure"]})
    for u in unreleased:
        out.append({"kind": "terminal_not_released", "dispatch_id": u["owner_dispatch_id"],
                    "detail": f'{u["release_state"]}/{u["ownership_state"]} {u["retained_reason"] or ""}'.strip()})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", required=True, help="commit in this repo, or ISO time")
    ap.add_argument("--until", help="commit in this repo, or ISO time (default: now)")
    ap.add_argument("--db", default=str(ORCA_DB))
    args = ap.parse_args()
    since = to_epoch(args.since)
    until = to_epoch(args.until) if args.until else datetime.now(timezone.utc).timestamp()

    dispatches, runs, msg_types, unreleased = load_orca(args.db, since, until)
    conductors = attach_transcripts(dispatches, since)
    for d in dispatches:
        d.pop("assignee_handle")
    print(json.dumps({
        "window": {"since": args.since, "until": args.until or "now",
                   "since_utc": iso(since), "until_utc": iso(until)},
        "summary": summarize(dispatches, conductors, msg_types, unreleased),
        "flags": flags(dispatches, unreleased),
        "runs": runs,
        "conductor_sessions": conductors,
        "dispatches": dispatches,
    }, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
