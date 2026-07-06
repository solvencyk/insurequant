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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import (
    KEY_CODE,
    KEY_ITEM,
    KEY_NAME,
    KEY_QUARTER,
    KEY_VALUE,
    KEY_VALUE_POST,
    run_validation,
)

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
    → RED. 공통 경과조치사(18사 외)는 후=전이어도 정상이라 검사 안 함.
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
                if abs(a - b) < _trans_margin(b):
                    out.append((c, q, name.get(c, c), ratio_it, b, a, "COPY"))
                    continue
                if b >= 0 and a < b:
                    out.append((c, q, name.get(c, c), ratio_it, b, a, "LOWER"))
                    continue
                an = qvn.get(q, (None, None))[1]
                ad = qvd.get(q, (None, None))[1]
                if an is not None and ad not in (None, 0):
                    derived = an / ad * 100.0
                    if abs(derived - a) > 2.0:
                        out.append((c, q, name.get(c, c), ratio_it, round(derived, 2), a,
                                    "AMT_MISMATCH"))
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp949
    except Exception:
        pass
    src = ROOT / "kics_disclosure.json"
    records = _load_records(src)
    report = run_validation(records, source_has_breakdown=_scan_breakdown_presence(records))
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
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # stable-name 최신 포인터: glob 정렬 함정(stale report_latest.json) 방지 — 매 실행 fresh 덮어쓰기.
    (out_dir / "report_latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = report.get("summary", {})
    by_status = summary.get("by_status", {})
    red = int(by_status.get("RED", 0))
    yellow = int(by_status.get("YELLOW", 0))
    err = int(by_status.get("ERROR", 0))
    census_red = len(census["missing_rows"])

    fail_by_rule = Counter(f.get("rule") for f in findings if f.get("status") == "RED")
    print(f"K-ICS validation report: {out_path}")
    print(
        f"Status counts: RED={red} YELLOW={yellow} GREEN={by_status.get('GREEN', 0)} "
        f"SKIP={by_status.get('SKIP', 0)} ERROR={err}"
    )
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
    print("RED failures by rule:")
    for rule_id, cnt in sorted(fail_by_rule.items(), key=lambda x: (-x[1], x[0])):
        print(f"  rule {rule_id}: {cnt}")
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

    return 2 if (red > 0 or census_red > 0 or parent_child or partial_child or trans_after) else 0


if __name__ == "__main__":
    raise SystemExit(main())
