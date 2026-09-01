# -*- coding: utf-8 -*-
"""Rebuild the COMBINED 경과조치 적용후 요구자본 chain from the raw 선택적용 tables.

validation inbox `20260821T0010Z` (MMULT_AFTER): axis C — `item15후 = R4(17-20)후 + 21후` —
failed on 36 (회사,분기) while 적용전 passed 484/484. Root cause: a company that elects
**several** selective transitions gets one table per transition (② 장수·사업비·해지·대재해 /
③ 주식 / ④ 금리, sometimes ③④ merged), and each table shows ONLY its own risk reduced with
every other row left at 적용전. The loaders took whole rows out of **one** table, so the master
ended up mixing a combined headline (item14후) with single-table components (item15/19/22후) —
and, in the worst cases, left a risk at 적용전 entirely because the table that reduced it was
never read (에이비엘 ③, 흥국화재 ④).

Model (verified against raw headlines before anything is written):

  leaf후   = the value from whichever table reduced that leaf (each table touches only its own);
             unchanged leaves stay at 적용전. Two tables reducing the same leaf = conflict, abort.
  생명장기후 = sqrt(S' R7 S) over the 7 life leaves          (cross-checked vs the table's own total)
  시장후    = sqrt(V' M V)  over the 5 market leaves          (same cross-check)
  기본요구자본후 = sqrt(W' R4 W) + 운영후,  W = (생명장기, 일반손해, 시장, 신용)후
  기준금액후   = 지급여력금액후 ÷ (원문 주요경영지표의 '지급여력비율(경과조치 후)') × 100
             — 회사가 직접 공시한 결합 결과에 앵커한다. 헤드라인이 없는 필링은 쓰지 않는다.
  법인세조정액후 = 기본요구자본후 + 기타요구자본후 − 기준금액후  (잔차)
             — 상수비(법인세전/기본요구자본전) 가정은 보편적으로 성립하지 않는다: 흥국화재
               2023.3Q 는 전·②·③ 이 모두 .2282954 인데 2023.2Q 는 ③④가 법인세를 그대로 둔다.
               그래서 비율로 밀지 않고 앵커의 잔차로 둔다.
  기타요구자본후 = 0 (대부분) 또는 관계회사 환산 — AFFILIATE 참조.

검증(쓰기 전 전부 통과해야 함)
  1. 적용전을 leaf 에서 R4/R7/M 로 재현해 표의 기본요구자본전과 일치할 것 (단위·행 매칭 확인).
  2. 표가 직접 공시한 생명장기후·시장후를 R7/MARKET_M 이 재현할 것.
  3. 결합 기본요구자본후·기준금액후가 **어떤 단일표 값보다도 작을 것**(단조성).
  4. 잔차 법인세후가 음수가 아니고 법인세전의 1.2배 이내일 것.

Writes items 15·16·17·19·22·14·27·28후 + the market leaves 36-40후 (life leaves 29-35후 are
already correct — axis A reconciles exactly on these cells). 적용전 is never touched.

Usage:
  ...python scripts/rebuild_combined_transition_after.py --dry-run
  ...python scripts/rebuild_combined_transition_after.py --only KR0005
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from solvency.validation.kics_json_rules import R4, R7, MARKET_M  # noqa: E402
sys.path.insert(0, str(REPO / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

TARGET = REPO / "kics_disclosure.json"

# keep in sync with _TRANSITION_APPLIERS in scripts/validate_kics_disclosure.py
# 기타요구자본(Ⅲ) = "업권별 자본규제를 활용한 관계회사의 요구자본 환산치". 그 회사의 결합
# 적용후 값은 관계회사의 요구자본에 딸려 움직이므로 이 필링만으로는 못 푼다 — 관계회사가
# 우리 마스터에 있으면 그쪽 item14 로 환산한다. 환산계수는 마스터 적용전으로 분기마다 구하고,
# 회사 중앙값과 0.002 이상 어긋나면 거부한다(실측: 흥국생명/흥국화재 13분기 0.40060±0.00003).
AFFILIATE = {"KR0071": "KR0005"}

APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082", "KR0083",
    "KR0097", "KR0100", "KR1010", "KR1011", "KR0104", "KR0049", "KR0002",
    "KR0003", "KR0004", "KR0005", "KR0032",
})

ZERO = {"-", "─", "–", "—", "", "0"}
DASH = {"-", "─", "–", "—"}          # ZERO 중 진짜 숫자 "0"·빈칸을 뺀, '표기 대시'만
NUMRE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")

LIFE = ["사망", "장수", "장해질병", "장기재물", "해지", "생명대재해"]      # + 대재해 handled below
LIFE7 = ["사망", "장수", "장해질병", "장기재물", "해지", "사업비", "생명대재해"]
MARKET5 = ["금리", "주식", "부동산", "외환", "자산집중"]
ITEM_OF = {
    "사망": 29, "장수": 30, "장해질병": 31, "장기재물": 32, "해지": 33,
    "사업비": 34, "생명대재해": 35,
    "금리": 36, "주식": 37, "부동산": 38, "외환": 39, "자산집중": 40,
}
LABELS = [
    ("비율", "지급여력비율"), ("가용자본", "지급여력금액"), ("기본자본", "기본자본"),
    ("보완자본", "보완자본"), ("기준금액", "지급여력기준금액"), ("기본요구자본", "기본요구자본"),
    ("생명장기", "생명·장기손해보험위험액"), ("사망", "사망위험"), ("장수", "장수위험"),
    ("장해질병", "장해·질병위험"), ("장기재물", "장기재물·기타위험"), ("해지", "해지위험"),
    ("사업비", "사업비위험"), ("생명대재해", "대재해위험"), ("일반손해", "일반손해보험위험액"),
    ("보험가격", "보험가격및준비금위험"), ("일반대재해", "대재해위험"), ("시장", "시장위험액"),
    ("금리", "금리위험"), ("주식", "주식위험"), ("부동산", "부동산위험"), ("외환", "외환위험"),
    ("자산집중", "자산집중위험"), ("신용", "신용위험액"), ("운영", "운영위험액"),
    ("법인세", "법인세조정액"), ("기타요구자본", "기타요구자본"),
]


def _num(tok):
    t = str(tok).strip().replace(" ", "").replace("%", "")
    if t in ZERO:
        return None if t == "" else 0.0
    for ch in ("△", "▲", "▽", "▼", "−"):
        t = t.replace(ch, "-")
    m = re.fullmatch(r"\((-?[\d,]+(?:\.\d+)?)\)", t)
    if m:
        t = "-" + m.group(1)
    t = t.replace(",", "").lstrip("+")
    try:
        return float(t)
    except ValueError:
        return None


def _pdf(period: str, code: str):
    # raw/ 우선, 없을 때만 pdf/ (공유 해석기 계약 — scripts/_disclosure_pdf_paths.py).
    # 종전에는 raw/ 만 봤는데, FY2026_Q2 는 원문이 `pdf/` 에 40개 있고 `raw/` 에는 1개뿐이라
    # **39개사를 조용히 건너뛰고 exit 0 으로 나갔다** — 호출자에게는 "재구성할 게 없었다" 로
    # 읽힌다. 2026-09-01 에 KR0071·KR0104 의 결합 경과조치 적용후가 잘못 역산된 채 남아 있던
    # 것이 이 침묵 때문이었다(validation 발주 `inbox/parser/20260901T0500Z`). 없는 것과 안 본
    # 것은 다르다. (중간판은 raw+pdf 매치를 합쳐 파일크기로 골라 raw 우선 계약을 깰 수 있었다
    # — KR0050/FY2026_Q2 는 두 사본이 우연히 바이트까지 동일해 지금은 안 드러났을 뿐이다.)
    pdfs = disclosure_pdfs(period, code)
    if not pdfs:
        return None
    am = [p for p in pdfs if "_amended" in p.name]
    return max(am or pdfs, key=lambda p: p.stat().st_size)


def _headline_after(doc) -> float | None:
    """주요경영지표 / 최근3개사업연도의 '지급여력비율 (경과조치 후)' 숫자."""
    for i in range(doc.page_count):
        text = doc[i].get_text()
        if "경과조치" not in text or "지급여력비율" not in text:
            continue
        lines = [x.strip() for x in text.splitlines()]
        for j, l in enumerate(lines):
            win = "".join(lines[max(0, j - 4):j + 1]).replace(" ", "")
            if "지급여력비율" not in win or "경과조치후" not in win.replace("(", "").replace(")", ""):
                continue
            for k in range(j + 1, min(j + 8, len(lines))):
                t = lines[k].replace(" ", "")
                if t in ("(", ")", "%", "(%)", "|", ""):
                    continue          # 표 장식 토큰은 건너뛴다(2025.2Q 흥국화재: '경과조치 후|(|)|220.77')
                if NUMRE.match(t):
                    v = float(t.strip("()%").replace(",", ""))
                    if 0 < v < 5000:
                        return v
                    break
                if t not in ZERO:
                    break
    return None


def scan_occurrences(pdf: Path):
    """-> ({label: [(전, 후), ...]}, headline_after_ratio or None).

    One line stream over every 경과조치 page in order — no per-table splitting. Page breaks cut
    tables in half and re-emit the header, which produced phantom all-zero blocks; and the
    per-page state reset mis-assigned '대재해위험' between the 생명장기 and 일반손해 blocks.
    Each leaf is resolved from the SET of its occurrences instead (resolve_leaf).
    """
    doc = fitz.open(pdf)
    try:
        headline = _headline_after(doc)
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()

    # 표가 열린 뒤에는 다음 페이지도 따라간다: 표 머리말만 있고 본문 전체가 다음 페이지로 넘어가는
    # 필링(흥국화재 2023.1Q ④금리위험 p10머리말/p11본문 — p11엔 '경과조치'라는 단어가 없다)이 있어,
    # 매칭된 페이지 바로 다음 페이지는 두 키워드가 없어도 포함한다(F3, 2026-08-21).
    matched = {i for i, text in enumerate(page_texts)
               if "경과조치" in text and "기본요구자본" in text}
    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)
    lines: list[str] = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())

    occ: dict[str, list[tuple]] = defaultdict(list)
    market_dash_idx: dict[str, list[int]] = defaultdict(list)  # MARKET5 항목별 dash-post 항목의 occ[key] 인덱스 (F4, 아래)
    block = None            # None | life | nl | market  (survives page breaks)
    last_key = None         # 대재해위험 은 바로 앞 leaf 로 판별한다 — 표 사이에 ①표가 끼어들면
                            # block 이 리셋돼(지급여력기준금액 행) 생명/일반 구분이 날아간다
    LIFE_PREV = {"사망", "장수", "장해질병", "장기재물", "해지", "사업비"}
    NL_PREV = {"일반손해", "보험가격"}
    k = 0
    def _norm(x: str) -> str:
        # 일부 필링은 가운뎃점을 별도 텍스트 라인으로 뽑는다("장해질병위험" / "·" / 값) —
        # 라벨·패턴 양쪽에서 점을 지우고 비교한다(2025.2Q 흥국화재).
        return x.replace("·", "").replace("‧", "").replace("∙", "")

    DECOR = {"·", "‧", "∙", "(", ")", "%", "(%)", "|", ","}
    while k < len(lines):
        s = _norm(lines[k].strip().lstrip("Ⅰ Ⅱ Ⅲ①②③④ .·-").replace(" ", ""))
        key = None
        for kk, pat in LABELS:
            if kk in ("생명대재해", "일반대재해"):
                continue
            pat = _norm(pat)
            if s == pat or s == pat.replace("위험액", "위험") or s.rstrip("()1+2+3") == pat:
                key = kk
                break
        if key is None and s in ("대재해위험", "대재해위험액"):
            if last_key in LIFE_PREV:
                key = "생명대재해"
            elif last_key in NL_PREV:
                key = "일반대재해"
            else:
                key = {"life": "생명대재해", "nl": "일반대재해"}.get(block)
        if key == "생명장기":
            block = "life"
        elif key == "일반손해":
            block = "nl"
        elif key == "시장":
            block = "market"
        elif key in ("신용", "운영", "법인세", "기타요구자본", "기본요구자본", "기준금액"):
            block = None
        if key:
            vals, toks, j = [], [], k + 1
            while j < len(lines) and len(vals) < 2:
                t = lines[j].replace(" ", "")
                if t == "" or t in DECOR:
                    j += 1
                    continue
                if NUMRE.match(t) or t in ZERO:
                    vals.append(_num(t))
                    toks.append(t)
                    j += 1
                    continue
                break
            if len(vals) == 2 and vals[0] is not None:
                a, b = vals
                # 시장위험(36-40) 표는 해당 선택경과조치를 적용하지 않으면 '후' 칸 전체를 "-"로
                # 채운다 — 이건 진짜 0 이 아니라 "전후 동일" 표기다(owner 확인, 롯데손보 2026.1Q
                # p25: 시장위험 하위위험 전부 "-"=전후동일). ZERO 취급(0.0)으로 읽으면 정상 미러값을
                # 0 으로 무너뜨린다. 생명장기(29-35)는 같은 표 안에서도 진짜 0 과 "-"가 섞여 나와
                # (장수/사업비=완전 소멸 vs 해지/대재해=일부잔존) 이 규칙을 적용할 수 없어 제외한다(F3).
                # F4(2026-08-24): 위 carry-forward 는 "이 표를 통째로 선택 안 함"(형제 5개가 전부
                # dash/무변화) 케이스에만 맞다. 같은 표 안에서 다른 시장위험 형제가 **진짜 변화**를
                # 보이면(선택적용이 실제로 걸린 표) dash 는 "적용후 인정액 0"을 뜻한다 — 예별손해보험
                # (KR0004) 2023.4Q~2024.2Q item36: 금리위험 65,239~71,606백만/'-', 형제 주식위험은
                # 188,325→112,644 등으로 실변화, MARKET_M 상관행렬로 회사 자신이 인쇄한 시장위험액후
                # 합계를 '금리후=0' 가설만 소수점까지 재현(carry-forward 가설은 26,000~38,000백만
                # 어긋남 — probe_20260821_kr0004_verify.py). 판정은 이 표(scan_occurrences 호출 1회
                # = 통상 회사·분기 1건) 전체를 다 읽은 뒤에야 가능해 즉시 스냅하지 않고 위치만
                # 기록, 루프 종료 후 일괄 후처리한다(아래). 전 APPLIERS x quarter(234버킷)
                # 시뮬레이션으로 이 갈래가 예별손해 3분기 외에는 결과를 바꾸지 않음을 확인했다
                # (scripts/_probes/probe_20260824_market_dash_simulate.py).
                is_dash_post = key in MARKET5 and toks[1] in DASH and a != 0.0
                if is_dash_post:
                    market_dash_idx[key].append(len(occ[key]))
                occ[key].append((a, b))
                last_key = key
                k = j
                continue
        k += 1

    if market_dash_idx:
        market_real_change = any(
            idx not in market_dash_idx.get(k5, []) and a2 is not None and b2 is not None and abs(a2 - b2) > 0.5
            for k5 in MARKET5 for idx, (a2, b2) in enumerate(occ.get(k5, []))
        )
        if not market_real_change:
            for k5, idxs in market_dash_idx.items():
                for idx in idxs:
                    a2, _b2 = occ[k5][idx]
                    occ[k5][idx] = (a2, a2)   # 형제 전부 무변화 -> 표 전체 미선택, 종전대로 carry-forward
        # market_real_change=True 이면 dash 항목은 이미 (a, 0.0)으로 들어가 있어 손댈 것 없음
    return occ, headline


def resolve_leaf(pairs, tol=0.5):
    """-> (value, note). Unchanged everywhere = 적용전. Exactly one differing value = that."""
    if not pairs:
        return None, "표에 없음"
    pre = pairs[0][0]
    changed = {round(b, 2) for a, b in pairs
               if a is not None and b is not None and abs(a - b) > tol}
    if not changed:
        return pre, "불변"
    if len(changed) > 1:
        return None, f"두 표가 같은 항목을 건드림 {sorted(changed)}"
    return changed.pop(), "감소"


def q2p(q):
    y, qq = q.split(".")
    return f"FY{y}_Q{qq[0]}"


def _leaves_mode(data, by_cq, name, val, dry, only, pre=False) -> int:
    """29-35후 / 36-40후 를 원문 결합 leaf 로 맞춘다 (부모후 재현이 되는 셀만).

    axis A/B 의 '계산불가'(하위 결측)와, 부모는 맞는데 하위 한 칸이 전값으로 남은 오염
    (처브 2023.3Q item35후=47.71, raw ②표는 '-') 을 동시에 닫는다. 가드: 재구성한 leaf 로
    R7/MARKET_M 을 돌려 **이미 저장된 부모후를 재현할 때만** 쓴다 — 못 하면 손대지 않는다.
    """
    from collections import defaultdict as _dd
    writes, holds = [], []
    for (c, q), items in sorted(by_cq.items()):
        if c not in APPLIERS or (only and c != only):
            continue
        pdf = _pdf(q2p(q), c)
        if pdf is None:
            continue
        occ, _hl = scan_occurrences(pdf)
        if not occ.get("기본요구자본"):
            continue
        base_pre_raw = max(a for a, _b in occ["기본요구자본"])
        scale = (val(items, 15, False) or 0) / base_pre_raw if base_pre_raw else 0
        if not (0.009 < scale < 0.011 or 0.99 < scale < 1.01):
            continue
        # 억원 마스터 / 백만원 원문. 앵커로 잰 비율은 반올림 때문에 0.01 에서 미세하게 벗어나므로
        # 정확한 단위로 스냅한다 (안 하면 4,691 -> 46.90 처럼 끝자리가 흔들린다).
        scale = 0.01 if scale < 0.5 else 1.0
        for parent, keys, mat in ((17, LIFE7, R7), (19, MARKET5, MARKET_M)):
            p_post = val(items, parent, not pre)
            if p_post is None:
                continue
            vals, ok = [], True
            for k in keys:
                if pre:
                    cand = [a for a, _b in occ.get(k, [])]
                    v = max(set(cand), key=cand.count) if cand else None
                else:
                    v, _n = resolve_leaf(occ.get(k, []))
                if v is None:
                    if k in ("자산집중", "장기재물", "장수"):
                        v = 0.0
                    else:
                        ok = False
                        break
                vals.append(v)
            if not ok:
                continue
            arr = np.array(vals, float)
            calc = float(np.sqrt(arr @ mat @ arr)) * scale
            if abs(calc - p_post) > max(2.0, 0.002 * abs(p_post)):
                holds.append((c, q, parent, f"부모후 재현 실패 계산={calc:,.2f} vs 저장={p_post:,.2f}"))
                continue
            for k, v in zip(keys, vals):
                it = ITEM_OF[k]
                row = items.get(it)
                if row is None:
                    continue
                col = "값" if pre else "값_적용후"
                cur = _num(row.get(col))
                new = round(v * scale, 2)
                # F2: 원문(백만원)->억원 변환은 근사가 아니라 정확해야 하는 변환이다. 비례 문턱
                # (0.0005*|new|)은 39,037억 셀에서 19.5억까지 허용해 스냅 도입 전에 쓰인 잔여
                # 스케일오차(<=0.10억)를 스스로 못 고쳤다 — 평평한 절대값(0.005억)으로 고정한다.
                if cur is None or abs(cur - new) > 0.005:
                    writes.append((c, q, it, row.get(col), new, row, col))
    print(f"{'DRY-RUN ' if dry else ''}leaves 모드: 갱신 {len(writes)}셀 · 부모후 재현실패 {len(holds)}")
    for c, q, it, old, new, _r, col in writes:
        print(f"  LEAF {c} {name.get(c,c):<12} {q} item{it:>2} [{col}]: {old} -> {new}")
    for c, q, parent, why in holds:
        print(f"  HOLD {c} {name.get(c,c):<12} {q} parent{parent}: {why}")
    if not dry and writes:
        def fmt(x):
            return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")
        for _c, _q, _it, _old, new, row, col in writes:
            row[col] = fmt(new)
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {TARGET.name}")
    return 0


def main() -> int:
    dry = "--dry-run" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    by_cq: dict[tuple, dict] = defaultdict(dict)
    name = {}
    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_cq[(c, q)][int(r["항목번호"])] = r

    def val(items, n, post):
        r = items.get(n)
        if r is None:
            return None
        return _num(r.get("값_적용후" if post else "값"))

    # targets = axis-C 적용후 failures, 선택경과조치 적용사만.
    # 비적용사(_TRANSITION_APPLIERS 밖)는 선택 표 자체가 없어 결합할 것이 없다 — 그쪽의 잔차는
    # 억원 정수 반올림이고, 고치는 방법은 재구성이 아니라 전=후 미러링이다. 건드리면 오히려
    # 이미 맞는 29-35후와 item17후가 어긋난다(2026-08-21 AIA 2023.3Q 실측).
    targets = []
    for (c, q), items in sorted(by_cq.items()):
        if only and c != only:
            continue
        if c not in APPLIERS:
            continue
        p15 = val(items, 15, True)
        vs = [val(items, i, True) for i in (17, 18, 19, 20)]
        v21 = val(items, 21, True)
        if p15 is None or any(v is None for v in vs) or v21 is None:
            continue
        w = np.array(vs, float)
        exp = float(np.sqrt(w @ R4 @ w)) + v21
        if abs(p15 - exp) > 2.0:
            targets.append((c, q))

    if "--leaves" in sys.argv:
        return _leaves_mode(data, by_cq, name, val, dry, only, pre="--pre" in sys.argv)

    print(f"axis-C 적용후 FAIL 대상 = {len(targets)} (회사,분기)")
    writes, rejects = [], []
    for c, q in targets:
        items = by_cq[(c, q)]
        pdf = _pdf(q2p(q), c)
        if pdf is None:
            rejects.append((c, q, "raw 없음"))
            continue
        occ, headline = scan_occurrences(pdf)
        if headline is None:
            rejects.append((c, q, "주요경영지표 경과조치후 헤드라인 못 찾음"))
            continue
        if not occ.get("기본요구자본"):
            rejects.append((c, q, "경과조치 표 파싱 실패"))
            continue

        other_cands = [a for a, _b in occ.get("기타요구자본", []) if a is not None]
        other_pre = max(other_cands) if other_cands else 0.0
        other_after_master = 0.0
        if abs(other_pre) > 0.5:
            link = AFFILIATE.get(c)
            o_pre_m = val(items, 23, False)
            l_pre = val(by_cq.get((link, q), {}), 14, False) if link else None
            l_post = val(by_cq.get((link, q), {}), 14, True) if link else None
            if not (link and o_pre_m and l_pre and l_post):
                rejects.append((c, q, f"기타요구자본전={other_pre:,.0f} (관계회사 환산치 — "
                                      f"연결사 {link} {q} 값 없음)"))
                continue
            ks = []
            for qq in {qq for (cc, qq) in by_cq if cc == c}:
                a = val(by_cq[(c, qq)], 23, False)
                b = val(by_cq.get((link, qq), {}), 14, False)
                if a and b:
                    ks.append(a / b)
            k = o_pre_m / l_pre
            med = sorted(ks)[len(ks) // 2] if ks else k
            if abs(k - med) > 0.002:
                rejects.append((c, q, f"관계회사 환산계수 이탈 {k:.5f} vs 중앙값 {med:.5f}"))
                continue
            other_after_master = k * l_post

        leaves, notes = {}, {}
        bad = None
        for k in LIFE7 + MARKET5 + ["신용", "운영", "일반손해"]:
            v, note = resolve_leaf(occ.get(k, []))
            leaves[k], notes[k] = v, note
            if v is None and k not in ("자산집중", "장기재물", "장수"):
                bad = f"{k}: {note}"
        if bad:
            rejects.append((c, q, bad))
            continue
        for k in ("자산집중", "장기재물", "장수"):
            if leaves[k] is None:
                leaves[k] = 0.0

        s = np.array([leaves[k] for k in LIFE7], float)
        life_after = float(np.sqrt(s @ R7 @ s))
        v = np.array([leaves[k] for k in MARKET5], float)
        mkt_after = float(np.sqrt(v @ MARKET_M @ v))
        w = np.array([life_after, leaves["일반손해"], mkt_after, leaves["신용"]], float)
        base_after = float(np.sqrt(w @ R4 @ w)) + leaves["운영"]

        # 적용전을 leaf 에서 되짚어 계산해 두고, 그 값과 맞는 '기본요구자본' occurrence 만 채택한다.
        # (같은 페이지의 [경과조치 적용 전 …세부] 표가 억원 단위로 같은 라벨을 갖고 있어, 첫
        #  occurrence 를 그냥 쓰면 백만원/억원이 섞여 법인세 비율이 100배 틀어진다.)
        sp = np.array([(occ[k][0][0] if occ.get(k) else 0.0) for k in LIFE7], float)
        life_pre = float(np.sqrt(sp @ R7 @ sp))
        vp = np.array([(occ[k][0][0] if occ.get(k) else 0.0) for k in MARKET5], float)
        mkt_pre = float(np.sqrt(vp @ MARKET_M @ vp))
        nl_pre = occ["일반손해"][0][0] if occ.get("일반손해") else 0.0
        cr_pre = occ["신용"][0][0] if occ.get("신용") else 0.0
        op_pre = occ["운영"][0][0] if occ.get("운영") else 0.0
        wp = np.array([life_pre, nl_pre, mkt_pre, cr_pre], float)
        base_pre_calc = float(np.sqrt(wp @ R4 @ wp)) + op_pre
        cands = [a for a, _b in occ["기본요구자본"]
                 if base_pre_calc and abs(a - base_pre_calc) <= max(2.0, 0.005 * base_pre_calc)]
        if not cands:
            rejects.append((c, q, f"적용전 기본요구자본 재현 실패 계산={base_pre_calc:,.0f} "
                                  f"표={sorted({a for a, _ in occ['기본요구자본']})}"))
            continue
        base_pre = cands[0]
        # 같은 라벨이 [경과조치 적용 전 …세부](억원)에도 있어 스케일이 섞인다 → 백만원 표의
        # 값(항상 더 큼)을 고르기 위해 base_pre 이하 중 최대를 채택한다.
        tax_cands = [a for a, _b in occ.get("법인세", []) if 0 <= a <= base_pre]
        tax_pre = max(tax_cands) if tax_cands else 0.0
        # --- 독립 검증 1: leaf 추출이 맞으면 표가 직접 공시한 부모후를 정확히 재현한다.
        disc_life = {round(b, 1) for a, b in occ.get("생명장기", []) if b is not None and abs(a - b) > 0.5}
        disc_mkt = {round(b, 1) for a, b in occ.get("시장", []) if b is not None and abs(a - b) > 0.5}
        if disc_life and not any(abs(life_after - d) <= max(2.0, 0.002 * d) for d in disc_life):
            rejects.append((c, q, f"생명장기후 재현 실패 R7={life_after:,.0f} vs 표={sorted(disc_life)}"))
            continue
        if disc_mkt and not any(abs(mkt_after - d) <= max(2.0, 0.002 * d) for d in disc_mkt) \
                and len(disc_mkt) < 2:
            rejects.append((c, q, f"시장후 재현 실패 M={mkt_after:,.0f} vs 표={sorted(disc_mkt)}"))
            continue

        avail_after = val(items, 1, True)
        if avail_after is None:
            rejects.append((c, q, "item1후 없음(비율 검산 불가)"))
            continue
        # master is 억원, raw tables 백만원 -> scale by the 적용전 anchor
        scale = (val(items, 15, False) or 0) / base_pre if base_pre else 0
        if not (0.009 < scale < 0.011 or 0.99 < scale < 1.01):
            rejects.append((c, q, f"단위 스케일 이상 {scale:.5f}"))
            continue

        # 기준금액후는 공시 헤드라인 비율에 앵커한다(회사가 직접 공시한 결합값).
        # 법인세조정액후는 그 잔차 — 필링마다 표별 재계산 여부가 갈려(2023.3Q는 비율 일정,
        # 2023.2Q는 ③④가 법인세를 그대로 둠) 상수비 가정이 보편적으로 성립하지 않는다.
        scr_after = avail_after / headline * 100 / scale
        other_after = other_after_master / scale if scale else 0.0
        tax_after = base_after + other_after - scr_after
        base_ratio = tax_pre / base_pre if base_pre else 0.0
        # --- 독립 검증 2: 단일 표 값과의 단조성 + 잔차 법인세 sanity.
        #     결합은 어떤 단일 경과조치보다도 요구자본을 더 줄여야 한다. 표별 법인세 비율은
        #     필링마다 재계산 여부가 갈려(2023.3Q 일정 / 2023.2Q ③④ 미재계산) 밴드로 못 묶는다 —
        #     대신 leaf→표 재현(위)과 이 단조성으로 검증하고, 법인세는 잔차로 둔다.
        disc_base = [b for a, b in occ["기본요구자본"]
                     if b is not None and a == base_pre and abs(a - b) > 0.5]
        disc_scr = [b for a, b in occ.get("기준금액", [])
                    if b is not None and b > 0.1 * base_pre and abs(a - b) > 0.5]
        imp = tax_after / base_after if base_after else 0.0
        if disc_base and base_after > min(disc_base) + 2.0:
            rejects.append((c, q, f"결합 기본요구자본후 {base_after:,.0f} > 단일표 최소 "
                                  f"{min(disc_base):,.0f} (단조성 위반)"))
            continue
        if disc_scr and scr_after > min(disc_scr) + 2.0:
            rejects.append((c, q, f"결합 기준금액후 {scr_after:,.0f} > 단일표 최소 "
                                  f"{min(disc_scr):,.0f} (단조성 위반)"))
            continue
        if not (-0.5 <= tax_after <= max(1.0, tax_pre * 1.2 + 2)):
            rejects.append((c, q, f"법인세후 잔차 비정상 {tax_after:,.0f} (전={tax_pre:,.0f})"))
            continue
        ratio_calc = headline

        new = {
            15: base_after * scale,
            17: life_after * scale,
            19: mkt_after * scale,
            22: tax_after * scale,
            14: scr_after * scale,
            16: (life_after + leaves["일반손해"] + mkt_after + leaves["신용"] + leaves["운영"]
                 - base_after) * scale,
        }
        if abs(other_after_master) > 0.005:
            new[23] = other_after_master
        for k in MARKET5:
            new[ITEM_OF[k]] = leaves[k] * scale
        v2, v14 = val(items, 2, True), new[14]
        new[27] = avail_after / v14 * 100
        if v2 is not None:
            new[28] = v2 / v14 * 100
        writes.append((c, q, new, headline, ratio_calc, imp, 0.0, 0.0))

    # --- 잔차 법인세비율 검증: 분기별 밴드 OR 회사 내 분기간 일관성(>=3분기, 폭<=0.006).
    #     밴드는 표가 법인세를 재계산했는지에 따라 흔들리지만, 잘못 재구성된 기본요구자본후는
    #     분기마다 다른 비율을 낳는다 — 여러 분기가 같은 비율로 수렴하면 그 자체가 검증이다.
    print(f"재구성 성공 {len(writes)} · 거부 {len(rejects)}")
    for c, q, new, hl, calc, imp, _lo, _hi in writes:
        old15 = val(by_cq[(c, q)], 15, True)
        print(f"  OK   {c} {name.get(c,c):<12} {q}  15후 {old15:,.2f} -> {new[15]:,.2f}  "
              f"비율 계산={calc:.2f} raw={hl:.2f}  법인세잔차비율={imp:.4f}")
    for c, q, why in rejects:
        print(f"  HOLD {c} {name.get(c,c):<12} {q}  {why}")

    # 스킵률: "raw 없음" 거부가 그 분기 타깃(축-C 실패) 수 대비 몇 %인지. 스킵은 성공이
    # 아니다 — raw/pdf 경로 계약이 다시 깨지면(inbox 20260901T0500Z 가 잡은 사고) 조용히
    # exit 0 으로 안 나가고 호출자가 알아채게 한다.
    targets_by_q: dict[str, int] = defaultdict(int)
    for c, q in targets:
        targets_by_q[q] += 1
    raw_missing_by_q: dict[str, int] = defaultdict(int)
    for c, q, why in rejects:
        if why == "raw 없음":
            raw_missing_by_q[q] += 1
    skip_breach = []
    for q in sorted(targets_by_q):
        n_t, n_m = targets_by_q[q], raw_missing_by_q.get(q, 0)
        pct = 100.0 * n_m / n_t if n_t else 0.0
        print(f"  스킵률 {q}: raw 없음 {n_m}/{n_t} ({pct:.0f}%)")
        if pct > 50.0:
            skip_breach.append((q, n_m, n_t, pct))
    for q, n_m, n_t, pct in skip_breach:
        print(f"  ABORT {q}: raw 없음 {n_m}/{n_t} ({pct:.0f}%) — 50% 초과, 원천 경로 자체를 "
              f"의심할 것 (스킵은 성공이 아니다)")

    if dry:
        print("(dry-run; 파일 안 씀)")
        return 1 if skip_breach else 0
    if not writes:
        return 1 if skip_breach else 0

    def fmt(x):
        return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")

    n = 0
    for c, q, new, _hl, _calc, _imp, _lo, _hi in writes:
        items = by_cq[(c, q)]
        for it, v in sorted(new.items()):
            row = items.get(it)
            if row is None:
                continue
            s = fmt(round(v, 2))
            if row.get("값_적용후") != s:
                row["값_적용후"] = s
                n += 1
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{n}셀 갱신, wrote {TARGET.name}")
    return 1 if skip_breach else 0


if __name__ == "__main__":
    raise SystemExit(main())
