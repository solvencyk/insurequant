# -*- coding: utf-8 -*-
"""orchestrator 발주(2026-08-24, iter-10) -- [지급여력비율의 경과조치 적용에 관한 사항]
"(1) 공통적용 경과조치 관련" 표의 **마지막 두 줄**을 신규 항목번호로 적재한다.

표 9줄 전체(구분 헤더 제외):
    지급여력비율 (%)                       <- 저장 안 함 (item27과 동일 개념, 헤드라인 소관)
    지급여력금액                           <- item52 (신규, 이 스크립트 -- 아래 "번호 충돌" 참고)
    기본자본                               <- item50 (기존, fix_20260822_tfi_tier_full_scan.py)
    보완자본                               <- item51 (기존)
    보완자본 한도 적용 전                   <- item47 (기존, fix_20260821_tier2_limit_lines.py)
    보완자본 한도                          <- item48 (기존)
    해약환급금 부족분 상당액 중 초과분       <- item49 (기존)
    (기발행 신종자본증권)                   <- item53 (신규, 이 스크립트)
    (기발행 후순위채무)                     <- item54 (신규, 이 스크립트)
    지급여력기준금액                        <- 저장 안 함 (item14전과 동일 개념, 스케일 앵커로만 사용)

## 왜 이 두 줄이 빠져 있었나

`fix_20260822_aia_kb_backlog.py`가 이미 한 번 발견했었다 -- "KB의 '(기발행 후순위채무)' 행
(2024.1Q=659,282백만 등 5개 분기 다 실값 존재)은 기존 47-51 스키마에 대응 항목번호가 없어
적재하지 않는다"(참고용으로 주석에만 기록). validation이 NH농협(KR0032) 2025.4Q를 발행사
자기모순 documented exception으로 등재하길 **거부**하면서(`validate_kics_disclosure.py`
`_TIER2_ISSUER_INCONSISTENT`의 `not_registered["KR0032 2025.4Q"]`) 다시 찾았다: raw p46에서
`697,899(item47전) + 447,254(item49) + 94,959(기발행 후순위채무) = 1,240,112 = item51전`이
소수점 없이 정확히 닫힌다 -- 발행사 자기모순이 아니라 **우리 구성식에 항이 빠진 것**이었다.

## 항목번호 -- **52는 애초 이 스크립트가 잡으려던 번호가 아니었다** (번호 충돌 정정)

47-51은 두 차례에 걸쳐 따로 번호가 붙어서(47/48/49가 먼저, 50/51이 나중) 항목번호 순서가
표의 인쇄 순서(기본자본→보완자본→한도적용전→한도→초과분)와 어긋나 있다. 처음엔 이번 두
메모행을 표에 인쇄된 순서 그대로 52/53(51 다음 정수)에 앉혔는데, **첫 dry-run 후 게이트를
돌리다가 충돌을 발견했다**: `src/solvency/validation/kics_json_rules.py`(축E
`50_tfi_tier_split_post` 주석)와 `TODO_validation.md`(§"parser 발주 3건" ②)가 이미
**"item52 신설(TFI 표 맨 윗줄 지급여력금액)"** 이라고 못박아 뒀다 -- validation이
`min(item1_전,item1_후) ≤ item50후+item51후 ≤ max(...)` 범위검사를 등식으로 승격하는 데
쓰려던 값이다. 신종자본증권/후순위채무로 52/53을 채웠으면 그 예약을 조용히 덮어써서
validation이 나중에 item52를 열었을 때 전혀 다른 개념(신종자본증권 발행액)을 만나게 됐을
것이다. 그래서 **52는 validation 요청대로 표 맨 윗줄 "지급여력금액"을 채우고**(같은 표·
같은 패스에서 이미 보고 있던 행이라 추가 스캔 비용 없음), 신종자본증권/후순위채무는 53/54로
한 칸씩 민다:
    52 = 지급여력금액 (TFI표, 공통적용경과조치) -- validation 예약분, 이번에 같이 채움
    53 = (기발행 신종자본증권)
    54 = (기발행 후순위채무)

## 자체검산 -- item51 == min(47,48) + 49 + item54(후순위채무)에만 신종자본증권을 넣지 않는다

item53(신종자본증권)는 개념상 **기본자본(Tier1)** 인정한도 항목이다(owner 확정,
`reference-kics-capital-tiering`: "신종자본증권 → 기본자본(Tier1) 분자 / 후순위채 →
보완자본(Tier2) 분자"). 이 표에 같이 인쇄되지만 item51(보완자본, Tier2)의 구성요소가 아니다 --
실측으로도 확인된다: 코리안리 2023.2Q는 신종자본증권=558,606(0 아님)인데도 기존
`min(47,48)+49`가 **이미 정확히 닫혀 있다**(51_tfi_tier2_composition 실측 7/7 통과 대상).
신종자본증권까지 더하면 이 버킷이 5,586.06억 어긋나며 깨진다 -- 그래서 자체검산 공식은
`item51 == min(47,48) + 49 + item54` 만 쓴다(52·53은 데이터로만 적재, 이 식엔 안 넣는다).

## 컬럼(적용전/적용후) -- 좌표로 판별, 가정하지 않는다

이 두 메모행은 **관찰 6/6 필링에서 전부 "적용 전" 컬럼에만 값이 인쇄되고 "적용 후" 컬럼은
공란**이다(NH농협·코리안리·흥국화재·메트라이프·카카오페이·롯데손해 word-좌표 전수 확인,
`scripts/_probes/probe_tfi_full_table_rows.py` + 개별 좌표 덤프). 그렇다고 "항상 전컬럼"으로
하드코딩하지 않는다 -- 표의 "지급여력기준금액" 종결행(두 값 다 확실히 존재)에서 두 컬럼의
우측정렬 x1 좌표를 앵커로 뽑아, 메모행 값의 x1이 어느 앵커에 더 가까운지로 매 (회사,분기)마다
판별한다. 값이 하나만 인쇄돼 있고 그 x1이 "후" 앵커에 더 가까우면 적용후로 기록한다 -- 방향을
가정하지 않고 좌표가 결정한다.

## 스케일

47/48/49/51이 **이미 마스터에 있는 버킷만** 대상으로 한다(그 표가 이미 위치·판독 확인된
버킷이라는 뜻). 이번에 그 표에서 다시 읽은 raw47/48/49/51(스케일 미확정)을 마스터의 기존
(이미 검증된) 스케일값과 비교해 비율을 구한다 -- item14 앵커를 새로 판별하지 않고 **이미 맞다고
확인된 값을 앵커로 재사용**한다. 여러 항목에서 서로 다른 깨끗한 배율이 나오면(모순) 쓰지 않고
CONFLICTING으로 보고한다.

Usage:
  ...python scripts/fix_20260824_tfi_capital_memo_rows.py --dry-run
  ...python scripts/fix_20260824_tfi_capital_memo_rows.py --dry-run --only KR0032
  ...python scripts/fix_20260824_tfi_capital_memo_rows.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import fitz  # noqa: E402

# 460버킷을 훑다 보면 malformed-xref 등 실제로 깨진 PDF가 섞여 있어 MuPDF C 레벨 경고가
# 뜬다 -- 그 경고를 찍는 내부 콜백이 (아래 stdout 재정비 이전에 바인딩된) 죽은 스트림을 써서
# `SystemError: null argument to internal routine`으로 전체가 죽는 걸 실측했다. 데이터를
# 잃는 게 아니라 콘솔 노이즈일 뿐이라 아예 끈다(fitz가 텍스트를 못 읽으면 우리 쪽 함수가
# 빈 dict/None으로 정상 보고한다 -- 이 표시를 끈다고 실패가 숨겨지지 않는다).
fitz.TOOLS.mupdf_display_errors(False)
fitz.TOOLS.mupdf_display_warnings(False)

import fix_20260821_tier2_limit_lines as T2  # noqa: E402  (reuse _num, _pdf, q2p, NUMRE, ZERO, DECOR)
import fix_20260822_tfi_tier_full_scan as T3  # noqa: E402  (reuse extract_tfi_full for scale anchor)

# T2 와 T3 는 **각자** import 시점에 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, ...)` 를
# 실행한다(한글 콘솔 출력용, 두 파일 다 독립적으로 만들어진 기존 스크립트라 이 파일을 고치지
# 않는다). 이 스크립트가 **둘 다** import 하면 재래핑이 2번 연쇄로 일어나는데, 실측 결과
# (스크래치패드 driver1~driver5 로 격리 재현) **직전 래퍼가 orphan 되며 close() 될 때 공유
# 중인 원본 buffer 객체 자체가 닫힌다** -- `sys.__stdout__` 까지 같이 죽는다(진짜 OS fd(1)는
# 안 죽는다, `os.write(1,...)` 는 살아있음 확인). 그래서 fd 를 직접 다시 연다 -- 어떤 Python
# 레벨 래퍼가 이미 죽었든 상관없이 새 텍스트스트림을 fd 1 위에 독립적으로 세운다.
import os  # noqa: E402
sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

TARGET = REPO / "kics_disclosure.json"
PROVENANCE_OUT = REPO / "data" / "_derived" / "tfi_capital_memo_rows_provenance.json"

ITEM_LABELS = {
    52: "지급여력금액(TFI표, 공통적용경과조치)",
    53: "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    54: "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
}
# item52 = 표 맨 윗줄 "지급여력금액" -- **애초 이 스크립트가 안 쓰려던 번호였으나
# `src/solvency/validation/kics_json_rules.py`(축E `50_tfi_tier_split_post` 주석)와
# `TODO_validation.md`(§"parser 발주 3건" ②)가 이미 "item52 신설(TFI 표 맨 윗줄 지급여력금액)"
# 이라고 못박아 뒀다 -- validation 이 range-check 를 등식으로 승격하는 데 쓰려는 값이다.
# 신종자본증권/후순위채무 를 52/53 에 앉히면 이 예약과 충돌해 그 축을 조용히 오염시킨다
# (2026-08-24 첫 dry-run 후 게이트 로그에서 발견 -- "item52(TFI표 자신의 지급여력금액 행)"
# 이라는 문구를 보고서야 알았다). 그래서 **52 는 validation 요청대로 채우고, 신종자본증권/
# 후순위채무는 53/54 로 한 칸씩 민다.** 어차피 같은 표·같은 패스에서 이 행도 이미 보고
# 있었다(옛 이름 `idx_end`/앵커로만 쓰고 값은 버렸었음) -- 추가 스캔 비용 없음.
LABEL_HEADLINE_CAPITAL = "지급여력금액"  # item52 판별용 정확매칭(단독행 -- "가.지급여력금액"과 다름)
LABEL_NEW_STOCK = "신종자본증권"   # item53 판별용 부분 문자열
LABEL_SUB_DEBT = "후순위채무"      # item54 판별용 부분 문자열
# "기발행"(issued)의 오식/변형 -- 신한라이프(KR0094) 실측: 원문이 "(기발생 신종자본증권)"/
# "(기발생 후순위채무)"로 인쇄된다(발행->발생, 한 글자 오식이 소스 PDF 자체에 있음). "행"/"생"
# 둘 다 받는다 -- 값을 지어내는 게 아니라 라벨 오탈자를 관대하게 받는 것뿐이다.
LABEL_ISSUED_PREFIXES = ("기발행", "기발생")
ROW_TOL = 3.0                      # 같은 물리행으로 묶는 y 허용오차(pt) -- 행간 최소 9pt 대비 충분히 좁음
EDGE_TOL_HINT = 8.0                # 참고용(강제 컷오프 아님, nearest-edge 판별이라 사실상 미사용)


def _label_norm(tokens: list[tuple[float, float, str]]) -> str:
    parts = []
    for _x0, _x1, t in tokens:
        s = t.strip()
        if s == "":
            continue
        if T2.NUMRE.match(s) or s in T2.ZERO:
            continue
        parts.append(s)
    return "".join(parts).replace(" ", "")


def _value_tokens(tokens: list[tuple[float, float, str]]):
    vals = []
    for x0, x1, t in tokens:
        s = t.strip()
        if s == "" or s in T2.DECOR:
            continue
        if T2.NUMRE.match(s) or s in T2.ZERO:
            vals.append((x1, s))
    return vals


def _cluster_rows(words, ytol: float = ROW_TOL):
    """fitz words((x0,y0,x1,y1,text,...)) -> [(row_y, [(x0,x1,text), ...] sorted by x0)], y오름차순.

    스트림 순서가 아니라 좌표로 행을 묶는다 -- 교보생명류(fitz 텍스트순서 뒤섞임)에서도
    안전하게 동작해야 하므로 stream order에 의존하지 않는다.

    한화생명류(실측: KR0068 2023.3Q)는 라벨 토큰이 **동일 좌표에 그대로 겹쳐 두 번** 나온다
    ("구","분","경과조치","적용","전" 등 전부 (x0,y0) 완전 일치 중복) -- dedup 없이 이으면
    "보완자본보완자본한도한도" 처럼 라벨 정확매칭이 깨진다. (x0,y0,x1,y1,text) 완전일치만
    제거한다(다른 좌표의 진짜 반복 라벨은 안 건드림)."""
    seen: set[tuple] = set()
    uniq = []
    for w in words:
        if w[4].strip() == "":
            continue
        key = (round(w[0], 1), round(w[1], 1), round(w[2], 1), round(w[3], 1), w[4])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(w)
    ws = sorted(uniq, key=lambda w: (w[1], w[0]))
    rows: list[tuple[float, list]] = []
    cur: list[tuple[float, float, str]] = []
    cur_y = None
    for w in ws:
        x0, y0, x1, _y1, txt = w[0], w[1], w[2], w[3], w[4]
        if cur_y is None or abs(y0 - cur_y) <= ytol:
            cur.append((x0, x1, txt))
            if cur_y is None:
                cur_y = y0
        else:
            rows.append((cur_y, sorted(cur, key=lambda t: t[0])))
            cur = [(x0, x1, txt)]
            cur_y = y0
    if cur:
        rows.append((cur_y, sorted(cur, key=lambda t: t[0])))
    return rows


def _extract_memo_rows_from_words(words) -> tuple[dict | None, str]:
    """words 리스트(한 페이지, 또는 페이지 경계를 Y-offset 으로 이어붙인 여러 페이지)에서
    item52/53 후보를 찾는다.

    -> ({"52": (pre,post,reason,found_row_bool), "53": (...), "edges": (edge_pre_x1,edge_post_x1)},
        "OK") 또는 (None, 사유)."""
    rows = _cluster_rows(words)
    idx48 = next((i for i, (_y, tok) in enumerate(rows) if _label_norm(tok) == "보완자본한도"), None)
    if idx48 is None:
        return None, "NO_ITEM48_ROW"

    # 윈도우 끝 경계: idx48 뒤 첫 "지급여력기준금액" 라벨(값 개수는 안 따진다 -- 그건 별개
    # 실패양식, 현대해상 2023.4Q 실측: 이 행이 컬럼 1개만 인쇄돼도 라벨 자체는 정상 등장한다).
    idx_end = next((i for i in range(idx48 + 1, len(rows))
                     if _label_norm(rows[i][1]) == "지급여력기준금액"), None)
    if idx_end is None:
        idx_end = min(len(rows), idx48 + 12)  # 종결 라벨 자체가 없으면 관대한 상한

    # 컬럼 x1 앵커: **item48(보완자본 한도) 자신의 행**을 1순위로 쓴다 -- 관찰 전수에서
    # 이 행이 2값을 안 낸 사례가 없었다(반해 "지급여력기준금액"은 컬럼이 같아도 1값만
    # 인쇄하는 필링이 있다 -- 현대해상 2023.4Q: SCR이 전=후라 한 셀로 병합 인쇄됨).
    # 실패하면 지급여력기준금액 -> item47 -> item51 순으로 폴백한다.
    def _edges_from(idx):
        if idx is None:
            return None
        vals = _value_tokens(rows[idx][1])
        if len(vals) >= 2:
            xs = sorted(v[0] for v in vals)
            return (xs[0], xs[1])
        return None

    # 단일컬럼(전=후 병합) 표 판별: item48 자신이 값 1개뿐이면(하나손해·BNP카디프 일부 분기
    # 실측 -- "(1) 공통적용 경과조치 관련 : 해당사항 없음", 자본증권 발행이력 자체가 없어
    # 경과조치 적용 전/후 구분이 무의미) **표 전체가 1값 레이아웃**이다(마스터의 기존
    # item47-51 도 이 경우 값==값_적용후로 이미 동일하게 실려 있다 -- 그 관행을 그대로 잇는다).
    v48 = _value_tokens(rows[idx48][1])
    n48 = len(v48)
    single_column = (n48 == 1)
    # 이 페이지에서 **직접** 읽은 item48 원문값(스케일 미확정) -- T3(라인 기반 재추출)가 실패
    # 하거나 다른 표를 잘못 짚는 버킷(실측: 삼성생명 KR0069 2025.4Q, 교보생명 KR0073 2023.1Q
    # -- 라벨 순서가 밀리거나 텍스트스트림이 뒤섞여 T3 가 엉뚱한 줄을 47/48/49/51 로 반환)의
    # 스케일 판별을 좌표기반 재확인으로 보강하는 데 쓴다. 같은 페이지·같은 idx48 행에서 뽑은
    # 값이라 메모행과 페이지 일치가 보장된다(T3 의 라인기반 결과와 달리 다른 표를 짚었을
    # 위험이 없다).
    raw48_here = (T2._num(v48[0][1]), T2._num(v48[1][1])) if n48 >= 2 else (
        (T2._num(v48[0][1]), None) if n48 == 1 else (None, None))

    edges = None
    if not single_column:
        edges = _edges_from(idx48)
        if edges is None:
            edges = _edges_from(idx_end)
        if edges is None:
            idx47 = next((i for i in range(max(0, idx48 - 6), idx48)
                           if _label_norm(rows[i][1]) == "보완자본한도적용전"), None)
            edges = _edges_from(idx47)
        if edges is None:
            idx51 = next((i for i in range(max(0, idx48 - 6), idx48)
                           if _label_norm(rows[i][1]) == "보완자본"), None)
            edges = _edges_from(idx51)
        if edges is None:
            return None, "NO_ANCHOR_ROW(2값 낼 수 있는 행 없음)"

    row_a = row_b = None
    for i in range(idx48 + 1, idx_end):
        lbl = _label_norm(rows[i][1])
        if not any(p in lbl for p in LABEL_ISSUED_PREFIXES):
            continue
        if LABEL_NEW_STOCK in lbl and row_a is None:
            row_a = rows[i][1]
        elif LABEL_SUB_DEBT in lbl and row_b is None:
            row_b = rows[i][1]

    # item52 = 표 맨 윗줄 "지급여력금액"(단독 라벨, "가.지급여력금액"과 정확매칭으로 구분).
    # idx48 **이전** 좁은 창(최대 10행)에서 찾는다 -- 정상 레이아웃은 지급여력금액->기본자본->
    # 보완자본->한도적용전 순으로 idx48 바로 몇 줄 위다.
    idx_hg = next((i for i in range(max(0, idx48 - 10), idx48)
                    if _label_norm(rows[i][1]) == LABEL_HEADLINE_CAPITAL), None)
    row_hg = rows[idx_hg][1] if idx_hg is not None else None

    def classify(tokens):
        if tokens is None:
            return None, None, "행_없음", False
        vals = _value_tokens(tokens)
        if not vals:
            return None, None, "라벨만_값없음", True
        if len(vals) >= 2:
            vs = sorted(vals, key=lambda v: v[0])
            return T2._num(vs[0][1]), T2._num(vs[1][1]), "2컬럼", True
        x1, raw = vals[0]
        if single_column:
            v = T2._num(raw)
            return v, v, "단일컬럼표(전=후 병합, item48도 1값)", True
        d_pre, d_post = abs(x1 - edges[0]), abs(x1 - edges[1])
        if d_pre <= d_post:
            return T2._num(raw), None, f"1컬럼_전(x1={x1:.1f} vs 전{edges[0]:.1f}/후{edges[1]:.1f})", True
        return None, T2._num(raw), f"1컬럼_후(x1={x1:.1f} vs 전{edges[0]:.1f}/후{edges[1]:.1f})", True

    hg_pre, hg_post, hg_reason, hg_found = classify(row_hg)
    a_pre, a_post, a_reason, a_found = classify(row_a)
    b_pre, b_post, b_reason, b_found = classify(row_b)
    if not hg_found and not a_found and not b_found:
        return None, "세_라벨_모두_미검출(윈도우 안)"
    return {
        "52": (hg_pre, hg_post, hg_reason, hg_found),
        "53": (a_pre, a_post, a_reason, a_found),
        "54": (b_pre, b_post, b_reason, b_found),
        "edges": edges,
        "raw48_here": raw48_here,
    }, "OK"


_PAGE_Y_OFFSET = 100000.0  # 페이지 병합 시 다음 페이지 y0 에 더하는 값 -- ytol(3.0)보다
                            # 압도적으로 커서 페이지 경계를 넘는 오검출 클러스터링이 없다.


def _find_memo_rows(pdf_path: Path):
    doc = fitz.open(pdf_path)
    try:
        texts = [doc[i].get_text() for i in range(doc.page_count)]
        matched = [i for i, t in enumerate(texts)
                   if "공통적용" in t and "보완자본" in t and "한도" in t]
        if not matched:
            return None, "NO_MATCHED_PAGE", None
        candidates = list(dict.fromkeys(matched + [i + 1 for i in matched if i + 1 < len(texts)]))
        last_reason = "NO_CANDIDATE_PAGE_HIT"
        for pi in candidates:
            result, reason = _extract_memo_rows_from_words(doc[pi].get_text("words"))
            if result is not None:
                return result, "OK", pi + 1
            last_reason = reason
        # 단일 페이지로 못 찾으면 -- 표가 페이지 경계에서 쪼개진 경우다(실측: 동양생명
        # KR0087 2024.1Q -- item47/48 은 p12(0idx=11), item49/메모행/앵커는 p13(0idx=12)에
        # 있다). 인접한 두 후보 페이지를 Y-offset 으로 이어붙여 하나의 표처럼 재시도한다.
        for pi, pj in zip(candidates, candidates[1:]):
            if pj != pi + 1:
                continue
            merged = list(doc[pi].get_text("words"))
            for w in doc[pj].get_text("words"):
                merged.append((w[0], w[1] + _PAGE_Y_OFFSET, w[2], w[3] + _PAGE_Y_OFFSET, *w[4:]))
            result, reason = _extract_memo_rows_from_words(merged)
            if result is not None:
                return result, "OK", f"{pi + 1}+{pj + 1}(병합)"
            last_reason = reason
        return None, last_reason, None
    finally:
        doc.close()


def _infer_scale(found_t3: dict, master_pins: dict):
    """마스터에 이미 있는 47/48/49/51(pre)을 앵커로, 이번에 재추출한 raw 값과의 비율로
    스케일(1.0 또는 0.01)을 판별한다. item14 재판별이 아니라 **이미 검증된 마스터 값** 재사용."""
    ratios = []
    for it in (47, 48, 49, 51):
        raw = found_t3.get(it)
        mv = master_pins.get(it)
        if raw is None or mv is None:
            continue
        rp, mp = raw[0], mv[0]
        if rp is None or mp is None:
            continue
        if abs(rp) < 1e-9:
            continue
        if abs(rp) < 0.005 and abs(mp) < 0.005:
            continue
        ratios.append((it, mp / rp))
    resolved = []
    for it, ratio in ratios:
        if 0.98 < ratio < 1.02:
            resolved.append((it, 1.0))
        elif 0.0098 < ratio < 0.0102:
            resolved.append((it, 0.01))
    if not resolved:
        # 47/48/49/51 전부 사실상 0(트리비얼) 인 회사군 -- 스케일 무관(0 x 무엇이든 0)
        trivial = all(
            (found_t3.get(it) is None or abs(found_t3[it][0] or 0.0) < 0.005)
            for it in (47, 48, 49, 51)
        )
        if trivial:
            return 1.0, "ALL_ZERO_TRIVIAL", ratios
        return None, "UNRESOLVED", ratios
    scales = {s for _it, s in resolved}
    if len(scales) > 1:
        return None, "CONFLICTING", ratios
    return resolved[0][1], f"MATCH_ITEM{resolved[0][0]}", ratios


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드 전 row_count = {len(data):,}")

    by_c: dict[str, set] = {}
    info: dict[str, dict] = {}
    existing = set()
    master_pins: dict[tuple, dict] = {}  # (c,q) -> {47:(pre,post),48:...,49:...,51:...}
    m51_pre: dict[tuple, float] = {}
    m1_pre: dict[tuple, float] = {}  # item1(헤드라인 지급여력금액) -- item52 스케일 3차 폴백용

    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        by_c.setdefault(c, set()).add(q)
        info.setdefault(c, {"원수사명": r.get("원수사명"), "티커": r.get("티커"),
                             "생손보여부": r.get("생손보여부")})
        it = int(r["항목번호"])
        existing.add((c, q, it))
        if it in (47, 48, 49, 51):
            master_pins.setdefault((c, q), {})[it] = (T2._num(r.get("값")), T2._num(r.get("값_적용후")))
            if it == 51:
                m51_pre[(c, q)] = T2._num(r.get("값"))
        if it == 1:
            m1_pre[(c, q)] = T2._num(r.get("값"))

    scope = sorted(master_pins.keys())  # 47/48/49/51 중 하나라도 이미 있는 버킷만 대상
    print(f"대상 버킷(47/48/49/51 중 하나라도 기존 적재) = {len(scope)}")

    new_rows = []
    census = []            # (c, name, q, status, detail)
    provenance = []
    selfcheck_rows = []    # (c, q, item51, item47, item48, item49, item53_val, item53_state, old_closed, new_closed, diff_old, diff_new)

    for c, q in scope:
        if only and c != only:
            continue
        name = info[c]["원수사명"]
        pdf = T2._pdf(T2.q2p(q), c)
        if pdf is None:
            census.append((c, name, q, "raw없음", ""))
            continue

        found_t3, _anchor_t3, reason_t3 = T3.extract_tfi_full(pdf)
        scale, scale_method, ratios = (
            _infer_scale(found_t3, master_pins.get((c, q), {})) if found_t3 else (None, "T3_미검출:" + (reason_t3 or ""), [])
        )

        # T3(라인기반 재추출) 는 텍스트스트림이 뒤섞인 필링(교보생명류)에서 라벨 자체를
        # 못 찾거나, 드물게 **다른 표를 짚어** 47/48/49/51 이 항목번호끼리 안 맞고 밀려서
        # 나온다(실측: 삼성생명 KR0069 2025.4Q -- T3 raw47 이 실제로는 master 의 48 과, raw51
        # 이 master 의 47 과 대응됨. `_infer_scale` 는 같은 항목번호끼리만 비교하므로 이 밀림을
        # 스스로 걸러 UNRESOLVED 를 낸다 -- 다행히 오탐은 아니지만 스케일을 못 구한다).
        # 이럴 때 좌표기반 재확인(`_find_memo_rows` 가 같은 페이지에서 직접 읽은 item48
        # 원문값)을 2차 앵커로 쓴다 -- 메모행과 **같은 페이지·같은 행**에서 나온 값이라
        # T3 재추출보다 그 페이지 자신에 대해서는 더 믿을 만하다.
        memo, memo_status, page_used = _find_memo_rows(pdf)

        # 2026-08-24 버그수정(orchestrator 발주, inbox 20260824T0400Z 항목A) -- ALL_ZERO_TRIVIAL
        # 은 "47/48/49/51 이 전부 0 이라 그 넷의 스케일은 무관하다"는 판정일 뿐인데, 그 스케일
        # (1.0)을 같은 버킷의 item52(지급여력금액)에도 무비판적으로 적용해 카카오페이(KR1098)
        # 5개 분기에서 item52 가 100배 부풀어 실렸다(raw 38,147백만=381.47억인데 38147 그대로
        # 적재됨). item52 는 47/48/49/51 과 달리 채무성자본이 0인 회사도 대개 실값(억대)이라
        # "0 x 무엇=0" 지름길이 안 통한다 -- ALL_ZERO_TRIVIAL 이 떴어도 item52 자체를 마스터
        # item1(헤드라인 지급여력금액)과 대조해 재확인하고, 명확히 다른 배율이 나오면 그걸로
        # 덮어쓴다(애매하면 ALL_ZERO_TRIVIAL 유지 -- 억지로 안 바꿈).
        if scale_method == "ALL_ZERO_TRIVIAL" and memo is not None:
            hg_pre_raw = memo["52"][0]
            m1v = m1_pre.get((c, q))
            if hg_pre_raw is not None and m1v is not None and abs(hg_pre_raw) >= 1e-9:
                ratio1 = m1v / hg_pre_raw
                if 0.0098 < ratio1 < 0.0102:
                    scale, scale_method = 0.01, "ITEM52_OVERRIDES_ALL_ZERO_TRIVIAL"
                elif 0.98 < ratio1 < 1.02:
                    scale, scale_method = 1.0, "ALL_ZERO_TRIVIAL_CONFIRMED_BY_ITEM52"

        if scale is None and memo is not None:
            raw48_here = memo.get("raw48_here", (None, None))
            m48 = master_pins.get((c, q), {}).get(48)
            if raw48_here[0] is not None and m48 is not None and m48[0] is not None:
                rp = raw48_here[0]
                if abs(rp) >= 1e-9:
                    ratio = m48[0] / rp
                    if 0.98 < ratio < 1.02:
                        scale, scale_method = 1.0, "COORD_ITEM48_ANCHOR"
                    elif 0.0098 < ratio < 0.0102:
                        scale, scale_method = 0.01, "COORD_ITEM48_ANCHOR"
            if scale is None:
                # item48 도 트리비얼(=0/0, 신한이지 KR0051 실측)이면 못 쓴다 -- item52(TFI표
                # 지급여력금액) vs 마스터 item1(헤드라인 지급여력금액)을 3차 앵커로 쓴다. 두
                # 값은 TFI 효과분만큼 다를 수 있어 **동일값이 아니지만**, 배율 오류(100배)는
                # 그 차이보다 훨씬 커서 좁은 밴드로도 자릿수 판별엔 안전하다(실측: KR0051
                # 2023.1Q raw52=119,658 vs item1=1,197 -> ratio=0.01000(diff 0.04%)).
                hg_pre_raw = memo["52"][0]
                m1v = m1_pre.get((c, q))
                if hg_pre_raw is not None and m1v is not None and abs(hg_pre_raw) >= 1e-9:
                    ratio1 = m1v / hg_pre_raw
                    if 0.98 < ratio1 < 1.02:
                        scale, scale_method = 1.0, "ITEM52_VS_ITEM1_ANCHOR"
                    elif 0.0098 < ratio1 < 0.0102:
                        scale, scale_method = 0.01, "ITEM52_VS_ITEM1_ANCHOR"
            if scale is None:
                # item48 앵커도 못 구했으면 마지막으로 -- **이번에 쓸 세 항목(52/53/54) 원문값이
                # 전부** 이미 사실상 0(트리비얼)이면 스케일은 애초에 결과에 영향이 없다
                # (0 x 무엇=0). item52(지급여력금액)는 큰 자본값이라 거의 항상 non-trivial이므로
                # 이 지름길은 사실상 "hg 자체가 결측이고 53/54 만 0" 인 경우에만 발동한다 --
                # hg 가 실값인데 스케일을 몰라 1.0 을 임의로 쓰면 최대 100배 오류라 안전 우선.
                hg_pre, hg_post = memo["52"][0], memo["52"][1]
                a_pre, a_post = memo["53"][0], memo["53"][1]
                b_pre, b_post = memo["54"][0], memo["54"][1]
                vals = [v for v in (hg_pre, hg_post, a_pre, a_post, b_pre, b_post) if v is not None]
                if vals and all(abs(v) < 0.005 for v in vals):
                    scale, scale_method = 1.0, "MEMO_ALL_TRIVIAL"

        prov = {
            "원보험사코드": c, "원수사명": name, "공시분기": q,
            "scale": scale, "scale_method": scale_method,
            "scale_ratios": [{"item": it, "ratio": round(rt, 6)} for it, rt in ratios],
            "memo_status": memo_status, "page_used": page_used,
            "raw_52_지급여력금액": memo["52"][:3] if memo else None,
            "raw_53_신종자본증권": memo["53"][:3] if memo else None,
            "raw_54_후순위채무": memo["54"][:3] if memo else None,
            "edges": memo["edges"] if memo else None,
        }
        provenance.append(prov)

        if memo is None:
            census.append((c, name, q, "메모행_미검출", memo_status))
            continue
        if scale is None:
            census.append((c, name, q, "스케일불명", scale_method))
            continue

        n_written = 0
        written = []
        for it_key, item_no in (("52", 52), ("53", 53), ("54", 54)):
            pre_raw, post_raw, _reason, _found = memo[it_key]
            if (c, q, item_no) in existing:
                continue
            pre = None if pre_raw is None else round(pre_raw * scale, 2)
            post = None if post_raw is None else round(post_raw * scale, 2)
            if pre is None and post is None:
                continue
            row = {
                "원보험사코드": c, "원수사명": name,
                "티커": info[c]["티커"], "생손보여부": info[c]["생손보여부"],
                "항목번호": item_no, "항목명": ITEM_LABELS[item_no], "공시분기": q,
            }
            if pre is not None:
                row["값"] = _fmt(pre)
            if post is not None:
                row["값_적용후"] = _fmt(post)
            new_rows.append(row)
            n_written += 1
            written.append(item_no)

        if n_written:
            census.append((c, name, q, "OK", f"{n_written}개 항목 신규 {written} scale={scale}"))
        else:
            census.append((c, name, q, "이미완비_또는_공란", ""))

        # --- 자체검산: item51 == min(47,48) + 49 + item54(후순위채무) -- 52/53(지급여력금액·
        # 신종자본증권)는 이 식엔 안 넣는다(52는 다른 개념=validation 축E 용, 53=Tier1 개념) ---
        i47 = master_pins.get((c, q), {}).get(47, (None, None))[0]
        i48 = master_pins.get((c, q), {}).get(48, (None, None))[0]
        i49 = master_pins.get((c, q), {}).get(49, (None, None))[0]
        i51 = m51_pre.get((c, q))
        pre54_raw, _post54_raw, _r54, found54 = memo["54"]
        item54_val = None if pre54_raw is None else round(pre54_raw * scale, 2)
        if i47 is not None and i48 is not None and i49 is not None and i51 is not None:
            old_formula = min(i47, i48) + i49
            new_formula = old_formula + (item54_val or 0.0)
            diff_old = i51 - old_formula
            diff_new = i51 - new_formula
            old_closed = abs(diff_old) <= 0.05
            new_closed = abs(diff_new) <= 0.05
            item54_state = (
                "결측" if not found54 else
                ("명시0" if (item54_val is not None and abs(item54_val) < 0.005) else "실값")
            )
            selfcheck_rows.append((c, name, q, i51, i47, i48, i49, item54_val, item54_state,
                                    old_closed, new_closed, round(diff_old, 2), round(diff_new, 2)))

    # ---------------- 리포트 ----------------
    ok = sum(1 for *_x, s, _d in census if s == "OK")
    print(f"\n스캔 버킷 = {len(census)} | 신규기록 OK = {ok} | 이미완비/공란 = "
          f"{sum(1 for *_x,s,_d in census if s=='이미완비_또는_공란')} | raw없음 = "
          f"{sum(1 for *_x,s,_d in census if s=='raw없음')} | 표_미검출(T3) = "
          f"{sum(1 for *_x,s,_d in census if s=='표_미검출(T3)')} | 메모행_미검출 = "
          f"{sum(1 for *_x,s,_d in census if s=='메모행_미검출')} | 스케일불명 = "
          f"{sum(1 for *_x,s,_d in census if s=='스케일불명')}")
    print(f"신규 셀 = {len(new_rows)}건 (item52_지급여력금액 {sum(1 for r in new_rows if r['항목번호']==52)}"
          f" / item53_신종자본증권 {sum(1 for r in new_rows if r['항목번호']==53)}"
          f" / item54_후순위채무 {sum(1 for r in new_rows if r['항목번호']==54)})")

    problems = [(c, n, q, s, d) for c, n, q, s, d in census
                if s not in ("OK", "이미완비_또는_공란")]
    if problems:
        print(f"\n=== 미해결 버킷 ({len(problems)}) ===")
        for c, n, q, s, d in problems:
            print(f"  {c} {n} {q}: {s} -- {d}")

    print(f"\n=== 자체검산: item51 == min(47,48)+49[+item54_후순위채무] ({len(selfcheck_rows)}버킷) ===")
    old_closed_n = sum(1 for r in selfcheck_rows if r[9])
    new_closed_n = sum(1 for r in selfcheck_rows if r[10])
    regressed = [r for r in selfcheck_rows if r[9] and not r[10]]
    newly_closed = [r for r in selfcheck_rows if not r[9] and r[10]]
    still_broken = [r for r in selfcheck_rows if not r[9] and not r[10]]
    print(f"  기존식(min+49) 닫힘 {old_closed_n} / 안닫힘 {len(selfcheck_rows)-old_closed_n}")
    print(f"  신규식(+item54) 닫힘 {new_closed_n} / 안닫힘 {len(selfcheck_rows)-new_closed_n}")
    print(f"  회귀(기존 닫혔는데 새 항 때문에 깨짐) = {len(regressed)}건")
    if regressed:
        for c, n, q, i51, i47, i48, i49, v54, st54, *_r in regressed:
            print(f"    [회귀!] {c} {n} {q}: item54={v54}({st54})")
    print(f"  신규닫힘(item54 덕에 새로 닫힘) = {len(newly_closed)}건")
    for c, n, q, i51, i47, i48, i49, v54, st54, _oc, _nc, d_old, d_new in newly_closed:
        print(f"    [신규닫힘] {c} {n} {q}: item51={i51:g} old_diff={d_old:g} -> new_diff={d_new:g} item54={v54}({st54})")
    print(f"  여전히 안닫힘 = {len(still_broken)}건 (강제로 안 맞춤, 목록만)")
    for c, n, q, i51, i47, i48, i49, v54, st54, _oc, _nc, d_old, d_new in still_broken:
        print(f"    [미해결] {c} {n} {q}: item51={i51:g} 47={i47:g} 48={i48:g} 49={i49:g} "
              f"item54={v54}({st54}) old_diff={d_old:g} new_diff={d_new:g}")

    if only is None:
        PROVENANCE_OUT.parent.mkdir(parents=True, exist_ok=True)
        PROVENANCE_OUT.write_text(
            json.dumps({
                "generated_by": "scripts/fix_20260824_tfi_capital_memo_rows.py",
                "총버킷": len(census),
                "신규셀": len(new_rows),
                "selfcheck": {
                    "총": len(selfcheck_rows),
                    "기존식_닫힘": old_closed_n,
                    "신규식_닫힘": new_closed_n,
                    "회귀": [{"code": r[0], "name": r[1], "quarter": r[2], "item54": r[7], "state": r[8]}
                             for r in regressed],
                    "신규닫힘": [{"code": c, "name": n, "quarter": q, "item51": i51,
                                 "diff_old": d_old, "diff_new": d_new, "item54": v54}
                                for c, n, q, i51, _i47, _i48, _i49, v54, _st54, _oc, _nc, d_old, d_new
                                in newly_closed],
                    "미해결": [{"code": c, "name": n, "quarter": q, "item51": i51, "item47": i47,
                               "item48": i48, "item49": i49, "item54": v54, "state": st54,
                               "diff_old": d_old, "diff_new": d_new}
                              for c, n, q, i51, i47, i48, i49, v54, st54, _oc, _nc, d_old, d_new
                              in still_broken],
                },
                "records": provenance,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nprovenance -> {PROVENANCE_OUT}")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0
    if not new_rows:
        print("쓸 셀 없음")
        return 0

    data.extend(new_rows)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(new_rows)}행 INSERT, wrote {TARGET.name} "
          f"(row_count {len(data)-len(new_rows):,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
