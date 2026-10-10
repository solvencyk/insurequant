# -*- coding: utf-8 -*-
"""Stage B helpers: turn the raw rows of one extracted table into canonical-label views.

All values returned are RAW (printed unit).  `cur` is the first numeric column (current period in every table
family seen so far; verified against the master anchors in the calling code).
"""
from __future__ import annotations

# exact-match canonical labels (normalised labels, whitespace-free)
_EXACT = {
    "자산총계": "자산총계", "부채총계": "부채총계", "자본총계": "자본총계",
    "부채와자본총계": "부채와자본총계", "부채및자본총계": "부채와자본총계", "자본및부채총계": "부채와자본총계",
    "자본과부채총계": "부채와자본총계", "부채와자본의총계": "부채와자본총계",
    "현금및예치금": "현금및예치금", "현금및현금성자산": "현금및현금성자산",
    "대출채권": "대출채권", "부동산": "부동산", "비운용자산": "비운용자산", "운용자산": "운용자산",
    "보험계약자산": "보험계약자산", "재보험계약자산": "재보험계약자산", "유형자산": "유형자산", "무형자산": "무형자산",
    "순확정급여자산": "순확정급여자산", "기타자산": "기타자산", "특별계정자산": "특별계정자산",
    "책임준비금": "책임준비금", "보험계약부채": "보험계약부채", "재보험계약부채": "재보험계약부채",
    "투자계약부채": "투자계약부채", "계약자지분조정": "계약자지분조정", "기타부채": "기타부채",
    "특별계정부채": "특별계정부채", "차입부채": "차입부채", "차입금": "차입부채",
    "자본금": "자본금", "자본잉여금": "자본잉여금", "신종자본증권": "신종자본증권", "이익잉여금": "이익잉여금",
    "자본조정": "자본조정", "기타포괄손익누계액": "AOCI",
}

_PL_CONTAINS = [
    ("법인세비용차감전", "세전이익"), ("법인세비용", "법인세"), ("당기순이익", "당기순이익"), ("당기순손실", "당기순이익"),
    ("반기순이익", "당기순이익"), ("분기순이익", "당기순이익"), ("당기순손익", "당기순이익"), ("반기순손익", "당기순이익"),
    ("분기순손익", "당기순이익"), ("영업손익", "영업이익"),
    ("재보험서비스비용", "재보험서비스비용"), ("재보험수익", "재보험수익"),
    ("보험서비스비용", "보험서비스비용"), ("보험수익", "보험수익"), ("보험손익", "보험손익"),
    ("기타사업비용", "기타사업비용"), ("투자손익", "투자손익"), ("투자수익", "투자수익"), ("투자비용", "투자비용"),
    ("영업이익", "영업이익"), ("영업손실", "영업이익"), ("영업외손익", "영업외손익"), ("영업외수익", "영업외수익"),
    ("영업외비용", "영업외비용"),
]


# ordered substring rules (first hit wins) -- ONLY for long, unambiguous labels.  Short generic labels (자본금, 이익잉여금,
# 대출채권, 부동산, 기타부채 ...) must match exactly (see _STRICT): "기본요구자본금" contains "자본금" and is not equity.
_CONTAINS = [
    ("부채와자본총계", "부채와자본총계"), ("부채및자본총계", "부채와자본총계"), ("자본및부채총계", "부채와자본총계"),
    ("자산총계", "자산총계"), ("부채총계", "부채총계"), ("자본총계", "자본총계"),
    ("상각후원가측정유가증권", "AC_SEC"), ("상각후원가유가증권", "AC_SEC"),
    ("상각후원가측정금융자산", "AC_FA"), ("상각후원가금융자산", "AC_FA"),
    ("상각후원가측정대출채권", "AC_LOAN"), ("상각후원가대출채권", "AC_LOAN"), ("상각후원가측정예치금", "AC_DEP"),
    ("상각후원가측정", "AC_OTHER"), ("상각후원가", "AC_OTHER"),
    ("기타포괄손익-공정가치측정", "FVOCI"), ("기타포괄손익공정가치측정", "FVOCI"), ("기타포괄손익인식", "FVOCI"),
    ("매도가능", "AFS"), ("만기보유", "HTM"),
    ("당기손익-공정가치측정", "FVPL"), ("당기손익공정가치측정", "FVPL"), ("당기손익인식", "FVPL"),
    ("관계·종속", "관계종속"), ("관계∙종속", "관계종속"), ("관계․종속", "관계종속"), ("관계종속", "관계종속"),
    ("기타포괄손익누계액", "AOCI"), ("기타포괄손익누적액", "AOCI"), ("기타자본구성요소", "AOCI"),
    ("현금및예치금", "현금및예치금"),
    ("특별계정부채", "특별계정부채"), ("특별계정자산", "특별계정자산"),
    ("계약자지분조정", "계약자지분조정"),
    ("재보험계약자산", "재보험계약자산"), ("재보험계약부채", "재보험계약부채"),
    ("보험계약자산", "보험계약자산"), ("보험계약부채", "보험계약부채"), ("투자계약부채", "투자계약부채"),
    ("순확정급여자산", "순확정급여자산"),
]

# short generic labels: exact match only (after the whitespace / numbering / footnote normalisation)
_STRICT = {
    "현금및현금성자산": "현금및현금성자산", "현금및현금성자산(주석)": "현금및현금성자산",
    "책임준비금": "책임준비금", "비운용자산": "비운용자산", "운용자산": "운용자산", "대출채권": "대출채권", "부동산": "부동산",
    "유형자산": "유형자산", "무형자산": "무형자산", "기타부채": "기타부채", "기타자산": "기타자산",
    "자본금": "자본금", "자본잉여금": "자본잉여금", "신종자본증권": "신종자본증권", "자본조정": "자본조정",
    "이익잉여금": "이익잉여금", "이익잉여금(결손금)": "이익잉여금", "결손금": "이익잉여금", "미처리결손금": "이익잉여금",
    "이익잉여금(결손금)합계": "이익잉여금", "본점영업기금": "자본금", "영업기금": "자본금", "차입부채": "차입부채", "차입금": "차입부채",
}


# contains-matching must not catch flow lines of other statements (cash-flow, OCI, notes): "현금및현금성자산의증가",
# "기타포괄손익공정가치측정금융자산평가손익", "...의처분", "...손실충당금"
_NOT_A_BS_LINE = ("평가손익", "처분", "취득", "증가", "감소", "변동", "환율", "이익", "손실", "손상", "환입", "수익", "비용",
                  "차익", "차손", "충당금", "이자", "배당", "기초", "기말", "재분류", "대체", "상계")


def canon(label: str, family: str = "bs"):
    if family == "pl":
        for sub, c in _PL_CONTAINS:
            if sub in label:
                return c
        return None
    if label in _EXACT:
        return _EXACT[label]
    if label in _STRICT:
        return _STRICT[label]
    if any(w in label for w in _NOT_A_BS_LINE):
        return None
    for sub, c in _CONTAINS:
        if sub in label:
            return c
    if label in ("총계", "계"):
        return "TOTAL?"
    if label in ("와총계", "와자본총계", "및총계"):
        return "부채와자본총계"
    return None


_BS_START = {"현금및예치금", "현금및현금성자산", "FVPL", "FVOCI", "AC_SEC", "운용자산", "AFS", "HTM"}


def _slice(kind: str, canons: list) -> tuple[int, int]:
    """[start, end) indices of the block of interest within the table rows."""
    n = len(canons)
    if kind in ("sum_pl", "pl_full"):
        s = next((i for i, c in enumerate(canons) if c == "보험손익"), None)
        if s is None:
            return 0, 0
        e = next((i for i in range(s, n) if canons[i] == "당기순이익"), n - 1)
        return s, e + 1
    if kind == "equity":
        g = next((i for i, c in enumerate(canons) if c == "자본금"), None)
        if g is None:
            return 0, 0
        s = g - 1 if g > 0 and canons[g - 1] == "자본총계" else g
        e = next((i for i in range(g, n) if canons[i] == "AOCI"), min(n - 1, g + 7))
        return s, e + 1
    # sum_bs / bs_full: from first asset-component row to the closing 부채와자본총계 (inclusive)
    s = next((i for i, c in enumerate(canons) if c in _BS_START or c == "자산총계"), None)
    if s is None:
        return 0, 0
    e = next((i for i in range(s, n) if canons[i] == "부채와자본총계"), None)
    if e is None:
        return s, n
    return s, e + 1


def _cluster(xs, gap=9.0):
    xs = sorted(xs)
    cl = []
    for x in xs:
        if cl and x - cl[-1][-1] <= gap:
            cl[-1].append(x)
        else:
            cl.append([x])
    return [sum(c) / len(c) for c in cl]


_ANCHOR_BS = {"자산총계", "부채총계", "자본총계", "부채와자본총계"}
_ANCHOR_PL = {"보험손익", "당기순이익", "세전이익", "투자손익"}


# balance-sheet lines that can legitimately be negative (a leading separate '-' cell may be their minus sign)
_SIGNABLE_BS = {"이익잉여금", "AOCI", "자본조정", "자본잉여금", "계약자지분조정", "자본총계", "신종자본증권"}


def align_block(block: list, canons: list, family: str):
    """Re-express the values of the rows of ONE table block on its VALUE columns.

    Columns are found from the geometry of ALL numeric tokens of the block (right edges, 9pt clusters):
      * two-tier statements put the amount of an ordinary line in an inner column and the amount of a subtotal in an
        outer column of the SAME period.  Two adjacent clusters (<= 100pt apart) belong to the same period iff they
        never occur in the same row (a row prints one amount per period) -- merged greedily left to right, never
        merging clusters that co-occur;
      * a leading note-number column ('주석') co-occurs with the first period, so it is never merged; it is dropped when
        all its tokens are small integers and it holds no totals-row token;
      * a column that holds ONLY dash tokens is not a value column ('auxiliary'): it is either the separate minus-sign
        cell some PDFs print left of an amount ('-   2,552,800', the amount right-aligned, the sign left-aligned) or a nil
        placeholder column.  Left of the first value column it is a sign column when it covers at most half of the
        first column's rows and every row it touches may be negative -> the first value is negated.  Between/after
        value columns the next value column is flagged `unsure` for those rows (its sign cannot be told).
    vals[k] is None where a row has no token for period column k.  Returns (new row dicts, column x positions)."""
    anchors = _ANCHOR_BS if family == "bs" else _ANCHOR_PL
    all_x = [x for r in block for x in r.get("xs", [])]
    if not all_x:
        return [dict(r) for r in block], []
    centers = _cluster(all_x)
    n = len(centers)

    def col_of(x):
        return min(range(n), key=lambda i: abs(centers[i] - x))

    present = []                       # per row: set of clusters
    for r in block:
        present.append({col_of(x) for x in r.get("xs", [])})
    co = [[False] * n for _ in range(n)]
    for ps in present:
        for i in ps:
            for j in ps:
                if i != j:
                    co[i][j] = True
    # greedy merge of tiers
    comps: list = []
    for c in range(n):
        if comps:
            last = comps[-1]
            if (centers[c] - centers[last[-1]] <= 100.0) and not any(co[c][k] for k in last):
                last.append(c)
                continue
        comps.append([c])
    comp_of = {}
    for ci, comp in enumerate(comps):
        for c in comp:
            comp_of[c] = ci
    # note column: leftmost component, tokens all small integers, no totals-row token, co-occurs with the next component
    anchored = set()
    for r, ps, cn in zip(block, present, canons):
        if cn in anchors:
            anchored |= {comp_of[c] for c in ps}
    drop = set()
    if len(comps) >= 2:
        toks0 = [v for r in block for v, x, d in zip(r["vals"], r.get("xs", []), r["dash"])
                 if comp_of[col_of(x)] == 0 and not d]
        small0 = len(toks0) >= 3 and all(float(v).is_integer() and 0 < v < 100 for v in toks0)
        if small0 and 0 not in anchored:
            drop.add(0)
        elif small0:
            # an anchor row (e.g. 당기순이익 with its '주석 14') puts a note number into the first column; it is still a note
            # column when the amounts next to it are two or more orders of magnitude larger (statements in 원 / 천원)
            toks1 = sorted(abs(v) for r in block for v, x, d in zip(r["vals"], r.get("xs", []), r["dash"])
                           if comp_of[col_of(x)] == 1 and not d and v)
            if toks1 and toks1[len(toks1) // 2] >= 100 * max(toks0):
                drop.add(0)
    # auxiliary (dash-only) components
    n_num = {ci: 0 for ci in range(len(comps))}
    n_dash = {ci: 0 for ci in range(len(comps))}
    for r in block:
        for x, d in zip(r.get("xs", []), r["dash"]):
            (n_dash if d else n_num)[comp_of[col_of(x)]] += 1
    aux = {ci for ci in range(len(comps)) if n_num[ci] == 0 and n_dash[ci] > 0 and ci not in drop}
    keep = [ci for ci in range(len(comps)) if ci not in drop and ci not in aux]
    pos = {ci: k for k, ci in enumerate(keep)}
    first = keep[0] if keep else None
    # sign component: the nearest dash-only component left of the first value component
    sign_ci = None
    if first is not None:
        left = [ci for ci in aux if ci < first]
        if left:
            cand = max(left)
            rows_neg = [i for i, r in enumerate(block)
                        if any(comp_of[col_of(x)] == cand for x in r.get("xs", []))]
            n_first = sum(1 for r in block
                          if any((comp_of[col_of(x)] == first and not d) for x, d in zip(r.get("xs", []), r["dash"])))
            if rows_neg and len(rows_neg) <= 0.5 * max(1, n_first):
                sign_ci = cand
    out = []
    for r, cn in zip(block, canons):
        signable = family == "pl" or cn in _SIGNABLE_BS
        vals = [None] * len(keep)
        dash = [False] * len(keep)
        unsure = [False] * len(keep)
        best_x = [None] * len(keep)
        neg = False
        for v, d, x in zip(r["vals"], r["dash"], r.get("xs", [])):
            ci = comp_of[col_of(x)]
            if ci == sign_ci:
                if signable:
                    neg = True
                elif keep:
                    unsure[0] = True            # a minus sign on a line that is never negative: do not trust the row
                continue
            if ci in aux:
                nxt = [k for k2, k in pos.items() if k2 > ci]
                if nxt:
                    unsure[min(nxt)] = True
                continue
            if ci not in pos:
                continue
            k = pos[ci]
            if best_x[k] is None or x > best_x[k]:
                best_x[k] = x
                vals[k] = None if d else v
                dash[k] = bool(d)
        signed = False
        if neg and keep and vals[0] is not None and not dash[0]:
            vals[0] = -abs(vals[0])
            signed = True
        nr = dict(r)
        nr["vals"], nr["dash"], nr["unsure"] = vals, dash, unsure
        if signed:
            nr["sign_applied"] = True
        out.append(nr)
    return out, [round(max(centers[c] for c in comps[ci]), 1) for ci in keep]


def view_all(table: dict) -> dict:
    """{canonical: [row, ...]} in document order, restricted to the block of interest of the table kind and with
    values aligned to the value columns (note-number column removed).  Bare '총계' rows are resolved positionally:
    first -> 자산총계, second -> 부채총계 (vertical captions swallowed the 자산/부채 prefix).  Cached on the table."""
    if "_view" in table:
        return table["_view"]
    kind = table["kind"]
    family = "pl" if kind in ("sum_pl", "pl_full") else "bs"
    rows = table["rows"]
    canons = [canon(r["label"], family) for r in rows]
    s, e = _slice(kind, canons)
    block, bcanons = rows[s:e], canons[s:e]
    # resolve bare totals first so that they count as anchors
    tot_seen = 0
    resolved = []
    for c in bcanons:
        if c == "TOTAL?":
            tot_seen += 1
            c = "자산총계" if tot_seen == 1 else ("부채총계" if tot_seen == 2 else None)
        resolved.append(c)
    # column geometry is read from the rows we actually use: page-number / caption / sub-line rows of the block
    # (canonical label None) would put stray tokens into the value-column clusters
    keep = [(r, c) for r, c in zip(block, resolved) if c is not None]
    aligned, vcols = align_block([r for r, _ in keep], [c for _, c in keep], family)
    out: dict = {}
    for r, (_, c) in zip(aligned, keep):
        out.setdefault(c, []).append(r)
    table["_view"] = out
    table["_vcols"] = vcols
    return out


def view(table: dict) -> dict:
    """{canonical: first row}"""
    return {k: v[0] for k, v in view_all(table).items()}


def cur(row):
    """current-period value (first VALUE column, note-number column already removed); None if empty or a printed dash."""
    return col(row, 0)


def col(row, k):
    if row is None or len(row["vals"]) <= k:
        return None
    if row.get("unsure") and row["unsure"][k]:
        return None                 # a separate dash cell sits left of this amount: its sign cannot be told
    return None if row["dash"][k] else row["vals"][k]
