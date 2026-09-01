"""Can the 금리민감도 table be read out of each FY2026_Q2 MD, and does it match?

Ticket 20260831T0700Z 추가사례 2 was closed at the time by adding a raw-PDF fitz
fallback to extract_kics_rate_sensitivity.py, leaving the MDs still missing the
6-8 위험민감도 page. This measures whether the re-converted MDs carry the table
again, and whether the numbers agree with kics_rate_sensitivity.json.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MD_DIR = REPO / "md_inbox" / "FY2026_Q2"
QUARTER = "2026.2Q"


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
    rs = _load("_rs4", REPO / "scripts" / "extract_kics_rate_sensitivity.py")
    master_path = REPO / "kics_rate_sensitivity.json"
    master = json.loads(master_path.read_text(encoding="utf-8")) if master_path.exists() else []
    have = {
        r.get("원보험사코드")
        for r in master
        if str(r.get("공시분기", "")).startswith(QUARTER)
    }

    in_md = []
    not_in_md = []
    for md in sorted(MD_DIR.glob("*.md")):
        code = md.stem.split("_")[0]
        body = _body(md)
        tbl = rs.find_section_table(body)
        (in_md if tbl is not None else not_in_md).append(code)

    print(f"\n=== {QUARTER} 금리민감도: MD 에서 표를 읽을 수 있는 회사 ===\n")
    print(f"  MD 에서 추출 가능 : {len(in_md)} / {len(in_md) + len(not_in_md)}")
    print(f"  MD 에서 불가      : {len(not_in_md)}  {not_in_md}")
    print(f"  마스터 보유       : {len(have)}")
    print(f"  마스터엔 있는데 MD 로는 못 읽는 회사: {sorted(set(have) - set(in_md))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
