"""Do the re-converted MDs reproduce kics_rate_sensitivity.json's 2026.2Q rows?

The sensitivity master was filled from a raw-PDF fitz fallback while the MD had
lost the 6-8 위험민감도 page (inbox 20260831T0700Z 추가사례 2). If the MD now
carries the table again, the master's numbers should be reproducible from it.
Read-only.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CODES = sys.argv[1:] or ["KR0001", "KR0051", "KR0100"]
MD_DIR = REPO / "md_inbox" / "FY2026_Q2"


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
    rs = _load("_rs2", REPO / "scripts" / "extract_kics_rate_sensitivity.py")
    master_path = REPO / "kics_rate_sensitivity.json"
    master = json.loads(master_path.read_text(encoding="utf-8")) if master_path.exists() else []
    for code in CODES:
        mds = sorted(MD_DIR.glob(f"{code}_*.md"))
        if not mds:
            print(f"{code}: no md")
            continue
        body = _body(mds[0])
        tbl = rs.find_section_table(body)
        print(f"\n=== {code} ===")
        if tbl is None:
            print("  MD: no 민감도 section table found")
        else:
            for row in tbl[:12]:
                print("  MD row:", row)
        rows = [
            r
            for r in master
            if r.get("원보험사코드") == code and str(r.get("공시분기", "")).startswith("2026.2Q")
        ]
        print(f"  master rows for 2026.2Q: {len(rows)}")
        for r in rows[:10]:
            print("   ", json.dumps(r, ensure_ascii=False)[:180])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
