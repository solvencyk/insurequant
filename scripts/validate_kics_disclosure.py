#!/usr/bin/env python3
"""Validate root kics_disclosure.json against K-ICS JSON rules."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import (
    IMAGE_OCR_COMPANIES,
    DIVERSIFIED_SQRT_TOL_REL,
    IMAGE_OCR_TOLERANCE,
    IRR_DERIVED_TOL_REL,
    INTERNAL_MODEL_36IRR_EXEMPT,
    IRR_DERIVE_ISSUER_INCONSISTENT,
    IRR_PIN_TOL,
    IRR_SCENARIO_EXEMPT,
    IRR_SCENARIO_ITEMS,
    KEY_CODE,
    KEY_ITEM,
    KEY_NAME,
    KEY_QUARTER,
    KEY_VALUE,
    KEY_VALUE_POST,
    MARKET_BREAKDOWN_EXEMPT,
    MARKET_M,
    R4,
    R7,
    _diversified_sqrt,
    irr_derive_expected,
    irr_pin_verdict,
    run_validation,
)


def _eff_tol(code: str) -> float:
    """룰엔진(적용전)이 쓰는 회사별 기본 허용오차와 동일. 이미지/OCR사만 10.0.
    적용후 검사가 적용전과 **같은 허용오차**를 쓰게 하기 위한 단일 소스 — 적용후 쪽만
    느슨하면 '룰은 돌지만 못 잡는' false-green 이 된다(2026-08-21 실측: 합-항등식 적용후가
    0.5% 였던 탓에 한화손해 2024.2Q item1후 COPY 오염 4.03억을 130배 여유로 통과시켰다)."""
    return IMAGE_OCR_TOLERANCE if code in IMAGE_OCR_COMPANIES else 2.0


def _ratio_tol(code: str, expected: float, denom: float | None) -> float:
    """비율룰(R7/R8) 허용오차 — 룰엔진 rule 7/8 과 동일한 sub-scale 동적식.
    초소형 분모(item14)의 억원 반올림이 재계산 비율을 크게 흔든다(카카오페이 item14후=20억
    → ±120%p). 정상 분모에선 사실상 eff_tol 과 같다. 적용후엔 **적용후 분모**를 넣는다."""
    base = _eff_tol(code)
    if not denom:
        return base
    d = abs(denom)
    return max(base, abs(expected) * 0.5 / d + 50.0 / d)

SPOT_CODE = "KR0005"
SPOT_QUARTER = "2025.4Q"
SPOT_NAME_HINT = "\ud5d5\uad6d\ud654\uc7ac"


def _load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Expected list JSON at {path}")
    return data


def _coverage_census(records: list[dict]) -> dict:
    """Expected (filer x quarter) grid census. A quarter present in the data that
    is missing 'regular filers' (codes seen in >=half of established quarters) goes
    RED — guards against a whole quarter being silently under-parsed (e.g. 2026.1Q
    held only 1 of ~35 filers yet rules emitted no finding → RED=0). Missing-cell is
    a first-class failure, not a SKIP. See memory: coverage-census-mandatory."""
    by_q: dict[str, set] = {}
    code_name: dict[str, str] = {}
    for r in records:
        q = r.get("공시분기")
        c = r.get("원보험사코드")
        if not q or not c:
            continue
        by_q.setdefault(q, set()).add(c)
        code_name[c] = r.get("원수사명", c)
    quarters = sorted(by_q)
    # 'established' history = all but trailing under-filled latest, used to learn the
    # regular-filer set; a code is a regular filer if it appears in >=50% of quarters.
    n_q = len(quarters)
    appears: dict[str, int] = {}
    for q in quarters:
        for c in by_q[q]:
            appears[c] = appears.get(c, 0) + 1
    regular = {c for c, n in appears.items() if n >= max(2, n_q // 2)}
    median_n = sorted(len(by_q[q]) for q in quarters)[len(quarters) // 2] if quarters else 0
    missing_rows = []  # (quarter, code, name)
    for q in quarters:
        present = by_q[q]
        for c in sorted(regular - present):
            missing_rows.append((q, c, code_name.get(c, c)))
    # also flag quarters whose filer count collapsed vs median (gross under-parse)
    collapsed = [
        (q, len(by_q[q])) for q in quarters if len(by_q[q]) < max(3, median_n // 2)
    ]
    return {
        "regular_filers": len(regular),
        "median_filers_per_q": median_n,
        "missing_rows": missing_rows,
        "collapsed_quarters": collapsed,
    }


# 보완자본 한도 3줄(47/48/49) 축 — 룰별 상태 + **결측 사유별 집계**를 인쇄한다.
#
# 왜 따로 인쇄하나: 이 세 항목은 2026-08-21 에 1,299칸 적재됐는데 게이트가 exit 0 이었다.
# 룰이 없어서 조용했던 것이라, 요약 어디에도 "이 축은 아무도 안 본다"가 드러나지 않았다.
# 그래서 ① 축별 상태를 항상 보이게 하고 ② 결측을 **사유별로** 세고(SKIP 을 통과로 읽지 못하게)
# ③ **증거력 없는 축에는 경고를 붙인다**.
#
# ③ 이 핵심이다. `48_tier2_limit`(item48 = item14 × 50%)은 parser 가 스케일 배율을 고를 때
# 쓰는 바로 그 식이라, 여기서 "FAIL: 0" 이 나와도 추출이 옳다는 뜻이 아니다. 숫자 옆에 그
# 사실을 같이 찍지 않으면 다음 사람이 0 을 증거로 읽는다.
_TIER2_AXES = {
    "2_tier1_bridge": "기본자본 다리 item2=item4−(item12−한도초과)−item13, 한도초과≤item12",
    "3_tier2_composition": "보완자본 구성 item3=min(47,48)+49 | =47 | =item13(TFI 미기재)",
    "47_tier2_census": "47/48/49 완전성·부호·자릿수·중복행·전기한도잔존",
    "48_tier2_limit": "한도 item48=item14_적용전×50%",
    # --- TFI 표 자신의 기본자본/보완자본(50/51), 2026-08-22 신설 ---------------
    # 47/48/49 의 부모행이다. 축 B(3_tier2_composition)는 **헤드라인** item3 를 쓰므로
    # 두 표의 스코프가 갈리면 깨지는데(코리안리 원문 확인), 축 F 는 표 안에서만 닫는다.
    "50_tfi_tier_split": "TFI표 tier 분할 item50+item51 (item52 있으면 등식 · 없으면 적용전=item1 폴백/적용후=범위검사)",
    "51_tfi_tier2_composition": "TFI표 안 보완자본 구성 item51 (축B와 같은 갈래, 동일표·동일컬럼)",
}
_TIER2_LOADER_ENFORCED = {"48_tier2_limit"}
_TIER2_POST_UNESTABLISHED = {"2_tier1_bridge", "3_tier2_composition",
                             "51_tfi_tier2_composition"}
# 적용후에 **등식이 아니라 범위검사**가 걸린 축. 등식의 비교 대상(TFI 표 자신의
# 지급여력금액 행 = item52)이 마스터에 없어서다 — 원문(IBK연금 FY2026_Q1 p17)이
# "그 합계 행은 두 컬럼에서 움직인다"를 보였으므로 item1_전·후 어느 쪽으로도 대체할 수 없다.
# YELLOW 는 "약한 검사만 통과" 라는 뜻이고, item52 가 적재되면 등식으로 승격한다.
_TIER2_POST_RANGE_ONLY = {"50_tfi_tier_split"}


def _print_tier2_axis_report(findings: list[dict]) -> None:
    from collections import Counter as _C
    by_rule: dict[str, _C] = {}
    reasons: dict[str, _C] = {}
    clamped: dict[str, int] = {}
    fallback_hits: dict[str, int] = {}
    for f in findings:
        rid = str(f.get("rule"))
        if rid.split("_post")[0] not in _TIER2_AXES:
            continue
        by_rule.setdefault(rid, _C())[f.get("status")] += 1
        if "클램프" in str(f.get("detail", "")):
            clamped[rid] = clamped.get(rid, 0) + 1
        # item52 결측 폴백(범위검사/구 item1 대조)이 **이번 실행에서 실제로 몇 칸을 탔는지**.
        # RED/YELLOW/GREEN 세 상태 다 이 접두어를 쓰므로 상태를 안 가리고 센다 — 아래
        # _TIER2_POST_RANGE_ONLY 노트를 하드코딩 문구가 아니라 이 실측으로 찍기 위해서다
        # (2026-08-25: item52 가 30버킷 더 실려 폴백이 0/450 이 됐는데도 노트가 그대로
        # "결측이라 범위검사"를 인쇄해 orchestrator 티켓 `20260825T0400Z`로 지적됐다).
        if str(f.get("detail", "")).startswith("TFI_TOTAL_ROW_ABSENT"):
            fallback_hits[rid] = fallback_hits.get(rid, 0) + 1
        # 결측·판정불가를 통과로 세지 않으려면 **사유별로** 쪼개야 한다. SKIP 뿐 아니라
        # YELLOW 도 센다 — `47_tier2_census` 의 "적용여부 미확정" 부재가 YELLOW 로 나가는데,
        # 사유 없이 `YELLOW=13` 만 찍히면 그 13칸이 review 인지 약한 통과인지 구분이 안 된다
        # (SKIP 을 갈라 적기 시작한 것과 정확히 같은 이유다, 2026-08-22 iter-5).
        if f.get("status") in ("SKIP", "YELLOW"):
            tag = str(f.get("detail", "")).split(":")[0].strip() or "UNLABELED"
            if f.get("status") == "YELLOW" and not tag.startswith("TIER2_TABLE_ABSENT"):
                continue        # 관계식 미확립 YELLOW 는 축 note 가 이미 설명한다
            reasons.setdefault(rid, _C())[f"{f['status']} {tag}"] += 1
    if not by_rule:
        print("보완자본 한도 축(47/48/49): 룰이 하나도 발화하지 않았다 — 배선 확인 필요")
        return
    print("보완자본 한도 축 (항목 47/48/49):")
    for base, desc in _TIER2_AXES.items():
        for rid in (base, f"{base}_post"):
            c = by_rule.get(rid)
            if not c:
                continue
            col = "적용후" if rid.endswith("_post") else "적용전"
            note = ""
            if base in _TIER2_LOADER_ENFORCED:
                note = "  ※ LOADER_ENFORCED — 로더가 이 식으로 배율을 골랐다. 통과는 증거가 아니다"
            elif rid.endswith("_post") and base in _TIER2_POST_UNESTABLISHED:
                note = "  ※ 적용후 관계식 미확립 → review(YELLOW), blocking 아님"
            elif rid.endswith("_post") and base in _TIER2_POST_RANGE_ONLY:
                hits = fallback_hits.get(rid, 0)
                if hits:
                    note = (f"  ※ {hits}칸은 등식 아님 — item52(TFI표 자신의 지급여력금액 행) "
                            "결측이라 범위검사(폴백). 나머지는 item52 로 등식 검사됨. "
                            "YELLOW = 약한 검사만 통과, parser 발주 대기")
                else:
                    note = ("  ※ item52(TFI표 자신의 지급여력금액 행)가 모든 대상 버킷에 있어 "
                            "전량 등식으로 검사됨 — 범위검사 폴백은 이번 실행 0칸 "
                            "(item52 결측 버킷이 재발하면 자동으로 다시 켜진다)")
            print(f"  [{col}] {desc}")
            print(f"        RED={c['RED']} YELLOW={c['YELLOW']} GREEN={c['GREEN']} "
                  f"SKIP={c['SKIP']}{note}")
            for tag, n in sorted(reasons.get(rid, {}).items(), key=lambda x: -x[1]):
                # 결측을 통과로 세지 않기 위해, 반드시 사유별로 쪼개서 보여준다.
                print(f"          사유 {tag}: {n}")
            # 다리의 item12 상한 클램프가 **몇 칸에서 발동했는지** 항상 인쇄한다.
            # 클램프가 걸린 칸에서는 item12 가 식에서 상쇄돼 그 칸만은 item12 를 못 본다.
            # 조용히 늘어나면 '검사가 줄어드는 것'이므로 숫자를 눈앞에 둔다(2026-08-22 기준 10칸).
            if base == "2_tier1_bridge" and clamped.get(rid):
                print(f"          ※ 한도초과 클램프 발동 {clamped[rid]}칸 "
                      "— 그 칸에서는 item12 가 식에서 상쇄돼 item12 오류를 못 본다")


def _top_offenders(findings: list[dict], status: str, limit: int = 10) -> list[dict]:
    rows = [f for f in findings if f.get("status") == status]
    rows.sort(key=lambda f: abs(float(f.get("diff") or 0.0)), reverse=True)
    return [
        {
            "rule": f.get("rule"),
            "code": f.get(KEY_CODE),
            "quarter": f.get(KEY_QUARTER),
            "diff": f.get("diff"),
        }
        for f in rows[:limit]
    ]


# 19_market source-grounded cadence: 시장위험 세부표(36-40) 5종 라벨이 **분해표 행으로 실재**하는지.
# 2026-06-14 fix: 종전 substring 카운트는 경과조치표의 '주식위험액증가분점진적인식'·산문의 '자산집중위험등'
#  같은 compound/서술 부분문자열을 라벨로 세어 distinct>=3을 거짓충족 → 삼성생명 odd-Q(2023.3Q 등)
#  false RED (parser D 분쟁, raw 확인 결과 분해표 부재 = SKIP 정당). → 번호접두어를 떼어낸 **셀 전체가
#  라벨과 일치**하거나 라벨 직후 숫자가 오는 행만 카운트.
_SUBRISK_LABELS = ["금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액"]
_NUM_PREFIX = re.compile(r"^[\s0-9.\-()ⅠⅡⅢⅣⅤ]*")


def _count_subrisk_rows(text: str) -> int:
    """Distinct 시장위험 5종 라벨이 분해표 '행'으로 실재하는 수.
    경과조치 compound('주식위험액증가분점진적인식')·산문('자산집중위험등')은 제외:
    번호접두어 제거 후 셀==라벨(또는 어간) 또는 라벨 직후 숫자(plain-text 표)만 인정."""
    found: set[str] = set()
    for line in text.splitlines():
        cells = line.split("|") if "|" in line else [line]
        for cell in cells:
            cleaned = _NUM_PREFIX.sub("", cell.strip()).strip()
            for lab in _SUBRISK_LABELS:
                stem = lab[:-1]  # '금리위험액' -> '금리위험'
                if cleaned == lab or cleaned == stem:
                    found.add(lab)
                    break
                if cleaned.startswith(lab) or cleaned.startswith(stem):
                    rest = cleaned[len(lab) if cleaned.startswith(lab) else len(stem):].lstrip()
                    if rest[:1].isdigit():
                        found.add(lab)
                        break
    return len(found)


def _scan_breakdown_presence(records: list[dict]) -> frozenset:
    """(원보험사코드, 공시분기) 중 disclosure MD에 36-40 세부표가 실재하는 셀의 집합.
    item19 공시인데 36-40 결측인 후보 셀만 MD 확인 → 표 있으면 파서갭(RED), 없으면 cadence(SKIP).
    See: 19_market source-grounded cadence fix (2026-06-13)."""
    by_cq: dict[tuple, set] = {}
    for r in records:
        c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        if c and q and it is not None and r.get("값") is not None:
            by_cq.setdefault((c, q), set()).add(it)
    candidates = [
        (c, q) for (c, q), items in by_cq.items()
        if 19 in items and not (set(range(36, 41)) & items)
    ]
    present, cache = set(), {}
    for c, q in candidates:
        fyq = f"FY{q[:4]}_Q{q[5]}"  # 2025.1Q -> FY2025_Q1
        cands = list((ROOT / "data" / "disclosure" / fyq / "parsed").glob(f"*{c}*.md"))
        if not cands:
            continue  # MD 없으면 후속 else 분기에서 RED(보수적) 처리
        p = cands[0]
        if p not in cache:
            try:
                cache[p] = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                cache[p] = ""
        if _count_subrisk_rows(cache[p]) >= 3:
            present.add((c, q))
    return frozenset(present)


def _market_tooling_fail(records: list[dict]) -> list[tuple]:
    """시장위험 페이지 localizer 실패(`market_pages_nonok.json`의 ERR/NO_SIGNAL/TIMEOUT/SCAN) (회사,분기) 중
    *현재도* 분해 갭(item19 공시·36-40 결측)인 셀 = re-localize 후보(TOOLING_FAIL).
    이미 백필된 stale-nonok은 제외(데이터 lag 방지). 추출도구가 죽었는데 게이트가 '미공시(SKIP)'로
    오인하는 SKIP-on-missing 위반을 가시화. 2026-06-14 배선(parser fitz-fallback 안착 → nonok 시맨틱
    안정 후). 게이트 차단은 안 함 — 짝수분기 진짜 갭은 19_market이 이미 RED, 이 목록은 원인 귀속·재로컬 워크리스트."""
    p = ROOT / "artifacts" / "kics_validation" / "market_pages_nonok.json"
    if not p.exists():
        return []
    try:
        nonok = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    by_cq: dict[tuple, set] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        name[c] = r.get("원수사명")
        if c and q and it is not None and r.get("값") is not None:
            by_cq.setdefault((c, q), set()).add(it)
    out = []
    for status, cells in (nonok.items() if isinstance(nonok, dict) else []):
        for cell in cells or []:
            if not (isinstance(cell, (list, tuple)) and len(cell) >= 2):
                continue
            c, q = cell[0], cell[1]
            items = by_cq.get((c, q), set())
            if 19 in items and not (set(range(36, 41)) & items):  # 여전히 갭(백필 안 됨)
                out.append((c, q, status, name.get(c, c)))
    return out


# 부모 위험액 항목 → 그 하위 세부항목 번호. 항목번호는 flat index라 계층은 라벨접두어가 아니라
# 명시 매핑으로 잡는다(라벨 '1.'은 자본tiering·종속회사 네임스페이스에도 출현 → 접두어 매칭 불가).
#   item 17 (1. 생명장기손해보험위험액) -> 29-35 (1-1..1-7)
#   item 19 (3. 시장위험액)            -> 36-40 (3-1..3-5)
_PARENT_CHILD_ITEMS = {17: (29, 30, 31, 32, 33, 34, 35), 19: (36, 37, 38, 39, 40)}


def _parent_zero_child_nonzero(records: list[dict]) -> list[tuple]:
    """부모 위험액 항목이 표에 0으로 존재하는데 하위 세부항목이 비0 = 행 오정렬/셀 밀림.
    구조상 불가능(K-ICS 상관행렬 집계상 분산총액 ≥ 최대 단일세부 → 세부 비0이면 부모도 비0).
    서울보증 25.4Q 생명장기(item17=0) 아래 대재해위험액(item35=5212) 파싱오류를 게이트가 못 잡던
    사각(owner 라이브 QA 3차). 부모 '결측'은 census 소관 → 여기선 부모 present&≈0만 RED."""
    def _num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    by_cq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        name[c] = r.get("원수사명", c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            by_cq.setdefault((c, q), {})[it] = _num(r.get("값"))
    out = []
    for (c, q), items in sorted(by_cq.items()):
        for parent, kids in _PARENT_CHILD_ITEMS.items():
            if parent not in items:
                continue  # 부모 결측 = census 소관, 이 룰 아님
            pv = items[parent]
            if pv is None or abs(pv) >= 1.0:
                continue  # 부모가 present & ≈0 인 경우만
            nz = [(k, items[k]) for k in kids
                  if items.get(k) is not None and abs(items[k]) >= 1.0]
            if nz:
                out.append((c, q, parent, name.get(c, c), nz))
    return out


# 유의미성 하한(억원). 회사유형(생/손보)으로 단정하지 않고 '그 회사'의 실보고값으로만 판단:
# 어떤 자식이 그 회사에서 평소(중앙값) 이 값 미만이면 사실상 0-행으로 보고 특정 분기 결측을
# 실질 갭으로 치지 않는다. 예) 장수위험액(item30)은 손보사라도 실재하면 중앙값이 커져 기대
# 대상이 되고(빠지면 RED), 그 회사가 0으로 보고할 때만 무시된다. 장기간병(item32) 등도 동일.
# 5억: 신한이지 LTC(중앙값 ~1억, 값 0~2억)처럼 상시 미소한 sub-risk의 결측을 RED로 오탐하지
# 않도록(2026-07-05). 실제 misparse 갭들은 median 24억+ 이라 이 하한에 안 걸린다.
_CHILD_MATERIAL_FLOOR = 5.0


def _num_cell(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _parent_present_child_incomplete(records: list[dict]) -> tuple[list, list]:
    """부모 위험액이 present&비0인데, 그 회사가 '평소 유의미하게 보고하던' 하위 세부항목이
    특정 분기만 결측 = 파싱 시 행 누락(docling 표뭉갬). `_parent_zero_child_nonzero`의 역방향
    사각(부모>0·자식결측)을 닫는다(하나손해 KR0050 25.3Q owner 적발, parser blind_spot 20260703).

    자식 '기대'는 회사별 self-census: 그 회사의 부모-present 분기 과반에서 present 이고 중앙값
    ≥ floor(억원)인 자식만 기대 대상 → 구조적 N/A·상시0인 자식은 자동 제외(회사유형이 아니라
    그 회사 실보고값 기준 — 손보사도 장수리스크를 실재로 보고하면 당연히 기대·검출 대상).
    반환: (partial_red, full_absent_even_review)
      - PARTIAL: 같은 부모 밑 자식 일부는 present인데 기대 자식 결측 = 표 실재+행누락 고신뢰 misparse → RED.
      - FULL_ABSENT_EVENQ: 짝수분기에 자식 전부 결측 = cadence/도입초 간이공시 애매 → 원천확인 review(비차단).
    See memory: coverage-census-mandatory."""
    by_cq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            by_cq.setdefault((c, q), {})[it] = _num_cell(r.get(KEY_VALUE))
    # 회사별 부모-present 분기 목록 + 자식 present 값들 → material_expected 산출용
    pq: dict[tuple, list] = {}
    child_vals: dict[tuple, list] = {}
    for (c, q), items in by_cq.items():
        for p, kids in _PARENT_CHILD_ITEMS.items():
            pv = items.get(p)
            if pv is None or abs(pv) < 1.0:
                continue
            pq.setdefault((c, p), []).append(q)
            for k in kids:
                if items.get(k) is not None:
                    child_vals.setdefault((c, p, k), []).append(items[k])

    def material_expected(c: str, p: int) -> set:
        n = len(pq.get((c, p), []))
        if n < 3:
            return set()  # 이력 부족 → 판단 보류
        thr = max(2, (n + 1) // 2)  # 과반
        out = set()
        for k in _PARENT_CHILD_ITEMS[p]:
            vals = child_vals.get((c, p, k), [])
            if len(vals) >= thr and median(abs(v) for v in vals) >= _CHILD_MATERIAL_FLOOR:
                out.add(k)
        return out

    partial, full_absent_even = [], []
    for (c, q), items in sorted(by_cq.items()):
        even_q = len(q) > 5 and q[5] in ("2", "4")
        for p, kids in _PARENT_CHILD_ITEMS.items():
            pv = items.get(p)
            if pv is None or abs(pv) < 1.0:
                continue
            exp = material_expected(c, p)
            if not exp:
                continue
            missing = sorted(k for k in exp if items.get(k) is None)
            if not missing:
                continue
            present_any = any(items.get(k) is not None for k in kids)
            if present_any:
                partial.append((c, q, p, name.get(c, c), tuple(missing)))
            elif even_q:
                full_absent_even.append((c, q, p, name.get(c, c), tuple(missing)))
    return partial, full_absent_even


# 지급여력비율(item27) 시계열 2변 스파이크 파라미터.
_RATIO_SPIKE_ITEM = 27
_RATIO_SPIKE_K = 3.0
_RATIO_SPIKE_FLOOR = 30.0  # %p


def _ratio_series_spikes(records: list[dict]) -> list[tuple]:
    """item27(지급여력비율) 회사별 시계열에서 인접 두 분기 '양쪽 모두'와 크게 벌어진 단일 분기.
    엉뚱한 회사 PDF가 슬롯에 적재돼도 자기정합적이면 산술룰 전부 GREEN 통과하는 사각을 잡는다
    (KR0083 2025.2Q에 KR0075 데이터 → +318%; parser 수정 후 현재 발화 0). 부호역전 자체는
    자본잠식사 정상 0선통과라 flag 안 함 — resid=|x-(prev+next)/2| > max(FLOOR, K·(|prev|+|next|))
    이고 양옆 각각과도 FLOOR 이상 벌어질 때만. YELLOW(비차단, parser 재확인 워크리스트).
    See memory: validation-blind-spots (하한 plausibility)."""
    # 분기별 dedup(last-wins): 삼성생명·메트라이프 등은 item27을 전정밀도+반올림 두 행으로 이중
    # 기재 → 같은 분기가 시계열에 두 번 들어가 이웃 계산이 왜곡되는 것을 막는다(by_cq 관례와 동일).
    series: dict[str, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q and it == _RATIO_SPIKE_ITEM:
            v = _num_cell(r.get(KEY_VALUE))
            if v is not None:
                series.setdefault(c, {})[q] = v
    out = []
    for c, qv in series.items():
        pts = sorted(qv.items())
        for i in range(1, len(pts) - 1):
            qa, a = pts[i - 1]
            qx, x = pts[i]
            qb, b = pts[i + 1]
            resid = abs(x - (a + b) / 2.0)
            thr = max(_RATIO_SPIKE_FLOOR, _RATIO_SPIKE_K * (abs(a) + abs(b)))
            if resid > thr and abs(x - a) > _RATIO_SPIKE_FLOOR and abs(x - b) > _RATIO_SPIKE_FLOOR:
                out.append((c, qx, name.get(c, c), round(x, 2),
                            qa, round(a, 2), qb, round(b, 2)))
    return out


# 경과조치 실효 마진(%p). 적용사 판정 + 적용후 유실 판정 공통. 실제 정상셀은 수십~백%p 차이라
# 이 값은 넉넉하다(복사/반올림 위장은 |diff|<0.1). item27만 방향 불변식이 깨끗(후>전 항상).
_TRANS_EFFECT_MARGIN = 1.0
# 소액/자본잠식 회사(|적용전|이 작음, 예: 예별손해·롯데손해 item28·IBK연금)는 절대마진 1.0pp가
# 상대적으로 과해서 진짜 개선폭(예: 2.09→3.08)까지 COPY로 오탐(2026-07-07, raw 3중검증 후 확정 —
# rule 8_life의 "5% of expected" 동적허용오차와 동일한 발상). |b|가 작을수록 마진도 비례해 줄인다.
_TRANS_EFFECT_MARGIN_PCT = 0.15
_TRANS_EFFECT_MARGIN_FLOOR = 0.1


def _trans_margin(b: float) -> float:
    return max(_TRANS_EFFECT_MARGIN_FLOOR, min(_TRANS_EFFECT_MARGIN, _TRANS_EFFECT_MARGIN_PCT * abs(b)))

# 선택(elective) 경과조치 적용사 18사 — 정본: FSS 2023-03-20 보도자료 붙임-1(원수사별 K-ICS 경과조치
# 신청현황, `trend20230320_3.pdf` p6). 신규보험위험액(TIR: 장수·해지·사업비·대재해)·시가평가 자본감소분
# (TAC) 등 '선택적' 경과조치 신청 19사 중 insurequant 데이터 존재 18사(SCOR재보험은 데이터 부재).
# 나머지는 전부 공통(TFI 등) 경과조치사 = 후=전이어도 정상(flag 안 함).
# 이 18사는 item27(지급여력비율)·item28(기본자본비율) 적용후 > 적용전이어야(선택경과조치 효과).
#   ※ 매핑 주의: 아이엠라이프(KR0076)=구 DGB생명 / 예별손해(KR0004)=구 MG손보 (붙임-1의 사명).
_TRANSITION_APPLIERS = frozenset({
    # 생보 12: 에이비엘·흥국생명·케이디비·교보생명·아이엠라이프(DGB)·DB생명·푸본현대·하나생명·처브·교보라플·IBK연금·농협생명
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    # 손보 6: AXA손해·한화손해·롯데손해·예별손해(MG)·흥국화재·NH농협손해
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})

# 회사별 경과조치 '종류' registry — 정본: FSS 2023-03-20 붙임-1(`trend20230320_3.pdf` p6,
# 좌표추출 총계 검증 4/19/12/8 일치). 각 사가 신청한 경과조치 종류: 'AC'=가용자본(시가평가 자본감소분,
# 4사뿐), 'IR'=요구자본 보험리스크(item17/생명·장기 subrisks, elective 18사 전원), 'EQ'=주식리스크,
# 'INT'=금리리스크(EQ·INT=요구자본 시장위험/item19; 조건부 적용 — K-ICS리스크 60%>RBC일 때만 실발동).
#   ※ UH-5(요구자본 부모 COPY 룰) 종결 근거 (owner 2026-07-21). 실측 78 "부모후=전" 셀 =
#      A(subrisk후≠전인데 부모후=전 모순) 0건 [기존 _transition_mmult_after가 이미 강제] +
#      C 52건 전부 item19(시장위험) 후=전 [주식/금리 미신청사=정당, 신청사도 조건부 미발동 가능] +
#      D 26건 census 소관. 진짜 미검출 0 → 부모 COPY 룰 신설 불요(item17=mmult 중복, item19=오탐 52).
#      headline(item27/28)은 _transition_ratio_after_capture가 18사 전원 검증 중. 소비 룰 없음(문서 registry).
_TRANSITION_KIND = {
    "KR0073": {"IR", "EQ"},              # 교보생명 (장수·해지·사업비·대재해)
    "KR0104": {"IR", "EQ", "INT"},       # 농협생명
    "KR0071": {"IR", "EQ"},              # 흥국생명
    "KR0082": {"IR", "INT"},             # DB생명
    "KR0072": {"AC", "IR", "EQ"},        # 케이디비(KDB)
    "KR1011": {"AC", "IR", "EQ", "INT"}, # IBK연금 (전종)
    "KR0076": {"IR", "EQ"},              # 아이엠라이프(DGB)
    "KR0097": {"AC", "IR", "EQ", "INT"}, # 하나생명 (전종)
    "KR1010": {"IR", "EQ"},              # 교보라이프플래닛
    "KR0070": {"IR", "EQ"},              # 에이비엘(ABL)
    "KR0083": {"AC", "IR", "EQ", "INT"}, # 푸본현대 (전종)
    "KR0100": {"IR"},                    # 처브라이프 (보험리스크만)
    "KR0002": {"IR"},                    # 한화손보 (해지·사업비만) → item19(시장) 후=전 정당
    "KR0003": {"IR"},                    # 롯데손보 (장수·해지·사업비·대재해, 일반손보 제외)
    "KR0005": {"IR", "EQ", "INT"},       # 흥국화재
    "KR0032": {"IR", "INT"},             # NH농협손보
    "KR0004": {"IR", "EQ", "INT"},       # 예별손보(MG)
    "KR0049": {"IR"},                    # AXA(악사) (보험리스크만)
    # SCOR재보험 = {"IR"} (붙임-1), insurequant 데이터 부재로 미등재
}

# 비율항목 → (분자item, 분모item): 적용후 정합(항등식) 검사용. 27=지급여력비율(item1/item14)·
# 28=기본자본비율(item2/item14). item27/28만 패치하고 금액후(1/2/14) 미수정하는 게임을 AMT_MISMATCH로 차단.
_TRANS_RATIOS = {27: (1, 14), 28: (2, 14)}


def _transition_ratio_after_capture(records: list[dict]) -> list[tuple]:
    """선택 경과조치 적용사 18사(owner FSS 정본 확정 2026-07-06)의 item27(지급여력비율)·item28(기본자본비율)
    '적용후' 무결성. 도메인 불변식: 선택 경과조치 적용 시 두 비율 적용후 > 적용전(가용자본↑/요구자본↓
    → 비율↑) — 단 **분자(item1/item2)가 음수인 회사는 예외**: 자본잠식/기본자본결손이 지속되는 채로
    분모(item14)만 줄면 비율은 오히려 더 음수가 커짐(0에서 멀어짐)이 수학적으로 정상(예: 롯데손해·
    케이디비생명·푸본현대·IBK연금 — 2026-07-07 raw 재검증으로 확인, 데이터는 맞는데 "후>전" 가정이
    반대 부호에서 깨지는 걸 잡아냄). 그래서 방향성(LOWER) 체크는 분자가 비음수일 때만 적용한다.
    적용사인데 특정 분기·항목의 적용후가:
      MISSING = None(결측) / COPY = 전과 |diff|<margin(적용전 복사·반올림 위장) /
      LOWER = 분자≥0인데 전보다 낮음(방향위반) /
      AMT_MISMATCH = 후는 margin 넘겼으나 분자후/분모후×100(항등식)과 불일치(비율만 패치·금액후 미수정)
    → RED.

    **명시된 scope 제한(2026-08-21 재확인 — 다른 적용후 룰과 달리 여기는 18사 한정이 정당하다)**:
    이 룰은 '후 > 전'이라는 **방향성** 불변식이고, 그건 선택(elective) 경과조치를 신청한 회사에서만
    성립한다. 공통(TFI) 경과조치만 적용받는 나머지 21사는 후=전이 정상이라 전사로 넓히면 전건 오탐이
    된다. 대신 그 21사의 적용후 비율은 **항등식**(R7/R8후, `_transition_identities_after`)과
    **결측**(`_post_transition_parent_census` 의 item27/28)으로 전사 검사된다 — 즉 방향성만 18사,
    산술·결측은 39사. 조용한 미순회가 아니라 근거 있는 축소다.
    반환 튜플: (code, quarter, name, item, before, after, kind)."""
    idx: dict[tuple, dict] = defaultdict(dict)  # (code, item) -> {q: (before, after)}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q and it in (1, 2, 14, 27, 28):  # 27/28=비율, 1/2/14=금액(항등식 정합용)
            idx[(c, it)][q] = (_num_cell(r.get(KEY_VALUE)), _num_cell(r.get(KEY_VALUE_POST)))
    out = []
    for c in sorted(_TRANSITION_APPLIERS):
        for ratio_it, (num_it, den_it) in _TRANS_RATIOS.items():
            qv = idx.get((c, ratio_it), {})
            qvn, qvd = idx.get((c, num_it), {}), idx.get((c, den_it), {})
            for q, (b, a) in sorted(qv.items()):
                if b is None:
                    continue
                if a is None:
                    out.append((c, q, name.get(c, c), ratio_it, b, None, "MISSING"))
                    continue
                # 금액(분자후/분모후)이 실제로 바뀌었으면 비율변화폭이 작아도 복사가 아니라 진짜 소액개선.
                # 자본잠식사(item28 음수)는 분자·분모가 같이 줄어 비율변화가 작아 margin에 걸리던 오탐 방지
                # (롯데손해 item28 2025.1Q/2Q — item2/14후가 전과 명백히 다름, 2026-07-08).
                nb, na = qvn.get(q, (None, None))
                db, da = qvd.get(q, (None, None))
                amounts_moved = ((nb is not None and na is not None and abs(na - nb) > 1.0)
                                 or (db is not None and da is not None and abs(da - db) > 1.0))
                if abs(a - b) < _trans_margin(b) and not amounts_moved:
                    out.append((c, q, name.get(c, c), ratio_it, b, a, "COPY"))
                    continue
                if b >= 0 and a < b:
                    out.append((c, q, name.get(c, c), ratio_it, b, a, "LOWER"))
                    continue
                an = na
                ad = da
                if an is not None and ad not in (None, 0):
                    derived = an / ad * 100.0
                    if abs(derived - a) > 2.0:
                        out.append((c, q, name.get(c, c), ratio_it, round(derived, 2), a,
                                    "AMT_MISMATCH"))
    return out


def _item12_equals_item1(records: list[dict]) -> list[tuple]:
    """item12(Ⅱ.지급여력금액으로 불인정하는 항목)에 item1(가.지급여력금액)이 그대로 복사된 셀밀림
    파싱오류 = RED. 불인정항목(지급예정 배당 등 소액)이 지급여력금액 전체와 동일할 수 없음(구조상
    불가). 산술룰은 못 잡음 — item1은 별도 공시값이라 정합 유지, item12만 orphan 오염.
    전수검증 2026-07-07 적발(KB손해·하나손해·신한라이프·DB생명·교보라플·DB손해·흥국생명·AIA 16셀)."""
    by_cq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q and it in (1, 12):
            by_cq.setdefault((c, q), {})[it] = _num_cell(r.get(KEY_VALUE))
    out = []
    for (c, q), m in sorted(by_cq.items()):
        v1, v12 = m.get(1), m.get(12)
        if v1 is not None and v12 is not None and abs(v1) > 1.0 and abs(v12 - v1) < 1e-6:
            out.append((c, q, name.get(c, c), v12))
    return out


# 적용후 mmult 축: 부모위험액 → (세부항목, 상관행렬, 가산항목, 허용오차종류).
#   17 = sqrt(29-35·R7)                     ← 룰엔진 8_life    (동적 tol: max(eff, 1%))
#   19 = sqrt(36-40·MARKET_M)               ← 룰엔진 19_market (동적 tol: max(eff, 1%))
# 'dyn5' 라는 이름은 5% 이던 시절의 흔적이다. 실제 배율은 `DIVERSIFIED_SQRT_TOL_REL`
# (2026-08-25 에 5%→1%) 이고, **적용전 룰엔진과 같은 상수를 import 해서 쓴다** —
# 적용후만 느슨하면 룰이 돌아도 안 잡힌다.
#   15 = sqrt([17,18,19,20]·R4) + item21    ← 룰엔진 rule 4    (flat eff_tol)
# **행렬은 전부 룰엔진에서 import** — 손으로 옮기면 검증기가 검증대상과 다른 행렬을 쓰게 된다.
# 축 15(기본요구자본)는 2026-08-21 신설: 그 전까지 `_TRANS_PARENT_SUBS` 가 {17,19} 뿐이라
# **기본요구자본 적용후 항등식이 통째로 미검사**였다(게이트의 '적용후 mmult 불일치: 0' 은
# 거짓말이 아니라 범위 밖이었다 = false-green).
_TRANS_PARENT_SUBS = {
    15: (list(range(17, 21)), R4, 21, "flat"),
    17: (list(range(29, 36)), R7, None, "dyn5"),
    19: (list(range(36, 41)), MARKET_M, None, "dyn5"),
}


# ---------------------------------------------------------------------------
# 부재형 면제 = **셀 단위 부재 박제**. 축을 순회에서 빼지 않는다 (2026-08-24 재설계).
# ---------------------------------------------------------------------------
# **사고 기록: 면제가 축을 눈감겨 틀린 값이 살아남았다.**
# 종전 `_AFTER_SUBRISK_NOT_DISCLOSED` 는 `(회사,분기)` 집합이었고, `_transition_mmult_after` 가
# 부모 조회 **전에** `continue` 했다. 그래서 하나생명 2024.4Q 는 mmult 3축(15·17·19) 전부와
# `_parent_present_child_incomplete_after` · `_diversification_negative` 적용후가 통째로
# 순회 대상이 아니었다. 그 사각 안에서 `item33후`·`item34후` 가 **직전분기 값 복사(stale)** 로
# 앉아 있었고 `item30후`·`item35후` 는 결측이었는데, 어떤 룰도 그 셀을 본 적이 없다.
# 실측 증거(2026-08-24): 그 4셀을 정정 전(942.86/896.15/결측/결측) 값으로 되돌린 마스터 사본으로
# 게이트를 돌려도 출력이 **바이트 동일**했다 — 값이 바뀌어도 게이트가 모른다 = false-green.
#
# **재설계 원칙 — 부재도 박제한다.** 면제는 "이 축을 보지 마라" 가 아니라
# "이 **셀**이 원천에 없다" 는 검증 가능한 명제로만 걸린다:
#   ① 박제된 셀이 **결측이면** → 그 사실을 셀 단위로 세어 인쇄한다(조용한 미순회 금지).
#      그 셀을 입력으로 쓰는 축만 `SOURCE_ABSENT_PINNED` 로 미판정 처리되고, 나머지 축은 그대로 돈다.
#   ② 박제된 셀에 **값이 나타나면** → 면제는 즉시 무효다. 축이 정상적으로 되살아나 검산하고,
#      `EXEMPTION_ABSENCE_PIN_VALUE_PRESENT` review 로 "원장은 부재라는데 값이 있다(=파생값)" 를 인쇄한다.
#   ③ 박제되지 **않은** 셀·축은 면제와 무관하다. 종전엔 하나생명 축 15후가 근거 없이 사각이었다
#      (원문 p281 에 여섯 값이 전부 인쇄돼 있고 실제로 닫힌다 — 실측 diff +0.0043, tol 2.0).
#
# 값은 `(회사, 분기) -> {원천에 적용후 컬럼이 없는 항목번호}`. 원장
# `data/_gold/kics_exemption_provenance.json` 의 `absent_cells` 와 **매 실행 대조**된다
# (`_exemption_pin_ledger_findings`) — 어긋나면 RED.
_AFTER_SOURCE_ABSENT_CELLS: dict[tuple[str, str], frozenset[int]] = {
    # 하나생명 2024.4Q — **claim 은 참, 스코프는 좁힌다.**
    #   · 29~35후(생명장기 7 하위위험) — 원문에 적용후 컬럼이 없다(아래 근거).
    #   · 36~40후(시장 5 하위위험)     — 2026-08-24 재감사가 추가 확인: p301~309 B.2 시장리스크
    #     절에 `경과조치` 0회. 종전엔 이 사실이 원장 어디에도 없이 축 19가 면제되고 있었다.
    #   · 축 15후(= sqrt([17~20]·R4) + item21후)는 **박제하지 않는다** — p281 이 여섯 값을 전부
    #     인쇄하고 산수도 닫힌다. 근거 없이 사각으로 들어가 있던 축이다.
    ("KR0097", "2024.4Q"): frozenset(range(29, 36)) | frozenset(range(36, 41)),
}

# 종전 이름의 호환 껍데기 — **축 제거용으로 쓰지 말 것.** 남겨 둔 이유는 면제 레지스트리
# census(`_exemption_registries`)·원장 대조가 (회사,분기) 키로 돌기 때문이다.
_AFTER_SUBRISK_NOT_DISCLOSED = frozenset(_AFTER_SOURCE_ABSENT_CELLS)

# 원래 등재 근거(그대로 보존):
_AFTER_SUBRISK_NOT_DISCLOSED_NOTES = {
    # 하나생명 2024.4Q — **유지**. 2026-08-21 validation 이 raw 를 열어 재확인했고, 주장이 참이다:
    #   p281 [지급여력기준금액] 은 적용후를 **위험 대분류(17·18·19·20·21)까지만** 공시하고,
    #   생명장기 7 하위위험(29~35)의 적용후 컬럼은 어디에도 없다. p325~327(C.3.1 경과조치 적용내역)은
    #   서술형이라 "최초 산출 금액 + 적용비율 10%" 만 준다(장수 14,325,093 · 해지 66,403,015 ·
    #   사업비 43,877,926 · 대재해 7,847,532 천원). 표준서식 헤딩 2개가 347p 전체에서 부재 —
    #   원장 verify.absent_markers 로 매 실행 기계 재확인된다.
    ("KR0097", "2024.4Q"): "29~35후 원문 부재(p281 은 대분류까지) + 36~40후 부재(B.2 절 경과조치 0회)",
    # ("KR0097", "2026.1Q") 해제 2026-08-21: 등재사유 "적용후 세부 미공시"가 **거짓**이다 —
    #   raw p10 의 [② 장수위험·사업비위험·해지위험 및 대재해위험 경과조치] 표가 적용후 세부를
    #   전부 싣는다(백만원: 사망 38,228 · 장수 - · 장해질병 71,560 · 장기재물 - · 해지 320,365 ·
    #   사업비 103,062 · 대재해 3,430, 생명장기 합계 405,579). 마스터 item29~35후가 이미 이 값과
    #   일치하고 R7 집계도 닫힌다(item17후 4,055.79 vs 4,055.7891, 잔차 +0.0009). 면제로 두면
    #   **실제로 공시됐고 이미 맞게 적재된 값이 영구 미검사**로 남는다.
    # ("KR0104", "2023.1Q") 해제 2026-08-21: 같은 유형. raw p12(②)·p13(③)이 적용후 세부를 전부
    #   싣는다. 등재사유는 "결합공식 불명"인데 그건 `_AFTER_SUBRISK_NOT_DISCLOSED`(=세부 미공시)의
    #   의미가 아니고, 게다가 결합은 지금 풀린다: ②의 생명장기후(897,970) + ③의 시장후(1,813,184)를
    #   함께 적용하면 기본요구자본후 = 39,138.92 − 분산효과후 10,221.92 = 28,917 로 마스터와 일치하고,
    #   item14후 22,802 · item27후 325.5 는 raw p9 [지급여력비율 총괄] 헤드라인과 정확히 같다.
    #   mmult 적용후도 양축 모두 닫힌다(item17후 잔차 +0.0048 · item19후 +0.0009).
    # ("KR0100", "2024.3Q") 해제 2026-08-20 (parser): "②표 값이 행별로 다른 컬럼 착지"는 Docling MD
    #   아티팩트였고 raw PDF는 fitz로 깨끗이 읽힌다(p15-16). 적용후 세부 전량 로드 완료 —
    #   R4(45,312·0·64,131·31,102)+5,563=106,993.75 = 공시 지급여력기준금액후 106,994,
    #   R7(적용후 subs)=45,312 정확. 면제로 두면 이 값들이 mmult 검사에서 영구 skip된다.
    # ("KR0005", "2024.4Q") 해제 2026-08-21: 등재사유 "image-only PDF(텍스트레이어 0)"가 **거짓**이다.
    #   data/disclosure/FY2024_Q4/raw/KR0005_흥국화재.pdf 는 367p / 246,676자(672자/p)이고,
    #   자본적정성 절(p173 "4-6. 자본 적정성 평가")을 240dpi 로 렌더링해 육안 확인한 결과
    #   **이미지 표가 아니라 순수 산문**이다(465자, 선택 가능). 그리고 "경과조치"가 367p 전체에서
    #   0회 — 이 파일은 정기경영공시가 아니라 DART 사업보고서(쪽바닥 "전자공시시스템 dart.fss.or.kr")
    #   이고, p173 다음이 곧바로 "5. 금융자산 및 금융부채"라 K-ICS 수치표 자체가 없다.
    #   docling 파싱 스코프도 p35-37/139-144/172-174(전부 산문)라 이 마스터 값들의 출처가 이 파일이
    #   아님을 확인했다. 면제를 유지하면 mmult19 적용후 실패가 계속 가려진다(아래 RED 참조).
    # ("KR0003", "2026.1Q") 해제 2026-08-21: 등재사유 "②③표 부재(raw 정독 확인)"가 **거짓**이었다 —
    #   raw PDF p24·p25 에 ②③표가 둘 다 있다. docling MD 가 그 페이지를 떨어뜨린 것을 raw 확인으로 적었다.
    #   parser 가 p24 로 item29~35후 7셀을 정정 완료(적대검증 20260821T0400Z ⑥).
    # ("KR0073", "2026.1Q") 해제 2026-08-21: 등재사유 "경과조치 섹션 자체 없음"도 **거짓** —
    #   raw PDF p15 에 ②표 전체가 있다. 같은 docling 페이지 유실. parser 가 p15 로 item29~35 7행 신설
    #   (R7 로 부모값 재현 확인). 면제로 두면 실제 공시된 값이 영구 미검사로 남는다.
}


def _all_missing_are_pinned(subs, m: dict, absent: frozenset, add_item=None) -> bool:
    """이 축의 적용후 입력 중 **결측인 것이 전부** 부재 박제 셀인가.

    하나라도 박제 밖 셀이 결측이면 False — 그건 부재 박제가 아니라 추출갭이다.
    결측이 아예 없으면 False (완비 = 검산 대상이지 미판정이 아니다)."""
    items = list(subs) + ([add_item] if add_item is not None else [])
    missing = [i for i in items if m.get(i, (None, None))[1] is None]
    return bool(missing) and all(i in absent for i in missing)


def _transition_mmult_after(records: list[dict], readability: dict | None = None
                            ) -> tuple[list, list, Counter, list]:
    """'적용후' mmult 정합 3축 — **전사 39사**(owner 2026-07-07/2026-08-21 blind spot).
    룰엔진의 8_life·19_market·rule4 는 적용전(값)만 검사 → 적용후(값_적용후) mmult 미검증.

    **2026-08-21 배선 확대 2건** (그 전까지의 '적용후 mmult 불일치: 0' 은 범위 밖이라 false-green):
      ① `if c not in _TRANSITION_APPLIERS: continue` 제거 → 비-applier 21사(적용후 셀 8,914개,
         적용사 6,089개보다 많다)가 통째로 미검사였다. 공통(TFI)경과조치사는 후=전이 정상이라
         '방향성'룰은 못 걸지만 **항등식은 후에도 그대로 성립해야** 하고, 실제로 그 축에서만
         적용후 오염 3건(신한이지 25.1Q item35후·하나손해 25.2Q item34후·KB라이프 24.2Q item33후)이
         나왔다. 방향성 룰(_transition_ratio_after_capture)만 18사 한정이 정당하다.
      ② 축 15(기본요구자본 = sqrt([17-20]·R4) + item21) 추가 — 종전 {17,19} 뿐이라 미검사.

    허용오차는 **룰엔진 적용전과 동일**(_eff_tol / dyn5) — 적용후만 느슨하면 룰이 돌아도 안 잡힌다.

    **2026-08-21 (b) — '후=전' 버킷을 원천 판독성으로 가른다** (owner 적대적 재검증 ④).
    종전엔 `세부후결측(후=전)` 246칸을 한 덩어리로 세면서 사실상 '구조적으로 정당' 취급했다.
    그 안에 **스캔본이라 애초에 판독 불가능한 셀**이 섞여 있었다(실측 13개 (회사,분기) = 26칸:
    KB손해·미래에셋·동양생명). 판독불가는 "확인했더니 정당"이 아니라 **"확인 자체를 못 함"** 이다 —
    정당 버킷에 섞이면 그 숫자가 곧 false-green 이 된다. 신호는 `data/_derived/kics_source_textlayer.json`
    (raw PDF 텍스트레이어 밀도)에서 온다. docling MD 길이로 대신하지 않는다 — MD 유실을 '원천 부재'로
    오독한 것이 이번에 적발된 면제 2건의 실패 모드다.

    반환 (mismatch, sub_missing, skipped, unverifiable):
      mismatch = 적용후 세부 완비인데 부모후 ≠ 계산값 = RED.
      sub_missing = 부모후 있고 경과조치 효과 有(후≠전)인데 세부후 결측 = 적용후 세부 추출갭(review).
      skipped = 축별 '계산불가/면제' 명시 집계 (조용한 미순회 금지 — 결측을 결함과 섞지 않되 숨기지도 않는다).
      unverifiable = '후=전' 인데 원천이 판독불가/경계/미측정이라 **정당하다고 말할 수 없는** 셀."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))
    if readability is None:
        readability = _source_readability()
    mismatch, sub_missing, unverifiable = [], [], []
    skipped: Counter = Counter()
    for (c, q), m in sorted(byq.items()):
        absent = _AFTER_SOURCE_ABSENT_CELLS.get((c, q), frozenset())
        for parent, (subs, mat, add_item, tol_kind) in _TRANS_PARENT_SUBS.items():
            pre_p, post_p = m.get(parent, (None, None))
            if post_p is None:
                skipped[f"item{parent}:부모후결측"] += 1
                continue  # 부모후 없음 = 별개 갭(post_transition_parent_census 소관)
            post_subs = [m.get(i, (None, None))[1] for i in subs]
            add_post = m.get(add_item, (None, None))[1] if add_item else 0.0
            if all(v is not None for v in post_subs) and add_post is not None:
                # **면제가 있어도 값이 완비되면 검산한다.** 부재 박제는 "원천에 없다" 는 명제이지
                # "검사하지 마라" 가 아니다 — 값이 나타나면 그 명제가 깨진 것이고 축은 되살아난다.
                exp = _diversified_sqrt(np.array(post_subs, dtype=float), mat) + add_post
                tol = (_eff_tol(c) if tol_kind == "flat"
                       else max(_eff_tol(c), DIVERSIFIED_SQRT_TOL_REL * abs(exp)))
                if abs(post_p - exp) > tol:
                    mismatch.append((c, q, name.get(c, c), parent, round(post_p, 1), round(exp, 1)))
            elif _all_missing_are_pinned(subs, m, absent, add_item):
                # 결측 셀이 **전부** 박제된 부재 셀 → 이 축만 미판정. 셀 번호를 세어 인쇄한다
                # (조용한 미순회 금지). 박제 밖 셀이 하나라도 섞이면 아래 추출갭 갈래로 내려간다.
                miss = [i for i in list(subs) + ([add_item] if add_item else [])
                        if m.get(i, (None, None))[1] is None]
                skipped[f"item{parent}:SOURCE_ABSENT_PINNED({','.join(str(i) + '후' for i in miss)})"] += 1
            elif pre_p is not None and abs(post_p - pre_p) > 1.0:
                sub_missing.append((c, q, name.get(c, c), parent))
                skipped[f"item{parent}:세부후결측(추출갭)"] += 1
            else:
                tag = readability.get((c, q), "UNMEASURED")
                if tag == "READABLE":
                    skipped[f"item{parent}:세부후결측(후=전)·원천판독가능"] += 1
                else:
                    skipped[f"item{parent}:세부후결측(후=전)·원천{tag}(판정불가)"] += 1
                    unverifiable.append((c, q, name.get(c, c), parent, tag))
    return mismatch, sub_missing, skipped, unverifiable


# 적용후 항등식 배터리 (owner 2026-07-07: "모든 룰은 적용전·적용후 동일 적용"). 적용사, genuine 적용후
# 입력(값_적용후)이 완비된 셀만 검산 — 안 닫히면 RED. R1=가용자본(item1)=기본자본(item2)+보완자본(item3).
_TRANS_AFTER_IDENT = [
    ("R1_가용자본=기본+보완", 1, (2, 3), lambda v: v[2] + v[3], False),
    ("R2_순자산합", 4, (5, 6, 7, 8, 9, 10, 11), lambda v: sum(v[i] for i in (5, 6, 7, 8, 9, 10, 11)), False),
    ("R5_기준금액", 14, (15, 22, 23), lambda v: v[15] - v[22] + v[23], False),
    ("R6_item16", 16, (17, 18, 19, 20, 21, 15), lambda v: sum(v[i] for i in (17, 18, 19, 20, 21)) - v[15], False),
    ("R7_지급여력비율", 27, (1, 14), lambda v: (v[1] / v[14] * 100) if v[14] else None, True),
    ("R8_기본자본비율", 28, (2, 14), lambda v: (v[2] / v[14] * 100) if v[14] else None, True),
]


def _transition_identities_after(records: list[dict]) -> tuple[list, Counter]:
    """'적용후' 항등식 정합 R1/R2/R5/R6/R7/R8 — **전사 39사** (owner 2026-07-07 blind spot).
    룰엔진의 R1~R8 은 적용전만 검사 → 적용후(값_적용후)는 미검증이었음.

    **2026-08-21 수정 2건** (둘 다 '룰은 돌지만 못 잡는' 유형):
      ① 적용사 18사 한정 제거 → 전사 39사. 비-applier 도 후=전 항등식은 그대로 성립해야 한다.
      ② **허용오차를 룰엔진(적용전)과 일치**시켰다. 종전 합-항등식 `max(2.0, 0.5%)` 는 적용전
         (flat 2.0)보다 최대 130배 느슨해서 한화손해 2024.2Q item1후=53,541(= 적용전 복사;
         raw 적용후는 5,353,772백만 = 53,537.7)의 4.03억 오염을 통과시켰다. 비율룰도 종전
         flat 2.0 → 룰엔진과 같은 sub-scale 동적식으로 바꿨다(카카오페이 micro 반올림 3건이
         적용전에선 GREEN 인데 적용후에서만 RED 로 뜨던 비대칭 제거).

    genuine 적용후 입력 완비 셀만 판정 — 결측은 결함과 섞지 않되 `skipped` 로 명시 집계한다.
    반환: (fails, skipped). fails = (code, quarter, name, rule, expected_after, disclosed_after, diff)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = _num(r.get(KEY_VALUE_POST))
    fails = []
    skipped: Counter = Counter()
    for (c, q), m in sorted(byq.items()):
        for rule, tgt, ins, fn, is_ratio in _TRANS_AFTER_IDENT:
            tv = m.get(tgt)
            if tv is None or any(m.get(i) is None for i in ins):
                skipped[f"{rule}:적용후입력결측"] += 1
                continue  # genuine 적용후 입력 완비 셀만 (결측은 추출갭 = 별도 리포트)
            exp = fn(m)
            if exp is None:
                skipped[f"{rule}:분모0"] += 1
                continue
            tol = _ratio_tol(c, exp, m.get(14)) if is_ratio else _eff_tol(c)
            if abs(exp - tv) > tol:
                fails.append((c, q, name.get(c, c), rule, round(exp, 2), round(tv, 2), round(tv - exp, 2)))
    return fails, skipped


# 36_irr 축의 항목 집합 — 단일 소스. `_transition_irr_after` 와 축 평가율 census 가 같은 것을 본다.
#   41=충격 전 순자산 · 42=평균회귀 · 43=금리상승 · 44=금리하락 · 45=평탄 · 46=경사
# **룰엔진에서 import** 한다(재타이핑 금지 — 게이트가 룰과 다른 항목집합을 보게 된다).
_IRR_SCENARIO_ITEMS = IRR_SCENARIO_ITEMS
_IRR_ALL_ITEMS = (36,) + _IRR_SCENARIO_ITEMS


def _transition_irr_after(records: list[dict]) -> tuple[list, Counter]:
    """36_irr(금리위험액 = 충격시나리오별 순자산가치에서 도출)의 '적용후' 검사 — **전사 39사**.
    2026-08-21 신설: 룰엔진 36_irr 은 적용전만 돌고 적용후 배선이 **아예 없었다**(R4 축과 함께
    '미배선 2건' 중 하나). 공식·면제목록은 전부 룰엔진에서 그대로 쓴다(재구현 금지):
        item36 = sqrt(max(R상승,R하락)² + max(R평탄,R경사)²) + R평균회귀,  R = item41 − 시나리오
    허용오차도 룰엔진과 동일 max(eff_tol, 5%).

    **결측을 RED 로 올리지 않는 이유(명시 skip)**: 41-46 적용후는 실측 103셀뿐이고 그 103셀은
    **전부 적용전과 값이 동일**(차 0건). 즉 원천에 시나리오표의 적용전/후 구분이 있는지 자체가
    미확인이라, 결측 114셀(짝수Q·적용전완비·적용후결측, 대부분 경과조치 적용사)을 RED 로 걸면
    근거 없이 push 를 막는다. → `POST_SCENARIO_ABSENT` 로 **세어서 보고**하고 원천 판정은
    parser 레인에 발주한다(조용한 미순회 금지, 그러나 미확인 결측을 결함으로 세지도 않는다).
    반환: (fails, skipped)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))
    irr_items = _IRR_ALL_ITEMS
    fails, skipped = [], Counter()
    for (c, q), m in sorted(byq.items()):
        post = {i: m.get(i, (None, None))[1] for i in irr_items}
        pre = {i: m.get(i, (None, None))[0] for i in irr_items}
        if (c, q) in INTERNAL_MODEL_36IRR_EXEMPT:
            skipped["INTERNAL_MODEL_EXEMPT"] += 1
            continue
        if (c, q) in IRR_SCENARIO_EXEMPT:
            skipped["IRR_SCENARIO_EXEMPT"] += 1
            continue
        # documented exception (owner 2026-08-21) — **적용후도 따로 박제한다.** 적용전만 면제하면
        # 이 축이 그대로 막는다(KR0079 8_life 전례). 박제잔차는 이 컬럼에서 재계산해 대조하고,
        # 이탈·결측은 SKIP 이 아니라 fails(=RED) 로 내려보낸다.
        pv, pinned, actual = irr_pin_verdict(c, q, "적용후", post)
        if pv == "MATCH":
            skipped["DOCUMENTED_EXEMPT_PINNED(적용후 잔차 박제 일치)"] += 1
            continue
        if pv == "DRIFT":
            skipped["IRR_EXEMPTION_RESIDUAL_DRIFT(면제 무효 → RED)"] += 1
            fails.append((c, q, name.get(c, c), round(post[36], 2),
                          round(irr_derive_expected(post), 2)))
            continue
        if pv == "INPUT_MISSING":
            skipped["IRR_EXEMPTION_INPUT_MISSING(면제 확인불가 → RED)"] += 1
            fails.append((c, q, name.get(c, c), post.get(36), None))
            continue
        if all(post.get(i) is not None for i in irr_items):
            exp = irr_derive_expected(post)
            if abs(post[36] - exp) > max(_eff_tol(c), IRR_DERIVED_TOL_REL * abs(exp)):
                fails.append((c, q, name.get(c, c), round(post[36], 2), round(exp, 2)))
        elif post.get(36) is None:
            skipped["부모(item36)후_결측"] += 1
        elif not q.endswith(("2Q", "4Q")):
            skipped["홀수분기_시나리오표_서식부재"] += 1
        elif all(pre.get(i) is not None for i in irr_items):
            skipped["POST_SCENARIO_ABSENT(짝수Q·적용전완비)"] += 1
        else:
            skipped["적용전도_시나리오_불완전"] += 1
    return fails, skipped


# ===========================================================================
# item23(기타 요구자본) = item24 + item25 + item26 — **적용전·적용후 양 컬럼**
# ---------------------------------------------------------------------------
# 배경(티켓 inbox/validation/20260821T1100Z): 룰엔진이 실제로 소비하는 항목집합을 마스터 46개
# 항목과 대조하니 **12·13·24·25·26 을 어떤 항등식도 참조하지 않았다**(적용전 2,254셀 +
# 적용후 1,111셀). 셀이 존재하므로 census 는 통과하고, 값은 아무도 안 본다 — 이 저장소가
# '맞는 산수·틀린 소스'로 두 달 데인 바로 그 유형이다. 24/25/26 을 잡아 주는 다리가 이 합계
# 하나뿐이라 먼저 건다(12·13 은 item2 다리 조사 중, 같은 티켓 ②).
#
# 이 항등식의 근거는 파생 가설이 아니라 **원문 행 라벨 자체**다: `Ⅲ. 기타 요구자본(1+2+3)`.
# 공시가 선언한 합이라 구조적으로 오탐 여지가 없다. 실측(2026-08-21, 라이브 마스터):
# 적용전 401검사/400통과/불일치 1 · 적용후 203검사/203통과/불일치 0.
#
# 검출 1건 = 흥국생명 KR0071 2023.3Q item24=8,313(날조). raw
# `data/disclosure/FY2023_Q3/raw/KR0071_흥국생명보험.pdf` p11 은 1번 행이 `-`, 3번 행만 8,313
# 이다(fitz 로 직접 확인). 같은 `-` 인 2번 행은 0 으로 들어갔으니 **같은 기호를 두 가지로 읽은**
# 파서 dash 처리 버그다. 이 오류를 잡는 검사가 지금까지 하나도 없었다.
_OTHER_CAPITAL_PARENT = 23
_OTHER_CAPITAL_CHILDREN = (24, 25, 26)


def _other_capital_children_sum(records: list[dict]) -> tuple[list, Counter]:
    """`item23 = item24 + item25 + item26` (기타 요구자본 = 종속회사 환산치 + 비례성원칙 대응치
    + 관계회사 환산치) 를 **적용전(값)·적용후(값_적용후) 양쪽**에서 검산한다. RED(blocking).

    허용오차는 룰엔진(적용전)과 동일한 `_eff_tol` — 적용후만 느슨하면 '룰은 돌지만 못 잡는'
    false-green 이 된다(2026-08-21 한화손해 item1후 사례).

    **결측은 결함으로 세지 않는다**(이 저장소 원칙: 결측과 결함을 섞지 말 것). 다만 조용히
    넘기지도 않는다 — `skipped` 로 사유별 명시 집계하고, 그중 `부모>0·자식전부결측` 은
    '값은 있는데 분해가 통째로 없는' 추출갭 후보라 따로 센다.
    반환: (fails, skipped). fails = (code, quarter, name, column, disclosed, expected, kids)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))
    fails: list[tuple] = []
    skipped: Counter = Counter()
    for (c, q), m in sorted(byq.items()):
        for col, idx in (("적용전", 0), ("적용후", 1)):
            tgt = m.get(_OTHER_CAPITAL_PARENT, (None, None))[idx]
            kids = [m.get(i, (None, None))[idx] for i in _OTHER_CAPITAL_CHILDREN]
            if tgt is None:
                skipped[f"{col}:부모(item23)결측"] += 1
                continue
            if any(k is None for k in kids):
                if all(k is None for k in kids):
                    # 부모가 material 한데 분해가 통째로 없으면 '미공시'가 아니라 추출갭 후보.
                    tag = "자식전부결측·부모>0(추출갭 후보)" if abs(tgt) >= 1.0 else "자식전부결측·부모≈0"
                else:
                    tag = "자식일부결측"
                skipped[f"{col}:{tag}"] += 1
                continue
            exp = sum(kids)
            if abs(exp - tgt) > _eff_tol(c):
                fails.append((c, q, name.get(c, c), col, round(tgt, 2), round(exp, 2),
                              tuple(round(k, 2) for k in kids)))
    return fails, skipped


# ===========================================================================
# 메타룰 — "룰이 돌았다"와 "룰이 판정했다"를 분리한다 (owner 2026-08-21 적대적 재검증)
# ---------------------------------------------------------------------------
# 배경: 어느 축도 '평가율'을 방출하지 않아서, 그리드의 21%만 판정하는 축이 `FAIL: 0` 한 줄로
# 통과처럼 읽혔다. 게다가 36_irr 적용후는 그 21% 조차 **값_적용후가 적용전과 전부 동일**해서
# 자기 자신과 비교하는 동어반복이었다(원천 시나리오표에 경과조치 전/후 축이 아예 없다).
# 그래서 두 가지를 1급 finding 으로 방출한다:
#   ① 평가율(evaluated / grid)  ② 자기미러(적용후 입력이 적용전과 수치 동일 = 정보량 0)
# 그리고 판정의 기준은 평가율이 아니라 **실질 평가율(평가 − 미러)** 이다.
# ===========================================================================

# 그리드 하한. 평가'율'은 모수가 몇 칸뿐이면 의미가 없다 — 실데이터 축의 그리드는 180~486 이라
# 이 하한에 걸리지 않고, 합성 selftest 픽스처(최대 12버킷)만 걸러진다.
_AXIS_MIN_GRID = 20
# 리뷰 임계. 데이터 임계가 아니라 **의사소통 임계**다: 그리드의 절반도 판정 못 하는 축의
# "FAIL 0" 은 소수파를 요약한 문장이라, 정보보다 오해를 더 많이 준다. 0% 는 아래에서 별도 RED.
_AXIS_EVAL_RATE_FLOOR = 0.50


def _axis_specs() -> list[tuple]:
    """축 정의 = (axis_id, target_item, input_items, exempt_set, 설명).

    **전부 기존 상수에서 파생한다** — 항목번호도 상관행렬도 여기서 다시 타이핑하지 않는다.
    재타이핑하면 평가율 측정기가 실제 룰과 다른 축을 재게 되고, 그때부터 이 메타룰 자신이
    false-green 의 원천이 된다."""
    specs: list[tuple] = []
    for parent, (subs, _mat, add_item, _tol) in sorted(_TRANS_PARENT_SUBS.items()):
        ins = list(subs) + ([add_item] if add_item is not None else [])
        # 면제 집합도 **축별**로 좁힌다(2026-08-24). 종전엔 (회사,분기) 통째 집합이라 축 15 처럼
        # 부재 박제가 하나도 없는 축까지 분모에서 빠졌다 — 평가율 측정기가 실제 룰과 다른 축을 잰다.
        ex = frozenset((c, q) for (c, q), cells in _AFTER_SOURCE_ABSENT_CELLS.items()
                       if cells & set(ins))
        specs.append((f"mmult{parent}", parent, ins, ex,
                      f"item{parent} = sqrt(세부·상관행렬)"))
    for rule, tgt, ins, _fn, _is_ratio in _TRANS_AFTER_IDENT:
        specs.append((rule, tgt, list(ins), frozenset(), f"item{tgt} 항등식"))
    specs.append(("36_irr", 36, list(_IRR_SCENARIO_ITEMS),
                  INTERNAL_MODEL_36IRR_EXEMPT | IRR_SCENARIO_EXEMPT,
                  "item36 = 시나리오 순자산(41-46) 도출"))
    return specs


# 축 → **그 축을 실제로 움직이는 경과조치 종류**. `_TRANSITION_KIND`(FSS 2023-03-20 붙임-1 정본)와 짝.
# 자기미러(값_적용후 == 값)의 의미가 회사마다 다르기 때문에 필요하다:
#   · 비적용사        → 후 = 전이 **정의상 참**. 조작이 아니라 그게 정답이다. 결함이 아니다.
#   · 적용사인데 그 종류를 **안 신청**했다 → 그 축은 안 움직이는 게 정상. 결함이 아니다.
#     (실측 2026-08-21: R1 적용후 미러 82건이 전부 여기 — 10사 모두 'AC' 미신청. 종류 게이팅 없이
#      "적용사 미러 = 오염"으로 걸었으면 82건 전건 오탐이었다.)
#   · 적용사이고 그 종류를 **신청**했는데 후 = 전 → 그때만 미러링 오염 의심.
# None = 그 축에 대해 '움직여야 한다'를 단정할 수 없음 → **카운트만 하고 발화하지 않는다**:
#   · EQ·INT 는 **조건부 발동**(K-ICS리스크 60%>RBC 일 때만) → 신청사여도 후=전이 정당할 수 있다.
#     owner 가 UH-5(2026-07-21)에서 정확히 이 이유로 item19 COPY 룰 신설을 기각했다(오탐 52건).
#   · 15/14/16/27/28 은 하류 집계축이라 어느 종류든 흘러들어와 단일 매핑이 불가능하다.
_AXIS_TRANSITION_KIND: dict[str, set | None] = {
    "R1_가용자본=기본+보완": {"AC"},   # 가용자본(시가평가 자본감소분 점진적 인식) — 조건부 아님
    "R2_순자산합": {"AC"},            # 순자산 세부도 가용자본측
    "mmult17": {"IR"},               # 신규 보험위험(장수·해지·사업비·대재해) — 적용사 전원, 조건부 아님
    "mmult19": None,                 # EQ·INT 조건부 → 발화 금지(UH-5)
    "36_irr": None,                  # INT 조건부 → 발화 금지
    "mmult15": None, "R5_기준금액": None, "R6_item16": None,
    "R7_지급여력비율": None, "R8_기본자본비율": None,
}


# ---------------------------------------------------------------------------
# 축 적용범위(scope) — `rate_all` 의 분모를 **구조**로 제한한다 (owner 2026-08-21).
# ---------------------------------------------------------------------------
# 배경: `36_irr`·`R2 적용후` 세 축이 절대 해소될 수 없는 AXIS_EVAL_RATE_LOW 를 매 실행 찍고
# 있었다. 영구 미해소 review 는 review 가 없는 것보다 나쁘다 — 사람들이 그 블록을 넘겨 읽는
# 습관을 들이기 때문이다. 원인은 임계가 아니라 **분모**였다: 반기공시 항목을 전 분기로 나누고,
# 경과조치 표가 재작성하지 않는 블록을 전 회사로 나누고 있었다.
#
# ⚠️ scope 는 **구조(분기 주기 · 경과조치 적용여부)에서만** 나온다. "값이 있는 버킷" 으로 정하면
# 추출갭이 분모에서 같이 사라져 지표가 저절로 좋아진다 — 이 파일이 두 분모를 두는 이유가 바로
# 그 함정이고, scope 를 데이터로 정하면 그 함정을 분모 안으로 다시 들여오는 셈이다.
# 그래서 범위 안인데 평가 안 된 칸은 `scope_missing` 으로 **이름을 붙여 인쇄한다.**
#
# 실측 근거 (validation 2026-08-21, 라이브 마스터 488버킷 · 39사 · 적용사 18 / 비적용사 21):
#   · cadence — 항목 41-46(금리위험 시나리오 순자산가치) 적용전 보유 버킷:
#     짝수분기 220/226, **홀수분기 0/262**(2023.1Q·3Q · 2024.1Q·3Q · 2025.1Q·3Q · 2026.1Q 전부 0).
#     원천에서도 확인됨(orchestrator 가 6사 × 2024.4Q~2026.1Q 라벨 스캔). 룰엔진이 이미 같은
#     주기를 쓴다(`is_even_q` → 홀수분기 결측은 SKIP, 짝수분기 결측은 RED).
#   · applier — 적용후 보유 여부가 경과조치 적용사/비적용사로 **완전히 갈린다**:
#     items 5-11  적용사 0/18 보유 · 비적용사 21/21 보유
#     items 41-46 적용사 0/18 보유 · 비적용사 21/21 보유
#     구조적 이유: [지급여력비율의 경과조치 적용에 관한 사항] ①②③ 표는 지급여력금액·기본자본·
#     보완자본·지급여력기준금액·기본요구자본과 위험액 legs 를 재작성하지만 **순자산 6구성
#     (보통주·자본증권·이익잉여금·자본조정·기타포괄손익·비지배지분)은 재작성하지 않고**
#     (하나생명 2026.1Q raw p10-11 · 농협생명 2023.1Q raw p11-13 직접 확인),
#     [② 금리위험액 현황] 표의 열 축은 충격 전/충격후 5시나리오뿐이라 **경과조치 축이 아예 없다**
#     (교보 2025.2Q p21 · 신한라이프 p22/p28/p131/p144 직접 확인).
#     따라서 적용사에게 이 두 블록의 적용후가 없는 것은 결함이 아니라 서식의 귀결이고,
#     비적용사는 후=전 미러라 값이 존재한다.
#     (orchestrator 가 보고한 예외 하나 — 하나생명 2024.2Q item41-46후 — 는 parser 가 이미
#      null 처리해 현재 적용사 × 41-46후 보유 셀은 **0건**이다. 재측정으로 확인.)
_AXIS_EVEN_QUARTER_ONLY = frozenset({"36_irr"})
_AXIS_POST_NONAPPLIER_ONLY = frozenset({"36_irr", "R2_순자산합"})


def _axis_scope(axis: str, column: str, all_cq) -> set:
    """그 축이 **구조적으로 적용되는** (회사,분기) 집합. 값 유무는 보지 않는다."""
    scope = set(all_cq)
    if axis in _AXIS_EVEN_QUARTER_ONLY:
        scope = {(c, q) for (c, q) in scope if q.endswith(("2Q", "4Q"))}
    if column == "적용후" and axis in _AXIS_POST_NONAPPLIER_ONLY:
        scope = {(c, q) for (c, q) in scope if c not in _TRANSITION_APPLIERS}
    return scope


def _axis_evaluation_census(records: list[dict]) -> list[dict]:
    """축 × 컬럼(적용전/적용후) 별 평가율 + 자기미러 3분류.

    **2026-08-21 (f) 정정 — 미러를 한 덩어리로 세던 게 틀렸다.** 처음 배선에서 "적용후 입력이
    적용전과 전부 동일 = 정보량 0" 이라 보고 전부 실질평가에서 뺐는데, **비적용사에게 후 = 전은
    정의상 참**이다. 조작된 값이 아니라 유일하게 가능한 값이고, 그 셀을 검사한 건 헛일이 아니라
    맞는 값을 확인한 것이다. 그걸 빼버리니 `36_irr 적용후`·`R2 적용후` 가 실질 0칸이 되어
    **정의를 결함으로 뒤집어 읽었다**(owner 지적). 미러는 이제 셋으로 나눈다:
      · `mirror_nonapplier`     비적용사 — **정의상 동일**. 평가로 인정한다.
      · `mirror_applier_legit`  적용사인데 그 축을 움직이는 종류를 미신청 — 정상. 평가로 인정한다.
      · `mirror_applier_suspect` 적용사 + 해당 종류 신청 + 후 = 전 → **미러링 오염 의심**(발화 대상).
    실질평가(effective) = evaluated − suspect. 즉 "동어반복" 판정은 **적용사 오염에만** 쓴다.

    나머지 용어
    - grid       = 그 축이 '적용되는' (회사,분기) = 적용전 컬럼에 **대상항목 + 입력 최소 1개**가
                   실재하는 버킷. 회사유형으로 단정하지 않고 그 회사의 실보고값으로만 정한다
                   (memory: no-category-assumptions). 면제 등재분은 grid 에 남기되 평가에서 뺀다 —
                   면제도 '판정 안 한 칸'이므로 분모에서 지워버리면 면제가 평가율을 올려준다.
    - buckets    = 그 축이 **구조적으로 적용되는** (회사,분기) = `_axis_scope`. grid 만 보면
                   **함정**이 있다: 추출갭으로 입력이 통째로 사라지면 grid 가 같이 줄어 평가율이
                   오히려 좋아진다(= '데이터가 사라질수록 지표가 개선'되는 census 룰 고질병의
                   거울상). 그래서 두 분모를 **둘 다** 재고 둘 중 하나라도 바닥을 뚫으면 review.
                   **2026-08-21 정정**: 종전에는 이것이 무조건 '전체 버킷'이었는데, 반기공시 항목
                   (41-46)을 홀수분기로도 나누고 경과조치 표가 재작성하지 않는 블록을 적용사로도
                   나누고 있어서 세 축이 **영원히 해소 불가능한 review** 를 찍었다. 영구 미해소
                   review 는 사람들에게 그 블록을 건너뛰는 습관을 준다. 분모를 구조로 좁히되
                   **좁힌 범위 안에서 평가 안 된 칸은 `scope_missing` 으로 이름을 붙여 인쇄**한다 —
                   범위 제한이 갭을 흡수해 숨기는 일은 없어야 한다.
    - buckets_all= 참고용 전체 (회사,분기). scope 가 얼마나 좁혀졌는지 보이기 위해 같이 싣는다.
    - evaluated  = 그 컬럼에서 대상+전 입력이 present → 실제로 비교가 돌아간 버킷.
    - independent = evaluated − 정의상/정상 미러. "후가 전과 달라질 수 있는 칸 중 판정한 수" —
                   보고용 보조지표이고 **판정에는 쓰지 않는다**(비적용사 미러는 결함이 아니다).
    """
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))

    out: list[dict] = []
    for axis, tgt, ins, exempt_set, desc in _axis_specs():
        items = [tgt] + list(ins)
        kinds = _AXIS_TRANSITION_KIND.get(axis)
        grid_cells = [(c, q) for (c, q), m in byq.items()
                      if m.get(tgt, (None, None))[0] is not None
                      and any(m.get(x, (None, None))[0] is not None for x in ins)]
        for column, i in (("적용전", 0), ("적용후", 1)):
            scope = _axis_scope(axis, column, byq)
            # grid 도 같은 범위로 자른다. grid_cells 는 **적용전** 존재로 정의되므로, 적용후
            # 컬럼에서는 "경과조치 표가 재작성하지 않아 구조적으로 적용후가 없는" 적용사 버킷까지
            # 분모에 들어가 있었다 — 그래서 36_irr·R2 적용후가 분모만 바꿔서는 안 풀리고
            # grid 쪽 바닥을 계속 뚫었다. 두 분모는 여전히 서로 다른 것을 잰다:
            #   grid  = 범위 안에서 **입력이 실재하는** 버킷 (데이터 의존 — 추출갭이 나면 줄어든다)
            #   범위  = 구조적으로 적용되는 버킷 (데이터 무관 — 줄지 않는다)
            # 둘의 차이가 곧 추출갭이고, 36_irr 적용전이 220/226 으로 그 6건을 그대로 보여 준다.
            col_grid = [cq for cq in grid_cells if cq in scope]
            ev = exempt = 0
            mir_non = mir_legit = 0
            suspect_cells, mirror_cells, exempt_cells, eval_cells = [], [], [], []
            for (c, q) in col_grid:
                m = byq[(c, q)]
                if (c, q) in exempt_set:
                    exempt += 1
                    exempt_cells.append((c, q))
                    continue  # documented exception 도 '판정 안 한 칸' — 분모에 남긴다
                if any(m.get(x, (None, None))[i] is None for x in items):
                    continue
                ev += 1
                eval_cells.append((c, q))
                if column != "적용후":
                    continue
                if not all(m.get(x, (None, None))[0] is not None
                           and m.get(x, (None, None))[0] == m.get(x, (None, None))[1]
                           for x in items):
                    continue
                mirror_cells.append((c, q))
                if c not in _TRANSITION_APPLIERS:
                    mir_non += 1                      # 비적용사 → 후=전은 정의상 참
                elif kinds is None or not (kinds & _TRANSITION_KIND.get(c, set())):
                    mir_legit += 1                    # 그 축을 움직이는 종류 미신청/조건부 → 정상
                else:
                    suspect_cells.append((c, q))      # 신청했는데 후=전 → 오염 의심
            grid = len(col_grid)
            suspect = len(suspect_cells)
            eff = ev - suspect
            indep = ev - mir_non - mir_legit - suspect
            # 범위 안인데 평가되지 않은 칸 = **진짜 잔여 갭**. scope 로 분모를 줄이면 이것들이
            # 분모에서 사라지지 않고 이름으로 남아야 한다 — 그러라고 scope 를 구조로만 정했다.
            scope_missing = sorted(scope - set(eval_cells) - set(exempt_cells))
            out.append({
                "axis": axis, "column": column, "desc": desc, "grid": grid,
                "buckets": len(scope), "buckets_all": len(byq),
                "scope_missing": scope_missing[:60],
                "scope_missing_n": len(scope_missing),
                "scoped": len(scope) != len(byq),
                "evaluated": ev, "exempt": exempt,
                "mirrored": len(mirror_cells),
                "mirror_nonapplier": mir_non,          # 미적용사_정의상_동일
                "mirror_applier_legit": mir_legit,     # 적용사_해당종류_미신청(또는 조건부)
                "mirror_applier_suspect": suspect,     # 적용사_해당종류_신청인데 후=전 → 발화
                "suspect_cells": sorted(suspect_cells),
                "gated_kinds": sorted(kinds) if kinds else None,
                "effective": eff, "independent": indep,
                "rate": (ev / grid) if grid else None,
                "rate_all": (ev / len(scope)) if scope else None,
                "effective_rate": (eff / grid) if grid else None,
                "independent_rate": (indep / grid) if grid else None,
                "mirror_share": (len(mirror_cells) / ev) if ev else None,
                "mirror_cells": sorted(mirror_cells)[:400],
                "exempt_cells": sorted(exempt_cells),
            })
    return out


def _axis_mirror_findings(census: list[dict]) -> list[dict]:
    """적용사 미러링 오염 `AXIS_SELF_MIRRORED_APPLIER` (RED, 셀 단위).

    **비적용사·비신청 적용사는 절대 여기 안 들어온다** — 그건 정의이거나 정상이다. 걸리는 건
    "그 축을 움직이는 경과조치를 실제로 신청한 회사인데 적용후가 적용전과 한 자리도 안 다른" 칸,
    즉 적용후 컬럼을 적용전에서 복사해 온 지문뿐이다. 현재 라이브 카운트 0 — 룰이 '없다'고
    말할 수 있는 상태가 정답이고, 전부를 동어반복이라 부르던 직전 배선이 오답이었다."""
    out = []
    for row in census:
        for (c, q) in row.get("suspect_cells") or []:
            out.append({"axis": row["axis"], "column": row["column"], "code": c, "quarter": q,
                        "kinds": row.get("gated_kinds")})
    return out


# 축 단위 documented exception — **(axis_id, column)** 쌍. 기본 비어 있다.
# 존재 이유: `AXIS_NOT_EVALUATED` 의 해소 경로는 두 개뿐이다 — 원천을 채워 실질 평가를 만들거나,
# owner 가 "이 축은 원천에 존재하지 않는다" 를 문서화 면제로 등재하는 것. 후자의 경로가 없으면
# 게이트가 영원히 막히거나(비생산적) 누군가 룰을 조용히 끄게 된다(원래 병으로 회귀).
# **등재는 owner 권한**이고, 여기 넣는 순간 `_exemption_registries()` 를 통해 근거 원장
# (data/_gold/kics_exemption_provenance.json) 기록이 강제된다 — registry 항목 = company 자리에
# axis_id, quarter 자리에 column("적용전"/"적용후"). 근거 없이 넣으면 즉시
# EXEMPTION_PROVENANCE_MISSING RED 라, '조용히 끄기'가 구조적으로 불가능하다.
# 2026-08-21 (f): 직전 배선이 `36_irr 적용후`·`R2 적용후` 를 여기 후보로 올렸었는데 **오판이었다**.
# 두 축의 미러 103/182 셀은 전부 **비적용사**라 후=전이 정의상 참이다(적용사 미러 0건 실측).
# 따라서 면제 후보가 아니라 평가율이 낮은 축일 뿐이고, 지금은 AXIS_EVAL_RATE_LOW(review)로만 뜬다.
_AXIS_NOT_EVALUATED_EXEMPT: frozenset[tuple[str, str]] = frozenset()


def _axis_eval_findings(census: list[dict]) -> tuple[list, list]:
    """평가율 census → (red, review).

    RED `AXIS_NOT_EVALUATED` — **실질 평가 0칸**. 두 가지가 여기 들어온다:
      (a) 그 컬럼에서 아무 칸도 계산되지 않은 축,
      (b) 계산된 칸이 **전부 적용사 미러링 오염**이라 새로 확인한 게 한 칸도 없는 축.
    둘 다 "FAIL 0" 을 증거로 쓸 수 없다는 점에서 같다. 이 저장소는 이미 같은 부류를 RED 로
    다룬다 — `CAPSEC_SOURCE_UNRESOLVED` · `DIV_CENSUS_SOURCE_MISSING`("검사축 소실 = 통과 아님").
    해소 경로는 두 개뿐이다: 원천을 채워 실질 평가를 만들거나, **owner 가** 그 축을 문서화 면제로
    등재하는 것. 게이트가 스스로 조용해지는 경로는 없다.

    ⚠️ **비적용사 미러를 실질평가에서 빼지 않는다** (2026-08-21 (f) 정정). 경과조치 미적용사에게
    후 = 전은 정의상 참이라 그 칸을 확인한 것은 헛일이 아니다. 직전 배선이 그걸 빼는 바람에
    `36_irr 적용후`·`R2 적용후` 를 "전부 동어반복" 이라 잘못 RED 로 올렸다 — 정의를 결함으로
    뒤집어 읽은 것이다. 미러의 결함성 판정은 `_axis_mirror_findings`(적용사 + 해당 종류 신청)만 한다.

    REVIEW `AXIS_EVAL_RATE_LOW` — **축 적용 그리드 기준 평가율** 또는 **전 버킷 기준 평가율**
    둘 중 하나가 50% 미만. 두 분모를 다 보는 이유는 grid 가 데이터와 함께 줄어드는 함정 때문이다
    (입력이 통째로 사라지면 grid 도 줄어 rate 는 100% 를 유지한다). 차단은 안 하지만 그 축의
    "FAIL 0" 옆에 항상 같이 인쇄돼서 소수파 요약을 전체로 오독하지 못하게 한다."""
    red, review = [], []
    for row in census:
        if row["grid"] < _AXIS_MIN_GRID:
            continue  # 모수 부족 → 비율 자체가 무의미(합성 픽스처·신규 축 도입기)
        if (row["axis"], row["column"]) in _AXIS_NOT_EVALUATED_EXEMPT:
            continue  # owner 등재 축 면제 — 근거 원장 기록이 별도로 강제된다
        if row["effective"] == 0:
            red.append(row)
            continue
        low = [(k, row[k]) for k in ("rate", "rate_all")
               if row[k] is not None and row[k] < _AXIS_EVAL_RATE_FLOOR]
        if low:
            review.append({**row, "low_on": [k for k, _v in low]})
    return red, review


# ---------------------------------------------------------------------------
# 메타룰 — 동어반복 `IDENTITY_TAUTOLOGY` (owner/orchestrator 티켓 20260821T1500Z)
# ---------------------------------------------------------------------------
# 커버리지(변이시험)와 동어반복은 **서로 다른 축**이다. `tests/test_rule_coverage_manifest.py`
# 는 "룰이 이 칸을 본다"를 증명하지만 "룰이 실패할 수 있다"는 증명하지 않는다. 파이프라인이
# 대상값을 자식합으로 되맞춰(reconcile) 저장하면 룰은 실데이터에서 영원히 통과하고, 변이시험은
# 여전히 GUARDED 로 나오며, 게이트는 그 축에 대해 `FAIL: 0` 을 인쇄한다. 그 0 은 증거가 아니다.
#
# ## 어떻게 재나 — 잔차 분포
#
# 공시표는 억원(일부 백만원)으로 **반올림해서 인쇄된다.** 부모와 자식이 각자 독립적으로 반올림된
# 값이면 `부모 − Σ자식` 은 0 이 아니라 ±1 을 오가는 것이 정상이다. 그 잔차가 정확히 0 인 비율이
# 반올림 잡음이 허용하는 것보다 높으면, 입력이 공시값이 아니라 **파생값**이라는 뜻이다.
#
# 귀무모형: k 개의 항이 각자 독립적으로 반올림됐다면 잔차 = round(ΣX) − Σround(X) 이고
# `P(잔차 = 0) = P(|S_k| ≤ 0.5)`, `S_k` = k 개 U(-0.5, 0.5) 의 합(Irwin–Hall). 스케일 무관이라
# 원천이 억원이든 백만원이든 같은 값이다 — 그래서 소수 셀을 굳이 걸러내지 않는다(걸러내면
# 적용후에서 '미러 셀만 남는' 선택편의가 생겨 통계가 망가진다. 실측으로 확인함).
#
# ## 임계는 추측이 아니라 실측이다 (2026-08-21, 라이브 마스터 486버킷)
#
# 6개 가법 항등식 축 × 2컬럼 = 12개를 전수 측정했다(`k_eff` = 0 아닌 항의 수, `k_eff ≥ 2` 만).
# `excess` = 실측 정확0비율 / 귀무기대비율, `z` = 이항 z-score.
#
#     축                              컬럼    n    정확0        excess     z
#     BR  item2 = item4-12-13         적용후  209   39.7%        0.57    -9.5   건전
#     BR  item2 = item4-12-13         적용전  465   47.7%        0.68   -10.7   건전
#     R1  item1 = item2+item3         적용후  476   56.3%        0.75    -9.4   건전
#     R6  item16 = Σ(17..21)-item15   적용후  481   40.3%        0.76    -5.8   건전
#     R5  item14 = 15-22+23           적용후  316   61.4%        0.86    -4.1   건전
#     R23 item23 = 24+25+26           적용전   52   67.3%        0.95    -0.6   건전
#     R5  item14 = 15-22+23           적용전  321   76.9%        1.07     2.1   건전
#     R23 item23 = 24+25+26           적용후   39   76.9%        1.10     1.0   건전
#     R6  item16 = Σ(17..21)-item15   적용전  486   59.3%        1.11     2.6   건전  ← 건전 최대
#     ---------------------------------------------------------------------------------
#     R1  item1 = item2+item3         적용전  477   97.7%        1.30    11.4   동어반복 ← 확인 최소
#     R2  item4 = Σ(5..11)            적용후  182  100.0%        1.83    12.3   동어반복
#     R2  item4 = Σ(5..11)            적용전  393   99.7%        1.84    18.1   동어반복
#
# 두 축이 **원인이 코드로 확인된** 동어반복이라 대조군의 반대편 끝을 고정해 준다:
#   · R2 — `scripts/fill_period_to_disclosure.py::_reconcile_item4_from_components` 가
#     item4 를 Σ(5..11) 로 덮어쓴다(잔차 ≤ 10 일 때). `scripts/recalc_kics_derived.py` 도 같은 일.
#   · R1 — `scripts/recalc_kics_derived.py` 가 **item3 = item1 − item2 를 무조건 덮어쓴다**
#     (라인 199-221). 그래서 R1 적용전은 정의상 닫힌다. 적용후는 recalc 가 안 건드려서 0.75 다.
#
# 임계 두 개를 **관측된 간극의 기하중점**에 놓는다. 하나만 쓰면 소표본에서 오탐/미탐이 난다:
#   · excess ≥ 1.20  — 건전 최대 1.11 과 확인 최소 1.30 의 기하중점 = 1.202. "효과가 크다".
#   · z      ≥ 5.0   — 건전 최대 2.6 과 확인 최소 11.4 의 기하중점 = 5.4. "잡음이 아니다".
# 둘 다 만족해야 발화한다. 임계를 느슨하게 잡아 0건으로 만드는 것은 이 룰의 존재 이유에 반한다.
#
# **위 표를 지금 다시 재면 R1·R2 행이 안 맞는다 — 정상이고, 룰이 작동한다는 증거다.** 같은 날
# parser 가 티켓 20260821T1505Z 로 item4 되맞춤을 원문값으로 복원하는 중이었고, 세션 내에서
# 다음처럼 걸어 내려왔다:
#     R2 적용전  1.84(z 18.1) → 1.28(z 6.0) → 1.25(z 5.4)   ← 아직 발화
#     R2 적용후  1.83(z 12.3) → 1.46(z 6.8) → 1.43(z 6.4)   ← 아직 발화
#     R1 적용전  1.30(z 11.4) →              → 1.08(z 3.2)   ← **발화 중단**
# 되맞춤이 걷힐수록 excess 가 귀무로 수렴하고, 복원이 끝나면 축은 **저절로 꺼진다**. R1 이
# 이미 그렇게 꺼졌다.
#
# **내 첫 판단이 틀린 부분을 남긴다** (validation 2026-08-21). 처음에 "R2 는 고쳐지는 중이니
# 임계를 코드로 원인이 확정되고 값이 고정된 R1 적용전(1.30)에 앵커한다"고 적었는데, R1 도 같은
# 세션에 1.08 로 내려갔다. 즉 **동어반복 쪽 끝은 어느 것도 고정 앵커가 아니다** — 고치면 다
# 움직인다. 앵커로 쓸 수 있는 것은 반대편, 즉 **건전 대조군의 위쪽 가장자리**뿐이고 그쪽은
# 세 번의 측정에서 R6 적용전 1.11 / z 2.6 으로 한 번도 움직이지 않았다. 따라서 임계의 정당화는
# 이렇게 읽어야 한다: 1.20 은 **안정적인 건전 상한 1.11 위**에 있고, 이 축들이 동어반복이던
# 동안 관측된 **최솟값 1.25 아래**에 있다. 위 표는 그 시점의 실측 기록으로 보존한다 —
# 재현이 안 된다고 표를 지우면 다음 사람이 임계의 근거를 잃는다.
#
# ## 왜 비율축·mmult축은 안 재나 (배제도 실측이다)
#
# `R7`(item27) · `R8`(item28) 은 나눗셈, `R4`/`8_life`/`19_market` 는 sqrt 라 잔차가 **연속량**이다.
# 실측: R4 적용전 486칸 중 |r|<1e-9 이 **0칸**, 8_life 363칸 중 0칸, 19_market 355칸 중 0칸.
# '정확히 0' 통계 자체가 정의되지 않으므로 여기서 재면 항상 excess ≈ 0 = 무조건 통과가 된다
# (검사처럼 보이는 무검사). 이 축들의 동어반복은 다른 지표(미러링·복사 지문)로 잡는다.
_TAUT_EXCESS_FLOOR = 1.20
_TAUT_Z_FLOOR = 5.0
_TAUT_MIN_CELLS = 30      # 실측 최소 축 n=39(R23 적용후). 이보다 작으면 비율 자체가 의미 없다.
_TAUT_ZERO_EPS = 1e-6     # 실제 잔차 최소 granularity 는 0.01(백만원) — float 잡음만 흡수한다.
_TAUT_MAX_K = 8

# ---------------------------------------------------------------------------
# owner 승인 documented exception — 상한 박제형 (2026-08-21)
# ---------------------------------------------------------------------------
# owner 원문: *"딱 보니까 테이블 숫자를 바꾸는 RED는 아닌거같은대? 이번에는 일단 풀고 올려라"*
#
# 맞는 판단이다. `IDENTITY_TAUTOLOGY` 는 **셀 값을 건드리지 않는다** — census 를 읽어 findings 만
# 만들고, 그 결과는 리포트·artifacts·exit code 로만 흘러간다(`records` 에 쓰는 경로 없음).
# 즉 이 축을 면제해도 화면·마스터·xlsx 숫자는 한 칸도 안 움직인다. 막고 있던 것은 "이 항등식이
# 통과해도 증거가 아니다" 라는 **검증 품질** 신호였고, 그것 때문에 실제로 검증된 한 달치
# 데이터가 라이브에 못 올라가고 있었다.
#
# **그래서 면제는 '끄기'가 아니라 '상한 박제'다.** 등재 시점 지표를 박아 두고 매 실행 재측정한다:
#   · 더 되맞춰지면(excess 가 박제 + 허용오차 초과) → RED `IDENTITY_TAUTOLOGY_PIN_DRIFT`. 차단.
#     되맞춤 write-path 가 다시 들어오는 것을 잡는 자리다.
#   · 여전히 발화하되 상한 안이면 → 면제(비차단). 다만 축별 표·"FAIL 0" 옆 경고는 **그대로 찍는다** —
#     면제한 것은 push 차단이지 경고가 아니다.
#   · 더 이상 발화하지 않으면 → REVIEW `IDENTITY_TAUTOLOGY_EXEMPT_UNNECESSARY`. 데이터가 수렴했다는
#     뜻이니 이 등재를 지우라고 알린다(면제가 영구 잔류물이 되는 것을 막는다).
#
# **원인 확정 (2026-08-21, parser-kics 원문 대조로 종결).** 되맞춤이 아니다 — **공시서식이 그렇게
# 생겼다.** 상위 7사(삼성생명·삼성화재·하나손해·신한라이프·코리안리·KB라이프·메트라이프)의 raw 는
# 그 행 라벨을 **`순자산 (1+2+3+4+5+6+7)`** 로 인쇄한다(삼성생명 FY2026_Q1 raw p17 직접 확인).
# 발행사가 총계를 성분의 합으로 **정의**하므로 잔차가 0 인 것이 정상이고, Irwin–Hall 독립반올림
# 귀무가 이 표본에 구조적으로 안 맞는 것이다. 마스터는 원문과 100% 일치한다(9사 23개 (회사,분기)
# 직접 대조 + 442버킷 전수 census, 9사 내 diff 0). 반대편 꼬리(교보생명 +1 쏠림 · 하나생명 −1)도
# raw==master 로, 그 발행사들은 총계 셀을 성분과 독립적으로 채운다 — 같은 라벨이 컬럼에 따라
# 성립/불성립이 갈리는 것이 증거다(교보 2023.2Q resid=0 vs 2023.1Q resid=−1, 같은 페이지).
# 8번째 항목 누락·표/컬럼 혼선·단위 불일치는 전부 원문으로 배제됐다.
#
# **따라서 이 축은 저절로 수렴하지 않는다** — 발행사마다 총계 산출방식이 다른 것은 영구적 특성이라
# `IDENTITY_TAUTOLOGY_EXEMPT_UNNECESSARY` 는 앞으로도 안 뜬다. 그걸 기다리지 마라. 이 등재의 남은
# 역할은 **되맞춤 write-path 재유입 감시** 하나다(그건 pin drift 로 즉시 잡힌다).
# 근본 해결을 하려면 축을 발행사 서식별로 갈라야 한다(라벨에 `(1+2+...)` 가 인쇄된 발행사는 항등식이
# 정의상 닫히므로 평가 대상에서 빼고, 총계가 독립인 발행사만 재는 것). 지금은 안 한다 — 면제가
# pin 으로 보호되고 있고, 축을 가르는 것은 별도 설계 결정이다.
# 조사 기록: `inbox/_resolved/20260821T1830Z` · 프로브 `scripts/_probes/probe_r2_company_detail.py`
# · `probe_r2_item4_source_dump.py`. 초기 가설 2개는 둘 다 반증됐다 — "image-only 24셀이 원인"
# (제외해도 1.25→1.23 · 1.43→1.40) 과 "우리가 item4 를 덮어썼다"(raw==master 100%).
_TAUT_EXEMPT: dict[tuple[str, str], dict[str, float]] = {
    ("R2_순자산합", "적용전"): {"excess": 1.25, "z": 5.4, "n": 393, "zeros": 267},
    ("R2_순자산합", "적용후"): {"excess": 1.43, "z": 6.4, "n": 182, "zeros": 142},
}
# 상한 여유. 데이터가 고쳐지면 n 이 움직이며 excess 도 소수점 둘째 자리에서 흔들린다 —
# 그 잡음은 통과시키되, 되맞춤 재유입(실측 전례: 1.25 -> 1.84)은 반드시 걸리는 폭이다.
_TAUT_PIN_EXCESS_TOL = 0.10

# 축별 부호표. **항목집합은 `_TRANS_AFTER_IDENT` 에서 가져오고** 여기서는 부호만 준다
# (그쪽이 lambda 라 부호를 기계추출할 수 없다). 두 곳이 어긋나면 조용히 다른 축을 재게 되므로
# 불일치는 skip 이 아니라 RED 다 — `TAUTOLOGY_AXIS_SPEC_DRIFT`.
_TAUT_SIGNS: dict[str, dict[int, int]] = {
    "R1_가용자본=기본+보완": {2: +1, 3: +1},
    "R2_순자산합": {5: +1, 6: +1, 7: +1, 8: +1, 9: +1, 10: +1, 11: +1},
    "R5_기준금액": {15: +1, 22: -1, 23: +1},
    "R6_item16": {17: +1, 18: +1, 19: +1, 20: +1, 21: +1, 15: -1},
}


def _taut_axes() -> tuple[list[tuple], list[dict]]:
    """(축 목록, spec drift RED). 축 = (axis_id, target_item, {item: sign}, desc)."""
    axes, drift = [], []
    for rule, tgt, ins, _fn, is_ratio in _TRANS_AFTER_IDENT:
        if is_ratio:
            continue  # 비율축은 잔차가 연속량 — 위 주석 참조
        signs = _TAUT_SIGNS.get(rule)
        if signs is None or set(signs) != set(ins):
            drift.append({"rule": "TAUTOLOGY_AXIS_SPEC_DRIFT", "axis": rule,
                          "detail": f"_TAUT_SIGNS {sorted(signs) if signs else None} != "
                                    f"_TRANS_AFTER_IDENT {sorted(ins)} — 부호표가 항등식과 "
                                    "어긋났다. 동어반복 검사가 다른 축을 재고 있다"})
            continue
        axes.append((rule, tgt, signs, f"item{tgt} 가법 항등식"))
    axes.append(("R23_기타요구자본", _OTHER_CAPITAL_PARENT,
                 {i: +1 for i in _OTHER_CAPITAL_CHILDREN},
                 f"item{_OTHER_CAPITAL_PARENT} = " +
                 "+".join(f"item{i}" for i in _OTHER_CAPITAL_CHILDREN)))
    return axes, drift


def _ih_cdf(x: float, k: int) -> float:
    """Irwin–Hall(k) CDF. MC 대신 닫힌형 — 시드 없이 결정론적이어야 골든이 고정된다."""
    if x <= 0:
        return 0.0
    if x >= k:
        return 1.0
    from math import comb, factorial
    return sum((-1) ** j * comb(k, j) * (x - j) ** k
               for j in range(int(x) + 1)) / factorial(k)


def _taut_null_p0(k: int) -> float:
    """k 개 항이 독립 반올림됐을 때 `P(잔차 = 0)` = P(|S_k| ≤ 0.5). 스케일 무관.
    실측 대조: k=2 0.750 · k=3 0.667 · k=5 0.550 · k=7 0.479."""
    k = min(max(int(k), 2), _TAUT_MAX_K)
    return _ih_cdf(k / 2 + 0.5, k) - _ih_cdf(k / 2 - 0.5, k)


def _identity_tautology_census(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """가법 항등식 축 × 컬럼별 잔차분포 → (census, spec_drift_red).

    **적용전·적용후 둘 다 잰다.** 적용후가 이 저장소의 최대 검증사각이고, 실제로 R2 적용후는
    적용전보다 더 심한 100.0%(182/182) 다 — 미러 셀이 적용전의 되맞춤을 그대로 물려받는다.

    `k_eff` = 그 셀에서 **0 이 아닌** 항의 수. 0 항은 반올림 오차를 만들지 않으므로 귀무기대에
    기여하지 않는다. `k_eff ≤ 1` 셀은 항등식이 자명하게 닫히는 퇴화 셀이라 통계에서 뺀다 —
    이걸 안 빼면 item23 축이 299칸의 `k_eff=0` 때문에 95.8% 로 부풀어 **건전한 축이 동어반복으로
    오탐된다**(실측 확인: 퇴화셀 제외 시 0.95 로 정상 복귀)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))

    axes, drift = _taut_axes()
    out: list[dict] = []
    for axis, tgt, signs, desc in axes:
        for column, i in (("적용전", 0), ("적용후", 1)):
            n = zeros = degenerate = incomplete = 0
            exp = var = 0.0
            khist: Counter = Counter()
            nonzero_examples: list[tuple] = []
            for (c, q), m in sorted(byq.items()):
                tv = m.get(tgt, (None, None))[i]
                if tv is None:
                    incomplete += 1
                    continue
                vals = {it: m.get(it, (None, None))[i] for it in signs}
                if any(v is None for v in vals.values()):
                    incomplete += 1
                    continue
                k_eff = sum(1 for v in vals.values() if v != 0)
                if k_eff < 2:
                    degenerate += 1
                    continue
                p = _taut_null_p0(k_eff)
                n += 1
                exp += p
                var += p * (1 - p)
                khist[k_eff] += 1
                resid = tv - sum(s * vals[it] for it, s in signs.items())
                if abs(resid) < _TAUT_ZERO_EPS:
                    zeros += 1
                elif len(nonzero_examples) < 8:
                    nonzero_examples.append((c, q, round(resid, 4)))
            rate = (zeros / n) if n else None
            exp_rate = (exp / n) if n else None
            excess = (rate / exp_rate) if (rate is not None and exp_rate) else None
            z = ((zeros - exp) / var ** 0.5) if var > 0 else None
            out.append({
                "axis": axis, "column": column, "desc": desc, "n": n, "zeros": zeros,
                "degenerate": degenerate, "incomplete": incomplete,
                "zero_rate": rate, "null_rate": exp_rate, "excess": excess, "z": z,
                "k_eff_hist": dict(sorted(khist.items())),
                "nonzero_examples": nonzero_examples,
            })
    return out, drift


def _identity_tautology_findings(census: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """census → (red, review, exempt).

    RED `IDENTITY_TAUTOLOGY` — excess ≥ 1.20 **그리고** z ≥ 5.0. 이 축의 `FAIL: 0` 은 증거가
    아니라 파이프라인이 대상값을 입력으로부터 되맞춰 저장했다는 지문이다. **해소는 데이터 쪽에서만
    가능하다** — 되맞춤을 제거해 공시값을 복원하면 잔차가 정상 분포로 돌아오고 룰은 저절로 꺼진다.
    임계를 올려서 끄는 것은 이 룰이 존재하는 이유 그 자체를 무력화한다.

    REVIEW `IDENTITY_TAUTOLOGY_MARGINAL` — 한쪽 임계만 넘은 축. 차단하지 않지만 인쇄한다.
    표본이 커지면 RED 로 넘어갈 수 있는 자리이고, 조용히 두면 임계 바로 밑에 눌러앉는다.

    표본부족(`n < 30`)은 통과가 아니라 `IDENTITY_TAUTOLOGY_UNDERPOWERED` review 다 — 축이
    사라져서 n 이 줄면 지표가 '개선'되는 census 고질병을 여기서도 막는다."""
    red, review, exempt = [], [], []
    for row in census:
        if row["excess"] is None:
            review.append({**row, "rule": "IDENTITY_TAUTOLOGY_UNDERPOWERED",
                           "why": "판정 가능한 셀 0칸"})
            continue
        if row["n"] < _TAUT_MIN_CELLS:
            review.append({**row, "rule": "IDENTITY_TAUTOLOGY_UNDERPOWERED",
                           "why": f"n={row['n']} < {_TAUT_MIN_CELLS}"})
            continue
        hi_excess = row["excess"] >= _TAUT_EXCESS_FLOOR
        hi_z = row["z"] is not None and row["z"] >= _TAUT_Z_FLOOR
        pin = _TAUT_EXEMPT.get((row["axis"], row["column"]))
        if hi_excess and hi_z:
            if pin is None:
                red.append(row)
            elif row["excess"] > pin["excess"] + _TAUT_PIN_EXCESS_TOL:
                red.append({**row, "rule": "IDENTITY_TAUTOLOGY_PIN_DRIFT",
                            "pin": pin,
                            "why": f"면제 등재 시점 excess {pin['excess']} 보다 "
                                   f"{row['excess'] - pin['excess']:+.2f} 되맞춰졌다 "
                                   f"(허용 +{_TAUT_PIN_EXCESS_TOL}) — 되맞춤 write-path 재유입 의심"})
            else:
                exempt.append({**row, "rule": "IDENTITY_TAUTOLOGY_EXEMPT", "pin": pin,
                               "why": f"owner 승인 documented exception (2026-08-21). "
                                      f"박제 excess {pin['excess']} · 실측 {row['excess']:.2f} "
                                      f"(Δ{row['excess'] - pin['excess']:+.2f}, 허용 "
                                      f"+{_TAUT_PIN_EXCESS_TOL})"})
        elif pin is not None:
            review.append({**row, "rule": "IDENTITY_TAUTOLOGY_EXEMPT_UNNECESSARY", "pin": pin,
                           "why": f"면제 등재돼 있으나 더는 발화하지 않는다 "
                                  f"(excess {row['excess']:.2f} · z {row['z']:.1f}) — "
                                  f"데이터가 수렴했다. _TAUT_EXEMPT 에서 이 축을 지워라"})
        elif hi_excess or hi_z:
            review.append({**row, "rule": "IDENTITY_TAUTOLOGY_MARGINAL",
                           "why": ("excess" if hi_excess else "z") + " 한쪽만 임계 초과"})
    return red, review, exempt


# ---------------------------------------------------------------------------
# 메타룰 — 원천 판독성 (스캔본을 '정당'으로 세지 않는다)
# ---------------------------------------------------------------------------
_TEXTLAYER_SIDECAR = ROOT / "data" / "_derived" / "kics_source_textlayer.json"


def _source_readability(path: Path | None = None) -> dict:
    """(code, quarter) -> 'READABLE'|'BORDERLINE'|'UNREADABLE'|'UNMEASURED'.

    `scripts/build_kics_source_textlayer.py` 가 raw PDF 텍스트레이어 밀도를 재서 남긴 사이드카를
    읽는다. **사이드카를 그대로 믿지 않는다**: 기록된 파일 크기를 디스크와 대조해 어긋나거나
    파일이 사라졌으면 그 칸을 `UNMEASURED` 로 강등한다(stale 사이드카가 조용히 '판독가능'을
    주장하는 경로 차단 — 2026-08-13 equity 라운드와 같은 지점). 사이드카 자체가 없으면 전 칸
    UNMEASURED = '판정 못 함'이지 '정당'이 아니다."""
    p = path or _TEXTLAYER_SIDECAR
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[tuple, str] = {}
    for key, rec in (data.get("cells") or {}).items():
        if "|" not in key or not isinstance(rec, dict):
            continue
        code, q = key.split("|", 1)
        raw, st = rec.get("raw"), rec.get("status")
        if not raw or st not in ("READABLE", "BORDERLINE", "UNREADABLE"):
            out[(code, q)] = "UNMEASURED"
            continue
        f = ROOT / "data" / "disclosure" / f"FY{q[:4]}_Q{q[5]}" / "raw" / raw
        try:
            fresh = f.stat().st_size == rec.get("bytes")
        except OSError:
            fresh = False
        out[(code, q)] = st if fresh else "UNMEASURED"
    return out


_TFI_APPLICABILITY_SIDECAR = (
    ROOT / "data" / "_derived" / "kics_transition_applicability.json"
)


def _load_tfi_applicability(path: Path | None = None) -> dict:
    """(code, quarter) -> 'O'|'X'|'NA'|'UNKNOWN' — 공통적용 경과조치(TFI) 적용여부 실측.

    `scripts/extract_transition_applicability.py` 가 494버킷을 전수 추출해 남긴 사이드카를
    읽는다. `47_tier2_census` 가 **47/48/49 전부 부재**를 정상 부재(발행사가 TFI 를 적용하지
    않아 근거표를 안 그림)와 추출갭(적용했는데 우리가 못 뽑음)으로 가르는 유일한 근거다.

    **사이드카를 그대로 믿지 않는다** — `_source_readability` 와 같은 방어를 건다:

      · 파일이 없거나 안 읽히면 **빈 맵**을 돌려준다. 빈 맵은 '전부 정상'이 아니라
        '전부 판정 불가'다(룰이 YELLOW review 로 내린다).
      · 레코드가 근거로 삼은 `md_path` 가 디스크에서 사라졌으면 그 칸을 `UNKNOWN` 으로
        **강등**한다. 원본이 없어진 판정은 stale 판정이고, stale 사이드카가 조용히
        '정상 부재'를 주장하는 경로가 이 저장소의 반복 사고형태다.
      · 알 수 없는 값(스키마 변경 등)도 `UNKNOWN` 으로 떨어뜨린다. 모르는 값을 X 로
        추정하면 그 순간 이 룰은 면제 발급기가 된다.

    돌려주는 맵에 키가 아예 없는 (회사,분기)도 룰에서는 UNKNOWN 과 같게 처리된다."""
    p = path or _TFI_APPLICABILITY_SIDECAR
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[tuple, str] = {}
    for rec in (data.get("records") or []):
        if not isinstance(rec, dict):
            continue
        code, q = rec.get("code"), rec.get("quarter")
        if not code or not q:
            continue
        val = rec.get("TFI")
        if val not in ("O", "X", "NA", "UNKNOWN"):
            out[(code, q)] = "UNKNOWN"
            continue
        md = rec.get("md_path")
        try:
            fresh = bool(md) and (ROOT / str(md).replace("\\", "/")).exists()
        except OSError:
            fresh = False
        out[(code, q)] = val if fresh else "UNKNOWN"
    return out


# ---------------------------------------------------------------------------
# 메타룰 — 면제 근거(provenance). "raw 확인" 이라고 쓰기만 하면 되던 자리를 닫는다.
# ---------------------------------------------------------------------------
# 2026-08-21 owner 적대적 재검증 ③: `_AFTER_SUBRISK_NOT_DISCLOSED` 의 두 항목이 "raw 정독 확인"
# 을 근거로 달고 있었는데, raw 에는 그 표가 **멀쩡히 있었다**(KR0003 2026.1Q p24·p25 / KR0073
# 2026.1Q p15 — 본 세션에서 fitz 로 직접 재확인). 실제로 본 것은 docling MD 였고 MD 가 그 페이지를
# 떨어뜨린 것이다. 즉 면제 근거가 **검증 불가능한 산문**이라 아무도 반박할 수 없었다.
# → 모든 면제 항목은 기계가 확인할 수 있는 인용(파일 + 페이지)을 들고 있어야 하고, 인용이 없으면
#   그 사실 자체가 finding 이 된다. 원장은 **억제 장치가 아니다** — 항목을 조용하게 만드는 필드가
#   아예 없고, 게이트는 원장으로 finding 을 지우지 않는다(오직 추가한다).
_EXEMPTION_LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"
# 원장에 있어선 안 되는 키 — 면제원장이 면제억제기로 변질되는 것을 기계로 막는다.
_LEDGER_FORBIDDEN_KEYS = {"suppress", "exempt", "ignore", "waive", "skip", "silence"}


def _after_parent_missing_child_present(records: list[dict]) -> list[tuple]:
    """**부모후 결측 + 세부후 present** = mmult 축이 아예 안 도는 조합 (review, 비차단).

    parser 가 2026-08-20 에 직접 지목한 룰 사각이다(inbox/parser/20260706T0502Z §2):
    `_transition_mmult_after` 는 `post_p is None` 이면 그 (회사,분기,부모)를 통째로 건너뛴다.
    부모후가 없는데 세부후가 채워져 있으면 **세부후가 틀려도 영원히 조용하다.** 실제로 예별손해
    2023.1Q·3Q 에서 item36/37후가 ②표(시장 불변) 값으로 잘못 채워져 있었는데 item19후 결측 때문에
    숨어 있었다 — 그 셀들은 지금 정정됐지만 조합 자체는 다음 분기에 재발한다.

    RED 로 올리지 않는 이유: 부모후 결측 자체는 `post_transition_parent_census` 가 이미 자기
    기준으로 판정하고 있어 여기서 또 차단하면 같은 사실을 두 번 막는다. 여기의 값은 **"이 칸은
    검사되지 않았다"를 명시적으로 세는 것** — 미판정을 통과로 읽지 않게 하는 census 다.

    R5(item14후 = item15후 − item22후 + item23후)로 부모후를 역산할 수 있으면 같이 실어 보낸다:
    검산할 앵커가 하나라도 있으면 다음 사람이 raw 를 열 때 먼저 볼 곳이 생긴다.
    반환 (code, quarter, name, parent, n_present, n_subs, derived_parent_or_None)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))
    out: list[tuple] = []
    for (c, q), m in sorted(byq.items()):
        # 2026-08-24: `(회사,분기)` 통째 skip 을 없앴다. 부재 박제는 **셀 단위**이므로 여기서
        # 걸러야 할 것은 "박제된 부재 셀이 present 로 나타난 조합" 뿐인데, 그건 오히려 봐야 할 신호다.
        for parent, (subs, _mat, _add, _tk) in _TRANS_PARENT_SUBS.items():
            if m.get(parent, (None, None))[1] is not None:
                continue
            present = [i for i in subs if m.get(i, (None, None))[1] is not None]
            if not present:
                continue
            derived = None
            if parent == 15:
                i14, i22, i23 = (m.get(x, (None, None))[1] for x in (14, 22, 23))
                if i14 is not None:
                    derived = round(i14 + (i22 or 0.0) - (i23 or 0.0), 2)
            out.append((c, q, name.get(c, c), parent, len(present), len(subs), derived))
    return out


# ---------------------------------------------------------------------------
# documented exception — 발행사 자기모순 (8_life). **통째 skip 이 아니라 '잔차 박제'다.**
# ---------------------------------------------------------------------------
# KR0079 미래에셋생명 2023.2Q: 총괄표 item17 = 17,495 와 세부표 29~35 의 R7 집계 16,127.5950 이
# 1,367.40억 어긋난다. **추출 오류가 아니라 발행사가 자기 표 둘을 안 맞게 공시한 것**이다.
# validation 이 2026-08-21 에 raw 를 200dpi 로 렌더링해 직접 판독했다
# (data/disclosure/FY2023_Q2/raw/KR0079_미래에셋생명.pdf):
#   p11 [경과조치 적용 전 지급여력비율 세부] 23.2Q 열 → 1.생명장기손해보험위험액 = 17,495,
#       지급여력비율 209.7. 마스터 item17 과 일치.
#   p15/p16 세부표(백만원) → 마스터 item29~35 와 ÷100 일치.
# 어느 쪽이 옳은지는 item17 쪽으로 기운다 — 독립 확증 4개(23.2Q p11 · 23.3Q p11 직전분기열 ·
# rule4 잔차 +0.74 · rule6 잔차 +1.00) 대 세부표 쪽 0개. item17 을 자체산출값으로 갈아끼우면
# RED 가 1→2 로 늘고 원문 2곳에서 확인된 지급여력비율 209.7 과도 어긋난다.
# **owner 가 이 측정을 보고 "원문 기재대로 두자" 로 결정했다(2026-08-21).**
#
# 설계 원칙 — **통째 skip 금지**. 기대잔차를 값으로 박제하고 매 실행 마스터에서 재계산한다.
# 잔차가 박제값에서 벗어나면 면제가 깨지고 다시 RED 다. 그래야 나중에 item17 이나 29~35 중
# 한 칸이 바뀌었을 때 이 면제가 그 변화를 숨기지 못한다. blanket skip 은 이 셀을 영구
# 사각지대로 만든다 — 이 저장소가 반복해서 데인 실패모드가 정확히 그것이다.
#
# **적용전·적용후 둘 다 박제한다.** 같은 자기모순이 게이트에 RED 를 두 번 만든다:
# 룰엔진 `8_life`(적용전) 1건 + 게이트 `_transition_mmult_after` 축 17(적용후) 1건.
# 적용전만 면제하면 적용후가 그대로 막는다 — '적용후가 최대 검증사각' 의 거울상이다.
_LIFE8_ISSUER_INCONSISTENT: dict[tuple[str, str], dict[str, float]] = {
    ("KR0079", "2023.2Q"): {"적용전": 1367.4049866571877, "적용후": 1367.4049866571877},
}
# 박제 허용오차. 마스터 셀은 소수 2자리라 재계산이 결정론적이다 — 느슨하게 잡는 순간
# '박제' 가 아니라 또 하나의 blanket skip 이 된다.
_LIFE8_PIN_TOL = 0.01


def _life8_residual(m: dict[int, tuple], idx: int) -> float | None:
    """item17 − sqrt(29~35 · R7) 을 한 컬럼에서 재계산. 입력 한 칸이라도 결측이면 None.

    R7 은 룰엔진에서 **import** 한다(재타이핑 금지 — 검증기가 검증대상과 다른 행렬을 쓰게 된다)."""
    parent = m.get(17, (None, None))[idx]
    subs = [m.get(i, (None, None))[idx] for i in range(29, 36)]
    if parent is None or any(s is None for s in subs):
        return None
    return parent - _diversified_sqrt(np.array(subs, dtype=float), R7)


def _life8_issuer_inconsistent(records: list[dict]) -> tuple[set, list, list, list]:
    """`_LIFE8_ISSUER_INCONSISTENT` 를 매 실행 마스터에 대고 재검산한다.

    반환 (accepted, red, review, detail)
      accepted — 적용전·적용후 **두 컬럼 모두** 박제잔차와 일치한 (code, quarter). 이 셀에 한해
                 8_life(적용전) RED 와 mmult 축17(적용후) RED 를 차단집계에서 뺀다.
      red      — 면제가 깨진 경우. 세 가지 전부 RED 다(결측을 skip 으로 삼지 않는다):
                 LIFE8_EXEMPTION_INPUT_MISSING   item17 또는 29~35 중 결측 → 박제 확인 불가
                 LIFE8_EXEMPTION_RESIDUAL_DRIFT  잔차가 박제값에서 이탈 → owner 판단의 전제가 바뀜
      review   — LIFE8_EXEMPTION_INERT: 잔차는 맞는데 그 셀에 8_life RED 가 없다(룰 허용오차가
                 바뀌었거나 룰이 안 돌았다). 차단하지 않지만 조용히 두지도 않는다 — 면제가
                 무용해졌으면 등재를 풀어야 한다.
      detail   — 인쇄용 (code, quarter, column, pinned, actual, delta)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))

    accepted: set = set()
    red: list = []
    review: list = []
    detail: list = []
    for (c, q), pins in sorted(_LIFE8_ISSUER_INCONSISTENT.items()):
        m = byq.get((c, q))
        if m is None:
            red.append({"rule": "LIFE8_EXEMPTION_INPUT_MISSING", "code": c, "quarter": q,
                        "detail": "면제 등재분인데 마스터에 그 (회사,분기) 버킷이 없다"})
            continue
        ok = True
        for col, idx in (("적용전", 0), ("적용후", 1)):
            pinned = pins.get(col)
            if pinned is None:
                continue
            actual = _life8_residual(m, idx)
            if actual is None:
                ok = False
                red.append({"rule": "LIFE8_EXEMPTION_INPUT_MISSING", "code": c, "quarter": q,
                            "column": col,
                            "detail": f"item17/29~35 [{col}] 결측 — 박제잔차 {pinned:.4f} 확인 불가. "
                                      "결측은 SKIP 이 아니라 RED 다"})
                continue
            detail.append((c, name.get(c, c), q, col, round(pinned, 4), round(actual, 4),
                           round(actual - pinned, 4)))
            if abs(actual - pinned) > _LIFE8_PIN_TOL:
                ok = False
                red.append({"rule": "LIFE8_EXEMPTION_RESIDUAL_DRIFT", "code": c, "quarter": q,
                            "column": col,
                            "detail": f"[{col}] 박제 {pinned:.4f} → 실측 {actual:.4f} "
                                      f"(Δ{actual - pinned:+.4f}, tol {_LIFE8_PIN_TOL}). "
                                      "owner 판단의 전제(양쪽 다 원문 그대로)가 바뀌었다 — 면제 무효"})
        if ok:
            accepted.add((c, q))
    return accepted, red, review, detail


# ---------------------------------------------------------------------------
# documented exception 3번째 — tier2/다리 축의 **발행사 자기모순** (owner 위임 2026-08-24).
# ---------------------------------------------------------------------------
# 선례는 `_LIFE8_ISSUER_INCONSISTENT`(미래에셋 2023.2Q) 다. owner 결정: "걍 발행사가 원문에
# 기재한 대로 냅두자." 파생값으로 갈아끼우면 RED 가 1→2 로 늘고 헤드라인까지 뒤집힌다.
#
# **등재 기준을 좁게 잡았다 — 발행사 자기모순이 raw 로 확증된 것만.**
# 등재 전 전수 판별에 쓴 기계적 갈래는 이것이다:
#   · TFI 표가 **자기 구성행으로 닫히는가** (`item51 == min(47,48)+49`, 같은 표·같은 컬럼)
#   · 그런데 헤드라인 `item3` 과는 다른가
# 둘 다 참이면 두 표가 서로 다른 값을 인쇄한 것이고, 우리 추출은 양쪽 다 원문 그대로다.
#
# **일부러 등재하지 않은 것들** (같은 축에서 RED 로 남는다 — 무지를 사면하지 않는다):
#   · ~~BNP카디프 2024.3Q~~ · ~~2024.4Q~~ · ~~2025.1Q~~ — 세 분기 전부 등재됐다.
#     2024.4Q·2025.1Q 는 iter-6, **2024.3Q 는 2026-08-24 owner 위임으로 마지막에 들어왔다**
#     (증거가 세 분기 동일한데 위임 목록에만 없어서 두 라운드를 RED 로 버텼다).
#   · ~~동양생명 2025.2Q~~ — iter-6 등재.
#   · ~~한화생명 2025.2Q~~ — **2026-08-24 owner 가 raw 를 직접 열어 보고 등재를 결정했다**
#     ("원문이 그렇게 적혀 있고 별다른 언급은 없다 — 원문대로 오차 용인"). **인과는 여전히
#     미규명**이라 원장 status 를 `VERIFIED_BY_OWNER` 로 따로 갈랐고, 게이트가 매 실행
#     `EXEMPTION_STANDS_ON_OWNER_JUDGEMENT` review 로 인쇄한다. 후속 티켓
#     `inbox/validation/20260824T0410Z` 는 **열어 둔다**(면제 ≠ 원인 규명).
#   · ~~예별손해 2025.1Q~~ — 2026-08-24 owner 위임 등재(아래 항목).
#   · **NH농협손해 2024.3Q — 여전히 RED.** 다리 잔차 −522, **미조사**. 조사 전에 등재하면
#     그건 근거가 아니라 추측이다.
#   · **삼성화재 2025.3Q — 면제 대상이 아니다.** owner 2026-08-24 결정: "자기모순이 자명하니
#     우리가 올바른 숫자로 고쳐서 올린다" → parser 정정 중(`inbox/parser/20260824T0400Z` §G).
#     **여기에 등재하지 말 것** — 고쳐지면 그 축이 저절로 닫힌다.
#   · ~~NH농협손해 2025.4Q~~ — **2026-08-24 (iter-7) 에 등재로 바뀌었다.** 아래 항목 참조.
#     iter-6 에 등재를 거부한 이유는 "표가 실제로는 닫힌다, 우리 식에 항이 빠진 것" 이었는데,
#     parser 가 그 항(`item54`)을 실은 뒤 **전수 시뮬레이션이 그 반대를 증명했다**:
#     `item51 == min(47,48)+49+item54` 를 전 버킷에 강제하면 새로 닫히는 것은 이 1버킷뿐이고
#     **218버킷이 새로 깨진다**(item47 이 이미 후순위채무를 포함해 보고되는 회사가 대다수).
#     즉 이건 K-ICS 공통식이 아니라 **이 발행사의 표 구성 관행**이다 → 잔차 박제형 면제.
#   · ~~롯데손해 2023.1Q~~ — TFI 표 자신의 지급여력금액(25,846) != 기본자본 8,034 + 보완자본
#     17,830 (= 25,864, 18억 차). **2026-08-24 owner 위임으로 등재됐다**(아래 항목).
#
# 설계는 `_LIFE8_*` 와 같다 — **통째 skip 금지, 잔차 박제.** 다만 한 겹 더 조인다:
#   ① `cells` — raw 로 직접 판독한 마스터 값을 그대로 박아 두고 **매 실행 마스터에서 재확인**
#      한다. 한 칸이라도 움직이면 `TIER2_EXEMPTION_INPUT_DRIFT` RED, 결측이면
#      `TIER2_EXEMPTION_INPUT_MISSING` RED. (결측은 SKIP 이 아니다.)
#   ② `findings` — 그 축이 실제로 낸 RED 의 잔차를 박아 두고 매 실행 대조한다. 잔차가 움직이면
#      `TIER2_EXEMPTION_RESIDUAL_DRIFT` RED. RED 가 사라지면 `TIER2_EXEMPTION_INERT` review
#      ("면제가 무용해졌다 — 등재를 풀어라").
# ①이 없으면 룰이 바뀌었을 때만 잡히고, ②가 없으면 데이터가 바뀌었을 때만 잡힌다. 둘 다 건다.
# finding 자체는 지우지 않는다 — report 의 `exempted_findings` 에 그대로 남는다.
_TIER2_PIN_TOL = 0.01

_TIER2_ISSUER_INCONSISTENT: dict[tuple[str, str], dict] = {
    # --- 코리안리 KR1000 ------------------------------------------------------
    # 헤드라인 `[경과조치 적용 전 지급여력비율 세부]` 의 보완자본이 TFI 표의 **적용후** 컬럼과
    # 같고, TFI 표의 **적용전** 컬럼은 자기 구성행으로 정확히 닫힌다. 즉 같은 필링이 '경과조치
    # 적용 전 보완자본' 을 두 값으로 인쇄한다. raw 7분기 전수 word-좌표 확인(2026-08-24):
    #   분기      헤드라인(억)   TFI 적용전(백만)      TFI 적용후(백만)
    #   2023.2Q      5,209        619,243=6,192.43      520,920=5,209.20
    #   2023.3Q      5,114        610,272=6,102.72      511,364=5,113.64
    #   2023.4Q      5,470        646,944=6,469.44      546,989=5,469.89
    #   2024.1Q      5,490        651,623=6,516.23      548,988=5,489.88
    #   2024.2Q      5,444        650,396=6,503.96      544,394=5,443.94
    #   2024.3Q      5,996        707,693=7,076.93      599,602=5,996.02
    #   2024.4Q      8,953        895,327=8,953.27      786,267=7,862.67   <- 여기서 뒤집힌다
    # **잔차가 분기마다 다르다**(-983 ~ -1,081) — TFI 재분류액 자체가 분기마다 달라서다.
    # 그래서 분기별로 따로 박는다. 하나로 뭉치면 그 순간 blanket skip 이다.
    ("KR1000", "2023.2Q"): {
        "cells": {3: {"값": 5209.0}, 47: {"값": 6167.44}, 48: {"값": 9832.38},
                  49: {"값": 24.99}, 51: {"값": 6192.43}},
        "findings": {"3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": -983.43}},
    },
    ("KR1000", "2023.3Q"): {
        "cells": {3: {"값": 5114.0}, 47: {"값": 6102.72}, 48: {"값": 9890.85},
                  49: {"값": 0.0}, 51: {"값": 6102.72}},
        "findings": {"3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": -988.72}},
    },
    ("KR1000", "2023.4Q"): {
        "cells": {3: {"값": 5470.0}, 47: {"값": 6081.79}, 48: {"값": 9995.5},
                  49: {"값": 387.65}, 51: {"값": 6469.44}},
        "findings": {"3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": -999.44}},
    },
    ("KR1000", "2024.1Q"): {
        "cells": {3: {"값": 5490.0}, 47: {"값": 6028.18}, 48: {"값": 10263.55},
                  49: {"값": 488.05}, 51: {"값": 6516.23}},
        "findings": {"3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": -1026.23}},
    },
    ("KR1000", "2024.2Q"): {
        "cells": {3: {"값": 5444.0}, 47: {"값": 5960.9}, 48: {"값": 10600.14},
                  49: {"값": 543.06}, 51: {"값": 6503.96}},
        "findings": {"3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": -1059.96}},
    },
    ("KR1000", "2024.3Q"): {
        "cells": {3: {"값": 5996.0}, 47: {"값": 5919.12}, 48: {"값": 10809.03},
                  49: {"값": 1157.8}, 51: {"값": 7076.93}},
        "findings": {"3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": -1080.92}},
    },
    # 2024.4Q 는 **같은 자기모순의 거울상**이다. 이 분기부터 헤드라인 보완자본(8,953)이 TFI
    # **적용전**(8,953.27)으로 넘어갔는데, 같은 헤드라인표의 `Ⅲ. 보완자본으로 재분류하는 항목`
    # 은 7,863 = TFI **적용후**(7,862.67) 그대로다 — 한 표의 두 행이 서로 다른 기준이다.
    # 그래서 이 분기만 composition 이 통과하고 다리(bridge)가 정확히 그 차액만큼 깨진다:
    #   42,723 - (910 - 0) - 7,863 = 33,950 ~= TFI 적용후 기본자본 33,950.12
    #   공시 기본자본 32,860       ~= TFI 적용전 기본자본 32,859.53      -> 잔차 -1,090
    # raw FY2024_Q4 p24 (헤드라인·TFI 가 같은 페이지) word-좌표 확인.
    ("KR1000", "2024.4Q"): {
        "cells": {2: {"값": 32860.0}, 3: {"값": 8953.0}, 4: {"값": 42723.0},
                  12: {"값": 910.0}, 13: {"값": 7863.0},
                  47: {"값": 7627.84}, 48: {"값": 10905.97}, 49: {"값": 1325.43},
                  50: {"값": 32859.53}, 51: {"값": 8953.27, "값_적용후": 7862.67}},
        "findings": {"2_tier1_bridge": {"flag": "item2 ==", "residual": -1090.0}},
    },
    # --- 롯데손해 KR0003 2023.1Q ---------------------------------------------
    # **owner 위임 2026-08-24.** iter-6 에 "성격은 자기모순이 맞지만 위임 목록 밖" 이라며
    # RED 로 남겨 뒀던 버킷이다. owner 가 등재를 승인했다.
    #
    # 한 필링 안에서 **두 표가 tier 분할을 다르게 인쇄**하고, 그중 TFI 표의 **적용전 컬럼만**
    # 자기 합계행과 안 닫힌다. raw FY2023_Q1 p9(헤드라인, 억원) · p10(TFI, **억원** — 이
    # 발행사는 이 표도 억원이다) 직접 판독:
    #   p9  지급여력금액 25,846 = 기본자본 8,034 + 보완자본 17,812      <- 헤드라인은 닫힌다
    #   p10 지급여력금액 25,846 / 25,846
    #       기본자본      8,034 /  8,469
    #       보완자본     17,830 / 17,377
    #       한도적용전    4,085 /  3,631 · 한도 9,385 / 9,385 · 초과분 13,746 / 13,746
    #       (신종) 454 · (후순위) 3,583
    # **같은 셀(경과조치 적용 전 보완자본)을 두 표가 17,812 와 17,830 으로 다르게 인쇄한다.**
    # 그래서 세 축이 전부 같은 18~19 를 가리키고 **부호가 정확히 반대**로 갈린다:
    #   · 다리   8,034 vs 22,293 − 30 − 14,248 = 8,015                 -> **+19**
    #   · 구성  17,812 vs min(4,085, 9,385) + 13,746 = 17,831          -> **−19**
    #   · TFI 분할 8,034 + 17,830 = 25,864 vs 자기 합계행 25,846        -> **−18**
    # 헤드라인 보완자본 17,812 = 25,846 − 8,034 이다 — 발행사가 헤드라인에서는 합계가 닫히도록
    # 보완자본을 역산해 넣고, TFI 표에는 구성행에서 나온 17,830 을 그대로 적었다.
    #
    # **적용후 컬럼은 정확히 닫힌다**(8,469 + 17,377 = 25,846). 같은 행에서 두 컬럼을 같이
    # 읽는데 한쪽만 깨지므로 우리 추출 결함일 수 없다 — 그래서 면제도 **적용전 축만** 박는다.
    # 순자산도 독립 확증이 있다: 6,902+454+4,788−10+3,538+6,621 = 22,293 (자기 6행 합, 정확).
    # 계산값 25,864 는 raw 전문에 **인쇄되지 않는다**(전 페이지 검색 0회) — 표에 숨은 행이
    # 있어서 닫히는 것이 아니라는 뜻이다.
    ("KR0003", "2023.1Q"): {
        "cells": {1: {"값": 25846.0},
                  2: {"값": 8034.0, "값_적용후": 8469.0},
                  3: {"값": 17812.0, "값_적용후": 17377.0},
                  4: {"값": 22293.0}, 12: {"값": 30.0}, 13: {"값": 14248.0},
                  47: {"값": 4085.0, "값_적용후": 3631.0},
                  48: {"값": 9385.0, "값_적용후": 9385.0},
                  49: {"값": 13746.0, "값_적용후": 13746.0},
                  50: {"값": 8034.0, "값_적용후": 8469.0},
                  51: {"값": 17830.0, "값_적용후": 17377.0},
                  52: {"값": 25846.0, "값_적용후": 25846.0},
                  53: {"값": 454.0}, 54: {"값": 3583.0}},
        "findings": {
            "2_tier1_bridge": {"flag": "item2 ==", "residual": 19.0},
            "3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": -19.0},
            "50_tfi_tier_split": {"flag": "item50 + item51 == item52 [값]", "residual": -18.0},
        },
    },
    # --- 롯데손해 KR0003 2024.4Q ---------------------------------------------
    # TFI 표(raw FY2024_Q4 p60, 백만원)의 **적용전 컬럼만** 자기 구성행과 301백만원 어긋난다:
    #   적용전  869,948(47) + 1,933,391(49) = 2,803,339  vs 인쇄된 보완자본 2,803,038  (-301)
    #   적용후  824,278(47) + 1,933,391(49) = 2,757,669  vs 인쇄된 보완자본 2,757,668  (-1, 반올림)
    # 대조군: 같은 발행사 2025.1Q 는 870,735 + 1,753,563 = 2,624,298 로 **정확히** 닫힌다.
    # 헤드라인 보완자본 28,030 은 TFI 적용전 28,030.38 과 같으므로 '두 표가 다른 값' 이 아니라
    # '표 자신이 자기 구성행과 안 닫힌다' 이고, 그 산수는 인쇄된 숫자만으로 완결된다 —
    # 재추출로 바뀔 수 있는 것이 없다. (NH농협과 달리 잔차 3.01억을 설명하는 다른 인쇄행이
    # 없다: 신종 45,370 + 후순위 822,410 = 867,780 은 어느 쪽과도 안 맞는다.)
    ("KR0003", "2024.4Q"): {
        "cells": {3: {"값": 28030.0}, 47: {"값": 8699.48, "값_적용후": 8242.78},
                  48: {"값": 10846.63}, 49: {"값": 19333.91},
                  51: {"값": 28030.38, "값_적용후": 27576.68}},
        "findings": {
            "3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": -3.39},
            "51_tfi_tier2_composition": {"flag": "TFI_COMPOSITION_NEITHER", "residual": -3.01},
        },
    },
    # --- 롯데손해 KR0003 2025.1Q ---------------------------------------------
    # 헤드라인표(raw FY2025_Q1 p18, 억원) 안에서 `Ⅲ. 보완자본으로 재분류하는 항목` 만 나머지
    # 행과 1,205억 어긋난다. 나머지 입력은 전부 독립 확증이 있다:
    #   Ⅰ 순자산 15,657 = 6,390 + 454 + 3,837 + 504 - 6,128 + 0 + 10,600  (자기 7개 구성행 합, 정확)
    #   기본자본 (2,348) = TFI 표 p19 기본자본 (234,845) / 100 = -2,348.45  (다른 표에서 재확인)
    #   Ⅱ 불인정 8
    #   15,657 - 8 - 19,202 = -3,553  vs  공시 -2,348   -> 잔차 +1,205
    # 대조군: **같은 발행사의 이웃 분기는 전부 정확히 닫힌다** — 2024.3Q 21,670-14-20,121=1,535 ·
    # 2024.4Q 19,095-19-19,806=-730 · 2026.1Q 19,208-23-23,147=-3,962. 이 분기만 안 닫힌다.
    ("KR0003", "2025.1Q"): {
        "cells": {2: {"값": -2348.0}, 3: {"값": 26243.0}, 4: {"값": 15657.0},
                  12: {"값": 8.0}, 13: {"값": 19202.0},
                  47: {"값": 8707.35}, 48: {"값": 11759.09}, 49: {"값": 17535.63},
                  50: {"값": -2348.45}, 51: {"값": 26242.98}},
        "findings": {"2_tier1_bridge": {"flag": "item2 ==", "residual": 1205.0}},
    },
    # --- 롯데손해 KR0003 2026.1Q ---------------------------------------------
    # **발행사가 전기(2025.4Q) TFI 표를 그대로 재게시했다.** raw FY2026_Q1 에서 한 필링 안의
    # 두 표를 직접 대조하면 결론이 나온다:
    #   p21 헤드라인 당분기(2026.1Q) : 26,955 / (3,962) / 30,918 / 기준금액 20,432
    #   p21 헤드라인 직전분기(2025.4Q): 26,058 / (3,875) / 29,934 / 기준금액 20,671
    #   p22 TFI 표                  : 2,605,850 / (387,514) / 2,993,363 / 2,067,069
    #                                 = 26,058.50 / -3,875.14 / 29,933.63 / 20,670.69
    # TFI 표가 **직전분기 열과 소수점까지 일치**한다. 그래서 이 버킷의 RED 5건은 전부 한 원인
    # 이다 — 보완자본 구성(+984.36) · tier 분할 전후(±896.51) · `TIER2_LIMIT_STALE` 전후
    # (item48 10,335.34 = **직전분기** item14 20,671 x 50%, 당분기 20,432 x 50% = 10,216 아님).
    ("KR0003", "2026.1Q"): {
        "cells": {1: {"값": 26955.0}, 3: {"값": 30918.0}, 14: {"값": 20432.0},
                  47: {"값": 8366.25, "값_적용후": 5801.18}, 48: {"값": 10335.34},
                  49: {"값": 21567.39},
                  50: {"값": -3875.14, "값_적용후": -3421.44},
                  51: {"값": 29933.63, "값_적용후": 29479.93}},
        # 2026-08-24 (iter-7) **핀 2개를 뺐다** — `50_tfi_tier_split{,_post}`. 축 E 의 비교
        # 대상이 item1(헤드라인)에서 item52(TFI 표 자신의 지급여력금액 행)로 바뀌면서 이 버킷은
        # 그 축에서 **정확히 닫힌다**: 재게시된 전기 표는 자기 안에서는 일관되기 때문이다
        # (item52 = 26,058.50 = 50 + 51). 게이트가 `TIER2_EXEMPTION_INERT` review 로 먼저
        # 알려 줬다. 재게시라는 사실 자체는 `3_tier2_composition` · `TIER2_LIMIT_STALE`
        # (헤드라인·직전분기 대조라 스코프가 다르다)이 그대로 잡으므로 사각이 생기지 않는다.
        # 죽은 핀을 남겨 두면 다음 세션이 "그 축도 면제돼 있다"고 잘못 읽는다.
        "findings": {
            "3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": 984.36},
            "47_tier2_census": {"flag": "TIER2_LIMIT_STALE", "residual": None},
            "47_tier2_census_post": {"flag": "TIER2_LIMIT_STALE", "residual": None},
        },
    },
    # =====================================================================
    # 아래 3버킷은 **사유가 다르다** — 코리안리·롯데 2026.1Q 는 '두 표가 서로 다른 값을
    # 인쇄' 이고, 여기부터는 '**한 표가 자기 구성행과 안 닫힌다**' 다. 게이트 보고에서
    # 두 계열을 섞어 읽지 않도록 사유 문구를 구분해 둔다.
    # (orchestrator iter-9 발주 2026-08-24. parser 가 raw 전체 텍스트 덤프로 '표에 숨은
    #  행이 없다' 를 확정했고, validation 이 word-좌표로 독립 재확인했다.)
    # =====================================================================
    # --- BNP카디프 KR0075 2024.3Q --------------------------------------------
    # **owner 위임 2026-08-24.** iter-6 에 "2024.4Q·2025.1Q 와 증거가 **동일**한데 위임 목록
    # 밖" 이라며 등재를 보류했던 바로 그 버킷이다(그때 §5-3 에 "자동으로 끼워 넣지 않았다" 고
    # 적었다). owner 가 세 분기를 같이 보게 되면서 위임됐다 — 사유는 아래 두 버킷과 같다.
    #
    # raw FY2024_Q3 p16 (백만원) 직접 판독 — **표 전체를 덤프해도 잔차를 메울 행이 없다**:
    #   보완자본            33,067 / 33,067
    #    보완자본 한도 적용 전 31,614 / 31,614
    #    보완자본 한도        31,614 / 31,614
    #    해약환급금 … 초과분   23,584 / 23,584
    #    (기발행 신종자본증권)    -
    #    (기발행 후순위채무)      -          <- **둘 다 대시**라 NH농협식 설명이 안 통한다
    #   min(31,614, 31,614) + 23,584 = 55,198  vs 인쇄된 보완자본 33,067  (-22,131 = -221.31억)
    #
    # ⚠️ **2026-08-24 박제잔차 정정 — 데이터는 안 움직였다. 룰의 식이 바뀌었다.**
    # 같은 날 `item47` 스코프 결함을 고치면서(아래 KR0068 해제 주석 참조) KR0075 는 **INCL 사**
    # 로 판정됐다(자기 18개 결정적 버킷 전부 INCL, EXCL 0). INCL 읽기에서 채무성 자본은
    # `item47 − item49` = 31,614 − 23,584 = 8,030 이라 한도(31,614)에 안 걸리고
    #   min(8,030, 31,614) + 23,584 = 31,614 (= item47)  vs 인쇄된 보완자본 33,067
    # 즉 **잔차 −221.31 → +14.53**(축 F) · **−220.98 → +14.86**(축 B) 로 이동한다.
    # 마스터 셀은 한 칸도 안 바뀌었다(`cells` 박제값 그대로 통과). 바뀐 것은 우리가 어느 식으로
    # 재는가뿐이다. **면제의 대상(발행사 자기모순)은 그대로이고 측정자만 정확해졌다.**
    # 새 값이 더 정직하다는 방증: 세 분기 모두 **구성 잔차가 다리 잔차와 같은 값으로 수렴한다**
    # (2024.3Q +14.86 vs 다리 +15 · 2024.4Q +87.22 vs 다리 +87). 종전 −221/−242 는 두 개의
    # 서로 다른 불일치가 있는 것처럼 보이게 했지만 실제로는 하나다.
    # 종전 값(EXCL 읽기)도 지우지 않고 원장 `expected_residual_alt_reading` 에 남겼다 —
    # 안 남기면 다음 세션이 "박제값이 등재 기록과 다르다"로 읽고 되돌린다.
    #
    # 헤드라인(p15, 억원)은 자기 안에서 닫힌다: 2,069 = 1,738 + 331. 다리만 +15 어긋난다
    # (2,098 − 44 − 331 = 1,723 vs 인쇄된 기본자본 1,738) — 2024.4Q 의 +87 과 같은 모양이다.
    # `item47 == item48` 은 두 셀을 잘못 읽은 지문이 아니라 **발행사가 같은 숫자를 두 줄에
    # 실제로 인쇄한 것**이다(위 덤프에 31,614 가 두 번 찍혀 있다).
    # TFI 표의 tier 분할 자체는 정확히 닫힌다(173,757 + 33,067 = 206,824 = 자기 합계행) —
    # 깨지는 것은 보완자본 **구성**뿐이라 면제도 그 축들만 박는다.
    ("KR0075", "2024.3Q"): {
        "cells": {1: {"값": 2069.0}, 2: {"값": 1738.0}, 3: {"값": 331.0}, 4: {"값": 2098.0},
                  12: {"값": 44.0}, 13: {"값": 331.0},
                  47: {"값": 316.14, "값_적용후": 316.14},
                  48: {"값": 316.14, "값_적용후": 316.14},
                  49: {"값": 235.84, "값_적용후": 235.84},
                  50: {"값": 1737.57, "값_적용후": 1737.57},
                  51: {"값": 330.67, "값_적용후": 330.67},
                  52: {"값": 2068.24, "값_적용후": 2068.24}},
        "findings": {
            "2_tier1_bridge": {"flag": "item2 ==", "residual": 15.0},
            "3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": 14.86},
            "47_tier2_census": {"flag": "TIER2_DUPLICATE_ROW", "residual": None},
            "47_tier2_census_post": {"flag": "TIER2_DUPLICATE_ROW", "residual": None},
            "51_tfi_tier2_composition": {"flag": "TFI_COMPOSITION_NEITHER", "residual": 14.53},
        },
    },
    # --- BNP카디프 KR0075 2024.4Q · 2025.1Q ----------------------------------
    # TFI 표(raw FY2024_Q4 p50 · FY2025_Q1 p20, 백만원)의 `보완자본` 행이 자기 구성행과
    # 안 닫힌다. **표 전체를 덤프해도 더 읽을 행이 없다** — `(기발행 신종자본증권)` ·
    # `(기발행 후순위채무)` 두 메모행이 **둘 다 대시("-")** 라 NH농협처럼 잔차를 메울
    # 인쇄행이 존재하지 않는다:
    #   2024.4Q  min(34,678, 34,678) + 32,949 = 67,627  vs 인쇄된 보완자본 43,353  (-24,274)
    #   2025.1Q  min(34,759, 34,759) + 30,450 = 65,209  vs 인쇄된 보완자본 40,878  (-24,331)
    # ⚠️ 위 두 줄은 **EXCL 읽기**다. 2026-08-24 스코프 정정 후 이 회사는 INCL 로 판정되어
    # 기대값이 `min(item47−item49, item48) + item49 = item47` 로 바뀐다(위 2024.3Q 주석의
    # 정정 설명이 세 분기에 그대로 적용된다):
    #   2024.4Q  min(1,729, 34,678) + 32,949 = 34,678  vs 43,353  ->  +87.22 (축 B) · +86.75 (축 F)
    #   2025.1Q  min( 4,309, 34,759) + 30,450 = 34,759  vs 40,878  ->  +61.41 (축 B) · +61.19 (축 F)
    # 마스터 셀은 안 움직였다. 박제잔차만 새 식 기준으로 갱신했다.
    # `item47 == item48` 은 두 셀을 잘못 읽은 지문이 아니다 — 발행사가 한도-체크 두 줄에 같은
    # 숫자를 실제로 인쇄한다(좌표읽기·pixmap·전체덤프 3방법 확인).
    # ⚠️ 종전 주석은 그 이유를 "채무성 자본이 0인 회사라서" 로 적었는데 **그건 틀렸다**
    # (2026-08-24 전분기 실측, `scripts/_probes/probe_20260824_kr0075_scope_evidence.py`):
    # item47 ≠ item48 인 나머지 9분기에서 채무성 자본(= item47 − item49)은 0 이 아니다
    # (2025.4Q 53.06 · 2026.1Q 71.51 · 2024.1Q 158.65 …). 이 세 분기만 `한도적용전` 자리에
    # 한도(= item14 × 50%)와 같은 값이 찍혀 있다 — 원인은 여전히 미규명이다.
    # **스코프 판정이 이 세 분기에 기대고 있지는 않다**: INCL 투표 18표는 전부 item47 ≠ item48
    # 인 9분기(각 2컬럼)에서 나오고, 그 분기들은 `i3 == item47` 이면서 item49 > 0 이라
    # "item49 가 item47 안에 있다"를 원문 산수로 직접 보여준다. 이 세 분기는 어느 읽기로도
    # 재현되지 않아(둘다실패) 그대로 RED 이고, 그래서 면제로 박는다.
    # **숨은 공식도 아니다**: 잔차/item49 비율이 6.2% → 26.3% → 20.1% 로 4배 넘게 흔들려
    # 상수가 아니다(3분기 전수). 표에 없는 행을 가정해 채우지 않는다.
    # 2024.4Q 는 그 잔차가 다리에도 그대로 나타난다 — `item51 − item47` = 86.75 ≈ 다리 잔차 87.
    ("KR0075", "2024.4Q"): {
        "cells": {1: {"값": 2091.0}, 2: {"값": 1657.0}, 3: {"값": 434.0}, 4: {"값": 2111.0},
                  12: {"값": 107.0}, 13: {"값": 434.0},
                  47: {"값": 346.78, "값_적용후": 346.78},
                  48: {"값": 346.78, "값_적용후": 346.78},
                  49: {"값": 329.49, "값_적용후": 329.49},
                  50: {"값": 1657.08}, 51: {"값": 433.53}},
        "findings": {
            "2_tier1_bridge": {"flag": "item2 ==", "residual": 87.0},
            "3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": 87.22},
            "47_tier2_census": {"flag": "TIER2_DUPLICATE_ROW", "residual": None},
            "47_tier2_census_post": {"flag": "TIER2_DUPLICATE_ROW", "residual": None},
            "51_tfi_tier2_composition": {"flag": "TFI_COMPOSITION_NEITHER", "residual": 86.75},
        },
    },
    ("KR0075", "2025.1Q"): {
        "cells": {1: {"값": 2118.0}, 2: {"값": 1709.0}, 3: {"값": 409.0}, 4: {"값": 2187.0},
                  12: {"값": 69.0}, 13: {"값": 409.0},
                  47: {"값": 347.59, "값_적용후": 347.59},
                  48: {"값": 347.59, "값_적용후": 347.59},
                  49: {"값": 304.5, "값_적용후": 304.5},
                  50: {"값": 1708.78}, 51: {"값": 408.78}},
        "findings": {
            "3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": 61.41},
            "47_tier2_census": {"flag": "TIER2_DUPLICATE_ROW", "residual": None},
            "47_tier2_census_post": {"flag": "TIER2_DUPLICATE_ROW", "residual": None},
            "51_tfi_tier2_composition": {"flag": "TFI_COMPOSITION_NEITHER", "residual": 61.19},
        },
    },
    # --- 동양생명 KR0087 2025.2Q ---------------------------------------------
    # **2026-08-24: `2_tier1_bridge` 박제를 해제했다 — 우리 룰 결함이었다.**
    #
    # 등재 당시 주장은 "헤드라인표가 자기 각주 주1) 을 어긴다" 였다. 그 주장은 **거짓**이다.
    # 주1) 은 지켜졌고, 틀린 것은 `한도초과 = max(0, item47 − item48)` 이라는 우리 룰의 가정이다.
    # 발행사는 `보완자본 한도 적용 전` 행에 **한도값을 그대로**(1,210,705 = item48) 인쇄했고,
    # 그러면 그 식은 구조적으로 0 을 낸다. 참 한도초과는 같은 표 적용후 컬럼에서 되짚어진다:
    #   promo = item2후 − item2전 = 17,563.63 − 14,118 = 3,445.63  (= (기발행 신종자본증권) 3,445.67)
    #   debt_post = item51후 − item49후 = 25,286.65 − 15,437.23 = 9,849.42
    #   debt_true = 13,295.05  →  한도초과 = 13,295.05 − 12,107.05 = 1,188.00
    #   다리: 33,001 − (1,188 − 1,188.00) − 18,883 = 14,118.00 = 공시 기본자본 (잔차 0.00)
    # 되짚기는 헤드라인표를 전혀 안 본다(입력이 겹치지 않는 독립 도출).
    # 같은 발행사 2025.4Q·2026.1Q 는 `47 > 48` 을 정상 인쇄해 현행 룰로 이미 닫히고(잔차 0.24·0.38)
    # 새 갈래가 그 두 분기를 건드리지 않는다(가드 D). 전 버킷 시뮬: 발동 1 · 해결 1 · **파손 0**.
    # 배선: `kics_json_rules._tier2_excess_recovered_from_post`.
    #
    # **`47_tier2_census` 의 `TIER2_DUPLICATE_ROW` 는 그대로 유지한다** — 그건 여전히 발행사쪽
    # 사실이다. 다만 사유를 정확히 적는다: "발행사가 우연히 같은 값을 두 줄에 인쇄했다" 가 아니라
    # **"참 한도적용전 13,295.05 인데 한도값 12,107.05 가 인쇄됐다"** 이다.
    ("KR0087", "2025.2Q"): {
        "cells": {2: {"값": 14118.0}, 3: {"값": 27544.0}, 4: {"값": 33001.0},
                  12: {"값": 1188.0}, 13: {"값": 18883.0},
                  47: {"값": 12107.05, "값_적용후": 8661.38},
                  48: {"값": 12107.05, "값_적용후": 12107.05},
                  49: {"값": 15437.23, "값_적용후": 15437.23},
                  50: {"값": 14117.96}, 51: {"값": 27544.28, "값_적용후": 25286.65}},
        "findings": {
            "47_tier2_census": {"flag": "TIER2_DUPLICATE_ROW", "residual": None},
        },
    },
    # --- NH농협손해 KR0032 2025.4Q -------------------------------------------
    # **iter-6 에 등재를 거부했던 버킷이다. iter-7 에 판단을 뒤집었다 — 근거가 바뀌었다.**
    #
    # 거부 사유는 "표가 실제로는 닫힌다, 우리 식에 항이 빠진 것" 이었다. raw FY2025_Q4 p46:
    #   보완자본                1,240,112 / 1,240,112
    #    보완자본 한도 적용 전     697,899 /   602,940
    #    보완자본 한도            801,952 /   801,952
    #    해약환급금 … 초과분       447,254 /   447,254
    #    (기발행 신종자본증권)          -
    #    (기발행 후순위채무)        94,959
    #   697,899 + 447,254 + 94,959 = 1,240,112 = 인쇄된 보완자본, **마지막 자리까지 정확**.
    #
    # 그래서 parser 에 `(기발행 후순위채무)` 적재를 발주했고(item54), 그 값이 오면
    # `item51 == min(47,48)+49+item54` 로 **식을 고칠** 생각이었다. 그런데 값이 온 뒤
    # **전수 시뮬레이션이 그 계획을 반증했다** (parser iter-10 + validation 독립 재현):
    #   · 450버킷 검사 · `+item54` 로 **새로 닫히는 것은 이 1버킷뿐**
    #   · `+item54` 를 전 버킷에 강제하면 **218버킷이 새로 깨진다** — 현대해상 12분기 전부,
    #     한화생명 12분기 등, item47(한도 적용 전) 자체가 **이미 후순위채무를 포함한 값**으로
    #     보고되는 회사가 대다수다(그 회사들은 기존 식으로 이미 정확히 닫힌다).
    # 즉 이 구성은 **K-ICS 공통 공식이 아니라 이 발행사의 표 구성 관행**이다. 공식을 고치면
    # 1건을 닫으려고 218건을 깨뜨린다 → 식은 그대로 두고 이 버킷만 잔차 박제형으로 등재한다.
    #
    # **해제조건**: 박제한 `cells` 에 item54(949.59)·47·48·49·51 을 넣었으므로, 발행사가 표
    # 구성을 바꾸거나 item54 가 움직이면 `TIER2_EXEMPTION_INPUT_DRIFT` RED 로 자동 해제된다.
    # 결측이 되면 `..._INPUT_MISSING` RED 다(SKIP 아님). 잔차가 움직여도 `..._RESIDUAL_DRIFT`.
    # 잔차 두 개가 미세하게 다른 이유: `3_tier2_composition` 은 헤드라인 item3(=12,401, 억원
    # 반올림)과, `51_tfi_tier2_composition` 은 같은 표 item51(=12,401.12)과 대조하기 때문이다.
    #
    # **2026-08-24 재감사 정정 2건.**
    # ① `claim_kind` 가 `ISSUER_TABLE_COMPOSITION_VARIANT` 였는데 **variant 가 아니다.**
    #    회사 관행이라면 다른 분기도 같아야 하는데 반대다 — 같은 발행사 13분기 스코어카드는
    #    현행 읽기 12 : `+item54` 읽기 2 이고, 그 2건 중 1건(2026.1Q)은 한도가 구속해 판별력이
    #    없다. 즉 원장이 "원문만으로 확정 불가" 라고 남긴 두 해석은 이제 **확정된다.**
    #    실제로 일어난 일은 **한 행이 후순위채무 한 스텝만큼 밀려 인쇄된 것**이다:
    #      관행대로면 적용전 한도적용전 = 보완자본 1,240,112 − 해약환급금 447,254 = 792,858
    #      인쇄값은 792,858 − 94,959 = 697,899, 적용후는 거기서 또 − 94,959 = 602,940
    # ② 그 진단을 **적용후 컬럼이 독립 확증한다** — 적용후 잔차가 정확히 **2배**다
    #    (1,899.18 = 949.59 × 2). 우연이 아니라 차감 스텝 수다.
    #    그런데 그 적용후 잔차가 종전엔 박제 대상 **밖**이었다(YELLOW 풀에 섞여 들어감).
    #    같은 원장의 KR0094 IRR 면제는 적용전·적용후를 각각 박제하는데 이 축만 비대칭이었다
    #    → 아래 `_post` 두 축을 추가로 박제한다(등급은 YELLOW 그대로, 재검산만 켜진다).
    ("KR0032", "2025.4Q"): {
        "cells": {3: {"값": 12401.0}, 47: {"값": 6978.99, "값_적용후": 6029.4},
                  48: {"값": 8019.52, "값_적용후": 8019.52},
                  49: {"값": 4472.54, "값_적용후": 4472.54},
                  50: {"값": 8606.22}, 51: {"값": 12401.12, "값_적용후": 12401.12},
                  52: {"값": 21007.34}, 53: {"값": 0.0}, 54: {"값": 949.59}},
        "findings": {
            "3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": 949.47},
            "51_tfi_tier2_composition": {"flag": "TFI_COMPOSITION_NEITHER", "residual": 949.59},
            # 적용후 = 후순위채무 2회 차감 (949.59 x 2). 적용전 1배와 짝이라 진단의 확증이다.
            "3_tier2_composition_post": {"flag": "COMPOSITION_NEITHER", "residual": 1899.06},
            "51_tfi_tier2_composition_post": {"flag": "TFI_COMPOSITION_NEITHER",
                                              "residual": 1899.18},
        },
    },
    # --- 예별손해 KR0004 2025.1Q ----------------------------------------------
    # **owner 위임 2026-08-24.** iter-7 에 면제 초안까지 써 놓고 "위임 목록 밖" 이라 등재하지
    # 않았던 버킷이다. 승인됐다.
    #
    # 사유가 위 두 계열과 또 다르다 — **합계는 두 표가 같은데 tier 분할만 다르다.**
    # raw FY2025_Q1 p16(헤드라인, 억원) · p17(TFI, 백만원) 직접 판독:
    #   p16 지급여력금액 △1,651 = 기본자본 △2,648 + 보완자본 997      <- 자기 안에서 닫힌다
    #   p17 지급여력금액 △165,099 (= △1,650.99억)                     <- 헤드라인과 **일치**
    #       기본자본     △165,099 (= △1,650.99억)                     <- 헤드라인 △2,648 과 다름
    #       보완자본            0                                       <- 헤드라인    997 과 다름
    #       한도적용전 0 / 한도 537,868 (=5,378.68억) / 초과분 0 / (신종) 0 / (후순위) 0
    # TFI 표가 보완자본 997억을 **기본자본 쪽에 통째로 합쳐** 인쇄했다. 자본잠식사라 기본자본이
    # 음수인데, 그 상태에서 tier 를 나누지 않고 한 줄로 적은 것이다.
    #
    # 그래서 **다른 축은 전부 정확히 닫힌다**: TFI 구성식 item51 = 0 = min(0, 5,378.68) + 0 ·
    # 다리도 통과(△2,629 − 0 − 19 = △2,648 = 인쇄된 기본자본, 정확). 남는 RED 는
    # `3_tier2_composition` 1건뿐이고 잔차가 **정확히 헤드라인 보완자본 997** 이다 —
    # 즉 "보완자본이 있다고 말하는 표와 0 이라고 말하는 표가 한 필링 안에 같이 있다".
    # 어느 쪽도 추출 오류가 아니라 둘 다 원문 그대로이므로 고칠 셀이 없다.
    # (한도 537,868 은 SCR 과 맞는다: item14_전 10,757 × 50% = 5,378.5 ≈ 5,378.68.)
    ("KR0004", "2025.1Q"): {
        "cells": {1: {"값": -1651.0}, 2: {"값": -2648.0}, 3: {"값": 997.0},
                  4: {"값": -2629.0}, 12: {"값": 0.0}, 13: {"값": 19.0},
                  47: {"값": 0.0, "값_적용후": 0.0},
                  48: {"값": 5378.68, "값_적용후": 5378.68},
                  49: {"값": 0.0, "값_적용후": 0.0},
                  50: {"값": -1650.99, "값_적용후": -1650.99},
                  51: {"값": 0.0, "값_적용후": 0.0},
                  53: {"값": 0.0, "값_적용후": 0.0},
                  54: {"값": 0.0, "값_적용후": 0.0}},
        "findings": {"3_tier2_composition": {"flag": "COMPOSITION_NEITHER", "residual": 997.0}},
    },
    # --- 한화생명 KR0068 2025.2Q — **2026-08-24 해제됨. 다시 등재하지 마라** -------
    # 이 버킷은 2026-08-24 오전에 `VERIFIED_BY_OWNER`(인과 미규명, owner 가 원문을 보고 오차를
    # 용인) 로 등재됐다가 **같은 날 인과가 규명되면서 해제됐다.** 원인은 발행사 모순이 아니라
    # **우리 룰의 스코프 가정**이었다 — 한화생명은 `item47`(보완자본 한도 적용 전)에
    # `item49`(해약환급금 초과분)를 포함해 인쇄하는데(INCL 관행), 룰은 item47 이 채무성 자본만
    # 이라고 가정해 한도초과를 item49 만큼 과대계산했다. 잔차 −30,095 는 그 과대값이 다리에
    # 들어간 결과이지 발행사가 만든 값이 아니었다.
    #
    # 룰을 스코프 인식으로 고치자(`kics_json_rules._tier2_i47_scope_map` + `_tier2_branch`)
    # 이 버킷의 한도초과가 70,821.29 → 825.74 로 내려가고 다리가 **잔차 0.26 으로 닫힌다**:
    #   213,475 − (30,921 − 825.74) − 100,874 = 82,505.74  vs 인쇄된 82,506
    # 게이트가 먼저 `TIER2_EXEMPTION_INERT` 로 "박제한 축에 RED 가 없다 — 등재를 풀어라" 를
    # 인쇄했고, 그에 따라 풀었다. **죽은 핀을 남기면 다음 세션이 "그 축은 면제돼 있다"고 잘못
    # 읽는다**(롯데 2026.1Q 에서 이미 겪었다).
    #
    # 되살아나는 경로는 막혀 있지 않다 — 값이 움직이면 `2_tier1_bridge` 가 그냥 RED 를 낸다.
    # 원장(`data/_gold/kics_exemption_provenance.json`)의 이 항목은 `status=CONTRADICTED` 로
    # 남겨 두었다(이 저장소의 확립된 해제 관행): 같은 (회사,분기)가 다시 면제로 등재되면
    # 게이트가 즉시 `EXEMPTION_CITATION_CONTRADICTED` RED 를 띄운다.
    # 상세·재현: `inbox/_resolved/20260824T0410Z__validation__KR0068_2025.2Q__...md`
    # --- NH농협손해 KR0032 2024.3Q -------------------------------------------
    # **발행사가 자기 각주 정의를 안 지킨다.** 각주는 기본자본 = 순자산 − (불인정항목 −
    # 보완자본한도초과) − 재분류 인데, 공시값으로 계산하면
    #   23,478 − (0 − 초과) − 8,867 = 14,611  vs  공시 기본자본 14,089  →  잔차 −522
    # 다리가 닫히려면 한도초과 = **−522**(음수)여야 한다. "한도를 초과한 금액"이 음수일 수
    # 없고, `item12`(불인정항목)가 **0** 이라 −522 가 들어갈 자리가 식에 아예 없다.
    # 후보 전부 반증: item54 후순위채무 988.61(차 −1,510.61) · item49 초과분 8,866.13
    # (차 −9,388.13) · max(47−48,0)=0(차 −522). 같은 회사 2025.4Q 는 필요 초과 0 으로
    # **정확히 닫힌다** — 이 분기만의 현상이다.
    # owner 결정(2026-08-24): *"나머지는 원수사 모순 그대로 가자"* — 원문대로 두고 박제한다.
    # 해제조건: item2/4/12/13 중 한 칸이라도 움직이면 `..._INPUT_DRIFT` RED 로 되살아난다.
    ("KR0032", "2024.3Q"): {
        "cells": {1: {"값": 24467.0}, 2: {"값": 14089.0}, 3: {"값": 10378.0},
                  4: {"값": 23478.0}, 12: {"값": 0.0}, 13: {"값": 8867.0},
                  47: {"값": 1512.15}, 48: {"값": 5791.11}, 49: {"값": 8866.13},
                  50: {"값": 14088.51}, 51: {"값": 10378.28}, 52: {"값": 24466.79},
                  54: {"값": 988.61}},
        "findings": {
            "2_tier1_bridge": {"flag": "branch=CAPPED", "residual": -522.0},
        },
    },
    # --- 농협생명 KR0104 2026.2Q ---------------------------------------------
    # `47_tier2_census_post` 가 `TIER2_DUPLICATE_ROW` 로 걸린다 — **적용후 컬럼에서만**
    # item47 == item48 == 11,925.57 이 소수점까지 같다. 그런데 이건 두 셀을 잘못 읽은
    # 지문이 아니라 **발행사가 두 줄에 같은 숫자를 실제로 인쇄한 것**이다.
    # 원문 그대로(md_inbox/FY2026_Q2/KR0104_농협생명보험.md L347-358, 백만원):
    #     보완자본 한도 적용 전   1,442,557 | 1,192,557
    #     보완자본 한도          1,719,757 | 1,192,557
    # 적용전 컬럼은 두 값이 다르므로(14,425.57 vs 17,197.57) `47_tier2_census`(적용전)는
    # GREEN 이고, 적용후만 걸린다. 경과조치가 한도를 끌어내려 한도적용전 금액과 한도가
    # 같아진 자리다.
    # **CAPPED 항등식이 두 컬럼 모두 잔차 0.0000 으로 닫힌다** — 추출이 옳다는 직접 증거다:
    #     적용전  min(14,425.57, 17,197.57) + 36,106.24 = 50,531.81 = item51 (잔차 0.0000)
    #     적용후  min(11,925.57, 11,925.57) + 36,106.24 = 48,031.81 = item51 (잔차 0.0000)
    # 즉 값을 고칠 게 없다. 중복행 휴리스틱이 정당한 인쇄를 오탐하는 자리라 그것만 박제한다.
    ("KR0104", "2026.2Q"): {
        "cells": {47: {"값": 14425.57, "값_적용후": 11925.57},
                  48: {"값": 17197.57, "값_적용후": 11925.57},
                  49: {"값": 36106.24, "값_적용후": 36106.24},
                  51: {"값": 50531.81, "값_적용후": 48031.81}},
        "findings": {
            "47_tier2_census_post": {"flag": "TIER2_DUPLICATE_ROW", "residual": None},
        },
    },
}


def _tier2_issuer_inconsistent(records: list[dict], findings: list[dict]):
    """`_TIER2_ISSUER_INCONSISTENT` 를 매 실행 **마스터 + 라이브 룰 산출**에 대고 재검산한다.

    두 겹을 다 본다 (한 겹만이면 반대쪽 변화를 못 본다):
      ① `cells` 를 마스터에서 다시 읽어 박제값과 대조 — 데이터가 움직였는지.
      ② 박제한 축이 실제로 그 잔차의 RED 를 내고 있는지 — 룰이 움직였는지.

    반환 (accepted_findings, red, review, detail)
      accepted_findings — 차단집계에서 뺄 finding 객체 리스트. report 에는 그대로 남는다.
      red      TIER2_EXEMPTION_INPUT_MISSING    박제 셀이 결측 -> 면제 확인 불가 (SKIP 아님)
               TIER2_EXEMPTION_INPUT_DRIFT      박제 셀이 이동 -> owner 판단의 전제가 바뀜
               TIER2_EXEMPTION_RESIDUAL_DRIFT   잔차·사유가 박제값에서 이탈
      review   TIER2_EXEMPTION_INERT            그 축에 RED 가 없다 -> 면제가 무용, 등재를 풀어라
      detail   인쇄용 (code, name, quarter, rule, pinned, actual, delta)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = {KEY_VALUE: _num(r.get(KEY_VALUE)),
                                              KEY_VALUE_POST: _num(r.get(KEY_VALUE_POST))}

    red: list = []
    review: list = []
    detail: list = []
    accepted: list = []
    for (c, q), spec in sorted(_TIER2_ISSUER_INCONSISTENT.items()):
        nm = name.get(c, c)
        m = byq.get((c, q))
        if m is None:
            red.append({"rule": "TIER2_EXEMPTION_INPUT_MISSING", "code": c, "quarter": q,
                        "detail": "면제 등재분인데 마스터에 그 (회사,분기) 버킷이 없다"})
            continue
        cells_ok = True
        for item, cols in sorted(spec["cells"].items()):
            row = m.get(item)
            for col, pinned in cols.items():
                actual = None if row is None else row.get(col)
                if actual is None:
                    cells_ok = False
                    red.append({"rule": "TIER2_EXEMPTION_INPUT_MISSING", "code": c, "quarter": q,
                                "item": item, "column": col,
                                "detail": f"item{item} [{col}] 결측 — 박제값 {pinned} 확인 불가. "
                                          "결측은 SKIP 이 아니라 RED 다"})
                elif abs(actual - pinned) > _TIER2_PIN_TOL:
                    cells_ok = False
                    red.append({"rule": "TIER2_EXEMPTION_INPUT_DRIFT", "code": c, "quarter": q,
                                "item": item, "column": col,
                                "detail": f"item{item} [{col}] 박제 {pinned} -> 실측 {actual} "
                                          f"(delta {actual - pinned:+.4f}, tol {_TIER2_PIN_TOL}). "
                                          "owner 판단의 전제(원문 그대로)가 바뀌었다 — 면제 무효"})
        for rule, pin in sorted(spec["findings"].items()):
            # `_post` 축은 관계식 미확립이라 설계상 YELLOW 로 내려간다(`_POST_UNESTABLISHED`).
            # 그래도 **박제는 걸 수 있어야 한다** — 잔차가 움직이면 알아야 하기 때문이다.
            # 2026-08-24 감사 지적: KR0094 IRR 면제는 적용전·적용후 두 컬럼을 각각 박제하는데
            # tier2 축은 적용전만 박아, 같은 원장 안에서 적용후 커버리지가 비대칭이었다.
            # (박제해도 차단 등급은 안 바뀐다 — YELLOW 는 그대로 YELLOW 다. 바뀌는 것은
            #  '그 잔차를 매 실행 재검산한다' 뿐이고, 이탈하면 RESIDUAL_DRIFT RED 다.)
            want = ("RED", "YELLOW") if rule.endswith("_post") else ("RED",)
            hit = [f for f in findings
                   if f.get("status") in want and str(f.get("rule")) == rule
                   and f.get(KEY_CODE) == c and f.get(KEY_QUARTER) == q]
            if not hit:
                review.append({"rule": "TIER2_EXEMPTION_INERT", "code": c, "quarter": q,
                               "axis": rule,
                               "detail": f"박제한 축 {rule} 에 RED 가 없다 — 룰 허용오차가 바뀌었거나 "
                                         "데이터가 수렴했다. 면제가 무용해졌으면 등재를 풀어라"})
                continue
            f = hit[0]
            flag = pin.get("flag") or ""
            if flag and flag not in str(f.get("detail") or ""):
                red.append({"rule": "TIER2_EXEMPTION_RESIDUAL_DRIFT", "code": c, "quarter": q,
                            "axis": rule,
                            "detail": f"{rule} RED 의 사유가 박제한 '{flag}' 가 아니다 — "
                                      f"실측 detail={str(f.get('detail'))[:120]}"})
                continue
            pinned = pin.get("residual")
            actual = f.get("diff")
            detail.append((c, nm, q, rule, pinned, actual,
                           None if (pinned is None or actual is None) else round(actual - pinned, 4)))
            if pinned is None:
                if actual is not None:
                    red.append({"rule": "TIER2_EXEMPTION_RESIDUAL_DRIFT", "code": c, "quarter": q,
                                "axis": rule,
                                "detail": f"{rule} 은 잔차 없는 census 플래그로 박제했는데 "
                                          f"diff={actual} 이 생겼다 — 축의 성격이 바뀌었다"})
                    continue
            elif actual is None or abs(actual - pinned) > _TIER2_PIN_TOL:
                red.append({"rule": "TIER2_EXEMPTION_RESIDUAL_DRIFT", "code": c, "quarter": q,
                            "axis": rule,
                            "detail": f"{rule} 박제 {pinned} -> 실측 {actual} (tol {_TIER2_PIN_TOL}). "
                                      "owner 판단의 전제가 바뀌었다 — 면제 무효"})
                continue
            if cells_ok:
                accepted.append(f)
    return accepted, red, review, detail

def _irr_pin_recheck(records: list[dict]) -> tuple[list, list]:
    """`IRR_DERIVE_ISSUER_INCONSISTENT` 를 매 실행 마스터에 대고 **인쇄용으로** 재검산한다.

    차단은 이 함수가 하지 않는다 — 이미 두 축이 각자 한다(룰엔진 `36_irr` 적용전 ·
    `_transition_irr_after` 적용후). 여기서는 ① 두 컬럼의 실측 잔차를 매 실행 눈에 보이게 찍고
    ② **면제가 무용해졌는지**(INERT) 를 본다. 잔차가 룰 자신의 허용오차 안으로 들어오면 룰이
    이미 통과시킬 셀이라 면제가 사각지대만 남긴다 → 등재를 풀어야 한다.

    반환 (detail, review). detail = (code, name, quarter, column, pinned, actual, delta, verdict)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))

    detail, review = [], []
    for (c, q), pins in sorted(IRR_DERIVE_ISSUER_INCONSISTENT.items()):
        m = byq.get((c, q))
        if m is None:
            review.append({"rule": "IRR_EXEMPTION_BUCKET_ABSENT", "code": c, "quarter": q,
                           "detail": "면제 등재분인데 마스터에 그 (회사,분기) 버킷이 없다 — "
                                     "등재를 풀거나 데이터를 확인하라"})
            continue
        for col, idx in (("적용전", 0), ("적용후", 1)):
            if col not in pins:
                continue
            vals = {i: m.get(i, (None, None))[idx] for i in _IRR_ALL_ITEMS}
            verdict, pinned, actual = irr_pin_verdict(c, q, col, vals)
            detail.append((c, name.get(c, c), q, col, round(pinned, 4),
                           None if actual is None else round(actual, 4),
                           None if actual is None else round(actual - pinned, 4), verdict))
            if verdict != "MATCH":
                continue
            exp = irr_derive_expected(vals)
            if abs(actual) <= max(_eff_tol(c), IRR_DERIVED_TOL_REL * abs(exp)):
                review.append({"rule": "IRR_EXEMPTION_INERT", "code": c, "quarter": q,
                               "column": col,
                               "detail": f"[{col}] 잔차 {actual:.4f} 가 룰 허용오차 "
                                         f"{max(_eff_tol(c), IRR_DERIVED_TOL_REL * abs(exp)):.4f} 안에 들어왔다 — "
                                         "룰이 이미 통과시킬 셀이라 면제가 사각지대만 남긴다. 등재를 풀어라"})
    return detail, review


def _exemption_registries() -> dict[str, frozenset]:
    """게이트·룰엔진이 실제로 소비하는 면제 레지스트리 전부. 새 레지스트리를 만들면 여기에
    등록해야 provenance 검사를 받는다(빠뜨리면 그 레지스트리는 근거 없이 조용히 산다)."""
    return {
        "_AFTER_SUBRISK_NOT_DISCLOSED": frozenset(_AFTER_SUBRISK_NOT_DISCLOSED),
        "_POST_PARENT_NOT_DISCLOSED": frozenset(_POST_PARENT_NOT_DISCLOSED),
        "INTERNAL_MODEL_36IRR_EXEMPT": frozenset(INTERNAL_MODEL_36IRR_EXEMPT),
        "IRR_SCENARIO_EXEMPT": frozenset(IRR_SCENARIO_EXEMPT),
        "MARKET_BREAKDOWN_EXEMPT": frozenset(MARKET_BREAKDOWN_EXEMPT),
        # (axis_id, column) 쌍 — company 자리=axis, quarter 자리=column 으로 원장에 적는다.
        "_AXIS_NOT_EVALUATED_EXEMPT": frozenset(_AXIS_NOT_EVALUATED_EXEMPT),
        "_LIFE8_ISSUER_INCONSISTENT": frozenset(_LIFE8_ISSUER_INCONSISTENT),
        # 잔차 박제형 면제 3번째 (tier2/다리 발행사 자기모순, owner 위임 2026-08-24).
        "_TIER2_ISSUER_INCONSISTENT": frozenset(_TIER2_ISSUER_INCONSISTENT),
        # 잔차 박제형 면제 2번째. 룰엔진에 살지만 근거 검사는 여기서 받는다 — 레지스트리를
        # 여기 등록하지 않으면 그 면제는 근거 없이 조용히 산다.
        "IRR_DERIVE_ISSUER_INCONSISTENT": frozenset(IRR_DERIVE_ISSUER_INCONSISTENT),
    }


def _load_exemption_ledger(path: Path | None = None):
    p = path or _EXEMPTION_LEDGER
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception:
        return {"_unreadable": True}


# 행 귀속 검사 밴드(포인트). 마커가 기록하려는 명제는 "**어느 행**이 값 V 를 인쇄한다" 인데
# 종전 검사는 "V 가 이 페이지 어딘가 있다" 만 봤다 — 검사처럼 보이는 무검사다(2026-08-24 감사 H5:
# 마커 155개 중 숫자만 132개, 그중 57개가 인용 페이지 안에서 2회 이상 등장).
# 이 밴드는 라벨과 값의 y-중심 거리 상한이다. 실측 캘리브레이션(12케이스 = 참 9 + 음성대조 3):
#   참 히트 최대 Δ 0.21pt · 거짓 히트 최소 Δ 4.63pt → 3.0 에서 12/12 정답, 여유 20배.
# 값이 라벨 **오른쪽**(x)에 있어야 한다는 조건도 같이 건다(표는 라벨열 → 값열 순).
_ROW_ANCHOR_BAND = 3.0


def _word_runs(words, needle: str, band: float = _ROW_ANCHOR_BAND
               ) -> list[tuple[float, float, float]]:
    """공백을 무시한 연속 단어매칭 → [(x0, y중심, x1)]. PDF 는 한 셀을 여러 단어로 쪼갠다.

    **매칭된 단어들이 같은 행 안에 있어야 한다**(y 산포 ≤ band). 이 제약이 없으면 버퍼가
    행 경계를 넘어 누적돼 서로 다른 행의 조각이 한 라벨로 '발견' 되고, 그 run 의 평균 y 가
    행 사이 아무 데나 찍힌다 — 2026-08-24 최초 구현이 정확히 이 버그로 롯데손해 2023.1Q 에서
    `8,034` 를 `기본자본`·`보완자본`·`지급여력금액` 세 행에 동시 귀속시켰다."""
    n = "".join(needle.split())
    if not n:
        return []
    out = []
    for i in range(len(words)):
        buf = ""
        for j in range(i, min(i + 16, len(words))):
            buf += "".join(str(words[j][4]).split())
            ys = [(w[1] + w[3]) / 2 for w in words[i:j + 1]]
            if max(ys) - min(ys) > band:
                break  # 행을 넘어가는 누적은 매칭이 아니다
            if n in buf:
                out.append((words[i][0], sum(ys) / len(ys), words[j][2]))
                break
            if len(buf) > len(n) + 32:
                break
    return out


def _row_anchor_check(pdf_path: Path, pages, row: str, value: str
                      ) -> tuple[bool, float | None]:
    """`행 라벨 row` 와 `값 value` 가 **같은 행**에 있는가 → (anchored, 최소Δ).

    발행사가 값을 다른 행으로 옮기거나 행 순서를 바꾸면 이 검사가 깨진다 — 그것이
    "V 가 페이지 어딘가 있다" 와의 차이다."""
    try:
        import fitz
    except Exception:
        return False, None
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return False, None
    best = None
    idx = [n - 1 for n in pages] if pages else range(doc.page_count)
    for n in idx:
        if not (0 <= n < doc.page_count):
            continue
        ws = sorted(doc[n].get_text("words"), key=lambda w: (w[5], w[6], w[7]))
        labels, values = _word_runs(ws, row), _word_runs(ws, value)
        for _lx0, ly, lx1 in labels:
            for vx0, vy, _vx1 in values:
                if vx0 >= lx1 - 1:
                    d = abs(vy - ly)
                    if best is None or d < best:
                        best = d
    doc.close()
    return (best is not None and best <= _ROW_ANCHOR_BAND), best


def _row_anchor_ys(pdf_path: Path, pages, row: str, value: str) -> list[float]:
    """행 귀속이 성립하는 **라벨 y 목록** (원장 마커 승격 도구가 쓴다). 게이트 판정은
    `_row_anchor_check` 하나로 하고, 이 함수는 그 내부 관측을 그대로 노출한다 —
    승격 도구가 판정기와 다른 기하를 쓰면 원장이 게이트와 다른 것을 근거로 삼게 된다."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
    except Exception:
        return []
    out = []
    idx = [n - 1 for n in pages] if pages else range(doc.page_count)
    for n in idx:
        if not (0 <= n < doc.page_count):
            continue
        ws = sorted(doc[n].get_text("words"), key=lambda w: (w[5], w[6], w[7]))
        labels, values = _word_runs(ws, row), _word_runs(ws, value)
        for _lx0, ly, lx1 in labels:
            if any(vx0 >= lx1 - 1 and abs(vy - ly) <= _ROW_ANCHOR_BAND
                   for vx0, vy, _vx1 in values):
                out.append(ly)
    doc.close()
    return out


def _verify_present_rows(spec: dict) -> tuple[list, list]:
    """`verify.present_rows = [{row, value}]` 를 행 귀속으로 검사 → (ok, broken).

    broken 원소는 (row, value, 최소Δ 또는 None). 하나라도 깨지면 근거가 반증된 것이다."""
    f = spec.get("file")
    rows = [r for r in (spec.get("present_rows") or []) if isinstance(r, dict)]
    if not f or not rows:
        return [], []
    p = ROOT / f
    if not p.exists() or p.suffix.lower() != ".pdf":
        return [], []
    pages = spec.get("pages")
    ok, broken = [], []
    for r in rows:
        row, val = r.get("row"), r.get("value")
        if not row or not val:
            continue
        hit, d = _row_anchor_check(p, pages, str(row), str(val))
        (ok if hit else broken).append((str(row), str(val), d))
    return ok, broken


def _verify_absent_markers(spec: dict) -> tuple[bool, str]:
    """인용된 원천을 **게이트가 직접 다시 열어** 근거를 매 실행 재확인한다.

    `verify = {file, pages?, absent_markers[], present_markers[]}`. 공백을 모두 제거한 뒤
    부분문자열로 찾는다 (PDF 텍스트 추출은 줄바꿈·공백이 제멋대로라 정확일치는 못 쓴다).
    페이지를 지정하면 그 페이지만 열어 비용이 사실상 0 이다.

    두 방향을 다 본다. 한 방향만으로는 근거를 못 세우는 면제가 실제로 있기 때문이다:
      · `absent_markers` — 발견되면 '그 표/섹션이 없다'는 주장이 **거짓** → 반증.
      · `present_markers` — 사라지면 근거로 든 문장 자체가 없어진 것 → 역시 **반증**.
        (2026-08-21 신설. 악사손해 2024.3Q 는 부재 증명보다 원문 각주 "지급여력비율은 2024년
         12월말 공시 예정임(보험업감독규정 부칙 제3조)" 가 훨씬 강한 근거다. 부재 마커만
         지원하면 이런 항목은 영원히 UNVERIFIED 로 남고, 그건 근거가 없어서가 아니라
         검사기가 그 모양의 근거를 표현하지 못해서다.)

    반환 (contradicted, why). why 는 사람이 읽을 사유 문자열."""
    f = spec.get("file")
    absent = [m for m in (spec.get("absent_markers") or []) if m]
    present = [m for m in (spec.get("present_markers") or []) if m]
    rows_spec = [r for r in (spec.get("present_rows") or []) if isinstance(r, dict)]
    if not f or not (absent or present or rows_spec):
        return False, ""
    p = ROOT / f
    if not p.exists():
        return False, ""
    pages = spec.get("pages")
    try:
        if p.suffix.lower() == ".pdf":
            import fitz  # 인용을 실제로 든 항목에서만 임포트 — 평시 게이트는 fitz 를 안 쓴다
            doc = fitz.open(p)
            idx = [n - 1 for n in pages] if pages else range(doc.page_count)
            text = "".join(doc[n].get_text() for n in idx if 0 <= n < doc.page_count)
            doc.close()
        else:
            text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False, ""
    flat = "".join(text.split())
    found = [m for m in absent if "".join(m.split()) in flat]
    missing = [m for m in present if "".join(m.split()) not in flat]
    why = []
    if found:
        why.append(f"부재 주장 반증 — {found} 실재")
    if missing:
        why.append(f"근거 문장 소실 — {missing} 를 인용 페이지에서 찾을 수 없음")
    _ok_rows, broken_rows = _verify_present_rows(spec)
    if broken_rows:
        why.append("행 귀속 반증 — " + ", ".join(
            f"'{r}' 행이 {v} 를 인쇄하지 않는다"
            + (f"(최소Δ {d:.1f}pt > {_ROW_ANCHOR_BAND})" if d is not None else "(값·라벨 미발견)")
            for r, v, d in broken_rows))
    return bool(why), " / ".join(why)


def _verify_markers_ran(spec: dict) -> bool:
    """근거 마커가 **실제로 대조됐는지**. 마커가 없거나 인용 파일이 디스크에 없으면 False.
    이게 없으면 'verify 블록을 비워 두는 것' 이 조용한 통과 경로가 된다 — 검사처럼 보이는 무검사."""
    f = spec.get("file")
    if not f or not (ROOT / f).exists():
        return False
    return bool([m for m in (spec.get("absent_markers") or []) if m]
                or [m for m in (spec.get("present_markers") or []) if m]
                or [r for r in (spec.get("present_rows") or []) if isinstance(r, dict)])


def _cited_page_text_density(spec: dict) -> tuple[int, int] | None:
    """인용 페이지의 텍스트레이어 밀도를 잰다 → (pages, total_chars). 못 재면 None.

    쓰임: 원장이 "스캔본이라 기계검증이 불가능하다" 고 주장할 때 **그 주장 자체를 기계로
    확인**하기 위한 것. 텍스트가 멀쩡히 나오는 PDF 에 image-only 를 적어 두면 그건 근거가
    아니라 회피다."""
    f = spec.get("file")
    if not f:
        return None
    p = ROOT / f
    if not p.exists() or p.suffix.lower() != ".pdf":
        return None
    pages = spec.get("pages")
    try:
        import fitz
        doc = fitz.open(p)
        idx = [n - 1 for n in pages] if pages else range(doc.page_count)
        idx = [n for n in idx if 0 <= n < doc.page_count]
        total = sum(len(doc[n].get_text().strip()) for n in idx)
        doc.close()
    except Exception:
        return None
    return (len(idx), total)


# image-only 주장을 반증하는 임계. 실측 기준점: 텍스트가 살아 있는 정상 표 페이지는 1,000~3,000자
# (예: 푸본현대 2026.1Q p18), 미래에셋 2023.2Q 스캔본은 p11/p15/p16 이 360/76/323자로 **행 라벨이
# 중간에서 잘려 값이 아예 없다**. 800자/페이지면 두 세계 사이에 넉넉히 들어간다.
_IMAGE_CLAIM_MAX_CHARS_PER_PAGE = 800


def _exemption_provenance_findings(registries: dict | None = None, ledger=None
                                   ) -> tuple[list, list]:
    """면제 근거 검사 → (red, review). red/review 원소는 dict(rule, registry, code, quarter, detail).

    RED  EXEMPTION_LEDGER_UNREADABLE      원장이 있는데 파싱 불가 (깨진 파일 ≠ 없는 파일).
    RED  EXEMPTION_LEDGER_SCHEMA_INVALID  원장에 억제성 키가 들어옴 = 원장이 면제억제기로 변질.
    RED  EXEMPTION_PROVENANCE_MISSING     레지스트리엔 있는데 원장에 기록이 아예 없음
                                          → **새 면제를 조용히 추가하는 경로를 즉시 막는다.**
    RED  EXEMPTION_CITATION_UNRESOLVED    인용한 파일이 디스크에 없음(확인 불가능한 인용).
    RED  EXEMPTION_CITATION_CONTRADICTED  게이트가 인용 원천을 열어 '부재' 주장을 반증함,
                                          또는 원장이 스스로 CONTRADICTED 로 기록.
    RED  EXEMPTION_OWNER_RECORD_INCOMPLETE  status=VERIFIED_BY_OWNER 인데 누가·언제·무엇을
                                          보고 무엇을 결정했는지가 비어 있음.
    REVIEW EXEMPTION_PROVENANCE_UNVERIFIED 기록은 있으나 아직 기계검증 가능한 인용이 없음.
    REVIEW EXEMPTION_STANDS_ON_OWNER_JUDGEMENT 인과가 규명된 것이 아니라 owner 가 원문을
                                          직접 보고 오차를 용인한 항목 — 매 실행 인쇄한다."""
    registries = _exemption_registries() if registries is None else registries
    if ledger is None:
        ledger = _load_exemption_ledger()
    red, review = [], []
    if isinstance(ledger, dict) and ledger.get("_unreadable"):
        red.append({"rule": "EXEMPTION_LEDGER_UNREADABLE", "registry": "-", "code": None,
                    "quarter": None,
                    "detail": f"{_EXEMPTION_LEDGER.name} 존재하지만 파싱 불가 — 면제 근거 검사축이 죽었다"})
        ledger = None
    entries = {}
    if isinstance(ledger, dict):
        for e in ledger.get("entries") or []:
            if not isinstance(e, dict):
                continue
            bad = sorted(_LEDGER_FORBIDDEN_KEYS & set(e))
            if bad:
                red.append({"rule": "EXEMPTION_LEDGER_SCHEMA_INVALID",
                            "registry": e.get("registry", "?"), "code": e.get("company"),
                            "quarter": e.get("quarter"),
                            "detail": f"금지 키 {bad} — 원장은 근거 기록이지 억제 장치가 아니다"})
            entries[(e.get("registry"), e.get("company"), e.get("quarter"))] = e
    for reg, cells in sorted(registries.items()):
        for code, q in sorted(cells):
            e = entries.get((reg, code, q))
            if e is None:
                red.append({"rule": "EXEMPTION_PROVENANCE_MISSING", "registry": reg,
                            "code": code, "quarter": q,
                            "detail": "면제 등재분인데 근거 원장에 기록이 없다 — "
                                      "확인 가능한 인용(파일+페이지) 없이 검사에서 빠져 있다"})
                continue
            cit = e.get("citation") or {}
            cf = cit.get("file")
            if cf and not (ROOT / cf).exists():
                red.append({"rule": "EXEMPTION_CITATION_UNRESOLVED", "registry": reg,
                            "code": code, "quarter": q,
                            "detail": f"인용 파일 부재: {cf}"})
                continue
            contradicted, why = _verify_absent_markers(e.get("verify") or {})
            if contradicted:
                v = e.get("verify") or {}
                red.append({"rule": "EXEMPTION_CITATION_CONTRADICTED", "registry": reg,
                            "code": code, "quarter": q,
                            "detail": f"'{e.get('claim','')}' — {v.get('file')} "
                                      f"p{v.get('pages')}: {why}"})
                continue
            if e.get("status") == "CONTRADICTED":
                red.append({"rule": "EXEMPTION_CITATION_CONTRADICTED", "registry": reg,
                            "code": code, "quarter": q,
                            "detail": f"원장 status=CONTRADICTED — {e.get('note', '')}"[:400]})
                continue
            # ---- 판독방식 = 렌더링 육안 (스캔본/텍스트레이어 손상본) -------------------
            # absent_markers 는 텍스트레이어가 살아 있는 PDF 에서만 뜻이 있다. 텍스트가 안 나오는
            # 원천에 마커 검사를 걸면 **항상 '마커 없음' = 주장 확인** 으로 끝나 검사가 무력해진다
            # (기계검증처럼 보이는데 실제로는 아무것도 안 보는 false-green). 그래서 그런 항목은
            # 'VERIFIED' 를 참칭하지 않고 VERIFIED_BY_IMAGE 로 적고, 게이트는 두 가지를 한다:
            #   ① image-only 라는 주장 자체를 기계로 검증(인용 페이지 텍스트 밀도 재측정),
            #   ② 그래도 조용해지지 않는다 — 매 실행 REVIEW 로 인쇄한다.
            if e.get("status") == "VERIFIED_BY_IMAGE":
                iv = e.get("image_verification") or {}
                missing = [k for k in ("method", "pages", "read_by", "why_not_machine_verifiable")
                           if not iv.get(k)]
                if missing:
                    red.append({"rule": "EXEMPTION_IMAGE_RECORD_INCOMPLETE", "registry": reg,
                                "code": code, "quarter": q,
                                "detail": f"VERIFIED_BY_IMAGE 인데 image_verification 필드 누락 {missing} "
                                          "— 판독방식·판독자·기계검증 불가 사유를 적지 않으면 산문 근거와 같다"})
                    continue
                dens = _cited_page_text_density({"file": cf, "pages": iv.get("pages")})
                if dens and dens[0] and dens[1] / dens[0] > _IMAGE_CLAIM_MAX_CHARS_PER_PAGE:
                    red.append({"rule": "EXEMPTION_IMAGE_CLAIM_REFUTED", "registry": reg,
                                "code": code, "quarter": q,
                                "detail": f"'기계검증 불가(스캔본)' 주장 반증 — {cf} p{iv.get('pages')} "
                                          f"텍스트레이어 {dens[1]}자/{dens[0]}페이지 "
                                          f"(={dens[1] / dens[0]:.0f}자/p > {_IMAGE_CLAIM_MAX_CHARS_PER_PAGE}). "
                                          "텍스트가 읽히는 원천이면 인용은 기계검증 가능하게 적어야 한다"})
                    continue
                review.append({"rule": "EXEMPTION_VERIFIED_BY_IMAGE_ONLY", "registry": reg,
                               "code": code, "quarter": q,
                               "detail": f"판독방식={iv.get('method')} 판독자={iv.get('read_by')} "
                                         f"p{iv.get('pages')} — 기계검증 불가 사유: "
                                         f"{iv.get('why_not_machine_verifiable')}"
                                         + (f" (인용페이지 텍스트 {dens[1]}자/{dens[0]}p 로 확인)"
                                            if dens else "")})
                continue
            # ---- 판독자 = owner 본인 (원문에 설명이 없다는 것을 owner 가 확인) -----------
            # 다른 면제들은 "발행사 자기모순" 을 **산수로** 증명한다 — 두 표가 다른 값을
            # 인쇄한다거나, 한 표가 자기 구성행과 안 닫힌다거나. 그런 항목은 근거가 기계로
            # 재현되므로 'VERIFIED' 다.
            #
            # 그런데 **잔차가 실재하는데 원문 어디에도 그 항목이 없는** 경우가 있다. 그때 남는
            # 근거는 "owner 가 원문을 직접 열어 보고 설명이 없음을 확인했고, 원문 그대로 오차를
            # 용인하기로 결정했다" 뿐이다. 이걸 'VERIFIED' 로 적으면 다음 세션이 **인과가
            # 규명된 것으로 오독한다** — 이 저장소가 반복해서 데인 형태다.
            # 그래서 별도 status 로 가르고, 두 가지를 같이 요구한다:
            #   ① 인쇄된 숫자 자체는 여전히 **기계로 재확인**한다(VERIFIED 와 동일한 마커 검사).
            #      owner 판단이 마커 검사를 면제해 주지 않는다.
            #   ② `owner_confirmation` = {read_by, date, what_was_read, verdict} 를 요구한다.
            #      누가·언제·무엇을 보고·무엇을 결정했는지 없으면 산문 근거와 같다.
            # 그리고 **조용해지지 않는다** — 매 실행 review 로 "이 면제는 인과가 아니라 owner
            # 판단 위에 서 있다" 를 인쇄한다. 인과 규명 티켓은 따로 열려 있어야 한다.
            if e.get("status") == "VERIFIED_BY_OWNER":
                oc = e.get("owner_confirmation") or {}
                missing = [k for k in ("read_by", "date", "what_was_read", "verdict")
                           if not oc.get(k)]
                if missing:
                    red.append({"rule": "EXEMPTION_OWNER_RECORD_INCOMPLETE", "registry": reg,
                                "code": code, "quarter": q,
                                "detail": f"VERIFIED_BY_OWNER 인데 owner_confirmation 필드 누락 "
                                          f"{missing} — 누가·언제·무엇을 보고 무엇을 결정했는지 "
                                          "적지 않으면 '누군가 확인했다' 는 산문과 같다"})
                    continue
                if not _verify_markers_ran(e.get("verify") or {}):
                    red.append({"rule": "EXEMPTION_VERIFIED_WITHOUT_MARKERS", "registry": reg,
                                "code": code, "quarter": q,
                                "detail": "VERIFIED_BY_OWNER 인데 verify 마커가 대조되지 않았다 — "
                                          "owner 판단은 '이 잔차를 용인한다' 이지 '숫자를 다시 "
                                          "안 봐도 된다' 가 아니다"})
                    continue
                review.append({"rule": "EXEMPTION_STANDS_ON_OWNER_JUDGEMENT", "registry": reg,
                               "code": code, "quarter": q,
                               "detail": f"인과 미규명 — 판독자={oc.get('read_by')} "
                                         f"확인일={oc.get('date')} 본것={oc.get('what_was_read')} "
                                         f"결정={oc.get('verdict')}"
                                         + (f" / 미규명 단서: {oc.get('open_lead')}"
                                            if oc.get("open_lead") else "")
                                         + (f" / 후속티켓: {oc.get('open_ticket')}"
                                            if oc.get("open_ticket") else "")})
                continue
            if e.get("status") != "VERIFIED" or not cf:
                red_or = review
                red_or.append({"rule": "EXEMPTION_PROVENANCE_UNVERIFIED", "registry": reg,
                               "code": code, "quarter": q,
                               "detail": f"status={e.get('status')} citation="
                                         f"{cf or 'None'} — 기계검증 가능한 인용 미비"})
                continue
            # status=VERIFIED 인데 대조할 마커가 없으면 그건 '검증됨'이 아니라 **검증한 척**이다.
            # 이 구멍을 막지 않으면 verify 블록을 비워 두는 것이 가장 조용한 면제 경로가 된다.
            if not _verify_markers_ran(e.get("verify") or {}):
                red.append({"rule": "EXEMPTION_VERIFIED_WITHOUT_MARKERS", "registry": reg,
                            "code": code, "quarter": q,
                            "detail": f"status=VERIFIED 인데 verify 마커가 대조되지 않았다 "
                                      f"(file={(e.get('verify') or {}).get('file') or 'None'}, "
                                      "absent_markers/present_markers 없음 또는 파일 부재). "
                                      "매 실행 재확인되지 않는 인용은 산문 근거와 같다"})
    return red, review


# ---------------------------------------------------------------------------
# 원장 ↔ 코드 박제 대조 (2026-08-24 신설)
# ---------------------------------------------------------------------------
# **문제**: 원장 `expected_residual` 을 읽는 코드가 하나도 없었다. 진짜 박제는 전부 코드
# 상수(`_TIER2_ISSUER_INCONSISTENT` / `_LIFE8_*` / `IRR_DERIVE_*`)에 있고 원장 숫자는 **사본**
# 이라, 원장만 바꿔도 아무 일이 안 일어났다. 규율이지 강제가 아니었다.
# 실제로 이미 어긋나 있었다 — KR0075 3분기의 **축 목록**이 코드와 다르다(2026-08-24 감사 H3):
#   2024.3Q 원장 `47_tier2_census|적용후` ← 존재하지 않는 축 이름(코드는 `_post` 접미사)
#   2024.4Q · 2025.1Q 원장에 census 두 축이 통째로 없다
# 숫자는 맞는데 "어떤 축을 박제했는가" 가 어긋난 상태였고, 아무도 못 봤다.
#
# **정본은 코드다** — 게이트를 실제로 움직이는 것이 코드 상수이기 때문이다. 원장은 그 사본이고,
# 사본이 어긋나면 RED 다. 이러면 원장이 "장식" 이 아니라 **두 번째 독립 기록**이 된다:
#   · 코드만 고치고 원장을 안 고치면  → `EXEMPTION_PIN_LEDGER_DISAGREE` RED
#   · 원장만 고치고 코드를 안 고쳐도  → 같은 RED (조용한 원장 편집 경로가 막힌다)
# 변이시험: `tests/test_exemption_pin_ledger.py`.
_PIN_COL_PRE, _PIN_COL_POST = "적용전", "적용후"


def _pin_axis_key(rule: str) -> str:
    """코드쪽 룰 이름 → 원장 `expected_residual` 키. `_post` 접미사가 곧 컬럼이다."""
    return f"{rule}|{_PIN_COL_POST if rule.endswith('_post') else _PIN_COL_PRE}"


def _code_pin_map() -> dict[tuple[str, str, str], dict]:
    """게이트가 **실제로 강제하는** 박제 전부를 원장과 같은 모양으로 편다.

    반환 `{(registry, company, quarter): {"expected_residual": {...}, "absent_cells": [...]}}`.
    새 박제형 레지스트리를 만들면 여기에 등록해야 원장 대조를 받는다(빠뜨리면 그 박제는
    원장과 어긋나도 조용하다 — 이 함수 자체가 `_exemption_registries` 와 같은 계약이다)."""
    out: dict[tuple[str, str, str], dict] = {}
    for (c, q), spec in _TIER2_ISSUER_INCONSISTENT.items():
        out[("_TIER2_ISSUER_INCONSISTENT", c, q)] = {
            "expected_residual": {_pin_axis_key(rule): pin.get("residual")
                                  for rule, pin in spec.get("findings", {}).items()},
        }
    for (c, q), pins in _LIFE8_ISSUER_INCONSISTENT.items():
        out[("_LIFE8_ISSUER_INCONSISTENT", c, q)] = {"expected_residual": dict(pins)}
    for (c, q), pins in IRR_DERIVE_ISSUER_INCONSISTENT.items():
        out[("IRR_DERIVE_ISSUER_INCONSISTENT", c, q)] = {"expected_residual": dict(pins)}
    for (c, q), cells in _AFTER_SOURCE_ABSENT_CELLS.items():
        out[("_AFTER_SUBRISK_NOT_DISCLOSED", c, q)] = {"absent_cells": sorted(cells)}
    for (c, q), cells in _POST_PARENT_SOURCE_ABSENT_CELLS.items():
        out[("_POST_PARENT_NOT_DISCLOSED", c, q)] = {"absent_cells": sorted(cells)}
    return out


def _pin_ledger_agreement_findings(ledger=None, pin_tol: float = 0.01,
                                   code_pins: dict | None = None) -> list:
    """코드 박제 == 원장 박제. 어긋나면 RED `EXEMPTION_PIN_LEDGER_DISAGREE`.

    세 방향을 전부 본다(한 방향만 보면 나머지 방향의 편집이 조용히 통과한다):
      ① 축 목록  — 코드에만 있는 키 / 원장에만 있는 키
      ② 잔차 값  — 같은 키의 값이 `pin_tol` 밖으로 다름 (None ↔ 숫자도 불일치)
      ③ 부재 셀  — `absent_cells` 항목집합이 다름
    `expected_residual_alt_reading` 은 종전 읽기의 보존 기록이라 대조 대상이 아니다."""
    if ledger is None:
        ledger = _load_exemption_ledger()
    red: list = []
    if not isinstance(ledger, dict) or ledger.get("_unreadable"):
        return red  # 원장 자체 이상은 `_exemption_provenance_findings` 가 이미 RED 로 낸다
    entries = {(e.get("registry"), e.get("company"), e.get("quarter")): e
               for e in (ledger.get("entries") or [])
               if isinstance(e, dict) and e.get("status") != "CONTRADICTED"}
    for key, code_pin in sorted((code_pins if code_pins is not None
                                 else _code_pin_map()).items()):
        e = entries.get(key)
        if e is None:
            continue  # 원장 기록 자체 부재는 EXEMPTION_PROVENANCE_MISSING 소관
        reg, c, q = key
        if "expected_residual" in code_pin:
            want, have = code_pin["expected_residual"], (e.get("expected_residual") or {})
            only_code = sorted(set(want) - set(have))
            only_led = sorted(set(have) - set(want))
            if only_code or only_led:
                red.append({"rule": "EXEMPTION_PIN_LEDGER_DISAGREE", "registry": reg,
                            "code": c, "quarter": q,
                            "detail": f"박제 축 목록 불일치 — 코드에만 {only_code} · "
                                      f"원장에만 {only_led}. 원장 숫자는 코드 박제의 사본이고, "
                                      "어긋나면 원장이 장식이 된다"})
            for k in sorted(set(want) & set(have)):
                a, b = want[k], have[k]
                if (a is None) != (b is None):
                    red.append({"rule": "EXEMPTION_PIN_LEDGER_DISAGREE", "registry": reg,
                                "code": c, "quarter": q,
                                "detail": f"박제 {k}: 코드 {a!r} vs 원장 {b!r} (한쪽만 null)"})
                elif a is not None and abs(float(a) - float(b)) > pin_tol:
                    red.append({"rule": "EXEMPTION_PIN_LEDGER_DISAGREE", "registry": reg,
                                "code": c, "quarter": q,
                                "detail": f"박제 {k}: 코드 {a} vs 원장 {b} "
                                          f"(Δ{float(b) - float(a):+.4f}, tol {pin_tol})"})
        # 축 단위 tripwire — **해제된 박제가 조용히 되살아나는 경로를 막는다.**
        # 원장 status 를 통째로 CONTRADICTED 로 돌리는 것(한화생명 선례)은 그 (회사,분기)의
        # **모든** 축이 풀렸을 때만 쓸 수 있다. 한 축만 풀리고 다른 축은 정당하게 남는 경우
        # (KR0087 2025.2Q: 다리는 우리 룰 결함으로 해제, census 중복행은 발행사 사실로 유지)
        # 를 담으려면 축 단위 기록이 필요하다.
        for k, why in sorted((e.get("contradicted_pins") or {}).items()):
            if k in (code_pin.get("expected_residual") or {}):
                red.append({"rule": "EXEMPTION_PIN_RE_REGISTERED", "registry": reg,
                            "code": c, "quarter": q,
                            "detail": f"박제 {k} 는 반증돼 해제된 축인데 코드에 다시 등재됐다 — "
                                      f"해제 사유: {str(why)[:300]}"})
        if "absent_cells" in code_pin:
            want_c = list(code_pin["absent_cells"])
            have_c = e.get("absent_cells")
            if have_c is None:
                red.append({"rule": "EXEMPTION_PIN_LEDGER_DISAGREE", "registry": reg,
                            "code": c, "quarter": q,
                            "detail": f"부재 박제 {want_c} 가 코드에 있는데 원장에 `absent_cells` "
                                      "가 없다 — 부재형 면제는 '어느 셀이 원천에 없는가' 가 "
                                      "명제 자체다. 적지 않으면 검증 불가능한 산문이다"})
            elif sorted(int(x) for x in have_c) != want_c:
                red.append({"rule": "EXEMPTION_PIN_LEDGER_DISAGREE", "registry": reg,
                            "code": c, "quarter": q,
                            "detail": f"부재 박제 셀집합 불일치 — 코드 {want_c} vs "
                                      f"원장 {sorted(int(x) for x in have_c)}"})
    return red


_MARKER_NUMERIC = re.compile(r"^[\d,.\s()%△▲-]+$")


def _marker_grade_census(ledger=None) -> tuple[list, list]:
    """verify 마커의 **신뢰도 등급**을 매 실행 센다 → (detail, review).

    ANCHORED   `present_rows` 의 (행 라벨, 값) 쌍 — 행 귀속을 실제로 검사한다. 최고 등급.
    LABELLED   라벨을 포함한 `present_markers` — 문장·행이름이라 위치가 어느 정도 특정된다.
    UNIQUE     숫자만이지만 인용 페이지에서 **1회**뿐 — 귀속이 유일성으로 함의된다.
    AMBIGUOUS  숫자만인데 2회 이상 — "V 가 이 페이지 어딘가 있다" 만 확인한다.
               **이건 검사처럼 보이는 무검사다.** 발행사가 행 순서를 바꾸거나 같은 값이 다른
               행으로 옮겨가도 통과한다. 등급을 낮춰 인쇄하고 review 로 남긴다.

    2026-08-24 감사 H5 가 지적한 그대로다 — `PM-2026-08-24_i47_scope_misread.md` 의
    "근거의 존재는 검사하지만 귀속은 검사하지 않는다" 가 마커 층에서 반복되고 있었다.
    반환 detail = (registry, code, quarter, {등급: [마커…]})."""
    if ledger is None:
        ledger = _load_exemption_ledger()
    detail, review = [], []
    if not isinstance(ledger, dict) or ledger.get("_unreadable"):
        return detail, review
    for e in ledger.get("entries") or []:
        if not isinstance(e, dict) or e.get("status") == "CONTRADICTED":
            continue
        v = e.get("verify") or {}
        f, pages = v.get("file"), v.get("pages")
        pres = [m for m in (v.get("present_markers") or []) if m]
        rows = [r for r in (v.get("present_rows") or []) if isinstance(r, dict)]
        if not f or not (pres or rows):
            continue
        p = ROOT / f
        if not p.exists():
            continue
        flat = ""
        try:
            if p.suffix.lower() == ".pdf":
                import fitz
                doc = fitz.open(p)
                idx = [n - 1 for n in pages] if pages else range(doc.page_count)
                flat = "".join("".join(doc[n].get_text().split())
                               for n in idx if 0 <= n < doc.page_count)
                doc.close()
            else:
                flat = "".join(p.read_text(encoding="utf-8", errors="ignore").split())
        except Exception:
            continue
        anchored_vals = {"".join(str(r.get("value", "")).split()) for r in rows}
        g = {"ANCHORED": [f"{r.get('row')}←{r.get('value')}" for r in rows],
             "LABELLED": [], "UNIQUE": [], "AMBIGUOUS": []}
        for m in pres:
            fm = "".join(m.split())
            n = flat.count(fm)
            if not _MARKER_NUMERIC.match(m):
                g["LABELLED"].append(m)
            elif n <= 1:
                g["UNIQUE"].append(m)
            elif fm in anchored_vals:
                pass  # 같은 값이 `present_rows` 로 행 귀속 검사를 받고 있다 → 더 이상 모호하지 않다
            else:
                g["AMBIGUOUS"].append(f"{m}(×{n})")
        detail.append((e.get("registry"), e.get("company"), e.get("quarter"), g))
        if g["AMBIGUOUS"]:
            review.append({
                "rule": "EXEMPTION_MARKER_UNANCHORED", "registry": e.get("registry"),
                "code": e.get("company"), "quarter": e.get("quarter"),
                "detail": "숫자만인 마커가 인용 페이지에서 2회 이상 등장하는데 행 귀속"
                          "(`present_rows`)이 없다 — '값이 어딘가 있다' 만 검사한다: "
                          + ", ".join(g["AMBIGUOUS"])
                          + f" (같은 항목의 행 귀속 마커 {len(g['ANCHORED'])}개는 검사 중)"})
    return detail, review


def _absence_pin_groups(reg: str, cells: frozenset) -> list[tuple[str, list[int]]]:
    """부재 박제 셀을 **축(부모) 단위 그룹**으로 가른다. 부분충전 판정의 단위다.

    `_AFTER_*` 는 `_PARENT_CHILD_AFTER`(15→16~21 · 17→29~35 · 19→36~40)로 가르고,
    요구자본 부모 박제(`_POST_PARENT_*`)는 그 자체가 한 표라 한 그룹이다."""
    if reg == "_POST_PARENT_NOT_DISCLOSED":
        return [("요구자본 부모표", sorted(cells))]
    out = []
    seen: set[int] = set()
    for p, kids in _PARENT_CHILD_AFTER.items():
        g = sorted(cells & set(kids))
        if g:
            out.append((f"item{p} 세부", g))
            seen |= set(g)
    rest = sorted(cells - seen)
    if rest:
        out.append(("기타", rest))
    return out


def _absence_pin_census(records: list[dict], pins: dict | None = None
                        ) -> tuple[list, list, list]:
    """부재 박제 셀의 **현재 상태**를 셀 단위로 센다 → (detail, red, review).

    detail = (registry, code, quarter, item, column, "결측"|"값존재", value)
    review = `EXEMPTION_ABSENCE_PIN_VALUE_PRESENT` — 원장이 '원천 부재' 라고 한 셀에 값이 있다.
             면제는 그 셀에 대해 **이미 무효**이고(축이 되살아나 검산 중이다), 그 값은 원문
             추출이 아니라 파생값이라는 뜻이므로 조용히 두지 않는다.
    red    = `EXEMPTION_ABSENCE_PIN_PARTIAL_FILL` — 한 축 그룹의 박제 셀이 **일부만** 채워졌다.

    ## 부분충전을 왜 RED 로 거는가 (이 라운드의 핵심 룰)

    부재 박제의 명제는 "이 그룹의 적용후 컬럼이 원천에 없다" 다. 그러면 상태는 둘 중 하나여야
    한다 — 전부 결측(명제 그대로)이거나, 전부 값이 있음(파생해서 채웠고 항등식이 검산한다).
    **섞여 있으면 항등식이 입력 결측으로 SKIP 되면서 채워진 쪽 값이 아무 검사도 안 받는다.**
    이것이 하나생명 2024.4Q 에서 실제로 일어난 일이다: item33후·item34후에 직전분기 값이
    복사돼 있었고 item30후·item35후는 결측이라, 설령 면제를 풀었어도 mmult 는 SKIP 이었다
    (2026-08-24 감사 H1 ②). 그 상태를 직접 겨냥하는 룰이 이것이다 — 부분충전 자체가 결함
    시그니처이고, 결측을 SKIP 으로 삼지 않는다는 이 저장소의 원칙 그대로다.

    이 census 가 이 라운드의 핵심이다 — 종전 부재형 면제는 축을 통째로 순회에서 빼서,
    박제된 셀이 결측인지 stale 값이 앉아 있는지조차 게이트 출력에 **한 줄도 안 나왔다**."""
    byq: dict[tuple, dict] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = _num_cell(r.get(KEY_VALUE_POST))
    detail, red, review = [], [], []
    # `pins` 는 selftest 주입용 override — 기본은 라이브 레지스트리다(주입은 추가만 하고
    # 기본 동작을 안 바꾼다: `--master` 인자와 같은 계약).
    sources = (pins.items() if pins is not None else
               (("_AFTER_SUBRISK_NOT_DISCLOSED", _AFTER_SOURCE_ABSENT_CELLS),
                ("_POST_PARENT_NOT_DISCLOSED", _POST_PARENT_SOURCE_ABSENT_CELLS)))
    for reg, reg_pins in sources:
        for (c, q), cells in sorted(reg_pins.items()):
            m = byq.get((c, q), {})
            present = []
            for it in sorted(cells):
                v = m.get(it)
                detail.append((reg, c, q, it, "적용후",
                               "결측" if v is None else "값존재", v))
                if v is not None:
                    present.append((it, v))
            for gname, group in _absence_pin_groups(reg, cells):
                have = [i for i in group if m.get(i) is not None]
                if have and len(have) < len(group):
                    red.append({
                        "rule": "EXEMPTION_ABSENCE_PIN_PARTIAL_FILL", "registry": reg,
                        "code": c, "quarter": q,
                        "detail": f"[{gname}] 부재 박제 {len(group)}셀 중 {len(have)}셀만 값이 있다 "
                                  f"(값존재 {[f'item{i}후' for i in have]} · "
                                  f"결측 {[f'item{i}후' for i in group if i not in have]}). "
                                  "부분충전은 항등식을 입력결측 SKIP 으로 만들어 채워진 값이 "
                                  "아무 검사도 안 받게 한다 — 결측은 SKIP 이 아니라 RED 다. "
                                  "전부 채우거나(파생 근거를 원장에 적고) 전부 비워라"})
            if present:
                review.append({
                    "rule": "EXEMPTION_ABSENCE_PIN_VALUE_PRESENT", "registry": reg,
                    "code": c, "quarter": q,
                    "detail": "원장은 '원천 부재' 인데 값이 있다 → 파생값이다. 이 셀들의 면제는 "
                              "무효이고 해당 축은 정상 검산 중이다: "
                              + ", ".join(f"item{i}후={v:g}" for i, v in present)})
    return detail, red, review


# 적용후 부모→자식 완전성 census 맵. 적용전 _PARENT_CHILD_ITEMS(하위위험 17·19만)에 더해
# 요구자본 구성(15→16~21)까지 포함 — 적용후 요구자본 부분충전(분산효과16·신용20·운영21후 결측)이
# 적용전 census(하위위험만)와 적용후 identity(결측셀 skip) 양쪽으로 새던 사각을 닫는다.
_PARENT_CHILD_AFTER = {
    15: (16, 17, 18, 19, 20, 21),      # 기본요구자본 → 분산효과 + 5대 위험액
    17: (29, 30, 31, 32, 33, 34, 35),  # 생명장기 → 7 하위위험(사망~대재해)
    19: (36, 37, 38, 39, 40),          # 시장 → 5 하위위험(금리~자산집중)
}


def _parent_present_child_incomplete_after(records: list[dict]) -> list[tuple]:
    """적용후(값_적용후) 부모 present인데 하위 결측 = 적용후 census (적용전 _parent_present_child_incomplete
    미러, owner 2026-07-12 '적용후도 적용전 검증로직 동일 적용'). 기대 자식 = 같은 셀에서 '적용전이
    present & material(≥floor)'인 항목 (적용전이 공시하는 항목은 적용후 표도 동일 구조로 공시해야 함).
    결측 = 파싱갭: 분산효과후 파생누락 / 신용·운영후 carry-forward누락 / 시장·생명장기후 재추출필요.
    부재 박제(`_AFTER_SOURCE_ABSENT_CELLS`)된 **셀만** 기대목록에서 빠지고 따로 집계된다 —
    (회사,분기) 통째 면제가 아니다(2026-08-24). RED(blocking).

    2026-08-21: 적용사 18사 한정 제거 → **전사 39사**. 적용전 census 는 전사인데 그 '적용후 미러'만
    18사였다(비-applier 21사의 적용후 부분충전이 미검사). 확대 즉시 코리안리 2023.3Q 가 잡혔다.
    반환: (out, pinned_absent). out = (code, quarter, parent, name, missing_children),
    pinned_absent = "회사 분기 item부모" → 부재 박제로 빠진 셀 수(인쇄용)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))
    out = []
    pinned_absent: Counter = Counter()
    for (c, q), m in sorted(byq.items()):
        # 2026-08-24: `(회사,분기)` 통째 skip → **셀 단위 부재 박제**. 박제된 셀만 기대목록에서
        # 빼고 따로 센다. 박제 밖 셀은 그대로 RED 이고, 박제된 셀에 값이 나타나면 자동으로
        # 기대목록을 만족해 아무 일도 안 일어난다(= 되살아난다).
        absent = _AFTER_SOURCE_ABSENT_CELLS.get((c, q), frozenset())
        for p, kids in _PARENT_CHILD_AFTER.items():
            post_p = m.get(p, (None, None))[1]
            if post_p is None or abs(post_p) < 1.0:
                continue  # 부모후 없음/0 → 적용후 표 부재(별개 갭, transition MISSING 소관)
            expected = [k for k in kids
                        if (m.get(k, (None, None))[0] is not None
                            and abs(m.get(k, (None, None))[0]) >= _CHILD_MATERIAL_FLOOR)]
            missing = [k for k in expected if m.get(k, (None, None))[1] is None]
            pinned = [k for k in missing if k in absent]
            if pinned:
                pinned_absent[f"{c} {q} item{p}"] += len(pinned)
            missing = [k for k in missing if k not in absent]
            if missing:
                out.append((c, q, p, name.get(c, c), tuple(missing)))
    return out, pinned_absent


def _diversification_negative(records: list[dict]) -> list[tuple]:
    """분산효과(item16)는 정의상 항상 ≥0 (상관계수≤1 → subadditivity). 저장값 음수 또는
    Σ(item17~21) < item15(기준금액) = 구성요소 과소/기준금액 과대 misparse. R6 항등식은 산술만
    봐서 '음수 분산효과'도 통과(item16 == Σ-15 이면 부호 무관) → 부호 sanity 별도 필수.
    IBK연금 2023.2Q ②③ 다중경과조치 표 혼합(item15후=②값·item19후=③값) 적발(2026-07-12).
    전·후 both, 전체 회사(적용사 한정 아님). 적용후는 documented exemption만 제외. RED(blocking).
    반환: (code, quarter, name, mode, value, kind)."""
    def _num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))
    out = []
    for (c, q), m in sorted(byq.items()):
        for mode, idx in (("전", 0), ("후", 1)):
            # 2026-08-24: 적용후 통째 skip 제거. 이 축의 입력(16·15·17~21)은 부재 박제 대상이
            # 아니고(하나생명도 p281 에 전부 인쇄됨), 결측이면 아래 조건이 알아서 통과시킨다.
            v16 = m.get(16, (None, None))[idx]
            i15 = m.get(15, (None, None))[idx]
            subs = [m.get(i, (None, None))[idx] for i in (17, 18, 19, 20, 21)]
            if v16 is not None and v16 < -1.0:
                out.append((c, q, name.get(c, c), mode, round(v16, 1), "저장음수"))
            elif i15 is not None and all(s is not None for s in subs):
                der = sum(subs) - i15
                if der < -1.0:
                    out.append((c, q, name.get(c, c), mode, round(der, 1), "Σ(17~21)<기준금액"))
    return out


# 요구자본 '부모' 항목 (경과조치 적용후 continuity census 대상). item14(지급여력기준금액=Ⅰ-Ⅱ+Ⅲ)의 구성:
#   15=Ⅰ.기본요구자본, 16=분산효과, 17=생명장기·18=일반손해·19=시장·20=신용·21=운영(5대 위험액),
#   22=Ⅱ.법인세조정액, 23=Ⅲ.기타요구자본(종속회사). 하위위험(29~40)의 한 단계 상위 부모(=화면 요구자본 세부행).
# 15~21=코어(경과조치 적용후에도 반드시 공시), 22/23=간헐(종속회사·법인세 유무로 legit-absent 가능).
_POST_PARENT_CORE = (15, 16, 17, 18, 19, 20, 21)
_POST_PARENT_ADJUST = (22, 23)
# 가용자본측·헤드라인 적용후 continuity (2026-08-21 신설). 요구자본(15-23)만 census 하고 있어
# item1(지급여력금액)·2(기본자본)·3(보완자본)·14(기준금액)·27/28(비율) 적용후가 통째로 빠져도
# 게이트가 아무 말도 안 했다 — 그 여섯은 항등식 R1/R5/R7/R8후의 **입력**이라, 결측이면 항등식이
# 조용히 skip 되어 이중으로 새는 자리다. 현재 break 0(확대해도 신규 RED 없음 = 순수 보험).
_POST_CAPITAL_CORE = (1, 2, 3, 14, 27, 28)

# 적용후 부모 census documented exception — 요구자본 '적용후' 컬럼이 구조적으로 미공시/재현불가 확정된
# (회사,분기)만. NO_POST_TRANSITION_DISCLOSURE(항목 4/12/13류)의 요구자본-부모 버전. exemption 추가는
# **owner 권한**(서브에이전트 자체판단 waiver 금지, memory: user-approves-not-executes). 등재분:
#   ("KR0071","2024.4Q") 흥국생명 — image-only PDF + TIR/TER 다중경과조치, R4 재현불가(역산 item15
#     14,747 vs 헤드라인 16,987, Δ2,240 비반올림). parser 비전판독으로 17~21은 채웠으나 15/16/22 결합불명.
#     owner 승인 2026-07-16.
#   ("KR0097","2024.4Q") 하나생명 — 비표준(감사보고서 재무상태표) 공시. 이미 _AFTER_SUBRISK_NOT_DISCLOSED
#     등재분. item16후 산술파생 가능하나 입력 item17후=1757.32가 raw page(2001.90) 불일치=partial-mmult
#     아티팩트 의심 → 파생값 불신. owner 승인 2026-07-16.
#
# **2026-08-24 재설계 — 여기도 셀 단위 부재 박제다.** 종전엔 `(회사,분기)` 통째 skip 이라
# 그 버킷의 **모든** 적용후 부모(1·2·3·14·15~23·27·28)가 continuity census 밖이었다.
# 검증된 claim 은 "15~23후가 원천 부재" 였고 1/2/3/14/27/28후는 실제로 채워져 있다 —
# claim 보다 넓은 면제였다. 이제 박제된 항목만 빠지고, 그 항목에 값이 나타나면 애초에
# break 가 성립하지 않아 자동으로 되살아난다.
_POST_PARENT_SOURCE_ABSENT_CELLS: dict[tuple[str, str], frozenset[int]] = {
    ("KR0049", "2024.3Q"): frozenset(range(15, 24)),
}
_POST_PARENT_NOT_DISCLOSED: frozenset = frozenset(_POST_PARENT_SOURCE_ABSENT_CELLS)

_POST_PARENT_NOT_DISCLOSED_NOTES: dict = {
    # ("KR0071", "2024.4Q") 해제 2026-08-21 (validation, raw fitz 전수). 등재사유 "image-only PDF"
    #   가 **거짓**이다: data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf 는 538p / 286,634자
    #   (533자/p)로 텍스트레이어가 멀쩡하고, K-ICS 인접 페이지(p249·p253·p302·p304)를 직접 열어
    #   보면 전부 선택 가능한 조밀한 본문이다. 진짜 문제는 다른 것 — **"경과조치" 가 538p 전체에서
    #   0회**다. 이 파일은 정기경영공시가 아니라 DART 사업보고서(연결 IFRS17 주석, 쪽번호 "- 135 -")
    #   이기 때문이다. "우리가 가진 파일이 틀린 문서다" 는 "발행사가 공시하지 않았다" 가 아니다 —
    #   문서화 면제로 등재하면 downloader 갭이 영구 사각으로 굳는다. downloader 재수집 대상.
    # ("KR0097", "2024.4Q") 해제 2026-08-21 (validation, raw fitz). 등재사유 "item16후 산술파생
    #   가능하나 입력 item17후=1757.32 가 raw page(2001.90)와 불일치 → 파생값 불신" 의 결론이
    #   **거꾸로였다**: raw p281 [지급여력기준금액] 표가 적용후 컬럼을 통째로 공시한다(단위 천원) —
    #   Ⅰ.기본요구자본 430,530,508 · 생명장기 200,189,811 · 시장 200,345,315 · 신용 154,877,709 ·
    #   운영 36,485,031 · (분산효과) (161,367,358) · Ⅳ.지급여력기준금액 430,530,508.
    #   즉 item16후는 파생할 필요조차 없이 **원문에 1,613.67억으로 찍혀 있고**, 마스터의
    #   item17후=1757.32 쪽이 결함이다(원문 2,001.90). 원문이 정본이므로 면제가 아니라 정정 사안.
    # 악사손해 2024.3Q — 그 분기 공시서에 지급여력비율 섹션이 아예 없다("지급여력비율은 2024년
    # 12월말 공시 예정임(보험업감독규정 부칙 제3조)", raw p3/p9/p11). JSON의 2024.3Q 값은 전부
    # FY2024_Q4 공시서의 '당분기-1분기' 컬럼에서 온 것인데, 그 공시서의 경과조치 적용에 관한
    # 사항 표(p41-43)는 당분기 전용이고, 과거분기 경과조치후를 싣는 건 [지급여력비율 총괄](p36)
    # 뿐이며 거기엔 비율·지급여력금액·지급여력기준금액 세 줄만 있다. 즉 15-23후는 원천 부재.
    # (가용자본측 item3후는 TIR 단독 적용 → 전=후로 확정 가능해 채웠다.) parser 2026-08-20,
    # TODO.md documented exception 등재.
    # 2026-08-24 재감사 보강 인용: FY2024_Q4 p36 [지급여력비율 총괄]이 과거분기 적용후로 싣는 것은
    # 비율·지급여력금액·지급여력기준금액 3줄뿐(당분기-1분기 = 1,939 · 286.5), p42 경과조치 세부표는
    # 당분기 1열 전용, p43 은 분기 컬럼 없음. → 15~23후는 어느 원천에도 없다.
    ("KR0049", "2024.3Q"): "15~23후 원천 부재 (FY2024_Q3 섹션 자체 없음 + FY2024_Q4 p36/p42/p43)",
}


def _post_transition_parent_census(records):
    """경과조치 '적용후' 요구자본 부모 항목(15~21 코어, 22/23 조정) 값_적용후 continuity census
    (owner 2026-07-15 blind spot). 기존 적용후 census/identity/mmult는 부모후가 present일 때만 동작 →
    부모후 자체가 통째 결측이면 전부 skip = false-green (2026.1Q 한화·교보·하나·롯데·농협 통과사고).

    continuity-break-is-RED 준용: (회사,항목) 값_적용후 시계열에서 **직전 공시분기에 적용후가 있었는데
    당 분기 결측**이고 (그 뒤 분기에도 적용후가 다시 있음=sandwiched, 또는 당 분기가 최신=trailing)이면
    = 추출갭 시그니처 → RED. 인접분기에 적용후가 있었다는 건 그 회사가 그 항목의 적용후를 공시한다는
    증거라, 당 분기 결측은 구조적 미공시가 아니라 파싱 유실. (직전 적용후 없는 도입초 onset·항구적
    중단은 flag 안 함 — 오탐 억제.)

    - 코어(15~21 요구자본 + 1·2·3·14·27·28 가용자본/헤드라인): continuity break = RED(blocking).
    - 조정(22/23=법인세조정·기타요구자본): 같은 (회사,분기)에 코어 break가 있을 때만 RED(표 전체 유실의
      일부) — 단독 22/23 break는 종속회사/법인세 legit-absence일 수 있어 review(비차단).
    - `_POST_PARENT_SOURCE_ABSENT_CELLS` 에 **셀 단위로** 박제된 (회사,분기,항목)만 면제이고,
      그 사실은 `pinned_absent` 로 세어 인쇄된다(2026-08-24 — 종전 (회사,분기) 통째 skip 폐지).

    반환 (red, review, pinned_absent): 앞 둘은 각 (code, quarter, name, item, neighbor_q,
    kind[SANDWICHED|TRAILING])."""
    pinned_absent: Counter = Counter()
    # (code, item) -> {quarter: (pre_present, post_present)}
    idx: dict[tuple, dict] = defaultdict(dict)
    name: dict[str, str] = {}
    items_of_interest = (set(_POST_PARENT_CORE) | set(_POST_PARENT_ADJUST)
                         | set(_POST_CAPITAL_CORE))
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if not (c and q) or it not in items_of_interest:
            continue
        pre_ok = _num_cell(r.get(KEY_VALUE)) is not None
        post_ok = (KEY_VALUE_POST in r) and (_num_cell(r.get(KEY_VALUE_POST)) is not None)
        idx[(c, it)][q] = (pre_ok, post_ok)

    def _breaks(items):
        out = []
        for (c, it), qv in idx.items():
            if it not in items:
                continue
            dq = sorted(q for q, (pre, _po) in qv.items() if pre)  # 적용전 present(=행 실재) 분기만
            for i, q in enumerate(dq):
                if qv[q][1]:
                    continue  # 적용후 present → OK
                prev_post = i > 0 and qv[dq[i - 1]][1]
                if not prev_post:
                    continue  # 직전 분기에 적용후 없음(도입초 onset / 직전도 결측) → break 아님
                is_latest = (i == len(dq) - 1)
                later_post = any(qv[dq[j]][1] for j in range(i + 1, len(dq)))
                if not (later_post or is_latest):
                    continue  # 직전만 있고 이후 계속 없음(항구적 중단) → 구조변화 가능, flag 안 함
                if it in _POST_PARENT_SOURCE_ABSENT_CELLS.get((c, q), frozenset()):
                    # 셀 단위 부재 박제 — 세어서 인쇄한다(조용한 미순회 금지). 값이 나타나면
                    # 애초에 break 가 성립하지 않으므로(위 `if qv[q][1]: continue`) 자동 복귀.
                    pinned_absent[f"{c} {q} item{it}후"] += 1
                    continue
                kind = "TRAILING" if is_latest else "SANDWICHED"
                out.append((c, q, name.get(c, c), it, dq[i - 1], kind))
        return out

    core = _breaks(set(_POST_PARENT_CORE) | set(_POST_CAPITAL_CORE))
    adjust = _breaks(_POST_PARENT_ADJUST)
    core_cells = {(c, q) for c, q, *_ in core}
    red = sorted(core + [b for b in adjust if (b[0], b[1]) in core_cells])
    review = sorted(b for b in adjust if (b[0], b[1]) not in core_cells)
    return red, review, pinned_absent


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp949
    except Exception:
        pass
    # `--master PATH` 는 **추가만 하는 인자**다(기본 동작 불변). 커버리지 변이시험이 마스터를
    # 흔든 사본으로 게이트를 돌려야 하는데, 진짜 마스터를 덮어쓰면서 시험할 수는 없기 때문에
    # 넣었다 — tests/test_rule_coverage_manifest.py 의 전체게이트 축 참조.
    src = ROOT / "kics_disclosure.json"
    if "--master" in sys.argv:
        src = Path(sys.argv[sys.argv.index("--master") + 1])
    records = _load_records(src)
    report = run_validation(records,
                            source_has_breakdown=_scan_breakdown_presence(records),
                            tfi_applicability=_load_tfi_applicability())
    findings = report.get("findings", [])

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "kics_validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"report_{ts}.json"
    report["source"] = str(src)
    report["generated_at"] = ts
    report["spot_check"] = {
        "code": SPOT_CODE,
        "quarter": SPOT_QUARTER,
        "name_hint": "헕국화재",
        "findings": [
            f
            for f in findings
            if f.get(KEY_CODE) == SPOT_CODE and f.get(KEY_QUARTER) == SPOT_QUARTER
        ],
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    census = _coverage_census(records)
    report["coverage_census"] = {
        "regular_filers": census["regular_filers"],
        "median_filers_per_q": census["median_filers_per_q"],
        "missing_count": len(census["missing_rows"]),
        "missing_rows": [
            {"quarter": q, "code": c, "name": n} for q, c, n in census["missing_rows"]
        ],
        "collapsed_quarters": census["collapsed_quarters"],
    }
    tooling_fail = _market_tooling_fail(records)
    report["market_tooling_fail"] = [
        {"code": c, "quarter": q, "status": s, "name": n} for c, q, s, n in tooling_fail
    ]
    parent_child = _parent_zero_child_nonzero(records)
    report["parent_zero_child_nonzero"] = [
        {
            "code": c, "quarter": q, "parent_item": p, "name": n,
            "nonzero_children": [{"item": k, "value": v} for k, v in nz],
        }
        for c, q, p, n, nz in parent_child
    ]
    partial_child, full_absent_child = _parent_present_child_incomplete(records)
    report["parent_present_child_incomplete"] = {
        "partial_red": [
            {"code": c, "quarter": q, "parent_item": p, "name": n,
             "missing_children": list(miss)}
            for c, q, p, n, miss in partial_child
        ],
        "full_absent_even_review": [
            {"code": c, "quarter": q, "parent_item": p, "name": n,
             "missing_children": list(miss)}
            for c, q, p, n, miss in full_absent_child
        ],
    }
    ratio_spikes = _ratio_series_spikes(records)
    report["ratio_series_spikes"] = [
        {"code": c, "quarter": q, "name": n, "value": x,
         "prev_quarter": qa, "prev": a, "next_quarter": qb, "next": b}
        for c, q, n, x, qa, a, qb, b in ratio_spikes
    ]
    trans_after = _transition_ratio_after_capture(records)
    report["transition_ratio_after_capture"] = [
        {"code": c, "quarter": q, "name": n, "item": it, "before": b, "after": a, "kind": k}
        for c, q, n, it, b, a, k in trans_after
    ]
    item12_copy = _item12_equals_item1(records)
    report["item12_equals_item1"] = [
        {"code": c, "quarter": q, "name": n, "value": v} for c, q, n, v in item12_copy
    ]
    mmult_mismatch, mmult_submissing, mmult_skipped, mmult_unverifiable = \
        _transition_mmult_after(records)
    # documented exception(잔차 박제) — 축 17 적용후의 같은 자기모순 1건을 차단집계에서만 뺀다.
    # **finding 자체는 지우지 않는다**: 아래 report/print 에 exempted 로 그대로 남는다.
    pmcp = _after_parent_missing_child_present(records)
    report["after_parent_missing_child_present"] = {
        "doc": ("부모후 결측 + 세부후 present = mmult 축 미가동 (review). parser 지목 사각 "
                "(inbox/parser/20260706T0502Z §2) — 2026-08-21 배선."),
        "review": [
            {"code": c, "quarter": q, "name": n, "parent_item": p,
             "children_present": np_, "children_total": nt, "derived_parent_r5": d}
            for c, q, n, p, np_, nt, d in pmcp
        ],
    }
    life8_ok, life8_red, life8_review, life8_detail = _life8_issuer_inconsistent(records)
    mmult_exempted = [row for row in mmult_mismatch
                      if row[3] == 17 and (row[0], row[1]) in life8_ok]
    mmult_mismatch = [row for row in mmult_mismatch if row not in mmult_exempted]
    report["transition_mmult_after"] = {
        "scope": "all 39 filers x 3 axes (15/17/19) — 2026-08-21 widened from 18 appliers x 2 axes",
        "mismatch_red": [
            {"code": c, "quarter": q, "name": n, "parent_item": p, "after": pv, "computed": ev}
            for c, q, n, p, pv, ev in mmult_mismatch
        ],
        "sub_missing_review": [
            {"code": c, "quarter": q, "name": n, "parent_item": p}
            for c, q, n, p in mmult_submissing
        ],
        "not_evaluated": dict(sorted(mmult_skipped.items())),
        "unverifiable_source": [
            {"code": c, "quarter": q, "name": n, "parent_item": p, "readability": tag}
            for c, q, n, p, tag in mmult_unverifiable
        ],
    }
    after_ident_fails, after_ident_skipped = _transition_identities_after(records)
    report["transition_identities_after"] = {
        "scope": "all 39 filers — 2026-08-21 widened from 18 appliers; tolerance now matches the pre-column engine",
        "red": [
            {"code": c, "quarter": q, "name": n, "rule": rule,
             "expected_after": e, "disclosed_after": a, "diff": diff}
            for c, q, n, rule, e, a, diff in after_ident_fails
        ],
        "not_evaluated": dict(sorted(after_ident_skipped.items())),
    }
    irr_after_fails, irr_after_skipped = _transition_irr_after(records)
    report["transition_irr_after"] = {
        "scope": "all 39 filers — 2026-08-21 new wiring (36_irr had no post-column check at all)",
        "red": [
            {"code": c, "quarter": q, "name": n, "after": a, "computed": e}
            for c, q, n, a, e in irr_after_fails
        ],
        "not_evaluated": dict(sorted(irr_after_skipped.items())),
    }
    irr_pin_detail, irr_pin_review = _irr_pin_recheck(records)
    report["irr_derive_issuer_inconsistent_exception"] = {
        "doc": ("36_irr documented exception (owner 2026-08-21) — blanket skip 이 아니라 기대잔차 박제. "
                "적용전(룰엔진 36_irr)·적용후(_transition_irr_after) 두 축이 각자 이 박제를 대조해 "
                "일치할 때만 차단하지 않는다. 잔차가 움직이거나 입력이 결측이면 다시 RED."),
        "registry": {f"{c}|{q}": pins
                     for (c, q), pins in IRR_DERIVE_ISSUER_INCONSISTENT.items()},
        "pin_tolerance": IRR_PIN_TOL,
        "residual_recheck": [
            {"code": c, "name": n, "quarter": q, "column": col,
             "pinned": p, "actual": a, "delta": d, "verdict": v}
            for c, n, q, col, p, a, d, v in irr_pin_detail
        ],
        "review": irr_pin_review,
    }
    other_cap_fails, other_cap_skipped = _other_capital_children_sum(records)
    report["other_capital_children_sum"] = {
        "scope": "all filers x both columns (값 / 값_적용후) — 2026-08-21 new wiring; "
                 "items 24/25/26 were referenced by no identity at all",
        "identity": "item23 = item24 + item25 + item26 (원문 행 라벨 'Ⅲ. 기타 요구자본(1+2+3)')",
        "red": [
            {"code": c, "quarter": q, "name": n, "column": col,
             "disclosed": tv, "expected": ev, "children": list(kids)}
            for c, q, n, col, tv, ev, kids in other_cap_fails
        ],
        "not_evaluated": dict(sorted(other_cap_skipped.items())),
    }
    after_incomplete, after_pinned_absent = _parent_present_child_incomplete_after(records)
    report["parent_present_child_incomplete_after"] = [
        {"code": c, "quarter": q, "parent_item": p, "name": n, "missing_children": list(miss)}
        for c, q, p, n, miss in after_incomplete
    ]
    report["parent_present_child_source_absent_pinned"] = dict(sorted(after_pinned_absent.items()))
    div_negative = _diversification_negative(records)
    report["diversification_negative"] = [
        {"code": c, "quarter": q, "name": n, "mode": mode, "value": v, "kind": k}
        for c, q, n, mode, v, k in div_negative
    ]
    axis_census = _axis_evaluation_census(records)
    axis_red, axis_review = _axis_eval_findings(axis_census)
    axis_mirror_red = _axis_mirror_findings(axis_census)
    report["axis_evaluation_census"] = {
        "doc": ("축 × 컬럼별 평가율. grid=적용전에 대상항목+입력 1개 이상이 실재하는 (회사,분기). "
                "미러(적용후=적용전)는 3분류: 비적용사=정의상 동일(정상) / 적용사·해당종류 미신청=정상 / "
                "적용사·해당종류 신청=오염 의심(AXIS_SELF_MIRRORED_APPLIER). "
                "effective=evaluated−오염의심 이 그 축이 실제로 확인해 준 칸 수다."),
        "mirror_applier_suspect": axis_mirror_red,
        "min_grid": _AXIS_MIN_GRID,
        "rate_floor": _AXIS_EVAL_RATE_FLOOR,
        "rows": [{k: v for k, v in r.items() if k != "mirror_cells"} for r in axis_census],
        "not_evaluated_red": [{"axis": r["axis"], "column": r["column"], "grid": r["grid"],
                               "evaluated": r["evaluated"], "mirrored": r["mirrored"]}
                              for r in axis_red],
        "rate_low_review": [{"axis": r["axis"], "column": r["column"], "grid": r["grid"],
                             "buckets": r["buckets"], "evaluated": r["evaluated"],
                             "rate": r["rate"], "rate_all": r["rate_all"],
                             "low_on": r["low_on"]}
                            for r in axis_review],
        "mirror_cells": {f'{r["axis"]}|{r["column"]}': [list(x) for x in r["mirror_cells"]]
                         for r in axis_census if r["mirrored"]},
    }
    taut_census, taut_drift = _identity_tautology_census(records)
    taut_red, taut_review, taut_exempt = _identity_tautology_findings(taut_census)
    # 경고 표시는 **면제 축도 포함**한다. 면제한 것은 push 차단이지 경고가 아니다 —
    # "FAIL 0" 이 찍히는 자리마다 "이 축은 통과해도 증거가 아니다" 가 같이 붙어야 한다.
    taut_red_axes = {(r["axis"], r["column"]) for r in taut_red + taut_exempt}
    report["identity_tautology"] = {
        "doc": ("가법 항등식 축의 **잔차 분포**. 억원으로 반올림된 표에서 부모−Σ자식이 정확히 0 인 "
                "비율은 반올림 잡음이 허용하는 범위(Irwin–Hall 귀무)를 넘을 수 없다. 넘으면 입력이 "
                "공시값이 아니라 파생값이고, 그 축의 'FAIL 0' 은 증거가 아니다. "
                "커버리지(변이시험)와는 다른 축 — 변이시험은 '룰이 이 칸을 본다'만 증명한다."),
        "excess_floor": _TAUT_EXCESS_FLOOR,
        "z_floor": _TAUT_Z_FLOOR,
        "min_cells": _TAUT_MIN_CELLS,
        "rows": taut_census,
        "red": [{"axis": r["axis"], "column": r["column"], "n": r["n"], "zeros": r["zeros"],
                 "zero_rate": r["zero_rate"], "null_rate": r["null_rate"],
                 "excess": r["excess"], "z": r["z"],
                 "verdict": "이 축의 FAIL 0 은 증거가 아니다 (동어반복)"} for r in taut_red],
        "review": [{"axis": r["axis"], "column": r["column"], "rule": r["rule"],
                    "why": r["why"], "n": r["n"], "excess": r["excess"], "z": r["z"]}
                   for r in taut_review],
        "spec_drift_red": taut_drift,
        "exempt": [{"axis": r["axis"], "column": r["column"], "n": r["n"], "zeros": r["zeros"],
                    "excess": r["excess"], "z": r["z"], "pin": r["pin"], "why": r["why"]}
                   for r in taut_exempt],
    }
    exempt_red, exempt_review = _exemption_provenance_findings()
    # 원장 ↔ 코드 박제 대조(2026-08-24). 어긋나면 RED — 원장 숫자를 아무도 안 읽던 구멍을 닫는다.
    pin_ledger_red = _pin_ledger_agreement_findings()
    exempt_red = exempt_red + pin_ledger_red
    # 부재 박제 셀단위 census + '값이 나타났다' review
    absence_detail, absence_red, absence_review = _absence_pin_census(records)
    exempt_red = exempt_red + absence_red
    exempt_review = exempt_review + absence_review
    # 마커 신뢰도 등급 census (행 귀속 검사 여부)
    marker_detail, marker_review = _marker_grade_census()
    exempt_review = exempt_review + marker_review
    report["exemption_provenance"] = {
        "ledger": str(_EXEMPTION_LEDGER.relative_to(ROOT)),
        "registries": {k: len(v) for k, v in sorted(_exemption_registries().items())},
        "red": exempt_red,
        "review": exempt_review,
        "pin_ledger_agreement": {
            "doc": ("코드 박제(게이트가 실제로 강제하는 것) == 원장 expected_residual/absent_cells. "
                    "정본은 코드이고 원장은 사본이다 — 어긋나면 RED."),
            "code_pins": {"|".join(k): v for k, v in sorted(_code_pin_map().items())},
            "red": pin_ledger_red,
        },
        "absence_pin_census": [
            {"registry": reg, "code": c, "quarter": q, "item": it, "column": col,
             "state": st, "value": v}
            for reg, c, q, it, col, st, v in absence_detail
        ],
        "marker_grades": {
            "doc": ("ANCHORED=행 귀속 검사(present_rows) · LABELLED=라벨 포함 · "
                    "UNIQUE=숫자만이나 인용페이지 1회 · AMBIGUOUS=숫자만·2회 이상"
                    "(= '값이 어딘가 있다' 만 검사 = 검사처럼 보이는 무검사)"),
            "totals": {k: sum(len(g[k]) for *_x, g in marker_detail)
                       for k in ("ANCHORED", "LABELLED", "UNIQUE", "AMBIGUOUS")},
            "by_entry": [{"registry": r, "code": c, "quarter": q, "grades": g}
                         for r, c, q, g in marker_detail],
        },
    }
    post_parent_red, post_parent_review, post_parent_pinned = _post_transition_parent_census(records)
    report["post_transition_parent_census"] = {
        "red": [{"code": c, "quarter": q, "name": n, "item": it,
                 "neighbor_q": nb, "kind": k} for c, q, n, it, nb, k in post_parent_red],
        "review_22_23": [{"code": c, "quarter": q, "name": n, "item": it,
                          "neighbor_q": nb, "kind": k} for c, q, n, it, nb, k in post_parent_review],
        "source_absent_pinned": dict(sorted(post_parent_pinned.items())),
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # stable-name 최신 포인터: glob 정렬 함정(stale report_latest.json) 방지 — 매 실행 fresh 덮어쓰기.
    (out_dir / "report_latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = report.get("summary", {})
    by_status = summary.get("by_status", {})
    red = int(by_status.get("RED", 0))
    yellow = int(by_status.get("YELLOW", 0))
    err = int(by_status.get("ERROR", 0))
    census_red = len(census["missing_rows"])

    # documented exception(잔차 박제) — 룰엔진 8_life RED 중 면제분만 **차단집계에서** 뺀다.
    # findings 매트릭스와 report 는 손대지 않는다: 골든이 고정하는 것도, 다음 사람이 읽는 것도
    # '룰이 무엇을 봤는가' 이고, 면제는 '그중 무엇을 차단하지 않기로 했는가' 라 층이 다르다.
    life8_exempt_findings = [
        f for f in findings
        if f.get("status") == "RED" and str(f.get("rule")) == "8_life"
        and (f.get(KEY_CODE), f.get(KEY_QUARTER)) in life8_ok
    ]
    for c, q in sorted(life8_ok):
        if not any((f.get(KEY_CODE), f.get(KEY_QUARTER)) == (c, q) for f in life8_exempt_findings):
            life8_review.append({"rule": "LIFE8_EXEMPTION_INERT", "code": c, "quarter": q,
                                 "detail": "잔차는 박제값과 일치하는데 그 셀에 8_life RED 가 없다 — "
                                           "룰 허용오차가 바뀌었거나 룰이 안 돌았다. 면제가 무용해졌으면 "
                                           "등재를 풀어라(면제가 남으면 그 자체가 사각지대다)"})
    # documented exception 3번째 — tier2/다리 축 발행사 자기모순(owner 위임 2026-08-24).
    # 같은 층에서 뺀다: findings 매트릭스는 손대지 않고 **차단집계에서만** 제외한다.
    tier2_accept, tier2_red, tier2_review, tier2_detail = _tier2_issuer_inconsistent(
        records, findings)
    tier2_exempt_ids = {id(f) for f in tier2_accept}
    # **RED 만 차감한다.** `_post` 축 박제는 YELLOW finding 을 받으므로(관계식 미확립 설계),
    # 그것까지 빼면 blocking RED 가 음수가 된다 — 2026-08-24 에 실제로 -2 가 찍혔다.
    # 면제는 등급을 바꾸지 않는다: YELLOW 박제는 '매 실행 재검산' 만 켜고 차단집계는 안 건드린다.
    tier2_accept_red = [f for f in tier2_accept if f.get("status") == "RED"]
    red_blocking = red - len(life8_exempt_findings) - len(tier2_accept_red)
    report["tier2_issuer_inconsistent_exception"] = {
        "doc": ("tier2/다리 축 발행사 자기모순 documented exception — blanket skip 이 아니라 "
                "**두 겹 박제**다. ① raw 로 판독한 마스터 셀을 매 실행 재확인(INPUT_DRIFT/"
                "INPUT_MISSING RED) ② 그 축이 실제로 그 잔차의 RED 를 내고 있는지 재확인"
                "(RESIDUAL_DRIFT RED · INERT review). 데이터가 움직여도, 룰이 움직여도 살아난다."),
        "registry": {
            f"{c}|{q}": {
                "cells": {f"item{it}": cols for it, cols in sorted(spec["cells"].items())},
                "findings": spec["findings"],
            }
            for (c, q), spec in sorted(_TIER2_ISSUER_INCONSISTENT.items())
        },
        "pin_tolerance": _TIER2_PIN_TOL,
        "residual_recheck": [
            {"code": c, "name": n, "quarter": q, "axis": rule,
             "pinned": p, "actual": a, "delta": d}
            for c, n, q, rule, p, a, d in tier2_detail
        ],
        "red": tier2_red,
        "review": tier2_review,
        "exempted_findings": [
            {"rule": f.get("rule"), "code": f.get(KEY_CODE), "quarter": f.get(KEY_QUARTER),
             "diff": f.get("diff"), "expected": f.get("expected"), "actual": f.get("actual")}
            for f in tier2_accept
        ],
        "not_registered": {
            "KR0068 2025.2Q": ("판정불가 유지. 단서 1건 — TFI 표 보완자본의 (적용후 − 적용전) = 825.75 가 "
                               "다리 잔차 826 과 반올림 이내로 같다. **인과는 못 박았다.** '거의 같다' 를 "
                               "근거로 면제하면 패턴을 원인으로 단정하는 것이다 — RED 로 남긴다"),
            "KR0032 2025.4Q": ("표가 실제로는 닫힌다: 697,899 + 447,254 + 94,959(기발행 후순위채무) "
                               "= 1,240,112 = 공시 보완자본. 잔차 949.59억이 그 행과 정확히 같다 — "
                               "발행사 자기모순이 아니라 룰/적재 커버리지 결손이라 면제 대상이 아니다"),
            "KR0075 2024.3Q": ("2024.4Q·2025.1Q 와 **증거가 동일**하다(같은 표 구조·같은 지문, "
                               "잔차 −220.98/−221.31, gap 14.53). 그런데 owner 위임 목록에 없어서 "
                               "등재하지 않았다 — 면제를 스스로 넓히지 않는다. 다음 라운드 승인 대상"),
            # 2026-08-25 제거: "KR0004 2025.1Q"·"KR0003 2023.1Q" 는 이 dict 에 stale 하게 남아
            # "확정 전"/"owner 위임 목록 밖"이라 적고 있었으나 실제로는 두 버킷 다
            # `_TIER2_ISSUER_INCONSISTENT`(L2024/L2325)에 이미 등록돼 있다(재감사보고서
            # artifacts/validation/reaudit_20260824_KR0003_KR0004.md F2 가 지적한 stale 산문 —
            # "다음 세션이 이 버킷은 면제가 아니다로 읽는 함정"). 차단집계 로직에는 영향 없었지만
            # (`not_registered` 는 리포트 산문일 뿐, `_TIER2_ISSUER_INCONSISTENT` 등록만 실제로
            # 차단여부를 정한다) 리포트 판독자를 오도하므로 이 항목만 제거한다(나머지 3건은
            # 실제로 미등록이라 그대로 둔다).
        },
    }
    report["life8_issuer_inconsistent_exception"] = {
        "doc": ("발행사 자기모순 documented exception — blanket skip 이 아니라 기대잔차 박제. "
                "적용전·적용후 두 컬럼 모두 박제값과 일치할 때만 차단집계에서 뺀다. 잔차가 움직이면 "
                "면제가 깨지고 다시 RED."),
        "registry": {f"{c}|{q}": pins for (c, q), pins in _LIFE8_ISSUER_INCONSISTENT.items()},
        "pin_tolerance": _LIFE8_PIN_TOL,
        "accepted": [{"code": c, "quarter": q} for c, q in sorted(life8_ok)],
        "residual_recheck": [
            {"code": c, "name": n, "quarter": q, "column": col,
             "pinned": p, "actual": a, "delta": d}
            for c, n, q, col, p, a, d in life8_detail
        ],
        "red": life8_red,
        "review": life8_review,
        "exempted_findings": {
            "rule_8_life_적용전": [
                {"code": f.get(KEY_CODE), "quarter": f.get(KEY_QUARTER), "diff": f.get("diff")}
                for f in life8_exempt_findings
            ],
            "mmult_item17_적용후": [
                {"code": c, "quarter": q, "name": n, "after": pv, "computed": ev}
                for c, q, n, _p, pv, ev in mmult_exempted
            ],
        },
    }

    # 면제 두 블록은 위 write 이후에 붙는다 → **다시 쓴다.** 안 그러면 콘솔에는 "무엇을 차단하지
    # 않았는가" 가 찍히는데 디스크 아티팩트에는 없다 — 게이트가 말하는 것과 남기는 것이 달라지는
    # 그 자리다(2026-08-24 발견: `life8_issuer_inconsistent_exception` 도 그동안 디스크에 없었다).
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "report_latest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    fail_by_rule = Counter(f.get("rule") for f in findings if f.get("status") == "RED")
    print(f"K-ICS validation report: {out_path}")
    print(
        f"Status counts: RED={red} YELLOW={yellow} GREEN={by_status.get('GREEN', 0)} "
        f"SKIP={by_status.get('SKIP', 0)} ERROR={err}"
    )
    if _LIFE8_ISSUER_INCONSISTENT:
        print(f"  documented exception (발행사 자기모순, 잔차 박제): "
              f"blocking RED={red_blocking} (= {red} − 8_life {len(life8_exempt_findings)}건 "
              f"− tier2 RED {len(tier2_accept_red)}건; tier2 YELLOW 박제 "
              f"{len(tier2_accept) - len(tier2_accept_red)}건은 차감 대상 아님) "
              f"· 적용후 mmult item17 면제 {len(mmult_exempted)}건")
        for c, n, q, col, p, a, d in life8_detail:
            print(f"    {q} {c} {n} [{col}] 박제잔차={p} 실측={a} Δ={d:+} "
                  f"(tol {_LIFE8_PIN_TOL}) → {'일치' if abs(d) <= _LIFE8_PIN_TOL else 'DRIFT'}")
        for r in life8_red:
            print(f"    RED [{r['rule']}] {r.get('quarter')} {r.get('code')}: {r.get('detail')}")
        for r in life8_review:
            print(f"    REVIEW [{r['rule']}] {r.get('quarter')} {r.get('code')}: {r.get('detail')}")
    if _TIER2_ISSUER_INCONSISTENT:
        print(f"  tier2/다리 발행사 자기모순 documented exception (잔차 박제, 두 겹): "
              f"{len(_TIER2_ISSUER_INCONSISTENT)}버킷 · finding {len(tier2_accept)}건 재검산"
              f"(그중 RED 면제 {len(tier2_accept_red)}건)")
        for c, n, q, rule, p, a, d in tier2_detail:
            verdict = ("일치" if (p is None and a is None)
                       else "DRIFT" if (p is None or a is None or abs(d) > _TIER2_PIN_TOL)
                       else "일치")
            shown = "census flag(잔차 없음)" if p is None else f"박제잔차={p} 실측={a} Δ={d:+}"
            print(f"    {q} {c} {n} [{rule}] {shown} (tol {_TIER2_PIN_TOL}) → {verdict}")
        for r in tier2_red:
            print(f"    RED [{r['rule']}] {r.get('quarter')} {r.get('code')}"
                  f"{' item' + str(r['item']) if r.get('item') else ''}"
                  f"{' ' + r['axis'] if r.get('axis') else ''}: {r.get('detail')}")
        for r in tier2_review:
            print(f"    REVIEW [{r['rule']}] {r.get('quarter')} {r.get('code')} "
                  f"{r.get('axis', '')}: {r.get('detail')}")
    print(
        f"Coverage census: regular_filers={census['regular_filers']} "
        f"median/q={census['median_filers_per_q']} "
        f"MISSING_CELLS(RED)={census_red} "
        f"collapsed_quarters={census['collapsed_quarters']}"
    )
    if census["missing_rows"]:
        by_q_missing = Counter(q for q, _, _ in census["missing_rows"])
        print("  missing filers by quarter:")
        for q, cnt in sorted(by_q_missing.items()):
            sample = ", ".join(
                n for qq, _, n in census["missing_rows"] if qq == q
            )
            print(f"    {q}: {cnt} missing — {sample[:160]}")
    if tooling_fail:
        print(f"Market localizer TOOLING_FAIL (re-localize, still-gap): {len(tooling_fail)}")
        for c, q, s, n in tooling_fail:
            print(f"    {q} {c} {n} [{s}] — item19 공시·36-40 결측, localizer 실패 → re-localize")
    else:
        print("Market localizer TOOLING_FAIL: 0 (nonok 셀 전부 백필됨 또는 비-갭)")
    if parent_child:
        print(f"Parent-zero / nonzero-child (structural misparse, RED): {len(parent_child)}")
        for c, q, p, n, nz in parent_child:
            kids = ", ".join(f"item{k}={v}" for k, v in nz)
            print(f"    {q} {c} {n}: 부모 item{p}=0 인데 자식 {kids} → 행 오정렬/셀 밀림")
    else:
        print("Parent-zero / nonzero-child: 0")
    if partial_child:
        print(f"Parent-present / child-incomplete PARTIAL (material misparse, RED): {len(partial_child)}")
        for c, q, p, n, miss in partial_child:
            kids = ", ".join(f"item{k}" for k in miss)
            print(f"    {q} {c} {n}: 부모 item{p}>0 인데 평소보고 자식 {kids} 결측 → 행 누락")
    else:
        print("Parent-present / child-incomplete PARTIAL: 0")
    if full_absent_child:
        print(f"Parent-present / child FULL-ABSENT even-Q (source-check review, non-blocking): {len(full_absent_child)}")
        for c, q, p, n, miss in full_absent_child:
            print(f"    {q} {c} {n}: 부모 item{p}>0·자식 전부결측 → 원천표 확인 필요")
    if ratio_spikes:
        print(f"지급여력비율(item27) series spikes (YELLOW, non-blocking): {len(ratio_spikes)}")
        for c, q, n, x, qa, a, qb, b in ratio_spikes:
            print(f"    {q} {c} {n}: {x} (인접 {qa}={a}, {qb}={b}) → 소스오염 의심")
    else:
        print("지급여력비율(item27) series spikes: 0")
    if trans_after:
        kc = Counter(k for *_, k in trans_after)
        ic = Counter(it for _, _, _, it, *_ in trans_after)
        print(f"선택경과조치 적용후 유실/부정합 ({len(_TRANSITION_APPLIERS)}적용사 item27·28, RED): {len(trans_after)} "
              f"[COPY={kc.get('COPY',0)} MISSING={kc.get('MISSING',0)} "
              f"LOWER={kc.get('LOWER',0)} AMT_MISMATCH={kc.get('AMT_MISMATCH',0)}] "
              f"(item27={ic.get(27,0)} item28={ic.get(28,0)})")
        for c, q, n, it, b, a, k in trans_after[:25]:
            if k == "AMT_MISMATCH":
                print(f"    {q} {c} {n} item{it}후={a} ≠ 금액후도출 {b} [AMT_MISMATCH] → 비율만 패치·금액후 미수정")
            else:
                print(f"    {q} {c} {n} item{it}: 전={b} 후={a} [{k}] → 적용후 유실/복사 (선택경과조치사는 후>전)")
        if len(trans_after) > 25:
            print(f"    ... +{len(trans_after) - 25} more")
    else:
        print("선택경과조치 적용후 유실/부정합 (item27·28): 0")
    if item12_copy:
        print(f"item12=item1 셀밀림 (불인정항목에 지급여력금액 복사, RED): {len(item12_copy)}")
        for c, q, n, v in item12_copy[:20]:
            print(f"    {q} {c} {n}: item12={v} = item1 → 셀밀림/미스매핑")
    else:
        print("item12=item1 셀밀림: 0")
    if mmult_mismatch:
        print(f"적용후 mmult 불일치 (item15/17/19후 ≠ 계산값, 전사 39사, RED): {len(mmult_mismatch)}")
        for c, q, n, p, pv, ev in mmult_mismatch[:20]:
            print(f"    {q} {c} {n} item{p}후: 공시={pv} 계산={ev} → 적용후 세부 미정합")
    else:
        print("적용후 mmult 불일치 (item15/17/19, 전사 39사): 0")
    print(f"    [적용후 mmult 미판정 내역] {dict(sorted(mmult_skipped.items()))}")
    if pmcp:
        print(f"적용후 부모결측·세부present (mmult 미가동 = 세부후 무검사, review): {len(pmcp)}")
        for c, q, n, p, np_, nt, d in pmcp[:20]:
            print(f"    {q} {c} {n} item{p}후 결측인데 세부후 {np_}/{nt} present"
                  + (f" · R5 역산 부모후≈{d}" if d is not None else " · 역산 앵커 없음"))
    else:
        print("적용후 부모결측·세부present (mmult 미가동): 0")
    if mmult_unverifiable:
        ucq = sorted({(c, q, n, tag) for c, q, n, _p, tag in mmult_unverifiable})
        tc = Counter(tag for *_x, tag in mmult_unverifiable)
        print(f"적용후 '후=전' 중 **원천 판독불가라 정당하다고 말할 수 없는** 칸: "
              f"{len(mmult_unverifiable)}칸 / {len(ucq)}(회사,분기) {dict(tc)}")
        print("    (종전엔 이 칸들이 '구조적으로 정당' 버킷에 섞여 있었다 — 확인한 게 아니라 못 읽은 것)")
        for c, q, n, tag in ucq:
            print(f"    {q} {c} {n} [{tag}] → OCR/재수집 없이는 적용후 세부를 판정할 수 없음")
    if mmult_submissing:
        print(f"적용후 세부위험 추출갭 (부모후≠전인데 세부후 결측, review): {len(mmult_submissing)}")
    if irr_after_fails:
        print(f"적용후 36_irr 불일치 (item36후 ≠ 시나리오후 도출, 전사 39사, RED): {len(irr_after_fails)}")
        for c, q, n, a, e in irr_after_fails[:20]:
            print(f"    {q} {c} {n} item36후: 공시={a} 계산={e}")
    else:
        print("적용후 36_irr 불일치 (전사 39사): 0")
    print(f"    [적용후 36_irr 미판정 내역] {dict(sorted(irr_after_skipped.items()))}")
    if IRR_DERIVE_ISSUER_INCONSISTENT:
        print(f"36_irr documented exception (재현식 미적용, 잔차 박제) {len(IRR_DERIVE_ISSUER_INCONSISTENT)}건 "
              f"— 적용전·적용후 각각 재검산 (tol {IRR_PIN_TOL}):")
        for c, n, q, col, p, a, d, verdict in irr_pin_detail:
            print(f"    {q} {c} {n} [{col}] 박제잔차={p} 실측={a} Δ={d if d is None else f'{d:+}'} → {verdict}")
        for r in irr_pin_review:
            print(f"    REVIEW [{r['rule']}] {r.get('quarter')} {r.get('code')}: {r.get('detail')}")
    if after_ident_fails:
        ic = Counter(rule for _, _, _, rule, *_ in after_ident_fails)
        print(f"적용후 항등식 위반 (전사 39사 R1/R2/R5/R6/R7/R8후 안 닫힘, RED): {len(after_ident_fails)} {dict(ic)}")
        for c, q, n, rule, e, a, diff in after_ident_fails[:25]:
            print(f"    {q} {c} {n} [{rule}] 공시후={a} 계산후={e} diff={diff}")
        if len(after_ident_fails) > 25:
            print(f"    ... +{len(after_ident_fails) - 25} more")
    else:
        print("적용후 항등식 위반 (전사 39사): 0")
    print(f"    [적용후 항등식 미판정 내역] {dict(sorted(after_ident_skipped.items()))}")
    if taut_red_axes:
        print(f"    ⚠ 위 '위반 0' 중 **동어반복으로 판정된 축은 증거가 아니다**: "
              f"{sorted(f'{a}[{c}]' for a, c in taut_red_axes)} — 아래 동어반복 검사 참조")
    if other_cap_fails:
        cc = Counter(col for *_x, col, _t, _e, _k in other_cap_fails)
        print(f"기타요구자본 분해 위반 (item23 ≠ item24+25+26, 전·후 양컬럼, RED): "
              f"{len(other_cap_fails)} {dict(cc)}")
        for c, q, n, col, tv, ev, kids in other_cap_fails[:25]:
            print(f"    {q} {c} {n} [{col}] item23={tv} ≠ 24+25+26={ev} {list(kids)}")
        if len(other_cap_fails) > 25:
            print(f"    ... +{len(other_cap_fails) - 25} more")
    else:
        print("기타요구자본 분해 위반 (item23 = item24+25+26, 전·후 양컬럼): 0")
    print(f"    [기타요구자본 미판정 내역] {dict(sorted(other_cap_skipped.items()))}")
    if after_incomplete:
        pc = Counter(p for _, _, p, _, _ in after_incomplete)
        PLBL = {15: "요구자본(16~21)", 17: "생명장기(29~35)", 19: "시장(36~40)"}
        print(f"적용후 하위 census 결측 (부모후 present·기대자식후 결측, RED): {len(after_incomplete)} "
              f"{{{', '.join(f'{PLBL.get(p,p)}:{n}' for p, n in sorted(pc.items()))}}}")
        for c, q, p, n, miss in after_incomplete[:30]:
            kids = ", ".join(f"item{k}" for k in miss)
            print(f"    {q} {c} {n}: 부모item{p}후 present인데 {kids}후 결측 → 적용후 부분충전")
        if len(after_incomplete) > 30:
            print(f"    ... +{len(after_incomplete) - 30} more")
    else:
        print("적용후 하위 census 결측: 0")
    if after_pinned_absent:
        print(f"    [부재 박제로 기대목록에서 제외된 자식후 셀] {dict(after_pinned_absent)}")
    if div_negative:
        print(f"분산효과(item16) 음수 (물리적 불가능, 구성요소 과소/기준금액 과대 misparse, RED): {len(div_negative)}")
        for c, q, n, mode, v, k in div_negative:
            print(f"    {q} {c} {n} [{mode}]: {v} [{k}] → 분산효과<0")
    else:
        print("분산효과(item16) 음수: 0")
    if post_parent_red:
        pc = Counter((c, q) for c, q, *_ in post_parent_red)
        kc = Counter(k for *_, k in post_parent_red)
        print(f"적용후 요구자본 부모 continuity break (적용후 공시하다 갑자기 결측=추출갭, RED): "
              f"{len(post_parent_red)}셀 / {len(pc)}(회사,분기) "
              f"[TRAILING={kc.get('TRAILING',0)} SANDWICHED={kc.get('SANDWICHED',0)}]")
        bycq = defaultdict(lambda: ["", []])
        for c, q, n, it, nb, k in post_parent_red:
            bycq[(q, c, n)][0] = k
            bycq[(q, c, n)][1].append(it)
        for (q, c, n), (k, its) in sorted(bycq.items()):
            print(f"    {q} {c} {n} [{k}]: item{sorted(its)}후 결측 (인접분기 적용후 present → 표 유실)")
    else:
        print("적용후 요구자본 부모 continuity break: 0")
    if post_parent_pinned:
        print(f"    [부재 박제로 continuity 에서 제외된 셀] {dict(post_parent_pinned)}")
    if post_parent_review:
        print(f"적용후 조정항목(22법인세·23기타요구자본) 단독 continuity break (종속회사/법인세 legit-absent "
              f"가능, 비차단 review): {len(post_parent_review)}")
        for c, q, n, it, nb, k in post_parent_review:
            print(f"    {q} {c} {n} item{it}후 결측 [{k}] → 원천확인(단독=코어 break 없음)")
    # ---- 메타룰: 축별 평가율 / 자기미러 (owner 2026-08-21) ----------------------------
    print("축별 평가율 — 미러 3분류: 미적용사=정의상 동일(정상) / 적용사·해당종류 미신청=정상 / "
          "적용사·신청=오염의심. 실질=평가−오염의심.")
    print(f"    분모 '범위' = 그 축이 구조적으로 적용되는 (회사,분기) — `*` 표시는 전 버킷"
          f"({axis_census[0]['buckets_all'] if axis_census else 0})보다 좁혀졌다는 뜻이다"
          f"(36_irr=짝수분기 한정 · 적용후 순자산/시나리오=경과조치 비적용사 한정). "
          f"좁힌 범위 안의 미평가 칸은 아래에 이름으로 인쇄된다:")
    scope_gaps = [r for r in axis_census if r.get("scoped") and r.get("scope_missing_n")]
    for r in scope_gaps:
        cells = ", ".join(f"{c} {q}" for c, q in r["scope_missing"][:12])
        print(f"      · {r['axis']} [{r['column']}] 범위 {r['buckets']} 중 미평가 "
              f"{r['scope_missing_n']}건 — {cells}"
              + (" ..." if r["scope_missing_n"] > 12 else ""))
    if not scope_gaps:
        print("      · 범위 제한 축 전부 잔여 미평가 0건")
    for r in axis_census:
        if r["grid"] == 0:
            continue
        rate = f"{100*r['rate']:5.1f}%" if r["rate"] is not None else "   n/a"
        rall = f"{100*r['rate_all']:5.1f}%" if r["rate_all"] is not None else "   n/a"
        eff = f"{100*r['effective_rate']:5.1f}%" if r["effective_rate"] is not None else "   n/a"
        ind = f"{100*r['independent_rate']:5.1f}%" if r["independent_rate"] is not None else "   n/a"
        flag = ""
        if r["grid"] >= _AXIS_MIN_GRID and r["effective"] == 0:
            flag = "  <<< RED 실질평가 0칸 (이 축의 'FAIL 0' 은 증거가 아니다)"
        elif r["grid"] >= _AXIS_MIN_GRID and any(
                r[k] is not None and r[k] < _AXIS_EVAL_RATE_FLOOR for k in ("rate", "rate_all")):
            flag = f"  <<< REVIEW 평가율 {int(_AXIS_EVAL_RATE_FLOOR*100)}% 미만"
        # 평가율이 100% 여도 그 축이 동어반복이면 판정 자체가 무의미하다 — 두 표시는 배타가 아니다.
        if (r["axis"], r["column"]) in taut_red_axes:
            flag += "  <<< 동어반복 (평가율과 무관하게 증거 아님)"
        scope_tag = (f"{r['buckets']}*" if r.get("scoped") else f"{r['buckets']}")
        print(f"    {r['axis']:<22s} {r['column']}  grid={r['grid']:>3}/{scope_tag:<5s} "
              f"평가={r['evaluated']:>3}(grid {rate} · 범위 {rall})  "
              f"미러[정의상 {r['mirror_nonapplier']:>3} · 정상 {r['mirror_applier_legit']:>3} · "
              f"의심 {r['mirror_applier_suspect']:>2}]  면제={r['exempt']:>2}  "
              f"실질={r['effective']:>3}({eff}) 독립={r['independent']:>3}({ind}){flag}")
    if axis_mirror_red:
        print(f"적용사 미러링 오염 — AXIS_SELF_MIRRORED_APPLIER (경과조치 신청 종류가 그 축을 "
              f"움직여야 하는데 후=전, RED): {len(axis_mirror_red)}")
        for f in axis_mirror_red[:30]:
            print(f"    {f['quarter']} {f['code']} {f['axis']}[{f['column']}] "
                  f"신청종류={f['kinds']} → 적용후가 적용전과 한 자리도 다르지 않음(복사 지문)")
    else:
        print("적용사 미러링 오염 (AXIS_SELF_MIRRORED_APPLIER): 0 "
              "— 비적용사·비신청 적용사의 후=전은 정의/정상이라 세지 않는다")
    if axis_red:
        print(f"축 평가율 RED — AXIS_NOT_EVALUATED (실질 평가 0칸, blocking): {len(axis_red)}")
        for r in axis_red:
            why = ("계산된 칸이 전부 적용사 미러링 오염"
                   if r["mirror_applier_suspect"] and r["mirror_applier_suspect"] == r["evaluated"]
                   else "계산가능 칸 자체가 0")
            print(f"    {r['axis']} [{r['column']}] grid={r['grid']} 평가={r['evaluated']} "
                  f"오염의심={r['mirror_applier_suspect']} → {why}")
    else:
        print("축 평가율 RED (AXIS_NOT_EVALUATED): 0")
    if axis_review:
        print(f"축 평가율 REVIEW — AXIS_EVAL_RATE_LOW (<{int(_AXIS_EVAL_RATE_FLOOR*100)}%, 비차단): "
              f"{len(axis_review)}")
        for r in axis_review:
            print(f"    {r['axis']} [{r['column']}] 평가 {r['evaluated']}칸 — "
                  f"입력실재(grid {r['grid']}) 기준 {100*r['rate']:.1f}% / "
                  f"구조범위({r['buckets']}) 기준 {100*r['rate_all']:.1f}% "
                  f"(바닥 뚫은 분모: {r['low_on']}, 범위 내 미평가 {r['scope_missing_n']}건)")
    # ---- 메타룰: 동어반복(IDENTITY_TAUTOLOGY) ------------------------------------------
    print(f"항등식 동어반복 검사 — 잔차 '정확히 0' 비율 vs 반올림 귀무(Irwin–Hall). "
          f"임계 excess≥{_TAUT_EXCESS_FLOOR} 및 z≥{_TAUT_Z_FLOOR} (둘 다, 실측 보정):")
    for r in sorted(taut_census, key=lambda x: -(x["excess"] or 0)):
        if r["n"] == 0:
            print(f"    {r['axis']:<22s} {r['column']}  판정가능 0칸 "
                  f"(퇴화 {r['degenerate']} · 입력결측 {r['incomplete']})  <<< UNDERPOWERED")
            continue
        mark = ""
        if (r["axis"], r["column"]) in taut_red_axes:
            mark = "  <<< RED 동어반복 — 이 축의 'FAIL 0' 은 증거가 아니다"
        elif any(v["axis"] == r["axis"] and v["column"] == r["column"] for v in taut_review):
            mark = "  <<< REVIEW"
        print(f"    {r['axis']:<22s} {r['column']}  n={r['n']:>3}  "
              f"정확0={r['zeros']:>3}({100*r['zero_rate']:5.1f}%)  귀무={100*r['null_rate']:5.1f}%  "
              f"excess={r['excess']:4.2f}  z={r['z']:6.1f}  "
              f"k_eff={r['k_eff_hist']}{mark}")
    if taut_drift:
        print(f"동어반복 축 정의 불일치 (TAUTOLOGY_AXIS_SPEC_DRIFT, RED): {len(taut_drift)}")
        for d in taut_drift:
            print(f"    {d['axis']}: {d['detail']}")
    if taut_exempt:
        print(f"동어반복 documented exception (owner 2026-08-21, 상한 박제): {len(taut_exempt)}"
              f"  — **경고는 유지, push 차단만 면제**")
        for r in taut_exempt:
            print(f"    {r['axis']} [{r['column']}] — {r['n']}칸 중 {r['zeros']}칸 잔차 정확히 0 "
                  f"({r['zero_rate'] * 100:.1f}%, 귀무 {r['null_rate'] * 100:.1f}%, "
                  f"excess {r['excess']:.2f}, z {r['z']:.1f}). {r['why']}")
            print(f"      해제조건: R2 되맞춤 원인 규명 (inbox/validation/20260821T1830Z). "
                  f"이 축이 통과해도 증거가 아니라는 사실은 그대로다.")
    if taut_red:
        print(f"동어반복 RED — IDENTITY_TAUTOLOGY (blocking): {len(taut_red)}")
        for r in taut_red:
            ex = ", ".join(f"{c} {q} r={v:+g}" for c, q, v in r["nonzero_examples"]) or "없음"
            print(f"    {r['axis']} [{r['column']}] — {r['n']}칸 중 {r['zeros']}칸이 잔차 정확히 0 "
                  f"({100*r['zero_rate']:.1f}%, 반올림 귀무 {100*r['null_rate']:.1f}%, "
                  f"excess {r['excess']:.2f}, z {r['z']:.1f}). "
                  f"**이 축이 통과해도 의미 없다** — 대상값이 입력으로부터 되맞춰져 있다. "
                  f"0 아닌 잔차 표본: {ex}")
    else:
        print("동어반복 RED (IDENTITY_TAUTOLOGY): 0")
    for r in taut_review:
        print(f"    REVIEW [{r['rule']}] {r['axis']} [{r['column']}]: {r['why']} "
              f"(n={r['n']}, excess={r['excess'] if r['excess'] is None else round(r['excess'], 2)}, "
              f"z={r['z'] if r['z'] is None else round(r['z'], 1)})")
    # ---- 메타룰: 면제 근거(provenance) ------------------------------------------------
    if absence_detail:
        miss = sum(1 for *_x, st, _v in absence_detail if st == "결측")
        pres = len(absence_detail) - miss
        print(f"부재형 면제 — 셀단위 부재 박제 census: {len(absence_detail)}셀 "
              f"(결측 {miss} · 값존재 {pres}) / {len({(r, c, q) for r, c, q, *_ in absence_detail})}버킷")
        for reg, c, q, it, col, st, v in absence_detail:
            print(f"    {q} {c} item{it}{col[-1]} [{reg}] {st}"
                  + ("" if v is None else f"={v:g} → 파생값, 해당 축 검산 라이브"))
    if marker_detail:
        tot = {k: sum(len(g[k]) for *_x, g in marker_detail)
               for k in ("ANCHORED", "LABELLED", "UNIQUE", "AMBIGUOUS")}
        print(f"면제 근거 마커 신뢰도 등급: {tot} "
              f"(AMBIGUOUS = 숫자만·인용페이지 2회 이상 → 행 귀속 미검사)")
        amb = [(r, c, q, g) for r, c, q, g in marker_detail if g["AMBIGUOUS"]]
        for r, c, q, g in amb:
            print(f"    {q} {c}: ANCHORED={len(g['ANCHORED'])} 잔여 AMBIGUOUS "
                  f"{g['AMBIGUOUS']}")
    if exempt_red or exempt_review:
        rc = Counter(f["rule"] for f in exempt_red)
        print(f"면제 근거(provenance) 검사: RED={len(exempt_red)} {dict(rc)} "
              f"REVIEW={len(exempt_review)}")
        for f in exempt_red:
            print(f"    RED    [{f['rule']}] {f['registry']} {f.get('code')} {f.get('quarter')}: "
                  f"{f['detail']}")
        for f in exempt_review[:20]:
            print(f"    REVIEW [{f['rule']}] {f['registry']} {f.get('code')} {f.get('quarter')}: "
                  f"{f['detail']}")
    else:
        print("면제 근거(provenance) 검사: 전 면제 항목이 기계검증 가능한 인용을 갖고 있음")
    print("RED failures by rule:")
    for rule_id, cnt in sorted(fail_by_rule.items(), key=lambda x: (-x[1], x[0])):
        print(f"  rule {rule_id}: {cnt}")
    _print_tier2_axis_report(findings)

    print("Top RED offenders:")
    for row in _top_offenders(findings, "RED", limit=10):
        print(f"  rule {row['rule']} {row['code']} {row['quarter']} diff={row['diff']}")

    spot = report["spot_check"]["findings"]
    spot_red = [f for f in spot if f.get("status") == "RED"]
    print(
        f"Spot-check {SPOT_CODE} {SPOT_QUARTER} ({SPOT_NAME_HINT}): "
        f"{len(spot)} results, RED={len(spot_red)}"
    )
    for f in spot:
        if f.get("status") == "RED":
            print(
                f"  RED rule {f.get('rule')}: expected={f.get('expected')} "
                f"actual={f.get('actual')} diff={f.get('diff')}"
            )

    # `red_blocking` = 룰엔진 RED − documented exception(잔차 박제로 매 실행 재확인된 것만).
    # 면제가 깨지면 `life8_red` 가 대신 차단한다 — 면제는 검사를 끄는 게 아니라 조건부로 미룬다.
    return 2 if (red_blocking > 0 or census_red > 0 or parent_child or partial_child
                 or trans_after or item12_copy or mmult_mismatch or after_ident_fails
                 or irr_after_fails or other_cap_fails
                 or after_incomplete or div_negative or post_parent_red
                 # 메타룰(2026-08-21): 판정하지 않은 축·적용사 미러링 오염·근거 없는 면제는 '통과'가 아니다.
                 or axis_red or axis_mirror_red or exempt_red or life8_red or tier2_red
                 # 동어반복 축의 'FAIL 0' 도 통과가 아니다 — 되맞춘 값은 룰을 영원히 통과시킨다.
                 or taut_red or taut_drift) else 0


if __name__ == "__main__":
    raise SystemExit(main())
