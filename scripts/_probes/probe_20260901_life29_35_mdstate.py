"""Do KR0009 / KR0094 / KR0099 have the 생명장기 sub-risk table in their MD?

Distinguishes "the table never reached the markdown" (window/bad_alloc) from
"the table is there but _scan_subitem_rows cannot read it" (extractor issue).
Runs against the pre-re-conversion backup and the current markdown.
"""

from __future__ import annotations

import importlib.util
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CODES = ["KR0009", "KR0094", "KR0099", "KR0029", "KR0051"]
OLD = REPO / "data" / "_derived" / "md_backup_20260901_windowfix" / "md_inbox"
NEW = REPO / "md_inbox" / "FY2026_Q2"
QUARTER = "2026.2Q"

LABELS = ("사망위험", "장수위험", "장해", "장기재물", "해지위험", "사업비위험", "대재해위험")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _body(p: Path) -> str:
    t = p.read_text(encoding="utf-8")
    _, _, rest = t.partition("---\n")
    _, _, body = rest.partition("\n---\n")
    return body


def main() -> int:
    sub = _load("_sub2", REPO / "scripts" / "fill_subitems_to_disclosure.py")
    for code in CODES:
        print(f"\n=== {code} ===")
        for tag, root in (("old", OLD), ("new", NEW)):
            mds = sorted(root.glob(f"{code}_*.md"))
            if not mds:
                print(f"  {tag}: missing")
                continue
            body = _body(mds[0])
            rows = sub._scan_subitem_rows(body, QUARTER)
            label_hits = {lab: body.count(lab) for lab in LABELS if lab in body}
            table_rows = [
                ln.strip()[:110]
                for ln in body.splitlines()
                if ln.strip().startswith("|") and any(lab in ln for lab in LABELS)
            ]
            print(f"  {tag}: _scan_subitem_rows -> {dict(sorted(rows.items()))}")
            print(f"       label counts: {label_hits}")
            for r in table_rows[:6]:
                print(f"       row: {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
