# -*- coding: utf-8 -*-
"""jp 레인 `JP_ESR_NOT_IN_SOURCE` 증거 수집기 — census 확정 전 선행 단계(네트워크).

왜 (2026-09-13 사고)
--------------------
2026-09-12 census 로 15사가 화면에 올라갈 때 빌더 self-check 는 전부 통과했는데, 다음 날
원문을 열어 보니 東京海上HD 238% 는 **어느 1차 문서에도 없는 2차보도 인용값**이었고
MS&AD 의 `source_url` 은 **ESR 이 한 줄도 없는 합병 보도자료**였다. 종전 검사는 범위·형식·합계만
보는 자기참조라 "그 문서에 그 숫자가 있나" 축이 아예 없었다.
근거: docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md §2·§4c-pre-실측

이 스크립트가 그 축의 **증거를 박제**한다. 빌더(`build_jesr_page_json.py::source_gate_check`)는
네트워크를 타지 않고 이 산출만 읽는다 — 빌드는 완전 오프라인을 유지한다.
`check_source_urls.py` 와 같은 봉투(`checked_at`/`scope`/`rows`)를 쓰므로 빌더의
`JP_SOURCE_EVIDENCE_STALE` 신선도 검사가 **그대로 재사용**된다.

근접 규칙 (2026-09-13 posted 15사 전수 실측으로 확정)
----------------------------------------------------
초안(§2)은 "ESR 라벨과 **같은 문장**" 이었다. 실측이 그걸 뒤집었다 — 결산 프레젠테이션·
전화회의자료·업적데이터 별책은 산문이 거의 없는 문서 유형이라 값과 라벨이 **표 행이나 차트
데이터라벨로만** 공존한다(15사 중 표 행 4 · 차트 데이터라벨 3 = 7사). 문자 그대로 걸면
멀쩡한 7사가 한꺼번에 거짓 RED 다. 그래서 근접을 두 갈래로 넓힌다.

  text_window  같은 페이지 읽기순서 텍스트에서 라벨과 값의 간격 <= 200자
               (산문 문장 · 대부분의 표 행 · 차트 범례+데이터라벨 군을 다 덮는다)
  table_row    같은 페이지에서 라벨 줄과 값 줄의 **세로 범위가 겹치면** 통과
               (열 간격이 넓어 읽기순서로는 200자 넘게 벌어지는 넓은 표용 안전망)

실측 간격(14개 PDF 의 최소거리): 0·1·1·1·2·2·7·8·13·20·22·39·39·72 — 전부 text_window 안이다.
table_row 는 표본에서 필요하지 않았지만, 읽기순서가 열을 갈라 놓는 표가 다음 라운드에
들어오면 그때는 없으면 거짓 RED 가 된다.

이미지형 PDF
------------
초안은 "최소 2사 이미지형" 이라고 **추정**했고 실측은 **0사**였다(부분 추출 4사의 빈 페이지는
전부 슬라이드 구분면이고 ESR 이 있는 페이지는 4사 모두 정상 추출). 그래서 `skip_no_text` 는
방어용으로만 남기고 문턱을 **공백 제외 0자**로 잡는다 — "몇 자 안 나오니 SKIP" 은 이 저장소가
반복해서 데인 SKIP-on-missing(결측은 SKIP 이 아니라 RED)이라 문턱을 올리지 않는다.

두 번째 축: 조정치 판정 (JP_ESR_ADJUSTED_FIGURE, UH-21 2026-09-13)
-----------------------------------------------------------------
위 축은 "그 문서에 그 숫자가 있나" 만 묻는다. 사고 3건 중 かんぽ 220% 는 그걸로 안 걸린다 —
220 은 자료 p35 에 **실재하는** 「大量解約リスクを除いた場合」 조정치이기 때문이다(실측 d=1).
그래서 같은 스캔에서 조정치 축을 같이 박제한다: `adjusted_verdict` 외 5개 필드가 rows 에 붙고,
게이트는 그 값만 읽는다(`scan_adjusted` 의 docstring 이 판정식 정본).

사용법
------
  python3 J-ESR/check_esr_in_source.py --all --out J-ESR/esr_in_source_health.json
  python3 J-ESR/check_esr_in_source.py --company かんぽ生命保険      # 디버그(좁은 범위)

종료코드: `not_found` 가 하나라도 있으면 1. **조정치 발화는 종료코드를 바꾸지 않는다** —
severity 가 YELLOW 라서다(사람이 원문을 봐야 결론 나는 축이고, 조건부 값을 정당하게 헤드라인으로
쓰는 회사가 있을 수 있다). 대신 로그에 한 줄씩 찍고, 배포본 증거에 발화가 남아 있으면
`tests/test_jp_source_gate.py::test_live_esr_evidence_has_no_unexempted_adjusted_figure` 가
push 묶음에서 막는다 — "인쇄만 하는 YELLOW" 는 통제가 아니다(2026-09-12 사고 당시 census notes
에 「特定条件を除いた場合の ESR は 220%」 라고 **적혀 있었는데도** 그 값이 그대로 나갔다).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jesr_http  # noqa: E402
# 값 후보의 도메인 상·하한은 **빌더가 정본**이다(`ESR_PCT_MIN`/`ESR_PCT_MAX`). 여기 다시
# 타이핑하면 수집기와 게이트가 서로 다른 범위로 같은 값을 판정하게 된다 — K-ICS 상관행렬을
# 재타이핑하지 말라는 것과 같은 이유다. 빌더는 import 시 부작용이 없다(상수·함수 정의뿐).
import build_jesr_page_json as _builder  # noqa: E402

HERE = Path(__file__).resolve().parent
CENSUS_CSV = HERE / "fy2025_esr_census_20260912.csv"
DEFAULT_OUT = HERE / "esr_in_source_health.json"
POSTED_STATUS = "posted"

#: 넓은 범위 산출을 좁은 범위가 덮어쓰면 증거가 조용히 줄어든다(check_source_urls.py 와 같은 guard).
SCOPE_RANK = {"partial": 1, "all": 4}

# ---------------------------------------------------------------------------
# ESR 라벨 — **정본은 docs/domains/claude-agent-jp.md §3** 이다.
# 여기 목록은 그 절의 기계본이고, tests/test_jp_source_gate.py 가 한 줄씩 원문에 있는지
# 대조한다(::test_esr_labels_are_all_named_in_the_domain_doc). 손으로 새 라벨을 지어내면
# 검증기가 정본과 다른 목록으로 검증하게 된다 — K-ICS 상관행렬을 재타이핑하지 말라는 것과
# 같은 이유다. 라벨을 늘리려면 도메인 문서 §3 을 먼저 고친다.
# ---------------------------------------------------------------------------

#: 무조건 ESR 라벨로 인정하는 표기.
ESR_LABELS_STRONG = (
    "ESR",
    "経済価値ベースのソルベンシー比率",
    "ソルベンシー・マージン比率（新基準）",
)

#: 구기준 옛 이름. §3: "신기준 표에서는 옛 이름을 그대로 쓰는 회사가 많다 — 표 안에
#: 所要資本·適格資本·UFR·민감도가 같이 있으면 신기준". 즉 **단독으로는 ESR 이 아니다**
#: (분모가 リスクの合計額 ×1/2 인 옛 지표). 같은 페이지에 신기준 표지가 있을 때만 라벨로 친다.
#: 이 조건을 빼면 au損保·明治安田損保의 5개년 구기준 표까지 라벨로 읽혀 거짓 통과가 난다.
ESR_LABEL_AMBIGUOUS = "ソルベンシー・マージン比率"
ESR_NEW_STANDARD_MARKERS = ("所要資本", "適格資本", "適格自己資本", "UFR")

#: 근접 판정 문턱(자). §4c-pre-실측으로 확정.
PROXIMITY_CHARS = 200

VERDICTS = ("found", "not_found", "skip_landing", "skip_no_text")

# ---------------------------------------------------------------------------
# JP_ESR_ADJUSTED_FIGURE — "있는 숫자 중 틀린 것을 골랐나" (UH-21, 2026-09-13)
#
# 위의 found/not_found 축은 **"그 문서에 그 숫자가 있나"** 만 묻는다. 2026-09-12 사고 3건 중
# かんぽ 220% 는 그 축으로 원리상 안 걸린다 — 220 은 자료 p35 에 실재한다
# (「大量解約リスクを除いた場合のESRは220%」·「ESR適正水準 150~220%」, 실측 d=1 → found).
# 즉 かんぽ형은 "없는 숫자를 썼다" 가 아니라 **"한정 조건이 붙은 조정치를 헤드라인으로 골랐다"**
# 이고, 같은 문서에 한정어 없는 진짜 헤드라인(181%)이 나란히 실려 있었다.
# 근거: docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md §5(UH-21)
#
# 판정 단위 = **산문 조각**(`。`·개행으로 자른 것). 일본어에서 한정어는 그 조각 안에서 값에
# 문법적으로 붙는다. PDF 추출은 문장을 개행으로 자주 끊으므로 조각은 실제 문장보다 짧아지고,
# 그 방향의 오차는 한정어를 **놓치는**(=발화 안 하는) 쪽이라 오탐에 안전하다.
# ---------------------------------------------------------------------------

#: 한정어 — 값에 조건·범위를 붙이는 표현. **15사 전수 실측으로 확정**했다(2026-09-13).
#: 라벨동반 조각 전체에서 실제로 관측된 것은 아래 표시한 4종뿐이고, 나머지는 같은 구문의
#: 이형이다. 늘릴 때는 반드시 15사에 다시 돌려 정상사 발화가 0인지 보고 늘린다.
#:
#: 관측 0인데 **일부러 뺀 것**(definition marker — "어느 ESR 이냐" 지 "조정했다" 가 아니다):
#:   ベース   住友의 정답 헤드라인이 「経済価値ベースのソルベンシー比率」 — 라벨 자체다
#:   内部管理  朝日의 정답 헤드라인이 「ESR(グループ)(内部管理ベース)は258.9%」
#:   規制     日本生命의 정답 헤드라인이 「規制ESR…連結:195%」
#:   速報値    富国의 다른 값(210%)에 붙어 있다
#: 이 넷을 한정어로 넣으면 정상 3사(日本生命·住友·朝日)가 거짓 발화한다(실측).
ADJUSTED_QUALIFIERS = (
    "除いた場合",       # 실측 2 — かんぽ p35 「大量解約リスクを除いた場合のESRは220%」. 사고 그 문장
    "除いたESR",        # 같은 구문의 이형(관측 0)
    "除くESR",          # 같은 구문의 이형(관측 0)
    "除外した",         # 같은 구문의 이형(관측 0)
    "調整後",           # PM seed. 관측 0이지만 「調整後ESR」 은 공시 관행 표기라 남긴다
    "適正水準",         # 실측 4 — かんぽ. **노이즈가 있다**: 정답값 181 의 조각에도 붙었다
                        #   (「適正水準の範囲内にある」). 그래도 빼면 안 된다 — 빼면 p18
                        #   「ESR適正水準 150~220%」 가 한정어 없는 조각이 되어 220 이 빠져나간다(실측)
    "ターゲットレンジ",  # 실측 1 — 富国 「ESRをターゲットレンジ内(230%~270%)に維持」
    "目標レンジ",       # 같은 뜻의 이형(관측 0)
    "参考値",           # PM seed 「参考」 를 좁힌 형태. 맨 「参考」 는 각주 기호와 충돌한다
    "試算値",           # 이형(관측 0)
)

#: 조정치 축의 판정 어휘. 게이트(build_jesr_page_json)가 이 값을 읽는다 — 모르는 값은 RED.
ADJUSTED_VERDICTS = (
    "unqualified",        # 한정어 없는 라벨동반 조각이 1개 이상 → 깨끗
    "adjusted_alt",       # 화면값 조각이 전부 한정어 + **한정어 없는 대안값이 같은 문서에 있다**
    "adjusted_only",      # 화면값 조각이 전부 한정어인데 대안값은 없다(보조 신호)
    "abstain_no_prose",   # 라벨동반 산문 조각 0개 → 판정하지 않는다(표·차트 전용 문서)
    "not_applicable",     # PDF 가 아니거나 문서를 못 받았다 → 판정 대상이 아니다
)

#: 조각 안의 % 값 후보. 범위는 빌더의 도메인 상·하한을 **그대로 쓴다**(재타이핑 금지).
FRAG_PCT_RE = re.compile(r"(?<![0-9.,])([0-9]{2,4}(?:\.[0-9])?)\s*%")
ADJ_PCT_MIN = _builder.ESR_PCT_MIN
ADJ_PCT_MAX = _builder.ESR_PCT_MAX

#: 메시지에 싣는 대안값 최대 개수(전부 실으면 한 줄이 못 읽게 길어진다).
ADJUSTED_ALT_LIMIT = 3


def log(msg: str) -> None:
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def norm_text(s: str) -> str:
    """NFKC — 전각 숫자 ２６８→268 · ％→% · （）→() 를 한 번에 정규화한다."""
    return unicodedata.normalize("NFKC", s or "")


def norm_pct(value) -> str | None:
    """`268` / `268.0` / `"268％"` → `"268"`, `208.7` → `"208.7"`. 못 읽으면 None."""
    if value is None:
        return None
    s = norm_text(str(value)).strip().rstrip("%").strip()
    if not s:
        return None
    try:
        return "%g" % float(s)
    except ValueError:
        return None


def value_pattern(pct: str) -> re.Pattern:
    """표기 정규화된 값 1개를 찾는 정규식.

    `268` 은 `268` · `268.0` · `268%` 에 걸리고 `1268` · `268.5` · `2,268` 에는 안 걸린다
    (앞이 숫자/소수점/천단위쉼표면 다른 수, 뒤에 숫자가 더 오면 다른 수).
    """
    forms = [pct] + ([pct + ".0"] if "." not in pct else [])
    alts = "|".join(re.escape(f) for f in forms)
    return re.compile(r"(?<![0-9.,])(?:%s)(?![0-9])(?!\.[0-9])" % alts)


def _label_spans(page_text: str, marker_scope: str | None = None) -> list[tuple[int, int, str]]:
    """정규화된 페이지 텍스트에서 ESR 라벨 위치 (start, end, label).

    `marker_scope` 는 구기준 라벨(`ソルベンシー・マージン比率`)을 인정할지 판정할 때
    신기준 표지를 찾는 범위다. 기본값은 `page_text` 자신 — 기존 호출자(페이지 전체 스캔·
    `_table_row_hit` 의 줄 단위)의 동작이 그대로 유지된다. 조각 단위로 부를 때는 조각이
    너무 짧아 표지가 안 들어오므로 **페이지 전체**를 넘긴다(표지 판정은 §3 대로 페이지 범위).
    """
    scope = page_text if marker_scope is None else marker_scope
    spans: list[tuple[int, int, str]] = []
    for lab in ESR_LABELS_STRONG:
        n = norm_text(lab)
        spans.extend((m.start(), m.end(), lab) for m in re.finditer(re.escape(n), page_text))
    if any(norm_text(k) in scope for k in ESR_NEW_STANDARD_MARKERS):
        n = norm_text(ESR_LABEL_AMBIGUOUS)
        spans.extend((m.start(), m.end(), ESR_LABEL_AMBIGUOUS + "(新基準ページ)")
                     for m in re.finditer(re.escape(n), page_text))
    return spans


def _prose_fragments(page_text: str) -> list[str]:
    """`。`·개행으로 자른 산문 조각. 일본어 한정어가 값에 붙는 문법 단위다."""
    return [f for f in re.split(r"[。\n]", page_text) if f.strip()]


def _frag_values(frag: str) -> list[str]:
    """조각 안의 ESR 값 후보(정규화). 빌더의 도메인 범위 밖 숫자는 ESR 이 아니다."""
    out = []
    for raw in FRAG_PCT_RE.findall(frag):
        v = float(raw)
        if ADJ_PCT_MIN <= v <= ADJ_PCT_MAX:
            out.append("%g" % v)
    return out


def scan_adjusted(page_texts: list[str], pct: str) -> dict:
    """`JP_ESR_ADJUSTED_FIGURE` 판정 — 화면값이 조건부 조정치인가.

    본 판정(`adjusted_alt`)은 **두 조건이 같이 성립할 때만** 난다.

      ① 화면값이 나오는 라벨동반 산문 조각이 **전부** 한정어를 달고 있다
      ② 같은 문서에 **한정어 없는 다른 ESR 값**이 있다 (= 우리가 썼어야 할 헤드라인 후보)

    ② 가 본 룰인 이유(2026-09-13 15사 전수 실측):
    ① 단독은 한정어 목록이 조금만 넓어져도 무너진다. 실제로 definition marker 4종
    (`ベース`·`内部管理`·`規制`·`速報値`)을 한정어로 오인해 넣으면 ① 단독은 정상 3사
    (日本生命·住友·朝日)가 거짓 발화하는데, ② 를 붙이면 그 3사는 전부 조용하고 かんぽ 220
    만 남는다. 즉 ② 가 이 룰의 오탐억제 본체고 ① 은 전제다.
    ① 만 성립하면 `adjusted_only` — 보조 신호로 따로 적는다(문서가 조건부 값만 싣는 경우를
    조용히 버리지 않기 위해서다. 15사 표본에서는 0건).

    라벨동반 조각이 0개면 **판정하지 않는다**(`abstain_no_prose`). 결산 프레젠테이션·
    업적데이터 별책은 산문이 없어 값과 라벨이 표·차트로만 공존한다 — 15사 중 7사가 그 형태라
    기권 조건 없이 걸면 거짓 발화 7건이다(실측). 기권은 SKIP 이 아니라 **따로 세는 분류**다:
    산출 summary 에 개수가 남고 게이트가 그 수를 인쇄한다.
    """
    screen: list[dict] = []
    free: dict[str, tuple[int, str]] = {}
    for pno, page in enumerate(page_texts, 1):
        for frag in _prose_fragments(page):
            if not _label_spans(frag, marker_scope=page):
                continue
            vals = _frag_values(frag)
            if not vals:
                continue
            quals = [q for q in ADJUSTED_QUALIFIERS if q in frag]
            short = frag.strip()[:160]
            if pct in vals:
                screen.append({"page": pno, "qualifiers": quals, "text": short})
            if not quals:
                for v in vals:
                    free.setdefault(v, (pno, short))

    base = {"adjusted_qualifiers": sorted({q for h in screen for q in h["qualifiers"]}),
            "adjusted_frags": len(screen),
            "adjusted_frags_unqualified": sum(1 for h in screen if not h["qualifiers"]),
            "adjusted_alternatives": []}
    if not screen:
        return {**base, "adjusted_verdict": "abstain_no_prose",
                "adjusted_evidence": "ESR 라벨과 화면값이 같이 나오는 산문 조각이 없다"
                                     "(표·차트 전용 문서) — 이 축은 판정하지 않는다"}
    if base["adjusted_frags_unqualified"]:
        free_frag = next(h for h in screen if not h["qualifiers"])
        return {**base, "adjusted_verdict": "unqualified",
                "adjusted_evidence": f"p{free_frag['page']} 한정어 없이: {free_frag['text']}"}
    alts = [{"pct": v, "page": free[v][0], "evidence": free[v][1]}
            for v in sorted((k for k in free if k != pct), key=float)][:ADJUSTED_ALT_LIMIT]
    hedged = screen[0]
    ev = f"p{hedged['page']} 한정어 {hedged['qualifiers']}: {hedged['text']}"
    if alts:
        a = alts[0]
        ev += f"  ┃ 대안(한정어 없음) p{a['page']} {a['pct']}%: {a['evidence']}"
    return {**base, "adjusted_alternatives": alts,
            "adjusted_verdict": "adjusted_alt" if alts else "adjusted_only",
            "adjusted_evidence": ev}


def _not_judged_adjusted(why: str) -> dict:
    """판정 대상이 아닌 행(비-PDF·미수신)의 조정치 필드. 필드를 **비우지 않는다** —
    키가 없으면 게이트가 '수집기가 이 축을 안 돌렸다' 로 읽어 RED 를 낸다(fail-closed)."""
    return {"adjusted_verdict": "not_applicable", "adjusted_qualifiers": [],
            "adjusted_frags": 0, "adjusted_frags_unqualified": 0,
            "adjusted_alternatives": [], "adjusted_evidence": why}


def _lines_with_boxes(page) -> list[tuple[str, float, float]]:
    """(정규화 줄 텍스트, y0, y1). words 를 (block, line) 로 묶는다."""
    buckets: dict[tuple[int, int], list] = {}
    for x0, y0, x1, y1, word, bno, lno, _wno in page.get_text("words"):
        buckets.setdefault((bno, lno), []).append((x0, y0, x1, y1, word))
    out = []
    for key in sorted(buckets):
        ws = sorted(buckets[key], key=lambda w: w[0])
        text = norm_text("".join(w[4] for w in ws))
        out.append((text, min(w[1] for w in ws), max(w[3] for w in ws)))
    return out


def _table_row_hit(page, vre: re.Pattern) -> tuple[str, str] | None:
    """같은 세로 범위(표의 한 행)에 라벨 줄과 값 줄이 같이 있으면 (라벨, 근거) 반환."""
    lines = _lines_with_boxes(page)
    val_lines = [ln for ln in lines if vre.search(ln[0])]
    if not val_lines:
        return None
    lab_lines = [(ln, _label_spans(ln[0])) for ln in lines]
    lab_lines = [(ln, sp) for ln, sp in lab_lines if sp]
    for vtext, vy0, vy1 in val_lines:
        for (ltext, ly0, ly1), spans in lab_lines:
            lo, hi = max(vy0, ly0), min(vy1, ly1)
            if hi <= lo:
                continue
            smaller = min(vy1 - vy0, ly1 - ly0) or 1.0
            if (hi - lo) / smaller >= 0.5:
                return spans[0][2], f"{ltext[:90]} ┃ {vtext[:90]}"
    return None


def scan_pdf(data: bytes, pct: str) -> dict:
    """PDF 바이트에서 `pct` 가 ESR 라벨 근처에 있는지. verdict/근거 dict 반환."""
    import fitz  # 수집기에서만 import — 빌더(오프라인)는 이 모듈을 import 하지 않는다

    vre = value_pattern(pct)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
        fh.write(data)
        tmp = fh.name
    try:
        doc = fitz.open(tmp)
        pages = len(doc)
        text_chars = 0
        best: dict | None = None
        row_hit: dict | None = None
        page_texts: list[str] = []
        for pno in range(pages):
            page = doc[pno]
            raw = page.get_text("text")
            text_chars += len("".join(raw.split()))
            t = norm_text(raw)
            page_texts.append(t)
            spans = _label_spans(t)
            for m in vre.finditer(t):
                for ls, le, lab in spans:
                    if le <= m.start():
                        d = m.start() - le
                    elif ls >= m.end():
                        d = ls - m.end()
                    else:
                        d = 0
                    if d <= PROXIMITY_CHARS and (best is None or d < best["distance"]):
                        best = {"rule": "text_window", "page": pno + 1, "distance": d,
                                "label": lab,
                                "evidence": t[max(0, m.start() - 90):m.end() + 90].replace("\n", "|")}
            # table_row 는 값이 그 페이지에 **있는데** 라벨과 읽기순서로 멀리 떨어진 경우의
            # 안전망이다. 값이 없는 페이지에서 돌릴 이유가 없다(100페이지 PDF 전 페이지에
            # words 추출을 도는 것을 막는다).
            if best is None and row_hit is None and vre.search(t):
                hit = _table_row_hit(page, vre)
                if hit:
                    row_hit = {"rule": "table_row", "page": pno + 1, "distance": None,
                               "label": hit[0], "evidence": hit[1]}
        doc.close()
    finally:
        os.unlink(tmp)

    if text_chars == 0:
        # 방어 분기(실측 0사). 문턱을 0 보다 올리지 않는다 — SKIP-on-missing 은 검증 무력화다.
        return {"verdict": "skip_no_text", "pages": pages, "text_chars": 0,
                "match_rule": None, "page": None, "distance": None, "label": None,
                "evidence": "텍스트 레이어 0자 — 이미지형 PDF 로 보인다. 사람이 원문을 직접 확인해야 한다",
                **_not_judged_adjusted("텍스트 레이어가 없어 조정치 판정도 불가")}
    # 조정치 축은 found/not_found 와 **독립으로** 돈다. found 여도 "정의가 다른 값" 일 수 있고
    # (かんぽ 220 이 정확히 그 모양), not_found 면 라벨동반 조각이 없어 자연히 기권이 된다.
    adjusted = scan_adjusted(page_texts, pct)
    hit = best or row_hit
    if hit:
        return {"verdict": "found", "pages": pages, "text_chars": text_chars,
                "match_rule": hit["rule"], "page": hit["page"], "distance": hit["distance"],
                "label": hit["label"], "evidence": hit["evidence"], **adjusted}
    return {"verdict": "not_found", "pages": pages, "text_chars": text_chars,
            "match_rule": None, "page": None, "distance": None, "label": None,
            "evidence": f"{pages}페이지 전체에서 {pct} 가 ESR 라벨 {PROXIMITY_CHARS}자/같은 표 행 안에 없다",
            **adjusted}


def scan_landing(data: bytes, pct: str) -> dict:
    """PDF 가 아닌 응답(상설 IR 페이지 등). 문서가 아니므로 SKIP+YELLOW.

    값이 본문에 보이는지는 **참고로만** 기록한다 — 목록 페이지의 우연한 3자리 수를 근거로
    통과시키지 않기 위해 verdict 는 바꾸지 않는다.
    """
    t = norm_text(data.decode("utf-8", errors="replace"))
    seen = bool(value_pattern(pct).search(re.sub(r"<[^>]+>", " ", t)))
    return {"verdict": "skip_landing", "pages": None, "text_chars": len("".join(t.split())),
            "match_rule": None, "page": None, "distance": None, "label": None,
            "evidence": (f"PDF 가 아니다(상설 페이지·목록 페이지). 본문에 {pct} 표기"
                         f"{'는 보인다' if seen else '가 안 보인다'} — 참고값이며 판정 근거 아님"),
            **_not_judged_adjusted("PDF 가 아니라 조정치 판정 대상이 아니다")}


def curl_download(url: str, timeout: int = 60) -> tuple[bytes, str, int] | None:
    """파이썬 TLS 가 악수 실패하는 사이트용 폴백(예: www.sonylife.co.jp).

    UA 는 `jesr_http.UA_BROWSER` 를 그대로 쓴다 — 헤더 기본값은 한 군데(jesr_http)에만 둔다.
    """
    if not shutil.which("curl"):
        return None
    with tempfile.NamedTemporaryFile(delete=False) as fh:
        tmp = fh.name
    try:
        out = subprocess.run(
            ["curl", "-sS", "-L", "--max-time", str(timeout), "-A", jesr_http.UA_BROWSER,
             "-o", tmp, "-w", "%{http_code}\t%{content_type}", url],
            capture_output=True, text=True, timeout=timeout + 15)
        code, _, ctype = (out.stdout or "").strip().partition("\t")
        data = Path(tmp).read_bytes()
        return data, ctype.split(";")[0].strip().lower(), int(code) if code.isdigit() else 0
    except Exception:
        return None
    finally:
        os.unlink(tmp)


def fetch(url: str, timeout: int) -> dict:
    """(data, content_type, status, via). 실패하면 error 를 채워 돌려준다."""
    try:
        resp = jesr_http.get(url, timeout=timeout)
        return {"data": resp.content, "status": resp.status_code, "via": "requests",
                "content_type": (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower(),
                "error": None}
    except Exception as exc:
        alt = curl_download(url, timeout=timeout)
        if alt is not None and alt[2] and alt[2] < 400:
            return {"data": alt[0], "status": alt[2], "via": "curl",
                    "content_type": alt[1], "error": f"requests 실패 후 curl 폴백: {type(exc).__name__}"}
        return {"data": None, "status": None, "via": None, "content_type": None,
                "error": f"{type(exc).__name__}: {str(exc)[:200]}"}


def check_row(company: str, url: str, pct_raw, timeout: int) -> dict:
    row = {"origin": CENSUS_CSV.name, "company": company, "field": "source_url",
           "url": url, "esr_pct": norm_pct(pct_raw), "esr_pct_raw": str(pct_raw)}
    if row["esr_pct"] is None:
        row.update({"verdict": "not_found", "match_rule": None, "page": None, "distance": None,
                    "label": None, "pages": None, "text_chars": None,
                    "evidence": f"census esr_pct 를 수로 읽을 수 없다: {pct_raw!r}",
                    "fetch": {"status": None, "via": None, "content_type": None, "error": None},
                    **_not_judged_adjusted("esr_pct 를 수로 못 읽어 조정치 판정 불가")})
        return row
    got = fetch(url, timeout)
    row["fetch"] = {k: got[k] for k in ("status", "via", "content_type", "error")}
    if got["data"] is None:
        # 받지 못하면 **판정하지 않는다**. not_found 로 적으면 네트워크 사고가 데이터 오류로
        # 둔갑하고, found 로 적으면 false-green 이다. 둘 다 아닌 제3의 값으로 남겨 게이트가
        # "모르는 verdict → RED" 로 잡게 한다.
        row.update({"verdict": "fetch_failed", "match_rule": None, "page": None,
                    "distance": None, "label": None, "pages": None, "text_chars": None,
                    "evidence": "문서를 받지 못했다 — 재실행이 필요하다(판정 아님)",
                    **_not_judged_adjusted("문서를 못 받아 조정치 판정도 못 했다")})
        return row
    data = got["data"]
    is_pdf = data[:5] == b"%PDF-" or "pdf" in (got["content_type"] or "")
    res = scan_pdf(data, row["esr_pct"]) if is_pdf else scan_landing(data, row["esr_pct"])
    row["doc_kind"] = "pdf" if is_pdf else "other"
    row["bytes"] = len(data)
    row.update(res)
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description="posted 행의 esr_pct 가 1차 출처 문서에 있는지 점검")
    ap.add_argument("--all", action="store_true", help="posted 전량(기본). scope=all 로 적는다")
    ap.add_argument("--company", action="append", default=[],
                    help="디버그용 회사 필터. 쓰면 scope=partial 이라 빌더 게이트는 RED 다")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--force", action="store_true",
                    help="좁은 범위 결과로 넓은 범위 산출을 덮어쓴다(기본 금지)")
    args = ap.parse_args()

    rows_in = [r for r in csv.DictReader(CENSUS_CSV.open(encoding="utf-8-sig", newline=""))
               if (r.get("fy2025_esr_status") or "").strip() == POSTED_STATUS]
    if args.company:
        rows_in = [r for r in rows_in if r["company_jp"] in set(args.company)]
    scope = "partial" if args.company else "all"
    log(f"[esr-in-source] posted {len(rows_in)}건 · scope={scope}")

    rows = []
    for r in rows_in:
        out = check_row(r["company_jp"], (r.get("source_url") or "").strip(),
                        r.get("esr_pct"), args.timeout)
        rows.append(out)
        log("  %-9s %-24s %-7s p%-4s d=%-5s %s" % (
            out["verdict"].upper(), out["company"], out["esr_pct"],
            out.get("page") or "-", out.get("distance") if out.get("distance") is not None else "-",
            (out.get("label") or out["fetch"].get("error") or "")[:40]))

    counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in VERDICTS}
    counts["fetch_failed"] = sum(1 for r in rows if r["verdict"] == "fetch_failed")
    # 조정치 축은 **따로 센다**. 기권(abstain_no_prose)을 SKIP 으로 삼키면 "몇 사가 아예
    # 판정되지 않았는지" 가 어디에도 안 남는다 — 이 저장소가 반복해서 데인 형태다.
    adj_counts = {v: sum(1 for r in rows if r.get("adjusted_verdict") == v)
                  for v in ADJUSTED_VERDICTS}
    not_found = [r for r in rows if r["verdict"] == "not_found"]
    adjusted = [r for r in rows if r.get("adjusted_verdict") in ("adjusted_alt", "adjusted_only")]
    log("")
    log("[summary] " + " · ".join(f"{k}={v}" for k, v in counts.items()))
    log("[adjusted] " + " · ".join(f"{k}={v}" for k, v in adj_counts.items()))
    for r in not_found:
        log(f"[not_found] {r['company']} esr={r['esr_pct']} — {r['url']}")
    for r in adjusted:
        alts = "·".join(f"{a['pct']}%(p{a['page']})" for a in r.get("adjusted_alternatives") or [])
        log(f"[{r['adjusted_verdict']}] {r['company']} esr={r['esr_pct']}"
            f" 한정어={r.get('adjusted_qualifiers')} 대안={alts or '없음'}")

    payload = {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "scope": scope,
        "targets": len(rows),
        "unique_urls": len({r["url"] for r in rows}),
        "summary": counts,
        "adjusted_summary": adj_counts,
        "not_found": len(not_found),
        "adjusted": len(adjusted),
        "proximity_chars": PROXIMITY_CHARS,
        "adjusted_qualifiers": list(ADJUSTED_QUALIFIERS),
        "rows": rows,
    }
    out_path = Path(args.out)
    if out_path.exists() and not args.force:
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8")).get("scope", "all")
        except Exception:
            prev = "all"
        if SCOPE_RANK.get(scope, 0) < SCOPE_RANK.get(prev, 0):
            out_path = out_path.with_suffix(f".{scope}.json")
            log(f"[guard] 기존 산출이 더 넓은 범위({prev})라 덮어쓰지 않는다 — {out_path} 로 쓴다"
                f" (덮어쓰려면 --force)")
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"[out] {out_path}  (scope={scope})")
    return 1 if not_found else 0


if __name__ == "__main__":
    raise SystemExit(main())
