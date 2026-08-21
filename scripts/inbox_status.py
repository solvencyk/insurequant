# -*- coding: utf-8 -*-
"""Print the live inbox state so nobody has to trust a summary written earlier.

Every row is read from disk at run time and carries the file's mtime, so a thread
that was answered days ago is visually distinct from one touched today. Read-only.

Usage:
  python scripts/inbox_status.py              # counts + threads awaiting the owner
  python scripts/inbox_status.py --all        # every active thread
  python scripts/inbox_status.py --from owner # only threads this sender must re-verify
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INBOX = REPO / "inbox"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _field(text, key):
    m = re.search(rf"^{key}:\s*(\S+)", text[:800], re.M)
    return m.group(1) if m else None


def _threads():
    for p in sorted(INBOX.rglob("*.md")):
        if p.name == "README.md" or "_resolved" in p.parts:
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        body = re.split(r"^##\s*답변.*$", t, flags=re.M)
        reply = [l.strip() for l in (body[-1] if len(body) > 1 else "").split("\n") if l.strip()]
        yield {
            "path": p, "stage": p.parent.name,
            "status": _field(t, "status"), "from": _field(t, "from"),
            "mtime": dt.datetime.fromtimestamp(p.stat().st_mtime),
            "reply_lines": len(reply), "reply_head": reply[0][:96] if reply else "(답변 없음)",
        }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="list every active thread")
    ap.add_argument("--from", dest="sender", default="owner",
                    help="list answered threads this sender must re-verify (default: owner)")
    args = ap.parse_args(argv)

    rows = list(_threads())
    now = dt.datetime.now()
    print(f"scanned {now:%Y-%m-%d %H:%M:%S}  |  active={len(rows)}  "
          f"resolved={len(list((INBOX / '_resolved').glob('*.md')))}\n")

    grid = Counter((r["stage"], r["status"]) for r in rows)
    stages = sorted({r["stage"] for r in rows})
    cols = ["open", "answered", "resolved", "superseded"]
    print(f"{'stage':12s}" + "".join(f"{c:>12s}" for c in cols))
    for s in stages:
        print(f"{s:12s}" + "".join(f"{grid.get((s, c), 0):>12d}" for c in cols))
    print(f"{'TOTAL':12s}" + "".join(
        f"{sum(v for (_, c2), v in grid.items() if c2 == c):>12d}" for c in cols))

    # "answered" means the recipient replied and the ORIGINAL SENDER still owes a
    # re-verification pass — that is the queue that silently grows.
    sel = [r for r in rows if r["status"] == "answered" and r["from"] == args.sender]
    print(f"\n=== answered, awaiting re-verification by '{args.sender}' — {len(sel)} ===")
    for r in sorted(sel, key=lambda x: x["mtime"]):
        age = (now.date() - r["mtime"].date()).days
        print(f"\n[{r['mtime']:%m-%d %H:%M} · {'today' if age == 0 else f'{age}d ago'}] "
              f"{r['stage']}/{r['path'].name[:60]}")
        print(f"    reply {r['reply_lines']} lines | {r['reply_head']}")

    if args.all:
        print(f"\n=== open — {sum(1 for r in rows if r['status'] == 'open')} ===")
        for r in sorted((r for r in rows if r["status"] == "open"), key=lambda x: x["mtime"]):
            print(f"  [{r['mtime']:%m-%d %H:%M}] {r['stage']}/{r['path'].name[:70]}")


if __name__ == "__main__":
    main(sys.argv[1:])
