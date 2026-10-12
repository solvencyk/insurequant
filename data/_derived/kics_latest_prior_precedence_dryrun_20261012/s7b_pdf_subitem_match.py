"""s7b_pdf_subitem_match.py -- step 7b (READ-ONLY).  PDF-text version of the sub-item (29..46) prior-half presence / equality test.

Why PDF text and not the Docling MD: the MD drops rows of the prior-half block for some layouts (Meritz FY2023_Q4: the 직전 반기 block of the
life-risk table stops after 사망위험), so an MD-based test mistakes parse gaps for conflicts.

For each EVEN quarter Q with a later even-quarter filing F(Q+2): scan the PDF pages, keep the pages that (a) carry a sub-risk table family
keyword AND (b) carry the prior-half marker ('직전 반기' / '직전반기' / the label of Q), and collect the numbers printed on them.
    completeness evidence : which families have such a page (life / life_cat / irr / stock / realestate / fx / conc)
    equality evidence     : every non-zero master sub-item of Q (29..46) is among those numbers (+-1 in 백만원, or exact in 억원)
A master value that is NOT printed on any prior-half page of F(Q+2) is reported as UNMATCHED (conflict or reading gap -> reviewed by hand).
"""
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

utf8_stdout()
import fitz  # noqa: E402

FAM_OF = {29: "life", 30: "life", 31: "life", 32: "life", 33: "life", 34: "life", 35: "life_cat",
          36: "irr", 41: "irr", 42: "irr", 43: "irr", 44: "irr", 45: "irr", 46: "irr",
          37: "stock", 38: "realestate", 39: "fx", 40: "conc"}
NUMRE = re.compile(r"^\(?-?[\d,]+(?:\.\d+)?\)?$")
SUBCACHE = CACHE / "sub"
SUBCACHE.mkdir(parents=True, exist_ok=True)


def tok_to_num(t):
    """-> (value, printed_decimals) or None.  The decimals of the PRINTED token matter: a branch that prints 억원 integers (제네럴 etc.)
    shows 47 where the master (from the own filing's finer table) holds 46.85 -- equal at the printed precision."""
    t = t.replace(" ", "")
    if not NUMRE.match(t):
        return None
    neg = t.startswith("(") or t.startswith("-")
    t = t.strip("()").lstrip("-").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    dec = len(t.split(".")[1]) if "." in t else 0
    return (-v if neg else v), dec


def fam_flags(flat):
    f = set()
    if "사망위험" in flat and ("해지위험" in flat or "사업비위험" in flat) and "위험액" in flat:
        f.add("life")
    if "전염병" in flat and "대형사고" in flat:
        f.add("life_cat")
    if "순자산가치" in flat and "금리" in flat:
        f.add("irr")
    if "주식위험액" in flat and ("기본법" in flat or "간편법" in flat):
        f.add("stock")
    if ("부동산위험액" in flat) and ("기본법" in flat):
        f.add("realestate")
    if "외환위험액" in flat and "환율" in flat:
        f.add("fx")
    if "한도초과" in flat and "익스포져" in flat:
        f.add("conc")
    return f


def scan_pdf(period, code, q_target):
    """-> {'status', 'pdf', 'pages', 'fam': {family: [numbers]}, 'fam_pages': {family: [page]}}"""
    f = SUBCACHE / f"sub_{period}_{code}_{q_target}.json"
    if f.exists():
        return read_json(f)
    pdfs = latest_disclosure_pdfs(period, code)
    out = {"period": period, "code": code, "target": q_target, "status": None, "pdf": None, "pages_total": None, "fam": {}, "fam_pages": {}}
    if not pdfs:
        out["status"] = "NO_PDF"
        write_json_lf(f, out, indent=None)
        return out
    p = pdfs[0]
    out["pdf"] = p.relative_to(REPO).as_posix()
    y, qn = q_target[:4], q_target[5]
    lab = re.compile(r"\(\s*'?\s*(?:%s|%s)\s*\.\s*%sQ\s*\)" % (y, y[2:], qn))
    try:
        doc = fitz.open(p)
    except Exception as e:  # noqa: BLE001
        out["status"] = "OPEN_FAIL:" + str(e)[:80]
        write_json_lf(f, out, indent=None)
        return out
    out["pages_total"] = doc.page_count
    chars = 0
    famnums = defaultdict(set)
    fampages = defaultdict(list)
    prev_flagged = {}                       # page index -> families flagged on it (for the continuation rule)
    for pno in range(doc.page_count):
        page = doc[pno]
        txt = page.get_text("text")
        chars += len(txt)
        flat = re.sub(r"\s+", "", txt)
        fams = fam_flags(flat)
        has_prior = ("직전반기" in flat) or ("직전분기" in flat) or bool(lab.search(txt)) or bool(lab.search(flat))
        if fams and has_prior:
            nums = set()
            for w in page.get_text("words"):
                v = tok_to_num(w[4])
                if v is not None:
                    nums.add(v)
            for fam in fams:
                famnums[fam].update(nums)
                fampages[fam].append(pno + 1)
            prev_flagged[pno] = set(fams)
        elif not fams and (pno - 1) in prev_flagged:
            # continuation page: the table spilled onto the next page, whose own text carries no family keyword -> numbers belong to the same families
            nums = set()
            for w in page.get_text("words"):
                v = tok_to_num(w[4])
                if v is not None:
                    nums.add(v)
            for fam in prev_flagged[pno - 1]:
                famnums[fam].update(nums)
                fampages[fam].append(-(pno + 1))      # negative = continuation page (only the single page right after a flagged one)
    doc.close()
    out["chars"] = chars
    out["status"] = "OK" if chars > 400 * max(1, out["pages_total"]) // 4 else "LOW_TEXT"
    out["fam"] = {k: sorted(v) for k, v in famnums.items()}
    out["fam_pages"] = dict(fampages)
    write_json_lf(f, out, indent=None)
    return out


def matched(v, toks):
    """toks = [[number, printed_decimals], ...] found on the prior-half pages.  Equal AT THE PRINTED PRECISION counts as equal:
       백만원 integer tables   : |token - round(v*100)| <= 1
       억원 tables, 2+ decimals: |token - v| <= 0.006
       억원 tables, 1 decimal  : round(v, 1) == token  (|v| >= 1)
       억원 integer tables     : round(v) == token     (|v| >= 5)   <- coarse: reported as 'rounded' by the caller via match_kind()"""
    n100 = round(v * 100)
    av = abs(v)
    for n, d in toks:
        if d == 0 and abs(n) >= 100 and abs(n - n100) <= 1.01:
            return True
        if d >= 2 and abs(n - v) <= 0.006:
            return True
        if d == 1 and av >= 1 and abs(round(v, 1) - n) <= 0.051:
            return True
        if d == 0 and av >= 5 and abs(round(v) - n) <= 0.01:
            return True
    return False


def main():
    rows = read_rows()
    midx, names = master_index(rows)
    codes = sorted(names)
    only = [x for x in (sys.argv[sys.argv.index("--codes") + 1].split(",") if "--codes" in sys.argv else []) if x]
    res = []
    t0 = time.time()
    for code in (only or codes):
        for q in QUARTERS:
            if not is_even(q) or (code, q) not in midx:
                continue
            q2 = qadd(q, 2)
            rec = {"code": code, "name": names[code], "quarter": q, "later": q2, "pdf": None, "fam_present": [], "fam_pages": {}, "matched": [], "unmatched": [], "n_nonzero": 0, "status": None}
            if not q2:
                rec["status"] = "NO_LATER_FILING"
                res.append(rec)
                continue
            s = scan_pdf(period_of(q2), code, q)
            rec["pdf"] = s.get("pdf")
            if s["status"] not in ("OK", "LOW_TEXT"):
                rec["status"] = "UNREADABLE:" + str(s["status"])
                res.append(rec)
                continue
            if s["status"] == "LOW_TEXT":
                rec["status"] = "UNREADABLE:LOW_TEXT(scan)"
                res.append(rec)
                continue
            rec["fam_present"] = sorted(s["fam"])
            rec["fam_pages"] = s["fam_pages"]
            m = midx[(code, q)]
            for it, fam in FAM_OF.items():
                if it not in m:
                    continue
                v = num(m[it][0])
                if v is None or abs(v) < 0.005:
                    continue
                if abs(v) < 1.0:
                    # under 1억원 (< 100 백만원): the printed unit cannot be told apart from a 억원-integer table, so the value is not checkable
                    rec.setdefault("small_unverifiable", []).append(it)
                    continue
                rec["n_nonzero"] += 1
                nums = s["fam"].get(fam, [])
                if matched(v, nums):
                    rec["matched"].append(it)
                else:
                    rec["unmatched"].append({"item": it, "master": v, "family": fam, "family_page_found": fam in s["fam"]})
            rec["status"] = "NO_SUBITEMS_IN_MASTER" if rec["n_nonzero"] == 0 else ("ALL_MATCH" if not rec["unmatched"] else "SOME_UNMATCHED")
            res.append(rec)
        print(f"{code} done ({time.time()-t0:.0f}s)", flush=True)
    write_json_lf(OUT / ("subitem_match_pdf.json" if not only else "subitem_match_pdf_partial.json"), res)
    print("status counts:", dict(Counter(r["status"] for r in res)))


if __name__ == "__main__":
    main()
