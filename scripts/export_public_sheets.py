# -*- coding: utf-8 -*-
"""Export each root master JSON to a stable public-export JSON snapshot for the
site's 방명록형 다운로드 (guestbook-style download) feature on index.html.

Reads the SAME 8 masters `build_master_xlsx.py` bundles (mirror this list if that
one changes) directly from JSON — never touches insurequant_master_tables.xlsx,
so there is no risk of wiping its formula cache (project rule: never openpyxl
load+save the master xlsx).

WHY a separate snapshot instead of fetching the root JSON directly at download
time (inbox/designer/20260828T0300Z, orchestrator): the root masters can be
mid-edit by another concurrent session (shared working tree) at any moment: a
download built straight from the live files could span a transitional state.
A dedicated export step gives a stable, dated point-in-time copy, and gives the
xlsx cover sheet an honest "스냅샷 생성일시" to report — re-run this script
deliberately (publishing/designer) whenever the public download should refresh.

Reads each master via `git show HEAD:<path>` rather than the live working-tree
file — the shared working tree can hold another session's uncommitted edits
(e.g. an in-progress PL_breakdown.json extension) that haven't passed review/
push yet; the last *committed* state is the only version safe to publish.

Output: public_exports/<sheet_name>.json (UTF-8, same row shape as the source).
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "public_exports"

# 표준 "YYYY.NQ" 형태만 분기범위 계산에 쓴다 — 일부 소스(CSM_amortization 등)는
# "annual (filings skim)" 같은 비표준 라벨을 공시분기 자리에 넣어 문자열 정렬 시
# 알파벳이 숫자보다 뒤로 가면서('2'<'a') 최댓값처럼 오판되는 실측 버그가 있었다(2026-08-28).
_QUARTER_RE = re.compile(r"^\d{4}\.\dQ$")


def read_committed_json(rel_path: str):
    """git show HEAD:<rel_path> — last committed bytes, ignoring uncommitted
    working-tree edits (possibly another session's WIP)."""
    out = subprocess.run(
        ["git", "show", f"HEAD:{rel_path}"],
        cwd=REPO, capture_output=True, check=True,
    )
    return json.loads(out.stdout.decode("utf-8"))

# (json file, sheet name) — mirrors build_master_xlsx.py MASTERS (그 리스트가
# 바뀌면 이것도 같이 바꿀 것). "요약" 시트는 실데이터가 아니라 제외(다운로드 쪽에서
# 별도로 표지 시트를 즉석 생성함 — download-survey.js).
MASTERS = [
    ("IFRS17_BS.json", "17BS"),
    ("kics_disclosure.json", "K-ICS공시"),
    ("kics_rate_sensitivity.json", "금리민감도"),
    ("CSM_waterfall.json", "CSM워터폴"),
    ("CSM_amortization.json", "CSM상각"),
    ("NB_CSM_multiple.json", "신계약CSM배수"),
    ("PL_breakdown.json", "손익분해PL"),
    ("dividend.json", "배당"),
]


def main():
    OUT_DIR.mkdir(exist_ok=True)
    manifest = {"generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sheets": {}}
    for json_name, sheet_name in MASTERS:
        rows = read_committed_json(json_name)
        out_path = OUT_DIR / f"{sheet_name}.json"
        out_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        quarters = sorted(set(
            r.get("공시분기") for r in rows
            if r.get("공시분기") and _QUARTER_RE.match(r.get("공시분기"))
        ))
        manifest["sheets"][sheet_name] = {
            "rows": len(rows),
            "quarter_min": quarters[0] if quarters else None,
            "quarter_max": quarters[-1] if quarters else None,
        }
        print(f"  wrote {out_path.relative_to(REPO)}: {len(rows)} rows")
    (OUT_DIR / "_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote _manifest.json (generated_at_utc={manifest['generated_at_utc']})")


if __name__ == "__main__":
    main()
