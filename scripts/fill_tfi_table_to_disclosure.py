"""Extract items 47-54 (the '(1) 공통적용 경과조치 관련' TFI detail table) into
kics_disclosure.json.

Until this script existed, items 47-54 had **no extractor at all** -- every
cell in the corpus (476-495 rows per item, out of ~536 possible buckets) was
put there by one-off `fix_2026*.py` company/quarter patch scripts or manual
`apply_transition_vision_overrides.py` runs. That's why the same bug (item48
polluted with item3's value) recurred 8+ separate times across sessions --
each fix touched one company and never generalised. This script is the
generalisation.

Table shape (one single markdown table, confirmed by direct inspection of
KR0005 2026.2Q and cross-checked against 463 other quarters -- see
`scripts/_probes/_tfi_enumerate_v2.py` in git history/session log for the
corpus-wide census this design is based on):

    구분                                    경과조치 적용 전   경과조치 적용 후
    지급여력비율 (%)                          ...              ...          <- item27 (NOT ours)
    지급여력금액                              ...              ...          <- item1  (NOT ours)
    기본자본                                 ...              ...          <- item2  (NOT ours)
    보완자본                                 ...              ...          <- item3  (NOT ours)
    보완자본 한도 적용 전                      ...              ...          <- item47
    보완자본 한도                             ...              ...          <- item48
    해약환급금 부족분 상당액 중 ...초과분        ...              ...          <- item49
    (기발행 신종자본증권)                      ...              ...          <- item53
    (기발행 후순위채무)                        ...              ...          <- item54
    지급여력기준금액                          ...              ...          <- item14 (NOT ours)

Items 50/51/52 (기본자본/보완자본/지급여력금액 "TFI표 자신") are the **same
three physical rows** already listed above (기본자본/보완자본/지급여력금액),
just captured under their own item numbers independent of whatever
item1/2/3 already hold. This matters because item1/2/3's `값` (전) comes from
a *different, bigger* summary table elsewhere in the filing (fill_period's
core extractor), so it can disagree with this table's own figure by a
rounding/scope sliver (confirmed on KR0005: item2=6313 vs item50=6313.02).
item50/51/52 exist precisely to preserve *this table's* own pre/post pair,
uncontaminated by whatever the headline table says. See
`src/solvency/validation/kics_json_rules.py` around line 1041 ("47/48/49 를
부모로 갖는 '보완자본' 셀은 마스터에 둘 있다") for the validator's side of
this.

item48 vs item3 confusion (the recurring bug this script exists to kill)
--------------------------------------------------------------------------
"보완자본 한도 적용 전" / "보완자본 한도" / "보완자본" share a common prefix.
A naive matcher that checks "보완자본" first grabs every one of these rows.
`TFI_ROW_MAP` below is ordered **longest/most-specific first** and reuses
`_match_row_label` (first-match-in-list-order wins) from
`fill_post_transition_to_disclosure.py` -- the same function + convention
already used correctly for items 1/2/3/14/27 in that script's `COMMON_ROW_MAP`.

There is a second collision this ordering does NOT protect against: some
filings also carry an unrelated row "6. 보완자본 한도를 초과한 금액" (a
*different* concept -- the excess-over-limit amount, from the "Ⅱ.지급여력
금액으로 불인정하는 항목" breakdown) whose normalised text still contains
"보완자본한도" as a substring. Empirically (471-file corpus scan) this row
only ever appears inside the *audit-statement* duplicate table (single
"금액" column, Roman-numeral rows -- see `_pick_pre_post_columns` failing on
it), which this script already excludes via the pre/post-column-pick
requirement. `_looks_like_excess_row` below is a second, cheap guard against
it in case some future filing prints it with real pre/post columns.

Table-selection modes (found by scanning all 541 md_inbox files across
14 quarters -- see git history of scripts/_probes/_tfi_enumerate*.py):
  MODE A (~461/471 files): a table containing the "보완자본 한도" signature
    row, whose header resolves via `_pick_pre_post_columns` (imported,
    unchanged) to two column indices -- validated further by requiring both
    columns to actually carry numeric data across >=3 rows (a raggedly
    split header, e.g. KR0032 2023.1Q's 5-cell
    ['구분','경과조치 적용 전','경과조치','적용','후'], can make the shared
    picker's fallback grab a bare label-fragment column that is blank on
    every single row -- silently wrong, not just missing).
  MODE B (mirror): header has exactly 2 cells (label + one value column)
    and the table's own heading context says "해당사항 없음"/"해당없음"
    (TFI not applied, filer still prints a pre-only table -- documented
    precedent: 하나손해보험 KR0050, kics_json_rules.py's TFI_NA discussion).
    적용후 = 적용전 (mirrored, not left blank -- matches the established
    convention already used for post-transition item1/2/3/14/27).
  MODE C (lost header): `_pick_pre_post_columns` fails outright, but the
  "header" row's own first cell normalises to a *known TFI row label*
    (docling dropped the real 구분/전/후 header line and promoted the first
    data row into its place -- KR0087 동양생명 2025.1Q). Recovered by
    treating [header]+body as data rows with pre_idx=1/post_idx=2 fixed
    (every other row in the same table shares that column layout).

  Any table not resolved by A/B/C is left alone and reported as
  unextractable-this-pass -- never guessed.

Row-merge splitting: docling occasionally glues 2-3 of this table's own
rows into one physical row (label cells concatenated, value cells
space-joined -- e.g. KR0049 2026.1Q: "보완자본 한도 적용 전 보완자본 한도
해약환급금 부족분 상당액 중 해약환급금 상당액 초과분" with pre-cell
"36,546 133,851 226,842"). `_MERGE_GROUPS` recognises exactly the two
concatenation patterns seen in the corpus scan and splits by matching
token count; anything that doesn't match one of those exact sequences is
left as an ordinary (probably unparseable -> skipped) row rather than
guessed at.

Self-checks (never silently trust a single extraction):
  - item48 == item14(적용전, from the ALREADY-LOADED core items) x 50%
    (`TIER2_LIMIT_RATIO`, imported from kics_json_rules.py, not retyped).
    A NEW item48 candidate that fails this check is NOT written -- flagged
    instead. (Existing item48 values are never touched by this script
    regardless -- see the overwrite policy below.)
  - `_tier2_branch()` (imported from kics_json_rules.py -- the CAPPED /
    UNCAPPED / I49_IN_I47_* / TFI_NA_* classifier, ~100 lines of prior art
    this script must NOT reimplement per the operator brief) is run against
    every bucket's merged (existing + candidate) view, for both target
    item3 and item51, both columns. The branch name is recorded on every
    bucket in the report; branch=NEITHER is flagged prominently but does
    NOT block the write of raw extracted values -- a filing's own numbers
    not reconciling via a known formula is a legitimate, well-precedented
    outcome in this codebase (headline-vs-TFI-table scope differences),
    not proof the extraction itself is wrong.

Overwrite policy (hard requirement from the operator brief):
  This script NEVER overwrites an existing 값/값_적용후. It only ever adds a
  brand-new (code, quarter, item_no) row when that cell is completely
  absent from the master. When a freshly-parsed candidate value disagrees
  with an already-present value, it is recorded in the CONFLICT report and
  the master is left untouched -- the existing value may be an
  owner-reviewed correction that predates this script.

CLI mirrors the other fill_*.py scripts' conventions (argparse, cell-level
UPSERT, `json.dumps(rows, ensure_ascii=False, indent=2)` +
`write_text(encoding="utf-8")`) but flips the safety default the operator
brief asked for: dry-run unless `--apply` is passed (the other fill_*.py
scripts default the other way, with an opt-in `--dry-run`).

Usage
-----
    python scripts/fill_tfi_table_to_disclosure.py --period FY2026_Q2
    python scripts/fill_tfi_table_to_disclosure.py --all-periods --apply
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import types
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"

sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from fill_post_transition_to_disclosure import (  # noqa: E402
    _scan_tables_with_context,
    _pick_pre_post_columns,
    _normalise,
    _parse_value,
    _normalise_unit,
    _match_row_label,
    _md_period_to_quarter,
)
from solvency.validation.kics_json_rules import (  # noqa: E402
    _tier2_branch,
    TIER2_LIMIT_RATIO,
    _TIER2_SCOPE_EXCL,
    IMAGE_OCR_COMPANIES,
    IMAGE_OCR_TOLERANCE,
)

DEFAULT_TOLERANCE = 2.0  # matches kics_json_rules.py's module default (2.0억)

# Row label keywords -> item_no. Longest/most-specific keyword first --
# _match_row_label returns the FIRST list entry whose normalised form is a
# substring of the row label, so a shorter, more generic keyword MUST sort
# after any longer keyword it is a prefix of (same convention as
# fill_post_transition_to_disclosure.COMMON_ROW_MAP).
TFI_ROW_MAP: list[tuple[str, int]] = [
    ("보완자본 한도 적용 전", 47),
    ("보완자본 한도 적용", 47),  # docling dropped the trailing "전" -- KR0087 2024.1Q's
                                # 5-cell-header table ("경과조치 적용 후" fragmented into
                                # 3 cells) also truncates this ONE row's own label the
                                # same way; without this alias the row falls through to
                                # the bare "보완자본 한도" keyword below and gets
                                # misfiled as item48. Confirmed sole occurrence corpus-wide
                                # (grep '| 보완자본 한도 적용 |' across all 541 md_inbox files).
    ("보완자본 한도", 48),
    ("해약환급금", 49),
    ("신종자본증권", 53),   # not "기발행신종자본증권" -- survives the 기발행->기발생 OCR misread
    ("후순위채무", 54),     # not "기발행후순위채무" -- same reason
    ("지급여력금액", 52),   # after 지급여력기준금액 would collide, but that label isn't in
    ("기본자본", 50),       # this map at all (item14/1/2/3/27 are out of scope, see module docstring)
    ("보완자본", 51),       # bare -- must stay LAST (prefix of every 보완자본* label above)
]

ITEM_LABELS: dict[int, str] = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)",
    51: "보완자본(TFI표, 공통적용경과조치)",
    52: "지급여력금액(TFI표, 공통적용경과조치)",
    53: "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    54: "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
}

TFI_ITEMS = tuple(ITEM_LABELS)

SIGNATURE = "보완자본한도"  # normalised -- unique to this table across a whole filing

# "6. 보완자본 한도를 초과한 금액" (Ⅱ.지급여력금액으로 불인정하는 항목의 세부)
# is a DIFFERENT concept from item48 that happens to contain the same
# substring. Empirically it only ever appears inside the audit-statement
# duplicate table (no valid pre/post columns -- excluded before this guard
# even runs), but kept as a second, cheap line of defence.
_EXCESS_ROW_MARKERS = ("한도를초과한금액", "한도초과")


def _looks_like_excess_row(label: str) -> bool:
    nl = _normalise(label)
    return any(m in nl for m in _EXCESS_ROW_MARKERS)


# Two docling row-merge patterns actually observed in the corpus (see module
# docstring). Each entry: (item_nos in row order, keywords that must appear
# in that order inside the merged label's normalised text).
_MERGE_GROUPS: list[tuple[tuple[int, ...], tuple[str, ...]]] = [
    ((47, 48, 49), ("보완자본한도적용전", "보완자본한도", "해약환급금")),
    ((53, 54), ("신종자본증권", "후순위채무")),
]


def _try_split_merged_row(
    label: str, pre_raw: str, post_raw: str
) -> list[tuple[int, str, str | None]] | None:
    """Split a docling-merged multi-concept row, or return None if it isn't one."""
    nl = _normalise(label)
    for item_nos, kws in _MERGE_GROUPS:
        cursor = 0
        ok = True
        for kw in kws:
            idx = nl.find(kw, cursor)
            if idx == -1:
                ok = False
                break
            cursor = idx + len(kw)
        if not ok:
            continue
        pre_toks = pre_raw.split()
        if len(pre_toks) != len(item_nos):
            continue
        pre_vals = [_parse_value(t) for t in pre_toks]
        if any(v is None for v in pre_vals):
            continue
        post_toks = post_raw.split() if post_raw else []
        if len(post_toks) == len(item_nos):
            post_vals: list[str | None] = [_parse_value(t) for t in post_toks]
        else:
            post_vals = [None] * len(item_nos)
        return list(zip(item_nos, pre_vals, post_vals))
    return None


_NA_MARKERS = ("해당사항없음", "해당없음")


def _heading_says_not_applicable(headings: list[str]) -> bool:
    ctx = _normalise(" ".join(headings[-3:]))
    return any(m in ctx for m in _NA_MARKERS)


def _find_signature_tables(tables: list[dict]) -> list[dict]:
    return [
        t for t in tables
        if any(SIGNATURE in _normalise(row[0]) for row in t["table"] if row)
    ]


def _column_has_data(table_rows: list[list[str]], idx: int, min_hits: int = 3) -> bool:
    hits = 0
    for row in table_rows:
        if idx >= len(row):
            continue
        if _parse_value(row[idx]) is not None:
            hits += 1
    return hits >= min_hits


def _select_table_mode(t: dict) -> tuple[str, list[list[str]], int, int, str]:
    """Return (mode, data_rows, pre_idx, post_idx, reason). mode == "SKIP" means
    data_rows/pre_idx/post_idx are meaningless; reason always explains why."""
    table = t["table"]
    if not table:
        return "SKIP", [], -1, -1, "EMPTY_TABLE"
    header = table[0]
    body = table[1:]

    # --- Mode A: normal pre/post header -----------------------------------
    pre_idx, post_idx = _pick_pre_post_columns(header)
    if pre_idx is not None and post_idx is not None:
        if len(header) > 3:
            # Extra header cells happen when docling splits "경과조치 적용
            # 전/후" into 2 cells -- usually harmless (the leftover cell is
            # blank on every row, e.g. KR0011 2026.2Q's
            # ['구분','경과조치 적용 전','경과조치','적용 후'] where column 2
            # is empty throughout and 1/3 hold the real pre/post data).
            # Two failure shapes need separate guards:
            #   (a) the CHOSEN column is itself blank everywhere (KR0032
            #       2023.1Q -- the picker's fallback grabbed a bare label
            #       fragment, not data).
            #   (b) an UNCHOSEN column actually holds real, comparable data
            #       (KR0002 2025.2Q's 4-cell header
            #       ['구분','경과조치','적용 전','경과조치 적용 후']: the
            #       picker lands on indices 2/3, but index 1 -- "경과조치",
            #       unchosen -- carries the TRUE pre value on most rows,
            #       with the row's real (pre,post) pair inconsistently
            #       split across columns 1/2/3 row by row. This shape does
            #       NOT fail the single-column blank check in (a) -- both
            #       chosen columns have *some* data, just the wrong mix --
            #       so it needs its own guard: any left-over column with as
            #       much data as the sparser of the two chosen ones means
            #       the split is ambiguous, not merely cosmetic.
            col_indices = range(len(header))
            counts = {i: sum(1 for row in body if i < len(row) and _parse_value(row[i]) is not None) for i in col_indices}
            if counts.get(pre_idx, 0) == 0 or counts.get(post_idx, 0) == 0:
                return (
                    "SKIP", [], -1, -1,
                    f"RAGGED_HEADER_DEGENERATE_COLUMN(header={header!r} pre_idx={pre_idx} "
                    f"post_idx={post_idx} counts={counts} -- chosen column(s) blank across body, distrust)",
                )
            min_chosen = min(counts[pre_idx], counts[post_idx])
            leftover = [i for i in col_indices if i not in (0, pre_idx, post_idx)]
            ambiguous = [i for i in leftover if counts.get(i, 0) >= min_chosen]
            if ambiguous:
                return (
                    "SKIP", [], -1, -1,
                    f"RAGGED_HEADER_AMBIGUOUS_COLUMN(header={header!r} pre_idx={pre_idx} "
                    f"post_idx={post_idx} counts={counts} -- unused column(s) {ambiguous} carry "
                    "as much data as the chosen ones, split is unreliable, distrust)",
                )
        return "A", body, pre_idx, post_idx, "OK"

    # --- Mode C: lost header (first data row promoted to header) ---------
    if len(header) == 3 and _normalise(header[0]) and not _looks_like_excess_row(header[0]):
        item_hit = _match_row_label(header[0], TFI_ROW_MAP)
        if item_hit is not None:
            return "C", [header] + body, 1, 2, f"LOST_HEADER_RECOVERED(first_cell={header[0]!r})"

    # --- Mode B: mirror (single-column, TFI not applied) ------------------
    if len(header) == 2:
        if _heading_says_not_applicable(t["headings"]):
            return "B", body, 1, 1, "MIRROR_NA"
        return (
            "SKIP", [], -1, -1,
            f"TWO_COL_HEADER_BUT_NO_NA_MARKER(header={header!r} headings={t['headings'][-2:]!r})",
        )

    return "SKIP", [], -1, -1, f"COLUMN_PICK_FAILED(header={header!r})"


def _extract_tfi_values(
    t: dict,
) -> tuple[dict[int, tuple[str, str | None]], str, str]:
    """Return ({item_no: (pre, post_or_None)}, mode, reason)."""
    mode, data_rows, pre_idx, post_idx, reason = _select_table_mode(t)
    if mode == "SKIP":
        return {}, mode, reason
    unit = t["unit"]
    out: dict[int, tuple[str, str | None]] = {}
    for row in data_rows:
        if not row or max(pre_idx, post_idx) >= len(row):
            continue
        label = row[0]
        if _looks_like_excess_row(label):
            continue
        pre_raw = row[pre_idx]
        post_raw = row[post_idx] if mode != "B" else row[pre_idx]

        pre_v = _parse_value(pre_raw)
        if pre_v is None:
            merged = _try_split_merged_row(label, pre_raw, post_raw or "")
            if merged is not None:
                for item_no, mp, mo in merged:
                    if item_no in out:
                        continue
                    mp_scaled = _normalise_unit(mp, unit)
                    mo_scaled = _normalise_unit(mo, unit) if mo is not None else None
                    out[item_no] = (mp_scaled, mo_scaled)
            continue

        item_no = _match_row_label(label, TFI_ROW_MAP)
        if item_no is None or item_no in out:
            continue
        post_v = _parse_value(post_raw) if post_raw is not None else None
        pre_scaled = _normalise_unit(pre_v, unit)
        post_scaled = _normalise_unit(post_v, unit) if post_v is not None else None
        out[item_no] = (pre_scaled, post_scaled)
    return out, mode, reason


def _extract_bucket(text: str) -> tuple[dict[int, tuple[str, str | None]], list[str]]:
    """Try every signature table in the file in document order; first one
    that yields any values wins (mirrors fill_post_transition's "first
    common section table wins" convention)."""
    tables = _scan_tables_with_context(text)
    candidates = _find_signature_tables(tables)
    log: list[str] = []
    if not candidates:
        return {}, ["NO_SIGNATURE_TABLE"]
    for t in candidates:
        values, mode, reason = _extract_tfi_values(t)
        log.append(f"table(headings={t['headings'][-2:]!r}): mode={mode} reason={reason} n_items={len(values)}")
        if values:
            return values, log
    return {}, log


# items 50/51/52 are the same physical rows as core items 2/3/1 (see module
# docstring) -- used as unit-vote anchors, same technique as
# fill_post_transition_to_disclosure._apply_post_corrections's "UNIT-FIX
# vote" (not imported -- that function is tightly coupled to the OTHER
# script's items 1/2/3/14/27 provenance bookkeeping; this is the same idea
# re-applied to items 47-54's own anchors).
_UNIT_VOTE_ANCHORS = ((52, 1), (50, 2), (51, 3))


def _apply_unit_vote(
    candidate: dict[int, tuple[str, str | None]],
    core: dict[int, dict],
    existing: dict[int, dict],
    log: list[str],
) -> None:
    """A 공통적용 table with no unit hint of its own inherits whatever
    '(단위: ...)' was last declared earlier in the document -- sometimes
    wrong (confirmed live: KR0002 2026.2Q inherits '억원' from an unrelated
    headline table three sections earlier when its own numbers are 백만원,
    producing a candidate item52 exactly 100x the already-correct existing
    item1). Vote using every available anchor: items 50/51/52 against their
    already-loaded core counterparts 2/3/1, PLUS any of 47-54 that already
    carry an existing value (a prior manual fix, presumably correct). If
    every anchor agrees on the same non-1 correction factor, rescale the
    WHOLE candidate dict (a wrong unit hint is a per-table, not per-row,
    mistake) and log it -- never applied on a single dissenting or mixed
    vote."""
    votes: list[float] = []
    detail: list[str] = []
    anchor_pairs = list(_UNIT_VOTE_ANCHORS)
    for item_no in candidate:
        if item_no in existing and existing[item_no].get("값") not in (None, ""):
            anchor_pairs.append((item_no, item_no))
    for cand_item, truth_item in anchor_pairs:
        if cand_item not in candidate:
            continue
        cand_pre = candidate[cand_item][0]
        truth_row = core.get(truth_item) if truth_item != cand_item else existing.get(cand_item)
        if truth_row is None:
            continue
        truth_v = truth_row.get("값")
        if truth_v in (None, "") or cand_pre in (None, ""):
            continue
        try:
            c = float(cand_pre)
            t = float(truth_v)
        except (TypeError, ValueError):
            continue
        if c == 0 or t == 0:
            continue
        ratio = t / c
        if 95 < ratio < 105:
            votes.append(100.0)
            detail.append(f"item{cand_item}~item{truth_item}: ratio={ratio:.3g} -> x100")
        elif 0.0095 < ratio < 0.0105:
            votes.append(0.01)
            detail.append(f"item{cand_item}~item{truth_item}: ratio={ratio:.3g} -> x0.01")
    if not votes or not all(abs(v - votes[0]) < 1e-9 for v in votes):
        return
    factor = votes[0]
    log.append(f"UNIT-VOTE: applying x{factor:g} to all candidate items ({'; '.join(detail)})")
    for item_no, (pre_v, post_v) in list(candidate.items()):
        try:
            new_pre = pre_v if pre_v is None else _fmt_rescaled(float(pre_v) * factor)
            new_post = post_v if post_v is None else _fmt_rescaled(float(post_v) * factor)
        except (TypeError, ValueError):
            continue
        candidate[item_no] = (new_pre, new_post)


def _fmt_rescaled(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def _tier2_bucket_view(
    core: dict[int, dict[str, float | None]], candidate: dict[int, tuple[str, str | None]]
) -> types.SimpleNamespace:
    """Build a minimal object with .values/.values_post (as required by
    _tier2_branch) merging already-loaded core items with this run's
    candidate 47-54 values -- for the advisory branch-classification report
    only, never used to gate a write except item48's own formula check."""

    def _f(x: str | float | None) -> float | None:
        if x is None:
            return None
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    values: dict[int, float] = {}
    values_post: dict[int, float] = {}
    for item_no, d in core.items():
        v = _f(d.get("값"))
        if v is not None:
            values[item_no] = v
        vp = _f(d.get("값_적용후"))
        if vp is not None:
            values_post[item_no] = vp
    for item_no, (pre, post) in candidate.items():
        v = _f(pre)
        if v is not None:
            values[item_no] = v
        vp = _f(post)
        if vp is not None:
            values_post[item_no] = vp
    return types.SimpleNamespace(values=values, values_post=values_post)


def _process_period(
    rows: list[dict], period_label: str
) -> tuple[list[dict], list[tuple[dict, str]], list[dict], list[dict], list[str]]:
    """Return (new_row_dicts, post_fills, conflict_records, bucket_reports, warnings).

    post_fills is a list of (existing_row_dict, new_값_적용후_value) pairs --
    existing_row_dict is the SAME object living inside `rows` (not a copy),
    so applying a fill is `row["값_적용후"] = value` in place; the caller
    only does that when --apply is passed."""
    quarter = _md_period_to_quarter(period_label)
    md_dir = MD_INBOX / period_label
    if not md_dir.is_dir():
        return [], [], [], [], [f"md_inbox/{period_label} missing"]

    core_index: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
    existing_47_54: dict[tuple[str, str], dict[int, dict]] = defaultdict(dict)
    meta_by_code: dict[str, dict] = {}
    for r in rows:
        if r["공시분기"] != quarter:
            continue
        key = (r["원보험사코드"], r["공시분기"])
        core_index[key][r["항목번호"]] = r
        if r["항목번호"] in TFI_ITEMS:
            existing_47_54[key][r["항목번호"]] = r
        meta_by_code.setdefault(r["원보험사코드"], {
            "원수사명": r["원수사명"], "티커": r["티커"], "생손보여부": r["생손보여부"],
        })

    new_rows: list[dict] = []
    post_fills: list[tuple[dict, str]] = []
    conflicts: list[dict] = []
    bucket_reports: list[dict] = []
    warnings: list[str] = []

    for md_path in sorted(md_dir.glob("*.md")):
        code = md_path.stem.split("_", 1)[0]
        if code not in meta_by_code:
            warnings.append(f"{period_label} {code}: no baseline metadata in master (skip)")
            continue
        text = md_path.read_text(encoding="utf-8", errors="replace")
        candidate, log = _extract_bucket(text)

        key = (code, quarter)
        existing = existing_47_54.get(key, {})
        core = core_index.get(key, {})

        if candidate:
            _apply_unit_vote(candidate, core, existing, log)

        item14_pre = core.get(14, {}).get("값")
        try:
            item14_pre_f = float(item14_pre) if item14_pre is not None else None
        except (TypeError, ValueError):
            item14_pre_f = None
        tol = IMAGE_OCR_TOLERANCE if code in IMAGE_OCR_COMPANIES else DEFAULT_TOLERANCE

        report = {
            "code": code, "quarter": quarter, "log": log,
            "n_candidate": len(candidate), "new": [], "conflict": [], "match": [],
            "post_fill": [], "selfcheck_blocked": [],
        }

        for item_no, (pre_v, post_v) in candidate.items():
            existing_row = existing.get(item_no)

            if item_no == 48 and existing_row is None and item14_pre_f is not None and pre_v is not None:
                try:
                    pre_f = float(pre_v)
                except ValueError:
                    pre_f = None
                if pre_f is not None:
                    expected = item14_pre_f * TIER2_LIMIT_RATIO
                    if abs(pre_f - expected) > tol:
                        report["selfcheck_blocked"].append(
                            f"item48 candidate {pre_f:g} != item14전x{TIER2_LIMIT_RATIO:g}="
                            f"{expected:g} (diff {pre_f - expected:g}, tol {tol:g}) -- NOT written"
                        )
                        continue

            if existing_row is None:
                new_row = {
                    "원보험사코드": code,
                    "원수사명": meta_by_code[code]["원수사명"],
                    "티커": meta_by_code[code]["티커"],
                    "생손보여부": meta_by_code[code]["생손보여부"],
                    "항목번호": item_no,
                    "항목명": ITEM_LABELS[item_no],
                    "공시분기": quarter,
                    "값": pre_v,
                }
                if post_v is not None:
                    new_row["값_적용후"] = post_v
                new_rows.append(new_row)
                report["new"].append((item_no, pre_v, post_v))
            else:
                existing_pre = existing_row.get("값")
                existing_post = existing_row.get("값_적용후")

                def _neq(a, b, tol=0.5):
                    # tol=0.5: items 50/51/52 duplicate items 2/3/1's own
                    # row (see module docstring) but item1/2/3's 값 was
                    # rounded to the nearest integer by the core extractor
                    # while this table's own reading keeps 2 decimals
                    # (confirmed: KR0005 existing item52='35693' vs this
                    # table's own '35692.65' -- same cell, different
                    # rounding, not a disagreement). A genuine conflict
                    # (item48's item3-copy contamination, OCR digit
                    # corruption, etc.) is never a sub-1-unit difference in
                    # this corpus -- it's off by 2x-10x or a wrong leading
                    # digit. 0.5 is the largest gap a single rounding step
                    # can produce.
                    if a is None or b is None:
                        return a is not None or b is not None
                    try:
                        return abs(float(a) - float(b)) > tol
                    except (TypeError, ValueError):
                        return str(a) != str(b)

                # `값` (pre) is present on essentially every existing row, so
                # any real mismatch there is a genuine conflict -- but
                # `값_적용후` (post) is the field this and the sibling
                # fill_post_transition_to_disclosure.py script routinely
                # ADD to an existing row (present-값/absent-값_적용후 is the
                # normal, common shape, not a disagreement). Distinguish:
                # existing_post is None -> a fillable gap on an otherwise-
                # untouched row (write it); existing_post has a real value
                # that disagrees -> genuine conflict (report, don't touch).
                pre_conflict = existing_pre is not None and _neq(existing_pre, pre_v)
                post_conflict = (
                    existing_post is not None and post_v is not None
                    and _neq(existing_post, post_v)
                )
                post_fillable = existing_post is None and post_v is not None

                if pre_conflict or post_conflict:
                    rec = {
                        "code": code, "quarter": quarter, "item_no": item_no,
                        "existing_pre": existing_pre, "candidate_pre": pre_v,
                        "existing_post": existing_post, "candidate_post": post_v,
                    }
                    conflicts.append(rec)
                    report["conflict"].append(rec)
                elif post_fillable:
                    post_fills.append((existing_row, post_v))
                    report["post_fill"].append((item_no, existing_pre, post_v))
                else:
                    report["match"].append(item_no)

        # advisory branch classification (report only, never blocks a write)
        merged_candidate = {n: (p, q) for n, (p, q) in candidate.items()}
        view = _tier2_bucket_view(core, merged_candidate)
        branches = {}
        for target in (3, 51):
            for post in (False, True):
                b, _ = _tier2_branch(view, post, DEFAULT_TOLERANCE, target_item=target, scope=_TIER2_SCOPE_EXCL)
                branches[(target, post)] = b
        report["branches"] = branches

        bucket_reports.append(report)

    return new_rows, post_fills, conflicts, bucket_reports, warnings


def main(argv: list[str]) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry-run report only)")
    parser.add_argument("--period", action="append", help="period label like FY2026_Q2 (may repeat)")
    parser.add_argument("--all-periods", action="store_true", help="process every FYxxxx_Qy under md_inbox/")
    parser.add_argument("--verbose", action="store_true", help="print per-file table-selection log")
    args = parser.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows from {JSON_PATH}")

    if args.all_periods:
        periods = sorted(p.name for p in MD_INBOX.glob("FY*_Q?") if p.is_dir())
    elif args.period:
        periods = args.period
    else:
        periods = ["FY2026_Q2"]
    print(f"processing periods: {periods}\n")

    all_new: list[dict] = []
    all_post_fills: list[tuple[dict, str]] = []
    all_conflicts: list[dict] = []
    all_reports: list[dict] = []
    all_warnings: list[str] = []

    for period in periods:
        new_rows, post_fills, conflicts, bucket_reports, warnings = _process_period(rows, period)
        all_new.extend(new_rows)
        all_post_fills.extend(post_fills)
        all_conflicts.extend(conflicts)
        all_reports.extend(bucket_reports)
        all_warnings.extend(warnings)

        print(f"=== {period} ===")
        n_files = len(bucket_reports)
        n_zero = sum(1 for r in bucket_reports if r["n_candidate"] == 0)
        n_new_cells = sum(len(r["new"]) for r in bucket_reports)
        n_post_fill_cells = sum(len(r["post_fill"]) for r in bucket_reports)
        n_conflict_cells = sum(len(r["conflict"]) for r in bucket_reports)
        n_selfcheck_blocked = sum(len(r["selfcheck_blocked"]) for r in bucket_reports)
        print(f"  companies scanned: {n_files}  zero-candidate: {n_zero}")
        print(f"  new cells (new rows): {n_new_cells}")
        print(f"  post-fill cells (existing row, only 값_적용후 was missing): {n_post_fill_cells}")
        print(f"  conflict cells (existing value disagrees, NOT overwritten): {n_conflict_cells}")
        print(f"  item48 self-check blocked (not written): {n_selfcheck_blocked}")
        if args.verbose:
            for r in bucket_reports:
                print(f"  --- {r['code']} {r['quarter']} ---")
                for line in r["log"]:
                    print(f"      {line}")
                if r["new"]:
                    print(f"      NEW: {r['new']}")
                if r["post_fill"]:
                    print(f"      POST_FILL: {r['post_fill']}")
                if r["conflict"]:
                    print(f"      CONFLICT: {r['conflict']}")
                if r["selfcheck_blocked"]:
                    print(f"      SELFCHECK_BLOCKED: {r['selfcheck_blocked']}")
                print(f"      branches: {r['branches']}")
        neither = [
            (r["code"], r["quarter"], k) for r in bucket_reports
            for k, v in r["branches"].items() if v == "NEITHER" and (r["new"] or r["conflict"])
        ]
        if neither:
            print(f"  branch=NEITHER buckets (advisory, not blocking): {neither}")
        print()

    if all_warnings:
        print("warnings:")
        for w in all_warnings:
            print(f"  - {w}")
        print()

    if all_conflicts:
        print(f"=== ALL CONFLICTS ({len(all_conflicts)}) -- existing value kept, reported only ===")
        for c in all_conflicts:
            print(
                f"  {c['code']} {c['quarter']} item{c['item_no']}: "
                f"existing(pre={c['existing_pre']!r}, post={c['existing_post']!r}) vs "
                f"candidate(pre={c['candidate_pre']!r}, post={c['candidate_post']!r})"
            )
        print()

    print(f"TOTAL new cells (new rows): {len(all_new)}")
    print(f"TOTAL post-fill cells (existing row, added missing 값_적용후 only): {len(all_post_fills)}")
    print(f"TOTAL conflicts: {len(all_conflicts)}")

    if not args.apply:
        print("(dry-run; no write -- pass --apply to write)")
        return 0

    if not all_new and not all_post_fills:
        print("nothing to write")
        return 0

    # Re-read the master fresh right before writing -- other sessions may
    # have touched it while this dry-run analysis ran (this repo has
    # multiple concurrent parser sessions on the same kics_disclosure.json;
    # observed live during this script's development: KR0011/KR0029's
    # 2026.2Q rows disappeared between two dry-runs a few minutes apart).
    # `all_new`/`all_post_fills` were computed against the in-memory `rows`
    # read at the top of main(); re-reading now and re-resolving post_fill
    # targets against the FRESH copy (by (code,quarter,item_no), not by
    # stale object identity) keeps this script's own write additive-only
    # even if the file moved under it mid-run.
    fresh_rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if len(fresh_rows) != len(rows):
        print(
            f"NOTE: master row count changed since load ({len(rows)} -> {len(fresh_rows)}) "
            "-- another session wrote to it during this run. Re-resolving post-fill "
            "targets against the fresh copy by (code,quarter,item_no)."
        )
    fresh_index = {
        (r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in fresh_rows
    }
    resolved_post_fills = []
    lost_post_fills = []
    for old_row_ref, value in all_post_fills:
        k = (old_row_ref["원보험사코드"], old_row_ref["공시분기"], old_row_ref["항목번호"])
        fresh_row = fresh_index.get(k)
        if fresh_row is None:
            lost_post_fills.append(k)
            continue
        if fresh_row.get("값_적용후") is not None:
            # someone else already filled it (or the row itself changed
            # shape) since the dry-run analysis -- don't clobber.
            lost_post_fills.append(k)
            continue
        resolved_post_fills.append((fresh_row, value))
    if lost_post_fills:
        print(f"NOTE: {len(lost_post_fills)} post-fill target(s) no longer safely fillable, skipped: {lost_post_fills}")

    backup_path = JSON_PATH.with_name(JSON_PATH.name + ".bak_pre_tfi_fill")
    if not backup_path.exists():
        backup_path.write_text(JSON_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"backup written: {backup_path}")

    for row, value in resolved_post_fills:
        row["값_적용후"] = value

    fresh_rows.extend(all_new)
    JSON_PATH.write_text(json.dumps(fresh_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"applied {len(resolved_post_fills)} post-fills + {len(all_new)} new rows")
    print(f"wrote {len(fresh_rows)} rows to {JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
