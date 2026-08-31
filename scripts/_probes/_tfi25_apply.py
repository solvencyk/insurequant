"""Apply the 25-RED TFI patch set to a kics_disclosure.json copy (cell-level, guarded).

Usage: PY _tfi25_apply.py <path-to-json> [--dry-run]

Each op is one of:
  ("correct", code, item, quarter, field, expected_old, new_value)   -- overwrite, guarded by expected_old
  ("addfield", code, item, quarter, field, new_value)                -- row exists, field currently absent/None
  ("create", code, item, quarter, fields_dict)                       -- row does not exist at all, append new row
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)",
    51: "보완자본(TFI표, 공통적용경과조치)",
    52: "지급여력금액(TFI표, 공통적용경과조치)",
    53: "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    54: "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
}

COMPANY_INFO = {
    "KR0001": ("메리츠화재해상보험", "000060", "손해보험"),
    "KR0003": ("롯데손해보험", "000400", "손해보험"),
    "KR0004": ("예별손해보험", "X", "손해보험"),
    "KR0011": ("DB손해보험", "005830", "손해보험"),
    "KR0029": ("AIG손해보험", "X", "손해보험"),
    "KR0051": ("신한이지손해보험", "X", "손해보험"),
    "KR0070": ("에이비엘생명보험", "X", "생명보험"),
    "KR0072": ("케이디비생명보험", "X", "생명보험"),
    "KR0080": ("에이아이에이생명보험", "X", "생명보험"),
    "KR0082": ("DB생명보험", "X", "생명보험"),
    "KR0083": ("푸본현대생명보험", "X", "생명보험"),
    "KR0087": ("동양생명", "082640", "생명보험"),
    "KR0094": ("신한라이프생명보험", "X", "생명보험"),
    "KR0097": ("하나생명보험", "X", "생명보험"),
    "KR0100": ("처브라이프생명보험", "X", "생명보험"),
    "KR0104": ("농협생명보험", "X", "생명보험"),
    "KR1011": ("IBK연금보험", "X", "생명보험"),
    "KR1098": ("카카오페이손해보험", "X", "손해보험"),
}

QUARTER = "2026.2Q"


def fmt(v):
    r = round(float(v), 2)
    if r == int(r):
        return str(int(r))
    return str(r)


def mk_row(code, item, fields):
    name, ticker, kind = COMPANY_INFO[code]
    row = {
        "원보험사코드": code,
        "원수사명": name,
        "티커": ticker,
        "생손보여부": kind,
        "항목번호": item,
        "항목명": LABELS[item],
        "공시분기": QUARTER,
    }
    row.update(fields)
    return row


# ---- planned operations -------------------------------------------------
OPS = [
    # KR0001 -- stale (2026.1Q carryover) correction, raw PDF p18 verified
    ("correct", "KR0001", 47, QUARTER, "값", 19627.2, 17484.88),
    ("addfield", "KR0001", 47, QUARTER, "값_적용후", None, 62.08),
    ("correct", "KR0001", 48, QUARTER, "값", 28892.4, 31553.53),
    ("addfield", "KR0001", 48, QUARTER, "값_적용후", None, 31553.53),
    ("create", "KR0001", 49, QUARTER, {"값": fmt(75409.56), "값_적용후": fmt(75409.56)}),

    # KR0003 -- raw MD (md_inbox line 626-634)
    ("addfield", "KR0003", 48, QUARTER, "값_적용후", None, 10555.50),
    ("create", "KR0003", 53, QUARTER, {"값": fmt(453.70)}),

    # KR0004 -- raw PDF p18 (docling dropped this page from MD)
    ("create", "KR0004", 47, QUARTER, {"값": fmt(0.49)}),
    ("create", "KR0004", 49, QUARTER, {"값": fmt(0)}),

    # KR0011 -- raw MD line 363-380 (mirrored table)
    ("addfield", "KR0011", 48, QUARTER, "값_적용후", None, 57549.42),
    ("create", "KR0011", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0011", 54, QUARTER, {"값": fmt(0)}),

    # KR0029 -- raw MD line 507-524 (mirrored table)
    ("addfield", "KR0029", 48, QUARTER, "값_적용후", None, 1389.83),

    # KR0051 -- raw MD line 362-388 (unit: 억원, dash memo rows)
    ("create", "KR0051", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0051", 54, QUARTER, {"값": fmt(0)}),

    # KR0070 -- raw MD line 447-464 (item54 already loaded, item53 dash)
    ("create", "KR0070", 53, QUARTER, {"값": fmt(0)}),

    # KR0072 -- raw MD line 320-337
    ("create", "KR0072", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0072", 54, QUARTER, {"값": fmt(0)}),

    # KR0080 (AIA) -- raw MD line 356-382
    ("create", "KR0080", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0080", 54, QUARTER, {"값": fmt(0)}),

    # KR0082 -- raw MD line 550-567 (item54 already loaded, item53 dash)
    ("create", "KR0082", 53, QUARTER, {"값": fmt(0)}),

    # KR0083 -- raw MD line 400-417 (item49 row is dash BOTH columns)
    ("create", "KR0083", 49, QUARTER, {"값": fmt(0), "값_적용후": fmt(0)}),

    # KR0087 -- raw PDF p17 visual render (docling OCR MD mis-shifted item49 to post-only)
    ("create", "KR0087", 47, QUARTER, {"값": fmt(12478.17)}),
    ("create", "KR0087", 49, QUARTER, {"값": fmt(16910.13)}),

    # KR0094 -- raw PDF p21 (docling dropped this page from MD; TFI=X but table still drawn)
    ("create", "KR0094", 47, QUARTER, {"값": fmt(8907.55)}),
    ("create", "KR0094", 49, QUARTER, {"값": fmt(50459.24)}),

    # KR0097 -- raw MD line 327-346
    ("create", "KR0097", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0097", 54, QUARTER, {"값": fmt(0)}),

    # KR0100 -- raw MD line 605-622
    ("create", "KR0100", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0100", 54, QUARTER, {"값": fmt(0)}),

    # KR0104 -- NO OP (TIER2_DUPLICATE_ROW raw-confirmed genuine, documented exception)

    # KR1011 -- raw PDF p18 (docling dropped this page from MD)
    ("create", "KR1011", 47, QUARTER, {"값": fmt(4346.77)}),
    ("create", "KR1011", 49, QUARTER, {"값": fmt(3557.89)}),

    # KR1098 -- raw MD line 429-444 (all three genuinely dash in both columns)
    ("create", "KR1098", 47, QUARTER, {"값": fmt(0), "값_적용후": fmt(0)}),
    ("create", "KR1098", 49, QUARTER, {"값": fmt(0), "값_적용후": fmt(0)}),
    ("create", "KR1098", 51, QUARTER, {"값": fmt(0), "값_적용후": fmt(0)}),

    # ---- round 2: 53_tfi_memo_rows RED newly exposed once 47/48/49 census completed ----
    # (axis G was SKIPping "TFI_MEMO_NO_TABLE" while body was incomplete; now that round-1
    #  completed the body, axis G requires 53/54 too. raw already read during round-1 recon.)
    ("create", "KR0001", 53, QUARTER, {"값": fmt(1791.95)}),
    ("create", "KR0001", 54, QUARTER, {"값": fmt(15630.85)}),
    ("create", "KR0004", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0004", 54, QUARTER, {"값": fmt(0)}),
    ("create", "KR0087", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0087", 54, QUARTER, {"값": fmt(0)}),
    ("create", "KR0094", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR0094", 54, QUARTER, {"값": fmt(0)}),
    ("create", "KR1011", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR1011", 54, QUARTER, {"값": fmt(1602.09)}),
    ("create", "KR1098", 53, QUARTER, {"값": fmt(0)}),
    ("create", "KR1098", 54, QUARTER, {"값": fmt(0)}),

    # ---- round 2: 3_tier2_composition RED newly exposed for KR1011 (item48 pre was item3-
    # copy contaminated: existing=7168=item3; raw p18 confirms true value=3610.46; with the
    # fix, CAPPED formula min(47,48)+49 = min(4346.77,3610.46)+3557.89 = 7168.35 ~= item3=7168,
    # closing the identity). KR0087's parallel case is NOT fixed here -- its item3 itself is a
    # different, pre-existing bug (mismapped from item1=48808, confirmed via raw p17/p19), so
    # correcting item48 alone would not close that identity; left untouched, flagged in report.
    ("correct", "KR1011", 48, QUARTER, "값", 7168, 3610.46),

    # KR0004 -- a concurrent session's pending patch file (data/_derived/_patch_2026q2_KR0004.json,
    # discovered while merging my own cells into it) independently read the SAME raw PDF p18 and
    # reached the SAME correction: existing item48=0 is under-loaded, true value (raw, both cols
    # mirrored) = 430,672 백만원 = 4306.72억. Cross-verified by two independent sessions.
    ("correct", "KR0004", 48, QUARTER, "값", 0, 4306.72),
]


def main():
    if len(sys.argv) < 2:
        print("usage: _tfi25_apply.py <path.json> [--dry-run]")
        return 1
    path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    data = json.loads(path.read_text(encoding="utf-8"))
    before_rows = len(data)
    before_combos = {(r.get("원보험사코드"), r.get("항목번호"), r.get("공시분기")) for r in data}

    index = {}
    for i, r in enumerate(data):
        key = (r.get("원보험사코드"), r.get("항목번호"), r.get("공시분기"))
        index.setdefault(key, []).append(i)

    log = []
    errors = []

    for op in OPS:
        kind = op[0]
        if kind == "correct":
            _, code, item, q, field, expected_old, new_val = op
            key = (code, item, q)
            idxs = index.get(key, [])
            if len(idxs) != 1:
                errors.append(f"CORRECT FAIL {key}: expected 1 row, found {len(idxs)}")
                continue
            row = data[idxs[0]]
            cur = row.get(field)
            cur_f = float(cur) if cur not in (None, "") else None
            if cur_f is None or abs(cur_f - expected_old) > 0.5:
                errors.append(
                    f"CORRECT GUARD FAIL {key}.{field}: expected_old={expected_old} "
                    f"but live value={cur!r} -- SKIPPED (possible concurrent edit)"
                )
                continue
            new_str = fmt(new_val)
            log.append(f"CORRECT {key}.{field}: {cur!r} -> {new_str!r}")
            if not dry_run:
                row[field] = new_str
        elif kind == "addfield":
            _, code, item, q, field, expected_old, new_val = op
            key = (code, item, q)
            idxs = index.get(key, [])
            if len(idxs) != 1:
                errors.append(f"ADDFIELD FAIL {key}: expected 1 row, found {len(idxs)}")
                continue
            row = data[idxs[0]]
            cur = row.get(field)
            if cur not in (None, ""):
                errors.append(
                    f"ADDFIELD GUARD FAIL {key}.{field}: expected empty but live value={cur!r} "
                    "-- SKIPPED (possible concurrent edit)"
                )
                continue
            new_str = fmt(new_val)
            log.append(f"ADDFIELD {key}.{field}: (empty) -> {new_str!r}")
            if not dry_run:
                row[field] = new_str
        elif kind == "create":
            _, code, item, q, fields = op
            key = (code, item, q)
            idxs = index.get(key, [])
            if idxs:
                errors.append(f"CREATE FAIL {key}: row already exists ({len(idxs)}) -- SKIPPED")
                continue
            new_row = mk_row(code, item, fields)
            log.append(f"CREATE {key}: {fields}")
            if not dry_run:
                data.append(new_row)
                index.setdefault(key, []).append(len(data) - 1)
        else:
            errors.append(f"UNKNOWN OP {op}")

    print(f"planned ops: {len(OPS)}")
    print(f"applied/would-apply: {len(log)}")
    for line in log:
        print("  " + line)
    if errors:
        print(f"ERRORS: {len(errors)}")
        for e in errors:
            print("  !! " + e)

    after_rows = len(data)
    after_combos = {(r.get("원보험사코드"), r.get("항목번호"), r.get("공시분기")) for r in data}
    new_combos = after_combos - before_combos
    print(f"rows: {before_rows} -> {after_rows} (delta {after_rows - before_rows})")
    print(f"new (code,item,quarter) combos: {len(new_combos)}")
    for c in sorted(new_combos):
        print("   +", c)
    # scope check: every new/changed combo must be code in COMPANY_INFO and quarter==2026.2Q
    out_of_scope = [c for c in new_combos if c[0] not in COMPANY_INFO or c[2] != QUARTER]
    print(f"out-of-scope new combos: {len(out_of_scope)} {out_of_scope}")

    if not dry_run:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"WROTE {path}")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
