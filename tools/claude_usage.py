#!/usr/bin/env python3
"""Read Claude subscription usage (same numbers as /usage) via the OAuth usage endpoint.

Uses the access token Claude Code keeps in ~/.claude/.credentials.json (read-only; never
printed, never refreshed here -- Claude Code refreshes it itself). Undocumented endpoint:
if it changes, fall back to asking the user for /usage.

  claude_usage.py            one line: 5h %, reset time, weekly %, Fable %
  claude_usage.py --json     raw JSON
  claude_usage.py --log F    also append a TSV row to F (ts, 5h, week, fable, 5h_reset)
"""
import json, sys, urllib.request, datetime as dt

import os
CRED = os.path.expanduser('~/.claude/.credentials.json')
URL = 'https://api.anthropic.com/api/oauth/usage'

def fetch():
    tok = json.load(open(CRED))['claudeAiOauth']['accessToken']
    req = urllib.request.Request(URL, headers={
        'Authorization': 'Bearer ' + tok, 'anthropic-beta': 'oauth-2025-04-20',
        'User-Agent': 'claude-code/usage-check', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as f:
        return json.load(f)

def local(iso):
    return dt.datetime.fromisoformat(iso).astimezone().strftime('%a %H:%M') if iso else '?'

def main():
    try:
        d = fetch()
    except Exception as e:
        code = getattr(e, 'code', None)
        print(f'usage: ERROR {code or e} (401 = token expired; Claude Code refreshes it when it next runs)')
        sys.exit(2)
    if '--json' in sys.argv:
        print(json.dumps(d, indent=1)); return
    fh, wk = d.get('five_hour') or {}, d.get('seven_day') or {}
    fable = next((l['percent'] for l in d.get('limits', []) if l.get('kind') == 'weekly_scoped'
                  and ((l.get('scope') or {}).get('model') or {}).get('display_name') == 'Fable'), None)
    now = dt.datetime.now().astimezone()
    print(f"{now:%m-%d %H:%M} 5h {fh.get('utilization')}% (reset {local(fh.get('resets_at'))}) | "
          f"week {wk.get('utilization')}% (reset {local(wk.get('resets_at'))}) | Fable {fable}%")
    if '--log' in sys.argv:
        with open(sys.argv[sys.argv.index('--log') + 1], 'a') as f:
            f.write(f"{now.isoformat(timespec='seconds')}\t{fh.get('utilization')}\t{wk.get('utilization')}\t{fable}\t{fh.get('resets_at')}\n")

main()
