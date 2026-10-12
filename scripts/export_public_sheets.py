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
# inbox/publishing/20260921T0320Z (owner, 2026-09-21): 자본비율전망 시트의 `_diagnostics`는
# build_master_xlsx.py:_flatten_forward_capital()가 confidence.reasons(내부 게이트 진단
# 문자열)를 담아 두는 칸이다 — 비고와 분리해 여기에만 넣었다. 비고는 그대로 남긴다(드롭 금지).
_DROP_COLS = {"원보험사코드", "_diagnostics"}

# 시트별 추가 제외 열 (공개 스냅샷에서만 빠진다 — 마스터 JSON·내부 마스터 xlsx 시트는 그대로).
# owner 승인 2026-10-12(inbox/publishing/20261012T1440Z): `자본성증권발행현황` 에서 **우리가 한도·인정액
# 계산으로 채운 열**은 공시 값이 아니라 분류 판단과 같은 성격이라 공개본에서 뺀다. 남는 열은 발행 사실
# (회사명·구분·종류·발행일·콜만기도래일·법정만기일·콜근거·액면가·잔액·공시분기·잔액기준일·출처·비고).
# `경과조치`·`경과조치종료일` 은 원천 열이 아니라 발행일 < K-ICS 시행일로 우리가 붙인 구분
# (build_capital_securities_recognition._row 의 `gf`)이라 같이 뺀다. 되돌리기: 이 집합에서 열 이름을 지우고
# exporter 를 다시 돌린다.
_SHEET_DROP_COLS = {
    "자본성증권발행현황": frozenset({
        "기본자본인정액_억", "보완자본인정액_억", "기본자본한도_억", "SCR_억",
        "보완자본인정율", "경과조치", "경과조치종료일",
    }),
}

# 비공개 시트 (owner 2026-10-12 「내린 시트들은 비공개로 돌리고」, inbox/publishing/20261012T1420Z).
# 분류 판단이 들어가는 숫자라 공개 사이트에서 접근 불가로 만든다. 재공개·유료화는 owner 가 나중에 정한다.
# 이 시트들은 공개 스냅샷(`public_exports/<시트>.json`)을 만들지 않고 manifest 에도 싣지 않는다. 마스터 JSON ·
# 마스터 xlsx 시트(`build_master_xlsx.MASTERS`) · output/ 은 저장소에 그대로 둔다(내부 보관).
# 배포 스크립트(`android_push_and_deploy.sh`)의 PRIVATE_PATHS 가 main 에서 이 경로들을 `git rm` 한다 —
# 그 목록과 아래 `private_paths()` 는 tests/test_private_deploy.py 가 같은지 대조한다.
# 되돌리기: PRIVATE_SHEETS 에서 시트를 빼고 PRIVATE_PATHS(.sh) 에서 경로를 빼고 download-survey.js 주석을 풀고
# exporter 를 다시 돌린다.
PRIVATE_SHEETS = ("기본자본소진율", "보완자본소진율", "자본비율전망")
# HTML 이 더는 fetch 하지 않는 루트 JSON. tier1 은 designer 커밋 `1624aba`(K-ICS 큼직한 셀을 타임라인 JSON 계산으로 교체,
# tier1 fetch 제거) 뒤에 넣었다 — 그 전에 넣으면 라이브 패널이 조용히 빈칸이 된다. 새로 HTML 이 이 파일들을 fetch 하게
# 되면 여기서 빼야 한다(test_deploy_assets 의 keep-list 시험이 잡는다).
PRIVATE_ROOT_JSONS = ("kics_tier1_utilization.json", "kics_tier2_utilization.json", "kics_forward_capital.json")


def private_paths():
    """main(라이브)에서 지워야 하는 저장소 상대 경로 전체."""
    return [f"public_exports/{s}.json" for s in PRIVATE_SHEETS] + list(PRIVATE_ROOT_JSONS)


def drop_cols(sheet):
    """그 시트의 공개 스냅샷에서 빠지는 열 이름 전체(공통 + 시트별)."""
    return set(_DROP_COLS) | set(_SHEET_DROP_COLS.get(sheet, ()))


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
    # 2026-09-22 신설(owner 지시). 경영공시 금리위험액 현황 표의 자산·부채총계 6시나리오와
    # 거기서 낸 자산D·부채D·듀레이션갭. K-ICS.html 금리민감도 패널이 이 마스터를 읽는다.
    ("kics_duration_gap.json", "금리듀레이션갭"),
    # 2026-10-11 신설(owner 승인). 잔여보장요소(LRC) + 발생사고요소(LIC) = 보험계약부채. IFRS17.html 섹션 3 콤보의
    # 원천. 기준표시·비고·단위 열은 build_master_xlsx.FLATTEN 이 붙인다(영문 provenance 코드는 한글 문구로 옮겨 나간다).
    ("insurance_liability_portfolio.json", "보험계약부채"),
    # 2026-10-12 신설(owner 승인, 스키마 변경). IFRS17.html 손해율 패널 예실차 블록의 원천. 출처쪽·플래그 열은
    # build_master_xlsx.FLATTEN 이 만든다(내부 파일 경로·영문 코드는 싣지 않는다). 원보험사코드는 _DROP_COLS 로 빠진다.
    ("data/loss_ratio/claims_ae_ratio.json", "보험금예실차비율"),
]


# 공개 스냅샷을 만드는 시트(= MASTERS - 비공개). 게이트도 이 목록을 import 해서 쓴다.
PUBLIC_MASTERS = [m for m in MASTERS if m[1] not in PRIVATE_SHEETS]


def main(only=None):
    """`only` = 시트 이름 하나. 주면 그 시트 파일만 쓰고 manifest 는 **그 시트 항목만** 추가/갱신한다
    (나머지 시트 파일·manifest 의 다른 항목·generated_at_utc·build_id 는 그대로). 다른 세션이 아직
    마스터를 바꾸는 중일 때 새 시트 하나만 먼저 내보내기 위한 것이다(2026-10-11 보험계약부채)."""
    OUT_DIR.mkdir(exist_ok=True)
    # license / build_id: 지문(fingerprint) 키 — 스냅샷이 돌아다닐 때 이용조건·빌드 시점이 같이 간다
    # (artifacts/legal/ip_protection_report_20260911.md §6-6). download-survey.js 는 sheets ·
    # generated_at_utc 만 읽고 build_id 는 있을 때만 표지 시트에 적으므로 구 스냅샷과 호환된다.
    try:
        build_id = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                                  capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        build_id = None
    # validate_live_artifacts CHECK 6 은 manifest 의 `sheets` 만 대조하므로 top-level 지문 키를
    # 늘려도 게이트는 깨지지 않는다(2026-09-11 실측, L636-663). 문구 정본은 루트 LICENSE.
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "license": ("All rights reserved. 열람·출처표기 인용·사내 분석은 자유, "
                    "자동수집(크롤링)으로 통째 긁어가기·대량 재배포·재판매는 금지."),
        "terms_url": "https://www.insurequant.com/privacy.html#terms",
        "copyright": "(c) 2026 InsureQuant (운영자 조상욱). 원천 수치의 권리는 각 공시 주체에게 있음.",
        "build_id": build_id,
        "sheets": {},
    }
    if only is not None:
        if only in PRIVATE_SHEETS:
            raise SystemExit(f"REFUSE: '{only}' 는 비공개 시트다(PRIVATE_SHEETS)")
        if only not in {sn for _jn, sn in MASTERS}:
            raise SystemExit(f"REFUSE: '{only}' 는 MASTERS 에 없다")
        mp = OUT_DIR / "manifest.json"
        if not mp.exists():
            raise SystemExit("REFUSE: --only 는 기존 manifest.json 이 있어야 한다(전체 실행을 먼저)")
        manifest = json.loads(mp.read_text(encoding="utf-8"))   # 최상위 키·다른 시트 항목 보존
    # 비공개 시트: 옛 스냅샷 파일·manifest 항목이 남아 있으면 지운다(되살아난 파일이 라이브로 가지 않게).
    for priv in PRIVATE_SHEETS:
        stale = OUT_DIR / f"{priv}.json"
        if stale.exists():
            stale.unlink()
            print(f"  removed private sheet snapshot {stale.relative_to(REPO)}")
        manifest.get("sheets", {}).pop(priv, None)
    for json_name, sheet_name in PUBLIC_MASTERS:
        if only is not None and sheet_name != only:
            continue
        rows = read_committed_json(json_name)
        flatten = FLATTEN.get(json_name)
        if flatten is not None:
            rows = flatten(rows)
        _drop = drop_cols(sheet_name)
        rows = [{k: v for k, v in r.items() if k not in _drop} for r in rows]
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
    import sys
    _only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    main(only=_only)
