#!/usr/bin/env python3
"""라이브 사이트가 fetch 하는 아티팩트를 검사한다 — 불변식 1번의 집행자.

`CLAUDE.md` 불변식 1: **게이트가 검사하는 파일 = 사용자가 보는 파일.** 다르면 산수가 맞아도
소스가 틀린 통과가 된다.

2026-08-25 에 그 불변식을 기계로 대조했더니(런타임 추적: `scripts/_probes/
probe_20260825_trace_validator_reads.py`) `origin/main` 의 배포 HTML 4종이 fetch 하는 .json
16개 중 **6개를 어떤 검사기도 읽지 않고 있었다.** 그중 넷이 여기서 처음 검사를 받는다:

  · `NB_CSM_multiple.json`                     index.html·IFRS17.html 의 CSM 버블맵 원천
  · `data/dart/viz/csm_amort_schedule.json`     CSM 상각 스케줄 패널
  · `data/dart/viz/csm_waterfall_history.json`  CSM 워터폴 이력 패널 (정적 스냅샷)
  · `data/dart/viz/insurance_pl_breakdown.json` 보험손익 원표 패널

나머지 둘(`kics_tier1_utilization.json`·`kics_tier2_utilization.json`)은 `check_as_of` 의
mtime/provenance 층만 배포본을 보고 **값 검사는 `output/tier{1,2}_utilization/` 빌더 산출물을
읽는다** — 같은 병이라 여기서 값 축을 배포본으로 잡는다.

**검사처럼 보이는 무검사 금지.** 파일 존재 여부 같은 형식 검사는 이 저장소가 반복해서 데인
함정이다. 여기 있는 룰은 전부 **마스터와의 교차대조** 또는 **파일 안에서 닫혀야 하는 산수**
또는 **기대 그리드 census** 다.

### 심각도 계약

  RED    baseline 에 없는 신규 발견 → exit 2 → push 차단
  YELLOW baseline 에 등재된 기지(旣知) 결함 → 매 실행 사유·티켓과 함께 인쇄 (조용한 skip 아님)

baseline = `data/_gold/live_artifact_baseline.json`. **통째 skip 이 아니라 건별 등재**다
(`statutory_reserve_baseline.json` 선례: "parser 가 고칠 때마다 줄을 지운다"). 등재 항목이
고쳐지면 STALE 로 인쇄되므로 baseline 이 거짓말을 하기 시작하면 바로 보인다.

사용:
    python scripts/validate_live_artifacts.py
    python scripts/validate_live_artifacts.py --emit-baseline   # 현 상태를 baseline 으로 박제
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

BASELINE_PATH = ROOT / "data" / "_gold" / "live_artifact_baseline.json"

# viz 파일들은 회사명만 갖고 코드가 없는데 표기가 파일마다 다르다(실측:
# scripts/_probes/probe_20260825_company_name_alias.py — 전 파일 합쳐 7개, 닫힌 집합).
# 이름으로 census 를 돌리면 이 7개가 통째로 "결측"으로 뜬다 = 오탐 발생기.
COMPANY_ALIAS = {
    "미래에셋생명": "미래에셋생명보험",
    "삼성생명": "삼성생명보험",
    "코리안리": "코리안리재보험",
    "아이비케이연금보험": "IBK연금보험",
    "케이비라이프생명보험": "KB라이프생명",
    "에이아이지손해보험": "AIG손해보험",
    "엠지손해보험": "예별손해보험",     # KR0004 구MG = 예별 (memory reference_mg_yebyeol_kics_history)
}

STAGE2ITEM = {"opening": 1, "new_business": 2, "interest": 3,
              "assumption": 4, "amortization": 5, "closing": 6}


# --------------------------------------------------------------------------- utils
def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def canon(name: str) -> str:
    return COMPANY_ALIAS.get(name, name)


def qkey(q: str):
    y, n = q.split(".")
    return (int(y), int(n[0]))


def prev_q(q: str):
    y, n = qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def parse_num(s):
    """표 셀 문자열 → 수. 괄호·△ 는 음수 (잔액표/BS 관행)."""
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace(" ", "")
    if t in ("", "-", "–", "—"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace("△", "-").replace("▲", "-")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


class Findings:
    def __init__(self):
        self.rows: list[dict] = []

    def add(self, artifact, rule, key, detail):
        self.rows.append({"artifact": artifact, "rule": rule, "key": key, "detail": detail})

    def ids(self):
        return {f"{r['artifact']}|{r['rule']}|{r['key']}" for r in self.rows}


# --------------------------------------------------------------------------- indexes
def wf_by_code():
    idx = defaultdict(dict)
    name = {}
    for r in load("CSM_waterfall.json"):
        idx[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = r["값"]
        name[r["원보험사코드"]] = r["원수사명"]
    return idx, name


def wf_by_name():
    idx = defaultdict(dict)
    for r in load("CSM_waterfall.json"):
        idx[(r["원수사명"], r["공시분기"])][r["항목번호"]] = r["값"]
    return idx


# --------------------------------------------------------------------------- 1) NB
def check_nb_csm_multiple(fd: Findings) -> dict:
    """`NB_CSM_multiple.json` — index.html CSM 버블맵의 원천.

    지금까지 **어떤 검사기도 이 파일을 읽지 않았다.** `validate_nb_csm_multiple.py` 는 이름이
    같지만 자기 산출물(`data/_derived/nb_csm_validation.json`)과 상류 `data/ir/nb_csm_ratio.json`
    만 본다 — `validate_master_tables` 의 PL 축과 **같은 병**이다(배포본 아닌 파일을 검사).

    네 축. 배수축은 연누계·당분기 **둘 다** 검산한다 (한 축만 걸면 나머지가 검증 사각이 된다 —
    이 저장소의 적용전/적용후 사고와 같은 구조).
    """
    nb = load("NB_CSM_multiple.json")
    idx = {(r["원보험사코드"], r["공시분기"]): r for r in nb}
    wf, _ = wf_by_code()
    stat = defaultdict(int)

    # (a) 배수 = CSM / 월납월초보험료  — 파일 안에서 닫혀야 하는 산수
    for axis in ("연누계", "당분기"):
        for r in nb:
            c, prem, m = (r.get(f"신계약CSM_{axis}"), r.get(f"월납월초보험료_{axis}"),
                          r.get(f"신계약CSM배수_{axis}"))
            if c is None or prem is None or m is None or prem == 0:
                stat[f"ratio_{axis}_skip"] += 1
                continue
            exp = c / prem
            if abs(exp - m) > max(0.01, 0.005 * abs(exp)):
                fd.add("NB_CSM_multiple.json", f"NB_RATIO_IDENTITY_{axis}",
                       f"{r['원보험사코드']}|{r['공시분기']}",
                       f"배수={m:.4f} 인데 CSM/보험료={exp:.4f} (CSM={c}, prem={prem})")
                stat[f"ratio_{axis}_fail"] += 1
            else:
                stat[f"ratio_{axis}_pass"] += 1

    # (b) 당분기 = 연누계(Q) - 연누계(Q-1). 유량 컬럼이 두 벌 있으면 서로 닫혀야 한다.
    for field in ("신계약CSM", "월납월초보험료"):
        for r in nb:
            cur, ytd = r.get(f"{field}_당분기"), r.get(f"{field}_연누계")
            if cur is None or ytd is None:
                stat[f"ytd_{field}_skip"] += 1
                continue
            pq = prev_q(r["공시분기"])
            if pq is None:
                exp = ytd
            else:
                pr = idx.get((r["원보험사코드"], pq))
                if pr is None or pr.get(f"{field}_연누계") is None:
                    stat[f"ytd_{field}_skip"] += 1
                    continue
                exp = ytd - pr[f"{field}_연누계"]
            if abs(exp - cur) > max(0.5, 0.01 * abs(exp)):
                fd.add("NB_CSM_multiple.json", f"NB_YTD_QUARTERLY_{field}",
                       f"{r['원보험사코드']}|{r['공시분기']}",
                       f"당분기={cur:,.2f} 인데 YTD 차={exp:,.2f}")
                stat[f"ytd_{field}_fail"] += 1
            else:
                stat[f"ytd_{field}_pass"] += 1

    # (c) 마스터 교차대조 — 화면 수치가 마스터와 다르면 그건 다른 데이터다.
    for r in nb:
        a = r.get("신계약CSM_연누계")
        b = wf.get((r["원보험사코드"], r["공시분기"]), {}).get(2)
        if a is None or b is None:
            stat["xwf_skip"] += 1
            continue
        if abs(a - b) > max(1.0, 0.01 * abs(b)):
            fd.add("NB_CSM_multiple.json", "NB_VS_WATERFALL",
                   f"{r['원보험사코드']}|{r['공시분기']}",
                   f"NB 신계약CSM_연누계={a:,.1f} vs CSM_waterfall 항목2={b:,.1f} "
                   f"(Δ={a - b:+,.1f}, ratio={a / b if b else float('nan'):.3f})")
            stat["xwf_fail"] += 1
        else:
            stat["xwf_pass"] += 1

    # (d) census — 등식은 0들로도 닫힌다. 통째 결측은 값 검사로 못 잡는다.
    grid = {k for k, v in wf.items() if v.get(2) is not None}
    for c, q in sorted(grid - set(idx)):
        fd.add("NB_CSM_multiple.json", "NB_CENSUS_MISSING", f"{c}|{q}",
               "CSM_waterfall 에 신계약CSM 이 있는데 NB 배포본에 그 (회사,분기) 행이 없다")
        stat["census_missing"] += 1
    stat["census_grid"] = len(grid)
    stat["census_rows"] = len(idx)
    return stat


# --------------------------------------------------------------------------- 2) amort
def check_csm_amort_schedule(fd: Findings) -> dict:
    """`data/dart/viz/csm_amort_schedule.json` — CSM 상각 스케줄 패널.

    세 축: ① 표 안 산수(연차 버킷 합 == 합계) ② 마스터 기말 CSM 과의 규모 대조 ③ census.
    ①은 **장기 꼬리 버킷 누락**을 잡는다 — 실측 2026-08-25 에 39사 중 22사가 Σ(연차) < 합계로
    -35~-44% 벌어져 있었다(원표 헤더에 16~20년·21~25년·26~30년·30년이후 컬럼이 있는데
    추출은 y1~y10 + y10plus(=11~15년) 까지만 담는다). 화면 막대가 그만큼 짧다.
    """
    a = load("data/dart/viz/csm_amort_schedule.json")
    wf = wf_by_name()
    latest = {}
    for (co, q), items in wf.items():
        if items.get(6) is None:
            continue
        if co not in latest or qkey(q) > qkey(latest[co][0]):
            latest[co] = (q, items[6])
    stat = defaultdict(int)

    for c in a["companies"]:
        co = canon(c["company"])
        st = c.get("status")
        stat[f"status_{st}"] += 1
        if st != "ok":
            fd.add("csm_amort_schedule.json", "AMORT_STATUS_NOT_OK", co,
                   f"status={st} — 패널이 이 회사를 빈칸으로 그린다")
            continue

        for kind in ("yearly", "buckets"):
            d = c.get(kind) or {}
            tot = d.get("total")
            if tot is None:
                continue
            s = sum(v for k, v in d.items() if k != "total" and isinstance(v, (int, float)))
            if abs(s - tot) > max(1.0, 0.005 * abs(tot)):
                fd.add("csm_amort_schedule.json", f"AMORT_{kind.upper()}_SUM_NE_TOTAL", co,
                       f"Σ={s:,.1f} vs total={tot:,.1f} (Δ={s - tot:,.1f}, "
                       f"{(s / tot - 1) * 100 if tot else 0:+.1f}%)")
                stat[f"{kind}_fail"] += 1
            else:
                stat[f"{kind}_pass"] += 1

        tot = (c.get("yearly") or {}).get("total") or (c.get("buckets") or {}).get("total")
        if tot is None or co not in latest:
            stat["xwf_skip"] += 1
            continue
        q, closing = latest[co]
        if not closing:
            stat["xwf_skip"] += 1
            continue
        ratio = abs(tot / closing)
        # 미래 인식될 CSM 총액은 기말 CSM 과 같은 자릿수여야 한다. 밴드 밖 = 단위 미정규화 의심.
        if ratio < 0.05 or ratio > 20:
            fd.add("csm_amort_schedule.json", "AMORT_TOTAL_VS_CLOSING_CSM_SCALE", co,
                   f"{q} 상각스케줄 합계={tot:,.1f} vs 기말CSM={closing:,.1f} "
                   f"(ratio={ratio:.4f}) — 단위 미정규화 의심")
            stat["xwf_scale_fail"] += 1
        elif not (0.6 <= ratio <= 1.4):
            fd.add("csm_amort_schedule.json", "AMORT_TOTAL_VS_CLOSING_CSM_BAND", co,
                   f"{q} 상각스케줄 합계={tot:,.1f} vs 기말CSM={closing:,.1f} (ratio={ratio:.3f})")
            stat["xwf_band_fail"] += 1
        else:
            stat["xwf_pass"] += 1

    have = {canon(c["company"]) for c in a["companies"]}
    allco = {co for co, _ in wf}
    for co in sorted(allco - have):
        fd.add("csm_amort_schedule.json", "AMORT_CENSUS_MISSING", co,
               "CSM_waterfall 마스터에 있는 회사인데 상각스케줄에 없다")
        stat["census_missing"] += 1
    stat["companies"] = len(a["companies"])
    return stat


# --------------------------------------------------------------------------- 3) history
def check_csm_waterfall_history(fd: Findings) -> dict:
    """`data/dart/viz/csm_waterfall_history.json` — CSM 워터폴 이력 패널.

    **아무도 재생성하지 않는 정적 스냅샷이다.** 선언된 빌더
    (`scripts/ifrs17_batch_historical.py`, 파일의 `source` 필드)는 2026-06 에 아카이브됐다.
    그래서 마스터가 백필·정정될 때마다 이 파일은 그 자리에 남아 벌어진다 — 화면은 그 벌어진
    값을 그린다. 벌어진 규모를 **지금 재고**, 정합화(재생성 또는 마스터 파생으로 교체)는
    parser 발주로 넘긴다. 검사는 지금 건다 — 안 걸면 영원히 안 걸린다.

    세 축: ① 파일 안 단계 항등식 ② 마스터 셀 대조(백만원→억원 /100) ③ census.
    """
    h = load("data/dart/viz/csm_waterfall_history.json")
    wf = wf_by_name()
    stat = defaultdict(int)

    for c in h["companies"]:
        co = canon(c["company"])
        for q, p in (c.get("periods") or {}).items():
            stages = p.get("stages") or {}
            vals = {k: (stages.get(k) or {}).get("value_mn_krw") for k in STAGE2ITEM}

            if all(vals[k] is not None for k in STAGE2ITEM):
                lhs = vals["closing"]
                rhs = sum(vals[k] for k in ("opening", "new_business", "interest",
                                            "assumption", "amortization"))
                if abs(lhs - rhs) > max(1.0, 0.001 * abs(lhs)):
                    fd.add("csm_waterfall_history.json", "HIST_STAGE_IDENTITY", f"{co}|{q}",
                           f"closing={lhs:,.0f} vs Σ(단계)={rhs:,.0f} (Δ={lhs - rhs:,.0f} 백만원)")
                    stat["identity_fail"] += 1
                else:
                    stat["identity_pass"] += 1
            else:
                stat["identity_skip"] += 1

            m = wf.get((co, q))
            if m is None:
                fd.add("csm_waterfall_history.json", "HIST_NOT_IN_MASTER", f"{co}|{q}",
                       "이력 스냅샷에는 있는데 CSM_waterfall 마스터에 그 (회사,분기)가 없다")
                stat["not_in_master"] += 1
                continue
            for stage, item in STAGE2ITEM.items():
                hv, mv = vals[stage], m.get(item)
                if hv is None or mv is None:
                    stat["drift_skip"] += 1
                    continue
                hv_eok = hv / 100.0                     # 백만원 → 억원
                if abs(hv_eok - mv) > max(2.0, 0.01 * abs(mv)):
                    fd.add("csm_waterfall_history.json", "HIST_MASTER_DRIFT",
                           f"{co}|{q}|{stage}",
                           f"snapshot={hv_eok:,.1f} vs master={mv:,.1f} (Δ={hv_eok - mv:+,.1f} 억원)")
                    stat["drift_fail"] += 1
                else:
                    stat["drift_pass"] += 1

    have = {canon(c["company"]) for c in h["companies"]}
    allco = {co for co, _ in wf}
    for co in sorted(allco - have):
        fd.add("csm_waterfall_history.json", "HIST_CENSUS_MISSING", co,
               "마스터에 있는 회사인데 이력 스냅샷에 없다 — 패널에서 통째로 빠진다")
        stat["census_missing"] += 1
    stat["companies"] = len(h["companies"])
    return stat


# --------------------------------------------------------------------------- 4) ins pl
def check_insurance_pl_breakdown(fd: Findings) -> dict:
    """`data/dart/viz/insurance_pl_breakdown.json` — 보험손익 원표 패널.

    원표를 문자열 그대로 담는 파일이라 항등식을 통째로 걸 수는 없다. 대신 **마스터와 겹치는
    한 행**(`보험계약마진상각`)을 뽑아 `PL_breakdown.json` 의 `원수CSM상각`(백만원)과 대조한다.
    실측(2026-08-25) 29사 중 그 행이 잡히는 10사에서 8사가 ratio 0.87~1.04 로 붙었다 —
    신호가 있는 대조다. 나머지는 census 로 센다.
    """
    p = load("data/dart/viz/insurance_pl_breakdown.json")
    pl = defaultdict(dict)
    plco = set()
    for r in load("PL_breakdown.json"):
        pl[(r["원수사명"], r["공시분기"])][(r["항목명"] or "").replace(" ", "")] = r["값"]
        plco.add(r["원수사명"])
    stat = defaultdict(int)

    for c in p["companies"]:
        co = canon(c["company"])
        st = c.get("status")
        stat[f"status_{st}"] += 1
        if st != "ok":
            fd.add("insurance_pl_breakdown.json", "INSPL_STATUS_NOT_OK", co, f"status={st}")
            continue

        rc = str(c.get("rcept_no") or "")
        try:
            q = f"{int(rc[:4]) - 1}.4Q"          # 사업보고서는 직전 사업연도 표
        except ValueError:
            stat["xpl_skip"] += 1
            continue

        val = None
        for row in (c.get("table") or []):
            if row and re.sub(r"\s+", "", str(row[0])) == "보험계약마진상각":
                nums = [x for x in (parse_num(v) for v in row[1:]) if x is not None]
                if nums:
                    val = nums[-1]
                break
        m = pl.get((co, q), {}).get("원수CSM상각")
        if val is None or m is None or m == 0:
            stat["xpl_skip"] += 1
            continue
        ratio = abs(val) / abs(m)
        if ratio > 100 or ratio < 0.01:
            fd.add("insurance_pl_breakdown.json", "INSPL_CSM_AMORT_SCALE", f"{co}|{q}",
                   f"표 보험계약마진상각 합계={val:,.1f} vs PL 마스터 원수CSM상각={m:,.1f} "
                   f"(ratio={ratio:,.1f}) — 행/열 오선택 또는 단위 미정규화 의심")
            stat["xpl_scale_fail"] += 1
        elif not (0.5 <= ratio <= 2.0):
            fd.add("insurance_pl_breakdown.json", "INSPL_CSM_AMORT_BAND", f"{co}|{q}",
                   f"표={val:,.1f} vs 마스터={m:,.1f} (ratio={ratio:.3f})")
            stat["xpl_band_fail"] += 1
        else:
            stat["xpl_pass"] += 1

    have = {canon(c["company"]) for c in p["companies"]}
    for co in sorted(plco - have):
        fd.add("insurance_pl_breakdown.json", "INSPL_CENSUS_MISSING", co,
               "PL 마스터에 있는 회사인데 보험손익 원표 패널에 없다")
        stat["census_missing"] += 1
    stat["companies"] = len(p["companies"])
    return stat


# --------------------------------------------------------------------------- 5) tier
# K-ICS.html 의 자본증권 도넛이 실제로 읽는 필드 전부 (updateDonutPanel, L906-917):
#   L906/907 utilization_pct(t1,t2) · L912 tier1_hybrid_issued_eok / tier1_hybrid_limit_eok
#   L917 numerator_eok / tier2_limit_eok
# 배포본↔빌더 대조를 utilization_pct 한 필드로만 걸어 두었더니(2026-08-25 최초 배선) 나머지
# 네 필드는 배포본에서 어떤 값으로 틀어져도 두 게이트가 전부 exit 0 이었다 — 변이시험 실측
# (2026-08-25 validation 재확인): 배포본 하나손해 tier1_hybrid_issued_eok 1,000.0 → 0.0 /
# → 500.0, 아이엠라이프 tier2 hybrid_eok·grandfathered_subordinated_eok → 0.0 넷 다
# live_artifacts exit 0 · data_contract exit 0. 화면은 "발행 0억 / 한도 694억 · 소진율
# 144.1%" 라는 자기모순 상태를 그리는데 아무 룰도 안 걸린다. 이번 사고에서 실제로 0 이었던
# 필드가 바로 그 issued 다(소진율까지 같이 0 이라 우연히 걸렸을 뿐).
# 소진율 항등식은 분자로 tier1_hybrid_recognized_eok 를 쓰므로 issued 를 보지 않고,
# validate_data_contract 의 CAPSEC 축은 배포본이 아니라 빌더 산출물을 읽는다(_load_tier) —
# 즉 이 네 필드에는 배포본을 보는 룰이 하나도 없었다. 여기서 붙인다.
# 이것은 소스 대조가 아니라 **같은 파이프라인의 두 산출물 동일성** 대조라, 다르면 조립을
# 건너뛴 것 외의 해석이 없다(관찰기 YELLOW 를 거칠 이유가 없는 RED).
_TIER_SCREEN_FIELDS = {
    "tier1": ("utilization_pct", "tier1_hybrid_issued_eok", "tier1_hybrid_limit_eok"),
    "tier2": ("utilization_pct", "numerator_eok", "tier2_limit_eok"),
}


def check_tier_utilization(fd: Findings) -> dict:
    """`kics_tier{1,2}_utilization.json` — 배포본의 **값**을 처음으로 검사한다.

    `validate_data_contract.ARTIFACTS` 는 이 두 파일을 배포 경로로 등록해 두었지만
    (2026-07-22 에 죽은 `templates/` 사본에서 옮겨온 자리), `_load_tier()` 는 값 검사를 위해
    `output/tier{1,2}_utilization/tier{1,2}_utilization_*.json` 빌더 산출물을 읽는다.
    즉 mtime·provenance 는 배포본을 보는데 **숫자는 상류를 본다.** 런타임 추적에서 배포본이
    한 번도 열리지 않는 것으로 확인됐다(2026-08-25). 여기서 배포본 자체를 연다.

    축: ① 배포본이 파싱되는가(깨진 파일 ≠ 없는 파일) ② **배포본 == 빌더 산출물**(분기·회사·
    소진율 값) — 게이트가 검사한 그 숫자가 실제로 배포됐는지 ③ 소진율 = 분자/한도×100 정의.

    ②가 이 함수의 존재 이유다. 게이트가 상류를 검사하고 화면은 하류를 보는 구조에서는
    "검사한 것"과 "보여준 것"이 갈라져도 아무도 모른다. 여기서 그 둘을 붙인다.
    """
    stat = defaultdict(int)
    for tier in ("tier1", "tier2"):
        rel = f"kics_{tier}_utilization.json"
        path = ROOT / rel
        if not path.exists():
            fd.add(rel, "TIER_ARTIFACT_MISSING", tier, "배포본이 없다")
            continue
        try:
            dep = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            fd.add(rel, "TIER_ARTIFACT_UNREADABLE", tier,
                   f"{type(e).__name__}: {e} — 있는데 파싱이 안 된다(하류는 '없음'으로 취급)")
            continue

        rows = dep.get("results") or []
        stat[f"{tier}_rows"] = len(rows)
        dep_q = dep.get("quarter")

        # ③ 소진율 정의 — 파일 안에서 닫혀야 하는 산수
        num_key = "numerator_eok" if tier == "tier2" else "tier1_hybrid_recognized_eok"
        lim_key = "tier2_limit_eok" if tier == "tier2" else "tier1_hybrid_limit_eok"
        for r in rows:
            co = r.get("company") or r.get("code")
            u, n, lim = r.get("utilization_pct"), r.get(num_key), r.get(lim_key)
            if u is None or n is None or lim in (None, 0):
                stat[f"{tier}_util_skip"] += 1
                continue
            # 소진율은 **자르지 않는다** — owner 2026-06-14 결정(docs/changelog_designer.md:783-789,
            # designer 프롬프트 L177 LOCKED). 분자=발행액(KOFIA/DART), 분모=인정한도(공시)로 소스가
            # 독립이라 >100% 가 정당하게 나온다. 자르는 것은 화면 원호뿐이고(K-ICS.html L833),
            # 숫자는 '100%+' + 툴팁 실제값(L841/L879)으로 표기한다. 2026-08-25 이전 이 자리에 있던
            # min(100, ...) 은 그 결정과 반대로 구현된 것이었고, 데이터쪽 캡(6사)을 정상으로
            # 통과시켜 화면이 평평한 100% 를 그리게 했다.
            exp = n / lim * 100.0
            if abs(exp - u) > max(0.15, 0.005 * abs(exp)):
                fd.add(rel, "TIER_UTILIZATION_IDENTITY", str(co),
                       f"utilization_pct={u} 인데 {num_key}/{lim_key}×100={exp:.2f}")
                stat[f"{tier}_util_fail"] += 1
            else:
                stat[f"{tier}_util_pass"] += 1
            if u < 0:
                fd.add(rel, "TIER_UTILIZATION_NEGATIVE", str(co),
                       f"utilization_pct={u} — 소진율은 음수일 수 없다")

        # ② 배포본 vs 빌더 산출물(게이트가 실제로 검사하는 쪽)
        base = ROOT / "output" / f"{tier}_utilization"
        files = sorted(base.glob(f"{tier}_utilization_*.json")) if base.exists() else []
        if not files:
            stat[f"{tier}_no_builder_output"] = 1
            continue
        try:
            up = json.loads(files[-1].read_text(encoding="utf-8"))
        except Exception as e:
            fd.add(rel, "TIER_BUILDER_UNREADABLE", tier, f"{files[-1].name}: {e}")
            continue
        up_q = up.get("quarter")
        if dep_q and up_q and dep_q != up_q:
            fd.add(rel, "TIER_DEPLOYED_QUARTER_STALE", f"{dep_q}->{up_q}",
                   f"배포본 quarter={dep_q} 인데 빌더 최신 산출물({files[-1].name})은 {up_q} — "
                   f"게이트의 값 검사는 빌더 쪽을 읽으므로 이 어긋남을 보지 못한다")
            stat[f"{tier}_quarter_stale"] = 1
        urows = {(r.get("company") or r.get("code")): r for r in (up.get("results") or [])}
        drows = {(r.get("company") or r.get("code")): r for r in rows}
        for co in sorted(set(urows) - set(drows), key=str):
            fd.add(rel, "TIER_DEPLOYED_MISSING_COMPANY", str(co),
                   f"빌더 산출물({files[-1].name})에 있는데 배포본에 없다")
            stat[f"{tier}_behind"] += 1
        if dep_q == up_q:
            for co in sorted(set(urows) & set(drows), key=str):
                for fld in _TIER_SCREEN_FIELDS[tier]:
                    a, b = drows[co].get(fld), urows[co].get(fld)
                    if a is None and b is None:
                        continue
                    if a is None or b is None:
                        fd.add(rel, "TIER_DEPLOYED_VALUE_DIFFERS", str(co),
                               f"배포본 {fld}={a} vs 빌더 산출물={b} — 한쪽만 결측이다"
                               f"(화면이 읽는 필드라 빈칸으로 그려진다)")
                        stat[f"{tier}_value_differs"] += 1
                        continue
                    if abs(a - b) > max(0.15, 0.005 * abs(b)):
                        fd.add(rel, "TIER_DEPLOYED_VALUE_DIFFERS", str(co),
                               f"배포본 {fld}={a} vs 빌더 산출물={b} — 같은 분기인데 다르다")
                        stat[f"{tier}_value_differs"] += 1
    return stat


# --------------------------------------------------------------------------- 6) public_exports
# `public_exports/*.json` 은 사이트의 다운로드 기능(`download-survey.js`)이 그대로 사용자에게
# 내려보내는 파일이다. 2026-08-30 실측: **어떤 검사기도 이 폴더를 읽지 않았다**
# (`grep -rn "public_exports" scripts/validate_*.py` -> 0건). 화면 패널만 검사하고 사용자가
# 실제로 내려받는 파일은 무검사였다 — 불변식 1번의 두 번째 구멍이다
# (inbox/validation/20260830T1500Z).
#
# **파일 목록을 여기에 다시 타이핑하지 않는다.** `export_public_sheets.MASTERS` 를 그대로
# import 한다. 베껴 쓰면 그 순간부터 두 목록이 갈라지고, 새 시트가 추가돼도 이 게이트는
# 모르는 채로 통과한다 — 이 저장소가 반복해 온 "빠진 게이트를 눈치챌 때마다 룰을 한 개씩
# 베껴 심는" 패턴(CLAUDE.md ①b)이다. import 하면 시트가 늘어나는 순간 자동으로 검사된다.
#
# **비교 기준은 워킹트리가 아니라 `git show HEAD:`** — exporter 자신이 그렇게 읽기 때문이다
# (다른 세션의 미커밋 편집을 공개 스냅샷에 실으면 안 된다는 게 그 스크립트의 설계). 워킹트리와
# 대조하면 남의 미커밋 편집 때문에 매번 거짓 RED 가 난다. HEAD 로 대조하면 "마스터는 커밋됐는데
# 스냅샷 재생성을 안 했다" 만 정확히 걸린다.
#
# **조인 키를 잘못 잡으면 전건 미스로 조용히 통과한다** — public 쪽에는 `원보험사코드` 가 없다
# (owner 지시로 드롭). 그래서 키는 아래 식별열 중 그 시트에 실재하는 것들로 만들고, 그 조합이
# 유일하지 않으면 값 비교를 하지 않고 KEY_AMBIGUOUS 로 **막는다**(조용히 통과시키지 않는다).
_PE_ID_COLS = ("원수사명", "티커", "생손보여부", "공시분기", "항목번호", "항목명",
               "섹션", "레벨", "종류주", "경과차년", "measure구분", "경과조치여부",
               # 2026-08-30 `가정민감도` 시트 신설 때 추가. 그 시트는 (회사, 분기) 하나에
               # 시나리오가 여러 줄이라 기존 식별열만으로는 163행이 중복됐고, 게이트가
               # `KEY_AMBIGUOUS` 로 **막았다**(조용히 통과시키지 않았다) — 이 룰이 설계대로
               # 동작한 첫 사례다. `기준일`은 값이 아니라 식별정보라 여기에 둔다.
               "기준일", "순번", "위험구분", "충격수준")


def check_public_exports(fd: Findings) -> dict:
    """`public_exports/*.json` — 사용자가 내려받는 스냅샷을 루트 마스터(HEAD)와 대조한다.

    축: ① 파일이 있고 파싱되는가 ② 루트 마스터(HEAD, exporter 와 동일 기준)와 **셀 단위로
    같은가** ③ 기대 그리드는 마스터다(마스터에 있는 행이 스냅샷에 없으면 SKIP 이 아니라 RED)
    ④ 내부 전용 열(`원보험사코드`)이 새어 나가지 않았는가 ⑤ manifest 가 실제 파일과 맞는가.

    발견은 (시트, 룰) 단위로 1건씩 집계한다 — 스냅샷이 한 세대 밀리면 전 행이 어긋나서
    11,546건이 찍히는데, 그 11,546건의 조치는 전부 하나("exporter 재실행")다.
    """
    stat = defaultdict(int)
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from export_public_sheets import (MASTERS, FLATTEN, _DROP_COLS, _QUARTER_RE,
                                          read_committed_json)
    except Exception as e:
        fd.add("public_exports/", "PUBLIC_EXPORT_EXPORTER_UNIMPORTABLE", "-",
               f"{type(e).__name__}: {e} — 시트 목록을 exporter 에서 가져오지 못했다")
        return stat

    out_dir = ROOT / "public_exports"
    if not out_dir.exists():
        fd.add("public_exports/", "PUBLIC_EXPORT_DIR_MISSING", "-",
               "public_exports/ 가 없다 — 사이트 다운로드가 전부 404 다")
        return stat

    stat["sheets_declared"] = len(MASTERS)
    seen_sheets = []
    for json_name, sheet in MASTERS:
        rel = f"public_exports/{sheet}.json"
        seen_sheets.append(sheet)
        path = out_dir / f"{sheet}.json"
        if not path.exists():
            fd.add(rel, "PUBLIC_EXPORT_FILE_MISSING", sheet,
                   f"{json_name} 의 공개 스냅샷이 없다 — 다운로드 시 이 시트가 통째로 빈다")
            continue
        try:
            pub = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            fd.add(rel, "PUBLIC_EXPORT_UNREADABLE", sheet,
                   f"{type(e).__name__}: {e} — 있는데 파싱이 안 된다(깨진 파일 != 없는 파일)")
            continue

        try:
            exp = read_committed_json(json_name)
        except Exception as e:
            fd.add(rel, "PUBLIC_EXPORT_SOURCE_UNREADABLE", sheet,
                   f"git show HEAD:{json_name} 실패 — {type(e).__name__}: {e}")
            continue
        flatten = FLATTEN.get(json_name)
        if flatten is not None:
            exp = flatten(exp)
        exp = [{k: v for k, v in r.items() if k not in _DROP_COLS} for r in exp]

        stat[f"rows_{sheet}"] = len(pub)

        leaked = sorted({c for r in pub for c in r} & set(_DROP_COLS))
        if leaked:
            fd.add(rel, "PUBLIC_EXPORT_INTERNAL_COL_LEAKED", sheet,
                   f"내부 전용 열 {leaked} 이 공개 스냅샷에 있다 "
                   f"(owner 지시 2026-08-28: 공개 다운로드에서 제외)")

        cols = sorted({k for r in exp for k in r})
        key_cols = [c for c in _PE_ID_COLS if c in cols]
        val_cols = [c for c in cols if c not in key_cols]
        if not key_cols or not val_cols:
            fd.add(rel, "PUBLIC_EXPORT_KEY_AMBIGUOUS", sheet,
                   f"식별열/값열을 나누지 못했다(cols={cols}) — _PE_ID_COLS 를 갱신해라. "
                   f"이대로 두면 값 비교가 통째로 건너뛰어진다")
            continue

        def _k(r):
            return tuple(r.get(c) for c in key_cols)

        ei: dict = {}
        dup_e = 0
        for r in exp:
            k = _k(r)
            if k in ei:
                dup_e += 1
            ei[k] = r
        if dup_e:
            fd.add(rel, "PUBLIC_EXPORT_KEY_AMBIGUOUS", sheet,
                   f"마스터 쪽에서 키 {key_cols} 가 유일하지 않다(중복 {dup_e}행) — "
                   f"셀 비교가 성립하지 않는다. 식별열을 늘려라")
            continue
        pi = {_k(r): r for r in pub}

        miss = sorted(set(ei) - set(pi))
        extra = sorted(set(pi) - set(ei))
        if miss:
            stat[f"missing_{sheet}"] = len(miss)
            fd.add(rel, "PUBLIC_EXPORT_MISSING_CELL", sheet,
                   f"마스터에 있는데 스냅샷에 없는 행 {len(miss)}건 "
                   f"(예: {miss[:3]}) — 기대 그리드는 마스터다. exporter 를 재실행해라")
        if extra:
            stat[f"extra_{sheet}"] = len(extra)
            fd.add(rel, "PUBLIC_EXPORT_EXTRA_CELL", sheet,
                   f"스냅샷에만 있는 행 {len(extra)}건 (예: {extra[:3]}) — "
                   f"마스터에서 지워진 행이 공개본에 남아 있다")

        drift, examples = 0, []
        for k in set(ei) & set(pi):
            for c in val_cols:
                a, b = pi[k].get(c), ei[k].get(c)
                if a != b:
                    drift += 1
                    if len(examples) < 3:
                        examples.append(f"{k}|{c}: 공개={a} vs 마스터={b}")
        if drift:
            stat[f"drift_{sheet}"] = drift
            fd.add(rel, "PUBLIC_EXPORT_DRIFT", sheet,
                   f"값이 다른 셀 {drift}건 — {' / '.join(examples)}. "
                   f"마스터가 커밋됐는데 스냅샷 재생성이 밀렸다: "
                   f"python scripts/export_public_sheets.py")

    # manifest — 다운로드 xlsx 표지가 이 값을 그대로 인쇄한다(행수·분기범위·스냅샷 생성일시).
    mpath = out_dir / "manifest.json"
    if not mpath.exists():
        fd.add("public_exports/manifest.json", "PUBLIC_EXPORT_MANIFEST_MISSING", "-",
               "manifest 가 없다 — 다운로드 표지 시트가 빈칸으로 나간다")
        return stat
    try:
        man = json.loads(mpath.read_text(encoding="utf-8"))
    except Exception as e:
        fd.add("public_exports/manifest.json", "PUBLIC_EXPORT_MANIFEST_UNREADABLE", "-",
               f"{type(e).__name__}: {e}")
        return stat
    msheets = man.get("sheets", {})
    for sheet in seen_sheets:
        path = out_dir / f"{sheet}.json"
        if not path.exists():
            continue
        if sheet not in msheets:
            fd.add("public_exports/manifest.json", "PUBLIC_EXPORT_MANIFEST_SHEET_MISSING",
                   sheet, "파일은 있는데 manifest 에 없다")
            continue
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        qs = sorted({r.get("공시분기") for r in rows
                     if r.get("공시분기") and _QUARTER_RE.match(str(r.get("공시분기")))})
        want = {"rows": len(rows),
                "quarter_min": qs[0] if qs else None,
                "quarter_max": qs[-1] if qs else None}
        got = {k: msheets[sheet].get(k) for k in want}
        if got != want:
            fd.add("public_exports/manifest.json", "PUBLIC_EXPORT_MANIFEST_MISMATCH", sheet,
                   f"manifest={got} vs 실제 파일={want} — 표지 시트가 사실과 다른 수를 인쇄한다")
    ghost = sorted(set(msheets) - set(seen_sheets))
    if ghost:
        fd.add("public_exports/manifest.json", "PUBLIC_EXPORT_MANIFEST_GHOST_SHEET",
               ",".join(ghost), f"manifest 에만 있고 exporter 목록에 없는 시트 {ghost}")
    stat["manifest_sheets"] = len(msheets)
    return stat


# --------------------------------------------------------------------------- baseline
# 등재는 **건별**이지만 사유는 룰 단위로 관리한다(같은 원인의 933건을 933번 적는 것은 문서가
# 아니라 소음이다). 사유 없는 등재는 이 게이트를 무력화하는 방법이므로 emit 시 강제한다.
RULE_REASON = {
    "csm_waterfall_history.json|HIST_MASTER_DRIFT":
        "정적 스냅샷 drift. 이 파일의 선언 빌더(scripts/ifrs17_batch_historical.py, 파일 "
        "source 필드)는 2026-06 에 아카이브돼 **아무도 재생성하지 않는다**. 마스터가 백필·"
        "정정될 때마다 이 파일은 그 자리에 남는다. 2026-08-25 실측: 대조 1,581셀 중 933건"
        "(59.0%) drift, 최대 Δ 43,852억(삼성화재 2023.3Q closing). **화면에는 안 나간다** — IFRS17.html 이 이 파일을 fetch 하지만 렌더 코드는 다른 소스를 쓴다(2026-08-25 origin/main 배포본 직접 대조로 확인, 종전 사유의 \"이력 패널이 그린다\" 는 오기라 정정). 따라서 사용자 피해는 없고, 파일의 거취(재생성 경로 복구 / 루트 마스터 파생 / 화면 fetch 제거)가 designer·owner 결정 대기 중이다. 마스터가 정정될 때마다 이 drift 는 **늘어난다** — 2026-08-25 삼성생명·교보생명 정정으로 11건 증가(917건으로 emit). "
        "2026-08-25(2차, inbox/parser/20260825T1520Z iter2 반영): 그 11건 증가는 실은 **CSM_waterfall 을 연결(consolidated) 기준으로 잘못 되돌린 결과**였다 — 이 스냅샷 자체가 삼성생명 한정으로 연결 기준(raw 확인: opening 12,392,570 백만은 _00761 연결에만 존재)이라, 마스터가 연결로 틀어지자 우연히 이 스냅샷과 더 가까워져 STALE 이 늘고 RED 가 준 것이었다. 삼성생명 CSM 을 별도(separate, gold basis)로 재복원하자 12건 RED(신규 drift) + 10건 STALE(더는 안 벌어짐) = 순증 2건, 919건으로 재emit. 이 스냅샷은 회사별로 기준이 혼재돼 있어(삼성생명=연결 확인, 신한라이프 opening 은 별도 쪽 문자열이 우세하게 일치 — 회사마다 다른, 이제는 아카이브된 파이프라인의 개별 버그) '전체가 연결'도 '전체가 별도'도 아니다 — drift 증감을 기준 판정의 근거로 쓰지 말 것.",
    "csm_waterfall_history.json|HIST_STAGE_IDENTITY":
        "스냅샷 자체의 단계 항등식 파탄 41건(opening+nb+int+assum+amort ≠ closing). 위와 같은 "
        "정적 스냅샷 결함 — 마스터 쪽 동일 (회사,분기) 는 closing identity 358P/0F 로 닫힌다.",
    "csm_waterfall_history.json|HIST_CENSUS_MISSING":
        "마스터 37사 중 스냅샷에 23사만 있어 14사가 패널에서 통째로 빠진다. 스냅샷이 만들어진 "
        "시점 이후 온보딩된 회사들이다.",
    "csm_waterfall_history.json|HIST_NOT_IN_MASTER":
        "스냅샷에는 있는데 마스터에 없는 (회사,분기). 회사명 별칭 정규화 후 잔여분.",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING":
        "배포본이 **한 분기 뒤처져 있다**. 31건 중 28건이 2026.2Q — 마스터 CSM_waterfall 은 "
        "2026.2Q 를 갖는데 NB 배포본의 최신 분기는 2026.1Q 다. 나머지 3건은 연차공시사 "
        "(라이나/AIA/메트라이프/하나/처브)의 4Q 결측.",
    "NB_CSM_multiple.json|NB_VS_WATERFALL":
        "예별손해보험 2023.4Q 신계약CSM 부호 반전(NB=-509.7 vs 마스터=+509.7). 화면 버블맵의 "
        "X축이 그 회사만 음수로 그려진다.",
    "csm_amort_schedule.json|AMORT_YEARLY_SUM_NE_TOTAL":
        "장기 꼬리 버킷 누락. 원표 헤더에 16~20년·21~25년·26~30년·30년이후 컬럼이 있는데 "
        "추출은 y1~y10 + y10plus(=11~15년)까지만 담는다 → 39사 중 22사에서 Σ(연차)가 합계보다 "
        "35~44% 작다. 화면 막대가 그만큼 짧다.",
    "csm_amort_schedule.json|AMORT_BUCKETS_SUM_NE_TOTAL":
        "위와 같은 원인(buckets 도 같은 연차 집계를 재사용한다).",
    "csm_amort_schedule.json|AMORT_STATUS_NOT_OK":
        "status=empty 4사 + partial 1사. 패널이 이 회사를 빈칸으로 그린다. 원표 부존재인지 "
        "추출 실패인지 raw 확인 전이라 단정하지 않는다(키워드 부재≠원문 부재, "
        "memory feedback_keyword_absence_is_not_source_absence).",
    "csm_amort_schedule.json|AMORT_TOTAL_VS_CLOSING_CSM_BAND":
        "상각스케줄 합계 / 기말CSM 이 0.28~0.57 인 4사(처브·AIA·메트라이프·라이나). 단위오류는 "
        "아니고(SCALE 룰 통과) PAA 적용분이 스케줄 표 밖일 가능성이 있다 — **미확인**. "
        "정당하면 legit 레지스트리로 옮기고, 아니면 추출 범위를 고쳐야 한다.",
    "csm_amort_schedule.json|AMORT_CENSUS_MISSING":
        "마스터에 있는데 상각스케줄에 없는 회사(별칭 정규화 후 잔여분).",
    "insurance_pl_breakdown.json|INSPL_CENSUS_MISSING":
        "PL 마스터 36사 중 29사만 있어 7사가 원표 패널에서 빠진다.",
    "insurance_pl_breakdown.json|INSPL_CSM_AMORT_SCALE":
        "한화손해보험 2024.4Q — 표의 보험계약마진상각 행 마지막 숫자가 -387,989,612 로 "
        "마스터(409,737)의 947배. 행 병합/열 오선택으로 셀 값이 이어붙은 파싱 사고다.",
    "insurance_pl_breakdown.json|INSPL_CSM_AMORT_BAND":
        "코리안리재보험 2024.4Q ratio 2.841. 2026-08-25 raw 재확인: 108,252 는 파싱 사고가 "
        "아니다 — data/dart/FY2024_Q4/raw/KR1000_코리안리_20250320001161/xml/"
        "20250320001161_00760.xml L14365 에 리터럴로 존재(캡션 '(4) 당기와 전기 중 "
        "보험손익 상세내역', 장기31,250+생명77,002+일반-=합계108,252). 마스터 원수CSM상각"
        "(38,102, PL_breakdown item4) 과 이 회사가 가진 나머지 CSM상각류 항목(item9 재보험 "
        "11,236 · item4-1 수재 33,740 · item9-1 출재 -8,756) 을 여러 조합으로 더해봐도 "
        "108,252 에 안 맞는다 — 원수/재보험/수재/출재 4축 구조라 이 표의 '합계' 열이 정확히 "
        "어느 조합인지 특정 못 함. **행/열 오선택이 아니라 재보험사 특유의 다축 구조에서 "
        "비교 앵커(item4 원수CSM상각 단독) 가 이 표 범위와 안 맞는 문제로 좁혀짐** — "
        "표시값은 원문 그대로이므로 안 고침. 다음 행동: PL_breakdown.json 쪽에서 이 표의 "
        "'합계' 열과 정확히 대응하는 파생 항목(또는 조합)을 규명하거나, 이 회사는 앵커 "
        "비교를 건너뛰도록 체커 쪽에서 판단할 것 — 둘 다 parser 단독 결정 범위 밖.",
    "insurance_pl_breakdown.json|INSPL_STATUS_NOT_OK": "status != ok.",
    "kics_tier1_utilization.json|TIER_DEPLOYED_VALUE_DIFFERS":
        "**불변식 1번 위반의 직접 증거.** 배포본(K-ICS.html 이 fetch)과 게이트가 실제로 검사하는 "
        "빌더 산출물(output/tier1_utilization/)이 같은 분기인데 값이 다르다. 하나손해보험: "
        "배포본 tier1_hybrid_issued=0 → 소진율 0.0%, 빌더 산출물은 1,000억 발행 → 100.0%. "
        "화면은 발행이 없는 것처럼 보인다.",
    "kics_tier2_utilization.json|TIER_DEPLOYED_VALUE_DIFFERS":
        "위와 같음. IBK연금보험(배포본 0.0% vs 빌더 22.2%, subordinated 0 vs 1,597.3억), "
        "아이엠라이프생명보험(0.0% vs 40.6%, hybrid 0 vs 948.8억) 등 3사.",
    "kics_tier1_utilization.json|TIER_DEPLOYED_QUARTER_STALE": "배포본 분기가 빌더보다 뒤처짐.",
    "kics_tier2_utilization.json|TIER_DEPLOYED_QUARTER_STALE": "배포본 분기가 빌더보다 뒤처짐.",
}

PROMOTE = (
    "승격 조건 — 아래를 충족하면 그 줄을 지우고 RED 로 되돌린다.\n"
    "  (1) 담당 stage 가 고쳐서 더는 실패하지 않으면 게이트가 BASELINE STALE 로 인쇄한다. "
    "그때 그 줄을 지운다(지우지 않으면 등재부가 거짓말을 시작한다).\n"
    "  (2) 등재에 없는 새 발견은 이미 RED 다 — exit 2 로 push 를 막는다. 초기 착지만 "
    "YELLOW 이고 신규는 처음부터 RED 다.\n"
    "  (3) 기한 2026-10-31. 그때까지 남은 줄은 (a) 정당하면 legit 레지스트리로 승격, "
    "(b) 아니면 RED 로 되돌린다. 무기한 방치 금지.\n"
    "  (4) csm_waterfall_history.json 은 예외적으로 **파일 자체의 처분**이 승격 조건이다 — "
    "빌더 재생성 또는 마스터 파생으로 교체(=drift 구조적으로 0). 그 전까지 drift 등재는 "
    "'스냅샷이 낡았다'는 사실의 박제이지 값의 승인이 아니다.\n"
    "라우팅: parser/ifrs17 (history·amort·insurance_pl·NB 부호), "
    "publishing (tier1/tier2 배포본 == 빌더 산출물 동기화, NB 배포본 분기 갱신)."
)


def load_baseline() -> dict:
    if not BASELINE_PATH.exists():
        return {"entries": {}, "_what": "", "_promote": ""}
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def main() -> int:
    fd = Findings()
    stats = {
        "NB_CSM_multiple.json": check_nb_csm_multiple(fd),
        "csm_amort_schedule.json": check_csm_amort_schedule(fd),
        "csm_waterfall_history.json": check_csm_waterfall_history(fd),
        "insurance_pl_breakdown.json": check_insurance_pl_breakdown(fd),
        "kics_tier{1,2}_utilization.json": check_tier_utilization(fd),
        "public_exports/*.json": check_public_exports(fd),
    }

    base = load_baseline()
    entries: dict = base.get("entries", {})
    reds, yellows = [], []
    for r in fd.rows:
        fid = f"{r['artifact']}|{r['rule']}|{r['key']}"
        (yellows if fid in entries else reds).append((fid, r))
    seen = {f"{r['artifact']}|{r['rule']}|{r['key']}" for r in fd.rows}
    stale = sorted(set(entries) - seen)

    print("=" * 96)
    print("LIVE ARTIFACT GATE — 라이브 HTML 이 fetch 하는 파일을 마스터와 대조한다")
    print("  (불변식 1: 게이트가 검사하는 파일 = 사용자가 보는 파일)")
    print("=" * 96)
    for art, st in stats.items():
        print(f"\n[{art}]")
        print("   " + "  ".join(f"{k}={v}" for k, v in sorted(st.items())))

    print("\n" + "=" * 96)
    print(f"YELLOW — baseline 등재 기지 결함 {len(yellows)}건 (조용한 skip 아님, 매 실행 인쇄)")
    print("=" * 96)
    byrule = defaultdict(list)
    for fid, r in yellows:
        byrule[(r["artifact"], r["rule"])].append(r)
    for (art, rule), rs in sorted(byrule.items()):
        note = entries.get(f"{art}|{rule}|{rs[0]['key']}", {})
        reason = note.get("reason", "") if isinstance(note, dict) else str(note)
        print(f"  {art} :: {rule}  ({len(rs)}건)")
        if reason:
            print(f"      사유: {reason}")
        for r in rs[:4]:
            print(f"      · {r['key']}  {r['detail']}")
        if len(rs) > 4:
            print(f"      · ... +{len(rs) - 4}건")

    if stale:
        print("\n" + "=" * 96)
        print(f"BASELINE STALE — 등재돼 있는데 더는 실패하지 않는다 {len(stale)}건")
        print("  고쳐진 것이면 baseline 에서 그 줄을 지워라. baseline 이 거짓말을 시작하는 자리다.")
        print("=" * 96)
        for fid in stale[:20]:
            print(f"  · {fid}")
        if len(stale) > 20:
            print(f"  · ... +{len(stale) - 20}건")

    print("\n" + "=" * 96)
    print(f"RED — baseline 에 없는 신규 발견 {len(reds)}건")
    print("=" * 96)
    for fid, r in reds:
        print(f"  RED  {r['artifact']} :: {r['rule']}  {r['key']}")
        print(f"       {r['detail']}")

    print("\n" + "#" * 96)
    print(f"SUMMARY live_artifacts  RED={len(reds)}  YELLOW(baselined)={len(yellows)}  "
          f"STALE_BASELINE={len(stale)}  총 발견={len(fd.rows)}")
    print("#" * 96)

    if "--emit-baseline" in sys.argv:
        missing = sorted({f"{r['artifact']}|{r['rule']}" for r in fd.rows} - set(RULE_REASON))
        if missing:
            print(f"\n[emit] 중단 — 사유가 없는 룰 {missing}. "
                  f"RULE_REASON 에 사유를 적어라. 사유 없는 등재가 이 게이트를 무력화한다.")
            return 2
        out = {
            "_what": "라이브 아티팩트 게이트(scripts/validate_live_artifacts.py)의 기지 결함 등재부. "
                     "건별 등재이며 통째 skip 이 아니다. 담당 stage 가 고칠 때마다 그 줄을 지운다 "
                     "(고쳐지면 게이트가 BASELINE STALE 로 알려준다). 선례: "
                     "data/_gold/statutory_reserve_baseline.json",
            "_emitted": "2026-08-25",
            "_promote": PROMOTE,
            "_counts": {},
            "entries": {},
        }
        for r in fd.rows:
            rk = f"{r['artifact']}|{r['rule']}"
            out["entries"][f"{rk}|{r['key']}"] = {
                "detail": r["detail"], "reason": RULE_REASON[rk], "first_seen": "2026-08-25"}
            out["_counts"][rk] = out["_counts"].get(rk, 0) + 1
        out["_counts"] = dict(sorted(out["_counts"].items(), key=lambda x: -x[1]))
        BASELINE_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"\n[emit] baseline {len(out['entries'])}건 -> {BASELINE_PATH}")
        for k, v in out["_counts"].items():
            print(f"   {v:5d}  {k}")
        return 0

    return 2 if reds else 0


if __name__ == "__main__":
    raise SystemExit(main())
