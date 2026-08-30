#!/usr/bin/env python3
"""Validate master tables: data/dart/viz/pl_breakdown_master.json + CSM_waterfall.json.

Implements V8 consumer code:
  - CSM_WATERFALL_CLOSING_IDENTITY : 기초+신계약+이자+가정+상각 = 기말  (CSM_waterfall, 억원)
  - PL_BRIDGE_DART_INTERNAL        : 8-eq P&L bridge                  (pl_breakdown_master, 백만원)
  - CSM_AMORT_IDENTITY             : pl.(원수+수재)CSM상각 == wf.CSM상각  (등식, 반올림 폭만)

Both masters long-format. PL master is **백만원**, CSM waterfall is **억원**:
cross-check aligns by ×100 (억→백만). Item names space-normalized.
Tolerance per equation: max(0.1%·|expected|, floor). floor = 2억 (waterfall) / 200백만 (PL).
An equation is SKIPPED if its LHS or any RHS term is missing (None) — 0.0 is a valid value.

Runs `build_root_masters.py` first (idempotent) so root masters reflect the latest
diag/viz source — parser fixes to the source aren't visible in root masters until rebuilt.
Pass --no-build to skip the rebuild and validate the existing root masters as-is.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from _quarter_horizon import QUARTER_FLOOR, quarter_horizon  # noqa: E402

# 2026-08-25: PL 축을 **배포본**으로 재조준했다. 그 전까지 이 게이트는 파서 중간산출물
# `data/dart/viz/pl_breakdown_master.json` 을 읽었다 — CSM 축은 배포본(CSM_waterfall.json)을
# 보는데 PL 축만 상류를 보는 비대칭이었고, 그건 **불변식 1번 위반**이다
# (게이트가 검사하는 파일 = 사용자가 보는 파일). 실측(scripts/_probes/
# probe_20260825_simulate_pl_source_reaim.py):
#   · viz 소스 7,391셀 / 배포본 8,698셀 → **배포본에만 있는 1,307셀이 PL 항등식을 한 번도 안 거쳤다**
#   · 이 게이트가 찍던 `HOLE-PL (통째)` 24건은 **24/24 전부 phantom** — 배포본엔 값이 다 있다
#   · `crosscheck fail` 1건(BNP 2025.4Q)도 phantom — 배포본 기준이면 통과
#   · 대신 PL_BRIDGE 실패가 12 → 26 으로 늘었다(2건은 phantom 소멸, 16건이 처음 검사받아 드러남)
# 방향 근거: `build_root_masters.build_pl` 은 viz 를 읽은 뒤 `_additive_merge(rows, PL_OUT)` 로
# 루트 마스터에 union 병합한다. 즉 **루트가 누적된 정본, viz 는 재생성 가능한 부분입력**이다.
# 다음 세션이 "HOLE-PL 24건이 사라졌다"를 회귀로 오인하지 않도록 SUMMARY 가 phantom 소멸을
# 명시한다(아래 main() 의 PHANTOM 주석·PL_BASELINE 참조).
PL_PATH = "PL_breakdown.json"
PL_SRC_UPSTREAM = "data/dart/viz/pl_breakdown_master.json"   # 참고용(더 이상 검사 대상 아님)
WF_PATH = "CSM_waterfall.json"
BS_PATH = "IFRS17_BS.json"   # PL_OCI_VS_BS_AOCI (항목4 기타포괄손익 누계액) 대조용

# 재조준으로 **처음 검사받게 된** 셀에서 드러난 기지(旣知) PL_BRIDGE 실패 등재부.
# 통째 면제가 아니다 — 건별로 열거하고, 여기 없는 실패가 하나라도 생기면 `pl_new` 가 0 을
# 벗어나 SUMMARY 가 움직이고 골든(tests/test_master_tables_golden.py)이 push 를 막는다.
# parser 가 고칠 때마다 그 줄을 지운다(선례: data/_gold/statutory_reserve_baseline.json).
PL_BRIDGE_BASELINE_PATH = "data/_gold/pl_bridge_baseline.json"


def norm(s: str) -> str:
    return (s or "").replace(" ", "")


# ===========================================================================
# CSM 상각 항등식 — **등식이지 밴드가 아니다** (owner 2026-08-25)
# ===========================================================================
# owner 원문: "0.7~1.4 band 가 아니라 당연히 1 이어야돼."
#
# 이 관계는 이 저장소에 **두 번** 구현돼 있었고 둘 다 밴드였다:
#   · `scripts/validate_data_contract.py` `_XCHK_LO/_HI = 0.4, 2.5`  (배수 밴드, 전 분기)
#   · 이 파일의 `_check_csm_crosscheck`   `OK≤max(5%,300mn) / FAIL>10%` (4Q 한정)
# 게다가 **대조식(comparand)이 서로 달랐다** — data-contract 쪽은 `원수 + 재보험`을 더했는데
# 재보험(출재)은 별도의 **보유 재보험계약자산** 워터폴이라 더하면 안 된다. 실측(346버킷):
#     원수+재보험(당시 식)  ±1% 밖 245건   ← 식 자체가 틀려서 신호가 잡음에 묻혔다
#     원수 단독              ±1% 밖  31건
#     원수+수재              ±1% 밖  20건   ← 정본
# 그 밴드가 실제로 잡은 것은 346버킷 중 **0건**이었고, 에이비엘생명 2025.1~3Q 의 복사 결함
# (비율 1.09~1.12)이 그냥 통과했다. 정정 후 그 6분기 비율은 0.9999~1.0001 이다.
#
# 정본 대조식 = **원수 + 수재**. 워터폴은 "발행한 보험계약"의 CSM 이므로 원수(direct)와
# 수재(assumed reinsurance) 둘 다 포함한다. 출재(ceded, 코리안리 9-1 / 타사 항목 9 재보험)는
# 보유 자산이라 제외한다. 실증: 코리안리 2023.4Q·2024.1Q~2026.2Q 11분기가 원수+수재로
# 정확히 1.0000 (원수 단독이면 0.41~0.71).
#
# 허용오차는 **반올림 폭만**:
#   0.1억  = 두 마스터 저장 그리드의 결합 반올림 상한(워터폴 억원 1자리 ±0.05 +
#            PL 백만원 ±0.005)을 억원 그리드 1스텝으로 올린 값.
#   0.05%  = 워터폴 상각이 **상품라인별 블록의 합**이라(관측 최대 5블록:
#            csm_waterfall_history 의 `summed_product_lines`) 블록별 반올림이 누적되는 폭.
# 실측 346버킷 중 318건이 이 안에 들어온다(p50 0.029억 · p90 0.21억). 밖으로 나가는 28건은
# 전건 원인을 분류해 `data/_gold/csm_amort_identity_ledger.json` 에 **건별 박제**했다 —
# 통째 skip 이 아니고, 잔차 값까지 박아서 데이터가 움직이면 박제가 깨진다.
CSM_AMORT_TOL_ABS_EOK = 0.1
CSM_AMORT_TOL_REL = 0.0005
CSM_AMORT_MIN_EOK = 10.0            # 상각 10억 미만은 대조 의미 없음(반올림이 지배)
CSM_AMORT_LEDGER_PATH = "data/_gold/csm_amort_identity_ledger.json"
# 등재부 잔차 박제가 "이 정도면 같다"고 볼 폭. 데이터가 고쳐지거나 더 나빠지면 깨진다.
CSM_AMORT_PIN_TOL_ABS_EOK = 0.5
CSM_AMORT_PIN_TOL_REL = 0.05

# 커버리지 래칫 baseline — "워터폴 상각은 있는데 PL 버킷이 통째로 없다" 는 자리의 건별 열거.
# 잔차 등재부(위)와는 다른 축이다: 저쪽은 **양쪽 값이 다 있는데 안 맞는** 것이고, 이쪽은
# **한쪽이 순회 대상 자체가 아닌** 것이다. 후자는 게이트에 보고조차 안 됐다(2026-08-26 실측 12건).
CSM_AMORT_COVERAGE_BASELINE_PATH = "data/_gold/pl_amort_coverage_baseline.json"

# PL 쪽 발행계약 CSM 상각 leg. 출재/재보험은 **의도적으로 빠져 있다**(보유 재보험계약자산).
CSM_AMORT_PL_LEGS = ("원수CSM상각", "수재CSM상각")

# FY내 기초 CSM 동일성(WFY) 축의 문서화된 면제 — 전부 legit_restatement
# (parser 판별 2026-06-11, inbox user_xlsx_audit_followup 답변). 원천 공시가 FY 중
# 정정·소급재작성한 건이라 데이터 수정 대상이 아니다(교보는 3Q24 공식 소급재작성 주석).
# **CONT(FY 경계 연속성)에는 적용하지 않는다** — owner 2026-06-16: continuity break 는 무조건 RED.
# 이 셋을 소비하는 곳이 두 군데다: 이 파일의 `_check_plausibility` 와
# `scripts/validate_csm_continuity.py` 의 WITHIN_FY_OPENING_DRIFT. 정본은 여기 하나다.
WFY_EXCEPTIONS = {
    ("교보생명보험", "2023"), ("교보생명보험", "2024"), ("KB라이프생명", "2024"),
    ("한화생명", "2023"), ("현대해상", "2023"), ("케이디비생명보험", "2023"),
    ("메리츠화재해상보험", "2023"), ("에이비엘생명보험", "2023"), ("농협생명보험", "2023"),
}


def csm_amort_tol(amort_eok: float) -> float:
    """CSM 상각 항등식의 허용오차(억원). 반올림 폭만 — 밴드가 아니다."""
    return max(CSM_AMORT_TOL_ABS_EOK, CSM_AMORT_TOL_REL * abs(amort_eok))


def csm_amort_pl_side_eok(plm: dict) -> float | None:
    """PL 쪽 발행계약 CSM 상각 합(억원). 원수 leg 가 없으면 None(대조 불가)."""
    direct = plm.get("원수CSM상각")
    if not isinstance(direct, (int, float)):
        return None
    total = abs(direct)
    for leg in CSM_AMORT_PL_LEGS[1:]:
        v = plm.get(leg)
        if isinstance(v, (int, float)):
            total += abs(v)
    return total / 100.0                      # 백만원 → 억원


def csm_amort_residual(plm: dict, wfm: dict) -> tuple[float, float, float] | None:
    """(잔차억, PL측억, 워터폴측억). 대조 불가(결측·미미)면 None."""
    amort = wfm.get("CSM상각")
    if not isinstance(amort, (int, float)) or abs(amort) < CSM_AMORT_MIN_EOK:
        return None
    pl_eok = csm_amort_pl_side_eok(plm)
    if pl_eok is None or pl_eok == 0:
        return None
    # 두 마스터의 실제 granularity 는 0.01억(백만원)이다. float 잔여를 그대로 두면
    # 푸본현대 2026.1Q 처럼 잔차가 정확히 tol 인 칸이 1e-16 때문에 RED 로 튄다.
    return (round(pl_eok - abs(amort), 2), pl_eok, abs(amort))


def csm_amort_ledger() -> dict:
    """기지 잔차 등재부. 없으면 빈 등재부(= 전부 신규로 취급)."""
    p = ROOT / CSM_AMORT_LEDGER_PATH
    if not p.exists():
        return {"entries": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def csm_amort_ledger_verdict(entry: dict | None, residual: float) -> str:
    """등재부 판정. 'NEW'(미등재) / 'PINNED'(박제 일치) / 'PIN_DRIFT'(박제 이탈)."""
    if entry is None:
        return "NEW"
    pinned = entry.get("residual_eok")
    if not isinstance(pinned, (int, float)):
        return "PIN_DRIFT"
    tol = max(CSM_AMORT_PIN_TOL_ABS_EOK, CSM_AMORT_PIN_TOL_REL * abs(pinned))
    return "PINNED" if abs(residual - pinned) <= tol else "PIN_DRIFT"


def csm_amort_coverage_baseline() -> dict:
    """PL 버킷 부재 커버리지 baseline. 없으면 빈 baseline(= 전부 신규 = 전부 차단).

    빈 파일을 '전부 통과' 가 아니라 '전부 차단' 으로 읽는 것이 이 함수의 계약이다 —
    등재부를 지우면 검사가 느슨해지는 형태는 면제로 위장한 무력화다."""
    p = ROOT / CSM_AMORT_COVERAGE_BASELINE_PATH
    if not p.exists():
        return {"entries": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def load_long(path: str) -> dict:
    d = json.loads((ROOT / path).read_text(encoding="utf-8"))
    idx: dict = defaultdict(dict)
    for r in d:
        idx[(r["원수사명"], r["공시분기"])][norm(r["항목명"])] = r["값"]
    return idx


# 표준 3슬롯(2 생명장기 / 13 자동차 / 14 일반) 밖에 앉는 **추가 LOB 다리**의 항목번호.
# 재보험사가 표준 분류를 안 쓸 때 파서가 여기에 발행한다 — 오늘은 코리안리재보험의
# `2-1`(장기재보험 손익) 하나뿐이지만, 룰은 회사명이 아니라 **번호 패턴**으로 잡는다.
# 회사로 하드코딩하면 다음 재보험사가 들어올 때 같은 사각이 조용히 재발한다
# (`build_pl_breakdown.py` L249-252 의 `_extra_lob` 계약과 같은 형태로 맞춘 것).
# `2-N` 만 더한다: `3-N`~`12-N` 은 그 다리의 **자식**이라(2-1 = 3-1 + 8-1) 같이 더하면 이중계상.
EXTRA_LOB_ITEM_NO = re.compile(r"^2-\d+$")
HYPHEN_ITEM_NO = re.compile(r"^(\d+)-\d+$")
# `2-N` = 추가 LOB **부모**(등식에 가산) · `3-N`~`12-N` = 그 부모의 **자식** 분해(가산하면 이중계상).
# 이 둘 밖의 하이픈 번호(예: 언젠가 나올 `13-1`)는 **이 등식이 아예 모르는 형태**다 — 조용히
# 빠지면 오늘 코리안리에서 난 사고가 그대로 재발하므로 2e 블록에서 건별로 인쇄한다.
KNOWN_HYPHEN_PARENTS = {str(i) for i in range(2, 13)}


def load_pl_extra_lob(path: str) -> tuple[dict, list]:
    """((원수사명, 공시분기) -> Σ 추가 LOB 다리(항목번호 `2-N`) 값, 미지 하이픈 항목 목록).

    `load_long()` 은 **항목명**으로 색인하므로 항목번호를 볼 수 없다 — 그래서 이 축만
    번호로 따로 읽는다. 항목명으로 잡지 않는 이유: 발행사마다 이름이 달라질 수 있고
    (`장기재보험 손익`), 이름 매칭은 새 재보험사가 다른 라벨을 쓰는 순간 다시 무검사가 된다.

    두 번째 반환값은 **커버리지 census** 다. 등식이 아는 하이픈 형태(`2-N` 가산 / `3-N`~`12-N`
    자식)를 벗어난 항목번호를 세어 둔다 — "검사에서 빠졌다"와 "검사 대상이 아니었다"는 다르고,
    후자는 잔차로도 안 드러나므로 따로 세지 않으면 게이트에 보고조차 안 된다."""
    d = json.loads((ROOT / path).read_text(encoding="utf-8"))
    out: dict = defaultdict(float)
    unknown: list = []
    for r in d:
        no = r.get("항목번호")
        if not isinstance(no, str):
            continue
        m = HYPHEN_ITEM_NO.match(no)
        if not m:
            continue
        if EXTRA_LOB_ITEM_NO.match(no):
            if r.get("값") is not None:
                out[(r["원수사명"], r["공시분기"])] += r["값"]
        elif m.group(1) not in KNOWN_HYPHEN_PARENTS:
            unknown.append((r["원수사명"], r["공시분기"], no, r.get("항목명")))
    return dict(out), unknown


def load_pl_dangi(path: str, item_no: int) -> dict:
    """(원수사명, 공시분기) -> 값_당분기 for one 항목번호.  load_long()과 달리 값_당분기를
    읽는다 — PL_OCI_VS_BS_AOCI가 대조하는 건 누계(YTD)가 아니라 그 분기의 순유량이라서다
    (BS 항목4는 저량(point-in-time)이므로 QoQ delta 자체가 이미 그 분기의 유량)."""
    d = json.loads((ROOT / path).read_text(encoding="utf-8"))
    return {(r["원수사명"], r["공시분기"]): r.get("값_당분기")
            for r in d if r["항목번호"] == item_no}


# ---- PL bridge equations: (label, LHS_key, [(RHS_key, sign), ...]) ----
# 보험손익은 dual-form(별도 처리): 회사마다 보험손익 = ΣLOB(bare) 또는 ΣLOB+기타영업수익-기타사업비용(adj).
# 손보(DB/현대/흥국/메리츠 등)는 기타영업수익·기타사업비용이 보험손익 라인 밖(별도 영업비용)이라 bare.
# 삼성화재 등은 adj. 둘 중 하나 닫히면 PASS.
PL_EQS = [
    ("생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
     "생명장기원수손익",
     [("원수CSM상각", 1), ("원수위험조정변동", 1), ("원수예실차", 1), ("기타생명장기원수손익", 1)]),
    ("생명장기재보험손익 = 재보험CSM상각+재보험RA+재보험예실차+기타재보험",
     "생명장기재보험손익",
     [("재보험CSM상각", 1), ("재보험위험조정변동", 1), ("재보험예실차", 1), ("기타생명장기재보험손익", 1)]),
    ("생명장기손익 = 원수손익+재보험손익",
     "생명장기손익",
     [("생명장기원수손익", 1), ("생명장기재보험손익", 1)]),
    ("투자손익 = 투자이익+보험금융손익",
     "투자손익",
     [("투자이익", 1), ("보험금융손익", 1)]),
    ("영업이익 = 보험손익+투자손익",
     "영업이익",
     [("보험손익", 1), ("투자손익", 1)]),
    ("세전이익 = 영업이익+영업외손익",
     "세전이익",
     [("영업이익", 1), ("영업외손익", 1)]),
    ("당기순이익 = 세전-법인세",
     "당기순이익",
     [("세전이익", 1), ("법인세", -1)]),
    # PL_OCI_TOTAL_IDENTITY (owner 티켓 inbox/parser/20260828T0113Z §작업3 룰1): 항목24+25=31.
    # 자명해 보이지만 25/31은 각각 SEPARATE 표준계정(ifrs-full_OtherComprehensiveIncome /
    # ifrs-full_ComprehensiveIncome)에서 독립적으로 뽑히므로, 이 등식은 "24+25로 31을 계산"이
    # 아니라 "두 태그를 제대로 골랐는지"를 검산한다 — 태그를 잘못 짚으면(예: 총포괄손익 대신
    # 지배기업귀속총포괄손익을 골랐다면) 여기서 걸린다. 전 버킷 시뮬레이션(scripts/_probes/
    # census_oci_labels_pass2.py, 282 CIS-보유 셀): 잔차 분포 min=median=p90=max=0.000 —
    # 반올림조차 없는 정확한 항등식이라 DEFAULT_FLOOR(200백만) 그대로 사용.
    ("총포괄손익 = 당기순이익+기타포괄손익",
     "총포괄손익",
     [("당기순이익", 1), ("기타포괄손익", 1)]),
    # PL_OCI_DETAIL_IDENTITY (owner 티켓 inbox/parser/20260828T1600Z): 항목25 = 26+27+28+29+30+32.
    # item32(기타 포괄손익(미분류))는 26-30 슬롯에 안 잡히는 CIS OCI leaf 전부를 합산하는
    # catch-all(fetch_dart_fs.py::_oci32_from_rows) — 이 등식은 "그 카탈로그가 실제로 총계와
    # 맞아떨어지는가"를 검산한다. 전 버킷 시뮬레이션(221개 항 전부 존재 셀, scripts/_probes/
    # residual_distribution_item32.py): 132/221 잔차 정확히 0.000000, 219/221 ≤0.000001(부동
    # 소수점 잡음), 나머지 2건도 rel 0.06%/0.72%로 1% 안. DEFAULT_FLOOR(200백만)로 220/221
    # PASS — 유일한 FAIL 후보(교보생명보험 2025.4Q, 잔차 1283.9)는 pl_bridge_baseline.json에
    # 등재(원인 규명됨: DART 이중 CF헤지 태그, ACCT_OCI_28_FALLBACK 주석 참조 — item28이 두
    # 태그 중 dominant만 취해 나머지 태그값이 항등식엔 안 잡히는 기존 설계, item32 회귀 아님).
    # 항이 하나라도 결측이면(예: 삼성화재 9개 분기 — 26-32 전부 None) 기존 동작대로 skip(fail
    # 아님) — 다른 PL_EQS 항목과 동일한 "결측 시 추측 금지" 원칙.
    ("기타포괄손익 = FVOCI채무증권+보험계약금융(OCI)+위험회피파생상품+FVOCI지분증권+재보험금융(OCI)+기타(미분류)",
     "기타포괄손익",
     [("FVOCI채무증권평가손익", 1), ("보험계약금융손익(OCI)", 1), ("위험회피파생상품평가손익", 1),
      ("FVOCI지분증권평가손익", 1), ("재보험금융손익(OCI)", 1), ("기타포괄손익(미분류)", 1)]),
]

# 등식별 abs floor (백만원). 영업이익은 0근처 회사(KDB 등) 과민 방지로 완화.
EQ_FLOOR = {"영업이익 = 보험손익+투자손익": 600.0}
DEFAULT_FLOOR = 200.0

# ---- 등식별 adj(대체) 형태 -----------------------------------------------------
# 발행사가 같은 등식을 두 형태로 공시한다. 위 dual-form 이 `보험손익` 층에서 하던 것과
# 같은 일을 `생명장기손익` 층에서도 해야 하는 회사가 있다 — **기타사업비용이 보험손익
# 라인 밖이 아니라 그 안의 세 번째 다리**인 회사들이다.
#
# 근거(raw, 2026-08-26 validation 재확인 · inbox/parser/20260825T1120Z §4):
#   교보라이프플래닛 FY2024 사업보고서 20250328001411_00760.xml `(단위 : 원)` 손익계산서 —
#     Ⅰ. 보험손익            (26,015,543,184)
#       1. 보험영업수익        19,825,745,982   (1) 보험수익 19,783,534,758 / (2) 재보험수익 42,211,224
#       2. 보험서비스비용      45,841,289,166   (1) 보험비용 37,629,857,356 / (2) 재보험비용 1,950,010,570
#                                              (3) **기타사업비용 6,261,421,240**
#   원수 = 19,783,534,758 − 37,629,857,356 = −17,846,322,598 = item3
#   재보험 = 42,211,224 − 1,950,010,570 =  −1,907,799,346 = item8
#   합계  = item3 + item8 − 기타사업비용 = −26,015,543,184 = item2 (원 단위까지 일치)
# 즉 `기타사업비용` 은 원수·재보험과 **나란한 세 번째 다리**이고, 룰이 그 항을 안 쓴 것이
# 결함이었다(데이터가 아니라 룰의 갭). 전 버킷 시뮬레이션: 3건 닫힘 · 파손 0 · 잔존 0.
# min-|잔차| 후보 선택이라 통과 버킷을 깨뜨릴 수 없고, 대신 **잔차가 하필 기타사업비용과
# 같은 크기인 미래의 추출결함은 통과시킨다** — 그 값이 라벨 정확일치로 독립 추출된 셀이라
# 감수한 비용이며, 오늘 그런 버킷은 위 3건뿐이다.
PL_EQ_ADJ = {
    "생명장기손익 = 원수손익+재보험손익": [("기타사업비용", -1)],
}

# ===========================================================================
# 등식별 증거력 — **주석이 아니라 코드가 읽는 상수다** (2026-08-29)
# ===========================================================================
# `pass=3057` 중 1,608(52.6%)이 **구성상 참**이다. 빌더가 우변의 한 항을 좌변에서 빼서
# 만들기 때문에 그 등식은 산수상 깨질 수가 없다 — 상류에서 잘못 뽑혀도 잔차는 항상 0 이다.
# 실측(변이시험, scripts/_probes/probe_20260829_pl_eqs_mutation.py, 주입 크기
# max(10,000백만, |v|×30%) = floor 의 50배 이상):
#
#   mutation            NAIVE det%   CONSTRUCTIVE det%   잡은 룰
#   item5  원수RA           94.3%          0.0%          없음
#   item6  원수예실차        97.2%          0.0%          없음
#   item9  재보험CSM상각     93.5%          0.0%          없음
#   item10 재보험RA         94.6%          0.0%          없음
#   item11 재보험예실차      94.3%          0.0%          없음
#   item19 보험금융손익      97.9%          0.0%          없음
#   item22 세전이익        100.0%          0.0%          없음  ← 2f 가 이것만 메운다
#   item23 법인세         100.0%          0.0%          없음 (빌더가 22-24 로 덮음)
#
# NAIVE = 마스터의 그 칸만 흔든다. CONSTRUCTIVE = 같은 칸을 흔들고 **빌더가 그 칸으로부터
# 계산하는 하류 항을 빌더와 똑같이 다시 계산한다**(파서가 틀리면 실제로 일어나는 형태).
#
# **왜 상수로 두나.** 무력한 줄 모르고 pass 를 세는 것이 이 저장소가 반복해서 당한
# false-green 의 정확한 형태다. 아래 판정을 SUMMARY 가 인쇄하므로 "3057 통과"가 아니라
# "진짜 1,135 · 구성상 1,608 · 부분 314" 로 읽힌다. 새 등식을 PL_EQS 에 추가하면서 여기
# 등재하지 않으면 `_assert_pl_eq_evidence_declared()` 가 즉시 죽는다(선언 없는 등식 금지).
#
# **동어반복 탐지기(tests/test_identity_tautology.py)를 그대로 못 쓴다.** 그 귀무모형
# `_taut_null_p0(k)` 는 각 항이 등식 자신의 단위로 반올림됐다고 가정하는데(K-ICS 는 백만원
# 정수) PL 마스터는 원÷1e6 이라 원 단위 정밀도가 살아 있어 **건전한 항등식도 잔차가 정확히
# 0** 이다. 실측 9축 전부 RED 이고 excess 1위(1.93)가 하필 진짜 검산 축인 EQ9 였다 —
# 통계가 두 부류를 분리하지 못한다. 판별자는 통계가 아니라 **write-path 추적 + 변이시험**이다.
# 재현: scripts/_probes/probe_20260829_taut_detector_on_pl.py
EQ_REAL = "REAL"            # 좌·우변이 서로 다른 원천에서 독립적으로 온다 → 깨질 수 있다
EQ_TAUTOLOGY = "TAUTOLOGY"  # 빌더가 우변 한 항을 좌변에서 빼 만든다 → 구성상 참, 영원히 통과
EQ_PARTIAL = "PARTIAL"      # 이 등식만 보면 동어반복이지만 같은 항을 보는 다른 축이 있다

# 보험손익 dual-form / leg-coverage 블록(PL_EQS 밖, `_check_pl_bridge` 안에서 직접 검산)의 라벨.
PL_DUAL_LABELS = ("보험손익(dual)", "보험손익(leg-coverage)")

PL_EQ_EVIDENCE = {
    "보험손익(dual)":
        (EQ_REAL, "item1 은 FS-API 표준계정, ΣLOB 은 주석 분해 — 서로 다른 원천"),
    "보험손익(leg-coverage)":
        (EQ_REAL, "위와 같음. 결측 다리를 0 으로 채워 판정하므로 SKIP 으로 숨지 않는다"),
    "생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수":
        (EQ_TAUTOLOGY, "item7 = 3-(4+5+6) plug (build_pl_breakdown.py assemble). "
                       "item7 은 저장소 전체에 다른 write-path 가 없다 — "
                       "**자기를 검사하는 등식의 잔차로만 존재하는 항목**이다. "
                       "결과: item5·item6 은 어떤 룰의 입력도 아니다"),
    "생명장기재보험손익 = 재보험CSM상각+재보험RA+재보험예실차+기타재보험":
        (EQ_TAUTOLOGY, "item12 = 8-(9+10+11) plug (같은 함수). "
                       "결과: item9·item10·item11 은 어떤 룰의 입력도 아니다"),
    "생명장기손익 = 원수손익+재보험손익":
        (EQ_PARTIAL, "item2 = 3+8 plug 지만 item2 는 보험손익 dual/leg-coverage 등식의 "
                     "ΣLOB 항이라 그쪽에서 독립 대조된다"),
    "투자손익 = 투자이익+보험금융손익":
        (EQ_TAUTOLOGY, "item18 = 17-19 plug 가 2층(fetch_dart_fs._parse L403-404 + "
                       "build_pl_breakdown.assemble L213-215) 전부 무조건. "
                       "결과: item19 는 어떤 룰의 입력도 아니다"),
    "영업이익 = 보험손익+투자손익":
        (EQ_REAL, "1·17·20 이 각각 독립 표준계정. 되맞춤(item17 += item19)은 410 중 3건뿐"),
    "세전이익 = 영업이익+영업외손익":
        (EQ_TAUTOLOGY, "item21 = 22-20 plug 410/418 (fetch_dart_fs._parse L392-394). "
                       "그 중 380 건은 독립 영업외수익/비용 계정이 있었는데 안 썼다. "
                       "item21 이 독립소스인 8/418 에서만 진짜 검산"),
    "당기순이익 = 세전-법인세":
        (EQ_TAUTOLOGY, "item23 = 22-24 plug 418/418 무조건 (assemble L226-228). "
                       "원천 법인세 계정은 418/418 존재하는데 버려진다 — "
                       "**그 버려지는 값을 되살려 대조하는 것이 아래 2f** 다"),
    "총포괄손익 = 당기순이익+기타포괄손익":
        (EQ_REAL, "24·25·31 이 각각 독립 표준계정(ifrs-full_ProfitLoss / "
                  "OtherComprehensiveIncome / ComprehensiveIncome) — 태그 오선택을 잡는다"),
    "기타포괄손익 = FVOCI채무증권+보험계약금융(OCI)+위험회피파생상품+FVOCI지분증권+재보험금융(OCI)+기타(미분류)":
        (EQ_REAL, "item32 는 25 의 잔차가 아니라 CIS leaf **카탈로그 합** "
                  "(fetch_dart_fs._oci32_from_rows) — 카탈로그가 틀리면 깨진다(실 FAIL 1건)"),
}


def _assert_pl_eq_evidence_declared() -> None:
    """모든 등식이 증거력 판정을 갖는지. **선언 없는 등식을 금지한다.**

    새 등식을 `PL_EQS` 에 추가하면서 판정을 안 붙이면 그 pass 는 아무 표시 없이 총합에
    섞인다 — 동어반복이면 그때부터 조용한 false-green 이다. 여기서 즉시 죽인다."""
    declared = set(PL_EQ_EVIDENCE)
    labels = {lab for lab, _l, _t in PL_EQS} | set(PL_DUAL_LABELS)
    missing = sorted(labels - declared)
    ghost = sorted(declared - labels)
    if missing:
        raise SystemExit(
            f"PL_EQ_EVIDENCE 에 판정이 없는 등식: {missing}\n"
            "  등식을 추가했으면 TAUTOLOGY/REAL/PARTIAL 중 하나를 근거와 함께 선언하라. "
            "판정 없는 pass 는 무력한 줄 모르고 세어진다.")
    if ghost:
        raise SystemExit(
            f"PL_EQ_EVIDENCE 에만 있고 실제 등식이 아닌 라벨: {ghost} — 개명/삭제됐다면 같이 고쳐라")


_assert_pl_eq_evidence_declared()

# **등식으로는 영원히 못 보는 항목** — plug 를 없애지 않는 한 원천 재대조가 유일한 수단이다.
# 이건 실패가 아니라 **결론**이다. 위 CONSTRUCTIVE 변이시험이 그것을 실측으로 보였다.
#
# 특히 item6(원수예실차)에 주의하라. 2026-08-29 에 3개사 50분기를 채웠는데,
# **폐쇄식(`3 = 4+5+6+7`)은 그 값을 전혀 검증하지 못한다** — item7 이 잔차라 무엇을 넣어도
# 닫힌다. 그날 실제로 쓴 검증은 전부 **독립 앵커**였다:
#   · 농협생명   보험수익 510,001 이 원문 표와 일치
#   · 미래에셋생명 3중 대사 594,378,172,139 (원 단위)
#   · 에이비엘생명 산문 공시 50억/3억
#   · 서울보증보험 소계 검산
# 다음 사람이 "폐쇄식이 닫혔으니 맞다" 로 판단하지 않도록 여기 못 박는다.
#
# item9(재보험CSM상각)도 같다. 유일한 독립 대조원 후보였던 CSM 워터폴에 **출재 축이 없다** —
# `build_csm_waterfall_master.py` 가 `_EXCLUDE_KW = ("재보험","출재",…)` 로 전 단계에서
# 의도적으로 배제하고, 마스터 `CSM_waterfall.json` 은 6항목(기초·신계약·이자·가정·상각·기말)
# 단일 축이다(2,172행 전수 확인, 출재 항목 0). 그 배제는 옳다 — 출재는 **보유 재보험계약자산**의
# 별도 워터폴이라 발행계약 워터폴에 더하면 안 된다(실측: 원수+재보험 식은 346버킷 중 245건이
# ±1% 밖, 원수+수재는 20건). 따라서 `CSM_AMORT_PL_LEGS` 를 넓히는 방식의 대안 축은 **없다**.
# 만들려면 파서가 출재 rollforward 를 별도 마스터로 추출해야 한다(원문에는 있다 — 캡션
# "원수 및 출재 …" 다수). 그것은 parser/ifrs17 레인의 신규 과제이고 이 게이트의 몫이 아니다.
PL_ITEMS_UNCHECKABLE_BY_EQUATION = {
    5:  "원수위험조정변동 — item7 plug 가 흡수. 원천 주석 재대조만이 수단",
    6:  "원수예실차 — 같음. **독립 앵커로만 검증됨**(위 주석의 4개사 사례)",
    9:  "재보험CSM상각 — item12 plug 가 흡수. CSM 워터폴에 출재 축이 없어 교차대조 불가",
    10: "재보험위험조정변동 — item12 plug 가 흡수",
    11: "재보험예실차 — item12 plug 가 흡수",
    19: "보험금융손익 — item18 = 17-19 plug 가 2층 모두 흡수",
    23: "법인세 — item23 = 22-24 plug 가 418/418 덮어씀(원천 계정은 2f 가 되살려 쓴다)",
}

# ===========================================================================
# 회사별 LOB 택소노미 — **표준 3슬롯은 보편 분류가 아니다** (2026-08-30)
# ===========================================================================
# PL 스키마의 LOB 슬롯 세 개(item2 `생명장기손익` · item13 `자동차손익` · item14 `일반손익`)는
# **국내 원수 손해보험사의 관행**을 그대로 옮긴 것이지 보험업 전체의 분류가 아니다.
# 발행사가 그 슬롯에 해당하는 사업을 **아예 영위하지 않으면** 그 칸은 세 상태 중 하나가 아니라
# 셋 다 다르다 —
#
#   결측(None, 못 뽑았다)   ≠   0.0(영위하는데 손익이 0)   ≠   미해당(N/A, 그 LOB 자체가 없다)
#
# 이 게이트는 지금까지 앞의 둘만 구별했다. 그래서 코리안리재보험의 item13 은 14분기 내내
# `0-fill=자동차손익` 으로 인쇄됐고, 그것을 본 사람은 **추출 실패로 읽을 수밖에 없었다**
# (실제로 2026-08-29 에 그렇게 읽혀 parser 레인으로 진단 요청이 나갔다, commit 15a61d1).
# 아래 등재부가 그 셋째 상태를 명시한다.
#
# **0 으로 채우지 않는다.** 0 은 "영위하는데 이번 분기 손익이 없었다"는 주장이고, 미해당은
# 그 주장을 하지 않는다. 마스터에 0 을 쓰면 화면·집계가 그 회사를 자동차 영위사로 센다.
#
# --- 회사별 실측 택소노미 (원문 컬럼 헤더 기준) ---
#
#   코리안리재보험(KR1000)  전업 재보험사.  `계약 유형` = **장기보험 · 생명보험 · 일반보험**
#     자동차 컬럼이 원문에 없다. FY2026_Q2 raw `20260814003862.xml` 의 보험수익/보험비용 표
#     헤더 실측: `계약 유형 | 합계 | 장기보험 | 생명보험 | 일반보험`.
#     빌더 매핑(`pl_breakdown/companies.py::extract_tier2_coreanre`):
#         생명보험 -> item2  (표준 슬롯, 라벨은 `생명장기손익`)
#         장기보험 -> item2-1 (`장기재보험 손익`, `_extra_items` 로 발행)
#         일반보험 -> item14
#         자동차   -> **없음 = 미해당**
#     >>> **leg-coverage 등식이 이 회사에서 `2-1` 을 왜 더해야 하는지가 여기서 나온다.**
#     이 회사는 LOB 이 3개인데 그 3개가 표준 3슬롯에 1:1 로 안 들어간다 — 생명과 장기가
#     별개 LOB 인데 표준 슬롯은 둘을 `생명장기` 한 칸으로 합쳐 놨다. 그래서 빌더가 장기를
#     `2-1` 로 넘치게 발행했고, `item1 = item2 + item13 + item14` 만 보는 등식은 그 항을
#     통째로 빠뜨려 12분기를 오탐했다(최대 잔차 41,051백만 = 4,105억).
#     즉 `2-N` 가산은 임의 보정이 아니라 **이 회사의 LOB 분류가 스키마 슬롯과 어긋난다는
#     사실의 직접적 귀결**이다. 다른 재보험사가 들어오면 같은 검토를 다시 해야 한다.
#
#   서울보증보험(KR0150)  국내 유일 종합 보증보험사.  `항목` = **보증 · 해외 · 상해 · 자동차 · 기타**
#     생명장기 leg 자체가 없다(ZLEG_LEGIT "ALL"). 자동차 컬럼은 **존재하되 전량 수재**다 —
#     FY2026_Q1 raw `20260515000688.xml` 보험수익 표 셀 실측:
#         원수: 보증 587,072,949 · 해외 762,496 · 상해 - · **자동차 -** · 기타 991,185
#         수재: 보증 -          · 해외 32,001,864 · 상해 5,786,143 · **자동차 12,516,475** · 기타 13,317,316
#     그래서 이 회사의 item13 은 "자동차 원수 미영위" 인데도 **미해당이 아니다**(수재로 실재).
#     등재부에 넣지 않는 이유가 이것이다 — 슬롯 이름만 보고 단정하면 정반대로 판정한다.
#
# 표 전체(38사)와 슬롯별 근거는 `docs/domains/claude-agent-ifrs17.md` §4.3.
#
# **이 등재부는 면제가 아니다.** 등재해도 leg-coverage 등식은 그대로 돌고 깨지면 그대로 RED 다.
# 등재가 바꾸는 것은 **판정이 아니라 그 결측을 어떻게 읽어야 하는가** 뿐이다. 그리고 등재 자체가
# `_check_lob_taxonomy()` 로 반증가능하다 — 마스터에 값이 생기면 등재부가 거짓이 되고 RED 다.
LOB_KEYS = ("생명장기손익", "자동차손익", "일반손익")   # item2 / item13 / item14

LOB_LEG_NA: dict[str, dict[str, str]] = {
    "코리안리재보험": {
        "자동차손익":
            "전업 재보험사 — 원문 `계약 유형` 컬럼이 장기보험·생명보험·일반보험 3개뿐, "
            "자동차 컬럼 부재(FY2026_Q2 raw 20260814003862.xml 헤더 실측 + 빌더 "
            "extract_tier2_coreanre 독스트링 'NO 자동차'). owner 결정 2026-08-30, "
            "ticket inbox/validation/20260830T0200Z__orchestrator__KR1000__lob_taxonomy_exception.md",
    },
}


def _assert_lob_leg_na_wellformed() -> None:
    """등재부의 슬롯 이름이 실제 LOB 슬롯인지, 근거 문장이 붙어 있는지.

    오타난 슬롯 이름은 **아무 것도 덮지 않으면서 덮은 것처럼 보인다** — 이 저장소가
    반복해서 당한 형태라 import 시점에 죽인다."""
    for co, legs in LOB_LEG_NA.items():
        bad = sorted(set(legs) - set(LOB_KEYS))
        if bad:
            raise SystemExit(
                f"LOB_LEG_NA[{co!r}] 의 슬롯 이름이 LOB_KEYS 에 없다: {bad}\n"
                f"  LOB_KEYS = {LOB_KEYS}. 오타난 이름은 아무 것도 덮지 않는다.")
        for leg, why in legs.items():
            if not (why or "").strip():
                raise SystemExit(
                    f"LOB_LEG_NA[{co!r}][{leg!r}] 에 근거가 없다 — "
                    "원문 컬럼 헤더 실측과 결정 출처를 적어라. 근거 없는 등재는 면제다.")


_assert_lob_leg_na_wellformed()

# 분기 지평 — **마스터에서 파생한다** (`scripts/_quarter_horizon.py`, 근거는 그 독스트링).
# 2026-08-29 까지 이 자리는 `2026.1Q` 로 끝나는 리터럴이었고 파일 최초 커밋(9243445) 이후
# 아무도 안 늘렸다. 그래서 2026.2Q 를 배포한 날 아래 축이 전부 그 분기를 **순회조차 안 했다**:
# coverage_holes · qoq_scan · spike · wfy · continuity. 실측으로 `HOLE-PL 흥국화재 2026.2Q`
# 하나가 그 사각에 숨어 있었다. 여기에 분기를 손으로 다시 적지 말 것 —
# `tests/test_quarter_horizon.py` 가 막는다.
QS = quarter_horizon()


def load_qoq_cfg():
    return yaml.safe_load((ROOT / "config" / "qoq_thresholds.yaml").read_text(encoding="utf-8"))


def qoq_threshold(cfg, yaml_key, domain="ifrs17"):
    items = (cfg.get("items", {}).get(domain, {}) or {})
    if yaml_key and yaml_key in items and "threshold" in items[yaml_key]:
        return items[yaml_key]["threshold"]
    dd = (cfg.get("defaults", {}).get(domain, {}) or {})
    return dd.get("threshold") or cfg["defaults"]["global"]["threshold"]


def prev_quarter(q):
    i = QS.index(q) if q in QS else -1
    return QS[i - 1] if i > 0 else None


def net_quarterly(idx, co, item, q):
    """YTD 누적값 → net 분기 증분. 같은 FY 내 cur-prev, FY 1Q는 cur 자체."""
    y, qq = q.split(".")
    qn = int(qq[0])
    cur = idx.get((co, q), {}).get(item)
    if cur is None:
        return None
    if qn == 1:
        return cur
    pv = idx.get((co, f"{y}.{qn - 1}Q"), {}).get(item)
    return None if pv is None else cur - pv


def qoq_scan(idx, items, floor, cfg):
    """items: [(항목명, yaml_key, cumulative)]. 2024+ 분기만 평가. YELLOW(anomaly).
    - cumulative(flow: 신계약/이자/상각/손익) → **YoY**: 같은 분기 전년 YTD 대비.
      net-quarterly QoQ는 분기 계절성(1Q net vs 4Q net)으로 노이즈가 커 부적합.
      YoY는 같은 누적 시점 비교라 계절성이 상쇄돼 추세 이상만 잡힘.
    - non-cumulative(stock: 기말 CSM) → QoQ: 잔액이라 직전 분기 대비 안정적."""
    rows = []
    eval_q = [q for q in QS if not q.startswith("2023.")]
    for (co, q) in idx:
        if q not in eval_q:
            continue
        for item, yk, cum in items:
            thr = qoq_threshold(cfg, yk)
            if cum:  # flow → YoY
                y, qq = q.split(".")
                ref = f"{int(y) - 1}.{qq}"
                basis = "yoy"
            else:    # stock → QoQ
                ref = prev_quarter(q)
                basis = "qoq"
            if ref is None:
                continue
            a, b = idx.get((co, q), {}).get(item), idx.get((co, ref), {}).get(item)
            if a is None or b is None or abs(b) < floor:
                continue
            delta = (a - b) / abs(b)
            if abs(delta) > thr:
                rows.append((co, q, item, delta, thr, a, b, basis))
    return rows


def coverage_holes(idx, key_items, active_min=7):
    """데이터 누락(hole) census. SKIP으로 숨기지 말고 명시.
    active 회사(핵심항목 보유 분기 >= active_min)의 빈 분기 = hole.
    그 미만(외국계·소형 = 애초에 미공시)은 structural로 분리(검증 제외).
    2023 분기는 사이트 비노출(사용자 결정)이라 known으로 분리 — real hole은 2024+."""
    cos = sorted({co for (co, _) in idx})
    real, known, struct = [], [], []
    for co in cos:
        present = [q for q in QS if any(idx.get((co, q), {}).get(k) is not None for k in key_items)]
        if not present:
            continue
        if len(present) < active_min:
            struct.append((co, len(present)))
            continue
        for q in QS:
            m = idx.get((co, q), {})
            vals = [m.get(k) for k in key_items]
            if all(v is None for v in vals):
                kind = "통째"
            elif any(v is None for v in vals):
                kind = "부분"
            else:
                continue
            (known if q.startswith("2023.") else real).append((co, q, kind))
    return real, known, struct


def rebuild_root_masters() -> None:
    """Run build_root_masters.py so root masters reflect the latest diag/viz source.
    parser가 소스(csm_waterfall_master_diag / pl_breakdown_master)를 고쳐도 이 빌드를
    안 돌리면 루트 CSM_waterfall.json / PL_breakdown.json(검증 대상)에 반영 안 됨.
    idempotent라 항상 선행 호출 (끄려면 --no-build)."""
    script = ROOT / "scripts" / "build_root_masters.py"
    print("[build] build_root_masters.py 실행 (루트 마스터 최신화) ...")
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"[build] ⚠️ 빌드 실패 (rc={r.returncode}) — 기존 마스터로 검증 진행.")
        if r.stderr:
            print("[build] " + r.stderr.strip().splitlines()[-1][:160])
    else:
        for ln in [l for l in (r.stdout or "").splitlines() if l.strip()][-2:]:
            print(f"[build] {ln[:120]}")
    print()


SENS_PATH = "data/dart/viz/sensitivity_heatmap.json"


# 민감도 표 쪽 회사명 -> CSM 마스터의 `원수사명`. 앵커를 못 찾으면 이 룰이 조용히 또래비교로
# 떨어지므로 별칭이 곧 판정력이다(같은 집합이 validate_live_artifacts.COMPANY_ALIAS 에도 있다).
_SENS_NAME_ALIAS = {
    "미래에셋생명": "미래에셋생명보험", "삼성생명": "삼성생명보험", "코리안리": "코리안리재보험",
    "아이비케이연금보험": "IBK연금보험", "케이비라이프생명보험": "KB라이프생명",
    "에이아이지손해보험": "AIG손해보험", "엠지손해보험": "예별손해보험",
}


def _sens_csm_anchor() -> dict:
    """{원수사명: 최신 기말 CSM(억원)} — 민감도 크기의 유일한 정당한 잣대."""
    out, seen = {}, {}
    try:
        rows = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return out
    for e in rows:
        if e.get("항목번호") != 6:
            continue
        n, q, v = str(e.get("원수사명") or ""), str(e.get("공시분기") or ""), e.get("값")
        if n and isinstance(v, (int, float)) and q >= seen.get(n, ""):
            seen[n], out[n] = q, float(v)
    return out


def sensitivity_unit_sanity():
    """CSM 민감도 단위/블록 sanity — **또래 중앙값이 아니라 그 회사 자신의 기말 CSM** 대비.

    2026-06-14 owner claim 2 로 만들 때는 또래 median 규모비를 썼다(현대해상=원 단위라
    삼성화재의 ~640배였던 케이스의 회귀가드). 그 잣대는 **큰 쪽에는 맞지만 작은 쪽에서는
    회사 규모와 단위오류를 구별하지 못한다** — 어떤 보험사도 또래의 1000배일 수는 없지만,
    또래의 1/1000 인 회사는 얼마든지 실재한다. 실측(2026-08-30): 카카오페이손해는 기말
    CSM 이 3.4억인 진짜 소형사인데 민감도 0.69억(자기 CSM 의 20.3% = 정상 밴드 한복판)을
    두고 두 달 넘게 RED 였다. 반대로 라이나생명은 유배당 소블록을 집어 자기 CSM 의
    0.004% 짜리 값을 싣고 있었는데 같은 잣대로는 카카오페이와 구별되지 않았다.

    그래서 잣대를 **자기 CSM 대비**로 바꾼다. 전 회사 실측 분포(앵커 확보 30/32)는
    0.77% ~ 34.3% 한 덩어리이고, 고장난 두 건만 그 밖에 있었다(라이나 0.004%,
    에이아이지 34,334%). 임계는 그 관측 분포에서 잡았다:

      RED   : rel < 0.05%  (관측 최소 0.77% 의 1/15 — 100배+ 단위오류·소블록 오선택)
              rel > 300%   (빌더의 3배 가드가 앵커 부재로 안 걸린 경우의 이중망)
      YELLOW: rel < 0.5% 또는 rel > 100%

    앵커가 없으면(마스터에 그 회사 CSM 이 없음) 종전 또래비교로 떨어지되 **작은 쪽은
    YELLOW 로만** 낸다 — 앵커 없이 소형사와 단위오류를 가르는 것은 불가능하고, 그걸
    RED 로 내는 것이 바로 위 오탐의 원인이었다. 큰 쪽(>1000배)은 앵커 없이도 RED 다.
    """
    sp = ROOT / SENS_PATH
    sens_red, sens_yellow = [], []
    if not sp.exists():
        return sens_red, sens_yellow
    sdoc = json.loads(sp.read_text(encoding="utf-8"))
    anchor = _sens_csm_anchor()
    scales = []
    for c in sdoc.get("companies", []) or []:
        ds = [abs(s["csm_delta"]) for s in (c.get("scenarios") or [])
              if isinstance(s.get("csm_delta"), (int, float))]
        if ds:
            n = c.get("company")
            own = anchor.get(n) or anchor.get(_SENS_NAME_ALIAS.get(n, n))
            scales.append((n, max(ds), c.get("unit"), c.get("unit_detected"), own))
    if len(scales) < 5:
        return sens_red, sens_yellow
    vals = sorted(v for _, v, _, _, _ in scales)
    med = vals[len(vals) // 2] or 1.0
    for name, mx, unit, ud, own in scales:
        if own and own > 0:
            rel = mx / own
            if rel < 5e-4 or rel > 3.0:
                sens_red.append((name, mx, rel, unit, ud))
            elif rel < 5e-3 or rel > 1.0:
                sens_yellow.append((name, mx, rel, unit, ud))
            continue
        ratio = mx / med                       # 앵커 없음 — 또래비교로 폴백
        if ratio > 1000:
            sens_red.append((name, mx, ratio, unit, ud))
        elif ratio > 100 or ratio < 1e-2:
            sens_yellow.append((name, mx, ratio, unit, ud))
    return sens_red, sens_yellow


def sensitivity_direction_sanity():
    """User 2026-06-14 rule-of-thumb: CSM이 증가하는 시나리오면 당기손익도 증가해야 한다(반대도 동일).
    100% 법칙은 아니나(onerous-block에선 실제 역행 가능) 의심 신호 → sign(csm_delta)≠sign(pl_impact)이면
    YELLOW flag. 파싱오류(손익/자본 컬럼 오선택·부호) 또는 실효과(흥국생명 해지율=source-faithful 역행)를
    한 망으로 triage. 0근방 노이즈는 floor로 제외. 게이트 비차단(보고만)."""
    sp = ROOT / SENS_PATH
    flags = []
    if not sp.exists():
        return flags
    sdoc = json.loads(sp.read_text(encoding="utf-8"))
    for c in sdoc.get("companies", []) or []:
        name = c.get("company")
        for s in (c.get("scenarios") or []):
            cd, pl = s.get("csm_delta"), s.get("pl_impact")
            if not (isinstance(cd, (int, float)) and isinstance(pl, (int, float))):
                continue
            if abs(cd) >= 1.0 and abs(pl) >= 1.0 and (cd > 0) != (pl > 0):
                ratio = abs(cd) / abs(pl) if pl else float("inf")
                flags.append((name, s.get("risk"), s.get("shock"), cd, pl, ratio))
    return flags


def _check_plausibility(wf: dict) -> tuple[list, list, list, list, list]:
    """CSM absolute-value sanity the closing identity misses: dup / spike /
    continuity break / FY-opening mismatch / zero-amortization. Prints its own
    section and returns (dup_rows, spike_rows, cont_rows, wfy_rows, zamort_rows).
    Split out of main() 2026-07-22; pinned by tests/test_master_tables_golden.py."""
    # ===== 1b. CSM_PLAUSIBILITY (절댓값 sanity — closing identity가 못 잡는 것) =====
    # closing identity는 내부 산술 합산만 봐서 (a)분기 복붙 (b)기말 QoQ 폭락 같은
    # 절댓값 이상을 통과시킴. 별도 plausibility 체크로 보강.
    wf_co: dict = defaultdict(dict)
    for (co, q), m in wf.items():
        wf_co[co][q] = m
    dup_rows = []     # (co, [분기...]) — 같은 회사 내 기말 CSM 동일 (복붙 의심)
    spike_rows = []   # (co, q_prev, q, prev, cur, dq) — 기말 QoQ |Δ|>50%
    for co, qmap in sorted(wf_co.items()):
        # 복붙: 같은 회사 내 서로 다른 분기의 기말 CSM이 소수점까지 동일.
        # CSM 잔액은 매분기 변하므로 동일 = 분기 데이터 복붙(2025를 2024로 채움 등) 강력 의심.
        end_sigs: dict = defaultdict(list)
        for q, m in qmap.items():
            e = m.get("기말CSM")
            if e is not None:
                end_sigs[round(e, 1)].append(q)
        for v, qq in end_sigs.items():
            if len(qq) > 1:
                dup_rows.append((co, sorted(qq)))
        for i in range(1, len(QS)):
            p = qmap.get(QS[i - 1], {}).get("기말CSM")
            c = qmap.get(QS[i], {}).get("기말CSM")
            if p is not None and c is not None and abs(p) > 1e-6 and abs((c - p) / p) > 0.50:
                spike_rows.append((co, QS[i - 1], QS[i], p, c, (c - p) / p))

    # 연속성: FY[t] 각 분기 기초 CSM = FY[t-1].4Q 기말 (YTD 연초값 고정 방식).
    # 작년 기말 = 올해 기시. 하한 FY(2023)는 전년 기말이 없어 SKIP.
    # QS 에서 파생한다 — 2026-08-29 까지 여기도 리터럴이었고 FY2026 이 `["2026.1Q"]` 라
    # **2026.2Q 는 연속성 검사 대상이 아니었다**(QS 와 별개의 두 번째 지평 하드코딩).
    FY_Q: dict[str, list[str]] = defaultdict(list)
    for _q in QS:
        FY_Q[_q[:4]].append(_q)
    FY_Q.pop(QUARTER_FLOOR[:4], None)
    PREV_CLOSE = {fy: f"{int(fy) - 1}.4Q" for fy in FY_Q}
    # 연속성(continuity) break = 무조건 RED. 원천 "소급재작성"으로 보이는 케이스라도 raw 대조로
    # 확정되기 전에는 면제하지 않는다 (owner 2026-06-16: self-closing identity는 opening을 검증 못 함 —
    # 2026.1Q 5사 기시 misparse를 '재작성'으로 오판한 사건. 기시≠직전기말이면 그냥 RED). 메모리: continuity-break-is-red.
    # owner는 면제(self-closing) 대신 **데이터 정정** 방식 채택(2026-06-20): 재작성/misparse 과거 cell은 후속 분기
    # 공시의 '전기(비교)' 테이블에서 재작성값을 추출해 마스터를 통일 → cont 자연 해소(parser 발주). 면제셋 미사용.
    cont_rows = []   # (co, q, 기초, 전년말기말, 전년말분기)
    for co, qmap in sorted(wf_co.items()):
        for fy, qq in FY_Q.items():
            pc = qmap.get(PREV_CLOSE[fy], {}).get("기말CSM")
            if pc is None:
                continue
            for q in qq:
                o = qmap.get(q, {}).get("기초CSM")
                if o is None:
                    continue
                if abs(o - pc) > max(0.005 * abs(pc), 2.0):
                    cont_rows.append((co, q, o, pc, PREV_CLOSE[fy]))

    # FY내 기초 일관성: YTD 컨벤션상 같은 FY 모든 분기의 기초 CSM은 동일(=전년말)해야 함.
    # 사용자 적발(2026-06-10): 롯데 2023.2Q 기초가 3Q/4Q와 다름 — FY경계 연속성만 보고
    # FY내 동일성을 안 봐서 미스. 2023도 검사 가능(전년 기말 없이 FY내 상호비교라).
    # Documented exceptions (parser 판별 2026-06-11, inbox user_xlsx_audit_followup 답변):
    # 전부 legit_restatement — 원천 공시가 FY 중 정정/소급재작성(교보는 3Q24 공식 소급재작성 주석).
    # 데이터 수정 대상 아님 → EXC 표시만, 게이트 제외. (CONT/연속성에는 적용 안 함 — owner 2026-06-16:
    # continuity break는 무조건 RED. WFY[FY내 동일성]만 이 면제 유지.)
    # 2026-08-25: 모듈 레벨로 올렸다 — `validate_csm_continuity` 가 같은 축을 검사하는데
    # 자기 면제셋이 없어서, 폭을 조이면 여기서 이미 판별이 끝난 건이 거기서 다시 RED 로
    # 튀었다. 면제를 두 번 쓰지 않도록 **정본을 한 곳에 두고 import** 한다.
    wfy_rows = []   # (co, fy, {q: 기초})
    wfy_exc = []
    ALL_FY = sorted({q[:4] for q in QS})    # QS 파생 (종전 ("2023".."2026") 리터럴)
    for co, qmap in sorted(wf_co.items()):
        for fy in ALL_FY:
            opens = [(q, qmap[q].get("기초CSM")) for q in QS
                     if q.startswith(fy + ".") and q in qmap and qmap[q].get("기초CSM") is not None]
            if len(opens) < 2:
                continue
            vals = [v for _, v in opens]
            if max(vals) - min(vals) > max(0.005 * abs(max(vals)), 2.0):
                rec = (co, fy, {q: round(v, 1) for q, v in opens})
                (wfy_exc if (co, fy) in WFY_EXCEPTIONS else wfy_rows).append(rec)

    # 불가능한 0: CSM상각 == 정확히 0 (경제적으로 불가능 — 보유계약 있으면 상각 발생).
    # 사용자 룰 지시(2026-06-10): 미래에셋 2025.2Q+ 상각 0 적발. None은 coverage가 잡지만
    # 0.0은 "present"로 통과하던 맹점.
    # parser AMORT_ZERO 스펙(2026-06-10): 상각 0인데 기초/기말이 양수면 RED.
    # 기초=기말=0(미보유) 정상사는 가드로 제외. None 0값은 coverage/ZLEG 담당.
    zamort_rows = []  # (co, q)
    for (co, q), m in sorted(wf.items()):
        a = m.get("CSM상각")
        o, c = m.get("기초CSM"), m.get("기말CSM")
        endpoints_pos = (o is not None and o > 0) or (c is not None and c > 0)
        if a is not None and a == 0 and endpoints_pos:
            zamort_rows.append((co, q))

    print()
    print("=" * 78)
    print(f"1b. CSM_PLAUSIBILITY  복붙(dup)={len(dup_rows)} 기말QoQ폭변(spike)={len(spike_rows)} "
          f"연속성위반(cont)={len(cont_rows)} FY내기초불일치(wfy)={len(wfy_rows)} 상각0(zamort)={len(zamort_rows)}")
    print("=" * 78)
    for co, qq in dup_rows:
        print(f"  DUP   {co:14s} 기말 CSM 동일(복붙 의심): {qq}")
    for co, qp, q, p, c, dq in spike_rows:
        print(f"  SPIKE {co:14s} {qp}->{q}: 기말 {p:.0f} -> {c:.0f} ({dq*100:+.0f}%)")
    for co, q, o, pc, pcq in cont_rows:
        print(f"  CONT  {co:14s} {q} 기초={o:.0f} ≠ {pcq} 기말={pc:.0f}  (Δ{o-pc:+.0f})")
    for co, fy, opens in wfy_rows:
        print(f"  WFY   {co:14s} FY{fy} 기초 불일치: {opens}")
    for co, fy, opens in wfy_exc:
        print(f"  WFYEX {co:14s} FY{fy} (documented: legit restatement) {opens}")
    for co, q in zamort_rows:
        print(f"  ZAMRT {co:14s} {q} CSM상각=0 (불가능 — 추출오류)")
    return dup_rows, spike_rows, cont_rows, wfy_rows, zamort_rows


def _check_pl_bridge(pl: dict, extra_lob: dict | None = None,
                     unknown_hyphen: list | None = None,
                     evidence_out: dict | None = None) -> tuple[int, list, int, list, list]:
    """PL bridge identity (2) + 생명장기 zero-legs (2b) + impossible-zero legs (2c).
    All three read pl_breakdown and share one print block, so they stay together.
    `extra_lob` = load_pl_extra_lob() 첫 반환값((co,q) -> Σ 항목번호 `2-N`); 생략하면 추가 LOB
    다리 없이 종전 3항 등식으로 돈다. `unknown_hyphen` = 그 두 번째 반환값(커버리지 census).
    `evidence_out` = 넘기면 `{REAL/TAUTOLOGY/PARTIAL: pass 수}` 로 채운다 — pass 를 증거력별로
    갈라 SUMMARY 에 인쇄하기 위한 것이고, **반환 arity 는 유지**한다(기존 호출부 보호).
    Returns (pb_pass, pb_fail, pb_skip, zleg_rows, zerolegs_rows). Split out of
    main() 2026-07-22; pinned by tests/test_master_tables_golden.py."""
    extra_lob = extra_lob or {}
    unknown_hyphen = unknown_hyphen or []
    na_of = LOB_LEG_NA          # (co) -> {leg: 근거}; 결측을 "미해당"으로 읽게 하는 등재부
    ev = {EQ_REAL: 0, EQ_TAUTOLOGY: 0, EQ_PARTIAL: 0}
    eq_pass_count = defaultdict(int)

    def _credit(label: str) -> None:
        ev[PL_EQ_EVIDENCE[label][0]] += 1
        eq_pass_count[label] += 1
    # ===== 2. PL_BRIDGE (pl_breakdown_master, 백만원) =====
    pb_pass = pb_skip = 0
    pb_fail = []
    eq_fail_count = defaultdict(int)
    legcov_pass, legcov_fail, nolhs_rows = [], [], []
    for (co, q), m in sorted(pl.items()):
        # --- 보험손익 dual-form (bare ΣLOB / adj +기타영업수익-기타사업비용) ---
        # `보험손익`(항목1)의 폐쇄식 `1 = 2+13+14(+15-16)` 은 **PL_EQS 밖의 이 블록**이
        # 검사한다. 2026-08-29 재확인: 오케스트레이터 티켓
        # (inbox/validation/20260829T1500Z__orchestrator__MULTI__insurance_result_closure_missing.md)
        # 은 "PL_EQS 9식에 이 등식만 없다"고 봤지만, 실측하면 이 파일 최초 커밋(135e6ff)부터
        # 있었고 그 실패 10건은 전부 pl_bridge_baseline.json 에 이미 등재돼 있다.
        #
        # 진짜 사각은 등식의 부재가 아니라 **결측 시 통째 SKIP** 이었다 — item1/2/13/14 중
        # 하나라도 None 이면 그 버킷의 보험손익은 어떤 룰도 안 봤다(356 버킷 중 71 = 19.9%).
        # 게다가 그 결측은 coverage census 도 못 봤다: 그쪽 key_items 는
        # 보험손익/생명장기손익/당기순이익 셋뿐이라 **13(자동차)·14(일반)의 결측은 애초에
        # 세지 않는다.** 코리안리재보험은 그렇게 13분기 내내 자동차 다리가 없는 채로
        # 두 검사를 모두 통과했다(2024+ 10분기, 잔차 최대 41,051백만 = 4,105억).
        #
        # 2026-08-29 신설(leg-coverage): LOB 다리가 결측이면 **0 으로 채워 검산한다.**
        #   닫히면 -> 그 다리는 정말 0 이다(발행사가 안 쓰는 LOB). SKIP 이 아니라 PASS 로 확정.
        #   깨지면 -> 결측 다리가 진짜 돈을 싣고 있다는 뜻이고 잔차가 그 하한이다 -> FAIL.
        # 즉 "결측이니 넘어간다"를 "결측이어도 산수로 판정한다"로 바꾼다. 생/손보 카테고리로
        # 다리의 유무를 단정하지 않고 회사별 실데이터가 판정하게 두는 형태이기도 하다.
        # 전 버킷 시뮬레이션(scripts/_probes/probe_20260829_item1_legcoverage_final.py):
        # 오늘 검사받던 285 버킷의 판정은 **한 건도 안 바뀐다**(regression 0).
        # SKIP 71 -> 18, PASS 275 -> 288(+13), FAIL 10 -> 50(+40).
        # 기타영업수익·기타사업비용 adj 후보는 기존 규칙 그대로(둘 다 있을 때만) 만든다 —
        # 0-fill 경로에 추가 후보를 붙이면 masking 면만 넓어지고, 실측상 그 후보가 필요한
        # 버킷도 없었다(13건 전부 기존 adj 로 닫혔다).
        bo = m.get("보험손익")
        if bo is None:
            # 좌변 자체가 없으면 등식을 세울 수 없다. 이 축은 coverage census(key_items 에
            # 보험손익 포함)의 몫이라 RED 로 올리지 않되, 조용히 사라지지 않게 건별로 인쇄한다.
            # 오늘 18건 전부 2023 분기(사이트 비노출)다 — 2024+ 가 여기 뜨면 그건 회귀다.
            pb_skip += 1
            nolhs_rows.append((co, q))
        else:
            raw_lob = [m.get(k) for k in LOB_KEYS]
            zf = [k for k, v in zip(LOB_KEYS, raw_lob) if v is None]
            # 결측 다리를 **미해당(등재부에 있음)** 과 **설명되지 않은 결측** 으로 가른다.
            # 판정에는 안 쓴다 — 등재는 면제가 아니므로 등식은 양쪽 다 똑같이 검산한다.
            # 인쇄만 갈라서, 다음 사람이 `0-fill=자동차손익` 을 추출 실패로 오독하지 않게 한다.
            na_legs = [k for k in zf if k in na_of.get(co, {})]
            zf_unex = [k for k in zf if k not in na_of.get(co, {})]
            # 2026-08-29 b: **추가 LOB 다리를 더한다.** 표준 3슬롯이 LOB 의 전부라는 가정이
            # 이 등식의 오탐 원인이었다.
            # **왜 코리안리재보험만 `2-N` 이 필요한가 = 그 회사의 LOB 택소노미 때문이다**
            # (근거·원문 헤더 실측은 위 `LOB_LEG_NA` 주석, 표는 domains/claude-agent-ifrs17 §4.3).
            # 요지: 그 회사의 LOB 은 장기/생명/일반 **3개**인데 표준 슬롯이 생명과 장기를
            # `생명장기` 한 칸으로 합쳐 놔서 1:1 로 안 들어간다 → 빌더가 장기를 `2-1`
            # (`장기재보험 손익`)로 넘치게 발행 → 표준 3슬롯만 보는 등식은 그 항을 통째로
            # 빠뜨렸다. 12분기 내내 "item13(자동차) 결측이 돈을 싣고 있다"고 찍혔지만 실제로는
            # 자동차 LOB 자체가 원문에 없고(원문 `계약 유형` 컬럼 3개, commit 15a61d1)
            # 잔차는 통째로 이 미포함 항이었다. 더하면 12분기 전부 |잔차| ≤ 2.8백만원.
            # 빌더의 Tier-2 RC 게이트는 이미 같은 항을 더하고 있었다(`_extra_lob`) — 즉
            # **빌더와 검증기가 서로 다른 등식을 쓰고 있었다**. 이제 같은 등식을 쓴다.
            # 새 재보험사·특수 분류사가 들어오면 `2-N` 을 무조건 더하는 것이 맞는지 그 회사의
            # 택소노미로 다시 확인해야 한다 — 슬롯 이름이 보편이라는 가정이 여기서 깨졌다.
            xlob = extra_lob.get((co, q), 0.0)
            bare = sum(0.0 if v is None else v for v in raw_lob) + xlob
            cands = [bare]
            oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
            if oi is not None and oe is not None:
                cands.append(bare + oi - oe)
            diff = min((c - bo for c in cands), key=abs)
            label = "보험손익(leg-coverage)" if zf else "보험손익(dual)"
            if abs(diff) > max(0.001 * abs(bo), DEFAULT_FLOOR):
                pb_fail.append((co, q, label, round(bo, 1), round(diff, 1)))
                eq_fail_count[label] += 1
                if zf:
                    legcov_fail.append((co, q, round(bo, 1), round(diff, 1),
                                        zf_unex, xlob, na_legs))
            else:
                pb_pass += 1
                _credit(label)
                if zf:
                    legcov_pass.append((co, q, round(diff, 1), zf_unex, xlob, na_legs))
        # --- 나머지 등식 ---
        for label, lhs_key, terms in PL_EQS:
            lhs = m.get(lhs_key)
            if lhs is None or any(m.get(k) is None for k, _ in terms):
                pb_skip += 1
                continue
            rhs = sum(sign * m[k] for k, sign in terms)
            # adj(대체) 형태: 발행사가 같은 등식에 다는 추가 다리(PL_EQ_ADJ 주석 참조).
            # 항이 하나라도 결측이면 후보를 만들지 않는다(추측 금지).
            adj = PL_EQ_ADJ.get(label)
            if adj and all(m.get(k) is not None for k, _ in adj):
                rhs = min((rhs, rhs + sum(s * m[k] for k, s in adj)), key=lambda c: abs(c - lhs))
            diff = rhs - lhs
            if abs(diff) > max(0.001 * abs(lhs), EQ_FLOOR.get(label, DEFAULT_FLOOR)):
                pb_fail.append((co, q, label, round(lhs, 1), round(diff, 1)))
                eq_fail_count[label] += 1
            else:
                pb_pass += 1
                _credit(label)

    # ===== 2b. PL_ZERO_LEGS (생명장기 sub-item 0/None 무더기 = 추출실패) =====
    # 사용자 적발(2026-06-10): 현대해상 등 생명장기 sub-item이 xlsx에서 전부 0으로 보임.
    # JSON 확인 결과 정확히-0이 아니라 **None**(추출 누락)이고 xlsx가 None→0 렌더링.
    # 기존 coverage는 헤드라인 3개(보험손익/생명장기손익/당기순이익)만 봐서 sub-item hole 사각.
    # 룰: 보험손익이 있는 active 행에서 sub-item 10종 중 (None 또는 정확히 0.0)이 ≥4 → flag.
    # (0.0도 함께 — 0=0+0+0 자명통과 맹점. 2023 분기는 사이트 비노출이라 제외.)
    PL_LEG_ITEMS = ["생명장기원수손익", "원수CSM상각", "원수위험조정변동", "원수예실차",
                    "기타생명장기원수손익", "생명장기재보험손익", "재보험CSM상각",
                    "재보험위험조정변동", "재보험예실차", "기타생명장기재보험손익"]
    # 불가능-0 leg (owner 확정 2026-06-11): 장기보험 영위사면 아래 4종은 0원일 수 없다.
    # 0.0이면 추출오류 — None(coverage가 잡음)과 별개로 명시 RED.
    IMPOSSIBLE_ZERO_LEGS = ["생명장기원수손익", "기타생명장기원수손익",
                            "생명장기재보험손익", "기타생명장기재보험손익"]
    # 무재보험사 legit-zero 재보험 leg (owner 확정, data/_gold/user_pl_confirmed_cells.json):
    # 재보험 미영위사(예: 순수 연금사 IBK연금보험 — 재보험 5개 leg 전부 0 + 원수분해 정확히 닫힘)는
    # 재보험 leg이 정당하게 0.0 → 추출오류 아님. (에이비엘은 leg이 None이라 애초에 미해당.)
    IMPOSSIBLE_ZERO_EXEMPT = {"IBK연금보험": {"생명장기재보험손익", "기타생명장기재보험손익"}}
    zerolegs_rows = []   # (co, q, item)
    for (co, q), m in sorted(pl.items()):
        if q.startswith("2023."):
            continue
        exempt = IMPOSSIBLE_ZERO_EXEMPT.get(co, set())
        for k in IMPOSSIBLE_ZERO_LEGS:
            if m.get(k) == 0 and k not in exempt:
                zerolegs_rows.append((co, q, k))

    # Legit-absent (parser 판별 2026-06-11): None이 추출실패가 아니라 원천 비공시인 케이스.
    # "ALL" = 생명장기 분해 자체 미공시(감사보고서-only 소형사/보증보험). 항목 set = 해당 항목만 분리 미공시.
    # 단 (co, q) 튜플은 *특정 분기만* 예외(진짜 미공시 confirmed) — 회사 전체 면죄 금지.
    ZLEG_LEGIT = {
        # 현대해상은 legit_absent 오판이었음(owner 답지로 2026.1Q 분리손익 실재 확인) → 회사 면제 제거.
        "에이비엘생명보험": {"생명장기재보험손익", "재보험CSM상각", "재보험위험조정변동", "기타생명장기재보험손익"},
        # IBK연금보험 = 순수 연금사 무재보험 (owner 확정, user_pl_confirmed_cells.json). 재보험 leg 전부 0.
        "IBK연금보험": {"생명장기재보험손익", "재보험CSM상각", "재보험위험조정변동", "재보험예실차", "기타생명장기재보험손익"},
        "서울보증보험": "ALL",          # 보증보험 — 생명장기 leg 자체 없음
        "AIG손해보험": "ALL",           # 감사보고서-only, 분해 미공시
        "교보라이프플래닛생명보험": "ALL",  # 디지털 최소공시 (TODO_parser L51 legit)
        "신한이지손해보험": "ALL",        # CSM 제외사(단위오류), PL 분해도 미공시
    }
    # 분기 단위 legit (진짜 미공시 confirmed). 현대 2024.1Q~2025.2Q: OLD form 주석에 보험서비스비용·재보험수익
    # LOB 미분리(parser 표단위 raw확인 2026-06-14: LOB-헤더 표=수지현황 netted·보험수익+재보험서비스비용·금융손익
    # 3종뿐 → 비용 leg 부재로 도출불가). 2025.3Q+는 NEW form(분석공시)부터 분리공시 → 추출됨(예외 불요).
    ZLEG_LEGIT_CQ = {("현대해상", q) for q in
                     ("2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q")}
    zleg_rows = []  # (co, q, n_zero, n_none, 생명장기손익)
    zleg_exc = 0
    for (co, q), m in sorted(pl.items()):
        if q.startswith("2023."):
            continue
        if m.get("보험손익") is None:
            continue
        legit = ZLEG_LEGIT.get(co)
        if legit == "ALL" or (co, q) in ZLEG_LEGIT_CQ:
            zleg_exc += 1
            continue
        items = [k for k in PL_LEG_ITEMS if not (legit and k in legit)]
        vals = [m.get(k) for k in items]
        n_none = sum(1 for v in vals if v is None)
        n_zero = sum(1 for v in vals if v is not None and v == 0)
        if n_none + n_zero >= 4:
            zleg_rows.append((co, q, n_zero, n_none, m.get("생명장기손익")))

    print()
    print("=" * 78)
    print(f"2. PL_BRIDGE (PL_breakdown.json 배포본, 백만원)  pass={pb_pass} fail={len(pb_fail)} skip={pb_skip}  "
          f"| 2b. ZERO_LEGS flag={len(zleg_rows)} | 2c. IMPOSSIBLE-0 leg={len(zerolegs_rows)}")
    print(f"   pass 내역: 진짜 {ev[EQ_REAL]} · 구성상 {ev[EQ_TAUTOLOGY]} · 부분 {ev[EQ_PARTIAL]}"
          f"  (구성상 = 빌더가 우변 한 항을 좌변에서 빼 만들어 **깨질 수 없는** 등식)")
    print("=" * 78)
    print("  -- pass by equation × 증거력 (판정 근거는 PL_EQ_EVIDENCE 상수 주석) --")
    print("     구성상(TAUTOLOGY) 의 pass 는 '검사했더니 깨끗' 이 아니라 '검사 대상이 아니었다' 로 읽어라.")
    for label in list(PL_DUAL_LABELS) + [lab for lab, _l, _t in PL_EQS]:
        verdict = PL_EQ_EVIDENCE[label][0]
        print(f"    [{verdict:<9s}] {eq_pass_count[label]:>4d}P  {label[:58]}")
    print("  -- fail count by equation --")
    for label, n in sorted(eq_fail_count.items(), key=lambda x: -x[1]):
        print(f"    {n:>3d}  {label}")
    print("  -- fail detail (first 35) --")
    for co, q, label, lhs, diff in pb_fail[:35]:
        print(f"  FAIL {co:14s} {q}  [{label.split('=')[0].strip()}]  lhs={lhs:.1f} diff={diff:+.1f}")
    print("  -- zero-legs (생명장기 sub-item 0/None 무더기, 2024+, first 40) --")
    for co, q, zs, nnone, lt in zleg_rows[:40]:
        lt_s = f"{lt:.0f}" if lt is not None else "None"
        print(f"  ZLEG {co:14s} {q}  zero={zs} none={nnone}  생명장기손익={lt_s}")
    print("  -- IMPOSSIBLE-0: 생명장기 분해손익 0원 불가 (owner 확정) --")
    for co, q, item in zerolegs_rows[:40]:
        print(f"  ZERO0 {co:14s} {q}  {item}=0 (불가능 — 추출오류)")
    # ---- 2e. 보험손익 leg-coverage (결측 LOB 다리 0-fill 판정, 2026-08-29 신설) ----
    print(f"  -- 2e. LEG-COVERAGE (결측 LOB 다리를 0 으로 채워 판정)  "
          f"닫힘={len(legcov_pass)} 깨짐={len(legcov_fail)} 좌변없음(item1 결측)={len(nolhs_rows)} --")
    print("     닫힘 = 그 다리는 정말 0(발행사 미영위). 종전에는 이것도 SKIP 이라 무검사였다.")
    print("     `N/A=` = LOB_LEG_NA 등재 = 그 LOB 이 원문에 아예 없다(미해당). 추출 실패가 아니다.")
    for co, q, diff, zf, xl, na in legcov_pass[:40]:
        xs = f"  +extraLOB(2-N)={xl:+,.1f}" if xl else ""
        ns = f"  N/A={'+'.join(na)}" if na else ""
        zs = f"  0-fill={'+'.join(zf)}" if zf else ""
        print(f"  LEGOK {co:14s} {q}  diff={diff:+.1f}{zs}{ns}{xs}")
    print("     깨짐 = 결측 다리가 진짜 돈을 싣고 있다. |diff| 가 미검사 금액의 하한이다.")
    print("     등재(N/A)는 면제가 아니다 — 등재사가 여기 뜨면 등재 근거가 잔차로 반박된 것이다.")
    for co, q, lhs, diff, zf, xl, na in legcov_fail[:60]:
        xs = f"  +extraLOB(2-N)={xl:+,.1f}" if xl else ""
        ns = f"  N/A={'+'.join(na)}(!! 등재 반박)" if na else ""
        zs = f"  0-fill={'+'.join(zf)}" if zf else ""
        print(f"  LEGRED {co:14s} {q}  lhs={lhs:.1f} diff={diff:+.1f}{zs}{ns}{xs}")
    print("     좌변없음 = item1 자체가 결측이라 등식 성립 불가(coverage census 소관).")
    for co, q in nolhs_rows[:40]:
        print(f"  NOLHS {co:14s} {q}  보험손익=None")
    # 추가 LOB 커버리지 census — 등식이 **모르는 형태**의 하이픈 항목이 있으면 여기서 운다.
    # 오늘 0 건이다(하이픈 항목은 코리안리재보험의 2-1~12-1 뿐). 0 이 아니게 되는 날은
    # 새 재보험사가 다른 슬롯에 LOB 을 냈다는 뜻이고, 그때 이 등식은 그 회사를 또 오탐한다.
    if unknown_hyphen:
        print(f"     !! 등식이 모르는 하이픈 항목 {len(unknown_hyphen)}건 — 추가 LOB 슬롯일 수 있다"
              f"(`2-N` 만 가산 대상). 확인 전까지 그 회사의 보험손익 판정은 신뢰할 수 없다.")
        for co, q, no, nm in unknown_hyphen[:20]:
            print(f"  LEGUNK {co:14s} {q}  항목번호={no} 항목명={nm}")
    _nolhs_recent = [(co, q) for co, q in nolhs_rows if not q.startswith("2023.")]
    if _nolhs_recent:
        print(f"  !! 2024+ 에서 item1 결측 {len(_nolhs_recent)}건 — 2026-08-29 신설 시점엔 0 이었다(회귀 의심)")
    print("  -- 등식으로는 영원히 못 보는 항목 (PL_ITEMS_UNCHECKABLE_BY_EQUATION) --")
    print("     plug 를 없애지 않는 한 원천 재대조만이 수단이다. 실패가 아니라 결론이다.")
    for no, why in sorted(PL_ITEMS_UNCHECKABLE_BY_EQUATION.items()):
        print(f"  NOEQ  item{no:<3d} {why}")
    if evidence_out is not None:
        evidence_out.update(ev)
    return pb_pass, pb_fail, pb_skip, zleg_rows, zerolegs_rows


def _check_lob_taxonomy(pl: dict, quiet: bool = False) -> tuple[list, list, list]:
    """2g. LOB 택소노미 등재부 무결성 (2026-08-30 신설).

    `LOB_LEG_NA` 는 "이 회사에는 그 LOB 이 아예 없다"는 **주장**이다. 주장은 반증가능해야
    등재부이고, 반증 못 하면 그냥 면제다. 여기서 마스터로 반증한다 —

      · STALE  = 등재한 슬롯에 마스터가 값을 싣고 있다. 등재가 거짓이거나 파서가 잘못 채웠다.
                 어느 쪽이든 게이트가 인쇄하는 문장이 거짓이 되므로 **RED**.
      · DANGLE = 등재한 회사가 마스터에 아예 없다. 개명·철수로 등재부만 남은 것 → RED.
      · N/A    = 정상. 그 셀이 결측인 것은 미해당이라서다(추출 실패 아님).

    **왜 별도 룰인가.** `ZLEG_LEGIT` 를 넓히는 선택지가 있었지만 안 골랐다. 그 등재부는
    `PL_LEG_ITEMS`(생명장기 sub-item 10종) 어휘로만 소비된다 — `items = [k for k in
    PL_LEG_ITEMS if not (legit and k in legit)]`. `자동차손익` 을 거기 넣으면 이름이
    교집합에 없어 **조용히 아무 것도 안 하면서 등재된 것처럼 보인다.** 이 저장소가 반복해서
    당한 형태(=죽은 등재부)라, 소비되는 자리에 새로 만들고 무결성 검사를 붙였다.

    Returns (na_cells, stale_rows, dangling). RED = stale + dangling."""
    na_cells, stale_rows, dangling = [], [], []
    cos_in_master = {co for co, _q in pl}
    for co, legs in sorted(LOB_LEG_NA.items()):
        if co not in cos_in_master:
            dangling.append(co)
            continue
        for (c, q), m in sorted(pl.items()):
            if c != co:
                continue
            for leg in sorted(legs):
                v = m.get(leg)
                if v is None:
                    na_cells.append((co, q, leg))
                else:
                    stale_rows.append((co, q, leg, v))
    if not quiet:
        print(f"  -- 2g. LOB_TAXONOMY_NA (미해당 LOB 슬롯 등재부)  "
              f"N/A확인={len(na_cells)} 등재반박(STALE)={len(stale_rows)} "
              f"등재사부재(DANGLE)={len(dangling)} --")
        print("     결측(못 뽑았다) · 0.0(영위하는데 0) · 미해당(그 LOB 자체가 없다)은 셋 다 다르다.")
        for co, legs in sorted(LOB_LEG_NA.items()):
            n = sum(1 for c, _q, _l in na_cells if c == co)
            print(f"  LOBNA {co:14s} {'+'.join(sorted(legs))}  미해당확인={n}분기")
        for co, q, leg, v in stale_rows[:40]:
            print(f"  LOBSTALE {co:14s} {q}  {leg}={v} — 미해당이라 등재했는데 값이 있다. "
                  f"등재부가 거짓이거나 파서가 잘못 채웠다.")
        for co in dangling:
            print(f"  LOBDANGLE {co} — 등재부에만 있고 PL 마스터에 없다(개명·철수?).")
    return na_cells, stale_rows, dangling


# ===========================================================================
# 2f. TAX22_SOURCE_CROSSCHECK — item22(세전이익)의 **유일한** 진짜 검산 (2026-08-29 신설)
# ===========================================================================
# 왜 필요한가. `당기순이익 = 세전 - 법인세` 는 빌더가 `item23 = 22 - 24` 로 **무조건** 덮기
# 때문에(418/418, build_pl_breakdown.assemble L226-228) 구성상 참이다. 그래서 item22 를
# 30% 흔들어도 게이트 전체에서 신규 RED 가 **0 건**이었다(CONSTRUCTIVE 변이시험).
#
# 그런데 **원천 법인세 계정은 418/418 디스크에 있다** — `ifrs-full_IncomeTaxExpense
# ContinuingOperations`(fetch_dart_fs.ACCT[23]). `_parse()` 가 그 값을 t1[23] 에 담아
# 돌려주는데 `assemble()` 이 곧바로 잔차로 덮어써서 버려진다. 그 버려지는 값을 되살려
# 마스터의 `|22 - 24|` 와 대조하면 item22 가 처음으로 검사 대상이 된다.
#
# **부호는 대조하지 않는다.** 빌더 주석이 명시하듯 발행사마다 법인세비용의 부호 관행이
# 다르다(양수 금액 vs 괄호 차감) — 그것이 애초에 잔차 plug 를 도입한 이유다. 그래서 크기로만
# 본다. 크기 대조만으로도 item22 오추출은 잡힌다(잔차 크기가 원천 세액과 어긋난다).
#
# **이 룰이 증명하는 것과 못 하는 것.**
#   증명한다 : ① 마스터가 자기 원천(FS-API 캐시)에서 드리프트했다(lost update·수기편집·
#              핸들러 오버라이드) ② 발행사 손익계산서의 바닥이 자기 안에서 안 닫힌다
#              (빌더 주석이 말하는 "법인세 라인을 통째로 오파싱" 케이스) ③ 마스터 item22
#              가 손상됐다.
#   못 한다   : `_parse` 가 22·24·23 을 **일관되게** 잘못된 기준(연결 vs 별도)에서 골랐다면
#              셋 다 같이 틀려 이 등식은 닫힌다. 기준 오선택은 다른 축의 몫이다.
#
# **오프라인·결정적이어야 한다.** `fetch_dart_fs.tier1_for()` 는 `resolve_corp()` 를 거치는데
# 그건 `data/dart/raw/CORPCODE.xml`(30MB, **gitignore**)을 읽고 없으면 **네트워크로 받는다**.
# 게이트가 그걸 쓰면 새 클론·CI 에서 커버리지가 달라져 골든이 환경마다 흔들린다. 그래서
# **git 추적 파일만** 쓴다: `data/_derived/alotmatter_fetch_census.json` 의 KR코드→corp_code
# (39/39 resolved) + 추적된 `data/dart/_fs_api_cache/`(1,040 파일). 실측으로 두 매핑이
# 36/36 동일하고 불일치 0 임을 확인했다
# (scripts/_probes/probe_20260829_offline_corpcode_join2.py).
# 캐시 파싱은 `fetch_dart_fs._parse` 를 **그대로 호출**한다 — 재구현하면 게이트가 빌더와 다른
# 값을 보게 된다(이 저장소의 반복 사고 형태).
TAX22_CENSUS_PATH = "data/_derived/alotmatter_fetch_census.json"
TAX22_CACHE_DIR = "data/dart/_fs_api_cache"
TAX22_FLOOR = 200.0        # 백만원 — 다른 PL 등식과 같은 floor
TAX22_REL = 0.001


def _tax22_corp_codes() -> dict:
    """KR코드 -> DART corp_code (추적 파일에서만, 네트워크 없음)."""
    p = ROOT / TAX22_CENSUS_PATH
    if not p.exists():
        return {}
    out = {}
    for c in json.loads(p.read_text(encoding="utf-8")).get("cells", []) or []:
        if c.get("kr") and c.get("corp_code"):
            out.setdefault(c["kr"], c["corp_code"])
    return out


def _tax22_tier1(fdf, cc: str, quarter: str):
    """FS-API 캐시 한 버킷을 빌더와 **같은 함수**(`fetch_dart_fs._parse`)로 읽는다.

    basis 우선순위도 `tier1_for` 와 같다 — OFS 우선, 손익계산서가 아예 없을 때만 CFS 폴백.
    `BASIS_CFS` 가 비어 있다는 전제를 코드로 확인한다(비면 빌더와 순서가 갈린다)."""
    if fdf.BASIS_CFS:
        raise SystemExit(
            "fetch_dart_fs.BASIS_CFS 가 비어 있지 않다 — 2f 의 basis 순서가 빌더와 갈린다. "
            "이 함수를 그 집합에 맞춰 고쳐라.")
    reprt = fdf.REPRT.get(quarter[5:])
    if not reprt:
        return None
    annual = quarter[5:] == "4Q"
    for fs_div in ("OFS", "CFS"):
        p = ROOT / TAX22_CACHE_DIR / f"{cc}_{quarter[:4]}_{reprt}_{fs_div}.json"
        if not p.exists():
            continue
        try:
            t1 = fdf._parse(json.loads(p.read_text(encoding="utf-8")), annual)
        except Exception:
            t1 = None
        if t1:
            return t1
    return None


def _check_tax22_crosscheck(rows: list | None = None,
                            quiet: bool = False) -> tuple[int, list, dict]:
    """item22 vs (item24 + 원천 법인세). Returns (pass, fail_rows, skip_counts).

    결측은 SKIP 이지만 **사유별로 세어 인쇄한다** — 조용히 사라지면 이 룰도 false-green 이 된다.
    `rows` 를 넘기면 그 마스터 사본으로 돈다(변이시험용 —
    tests/test_rule_coverage_manifest.py::test_pl_item_coverage_matches_manifest).
    """
    if rows is None:
        rows = json.loads((ROOT / PL_PATH).read_text(encoding="utf-8"))
    master, code_of = defaultdict(dict), {}
    for r in rows:
        master[(r["원수사명"], r["공시분기"])][norm(r["항목명"])] = r["값"]
        code_of[r["원수사명"]] = r["원보험사코드"]

    skips = defaultdict(int)
    unresolved_names, fails = set(), []
    n_pass = 0
    try:
        sys.path.insert(0, str(ROOT))
        import fetch_dart_fs as fdf
    except Exception as e:                       # noqa: BLE001 — 조용히 죽으면 축이 사라진다
        if not quiet:
            print()
            print("=" * 78)
            print(f"2f. TAX22_SOURCE_CROSSCHECK  **UNAVAILABLE** ({type(e).__name__}: {e})")
            print("    fetch_dart_fs 를 import 못 했다. item22 는 다시 무검사다 — 고치기 전엔")
            print("    이 게이트의 pass 를 item22 의 증거로 쓰지 마라.")
            print("=" * 78)
        return 0, [], {"IMPORT_FAILED": len(master)}

    kr2cc = _tax22_corp_codes()
    for (co, q) in sorted(master):
        m = master[(co, q)]
        m22, m24 = m.get("세전이익"), m.get("당기순이익")
        if m22 is None or m24 is None:
            skips["MASTER_22_OR_24_MISSING"] += 1
            continue
        cc = kr2cc.get(code_of.get(co, ""))
        if not cc:
            skips["CORP_CODE_UNRESOLVED"] += 1
            unresolved_names.add(co)
            continue
        t1 = _tax22_tier1(fdf, cc, q)
        if not t1:
            skips["NO_FS_API_CACHE"] += 1
            continue
        raw_tax = t1.get(23)
        if raw_tax is None:
            skips["SOURCE_TAX_ACCOUNT_ABSENT"] += 1
            continue
        lhs = abs(m22 - m24)          # 마스터가 법인세로 쓰는 잔차의 크기
        rhs = abs(raw_tax)            # 원천 법인세 계정의 크기
        tol = max(TAX22_REL * max(abs(m22), lhs), TAX22_FLOOR)
        if abs(rhs - lhs) > tol:
            fails.append((co, q, round(m22, 1), round(lhs, 1), round(rhs, 1),
                          round(rhs - lhs, 1), round(tol, 1)))
        else:
            n_pass += 1

    if not quiet:
        print()
        print("=" * 78)
        print(f"2f. TAX22_SOURCE_CROSSCHECK (|item22-item24| == |원천 법인세 계정|, 백만원)  "
              f"pass={n_pass} fail={len(fails)} skip={sum(skips.values())}")
        print("    item22 를 보는 **유일한** 룰이다. `당기순이익 = 세전-법인세` 는 빌더가")
        print("    item23 을 22-24 로 덮어 구성상 참이라 item22 오추출을 영원히 못 본다.")
        print("=" * 78)
        for co, q, m22, lhs, rhs, d, tol in fails[:40]:
            print(f"  FAIL {co:14s} {q}  22={m22:>+14,.1f}  |22-24|={lhs:>13,.1f}  "
                  f"|원천세|={rhs:>13,.1f}  diff={d:>+12,.1f}  tol={tol:,.1f}")
        for k, v in sorted(skips.items()):
            print(f"  SKIP {v:>4d}  {k}")
        if unresolved_names:
            print(f"  !! corp_code 미해결 회사 {len(unresolved_names)}개 — {TAX22_CENSUS_PATH} 가")
            print(f"     새 회사를 아직 모른다: {sorted(unresolved_names)}")
        print("  주의: SKIP 버킷의 item22 는 여전히 **어떤 룰도 안 본다**(원천이 FS-API 가 아닌")
        print("        핸들러/HTML 경로). 그 자리는 '검사했더니 깨끗'이 아니라 '검사 대상 아님'이다.")
    return n_pass, fails, dict(skips)


def _check_closing_identity(wf: dict) -> tuple[int, list, int]:
    """CSM_WATERFALL_CLOSING_IDENTITY: 기초+신계약+이자+가정+상각 = 기말 (CSM_waterfall, 억원).
    Prints its own section and returns (ci_pass, ci_fail, ci_skip). Split out of
    main() 2026-07-22; pinned by tests/test_master_tables_golden.py."""
    # ===== 1. CLOSING_IDENTITY (CSM_waterfall, 억원) =====
    need = ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"]
    ci_pass = ci_skip = 0
    ci_fail = []
    for (co, q), m in sorted(wf.items()):
        if any(m.get(k) is None for k in need):
            ci_skip += 1
            continue
        lhs = sum(m[k] for k in need[:-1])
        rhs = m["기말CSM"]
        diff = lhs - rhs
        if abs(diff) > max(0.001 * abs(rhs), 2.0):
            ci_fail.append((co, q, round(rhs, 1), round(diff, 1)))
        else:
            ci_pass += 1

    print("=" * 78)
    print(f"1. CLOSING_IDENTITY (CSM_waterfall, 억원)  pass={ci_pass} fail={len(ci_fail)} skip={ci_skip}")
    print("=" * 78)
    for co, q, rhs, diff in ci_fail:
        print(f"  FAIL {co:14s} {q}  기말={rhs:>11.1f}  diff={diff:>+10.1f}  ({diff/rhs*100:+.1f}%)")
    return ci_pass, ci_fail, ci_skip


def _check_coverage(wf: dict, pl: dict) -> tuple[list, list]:
    """COVERAGE: 데이터 누락(hole) census — SKIP으로 숨기지 않고 명시.
    Prints its own section and returns (wf_holes, pl_holes). Split out of
    main() 2026-07-22; pinned by tests/test_master_tables_golden.py."""
    # ===== 0. COVERAGE (데이터 누락 hole — SKIP으로 숨기지 않음) =====
    wf_holes, wf_known, wf_struct = coverage_holes(wf, ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"])
    pl_holes, pl_known, pl_struct = coverage_holes(pl, ["보험손익", "생명장기손익", "당기순이익"])
    print("=" * 78)
    print(f"0. COVERAGE real hole(2024+)  CSM={len(wf_holes)} PL={len(pl_holes)}  | "
          f"2023 known(비노출)={len(wf_known)+len(pl_known)} | struct(미공시)제외={len(wf_struct)+len(pl_struct)}")
    print("=" * 78)
    for co, q, kind in wf_holes:
        print(f"  HOLE-CSM {co:14s} {q} ({kind})")
    for co, q, kind in pl_holes:
        print(f"  HOLE-PL  {co:14s} {q} ({kind})")
    print()
    return wf_holes, pl_holes


def _check_csm_crosscheck(pl: dict, wf: dict) -> tuple[int, list, int, int]:
    """CSM_AMORT_IDENTITY: PL(원수+수재) CSM상각 == 워터폴 CSM상각. **등식이다.**
    Prints its own section and returns (cc_pass, cc_fail, cc_pinned, cc_skip).
    Split out of main() 2026-07-22; pinned by tests/test_master_tables_golden.py.

    2026-08-25 (owner "당연히 1 이어야돼"): 세 가지가 같이 바뀌었다 —
      ① tol  : OK≤max(5%,300mn)/FAIL>10% 라는 **밴드** → 반올림 폭 max(0.1억, 0.05%)
      ② scope: 4Q-only → **전 분기**. "1~3Q 는 분기배분 차이로 틀어진다"는 근거 없는 전제였다.
               실측: 전 분기 346버킷 중 318건이 반올림 폭 안에서 닫힌다(4Q 만 볼 이유가 없다).
      ③ 기지 잔차는 `data/_gold/csm_amort_identity_ledger.json` 에 **건별·잔차까지 박제**.
    대조식·허용오차의 근거는 파일 상단 `CSM_AMORT_*` 주석 참조.
    """
    ledger = csm_amort_ledger().get("entries", {})
    cc_pass = cc_pinned = cc_skip = 0
    cc_fail = []          # 등재부에 없는 신규 이탈 + 박제 이탈 → exit code 에 반영
    cc_pinned_rows = []
    common = sorted(set(pl) & set(wf))
    seen = set()
    for (co, q) in common:
        r = csm_amort_residual(pl[(co, q)], wf[(co, q)])
        if r is None:
            cc_skip += 1
            continue
        resid, p_eok, w_eok = r
        key = f"{co}|{q}"
        if abs(resid) <= csm_amort_tol(w_eok):
            cc_pass += 1
            continue
        seen.add(key)
        verdict = csm_amort_ledger_verdict(ledger.get(key), resid)
        row = (co, q, round(p_eok, 2), round(w_eok, 2), resid, abs(resid) / w_eok,
               (ledger.get(key) or {}).get("cause", "-"), verdict)
        if verdict == "PINNED":
            cc_pinned += 1
            cc_pinned_rows.append(row)
        else:
            cc_fail.append(row)
    stale = sorted(k for k in ledger if k not in seen)

    print()
    print("=" * 78)
    print(f"3. CSM_AMORT_IDENTITY (PL 원수+수재 == 워터폴 상각, 억원, 전 분기)  "
          f"common={len(common)} pass={cc_pass} pinned={cc_pinned} fail={len(cc_fail)} "
          f"skip={cc_skip} stale={len(stale)}")
    print(f"   tol: max({CSM_AMORT_TOL_ABS_EOK}억, {CSM_AMORT_TOL_REL*100:g}%) — 반올림 폭. "
          f"밴드가 아니다(owner 2026-08-25)")
    print("=" * 78)
    for co, q, p, w, s, rel, cause, verdict in cc_fail[:40]:
        print(f"  FAIL  {co:14s} {q}  PL={p:>+12.2f}  WF={w:>+12.2f}  잔차={s:>+10.2f}억 "
              f"({rel*100:+.3f}%)  [{verdict}/{cause}]")
    for co, q, p, w, s, rel, cause, verdict in cc_pinned_rows[:40]:
        print(f"  PIN   {co:14s} {q}  PL={p:>+12.2f}  WF={w:>+12.2f}  잔차={s:>+10.2f}억 "
              f"({rel*100:+.3f}%)  [{cause}]")
    for k in stale[:20]:
        print(f"  FIXED? {k}  <- 더는 벌어지지 않는다. 등재부에서 줄을 지워라")
    return cc_pass, cc_fail, cc_pinned, cc_skip


def _check_qoq_warn(wf: dict) -> list:
    """QOQ_DELTA_WARN: 시계열 anomaly (YELLOW — 다운스트림 차단 안 함).
    Writes data/_derived/qoq_warn.json, prints its own section, and returns
    qoq_rows. Split out of main() 2026-07-22; pinned by
    tests/test_master_tables_golden.py."""
    # ===== 4. QOQ_DELTA_WARN (시계열 anomaly, YELLOW — 다운스트림 차단 안 함) =====
    # 누적항목(신계약/이자/상각, PL 손익)은 net-quarterly 증분 비교, 시점값(기말 CSM)은 raw QoQ.
    # 2024+ 분기만 평가. threshold는 config/qoq_thresholds.yaml.
    qcfg = load_qoq_cfg()
    # spec(qoq_thresholds.yaml items.ifrs17) 대상 = CSM 항목만. PL 손익(보험손익/투자손익/당기순이익)은
    # 시장·금리 민감으로 본질적 고변동 + spec 미등록이라 anomaly 룰 부적합 → 제외.
    CSM_QOQ = [("신계약CSM", "new_business_csm", True), ("이자부리", "csm_interest_accretion", True),
               ("CSM상각", "csm_amortization", True), ("기말CSM", "csm_closing", False)]
    qoq_rows = qoq_scan(wf, CSM_QOQ, 50.0, qcfg)  # floor 50억 (작은 분모 폭발 제거)
    qoq_rows.sort(key=lambda r: -abs(r[3]))
    print()
    print("=" * 78)
    print(f"4. QOQ_DELTA_WARN (시계열 급변, YELLOW)  flagged={len(qoq_rows)} (2024+, net-quarterly)")
    print("=" * 78)
    for co, q, item, delta, thr, a, b, basis in qoq_rows[:30]:
        print(f"  YEL {co:14s} {q} {item:10s} ΔQoQ={delta*100:>+8.1f}% (>{thr*100:.0f}%, {basis}) {b:.0f}→{a:.0f}")
    if len(qoq_rows) > 30:
        print(f"  ... +{len(qoq_rows)-30} more")
    qout = ROOT / "data" / "_derived" / "qoq_warn.json"
    qout.parent.mkdir(parents=True, exist_ok=True)
    qout.write_text(json.dumps(
        [{"company": c, "quarter": q, "item": it, "delta_pct": round(d * 100, 1),
          "threshold_pct": round(t * 100, 0), "cur": round(a, 1), "ref": round(b, 1),
          "basis": bs, "sign_flip": (a < 0) != (b < 0)} for c, q, it, d, t, a, b, bs in qoq_rows],
        ensure_ascii=False, indent=2), encoding="utf-8")
    return qoq_rows


def _check_sensitivity() -> tuple[list, list, list]:
    """SENSITIVITY_UNIT_SANITY (5) + SENSITIVITY_DIRECTION_SANITY (5b): CSM 민감도
    단위/부호 sanity via sensitivity_unit_sanity() / sensitivity_direction_sanity().
    Prints its own sections and returns (sens_red, sens_yellow, sens_dir). Split out
    of main() 2026-07-22; pinned by tests/test_master_tables_golden.py."""
    sens_red, sens_yellow = sensitivity_unit_sanity()
    sens_dir = sensitivity_direction_sanity()
    print()
    print("=" * 78)
    print(f"5. SENSITIVITY_UNIT_SANITY (max|csm_delta| / 그 회사 자신의 기말 CSM)  "
          f"RED={len(sens_red)} YELLOW={len(sens_yellow)}")
    print("   RED: rel<0.05% or >300% (단위오류·소블록 오선택) / YELLOW: <0.5% or >100%")
    print("   앵커(마스터 CSM) 없으면 또래비교 폴백 — 그때 작은 쪽은 YELLOW 까지만"
          "(소형사와 단위오류를 가를 수 없다)")
    print("=" * 78)
    for name, mx, ratio, unit, ud in sens_red:
        print(f"  RED  {str(name):18s} max|Δ|={mx:>12.2f} rel={ratio:>10.4%}  unit={unit}/det={ud}")
    for name, mx, ratio, unit, ud in sens_yellow:
        print(f"  YEL  {str(name):18s} max|Δ|={mx:>12.2f} rel={ratio:>10.4%}  unit={unit}/det={ud}")

    print()
    print("=" * 78)
    print(f"5b. SENSITIVITY_DIRECTION_SANITY (CSM↔손익 부호 역행 = 파싱오류/onerous 의심, YELLOW)  flag={len(sens_dir)}")
    print("    rule(user): CSM↑면 손익도↑ 통상 — sign 불일치 시 flag. |CSM|·|손익|≥1억 floor.")
    print("=" * 78)
    for name, risk, shock, cd, pl, ratio in sens_dir:
        print(f"  SDIR {str(name):16s} {str(risk):14s} {str(shock):20s} CSM={cd:>+10.1f} 손익={pl:>+9.1f} (|CSM|/|손익|={ratio:.0f}x)")
    return sens_red, sens_yellow, sens_dir


# PL_OCI_VS_BS_AOCI (owner 티켓 inbox/parser/20260828T0113Z §작업3 룰2): PL 항목25(기타포괄손익,
# 그 분기 순유량) 을 IFRS17_BS.json 항목4(기타포괄손익 누계액, 저량) 의 QoQ 증감과 대조한다.
# **먼저 전 버킷 시뮬레이션**(scripts/_probes/simulate_pl_oci_vs_bs_aoci.py,
# artifacts/parser/pl_oci_vs_bs_aoci_simulation.json, 259 비교가능 셀)을 돌려 실제 잔차
# 분포를 본 뒤 결정했다 — 룰 수정 전 시뮬레이션 필수 원칙(1건 고치려다 129건 깨뜨릴 뻔한 전례).
#   중앙값·p25 잔차 = 정확히 0.000 (다수 셀이 완전히 닫힘 — 개념 자체는 맞다는 근거).
#   그런데 p90=13,770백만·p95=59,067백만·max=5,391,139백만(삼성생명 2025.4Q, 22.8%) — 관대한
#   허용오차(rel100%+10,000백만)조차 259건 중 2건은 못 잡는다. 최악 30건 중 17건(56.7%,
#   기저율 25% 대비 과다)이 **4Q(연차) 분기에 몰려 있다** — 이 저장소에 이미 같은 패턴이 문서화돼
#   있다(build_root_masters.py: "신계약CSM 당분기가 음수(4Q 연차 재서술 artifact)"). 재분류조정
#   (FVOCI 매도 시 OCI→P&L 재분류)·자본거래·법인세 조정이 CIS 당기 순액과 BS 잔액 증감을
#   갈라놓을 수 있다는 게 회계상 실제 메커니즘이라 **등식이 아니다** — owner 지시대로 RED가
#   아니라 YELLOW(다운스트림/exit code 미차단)로 배선한다.
# 허용오차 = max(20%·|ΔBS|, 2,000백만) — 259건 중 245건(94.6%) 통과, 14건 flag.  ledger/baseline
# 불요: RED 계열(pl_bridge/csm_amort_identity)만 exit code를 막아 "몰래 통과"를 막을 필요가
# 있고, 이 룰은 처음부터 다운스트림을 막지 않는 진단성 YELLOW라 qoq_warn과 같은 패턴을 쓴다.
OCI_AOCI_TOL_REL = 0.20
OCI_AOCI_TOL_ABS_MN = 2000.0


def _check_pl_oci_vs_bs_aoci() -> list:
    """PL_OCI_VS_BS_AOCI: PL 항목25 값_당분기 vs BS 항목4 QoQ delta.  YELLOW만 — exit code
    미반영.  Prints its own section, writes data/_derived/pl_oci_vs_bs_aoci_warn.json,
    returns the flagged rows.  New 2026-08-28 (ticket inbox/parser/20260828T0113Z)."""
    bs_path = ROOT / BS_PATH
    if not bs_path.exists():
        print()
        print("=" * 78)
        print("6. PL_OCI_VS_BS_AOCI  SKIPPED (IFRS17_BS.json not found)")
        print("=" * 78)
        return []
    bs = load_long(BS_PATH)
    pl_dangi = load_pl_dangi(PL_PATH, 25)
    rows = []
    n_skip = 0
    for (co, q), dangi in sorted(pl_dangi.items()):
        if dangi is None:
            continue
        cur = bs.get((co, q), {}).get("기타포괄손익누계액")
        pq = prev_quarter(q)
        prev = bs.get((co, pq), {}).get("기타포괄손익누계액") if pq else None
        if cur is None or prev is None:
            n_skip += 1
            continue
        delta_bs = cur - prev
        resid = delta_bs - dangi
        tol = max(OCI_AOCI_TOL_REL * abs(delta_bs), OCI_AOCI_TOL_ABS_MN)
        if abs(resid) > tol:
            rows.append((co, q, delta_bs, dangi, resid))
    rows.sort(key=lambda r: -abs(r[4]))
    print()
    print("=" * 78)
    print(f"6. PL_OCI_VS_BS_AOCI (PL 항목25 당분기 vs BS 항목4 QoQ delta, 백만원, YELLOW)  "
          f"flagged={len(rows)} (비교가능 {len(pl_dangi) - n_skip - len(rows)}건은 tol 이내, "
          f"BS 결측 skip={n_skip})")
    print(f"   tol = max({OCI_AOCI_TOL_REL*100:.0f}%·|ΔBS|, {OCI_AOCI_TOL_ABS_MN:.0f}백만) — "
          f"재분류조정·자본거래·법인세, 특히 4Q 연차재서술로 구조적 잔차 존재(owner 지시: RED 아님)")
    print("=" * 78)
    for co, q, dbs, dg, resid in rows[:30]:
        print(f"  YEL {co:14s} {q}  ΔBS={dbs:>12.1f}  PL당분기={dg:>12.1f}  resid={resid:>+12.1f}")
    if len(rows) > 30:
        print(f"  ... +{len(rows) - 30} more")
    out = ROOT / "data" / "_derived" / "pl_oci_vs_bs_aoci_warn.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        [{"company": c, "quarter": q, "delta_bs_mn": round(dbs, 3), "pl_oci_dangi_mn": round(dg, 3),
          "residual_mn": round(resid, 3)} for c, q, dbs, dg, resid in rows],
        ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def _pl_bridge_baseline() -> dict:
    """기지 PL_BRIDGE 실패 등재부. 없으면 빈 등재부(= 전부 신규로 취급)."""
    p = ROOT / PL_BRIDGE_BASELINE_PATH
    if not p.exists():
        return {"entries": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def _pl_fail_id(row) -> str:
    co, q, label = row[0], row[1], row[2]
    return f"{co}|{q}|{label}"


def _report_pl_baseline(pb_fail) -> tuple[int, int, list[str]]:
    """(baselined, new, stale) — 신규 실패를 기지 실패와 갈라낸다.

    소스 재조준(2026-08-25)으로 1,307셀이 처음 검사 대상이 되면서 16건이 드러났다. 전부
    이번 라운드에 고칠 수 없어 **초기 YELLOW 로 착지**시키되(선례: UH-3 ·
    CSM_WATERFALL_PLAUSIBILITY), 조용히 통과시키지는 않는다 — 매 실행 건별로 인쇄하고,
    등재되지 않은 실패는 `pl_new` 로 SUMMARY 에 올라가 골든이 push 를 막는다.
    """
    base = _pl_bridge_baseline()
    entries = base.get("entries", {})
    ids = {_pl_fail_id(r) for r in pb_fail}
    new = sorted(i for i in ids if i not in entries)
    stale = sorted(i for i in entries if i not in ids)
    print()
    print("=" * 78)
    print(f"2d. PL_BRIDGE BASELINE (data/_gold/pl_bridge_baseline.json)  "
          f"기지={len(ids) - len(new)} 신규={len(new)} 등재부에만 남은 것={len(stale)}")
    print("    기지 = 2026-08-25 소스 재조준으로 처음 검사받아 드러난 실패. 건별 등재이며")
    print("    통째 skip 이 아니다. parser 가 고칠 때마다 그 줄을 지운다.")
    print("=" * 78)
    for i in new:
        print(f"  NEW-FAIL  {i}   <- 등재부에 없다. 진짜 회귀인지 확인하고 고치거나 등재하라")
    for i in stale[:20]:
        print(f"  FIXED?    {i}   <- 더는 실패하지 않는다. 고쳐진 것이면 등재부에서 줄을 지워라")
    return len(ids) - len(new), len(new), stale


def main() -> int:
    if "--no-build" not in sys.argv:
        rebuild_root_masters()
    pl = load_long(PL_PATH)
    wf = load_long(WF_PATH)

    ci_pass, ci_fail, ci_skip = _check_closing_identity(wf)

    wf_holes, pl_holes = _check_coverage(wf, pl)

    dup_rows, spike_rows, cont_rows, wfy_rows, zamort_rows = _check_plausibility(wf)

    pl_extra_lob, pl_unknown_hyphen = load_pl_extra_lob(PL_PATH)
    pl_evidence: dict = {}
    pb_pass, pb_fail, pb_skip, zleg_rows, zerolegs_rows = _check_pl_bridge(
        pl, pl_extra_lob, pl_unknown_hyphen, pl_evidence)

    lob_na, lob_stale, lob_dangle = _check_lob_taxonomy(pl)

    tax_pass, tax_fail, tax_skip = _check_tax22_crosscheck()

    cc_pass, cc_fail, cc_pinned, cc_skip = _check_csm_crosscheck(pl, wf)

    qoq_rows = _check_qoq_warn(wf)

    sens_red, sens_yellow, sens_dir = _check_sensitivity()

    oci_aoci_rows = _check_pl_oci_vs_bs_aoci()

    pb_base, pb_new, pb_stale = _report_pl_baseline(pb_fail)

    print()
    print("-" * 78)
    print("NOTE (2026-08-25): PL 축 소스를 배포본으로 재조준했다. 그 전 이 게이트가 찍던")
    print("  `HOLE-PL (통째)` 24건은 **24/24 전부 phantom** 이었다(중간산출물에만 없던 것이고")
    print("  배포본엔 값이 있었다). crosscheck fail 1건(BNP 2025.4Q)도 같은 이유로 사라졌다.")
    print("  즉 아래 0 은 회귀가 아니라 **가짜 hole 의 소멸**이다. 되살리려 하지 말 것.")
    print("-" * 78)

    print()
    print("#" * 78)
    print(f"SUMMARY  coverage_hole:{len(wf_holes)}CSM/{len(pl_holes)}PL | "
          f"closing:{ci_pass}P/{len(ci_fail)}F/{ci_skip}S | "
          f"plausibility:{len(dup_rows)}dup/{len(spike_rows)}spike/{len(cont_rows)}cont/"
          f"{len(wfy_rows)}wfy/{len(zamort_rows)}zamort | "
          f"pl_bridge:{pb_pass}P(진짜{pl_evidence.get(EQ_REAL, 0)}"
          f"·구성상{pl_evidence.get(EQ_TAUTOLOGY, 0)}"
          f"·부분{pl_evidence.get(EQ_PARTIAL, 0)})/{len(pb_fail)}F/{pb_skip}S/{pb_new}NEW | "
          f"tax22_src:{tax_pass}P/{len(tax_fail)}F/{sum(tax_skip.values())}S | "
          f"zero_legs:{len(zleg_rows)} | "
          f"impossible0:{len(zerolegs_rows)} | "
          f"lob_na:{len(lob_na)}NA/{len(lob_stale) + len(lob_dangle)}BAD | "
          f"csm_amort_identity:{cc_pass}P/{cc_pinned}PIN/{len(cc_fail)}F/{cc_skip}S | "
          f"qoq_warn:{len(qoq_rows)}Y | sens:{len(sens_red)}R/{len(sens_yellow)}Y/{len(sens_dir)}dir | "
          f"oci_vs_bs_aoci:{len(oci_aoci_rows)}Y")
    print("#" * 78)
    # QOQ/sens_yellow는 YELLOW(anomaly)라 exit code에 반영 안 함. wfy/zamort/zleg/impossible0/sens_red은 데이터 오류라 반영.
    # lob_stale/lob_dangle = 게이트 자신의 등재부가 마스터와 어긋난 것 → RED(인쇄되는 문장이 거짓).
    return 0 if not (ci_fail or pb_fail or cc_fail or dup_rows or spike_rows or cont_rows
                     or wf_holes or pl_holes or wfy_rows or zamort_rows or zleg_rows
                     or zerolegs_rows or sens_red or tax_fail
                     or lob_stale or lob_dangle) else 2


if __name__ == "__main__":
    raise SystemExit(main())
