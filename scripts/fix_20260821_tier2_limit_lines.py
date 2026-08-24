# -*- coding: utf-8 -*-
"""inbox 20260821T1425Z (validation) — [지급여력비율의 경과조치 적용에 관한 사항]
1) 공통적용 경과조치 표에서 기본자본 다리(item2 = item4 - (item12-한도초과) - item13)를
닫는 3줄을 신규 항목번호 47/48/49로 적재한다.

  47 = 보완자본 한도 적용 전
  48 = 보완자본 한도               (검산: SCR(=경과조치 적용전 지급여력기준금액, item14전) x 50%)
  49 = 해약환급금 부족분 상당액 중 해약환급금 상당액 초과분

번호 선택 근거: 마스터의 기존 항목번호는 1-46(핵심 1-28 + 생명장기 29-35 + 시장 36-40 +
금리IRR 41-46)까지 전부 사용 중 — 47부터가 최초 미사용 구간이다.

단위: **표 캡션("(단위: 백만원, %)")을 맹신하지 않는다.** 티켓의 3개 검증 사례(처브라이프·
푸본현대·IBK연금)에서는 백만원이 맞았지만, 전사 스캔 후 anchor 검산을 돌려보니 439건 중
128건(29%)이 **이미 억원**이었다(예: 메리츠화재 2023.1Q — 표 캡션은 백만원인데 실제 인쇄된
숫자 115,146 이 그대로 마스터의 기존 item14전(56,947, 억원)과 정확히 같은 자리수). 회사·분기별로
캡션과 실제 인쇄 단위가 어긋나는 사례가 있다는 뜻 — **표 자체의 '지급여력기준금액' 종결행을
앵커로 매 (회사,분기)마다 스케일을 직접 판별**한다(마스터 기존 item14전/후와 대조,
`rebuild_combined_transition_after.py`가 이미 쓰는 것과 같은 앵커링 방법론). 비율이 1(이미 억원)도
100(백만원, ÷100 필요)도 아니면 **적재하지 않고 애매로 보고**한다(틀린 값보다 빈 칸).

스코프: `_TRANSITION_APPLIERS`(선택경과조치 18사) 한정이 아니다 — "1) 공통적용 경과조치"는
회사 대부분에 존재하는 섹션이라(validation 원 조사 473검사가 18사를 넘는 회사를 포함) 마스터의
전체 (회사,분기) 488건을 스캔한다. 텍스트가 없는(스캔본) PDF는 자연히 미검출로 남는다(빈 칸
정책 — 억지로 만들지 않는다).

Usage:
  ...python scripts/fix_20260821_tier2_limit_lines.py --dry-run
  ...python scripts/fix_20260821_tier2_limit_lines.py
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"
DISCLOSURE = REPO / "data" / "disclosure"
PROVENANCE_OUT = REPO / "data" / "_derived" / "tier2_scale_provenance.json"

# "ㅡ"(U+3161 HANGUL LETTER EU)는 박스드로잉 대시(─, U+2500)와 육안으로 거의 구분 안 되지만
# 다른 코드포인트다. 라이나생명 등 일부 필링이 "해당없음"을 이 한글 채움문자로 인쇄한다
# (2026-08-21 발견 — 이걸 못 읽어서 item47 행 전체가 결측 처리됐었다).
ZERO = {"-", "─", "–", "—", "ㅡ", "", "0"}
DASH = {"-", "─", "–", "—", "ㅡ"}
NUMRE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")
DECOR = {"·", "‧", "∙", "(", ")", "%", "(%)", "|", ",", " "}

ITEM_LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
}


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


def q2p(q):
    y, qq = q.split(".")
    return f"FY{y}_Q{qq[0]}"


def _pdf(period: str, code: str):
    raw = DISCLOSURE / period / "raw"
    pdfs = sorted(raw.glob(f"{code}_*.pdf"))
    if not pdfs:
        return None
    am = [p for p in pdfs if "_amended" in p.name]
    return max(am or pdfs, key=lambda p: p.stat().st_size)


def _collect_values(lines: list[str], start: int, need: int = 2):
    """lines[start:] 에서 숫자 need개를 모은다. -> (vals, next_index).

    일부 필링(DB생명 2026.1Q 등)은 전/후 두 값이 **한 줄에 공백으로 붙어** 나온다
    ("           743,755                   743,755 "). 예전엔 그 줄 전체를 공백제거
    후 한 토큰으로 봐서 "743,755743,755" 처럼 두 수가 이어붙은 채로 NUMRE 를 통과해
    버렸다(콤마만 있고 공백이 없어 정규식이 그냥 받아들임 → 100만배 사고). 줄을
    공백 기준으로 먼저 쪼갠 뒤 토큰 단위로 판정해 이 병합을 막는다 — 한 줄에 값이
    하나뿐인 (더 흔한) 경우는 예전과 동일하게 동작한다."""
    vals: list[float | None] = []
    j = start
    while j < len(lines) and len(vals) < need:
        toks = lines[j].split()
        stop = False
        for tok in toks:
            if len(vals) >= need:
                break
            t = tok.strip()
            if t in DECOR or t == "":
                continue
            if NUMRE.match(t) or t in ZERO:
                vals.append(_num(t))
                continue
            stop = True
            break
        if stop:
            return vals, j  # 라벨/문구를 만남 — 이 줄은 안 먹고 그대로 둔다
        j += 1
    return vals, j


def extract_tier2(pdf: Path):
    """-> (dict[47|48|49] -> (pre, post) 표에 인쇄된 그대로(단위 미확정), anchor, reason_if_empty).

    anchor = 이 표 자신의 종결행 '지급여력기준금액' (pre, post) — 48(보완자본 한도) 매칭 위치
    **다음**부터 찾은 첫 occurrence라 상단 SCR 세부표나 하단 (2)선택적용표의 동명 행과 섞이지
    않는다. 호출자가 이 anchor 를 마스터의 기존 item14 와 대조해 진짜 스케일을 정한다."""
    doc = fitz.open(pdf)
    try:
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()

    matched = {i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t}
    if not matched:
        # 텍스트레이어 실질 부재(스캔본) 여부를 구분해서 사유를 남긴다.
        total_chars = sum(len(t) for t in page_texts)
        n = len(page_texts)
        density = total_chars / n if n else 0
        if density < 400:
            return {}, None, f"UNREADABLE(스캔본 의심, {density:.1f}자/p, {n}p)"
        return {}, None, "'공통적용'+'보완자본'+'한도' 3키워드 동시 페이지 없음"

    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)

    lines: list[str] = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())

    def norm(s: str) -> str:
        return s.replace(" ", "")

    # 일부 필링(한화생명 등)은 텍스트레이어가 라벨·값 전부 통째로 인접 중복 인쇄된다
    # ("보완자본 한도 적용 전"이 연속 두 줄, 뒤따르는 두 값도 각각 연속 두 줄). 진짜 표는 같은
    # 행 라벨이 바로 다음 줄에 또 나오지 않으므로, 그 신호(고유 라벨 직후 자기반복)가 보이면
    # 이 페이지 전체를 인접중복 제거해 원래 단일표로 되돌린다. 신호가 없는 정상 문서는 손대지 않는다.
    if norm("보완자본 한도 적용 전") in {norm(l) for l in lines}:
        idx = next(i for i, l in enumerate(lines) if norm(l) == norm("보완자본 한도 적용 전"))
        if idx + 1 < len(lines) and norm(lines[idx + 1]) == norm("보완자본 한도 적용 전"):
            deduped = []
            for l in lines:
                if deduped and deduped[-1].strip() == l.strip():
                    continue
                deduped.append(l)
            lines = deduped

    targets = {
        47: norm("보완자본 한도 적용 전"),
        48: norm("보완자본 한도"),
    }
    LABEL49_HEAD = norm("해약환급금 부족분 상당액 중")
    found: dict[int, tuple] = {}
    pos_48_end = None
    k = 0
    while k < len(lines):
        s = norm(lines[k])
        hit_it = None
        if s == targets[47]:
            hit_it = 47
        elif s == targets[48]:
            hit_it = 48
        elif s != "" and (s.startswith(LABEL49_HEAD) or LABEL49_HEAD.startswith(s)):
            # 라벨 줄바꿈이 4가지 변형으로 나타난다: 한 줄로 이어짐(하나손해) / 의미단위
            # 두줄(대다수) / 페이지폭에 걸려 단어 중간에서 줄바꿈(메리츠 "…중 해약환\n급금…") /
            # **단어 단위로 잘게 쪼개짐**(동양생명 "해약환급금"/"부족분"/"상당액"/"중" 각각
            # 별도 줄, NH농협손해 "해약환급금 부족분 상당액"/"중 해약환급금 상당액 초과분" 2줄
            # — 첫 줄만으로는 LABEL49_HEAD 전체를 포함 못 해 기존 `startswith(HEAD)` 가 아예
            # 트리거되지 않았다, 2026-08-21 발견). `HEAD.startswith(s)` 는 s 가 HEAD 의 순수
            # 접두어(그래서 아직 라벨이 안 끝난 상태)일 때도 트리거해 이 변형을 잡는다 — s 가
            # 빈 문자열이면 모든 문자열의 접두어라 오매칭되므로 `s != ""` 로 막는다.
            # 그래서 고정 2줄 매칭 대신, "초과분" 이 누적문자열에 나타나거나 숫자줄을 만날
            # 때까지 계속 이어붙인다.
            acc = s
            j = k + 1
            while "초과분" not in acc and j < len(lines):
                nxt = lines[j].replace(" ", "")
                if nxt == "" or nxt in DECOR:
                    j += 1
                    continue
                if NUMRE.match(nxt) or nxt in ZERO:
                    break  # 라벨이 안 끝났는데 숫자가 나오면 이 occurrence 는 포기
                acc += norm(lines[j])
                j += 1
            if "초과분" in acc:
                hit_it = 49
                k = j - 1  # 라벨 마지막 소비줄 — 아래 공용 값-캡처가 k+1부터 스캔
            else:
                k += 1
                continue
        if hit_it and hit_it not in found:
            vals, j = _collect_values(lines, k + 1, need=2)
            if len(vals) == 2:
                found[hit_it] = (vals[0], vals[1])
            elif len(vals) == 1:
                # 비적용사("해당사항 없음"/"경과조치 적용 전·후 금액 및 비율이 동일함" 각주)는
                # 전=후 전부 같아서 표를 한 컬럼만 인쇄한다(하나손해 KR0050 확인) — 그 한 값을
                # 전=후 로 미러링한다. 진짜로 값이 없는 행은 vals가 0개라 여기 안 걸린다.
                found[hit_it] = (vals[0], vals[0])
            if hit_it == 48:
                pos_48_end = j
            k = j
            continue
        k += 1

    if not found:
        return {}, None, "라벨 매칭 실패(페이지는 찾았으나 3줄 못 읽음)"

    # 일부 필링(한화생명 등)은 텍스트레이어가 라벨·값 전부 통째로 중복 인쇄된다("지급여력
    # 기준금액"이 연속 두 줄, 값도 연속 두 줄). 첫 occurrence 바로 다음이 (값이 아니라) 같은
    # 라벨의 중복이면 캡처가 실패하니 — 그 경우 멈추지 말고 다음 occurrence 로 계속 찾는다.
    anchor = None
    if pos_48_end is not None:
        k2 = pos_48_end
        while k2 < len(lines):
            if norm(lines[k2]) != "지급여력기준금액":
                k2 += 1
                continue
            vals, j = [], k2 + 1
            vals, j = _collect_values(lines, k2 + 1, need=2)
            if len(vals) == 2:
                anchor = (vals[0], vals[1])
                break
            if len(vals) == 1:
                anchor = (vals[0], vals[0])
                break
            k2 += 1  # 캡처 실패(다음 줄이 라벨 중복 등) — 다음 occurrence 계속 탐색
    return found, anchor, None


def _trivial(pair):
    """pair=(pre,post) 가 사실상 0(둘 다 절대값 0.5 미만)인가 -- 스케일이 이 항목에
    한해 무의미한지 판정(스케일 게이트에서 사용)."""
    if pair is None:
        return True
    a = abs(pair[0]) if pair[0] is not None else 0.0
    b = abs(pair[1]) if pair[1] is not None else 0.0
    return a < 0.5 and b < 0.5


def main() -> int:
    dry = "--dry-run" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드 전 row_count = {len(data):,}")

    by_c: dict[str, set] = {}
    info: dict[str, dict] = {}
    existing = set()  # (code, quarter, item) 이미 있는 셀 (덮어쓰기 방지용 — 신규 항목이라 없어야 정상)
    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        by_c.setdefault(c, set()).add(q)
        info.setdefault(c, {"원수사명": r.get("원수사명"), "티커": r.get("티커"),
                             "생손보여부": r.get("생손보여부")})
        existing.add((c, q, int(r["항목번호"])))

    # item14(전/후) 룩업 — 앵커 스케일 판별용 (마스터 기존값, 새로 안 건드림)
    m14: dict[tuple, tuple] = {}
    for r in data:
        if int(r["항목번호"]) == 14:
            c, q = r["원보험사코드"], r["공시분기"]
            m14[(c, q)] = (_num(r.get("값")), _num(r.get("값_적용후")))

    new_rows = []
    census = []  # (code, name, quarter, status, detail)
    provenance = []  # inbox 20260821T1425Z §4 요청 — 배율 선택 근거 기록 (data/_derived/ 로 덤프)
    for c in sorted(by_c):
        if only and c != only:
            continue
        for q in sorted(by_c[c]):
            pdf = _pdf(q2p(q), c)
            if pdf is None:
                census.append((c, info[c]["원수사명"], q, "raw없음", ""))
                continue
            found, anchor, reason = extract_tier2(pdf)
            if not found:
                census.append((c, info[c]["원수사명"], q, "미검출", reason or ""))
                continue

            # --- 스케일/무결성 판별: item48(보완자본 한도) vs 마스터 기존 item14 x 50% ---
            # 원래는 표 자신의 "지급여력기준금액" 종결행(anchor)을 앵커로 썼는데,
            # 오케스트레이터 전수검산으로 이게 신뢰 불가임이 드러났다 — 교보생명 홀수분기
            # 처럼 텍스트스트림이 뒤섞인 필링에서 anchor 검색이 엉뚱한 occurrence 를 집어도
            # 근사 비율(1 or 100)처럼 보이는 값을 우연히 만들어낼 수 있다.
            # 대신 "item48 == item14(마스터, 이미 여러 라운드 검증됨) x 50%" 를 쓴다 —
            # 이 항등식은 전사 429/430(99.8%)에서 정확히 성립하고 유일한 예외(AIA 2023.3Q)도
            # 원문 자체의 1.6% 오차라, anchor 보다 훨씬 신뢰도 높은 독립 검산축이다
            # (오케스트레이터가 지적한 바로 그 관계 — item47/48/49 스케일과 회사·분기 자체의
            # 무결성을 동시에 검사하는 게이트로 쓴다. 이 게이트를 못 넘으면 47/48/49 전부
            # 적재하지 않는다 — 틀린 값을 싣느니 빈 칸).
            m14_pre, m14_post = m14.get((c, q), (None, None))
            f47, f48, f49 = found.get(47), found.get(48), found.get(49)
            scale = None
            method = None       # 판정에 실제로 쓰인 축 -- provenance 기록용
            ratio_used = None   # 그 축의 비율값 -- provenance 기록용
            ratio48 = f48[0] / (m14_pre * 0.5) if (
                f48 is not None and f48[0] is not None and m14_pre and m14_pre * 0.5) else None
            ratio_scr = anchor[0] / m14_pre if (anchor is not None and anchor[0] and m14_pre) else None

            if (f48 is not None and f48[0] is not None and abs(f48[0]) < 0.005
                    and _trivial(f47) and _trivial(f49)):
                # 후순위채/신종자본증권 자체가 없는 회사는 47/48/49 **전부** 원문에 "0"으로
                # 직접 인쇄된다(메트라이프·카카오페이 등 raw 로 확인) — 이때는 스케일과
                # 무관하게(0 x 어떤 배율도 0) 참이니 게이트를 그대로 통과시킨다.
                # **주의**: 이 단축은 47·49 도 함께 사실상 0 일 때만 쓴다. 2026-08-21
                # 카카오페이(KR1098) 2025.1Q 에서 발견 — item48 만 0 이고 item49=1,553(실질값)인
                # 혼재 케이스에 이 단축을 무조건 적용했더니 item49 가 스케일 판정 없이(=1.0
                # 가정) 그대로 실려 item14(SCR)의 10 배가 넘는 값이 됐다(TIER2_SCALE RED).
                # item48 은 "48 자신이 0"이라는 사실만 말해줄 뿐 47/49 의 배율까지 보증하지
                # 않는다.
                scale = 1.0
                method = "ALL_ZERO_TRIVIAL"
            elif f48 is not None and f48[0] is not None and abs(f48[0]) >= 0.005 and ratio48 is not None:
                if 0.98 < ratio48 < 1.02:
                    scale = 1.0
                    method, ratio_used = "ITEM48_ANCHOR", ratio48
                elif 98 < ratio48 < 102:
                    scale = 0.01
                    method, ratio_used = "ITEM48_ANCHOR", ratio48

            if scale is None and ratio_scr is not None:
                # item48 이 0(=무정보)인데 47 또는 49 가 실질값인 혼재 케이스 재시도 — 이
                # 표 자신의 종결행(anchor, 지급여력기준금액)을 item14 와 대조한다. anchor는
                # 교보생명류(텍스트순서 뒤섞임)에서만 신뢰 불가였다(그래서 주축에서 밀려났다) —
                # 그 코호트가 아닌 회사(카카오페이 등)에서는 여전히 유효한 2차 검증축이다.
                if 0.98 < ratio_scr < 1.02:
                    scale = 1.0
                    method, ratio_used = "SCR_ANCHOR_FALLBACK", ratio_scr
                elif 98 < ratio_scr < 102:
                    scale = 0.01
                    method, ratio_used = "SCR_ANCHOR_FALLBACK", ratio_scr

            # provenance: 판정됐든 안 됐든 두 축의 비율을 전부 남긴다 — "골랐다"를
            # "확인했다"로 바꾸는 데 필요한 게 이거다(inbox 20260821T1425Z §4).
            # ambiguous = SCR_ANCHOR_FALLBACK(2차축, 덜 신뢰) 로 판정됐거나, 판정에 쓴
            # 비율이 깔끔한 1.00/100.00 에서 0.5% 이상 벗어난 경우 -- review 후보.
            clean_target = 1.0 if scale == 1.0 else (100.0 if scale == 0.01 else None)
            ambiguous = (
                method == "SCR_ANCHOR_FALLBACK"
                or (ratio_used is not None and clean_target is not None
                    and abs(ratio_used - clean_target) / clean_target > 0.005)
            )
            provenance.append({
                "원보험사코드": c, "원수사명": info[c]["원수사명"], "공시분기": q,
                "method": method, "scale": scale,
                "ratio_item48_anchor": ratio48, "ratio_scr_anchor": ratio_scr,
                "ratio_used": ratio_used, "ambiguous": bool(ambiguous) if scale is not None else None,
                "resolved": scale is not None,
                "raw_47": f47, "raw_48": f48, "raw_49": f49, "raw_anchor_scr": anchor,
                "m14_pre": m14_pre,
            })

            if scale is None:
                census.append((c, info[c]["원수사명"], q, "스케일불명",
                                f"item48={f48} m14전x50%={m14_pre*0.5 if m14_pre else None} "
                                f"(참고 in-page anchor={anchor})"))
                continue

            n_written = 0
            for it in (47, 48, 49):
                if it not in found:
                    continue
                if (c, q, it) in existing:
                    continue  # 이미 있으면 스킵(신규 항목이라 정상적으론 없어야 함)
                pre_raw, post_raw = found[it]
                pre = None if pre_raw is None else round(pre_raw * scale, 2)
                post = None if post_raw is None else round(post_raw * scale, 2)
                if pre is None and post is None:
                    continue
                row = {
                    "원보험사코드": c,
                    "원수사명": info[c]["원수사명"],
                    "티커": info[c]["티커"],
                    "생손보여부": info[c]["생손보여부"],
                    "항목번호": it,
                    "항목명": ITEM_LABELS[it],
                    "공시분기": q,
                }
                if pre is not None:
                    row["값"] = _fmt(pre)
                if post is not None:
                    row["값_적용후"] = _fmt(post)
                new_rows.append(row)
                n_written += 1
            census.append((c, info[c]["원수사명"], q, "OK",
                            f"{n_written}개 항목 ({sorted(found)}) scale={scale}"))

    ok = sum(1 for *_x, s, _d in [(c, n, q, s, d) for c, n, q, s, d in census] if s == "OK")
    print(f"\n스캔 (회사,분기) = {len(census)}  |  OK = {ok}  |  raw없음 = "
          f"{sum(1 for *_x,s,_d in census if s=='raw없음')}  |  미검출 = "
          f"{sum(1 for *_x,s,_d in census if s=='미검출')}")
    print(f"신규 셀 = {len(new_rows)}건")

    # 회사x분기 커버리지 표
    print("\n=== 회사별 커버리지 (OK분기수 / 전체분기수) ===")
    by_company_ok: dict[str, list] = {}
    for c, n, q, s, d in census:
        by_company_ok.setdefault(c, []).append((q, s, d))
    for c in sorted(by_company_ok):
        entries = by_company_ok[c]
        ok_n = sum(1 for _q, s, _d in entries if s == "OK")
        miss = [f"{q}({s})" for q, s, d in entries if s != "OK"]
        print(f"  {c} {info[c]['원수사명']:<16} {ok_n:>2}/{len(entries):<2}"
              + (f"  미충족: {', '.join(miss)}" if miss else ""))

    # 스케일 provenance 산출 (inbox 20260821T1425Z §4) — 전수 스캔(--only 미사용)일 때만
    # 덤프한다. 부분스캔으로 전체 파일을 덮어쓰면 나머지 회사 기록이 사라지는 사고가 되므로.
    if only is None:
        n_amb = sum(1 for p in provenance if p.get("ambiguous"))
        n_unresolved = sum(1 for p in provenance if not p["resolved"])
        PROVENANCE_OUT.parent.mkdir(parents=True, exist_ok=True)
        PROVENANCE_OUT.write_text(
            json.dumps({
                "generated_at_note": "scripts/fix_20260821_tier2_limit_lines.py 실행 시 갱신",
                "총건수": len(provenance),
                "resolved": sum(1 for p in provenance if p["resolved"]),
                "미해결(스케일불명)": n_unresolved,
                "ambiguous(review 필요)": n_amb,
                "records": provenance,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n스케일 provenance -> {PROVENANCE_OUT}  "
              f"(전체 {len(provenance)} · 미해결 {n_unresolved} · ambiguous {n_amb})")
    else:
        print(f"\n(--only {only} 부분스캔 -- 스케일 provenance 파일은 안 건드림)")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0
    if not new_rows:
        print("쓸 셀 없음")
        return 0

    data.extend(new_rows)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(new_rows)}행 INSERT, wrote {TARGET.name}  (row_count {len(data)-len(new_rows):,} -> {len(data):,})")
    return 0


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


if __name__ == "__main__":
    raise SystemExit(main())
