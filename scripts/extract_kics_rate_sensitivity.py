"""Extract K-ICS 지급여력 금리민감도 (rate-sensitivity) from md_inbox -> master + diag.

Source: 경영공시 `금리 민감도 분석` table (2-key matrix: 경과조치 적용전/후 x measure
{지급여력비율/금액/기준금액} x {base, -100bp, -50bp, +50bp, +100bp}).
Spec (정본): docs/agents/kics-rate-sensitivity-spec.md.

Self-validation built in (RS1): 비율[c] ≈ 금액[c] / 기준금액[c] x 100 for every shock
column c. Tables are parsed absolute-first; if RS1 fails, re-interpreted as delta
(absolute = base + cell, 흥국 계열) and re-checked. Per-(사,분기) status -> diag.

Usage: PYTHONIOENCODING=utf-8 python scripts/extract_kics_rate_sensitivity.py [--dry-run]

2026-10-11 (재보사 수작업 정정 8쌍을 추출기가 스스로 재현하도록 — runlog 13 §4):
  · 단위 환산: 표 머리말 단위(「억원」으로 잘못 적힌 뮌헨·스위스리 표 포함)를 믿지 않고, 적용전 블록의 금액 base 를 kics_disclosure 헤드라인(억원)과 비교해
    비율이 100(백만원)·100000(천원) 근처면 금액 계열 전 칸을 나눈다(`unit_factor`). 비율(%)·듀레이션·컨벡서티는 단위 불변.
  · 잘린 라벨: 「지급여력기준금」(제네럴)도 기준금액 행으로 읽는다.
  · 쪽 넘김: 표가 쪽 사이에서 갈라지면 첫 데이터 행이 앞 표의 6칸 행(구분 칸에 경과조치 라벨 없음)으로 떨어진다 — 머리행 바로 아래 6칸 행을 되살린다.
  · 「0 인쇄 = 비어 있음」: 한 블록의 모든 칸이 0 이면(지급여력비율 0% · 금액 0 은 실제 값일 수 없다) 빈 블록으로 본다.
  · 비적용사 후 블록 미러(`NON_APPLIER_POST_MIRROR`): 원문이 경과조치 비적용·전후 동일을 명문으로 적고 후 블록을 공란·0 으로 인쇄한 (회사, 분기)만, 등재부에 있을 때에 한해
    적용전 블록을 후에 그대로 옮긴다(값을 새로 만들지 않는다). 기존 39사의 post_dash 구멍(RS6 알려진 구멍)은 등재가 없으므로 건드리지 않는다.
  · 같은 분기에 판이 둘이면 매니페스트가 정한 최신 판을 읽는다(`_disclosure_pdf_paths.prefer_latest_edition`).
"""
from __future__ import annotations
import argparse, io, json, re, sys, glob
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))   # scripts/ — 공통 헬퍼
from _disclosure_pdf_paths import latest_disclosure_pdfs, prefer_latest_edition  # noqa: E402
MD_INBOX = REPO / "md_inbox"
DISCLOSURE = REPO / "data" / "disclosure"
DISC_JSON = REPO / "kics_disclosure.json"
OUT_JSON = REPO / "kics_rate_sensitivity.json"
DIAG_JSON = REPO / "data" / "_derived" / "kics_rate_sensitivity_diag.json"

MEASURES = ["지급여력비율", "지급여력금액", "지급여력기준금액"]
# source column order after the 2 label cols: 기준금액, △100bp, △50bp, +50bp, +100bp
SRC_ORDER = ["base", "-100bp", "-50bp", "+50bp", "+100bp"]

# raw-PDF truncation/mis-pick suspects (spec §4) — section-absent here is suspicious
SUSPECTS = {("KR0080", None), ("KR0010", "2025.4Q"), ("KR0075", "2025.4Q")}

_PERIOD_RE = re.compile(r"^FY(\d{4})_Q([1-4])$")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def period_to_quarter(p):
    m = _PERIOD_RE.match(p)
    return f"{m.group(1)}.{m.group(2)}Q"


def parse_value(raw):
    if raw is None:
        return None
    c = str(raw).strip().replace(",", "").replace(" ", "").replace("%", "")
    if c in ("", "-", "─", "–", "—", "n/a", "N/A"):
        return None
    for ch in ("△", "▲", "▽", "▼", "−", "ı"):
        c = c.replace(ch, "-")
    pa = re.fullmatch(r"\((-?\d[\d.]*)\)", c)
    if pa:
        c = "-" + pa.group(1)
    c = c.lstrip("+")
    if not re.fullmatch(r"-?\d+(\.\d+)?", c):
        return None
    return float(c)


def pick_md(code, period):
    hits = glob.glob(str(MD_INBOX / period / f"{code}_*.md"))
    if not hits:
        return None
    # 같은 (분기, 회사)에 MD 가 둘이면(예: 스위스리 2023.4Q 옛 60쪽 판 + 새 `_v20240510` 판) 매니페스트가 정한 최신 판의 짝만 남긴다. 판정이 없으면 hits 그대로(종전 규칙).
    hits = [str(p) for p in prefer_latest_edition(period, code, [Path(h) for h in hits])]
    amended = [h for h in hits if "_amended" in h]
    pool = amended or hits
    return max(pool, key=lambda h: Path(h).stat().st_size)


def find_section_table(md_text):
    """Return the markdown table (list of | rows) under the 금리 민감도 분석 heading.

    2026.2Q 동양생명(KR0087, OCR/scanned) exposed a bug: the page-break running-header
    boilerplate ("## 수호천사동양생명" / "## 우리금융그룹") that OCR emits between the
    heading and its table looks like a heading itself, so the old "stop at the first #"
    rule broke *before* any table row was ever collected. Fix: a "#" line only ends the
    section once we've already collected >=1 table row (a true next-section boundary);
    a "#" line seen before that is page furniture — skip it and keep scanning. Bound the
    furniture-skip so a genuinely table-less section doesn't scan half the document.
    """
    lines = md_text.splitlines()
    for i, ln in enumerate(lines):
        if not ln.lstrip().startswith("#"):
            continue
        h = norm(ln)
        if "금리" in h and "민감도" in h and "분석" in h and not any(
                bad in h for bad in ("환율", "보험위험", "가정", "개요", "방법")):
            tbl = []
            scanned_since_heading = 0
            for ln2 in lines[i + 1:]:
                scanned_since_heading += 1
                s = ln2.lstrip()
                if s.startswith("#"):
                    if tbl:
                        break  # true next section — table already collected
                    if scanned_since_heading > 60:
                        break  # furniture-skip budget exhausted — genuinely no table
                    continue  # page-break furniture before the table starts
                if s.startswith("|"):
                    tbl.append(ln2)
            if tbl:
                return tbl
    return None


def match_measure(label):
    """Canonical measure for a label cell, tolerating 지금/지급 typo and OCR spacing."""
    n = norm(label).replace("지금여력", "지급여력")
    if "여력기준금" in n:   # 「…기준금액」 + 칸 폭에 잘린 「지급여력기준금」(제네럴 2024.4Q·2025.4Q)
        return "지급여력기준금액"
    if "여력비율" in n:
        return "지급여력비율"
    if "여력금액" in n:
        return "지급여력금액"
    return None


_NUM_TOK_RE = re.compile(r"^[△▲▽▼+\-]?[\d,]+(\.\d+)?$")


def extract_from_raw_pdf(code, period):
    """Fallback: reconstruct the 금리 민감도 분석 table directly from the raw PDF via
    word-bbox row clustering, for cases where Docling's MD dropped the table's content
    even though the source page was inside its own selected keyword window (confirmed
    2026.2Q KR0001/KR0051/KR0100: the page is *in* source_page_ranges and even in
    keyword_hit_pages, yet none of the table's text made it into the MD — a Docling
    conversion gap, not a page-selection gap; same root-cause *class* as inbox
    20260831T0700Z (there: whole 6-4 section dropped) but confirmed here for 6-8, and a
    general Docling-internals fix is out of this script's scope). Values are verified:
    every company below round-trips RS1 (비율=금액/기준금액x100) to <=0.1 and reproduces
    the page's own narrative sentence ("50bp 상승시 N%p 하락...") to the printed digit —
    see the 2026-09-01 rate-sensitivity round for the by-hand cross-check (word-bbox
    dump + 300dpi render) this function's output was diffed against before trusting it.

    Returns rows shaped like measure_rows(): [(frag, measure, [5 vals])], or None.
    """
    try:
        import fitz
    except ImportError:
        return None
    # raw/ 우선(없으면 pdf/), 판이 둘이면 매니페스트가 정한 최신 판 — `_disclosure_pdf_paths.latest_disclosure_pdfs`
    # (종전: pdf/ 먼저·이름순 첫 파일. pdf/ 폴더는 raw/ 로 합쳐져 어느 분기에도 없어 선택이 달라지지 않는다 — runlog 13 §5 에서 645조합 전수 대조).
    pdfs = latest_disclosure_pdfs(period, code, root=DISCLOSURE)
    if not pdfs:
        return None
    doc = fitz.open(str(pdfs[0]))
    target_i = None
    for i in range(doc.page_count):
        t = norm(doc.load_page(i).get_text())
        if "금리민감도분석" in t and "억원" in t:
            target_i = i
            break
    if target_i is None:
        doc.close()
        return None
    words = doc.load_page(target_i).get_text("words")
    doc.close()
    if not words:
        return None

    # group into visual lines by y0 (row gap on this table is >20pt; same-row jitter
    # observed <=0.3pt across companies, 2.0pt tolerance leaves ample margin either way)
    ws = sorted(words, key=lambda w: (w[1], w[0]))
    lines, cur, cur_y = [], [], None
    for w in ws:
        if cur and abs(w[1] - cur_y) > 2.0:
            lines.append(cur)
            cur = []
        cur.append(w)
        cur_y = w[1]
    if cur:
        lines.append(cur)

    # header line: sanity-gate only (has a token '기준금액' and one containing '100bp')
    # — confirms this is really the shock-column table before trusting any data row.
    if not any("기준금액" in "".join(w[4] for w in ln) and "100bp" in "".join(w[4] for w in ln)
               for ln in lines):
        return None

    out = []
    for ln in lines:
        ln_sorted = sorted(ln, key=lambda w: w[0])
        label_toks = [w[4] for w in ln_sorted if not _NUM_TOK_RE.match(w[4])]
        measure = match_measure(norm("".join(label_toks)))
        if not measure:
            continue
        num_toks = [w for w in ln_sorted if _NUM_TOK_RE.match(w[4])]
        if len(num_toks) < 5:
            continue
        # positional, NOT nearest-to-header-x: right-aligned columns shift a value's x0
        # left/right with its own digit count (a 3-digit "844" sits further right than a
        # 5-digit "48,808" would in the same column), which can put a value's x0 closer
        # to the *next* header cell than its own — confirmed wrong 2026.2Q KR0100 (기준
        #금액 적용후 base "844" nearest-matched into the -100bp slot, dropping base to
        # None). The row's 5 numeric tokens are always exactly [base,-100bp,-50bp,+50bp,
        # +100bp] left-to-right (spec, invariant) — trust column ORDER, not column X.
        num_toks = sorted(num_toks[-5:], key=lambda w: w[0])  # rightmost 5, then x-order
        vals = [parse_value(w[4]) for w in num_toks]
        out.append(("", measure, vals))
    return out or None


# Manual overrides: 원문이 순수 스캔(embedded text layer 0)이라 raw-PDF word-bbox도
# fitz MD도 못 읽는 셀. 300dpi 렌더링을 육안 판독해 확정(RS1 항등식 5열 전부
# tol<=0.05 이내, 서술문 "50bp 상승시 N%p 하락..." 4문장 전부 소수점까지 일치 확인).
# {(원보험사코드, 공시분기): {경과조치여부: {measure: [base,-100bp,-50bp,+50bp,+100bp]}}}
MANUAL_OVERRIDE = {
    ("KR0079", "2026.2Q"): {
        "적용전": {
            "지급여력비율": [155.3, 182.6, 168.5, 141.8, 130.5],
            "지급여력금액": [37207, 39716, 38546, 35796, 34468],
            "지급여력기준금액": [23962, 21752, 22874, 25252, 26415],
        },
        # 주3) 당사는 선택경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함
        "적용후": {
            "지급여력비율": [155.3, 182.6, 168.5, 141.8, 130.5],
            "지급여력금액": [37207, 39716, 38546, 35796, 34468],
            "지급여력기준금액": [23962, 21752, 22874, 25252, 26415],
        },
    },
}


def measure_rows(tbl):
    """Rows whose measure cell (col1) maps to a measure -> (col0frag, measure, [5 vals]).

    쪽 넘김: 표가 쪽 사이에서 갈라지면 docling 이 첫 데이터 행을 앞 표의 머리행 바로 아래 **6칸 행**
    (`| 지급여력비율 | 258.42 | 234.00 | … |`, 구분 칸에 경과조치 라벨이 없다)으로 떨군다(제네럴 2025.4Q p27→p28). 7칸을 요구하는 종전 규칙은 이 행을 버려
    적용전 지급여력비율이 빠졌다. 머리행(`구분` 으로 시작) 바로 다음의 6칸 행이 (측정항목 라벨, 숫자 5개)로 읽히면 ("", measure, vals) 로 되살린다.
    """
    out = []
    after_header = False
    for ln in tbl:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):   # `|---|---|` 구분선은 머리행 상태를 바꾸지 않는다
            continue
        if len(cells) == 6 and after_header:
            after_header = False
            m = match_measure(cells[0])
            if m:
                vals = [parse_value(c) for c in cells[1:6]]
                if any(v is not None for v in vals):
                    out.append(("", m, vals))
            continue
        after_header = norm(cells[0]) == "구분"
        if len(cells) < 7:
            continue
        m = match_measure(cells[1])
        if m:
            vals = [parse_value(c) for c in cells[2:7]]
            out.append((cells[0], m, vals))
    return out


# 비적용사 후 블록 미러 등재부 — 원문이 경과조치 비적용·전후 동일을 **명문으로** 적고(근거 쪽·문장 아래), 금리 민감도 표의 후 블록을 공란 또는 0 으로 인쇄한 (회사, 분기).
# 후 블록이 공란·0(빈 블록)일 때만 같은 표의 적용전 블록을 후에 그대로 옮긴다 — 후 블록에 실제 값이 인쇄돼 있으면 문서 값이 이긴다. 값을 만들어 넣는 것이 아니다.
# 일반 규칙(헤드라인 값_적용후 == 값, 또는 MD 의 비적용 문장)으로 만들지 않은 이유: 같은 증거가 기존 39사의 post_dash 구멍(RS6 알려진 구멍 31행 — 하나손보·삼성생명·신한이지·동양)에도
# 있어 일반 규칙은 기존 39사 행을 바꾼다. 그 구멍은 분기별 raw 각주 확인을 거쳐 owner/validation 이 따로 정한다(inbox/parser/20260921T1400Z §A). 새 (회사, 분기)는 원문을 확인한 뒤 여기에 추가한다.
# 근거(validation 단계 10 §4 `hannover12.py` 가 raw PDF 로 재확인): 하노버(KR1104)는 경과조치를 적용하지 않는다 — 4개 문서 모두 「당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함」.
NON_APPLIER_POST_MIRROR = {
    ("KR1104", "2024.4Q"): "FY2024_Q4 p34·p35 + 민감도 표(p52) 주3) 「당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함」; 후 블록 공란",
    ("KR1104", "2025.2Q"): "FY2025_Q2 p18 「당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함」; 후 블록(p32) 0 인쇄",
    ("KR1104", "2025.4Q"): "FY2025_Q4 p34 「당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함」; 후 블록(p52) 0 인쇄",
    ("KR1104", "2026.2Q"): "FY2026_Q2 p18 「당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함」; 후 블록(p33) 0 인쇄",
}

# 단위 환산(표 머리말 단위는 믿지 않는다 — 뮌헨 2025.4Q·스위스리 2024.4Q 는 「억원」이라 적고 실제는 백만원·천원; 같은 문서 경과조치 표(「단위: 백만원」)와 헤드라인 억원으로 확정).
_UNIT_FACTORS = (100.0, 100000.0)      # 백만원 -> 억원 · 천원 -> 억원 (실제로 나온 단위만)
_UNIT_TOL = 0.02                        # 헤드라인이 억원 정수/소수 2자리로 인쇄돼 있어 생기는 반올림 폭


def unit_factor(pre_base, anchors):
    """적용전 블록의 금액 base(지급여력금액·지급여력기준금액) 를 kics_disclosure 헤드라인(억원)과 비교해 단위 배율을 돌려준다.
    둘(있는 것 전부)의 비율이 100 또는 100000 의 ±2% 안이면 그 배율, 아니면 1.0(억원 그대로·판정 불가는 환산하지 않는다)."""
    ratios = []
    for m in ("지급여력금액", "지급여력기준금액"):
        b, a = pre_base.get(m), anchors.get(m)
        if b is None or a is None or a == 0 or b == 0:
            continue
        ratios.append(b / a)
    if not ratios:
        return 1.0
    for f in _UNIT_FACTORS:
        if all(abs(r / f - 1.0) <= _UNIT_TOL for r in ratios):
            return f
    return 1.0


def scale_amounts(d, factor):
    """금액 계열(지급여력금액·지급여력기준금액)만 factor 로 나눈다. 비율(%)은 단위가 없다."""
    if factor == 1.0:
        return d
    return {m: ([None if v is None else v / factor for v in vals] if m in _DC_MEASURES else vals) for m, vals in d.items()}


def block_phase(block):
    j = norm("".join(r[0] for r in block))
    if "후" in j:
        return "적용후"
    if "전" in j:
        return "적용전"
    return None


def split_blocks(rows):
    blocks, cur = [], []
    for r in rows:
        if r[1] == MEASURES[0] and cur:
            blocks.append(cur); cur = []
        cur.append(r)
    if cur:
        blocks.append(cur)
    return blocks


def block_dict(block):
    """{measure: [5 vals]}; None if block is entirely empty (all-dash/blank) **or all zero**.

    「0 인쇄 = 비어 있음」: 비적용사가 후 블록을 지급여력비율 0 · 금액 0 · 기준금액 0 으로 채워 인쇄하는 표가 있다(하노버 2025.2Q·2025.4Q·2026.2Q). 0/0/0 은 값이 아니라 빈 블록 표시다
    (지급여력비율 0% 는 실제 회사에 불가능). 전 칸이 None/0 이면 대시 블록과 같은 빈 블록으로 본다."""
    d = {}
    any_val = False
    for _frag, m, vals in block:
        d[m] = vals
        if any(v is not None and v != 0 for v in vals):
            any_val = True
    return d if any_val else None


def rs1_status(d):
    """Ratio identity check across shock columns. Return True/False/None(can't check)."""
    r, a, b = d.get("지급여력비율"), d.get("지급여력금액"), d.get("지급여력기준금액")
    if not (r and a and b):
        return None
    checks = []
    for c in range(5):
        if r[c] is None or a[c] is None or b[c] is None or b[c] == 0:
            continue
        expected = a[c] / b[c] * 100
        tol = max(0.5, 0.005 * abs(r[c]))
        checks.append(abs(expected - r[c]) <= tol)
    return all(checks) if checks else None


def as_delta(d):
    out = {}
    for m, vals in d.items():
        base = vals[0]
        out[m] = [base] + [(base + v if (v is not None and base is not None) else None)
                           for v in vals[1:]]
    return out


def resolve_block(d):
    """Return (resolved_dict, encoding) choosing absolute vs delta by RS1."""
    abs_ok = rs1_status(d)
    if abs_ok is True:
        return d, "absolute"
    dd = as_delta(d)
    if rs1_status(dd) is True:
        return dd, "delta"
    # neither passes — keep absolute, flag rs1_fail (validator will RED if truly wrong)
    return d, ("rs1_fail" if abs_ok is False else "unverified")


# 듀레이션·컨벡서티가 의미를 갖는 것은 **금액** 계열뿐이다. 지급여력비율은 두 금액의
# 나눗셈이라 그 1·2차 미분을 '듀레이션/컨벡서티'라 부르면 잘못된 이름이 된다 -> null 로 둔다.
_DC_MEASURES = ("지급여력금액", "지급여력기준금액")


def duration_convexity(measure, base, dn100, up100):
    """±100bp 평행이동에서 유효듀레이션(년)·유효컨벡서티. (owner 2026-08-30)

        D = -(V₊ - V₋) / (2 · V₀ · Δy)
        C =  (V₊ + V₋ - 2·V₀) / (V₀ · Δy²)

    부호 규약: **D 양수 = 금리 상승 시 가치 감소**(자산 듀레이션이 부채보다 김).
    보험사 순자산(가용자본)은 해지옵션·최저보증 때문에 금리에 오목한 경우가 많아
    C 가 음수로 나오는 것이 정상이다.

    ±50bp 로도 같은 계산이 가능하지만 컬럼은 owner 지시대로 2개만 둔다 — 주값은
    바깥 충격(±100bp)이다. 두 벌의 괴리는 `validate_kics_rate_sensitivity.py` 가 본다.
    """
    if measure not in _DC_MEASURES:
        return None, None
    if base in (None, 0) or dn100 is None or up100 is None:
        return None, None
    dy = 0.01
    d = -(up100 - dn100) / (2.0 * base * dy)
    c = (up100 + dn100 - 2.0 * base) / (base * dy * dy)
    return round(d, 4), round(c, 2)


def emit_rows(meta, quarter, phase, d):
    rows = []
    for m, vals in d.items():
        dur, conv = duration_convexity(m, vals[0], vals[1], vals[4])
        rows.append({
            **meta, "공시분기": quarter, "경과조치여부": phase, "measure구분": m,
            "-100bp": vals[1], "-50bp": vals[2], "base": vals[0],
            "+50bp": vals[3], "+100bp": vals[4],
            "듀레이션": dur, "컨벡서티": conv,
        })
    return rows


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--period", help="restrict to one md_inbox period, e.g. FY2026_Q2 "
                     "(scoped run: merges into the master instead of full-rebuild-overwrite)")
    ap.add_argument("--only", help="comma-separated 원보험사코드 list; with --period, "
                     "restricts the scoped run further so untouched companies' existing "
                     "rows for that quarter (e.g. hand-patched cells) are never re-derived")
    args = ap.parse_args(argv)
    scoped = bool(args.period)
    only_codes = set(args.only.split(",")) if args.only else None

    disc = json.loads(DISC_JSON.read_text(encoding="utf-8"))
    prefix = {}
    anchor = {}  # RS2: (code, quarter, item) -> base value from kics_disclosure
    for r in disc:
        prefix.setdefault(r["원보험사코드"], {
            "원보험사코드": r["원보험사코드"], "원수사명": r["원수사명"],
            "티커": r["티커"], "생손보여부": r["생손보여부"]})
        if r["항목번호"] in (1, 14, 27):
            anchor[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = parse_value(str(r["값"]))
    anchor_item = {"지급여력금액": 1, "지급여력기준금액": 14, "지급여력비율": 27}

    if scoped:
        periods = [args.period]
    else:
        periods = sorted(p.name for p in MD_INBOX.glob("FY*_Q*") if p.is_dir())
    out_rows, diag = [], {}
    stats = {}
    touched_combos = set()  # (code, quarter) actually (re)produced this run — scoped-merge key
    fallback_used = []  # (code, quarter, method) for the run report
    rescaled = []  # (code, quarter, factor) — 표 단위가 억원이 아니라 환산한 칸 (run report)
    mirrored = []  # (code, quarter) — 비적용사 후 블록 미러(등재부) (run report)

    for period in periods:
        quarter = period_to_quarter(period)
        codes = sorted(only_codes) if only_codes else sorted(prefix)
        for code in codes:
            if code not in prefix:
                continue
            md = pick_md(code, period)
            key = f"{code}|{quarter}"
            if md is None:
                continue  # company didn't file that quarter
            tbl = find_section_table(Path(md).read_text(encoding="utf-8"))
            if not tbl:
                # MD path failed — try raw-PDF word-bbox fallback, then manual override,
                # before conceding the section is absent (spec §4: absence must be earned,
                # not assumed — see extract_from_raw_pdf docstring for why this exists).
                fb_rows = extract_from_raw_pdf(code, period)
                fb_method = "pdf_fallback"
                if fb_rows is None:
                    ov = MANUAL_OVERRIDE.get((code, quarter))
                    if ov is not None:
                        fb_rows = []
                        for ph, measures in ov.items():
                            for m, vals in measures.items():
                                fb_rows.append((ph, m, list(vals)))
                        fb_method = "manual_override"
                if fb_rows is None:
                    # absent section: normal pre-format, or a flagged suspect
                    if (code, quarter) in SUSPECTS or (code, None) in SUSPECTS:
                        diag[key] = "suspect_truncation"
                        stats["suspect_truncation"] = stats.get("suspect_truncation", 0) + 1
                    else:
                        diag[key] = "absent_section"
                    continue
                rows = fb_rows
                fallback_used.append((code, quarter, fb_method))
            else:
                rows = measure_rows(tbl)
            touched_combos.add((code, quarter))
            blocks = split_blocks(rows)
            # phase per block; default a label-less block to 적용전/적용후 in order
            # (BEFORE dedup, so identical-but-distinct 전/후 blocks survive).
            assigned = []
            for blk in blocks:
                ph = block_phase(blk)
                if ph is None:
                    ph = "적용전" if not any(p == "적용전" for p, _ in assigned) else "적용후"
                assigned.append((ph, block_dict(blk)))
            # dedup verbatim-duplicate blocks (OCR), e.g. KR1098 두 적용전 동일
            seen, uniq = set(), []
            for ph, d in assigned:
                sig = (ph, json.dumps(d, sort_keys=True, default=str)) if d else (ph, "EMPTY")
                if sig in seen:
                    continue
                seen.add(sig); uniq.append((ph, d))

            emitted, encs, post_dash = 0, set(), False
            pre_base = {}
            # 단위 배율: 마지막 적용전 블록(RS2 가 비교하는 블록)의 금액 base 대 헤드라인(억원). 같은 표의 후 블록에도 같은 배율.
            factor = 1.0
            for ph, d in uniq:
                if ph == "적용전" and d is not None:
                    factor = unit_factor({m: v[0] for m, v in resolve_block(d)[0].items()},
                                         {"지급여력금액": anchor.get((code, quarter, 1)),
                                          "지급여력기준금액": anchor.get((code, quarter, 14))})
            if factor != 1.0:
                rescaled.append((code, quarter, factor))
            pre_rd, have_post = None, False
            for ph, d in uniq:
                if d is None:  # all-dash / blank / all-zero block
                    if ph == "적용후":
                        post_dash = True
                    continue
                rd, enc = resolve_block(d)
                rd = scale_amounts(rd, factor)
                encs.add(enc)
                if ph == "적용전":
                    pre_base = {m: v[0] for m, v in rd.items()}
                    pre_rd = rd
                elif ph == "적용후":
                    have_post = True
                out_rows.extend(emit_rows(prefix[code], quarter, ph, rd))
                emitted += len(rd)
            # 비적용사 후 블록 미러(등재부 NON_APPLIER_POST_MIRROR 에 있는 (회사, 분기)만): 후 블록이 공란·0 이면 같은 표의 적용전 블록을 그대로 옮긴다.
            post_mirrored = False
            if not have_post and pre_rd is not None and (code, quarter) in NON_APPLIER_POST_MIRROR:
                out_rows.extend(emit_rows(prefix[code], quarter, "적용후", pre_rd))
                emitted += len(pre_rd)
                post_mirrored, post_dash = True, False
                mirrored.append((code, quarter))

            # RS2: does the 적용전 base agree with the headline kics_disclosure?
            rs2_diff = False
            for m, item in anchor_item.items():
                a = anchor.get((code, quarter, item))
                bv = pre_base.get(m)
                if a is not None and bv is not None:
                    tol = 0.5 if m == "지급여력비율" else 2.0
                    if abs(a - bv) > tol:
                        rs2_diff = True

            if emitted == 0:
                diag[key] = "absent_subtable"
            elif "rs1_fail" in encs:
                diag[key] = "rs1_fail"
            elif rs2_diff:
                diag[key] = "rs2_base_diff"  # faithfully extracted but base != headline (basis/scope)
            elif "delta" in encs:
                diag[key] = "delta_converted"
            elif post_mirrored:
                diag[key] = "post_mirrored"  # 후 블록은 문서에 값이 없고(공란·0), 등재부 근거로 적용전을 옮겼다
            elif post_dash:
                diag[key] = "post_dash"
            else:
                diag[key] = "extracted"
            stats[diag[key]] = stats.get(diag[key], 0) + 1

    print(f"periods: {len(periods)}  output rows: {len(out_rows)}")
    print("diag status counts:")
    for k, v in sorted(stats.items(), key=lambda kv: -kv[1]):
        print(f"  {k:22s} {v}")
    # show rs1_fail / suspect for review
    for flag in ("rs1_fail", "rs2_base_diff", "suspect_truncation", "delta_converted"):
        hits = [k for k, s in diag.items() if s == flag]
        if hits:
            print(f"  -- {flag}: {', '.join(sorted(hits))}")
    if fallback_used:
        print(f"fallback used ({len(fallback_used)}):")
        for code, quarter, method in fallback_used:
            print(f"  {code:8s} {quarter}  {method}")
    if rescaled:
        print(f"unit rescaled ({len(rescaled)}): " + ", ".join(f"{c} {q} /{f:g}" for c, q, f in rescaled))
    if mirrored:
        print(f"post block mirrored from 적용전 ({len(mirrored)}): " + ", ".join(f"{c} {q}" for c, q in mirrored))

    if args.dry_run:
        print("\n(dry-run; no write)")
        return 0

    if not scoped:
        OUT_JSON.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        DIAG_JSON.write_text(json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nwrote {OUT_JSON.name} ({len(out_rows)} rows) + {DIAG_JSON.name}")
        return 0

    # ---- scoped merge: touch ONLY (code, quarter) combos this run actually produced
    # rows for (or reprocessed to zero). Everything else in the master — every other
    # period, every company not in --only — passes through byte-for-byte. This is what
    # keeps a --period/--only run from wiping owner gold rows or earlier cell-level
    # patches (e.g. KR0010 2026.2Q's OCR fix) that a full rebuild would regenerate wrong.
    existing = json.loads(OUT_JSON.read_text(encoding="utf-8")) if OUT_JSON.exists() else []
    before_n = len(existing)
    before_combos = {(r["원보험사코드"], r["공시분기"]) for r in existing}
    kept = [r for r in existing if (r["원보험사코드"], r["공시분기"]) not in touched_combos]
    merged = kept + out_rows
    after_combos = {(r["원보험사코드"], r["공시분기"]) for r in merged}
    untouched_before = {c for c in before_combos if c not in touched_combos}
    untouched_after = {c for c in after_combos if c not in touched_combos}
    print(f"\nscoped merge: existing={before_n} rows / {len(before_combos)} combos; "
          f"touched_combos={len(touched_combos)}; merged={len(merged)} rows / {len(after_combos)} combos")
    if untouched_before != untouched_after:
        print("ABORT: a combo outside touched_combos changed — refusing to write.")
        print(f"  missing after merge: {sorted(untouched_before - untouched_after)}")
        return 2
    OUT_JSON.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    existing_diag = json.loads(DIAG_JSON.read_text(encoding="utf-8")) if DIAG_JSON.exists() else {}
    existing_diag.update(diag)
    DIAG_JSON.write_text(json.dumps(existing_diag, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON.name} ({len(merged)} rows, scoped merge) + {DIAG_JSON.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
