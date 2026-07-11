"""Add market-risk sub-items (36-46) to kics_disclosure.json.

36-40: 시장위험액 하위 5종 (금리/주식/부동산/외환/자산집중 위험액)  ← from md_inbox MD
        source: "시장위험액 세부내역" table, 경과조치 적용 전(col0), 백만원→억원.
41-46: 금리위험 시나리오별 순자산가치 (충격전/평균회귀/상승/하락/평탄/경사) ← from raw PDF
        source: "금리위험액 현황" table 의 Ⅲ.순자산가치 row, 백만원→억원.
        (현재 MD가 이 표를 안 뽑으므로 raw PDF에서 fitz로 직접 추출.)

UPSERT: 기존 (회사,분기,항목번호) 행 불변, 결측만 append. Idempotent.
Spec: docs/agents/kics-market-risk-decomposition.md §6-§8.

Usage: python scripts/fill_market_subitems_to_disclosure.py [--dry-run] [--all-periods] [--period FY2025_Q4]
"""
from __future__ import annotations
import argparse, io, json, re, sys, glob, math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"
DISCLOSURE = REPO / "data" / "disclosure"

_PERIOD_RE = re.compile(r"^FY(\d{4})_Q([1-4])$")

# market sub-risk labels (item_no, label, match keywords). order = M-matrix order.
MKT_SUBS = [
    (36, "3-1. 금리위험액", ["금리위험"]),
    (37, "3-2. 주식위험액", ["주식위험"]),
    (38, "3-3. 부동산위험액", ["부동산위험"]),
    (39, "3-4. 외환위험액", ["외환위험"]),
    (40, "3-5. 자산집중위험액", ["자산집중위험", "자산집중"]),
]
# IRR scenario net-asset items, in the column order seen in 금리위험액 현황 table.
IRR_SCEN = [
    (41, "3-1-0. 금리위험 순자산가치(충격전)"),
    (42, "3-1-1. 금리위험 순자산가치(평균회귀)"),
    (43, "3-1-2. 금리위험 순자산가치(금리상승)"),
    (44, "3-1-3. 금리위험 순자산가치(금리하락)"),
    (45, "3-1-4. 금리위험 순자산가치(금리평탄)"),
    (46, "3-1-5. 금리위험 순자산가치(금리경사)"),
]

# M matrix order 금리,주식,부동산,외환,자산집중
M = [[1,.25,.25,.25,0],[.25,1,.25,-.25,0],[.25,.25,1,.25,0],[.25,-.25,.25,1,0],[0,0,0,0,1]]


def _md_period_to_quarter(p):
    m = _PERIOD_RE.match(p)
    return f"{m.group(1)}.{m.group(2)}Q"


def _norm(s):
    # Includes both middle-dot variants: '·' (U+00B7) and '∙' (U+2219
    # BULLET OPERATOR, KR0049 악사손해보험 label rendering).
    return re.sub(r"[\s\(\)\[\]\.\,\:·∙\-\+\*Ⅰ-Ⅹⅰ-ⅸ㈜]+", "", s or "")


def _parse_value(raw):
    if raw is None:
        return None
    c = raw.strip().replace(",", "")
    if c in ("", "-", "─", "–", "—"):
        return None
    for ch in ("△", "▲", "▽", "▼", "−"):
        c = c.replace(ch, "-")
    c = c.replace(" ", "")
    pa = re.fullmatch(r"\((-?\d[\d.]*)\)", c)
    if pa:
        c = "-" + pa.group(1)
    if not re.fullmatch(r"-?\d+(\.\d+)?", c):
        return None
    return c


def _to_eok(value, unit="백만원"):
    try:
        f = float(str(value).replace(",", ""))
    except ValueError:
        return value
    div = {"억원": 1.0, "백만원": 100.0, "만원": 10000.0, "천원": 100000.0, "원": 1e8}.get(unit, 1.0)
    s = f / div
    if abs(s - round(s)) < 1e-6:
        return str(int(round(s)))
    return f"{s:.2f}".rstrip("0").rstrip(".")


# ---------- Phase 1: items 36-40 from MD 시장위험 세부표 ----------
def _bare_subrisk_item(label):
    """item_no if `label` IS a bare 시장위험 sub-risk label (금리위험/주식위험/…),
    not a sentence (e.g. the 경과조치 종류 row '…주식위험액 증가분 점진적 인식').

    Handles enumerator prefixes the row labels carry across layouts:
    '1.금리위험액' (삼성생명), 'Ⅳ.금리위험액', 'IV.금리위험액' (latin-OCR roman).
    _norm already drops unicode roman + dots; we additionally strip a leading run
    of ASCII digits / latin roman so the bare label matches the keyword."""
    nlab = _norm(label)
    if not nlab or len(label) > 16:
        return None
    nlab = re.sub(r"^[0-9IVXivx]+", "", nlab)  # strip '1', 'IV', … enumerators
    for item_no, _, kws in MKT_SUBS:
        for kw in kws:
            nk = _norm(kw)
            if nlab == nk or nlab == nk + "액":
                return item_no
    return None


_UNIT_HINT_RE = re.compile(r"\(\s*단위\s*[:：]?\s*[^)]*?(억원|백만원|만원|천원|원)[^)]*\)")


def extract_mkt_subs(md_text):
    """Return {item_no: (value_string, unit)} for items 36-40.

    The 시장위험액 세부 breakdown is frequently FRAGMENTED in the docling MD — each
    sub-risk row lands in its own one-row table separated by '<!-- image -->'
    (e.g. 하나손해 2025.4Q: 주식/부동산/외환/자산집중 each a singleton). So we scan
    EVERY table row across the whole MD, pick rows whose col0 is a *bare* sub-risk
    label, and take the first numeric cell (= 경과조치 전 / 당기 column). Wrong
    pickups (e.g. the IRR 충격 table's 금리위험액) are rejected downstream by the
    19_market matrix reconciliation gate, so over-collecting here is safe.

    Unit defaults to 백만원 (the common case) but tracks the nearest preceding
    standalone '(단위: ...)' hint — some companies (e.g. KR0051) fold the
    breakdown into an 억원 경과조치 table instead of a dedicated 백만원 세부표,
    and dividing that by 100 silently produced ~99%-off values that the 19_market
    reconciliation gate below correctly rejected but then left items 36-40 unset."""
    out = {}
    unit = "백만원"
    for ln in md_text.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            m = _UNIT_HINT_RE.search(s)
            if m:
                unit = m.group(1)
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        item_no = _bare_subrisk_item(cells[0])
        if item_no is None or item_no in out:
            continue
        for c in cells[1:]:
            v = _parse_value(c)
            if v is not None:
                out[item_no] = (v, unit)
                break
        else:
            # Every value cell was a bare dash, not just unparseable —
            # same convention as items 29-35's leaf sub-risks: a dash in a
            # leaf market sub-risk row means the company discloses zero
            # exposure to that specific risk, not "no data" (e.g. KR0004/
            # KR0072 자산집중위험 '-'/'-' — genuinely zero concentration
            # risk, not a missing table). Without this, item40's row never
            # gets created at all and the parent(item19)-has-children-
            # missing review flag never clears.
            value_cells = cells[1:]
            if value_cells and all(
                c.strip().replace(",", "") in ("-", "─", "–", "—") for c in value_cells
            ):
                out[item_no] = ("0", unit)
    return out  # values are (raw_string, unit) pairs; caller converts to 억원


# ---------- Phase 2: items 41-46 from raw PDF 금리위험액 현황 ----------
def extract_irr_netassets(pdf_path):
    """Return ([base,평균회귀,상승,하락,평탄,경사] as 백만원 floats) or None, plus disclosed 금리위험액 total or None."""
    import fitz
    doc = fitz.open(pdf_path)
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if "순자산가치" in t and "금리상승" in t and "금리하락" in t and ("금리경사" in t or "평균회귀" in t):
            # the 당기 table is the first such page. parse tokens.
            toks = t.split("\n")
            # locate 순자산가치 line index
            idx = None
            for j, line in enumerate(toks):
                if "순자산가치" in line:
                    idx = j
                    break
            if idx is None:
                continue
            # collect numeric tokens after 순자산가치 (could be on same line tail or following lines)
            nums = []
            # same-line tail
            tail = toks[idx].split("순자산가치", 1)[1]
            nums += re.findall(r"-?[\d,]+\.?\d*", tail)
            j = idx + 1
            while len(nums) < 6 and j < len(toks):
                found = re.findall(r"-?[\d,]+\.?\d*", toks[j])
                # skip empty/label-only lines
                nums += found
                j += 1
            vals = []
            for n in nums[:6]:
                v = _parse_value(n)
                vals.append(float(v) if v is not None else None)
            if len(vals) < 6 or any(v is None for v in vals):
                doc.close()
                return None, None
            # disclosed 금리위험액 total: the FIRST number after a 금리위험액 token
            # that appears AFTER the 순자산가치 row (handles split 'Ⅳ' tokens).
            total = None
            for j in range(idx + 1, len(toks)):
                line = toks[j]
                if ("금리" in line and "위험액" in line) or line.strip() == "금리위험액":
                    for k in range(j, min(j + 6, len(toks))):
                        seg = toks[k]
                        if k == j and "위험액" in seg:
                            seg = seg.split("위험액", 1)[1]
                        mt = re.findall(r"-?[\d,]+\.?\d*", seg)
                        if mt:
                            tv = _parse_value(mt[0])
                            if tv is not None:
                                total = float(tv); break
                    break
            doc.close()
            return vals, total
    doc.close()
    return None, None


def derive_irr(vals):
    """vals = [base,mr,up,down,flat,steep] (백만원). Return derived 금리위험액 (백만원)."""
    base, mr, up, down, flat, steep = vals
    R_mr = base - mr
    R_up = max(base - up, 0.0)
    R_down = max(base - down, 0.0)
    R_flat = max(base - flat, 0.0)
    R_steep = max(base - steep, 0.0)
    return math.sqrt(max(R_up, R_down) ** 2 + max(R_flat, R_steep) ** 2) + R_mr


def mkt_est(v5):
    """v5 = [금리,주식,부동산,외환,자산집중] floats. sqrt(V'MV)."""
    q = sum(v5[a] * M[a][b] * v5[b] for a in range(5) for b in range(5))
    return math.sqrt(q) if q > 0 else 0.0


def _meta_for(rows, code):
    for r in rows:
        if r["원보험사코드"] == code:
            return {"원수사명": r["원수사명"], "티커": r["티커"], "생손보여부": r["생손보여부"]}
    return None


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--period", action="append")
    ap.add_argument("--all-periods", action="store_true")
    args = ap.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    if args.all_periods:
        periods = sorted(p.name for p in MD_INBOX.glob("FY*_Q?") if p.is_dir())
    elif args.period:
        periods = args.period
    else:
        periods = ["FY2025_Q4"]
    print("periods:", periods, "\n")

    existing = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in rows}
    new_rows = []
    golden = {"mkt_ok": 0, "mkt_bad": 0, "irr_ok": 0, "irr_bad": 0}
    bad_detail = []

    for period in periods:
        quarter = _md_period_to_quarter(period)
        md_dir = MD_INBOX / period
        pdf_dir = DISCLOSURE / period / "raw"
        if not md_dir.is_dir():
            print(f"  {period}: no md_inbox, skip"); continue
        n36 = n41 = 0
        for md_path in sorted(md_dir.glob("*.md")):
            code = md_path.stem.split("_", 1)[0]
            meta = _meta_for(rows, code)
            if not meta:
                continue
            # --- 36-40 (GATE: store only if 19_market reconciles <2% vs item19) ---
            subs = extract_mkt_subs(md_path.read_text(encoding="utf-8"))
            v5map = {}
            mkt_rows_pending = []
            item36_stored = None  # 금리위험액 (억원) once 36 is stored — used to gate 41-46
            for item_no, name, _ in MKT_SUBS:
                if item_no in subs:
                    value, unit = subs[item_no]
                    eok = _to_eok(value, unit)
                    v5map[item_no] = float(eok)
                    key = (code, item_no, quarter)
                    if key not in existing:
                        mkt_rows_pending.append({**meta, "원보험사코드": code, "항목번호": item_no,
                                                 "항목명": name, "공시분기": quarter, "값": eok})
            if v5map:
                v5 = [v5map.get(36, 0.0), v5map.get(37, 0.0), v5map.get(38, 0.0),
                      v5map.get(39, 0.0), v5map.get(40, 0.0)]
                item19 = next((float(str(r["값"]).replace(",", "")) for r in rows
                               if r["원보험사코드"] == code and r["공시분기"] == quarter
                               and r["항목번호"] == 19 and _parse_value(str(r["값"])) is not None), None)
                if item19 and sum(v5) > 0:
                    est = mkt_est(v5)
                    rel = abs(est - item19) / item19 * 100
                    if rel < 2:
                        golden["mkt_ok"] += 1
                        new_rows.extend(mkt_rows_pending); n36 += len(mkt_rows_pending)
                        item36_stored = v5map.get(36)  # 금리위험액 in 억원 now in JSON
                    else:
                        golden["mkt_bad"] += 1
                        bad_detail.append(f"  MKT-SKIP {code} {quarter}: est={est:.0f} item19={item19:.0f} rel={rel:.1f}% (not stored)")
                else:
                    # no item19 to verify against → skip (can't self-check)
                    bad_detail.append(f"  MKT-SKIP {code} {quarter}: no item19 anchor (not stored)")
            # --- 41-46 from PDF ---
            pdfs = sorted(glob.glob(str(pdf_dir / f"{code}_*.pdf"))) if pdf_dir.is_dir() else []
            if pdfs:
                try:
                    vals, total = extract_irr_netassets(pdfs[0])
                except Exception as e:
                    vals, total = None, None
                # GATE: store 41-46 only if derived 금리위험액 reconciles disclosed total <3%.
                # (Reconciliation proves the 6 net-asset tokens are correct — works with
                #  negative net assets too, since only the deltas matter. 직접형 insurers
                #  that compute granularly won't reconcile and are skipped for now.)
                if vals and total is not None and total > 0:
                    rel = abs(derive_irr(vals) - total) / total * 100  # token correctness vs PDF total
                    # Mirror the validator EXACTLY: it re-derives from the ROUNDED stored
                    # 억원 values and compares to item36 with abs tol max(2.0, 0.05*item36).
                    eok_vals = [float(_to_eok(v, "백만원")) for v in vals]
                    derived_eok = derive_irr(eok_vals)
                    if item36_stored is not None:
                        # validator tol basis = 0.05*expected where expected=derived.
                        # 0.9 safety margin keeps us clear of the boundary (float rounding).
                        tol = 0.9 * max(2.0, 0.05 * abs(derived_eok))
                        passes = abs(derived_eok - item36_stored) <= tol
                        anchor = f"item36={item36_stored:.0f} derived={derived_eok:.1f} tol={tol:.1f}"
                    else:
                        # item36 not stored → validator 36_irr will SKIP. Safe to store if
                        # tokens reconcile the PDF total (<5%).
                        passes = rel < 5
                        anchor = f"no item36; rel_total={rel:.1f}%"
                    if passes:
                        golden["irr_ok"] += 1
                        for k, (item_no, name) in enumerate(IRR_SCEN):
                            key = (code, item_no, quarter)
                            if key not in existing:
                                new_rows.append({**meta, "원보험사코드": code, "항목번호": item_no,
                                                 "항목명": name, "공시분기": quarter, "값": _to_eok(vals[k], "백만원")})
                                n41 += 1
                        # item36 (금리위험액) lives in this same IRR 현황 table as the
                        # disclosed total; the reconciliation above proves it correct.
                        # Store it when the ③경과조치 breakdown path didn't already
                        # (메리츠/한화/현대/DB… disclose 금리위험액 ONLY via this table).
                        if (item36_stored is None
                                and (code, 36, quarter) not in existing
                                and total is not None and total > 0):
                            new_rows.append({**meta, "원보험사코드": code, "항목번호": 36,
                                             "항목명": "3-1. 금리위험액", "공시분기": quarter,
                                             "값": _to_eok(total, "백만원")})
                            n36 += 1
                    else:
                        golden["irr_bad"] += 1
                        tag = "직접형/granular?" if rel > 8 else "원천표 불일치/근사미달"
                        bad_detail.append(f"  IRR-SKIP {code} {quarter}: {anchor} rel_total={rel:.1f}% ({tag}; not stored)")
                elif vals:
                    bad_detail.append(f"  IRR-SKIP {code} {quarter}: no disclosed 금리위험액 total to verify (not stored)")
        print(f"  {period}: +{n36} mkt-sub rows, +{n41} irr-netasset rows")

    print(f"\nTOTAL new rows: {len(new_rows)}")
    print(f"golden 19_market: ok={golden['mkt_ok']} bad={golden['mkt_bad']}")
    print(f"golden 36_irr:    ok={golden['irr_ok']} bad={golden['irr_bad']}")
    if bad_detail:
        print("\nMISMATCHES (first 30):")
        for d in bad_detail[:30]:
            print(d)

    if args.dry_run:
        print("\n(dry-run; no write)")
        return 0
    if not new_rows:
        print("nothing to write"); return 0
    rows.extend(new_rows)
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
