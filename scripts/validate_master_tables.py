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
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

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

QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q",
      "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]


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


def sensitivity_unit_sanity():
    """Owner 2026-06-14 claim 2: CSM 민감도 단위 미정규화(원/만원/억원 혼재) sanity.
    회사별 max|csm_delta| vs 또래 median 규모비. 정규화 후엔 동일단위(억원) 가정이므로 또래 대비
    거대 outlier = 미정규화 시그니처(현대해상=원 단위라 삼성화재의 ~640배였던 케이스의 회귀가드).
      RED   : ratio>1000x or <1/1000x (clean 단위오류 — gate 차단)
      YELLOW: ratio>100x or <1/100x  (의심 — 보고만, 또래보다 100배+ 작은 미정규화 ÷ 누락 등)."""
    sp = ROOT / SENS_PATH
    sens_red, sens_yellow = [], []
    if not sp.exists():
        return sens_red, sens_yellow
    sdoc = json.loads(sp.read_text(encoding="utf-8"))
    scales = []
    for c in sdoc.get("companies", []) or []:
        ds = [abs(s["csm_delta"]) for s in (c.get("scenarios") or [])
              if isinstance(s.get("csm_delta"), (int, float))]
        if ds:
            scales.append((c.get("company"), max(ds), c.get("unit"), c.get("unit_detected")))
    if len(scales) < 5:
        return sens_red, sens_yellow
    vals = sorted(v for _, v, _, _ in scales)
    med = vals[len(vals) // 2] or 1.0
    for name, mx, unit, ud in scales:
        ratio = mx / med
        if ratio > 1000 or ratio < 1e-3:
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
    # 작년 기말 = 올해 기시. 2023은 2022 데이터 없어 SKIP.
    FY_Q = {
        "2024": ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"],
        "2025": ["2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q"],
        "2026": ["2026.1Q"],
    }
    PREV_CLOSE = {"2024": "2023.4Q", "2025": "2024.4Q", "2026": "2025.4Q"}
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
    for co, qmap in sorted(wf_co.items()):
        for fy in ("2023", "2024", "2025", "2026"):
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


def _check_pl_bridge(pl: dict) -> tuple[int, list, int, list, list]:
    """PL bridge identity (2) + 생명장기 zero-legs (2b) + impossible-zero legs (2c).
    All three read pl_breakdown and share one print block, so they stay together.
    Returns (pb_pass, pb_fail, pb_skip, zleg_rows, zerolegs_rows). Split out of
    main() 2026-07-22; pinned by tests/test_master_tables_golden.py."""
    # ===== 2. PL_BRIDGE (pl_breakdown_master, 백만원) =====
    pb_pass = pb_skip = 0
    pb_fail = []
    eq_fail_count = defaultdict(int)
    for (co, q), m in sorted(pl.items()):
        # --- 보험손익 dual-form (bare ΣLOB / adj +기타영업수익-기타사업비용) ---
        bo = m.get("보험손익")
        lob = [m.get("생명장기손익"), m.get("자동차손익"), m.get("일반손익")]
        if bo is None or any(x is None for x in lob):
            pb_skip += 1
        else:
            bare = sum(lob)
            cands = [bare]
            oi, oe = m.get("기타영업수익"), m.get("기타사업비용")
            if oi is not None and oe is not None:
                cands.append(bare + oi - oe)
            diff = min((c - bo for c in cands), key=abs)
            if abs(diff) > max(0.001 * abs(bo), DEFAULT_FLOOR):
                pb_fail.append((co, q, "보험손익(dual)", round(bo, 1), round(diff, 1)))
                eq_fail_count["보험손익(dual)"] += 1
            else:
                pb_pass += 1
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
    print("=" * 78)
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
    return pb_pass, pb_fail, pb_skip, zleg_rows, zerolegs_rows


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
    print(f"5. SENSITIVITY_UNIT_SANITY (csm_delta 또래-median 규모비, 억원)  "
          f"RED={len(sens_red)} YELLOW={len(sens_yellow)}")
    print("   RED: ratio>1000x or <1/1000x (단위 미정규화) / YELLOW: >100x or <1/100x")
    print("=" * 78)
    for name, mx, ratio, unit, ud in sens_red:
        print(f"  RED  {str(name):18s} max|Δ|={mx:>12.2f} ×med={ratio:>8.3g}  unit={unit}/det={ud}")
    for name, mx, ratio, unit, ud in sens_yellow:
        print(f"  YEL  {str(name):18s} max|Δ|={mx:>12.2f} ×med={ratio:>8.3g}  unit={unit}/det={ud}")

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

    pb_pass, pb_fail, pb_skip, zleg_rows, zerolegs_rows = _check_pl_bridge(pl)

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
          f"pl_bridge:{pb_pass}P/{len(pb_fail)}F/{pb_skip}S/{pb_new}NEW | "
          f"zero_legs:{len(zleg_rows)} | "
          f"impossible0:{len(zerolegs_rows)} | "
          f"csm_amort_identity:{cc_pass}P/{cc_pinned}PIN/{len(cc_fail)}F/{cc_skip}S | "
          f"qoq_warn:{len(qoq_rows)}Y | sens:{len(sens_red)}R/{len(sens_yellow)}Y/{len(sens_dir)}dir | "
          f"oci_vs_bs_aoci:{len(oci_aoci_rows)}Y")
    print("#" * 78)
    # QOQ/sens_yellow는 YELLOW(anomaly)라 exit code에 반영 안 함. wfy/zamort/zleg/impossible0/sens_red은 데이터 오류라 반영.
    return 0 if not (ci_fail or pb_fail or cc_fail or dup_rows or spike_rows or cont_rows
                     or wf_holes or pl_holes or wfy_rows or zamort_rows or zleg_rows
                     or zerolegs_rows or sens_red) else 2


if __name__ == "__main__":
    raise SystemExit(main())
