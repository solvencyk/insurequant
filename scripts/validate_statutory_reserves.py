#!/usr/bin/env python3
"""법정준비금(IFRS17_BS 항목 5/6/7/8) 검증 룰 R-RSV-1~12.

owner 발주: `inbox/validation/20260819T0558Z__owner__MULTI__statutory_reserve_rules.md`.
대상 = `IFRS17_BS.json` 의 `준비금` 섹션 4종
  5 해약환급금준비금 · 6 비상위험준비금 · 7 대손준비금 · 8 보증준비금

## 왜 부호 룰(R-RSV-2/3)이 여기서 "마스터만" 보는가 — 설계 결정 (2026-08-20)

owner 룰 원문은 R-RSV-2/3 을 "괄호·△ = 음수" 전제로 썼다. **그 전제만으로 raw 를 다시 읽으면
틀린다.** 2026-08-19 에 validation 이 그렇게 해서 NH농협손해보험 2026.2Q 비상위험준비금을
297,481 이라고 발주했고, parser 가 반박해 정답이 309,489 로 확정됐다 — 조정이익 프레임 표
(`반영전 순이익 / 적립 예정금액 / 반영후 조정이익`) 의 괄호는 **"이익에서 차감"** 표기이고
준비금은 그만큼 **증가**한다(표 안 산수로 확정: 71,666 − 6,004 = 65,662).

그런데 그 반전 규칙조차 보편적이지 않다. `build_equity_composition_tier2.py:495` 실측:

    if net_income_framed and concept != "보증준비금":   # 보증준비금은 반전 제외
        v = -v

보증준비금은 반대 사례(한화생명 FY2023)가 있어 프레임 반전을 걸면 오히려 깨진다. 즉
**부호 해석은 개념별·표별로 갈리고, 그 지식은 이미 빌더에 있다.** 게이트가 그걸 재구현하면
두 벌이 갈라지고, 갈라진 쪽이 틀렸을 때 게이트가 옳은 데이터를 RED 로 막는다.

**그래서 이 모듈은 raw 부호를 다시 해석하지 않는다.** 빌더가 부호를 확정해 배출한
**마스터를 입력으로 받아 그 결과(음수 잔액·부호반전·항등식 깨짐)만 검사한다.**
R-RSV-2/3 이 지금 0건인 것은 "부호가 옳다"가 아니라 "빌더가 배출 시점에 abs() 를 취해
음수가 원천 차단돼 있다"는 뜻이며, 이 룰은 **그 abs 가 제거되거나 우회되는 회귀를 잡는
안전망**으로 유효하다.

R-RSV-4/11/12(구성요소 항등식)는 기적립액·적립예정액을 따로 봐야 하므로 FS-API 캐시를
읽되, **추출은 `build_ifrs17_bs._extract_from_list` 를 그대로 호출**한다(자체 파싱 금지 —
같은 이유).

## legit-zero 면제

`data/_gold/user_pl_confirmed_cells.json` (master="IFRS17_BS") 를 그대로 재사용한다.
회사가 기적립액 전액을 환입예정으로 상계해 **잔액이 정말 0** 인 케이스가 있다
(케이디비생명 보증준비금, 하나생명 대손·보증). 등재된 셀은 R-RSV-6 에서 면제된다.
면제는 **마스터 값이 등재값과 여전히 일치할 때만** 유효하다 — 값이 바뀌면 다시 뜬다.

실행:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_statutory_reserves.py
  ... --json <path>   결과를 JSON 으로 저장
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "IFRS17_BS.json"
GOLD = ROOT / "data" / "_gold" / "user_pl_confirmed_cells.json"
BASELINE = ROOT / "data" / "_gold" / "statutory_reserve_baseline.json"
LEGIT = ROOT / "data" / "_gold" / "statutory_reserve_legit.json"

RESERVE_ITEMS = (5, 6, 7, 8)
CONCEPT = {5: "해약환급금준비금", 6: "비상위험준비금", 7: "대손준비금", 8: "보증준비금"}

# R-RSV-7: 해약환급금준비금 제도 시행이 2023년. 그 이전 분기 nonzero 는 의심(RED 아님 —
# 언론 집계 23.7조(2022년말)는 소급 가정 기준이라 장부값과 다르다는 owner 단서).
SURRENDER_START = (2023, 1)

# R-RSV-10 업권 앵커(백만원). 출처는 owner 티켓의 보도 표.
INDUSTRY_ANCHOR = {"2022.4Q": 23_700_000, "2023.4Q": 32_200_000,
                   "2024.2Q": 38_500_000, "2026.2Q": 58_100_000}
ANCHOR_TOL = 0.05
COMPANY_ANCHOR = {("한화생명", "2026.2Q", 5): 7_109_700}

RED, ORANGE = "RED", "ORANGE"
# 래칫: baseline 에 열거된 기존 결함은 비차단(BASELINE), 목록에 없는 새 RED 만 차단한다.
BASELINE_SEV = "BASELINE"


def _qk(q: str) -> tuple[int, int]:
    m = re.match(r"(\d{4})\.(\d)Q", str(q or ""))
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def _norm(s) -> str:
    return re.sub(r"\s+", "", str(s or ""))


class Finding(dict):
    pass


def _f(rule, sev, company, item, quarter, message, **kw):
    d = Finding(rule=rule, severity=sev, company=company, item=item,
                quarter=quarter, message=message)
    d.update(kw)
    return d


def load_registry() -> tuple[dict, float, float]:
    """legit-zero / owner-confirmed 셀. 키 = (master, company, quarter, item-label)."""
    if not GOLD.exists():
        return {}, 2.0, 0.01
    d = json.loads(GOLD.read_text(encoding="utf-8"))
    out = {}
    for c in d.get("cells", []):
        if c.get("master") != "IFRS17_BS":
            continue
        out[(_norm(c["company"]), str(c["quarter"]), _norm(c["item"]))] = float(c["value"])
    return out, float(d.get("tolerance_abs", 2.0)), float(d.get("tolerance_rel", 0.01))


def _registered(reg, company, quarter, label, value) -> bool:
    table, tol_abs, tol_rel = reg
    v = table.get((_norm(company), str(quarter), _norm(label)))
    if v is None or value is None:
        return False
    return abs(value - v) <= max(tol_abs, tol_rel * abs(v))


def load_legit() -> tuple[set, set]:
    """정당 사유 레지스트리 — baseline(미해결 결함)과 **반대 개념**이다.

      disclosed_none : 원문이 "적립한 내역은 없습니다" 라고 명시한 (회사, 항목, 분기).
                       결측이 아니라 **공시된 없음**이므로 R-RSV-9 census 에서 뺀다.
      legit_flat     : 적립이 멈출 정당한 사유(미처리결손금 등)가 원문에 있는 flat 구간.
                       R-RSV-1 에서 뺀다.

    각 항목은 raw 원문 인용(evidence)을 갖는다. 근거 없는 등재는 결함 은폐다.
    """
    if not LEGIT.exists():
        return set(), set()
    d = json.loads(LEGIT.read_text(encoding="utf-8"))
    none_cells = {(_norm(e["company"]), e["item"], q)
                  for e in d.get("disclosed_none", []) for q in e.get("quarters", [])}
    # 구간은 **포함관계**로 본다(정확일치 금지). 이월·백필로 flat 구간이 늘어나도 계속 매칭돼야
    # 한다 — 2026-08-20 에 owner 이월 결정으로 하나손해보험 구간이 2025.4Q→2026.2Q 로 늘자
    # 정확일치가 실패해 등재해 둔 정당 사유가 RED 로 되살아난 전례가 있다.
    flat_ranges = [(_norm(e["company"]), e["item"], e.get("from"), e.get("to"))
                   for e in d.get("legit_flat", [])]
    return none_cells, flat_ranges


# 연1회 공시사 hold-forward 면제 (parser 20260820T1130Z, owner 2026-08-20 "기말준비금을 중간분기로
# 이월하자"). 이월로 (회사,분기) 키가 생기면 코어 census 가 총계 1/2/3/4 를 요구하는데, 그 분기엔
# 회사가 재무제표를 아예 안 낸다. 카카오페이 건과 같은 구조 — 자식 행 하나가 키를 만들고 코어가 RED.
CARRY_FORWARD_SIDECAR = ROOT / "data" / "_derived" / "bs_carry_forward_cells.json"
_FYQ = {"1Q": "Q1", "2Q": "Q2", "3Q": "Q3", "4Q": "Q4"}


def carry_forward_exempt() -> tuple[set, list]:
    """사이드카를 **그대로 믿지 않고** 독립 근거로 재검증한 면제 셀만 돌려준다.

    사이드카는 검사받는 쪽(빌더)이 매 빌드 다시 쓰는 파일이다. 그걸 무조건 면제로 쓰면
    "검사받는 쪽이 자기 면제목록을 쓰는" 구조가 된다(2026-08-13 equity 라운드에서 같은 지점을
    지적한 적이 있다). 그래서 두 조건을 **여기서 다시 확인**한다:

      1. 4Q(연간필링 분기)가 아니다 — 그 분기는 원천이 있으므로 계속 코어를 요구한다.
      2. downloader 근거로 그 분기에 **필링이 없다** — raw 디렉터리가 없거나
         `meta.json` 이 `no_filing: true` 다.

    둘 중 하나라도 어긋나면 면제하지 않고 `rejected` 로 돌려 RED 로 남긴다.
    """
    if not CARRY_FORWARD_SIDECAR.exists():
        return set(), []
    try:
        d = json.loads(CARRY_FORWARD_SIDECAR.read_text(encoding="utf-8"))
    except Exception:
        return set(), []
    ok, rejected = set(), []
    for code, quarters in (d.get("companies") or {}).items():
        for q in quarters:
            m = re.match(r"(\d{4})\.(\d)Q", str(q))
            if not m:
                rejected.append((code, q, "분기 형식 불량")); continue
            if q.endswith("4Q"):
                rejected.append((code, q, "연간필링 분기(4Q)는 면제 대상이 아니다")); continue
            dirs = list((ROOT / "data" / "dart" / f"FY{m.group(1)}_Q{m.group(2)}" / "raw")
                        .glob(f"{code}_*"))
            if not dirs:
                ok.add((code, q)); continue        # 원천 디렉터리 자체가 없다 = 미제출
            meta = dirs[0] / "meta.json"
            try:
                no_filing = json.loads(meta.read_text(encoding="utf-8")).get("no_filing") is True
            except Exception:
                no_filing = False
            if no_filing:
                ok.add((code, q))
            else:
                rejected.append((code, q, f"그 분기 raw 가 실재한다({dirs[0].name}) — 미제출이 아니다"))
    return ok, rejected

_RSV_REPRT = {1: "11013", 2: "11012", 3: "11014", 4: "11011"}


def rollforward_exempt() -> tuple[set, list]:
    """빌더가 **복제해 채운** 칸(사이드카 `rollforward_filled`) 중 그 분기에 **필링 자체가
    없다**가 독립 확인된 (회사, 항목, 분기) 만 돌려준다.

    parser 20260820T1500Z 가 R-RSV-1 flat 44건 중 28건을 "빌더 복제라 flat 은 구성상 필연"
    이라며 일괄 면제 요청했다. **논리는 옳다** — 우리가 만든 사본을 우리가 결함으로 다시 세면
    순환이다. 그러나 "원천이 없다"의 근거가 **빌더 자신의 추출 결과**뿐이면 그것은
    "우리 파서가 못 읽었다"와 구분되지 않는다. 실제로 구분되지 않았다(validation 2026-08-20):

        삼성화재 FY2023_Q2 필링(20230814002808.xml)에
        `(해약환급금준비금 적립예정액: 556,503,490,830 원)` 이 그대로 실려 있는데
        빌더 파서는 그 분기를 '원천 없음'으로 보고 2023.3Q 값 916,764(백만원)을 뒤로
        복사했다. 공시값 556,503 의 **1.65배**다.

    그래서 면제는 **필링의 부재**로만 준다(추출 실패로는 주지 않는다). 두 조건 모두:

      1. raw 필링 디렉터리가 없다(또는 `meta.json` 이 `no_filing: true`).
      2. FS-API 캐시도 그 (분기, 항목)에 값을 주지 않는다.

    필링이 실재하면 `rejected` 로 남기고 R-RSV-1 은 계속 문다 — 그 칸은 면제 대상이 아니라
    **채워야 할 칸**이다(발주 inbox/parser/20260820T1900Z).
    """
    if not CARRY_FORWARD_SIDECAR.exists():
        return set(), []
    try:
        d = json.loads(CARRY_FORWARD_SIDECAR.read_text(encoding="utf-8"))
    except Exception:
        return set(), []
    rf = d.get("rollforward_filled") or {}
    if not rf:
        return set(), []
    try:
        sys.path.insert(0, str(ROOT))
        from scripts.build_ifrs17_bs import _basis_data, _extract_from_list   # noqa: E402
    except Exception:
        return set(), []            # 빌더를 못 읽으면 면제하지 않는다(안전측)

    corp: dict[str, str] = {}
    for p in ROOT.glob("data/dart/*/raw/*/meta.json"):
        kr = p.parent.name.split("_", 1)[0]
        if kr in corp:
            continue
        try:
            cc = json.loads(p.read_text(encoding="utf-8")).get("corp_code")
        except Exception:
            continue
        if cc:
            corp[kr] = cc

    ok, rejected = set(), []
    for kr, per_item in rf.items():
        for item_s, quarters in per_item.items():
            try:
                item = int(item_s)
            except (TypeError, ValueError):
                continue
            for q in quarters:
                m = re.match(r"(\d{4})\.(\d)Q", str(q))
                if not m:
                    continue
                y, qn = int(m.group(1)), int(m.group(2))
                dirs = list((ROOT / "data" / "dart" / f"FY{y}_Q{qn}" / "raw").glob(f"{kr}_*"))
                filed = bool(dirs)
                if filed:
                    try:
                        filed = json.loads(
                            (dirs[0] / "meta.json").read_text(encoding="utf-8")
                        ).get("no_filing") is not True
                    except Exception:
                        filed = True
                if filed:
                    rejected.append((kr, item, q,
                                     f"그 분기 필링이 실재한다({dirs[0].name}) — "
                                     f"복제가 아니라 추출 실패일 수 있다"))
                    continue
                cc = corp.get(kr)
                if cc:
                    got, _pend = _extract_from_list(
                        _basis_data(cc, str(y), _RSV_REPRT[qn], "OFS"))
                    if item in got:
                        rejected.append((kr, item, q, "FS-API 캐시가 그 항목 값을 준다"))
                        continue
                ok.add((kr, item, q))
    return ok, rejected


def load_baseline() -> tuple[set, list]:
    """이미 알려진 미해결 RED 목록.

    두 벌로 돌려준다:
      exact : {(rule, company, item, quarter)}  — 단일 분기 엔트리(R-RSV-5/6/8/9 등)
      spans : [(rule, company, item, from, to, value)] — 구간 엔트리(R-RSV-1)

    **구간을 문자열 정확일치로 잡지 않는 이유** (2026-08-20, parser 20260820T2010Z):
    래칫이 막아야 하는 것은 **새로운 결함**인데, 구간 문자열을 키로 쓰면 **데이터가 좋아져도**
    RED 이 뜬다. 뒤채움 사본을 걷어내자 flat 구간이 짧아졌고(예: DB생명 item5
    `2023.1Q~2024.3Q` → `2023.4Q~2024.3Q`, 값은 1,633,087 그대로), 축소된 구간이 키에서
    빠져 신규 RED 6건으로 잡혔다 — 같은 결함의 **경계 이동**일 뿐인데 막아 버린다.

    같은 실패를 오늘 이미 한 번 했다: `legit_flat` 도 span 정확일치라 이월로 구간이 늘자
    등재해 둔 정당 사유가 RED 로 되살아났다(그때는 from/to 포함관계로 고쳤다).
    **구간 키를 문자열 정확일치로 잡지 말 것** — 데이터가 자라거나 줄면 조용히 어긋난다.
    """
    if not BASELINE.exists():
        return set(), []
    d = json.loads(BASELINE.read_text(encoding="utf-8"))
    exact, spans = set(), []
    for e in d.get("entries", []):
        q = str(e.get("quarter"))
        key3 = (e["rule"], _norm(e.get("company")), e.get("item"))
        if "~" in q and e.get("value") is not None:
            a, b = q.split("~", 1)
            spans.append((*key3, a, b, float(e["value"])))
        else:
            exact.add((*key3, q))
    return exact, spans


def apply_baseline(findings: list[Finding], baseline) -> list[Finding]:
    """baseline 에 있는 RED 는 BASELINE(비차단)으로 강등한다. ORANGE 는 원래 비차단이라 그대로.

    구간 엔트리는 **포함관계 + 값 일치**로 판정한다. 둘 다 요구하는 이유:
      - 포함관계만 보면, 프리즌 구간 안에서 **다른 값**의 새 flat 이 생겨도 흡수해 버린다.
      - 값만 보면, 구간이 **길어진 것**(결함 확대)도 통과시킨다 — 포함관계가 그걸 막는다.
    구간이 프리즌 밖으로 뻗으면 포함이 깨져 RED 로 남는다(의도).
    """
    exact, spans = baseline if isinstance(baseline, tuple) else (baseline, [])
    for f in findings:
        if f["severity"] != RED:
            continue
        key3 = (f["rule"], _norm(f["company"]), f["item"])
        q = str(f["quarter"])
        hit = (*key3, q) in exact
        why = "동결된 기존 결함"
        if not hit and "~" in q and f.get("value") is not None:
            a, b = q.split("~", 1)
            fv = float(f["value"])
            for (r, c, it, fa, fb, bv) in spans:
                if (r, c, it) != key3:
                    continue
                if _qk(fa) <= _qk(a) and _qk(b) <= _qk(fb)                         and abs(fv - bv) <= max(1e-6, abs(bv) * 1e-9):
                    hit = True
                    why = ("동결된 기존 결함" if (fa, fb) == (a, b)
                           else f"동결 구간 {fa}~{fb} 의 축소분(같은 값 {bv:,.0f})")
                    break
        if hit:
            f["severity"] = BASELINE_SEV
            f["message"] += f"  [BASELINE — 2026-08-20 {why}, 비차단]"
    return findings


def _load_master(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def run(rows: list[dict], reg, legit=None, carry=None, rollfwd=None) -> list[Finding]:
    findings: list[Finding] = []
    disclosed_none, legit_flat = legit if legit is not None else load_legit()
    # 준비금 hold-forward 로 만들어진 칸(owner 2026-08-20 이월 결정). 이 칸들은 **설계상**
    # 직전 연간필링 값과 같으므로 R-RSV-1(연속 동일값)이 무는 게 당연하다 — 결함이 아니다.
    carry_cells = carry if carry is not None else carry_forward_exempt()[0]
    # 빌더가 복제해 채운 칸 중 **필링 부재가 독립 확인된** 것만 (rollforward_exempt 참조).
    # 추출 실패로 생긴 복제는 여기 안 들어온다 — 그건 면제가 아니라 채워야 할 칸이다.
    rollfwd_cells = rollfwd if rollfwd is not None else rollforward_exempt()[0]

    names, biz, labels = {}, {}, {}
    series: dict[tuple[str, int], dict[str, float]] = collections.defaultdict(dict)
    bs_quarters: dict[str, set] = collections.defaultdict(set)
    for r in rows:
        # 메타 3종은 .get 으로 읽는다: 실마스터 행엔 항상 있지만 데이터계약 게이트의
        # --selftest 가 주입하는 **합성 BS 행**엔 없어서 KeyError 로 죽었고, 그 바람에
        # selftest I1/I2/I3(BS 항등식·코어 census·미배포 YELLOW) 세 케이스가 ERROR 로
        # 남아 **그 세 룰이 사실상 무검증**이었다(2026-08-21 적발, 게이트 자기검사의 사각).
        co = r.get("원보험사코드")
        if not co:
            continue
        item_no = r.get("항목번호")
        names[co] = r.get("원수사명", co)
        biz[co] = r.get("생손보여부", "")
        if item_no in (1, 2, 3):
            bs_quarters[co].add(r.get("공시분기"))
        if item_no in RESERVE_ITEMS:
            series[(co, item_no)][r.get("공시분기")] = r.get("값")
            labels[item_no] = r.get("항목명", f"item{item_no}")

    # ---------- R-RSV-8: 항목명이 4종 사이에서 같은 정의를 쓰는가 ----------
    # 빌더는 4개 항목 모두 `기적립액 + 적립(환입)예정액` 합산을 싣는다. 항목명이 "기적립액"/"기말"
    # 처럼 다른 정의를 가리키면 같은 섹션 안에서 정의가 섞인다.
    for item, lab in sorted(labels.items()):
        core = _norm(lab).replace(CONCEPT[item], "")
        if core != "적립액":
            findings.append(_f(
                "R-RSV-8", RED, None, item, None,
                f"항목명 '{lab}' 이 합산 정의(적립액)와 불일치 — 4종 전부 "
                f"'~준비금 적립액' 이어야 한다(빌더가 기적립액+적립예정액을 싣는다)"))

    # ---------- 개념상 보유하지 않는 업권에 값이 실렸는가 (R-RSV-8 파생) ----------
    holders = {}
    for item in RESERVE_ITEMS:
        cos = {co for (co, it), s in series.items()
               if it == item and any(v for v in s.values())}
        holders[item] = cos
        kinds = collections.Counter(biz[c] for c in cos)
        if len(kinds) == 1:
            only = next(iter(kinds))
            for (co, it), s in series.items():
                if it != item or biz[co] == only:
                    continue
                for q, v in s.items():
                    findings.append(_f(
                        "R-RSV-8", RED, names[co], item, q,
                        f"{CONCEPT[item]}은 실측상 {only} 전용({len(cos)}사)인데 "
                        f"{biz[co]}사에 값 {v}이 실렸다 — 미공시(N/A)를 0/값으로 채우면 "
                        f"업권 합계·census 가 오염된다"))

    # ---------- 시계열 룰 ----------
    for co in sorted(names):
        for item in RESERVE_ITEMS:
            s = series.get((co, item), {})
            if not s:
                continue
            qs = sorted(s, key=_qk)
            label = labels.get(item, CONCEPT[item])

            # R-RSV-7
            if item == 5:
                for q in qs:
                    v = s[q]
                    if v not in (None, 0) and _qk(q) < SURRENDER_START:
                        findings.append(_f(
                            "R-RSV-7", ORANGE, names[co], item, q,
                            f"제도 시행(2023) 이전 분기에 nonzero {v:,.0f} — 오추출 의심"))

            for i, q in enumerate(qs):
                v = s[q]
                if v is None:
                    continue
                # R-RSV-2
                if v < 0:
                    findings.append(_f(
                        "R-RSV-2", RED, names[co], item, q,
                        f"준비금 잔액(stock)이 음수 {v:,.0f} — 구조상 불가. "
                        f"진짜 환입은 전분기 대비 '감소'로 나타난다"))
                if i == 0:
                    continue
                pq, pv = qs[i - 1], s[qs[i - 1]]
                if pv is None:
                    continue
                # R-RSV-3
                if pv and v and (pv < 0) != (v < 0) \
                        and abs(abs(pv) - abs(v)) <= max(1.0, abs(pv) * 0.01):
                    findings.append(_f(
                        "R-RSV-3", RED, names[co], item, q,
                        f"부호반전 + 절댓값 유사: {pq} {pv:,.0f} → {q} {v:,.0f}"))
                # R-RSV-5
                if pv and v:
                    ratio = abs(v) / abs(pv)
                    if ratio >= 10 or ratio <= 0.1:
                        findings.append(_f(
                            "R-RSV-5", ORANGE, names[co], item, q,
                            f"스케일 점프 ×{ratio:.1f}: {pq} {pv:,.0f} → {q} {v:,.0f} "
                            f"— 단위/자릿수 오류 의심"))
                # R-RSV-6 (legit-zero 레지스트리 면제)
                if pv not in (None, 0) and v == 0:
                    if _registered(reg, names[co], q, label, 0.0):
                        findings.append(_f(
                            "R-RSV-6", "SUPPRESSED", names[co], item, q,
                            f"{pq} {pv:,.0f} → {q} 0 — owner/validation 확정 legit-zero "
                            f"(data/_gold/user_pl_confirmed_cells.json)"))
                    else:
                        findings.append(_f(
                            "R-RSV-6", ORANGE, names[co], item, q,
                            f"{pq} {pv:,.0f} → {q} 정확히 0 — 추출 누락 의심. "
                            f"진짜 0이면 레지스트리에 등재할 것"))

            # R-RSV-1 (연속 동일값 run)
            i = 0
            while i < len(qs):
                v = s[qs[i]]
                if v in (None, 0):
                    i += 1
                    continue
                j = i
                while j + 1 < len(qs) and s[qs[j + 1]] is not None \
                        and abs(s[qs[j + 1]] - v) < 1e-6:
                    j += 1
                n = j - i + 1
                if n >= 2:
                    span = qs[i:j + 1]
                    crosses_fy = len({q.split(".")[0] for q in span}) > 1
                    has_q4 = any(q.endswith("4Q") for q in span)
                    # owner 권고 강화: 3분기 이상 연속 또는 FY경계+4Q 포함 → RED.
                    # 결산 적립은 FY말에 반드시 움직인다.
                    sev = RED if (n >= 3 or (crosses_fy and has_q4)) else ORANGE
                    if any(c == _norm(names[co]) and it2 == item
                           and (not fr or _qk(span[0]) >= _qk(fr))
                           and (not to or _qk(span[-1]) <= _qk(to))
                           for c, it2, fr, to in legit_flat):
                        sev = "SUPPRESSED"     # 원문에 적립 중단 사유가 있는 구간(포함관계)
                    elif all((co, qq) in carry_cells for qq in span[1:]):
                        # 첫 분기(실제 연간필링) 뒤가 전부 이월 칸이면 flat 은 구성상 필연이다.
                        # 첫 분기까지 이월이면 원천이 아예 없다는 뜻이라 그것도 포함해 억제.
                        sev = "SUPPRESSED"
                    elif len([qq for qq in span
                              if (co, item, qq) not in rollfwd_cells]) <= 1:
                        # 구간 안의 **진짜 관측이 1개 이하**면 flat 은 구성상 필연이다 —
                        # 나머지는 빌더가 복제한 사본이다. 뒤채움(backward)은 첫 관측이
                        # 구간 끝에 오므로 span[1:] 이 아니라 '실관측 수'로 센다.
                        sev = "SUPPRESSED"
                    findings.append(_f(
                        "R-RSV-1", sev, names[co], item, f"{span[0]}~{span[-1]}",
                        f"{n}분기 연속 동일값 {v:,.0f}"
                        + (" (FY경계+4Q 포함 — 결산 적립이 안 움직였다)"
                           if crosses_fy and has_q4 else ""),
                        value=v))
                i = j + 1

    # ---------- R-RSV-9 census ----------
    # 기대 그리드 = 그 항목을 한 번이라도 공시한 회사 × 그 회사가 BS(항목1/2/3)를 가진 분기.
    # ⚠ 알려진 사각: 총계가 통째로 없는 (회사,분기)는 이 그리드에서 조용히 빠진다.
    #    별도 룰(BS_CENSUS)이 그쪽을 본다 — validate_data_contract.py.
    for item in RESERVE_ITEMS:
        for co in sorted(holders[item], key=lambda c: names[c]):
            s = series[(co, item)]
            # 그 회사가 이 항목을 **처음 공시한 분기**. 그 이전의 부재는 결함이 아니라
            # 제도·서식 문제일 수 있다(비상장사 감사보고서에는 이익잉여금 구성내역 표가
            # 아예 없는 경우가 있다 — 악사손해보험 2022.4Q 실측: '비상위험준비금' 3회가
            # 전부 회계정책 주석 2.18 이고 값 행이 없다. 그 회사 item6 은 2023.4Q 부터
            # 공시된다). 그래서 **첫 공시 이전 = ORANGE(볼 값어치는 있음), 첫 공시 이후의
            # 구멍 = RED(회사가 내는 걸 아는데 우리가 못 잡은 것)** 로 나눈다.
            # 이 구분이 없으면 downloader 가 과거 raw 를 채울 때마다 RED 가 늘어난다
            # (parser 20260820T0930Z 가 지적한 구조적 함정).
            first_q = min((q for q, v in s.items() if v is not None), key=_qk, default=None)
            missing, pre_first = [], []
            for q in sorted(bs_quarters.get(co, ()), key=_qk):
                if q in s:
                    continue
                # 제도 시행 이전 분기는 기대 그리드에서 뺀다. 해약환급금준비금(5)은 2023년
                # 신설이고, 이익잉여금 내 법정 보증준비금(8)도 그 이전 분기에는 마스터 전체에서
                # 한 건도 공시되지 않는다(실측 2026-08-20: item5 4건은 전부 코리안리 —
                # R-RSV-7 이 따로 오추출로 문다, item8 은 0건). R-RSV-7 이 "2023 이전 nonzero =
                # 의심" 이라고 하면서 census 가 그 분기를 "있어야 하는데 없다" 고 세면 자기모순이다.
                # (parser 20260820T0430Z 지적 — 아이엠라이프 2022.4Q 가 신규 RED 로 push 를 막았다.
                #  그 필링의 '보증준비금' 7회는 전부 구 IFRS4 책임준비금 구성요소 서술이라
                #  거기서 값을 뽑으면 C-2 정의혼재 함정에 걸린다. raw 재확인 완료.)
                if item in (5, 8) and _qk(q) < SURRENDER_START:
                    continue
                # 원문이 "적립한 내역은 없습니다" 라고 명시한 셀 — 결측이 아니라 공시된 없음
                if (_norm(names[co]), item, q) in disclosed_none:
                    continue
                if first_q is not None and _qk(q) < _qk(first_q):
                    pre_first.append(q)
                else:
                    missing.append(q)
            if missing:
                findings.append(_f(
                    "R-RSV-9", RED, names[co], item, None,
                    f"첫 공시({first_q}) 이후 결측 {len(missing)}셀: {', '.join(missing)} "
                    f"— 회사가 공시하는 항목인데 비었다",
                    missing=missing))
            if pre_first:
                findings.append(_f(
                    "R-RSV-9", ORANGE, names[co], item, None,
                    f"첫 공시({first_q}) 이전 {len(pre_first)}셀 부재: {', '.join(pre_first)} "
                    f"— 서식·제도 문제일 수 있어 비차단. 원문에 값이 있으면 추출 대상이다",
                    missing=pre_first))

    # ---------- R-RSV-10 업권 앵커 ----------
    for q, target in INDUSTRY_ANCHOR.items():
        total, cell_missing, bs_missing = 0.0, [], []
        for co in holders[5]:
            v = series[(co, 5)].get(q)
            if v is not None:
                total += v
            elif q in bs_quarters.get(co, ()):
                cell_missing.append(names[co])
            else:
                bs_missing.append(names[co])
        dev = (total - target) / target
        if abs(dev) > ANCHOR_TOL:
            findings.append(_f(
                "R-RSV-10", ORANGE, None, 5, q,
                f"업권 합 {total:,.0f} vs 보도 {target:,.0f} ({dev:+.1%}). "
                f"셀결측 {len(cell_missing)}사[{', '.join(cell_missing) or '-'}] / "
                f"그 분기 BS부재 {len(bs_missing)}사[{', '.join(bs_missing) or '-'}]",
                cell_missing=cell_missing, bs_missing=bs_missing))
    for (nm, q, item), target in COMPANY_ANCHOR.items():
        co = next((c for c in names if names[c] == nm), None)
        v = series.get((co, item), {}).get(q) if co else None
        if v is None:
            findings.append(_f("R-RSV-10", ORANGE, nm, item, q, "회사 앵커 대상 셀이 결측"))
        elif abs(v - target) / target > ANCHOR_TOL:
            findings.append(_f("R-RSV-10", ORANGE, nm, item, q,
                               f"{v:,.0f} vs 보도 {target:,.0f} ({(v-target)/target:+.1%})"))
    return findings


def run_components(rows: list[dict]) -> list[Finding]:
    """R-RSV-4 / 11 / 12 — FS-API 캐시의 기적립액·적립예정액 대조.

    추출은 빌더 함수를 그대로 호출한다(부호 해석 재구현 금지 — 모듈 docstring 참조).
    빌더가 두 성분을 합쳐서 돌려주므로 여기서 얻는 것은 '합산값이 마스터와 맞는가'다.
    성분 단위 분해가 필요한 R-RSV-11(FY 경계 롤포워드)은 빌더가 그 형태로 노출하지
    않으므로 **미구현으로 남긴다** — 억지로 자체 파싱하면 A-1 오판을 재생산한다.
    """
    findings: list[Finding] = []
    try:
        sys.path.insert(0, str(ROOT))
        from scripts.build_ifrs17_bs import _basis_data, _extract_from_list  # noqa
    except Exception as e:      # 빌더가 리팩토링 중이면 조용히 건너뛰지 않고 알린다
        findings.append(_f("R-RSV-12", ORANGE, None, None, None,
                           f"구성요소 대조 불가 — 빌더 임포트 실패: {e}"))
        return findings

    REPRT = {1: "11013", 2: "11012", 3: "11014", 4: "11011"}
    corp = {}
    for p in ROOT.glob("data/dart/*/raw/*/meta.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        cc = d.get("corp_code")
        if cc:
            corp.setdefault(cc, p.parent.name.split("_", 1)[0])

    master = collections.defaultdict(dict)
    for r in rows:
        if r["항목번호"] in RESERVE_ITEMS:
            master[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]

    checked = 0
    for cc, co in sorted(corp.items()):
        for (y, qn), q in [((y, qn), f"{y}.{qn}Q")
                           for y in range(2023, 2027) for qn in (1, 2, 3, 4)]:
            lst = _basis_data(cc, str(y), REPRT[qn], "OFS")
            if not lst:
                continue
            got, _pending_seen = _extract_from_list(lst)
            for item in RESERVE_ITEMS:
                if item not in got:
                    continue
                checked += 1
                src = abs(got[item])
                mv = master.get((co, item), {}).get(q)
                if mv is None:
                    findings.append(_f(
                        "R-RSV-12", ORANGE, co, item, q,
                        f"FS-API 로는 {src:,.0f} 이 나오는데 마스터에 셀이 없다"))
                elif abs(src - mv) > max(1.0, abs(mv) * 0.002):
                    findings.append(_f(
                        "R-RSV-4", RED, co, item, q,
                        f"FS-API 재현값 {src:,.0f} ≠ 마스터 {mv:,.0f} "
                        f"(차 {mv - src:,.0f}) — 빌더 산출과 마스터가 갈렸다"))
    findings.append(_f("R-RSV-4", "INFO", None, None, None,
                       f"FS-API 구성요소 대조 {checked}셀 수행"))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=str(MASTER))
    ap.add_argument("--json", help="결과 JSON 저장 경로")
    ap.add_argument("--no-components", action="store_true",
                    help="FS-API 구성요소 대조(R-RSV-4/12) 건너뛰기")
    ap.add_argument("--no-baseline", action="store_true",
                    help="래칫 baseline 무시 — 기존 결함까지 전부 RED 로 본다(전수 현황 확인용)")
    a = ap.parse_args()

    rows = _load_master(Path(a.master))
    reg = load_registry()
    findings = run(rows, reg, load_legit(), carry_forward_exempt()[0],
                   rollforward_exempt()[0])
    if not a.no_components:
        findings.extend(run_components(rows))
    if not a.no_baseline:
        findings = apply_baseline(findings, load_baseline())

    order = {RED: 0, BASELINE_SEV: 1, ORANGE: 2, "INFO": 3, "SUPPRESSED": 4}
    counts = collections.Counter(f["severity"] for f in findings)
    by_rule = collections.Counter((f["rule"], f["severity"]) for f in findings)

    print("=" * 92)
    print(f"법정준비금 룰 R-RSV-1~12  ({Path(a.master).name}, {len(rows)}행)")
    print("=" * 92)
    for k in sorted(by_rule, key=lambda x: (order.get(x[1], 9), x[0])):
        print(f"  {k[0]:10s} {k[1]:11s} {by_rule[k]:4d}")
    print("-" * 92)
    for f in sorted(findings, key=lambda x: (order.get(x["severity"], 9), x["rule"],
                                             str(x["company"]), str(x["quarter"]))):
        if f["severity"] == "INFO":
            continue
        co = f["company"] or "-"
        it = f"item{f['item']}" if f["item"] else "-"
        print(f"  {f['severity']:11s} {f['rule']:10s} {it:7s} {co:16s} "
              f"{str(f['quarter'] or '-'):18s} {f['message']}")
    red = counts[RED]
    print("#" * 92)
    print(f"SUMMARY  RED={red}(차단)  BASELINE={counts[BASELINE_SEV]}(기존, 비차단)  "
          f"ORANGE={counts[ORANGE]}  SUPPRESSED={counts['SUPPRESSED']}")
    if not red and counts[BASELINE_SEV]:
        print(f"  신규 RED 없음. baseline {counts[BASELINE_SEV]}건은 "
              f"data/_gold/statutory_reserve_baseline.json 에 건별 열거돼 있다 "
              f"(parser 가 고칠 때마다 줄을 지운다).")
    print("#" * 92)
    if a.json:
        Path(a.json).write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
        print(f"  -> {a.json}")
    return 2 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
