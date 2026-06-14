"""Extract K-ICS 지급여력 금리민감도 (rate-sensitivity) from md_inbox -> master + diag.

Source: 경영공시 `금리 민감도 분석` table (2-key matrix: 경과조치 적용전/후 x measure
{지급여력비율/금액/기준금액} x {base, -100bp, -50bp, +50bp, +100bp}).
Spec (정본): docs/agents/kics-rate-sensitivity-spec.md.

Self-validation built in (RS1): 비율[c] ≈ 금액[c] / 기준금액[c] x 100 for every shock
column c. Tables are parsed absolute-first; if RS1 fails, re-interpreted as delta
(absolute = base + cell, 흥국 계열) and re-checked. Per-(사,분기) status -> diag.

Usage: PYTHONIOENCODING=utf-8 python scripts/extract_kics_rate_sensitivity.py [--dry-run]
"""
from __future__ import annotations
import argparse, io, json, re, sys, glob
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
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
    amended = [h for h in hits if "_amended" in h]
    pool = amended or hits
    return max(pool, key=lambda h: Path(h).stat().st_size)


def find_section_table(md_text):
    """Return the markdown table (list of | rows) under the 금리 민감도 분석 heading."""
    lines = md_text.splitlines()
    for i, ln in enumerate(lines):
        if not ln.lstrip().startswith("#"):
            continue
        h = norm(ln)
        if "금리" in h and "민감도" in h and "분석" in h and not any(
                bad in h for bad in ("환율", "보험위험", "가정", "개요", "방법")):
            # collect ALL pipe-rows until the next heading — Docling sometimes splits
            # one table across a blank line, so don't stop at the first gap.
            tbl = []
            for ln2 in lines[i + 1:]:
                s = ln2.lstrip()
                if s.startswith("#"):
                    break  # next section
                if s.startswith("|"):
                    tbl.append(ln2)
            if tbl:
                return tbl
    return None


def match_measure(label):
    """Canonical measure for a label cell, tolerating 지금/지급 typo and OCR spacing."""
    n = norm(label).replace("지금여력", "지급여력")
    if "여력기준금액" in n:
        return "지급여력기준금액"
    if "여력비율" in n:
        return "지급여력비율"
    if "여력금액" in n:
        return "지급여력금액"
    return None


def measure_rows(tbl):
    """Rows whose measure cell (col1) maps to a measure -> (col0frag, measure, [5 vals])."""
    out = []
    for ln in tbl:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        m = match_measure(cells[1])
        if m:
            vals = [parse_value(c) for c in cells[2:7]]
            out.append((cells[0], m, vals))
    return out


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
    """{measure: [5 vals]}; None if block is entirely empty (all-dash)."""
    d = {}
    any_val = False
    for _frag, m, vals in block:
        d[m] = vals
        if any(v is not None for v in vals):
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


def emit_rows(meta, quarter, phase, d):
    rows = []
    for m, vals in d.items():
        rows.append({
            **meta, "공시분기": quarter, "경과조치여부": phase, "measure구분": m,
            "-100bp": vals[1], "-50bp": vals[2], "base": vals[0],
            "+50bp": vals[3], "+100bp": vals[4],
        })
    return rows


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

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

    periods = sorted(p.name for p in MD_INBOX.glob("FY*_Q*") if p.is_dir())
    out_rows, diag = [], {}
    stats = {}

    for period in periods:
        quarter = period_to_quarter(period)
        for code in sorted(prefix):
            md = pick_md(code, period)
            key = f"{code}|{quarter}"
            if md is None:
                continue  # company didn't file that quarter
            tbl = find_section_table(Path(md).read_text(encoding="utf-8"))
            if not tbl:
                # absent section: normal pre-format, or a flagged suspect
                if (code, quarter) in SUSPECTS or (code, None) in SUSPECTS:
                    diag[key] = "suspect_truncation"
                    stats["suspect_truncation"] = stats.get("suspect_truncation", 0) + 1
                else:
                    diag[key] = "absent_section"
                continue
            rows = measure_rows(tbl)
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
            for ph, d in uniq:
                if d is None:  # all-dash block
                    if ph == "적용후":
                        post_dash = True
                    continue
                rd, enc = resolve_block(d)
                encs.add(enc)
                if ph == "적용전":
                    pre_base = {m: v[0] for m, v in rd.items()}
                out_rows.extend(emit_rows(prefix[code], quarter, ph, rd))
                emitted += len(rd)

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

    if args.dry_run:
        print("\n(dry-run; no write)")
        return 0
    OUT_JSON.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    DIAG_JSON.write_text(json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON.name} ({len(out_rows)} rows) + {DIAG_JSON.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
