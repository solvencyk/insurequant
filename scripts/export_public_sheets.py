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

# kics_tier1_utilization / kics_tier2_utilization / kics_forward_capital are the only
# masters that are NOT already long-format on disk (per-company snapshots / per-year
# projection nests). build_master_xlsx.py owns the reshape *and* the 비고 (known-limitation)
# note text; re-typing either here would let the download and the official xlsx drift
# apart on exactly the caveats that must travel with the numbers. Import instead —
# build_master_xlsx.main() is __main__-guarded, so importing it writes nothing.
from build_master_xlsx import FLATTEN  # noqa: E402  (same scripts/ dir → on sys.path)

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "public_exports"

# owner 지시(2026-08-28): 이 필드는 코리안리 내부 코드라 공개 다운로드에 넣으면 안 된다.
# 대시보드(K-ICS/IFRS17/공시보고서 .html)는 이 필드를 회사 선택 조회 키로 그대로 쓰므로
# 루트 마스터 JSON에서는 빼지 않는다 — public_exports/ 스냅샷에서만 제외.
_DROP_COLS = {"원보험사코드"}

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
    ("CSM_sensitivity.json", "가정민감도"),   # 2026-08-30 신설 (IFRS17 가정민감도 ΔCSM)
    ("NB_CSM_multiple.json", "신계약CSM배수"),
    ("PL_breakdown.json", "손익분해PL"),
    ("dividend.json", "배당"),
    # 2026-08-29 신설(inbox/designer/20260829T0700Z). 이 3개는 FLATTEN을 거쳐야 long-format이 되고,
    # 다른 8시트에 없는 "비고" 열이 하나 더 붙는다 — 셀별 known limitation(tier1 분자 BS 대체,
    # tier2 구 산식 폐기, 소진율 100% 초과가 정상인 이유, forward 콜일자 추정)이 거기 실린다.
    # 화면에는 hover로 맥락이 있지만 xlsx만 받아 간 사람에게는 이 열이 유일한 맥락이라
    # 절대 드롭하면 안 된다(_DROP_COLS에 넣지 말 것).
    ("kics_tier1_utilization.json", "기본자본소진율"),
    ("kics_tier2_utilization.json", "보완자본소진율"),
    # 2026-09-01 신설(owner 설계). 자본성증권을 **한 건 단위**로 관리하는 정본 —
    # 소진율·forward outlook 이 이 위에서 산출된다.
    ("kics_capital_securities.json", "자본성증권발행현황"),
    ("kics_forward_capital.json", "자본비율전망"),
]


def main():
    OUT_DIR.mkdir(exist_ok=True)
    manifest = {"generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sheets": {}}
    for json_name, sheet_name in MASTERS:
        rows = read_committed_json(json_name)
        flatten = FLATTEN.get(json_name)
        if flatten is not None:
            rows = flatten(rows)
        rows = [{k: v for k, v in r.items() if k not in _DROP_COLS} for r in rows]
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
    # 밑줄로 시작하는 이름 금지 — GitHub Pages 기본 Jekyll이 _로 시작하는 파일/폴더를
    # 조용히 배포에서 뺀다(.nojekyll 없음, 이 저장소 실측: _manifest.json 404였음 2026-08-28).
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote manifest.json (generated_at_utc={manifest['generated_at_utc']})")


if __name__ == "__main__":
    main()
