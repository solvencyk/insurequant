"""READ-ONLY 전수 audit v4 — item 4/12/13 `값_적용후` mirror (backfill_post_transition_when_not_applied).

Five independent axes per (company, quarter) bucket that carries a 값_적용후 on 4/12/13:

  A  MD, golden extractor  scripts/fill_post_transition_to_disclosure._extract_post_values
     (the same code path that produced the master's own item1/2/3/14/27 적용후)
  B  MD, tolerant fallback scan for docling-mangled headers ("적용 전 경과조치 | 적용 후")
  C  data/_derived/kics_transition_applicability.json  TFI = O/X/NA/UNKNOWN
  D  master-internal: item2/item3 값 vs 값_적용후 (our own disclosed tier pair)
  E  raw PDF (fitz word boxes, y-banded rows) — so an MD keyword miss is never
     reported as 'source absent'

Verdict precedence: a directly read 공통적용 2-column tier pair (A>B>E) wins; then D;
then C(X/NA) / explicit MD negation; otherwise UNMEASURED (reported per cell).

Writes data/_derived/_probe_20260919_mirror_audit_v4.json and a CSV table.
No mutation of any master. No build. No network.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fill_post_transition_to_disclosure as FP  # noqa: E402
from _disclosure_pdf_paths import disclosure_pdfs, period_of  # noqa: E402
import fitz  # noqa: E402

OUT = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v4.json"
OUT_CSV = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v4.csv"
APPLIC = ROOT / "data" / "_derived" / "kics_transition_applicability.json"

K_CODE, K_NAME, K_ITEM, K_Q, K_V, K_VA = (
    "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후")
TARGET_ITEMS = (4, 12, 13)
TOL = 0.01

APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})

NUMTOK = re.compile(r"^\(?-?[\d,]+\.?\d*\)?%?$")
PDF_LABELS = ("기본자본", "보완자본", "지급여력금액", "지급여력기준금액", "지급여력비율")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").replace("%", "").strip()
    if s in ("", "-", "ㅡ", "–", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------- axis B
def fallback_scan(text):
    lines = text.splitlines()
    anchors = [i for i, ln in enumerate(lines) if "공통적용" in norm(ln)]
    cands = []
    for a in anchors:
        for j in range(a, min(len(lines), a + 30)):
            if lines[j].lstrip().startswith("|"):
                cands.append(j)
                break
    if not cands:
        for i, ln in enumerate(lines):
            if ln.lstrip().startswith("|") and "적용전" in norm(ln) and "적용후" in norm(ln):
                cands.append(i)
    for hdr in cands:
        cols = [c.strip() for c in lines[hdr].strip().strip("|").split("|")]
        pre_i = post_i = None
        for k, c in enumerate(cols):
            cn = norm(c)
            if pre_i is None and cn.endswith("적용전"):
                pre_i = k
            if post_i is None and (cn.endswith("적용후") or cn == "적용후"):
                post_i = k
        if pre_i is None or post_i is None or pre_i == post_i:
            continue
        out, j = {}, hdr + 1
        if j < len(lines) and set(lines[j].replace("|", "").replace(" ", "")) <= set("-:"):
            j += 1
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
            lbl = norm(cells[0]) if cells else ""
            ax = None
            if lbl.startswith("기본자본") and "요구자본" not in lbl:
                ax = "tier1"
            elif lbl.startswith("보완자본") and "한도" not in lbl:
                ax = "tier2"
            if ax and ax not in out and max(pre_i, post_i) < len(cells):
                pr, po = cells[pre_i], cells[post_i]
                if num(pr) is None and len(pr.split()) == 2:
                    pr, po = pr.split()
                elif po == "" and len(pr.split()) == 2:
                    pr, po = pr.split()
                out[ax] = (num(pr), num(po), cells[0], j + 1, po)
            j += 1
        if out:
            out["_hdr_line"] = hdr + 1
            return out
    return None


# ---------------------------------------------------------------- axis E
def pdf_scan(code, quarter):
    res = {"pdfs": [], "rows": [], "text_chars": 0, "anchor_pages": 0}
    for p in disclosure_pdfs(period_of(quarter), code):
        res["pdfs"].append(str(p.relative_to(ROOT)).replace("\\", "/"))
        try:
            doc = fitz.open(str(p))
        except Exception as exc:
            res.setdefault("errors", []).append(str(exc))
            continue
        for pno in range(doc.page_count):
            page = doc[pno]
            t = page.get_text()
            res["text_chars"] += len(t)
            nt = norm(t)
            if "공통적용" not in nt and "경과조치적용후" not in nt:
                continue
            res["anchor_pages"] += 1
            words = page.get_text("words")
            bands = defaultdict(list)
            for w in words:
                bands[round(w[1] / 3.0)].append(w)
            for key in sorted(bands):
                ws = sorted(bands[key], key=lambda w: w[0])
                joined = norm("".join(w[4] for w in ws))
                if not any(joined.startswith(L) for L in PDF_LABELS):
                    continue
                toks = [(w[4], w[0]) for w in ws if NUMTOK.match(w[4])]
                res["rows"].append({"pdf": p.name, "page": pno + 1,
                                    "row": " ".join(w[4] for w in ws),
                                    "nums": [t0 for t0, _ in toks],
                                    "x": [round(x, 1) for _, x in toks]})
        doc.close()
    return res


def pdf_tier_pair(scan):
    """From the PDF rows pick the 공통적용 2-col (pre, post) for 기본자본/보완자본.
    A 공통적용 row has exactly two numeric tokens and its page also holds a
    지급여력금액 row with two numeric tokens (the 세부표 has three: 당/직전/전전분기)."""
    bypage = defaultdict(list)
    for r in scan["rows"]:
        bypage[(r["pdf"], r["page"])].append(r)
    best = None
    for key, rs in bypage.items():
        two = {}
        for r in rs:
            j = norm(r["row"])
            n = r["nums"]
            if len(n) != 2:
                continue
            if j.startswith("기본자본") and "요구자본" not in j:
                two.setdefault("tier1", (num(n[0]), num(n[1]), r["row"], r["page"]))
            elif j.startswith("보완자본") and "한도" not in j:
                two.setdefault("tier2", (num(n[0]), num(n[1]), r["row"], r["page"]))
            elif j.startswith("지급여력금액"):
                two.setdefault("amount", (num(n[0]), num(n[1]), r["row"], r["page"]))
        if ("tier1" in two or "tier2" in two) and "amount" in two:
            if best is None or len(two) > len(best):
                best = two
    return best


def main():
    data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    midx = {}
    for r in data:
        midx.setdefault((r.get(K_CODE), r.get(K_Q)), {})[r.get(K_ITEM)] = r

    app = {(r["code"], r["quarter"]): r
           for r in json.loads(APPLIC.read_text(encoding="utf-8"))["records"]}

    mdmap = {}
    for pdir in sorted(FP.MD_INBOX.glob("FY*_Q?")):
        if pdir.is_dir():
            q = FP._md_period_to_quarter(pdir.name)
            for md in sorted(pdir.glob("*.md")):
                mdmap[(md.stem.split("_", 1)[0], q)] = md

    rows = []
    for (code, q), items in sorted(midx.items()):
        hit = [n for n in TARGET_ITEMS
               if items.get(n) and items[n].get(K_VA) not in (None, "")]
        if not hit:
            continue
        name = next((items[n].get(K_NAME) for n in items if items[n].get(K_NAME)), code)
        rec = {"code": code, "name": name, "q": q, "mirrored_items": sorted(hit),
               "elective_applier": code in APPLIERS}
        for n in (1, 2, 3, 4, 12, 13, 14, 27, 28):
            row = items.get(n)
            rec[f"m{n}"] = [row.get(K_V), row.get(K_VA)] if row else None

        a = app.get((code, q))
        rec["TFI"] = a.get("TFI") if a else "NO_RECORD"

        md = mdmap.get((code, q))
        rec["md"] = str(md.relative_to(ROOT)).replace("\\", "/") if md else None
        got, fb = {}, None
        if md:
            text = md.read_text(encoding="utf-8", errors="replace")
            nt = norm(text)
            rec["md_negation"] = ("공통적용경과조치를적용하지않아" in nt
                                  or "공통적용경과조치관련:해당사항없음" in nt
                                  or "공통적용경과조치관련:해당없음" in nt)
            try:
                got, _pv, _d, _u = FP._extract_post_values(
                    FP._scan_tables_with_context(text), code,
                    {it: r0.get(K_V) for it, r0 in items.items()})
            except Exception as exc:
                rec["extractor_error"] = f"{type(exc).__name__}: {exc}"
            fb = fallback_scan(text)

        def dd(pair):
            if not pair:
                return None
            x, y = num(pair[0]), num(pair[1])
            return None if (x is None or y is None) else round(y - x, 4)

        src, delta, ev = None, None, None
        if dd(got.get(2)) is not None or dd(got.get(3)) is not None:
            src = "A(MD golden)"
            d2, d3 = dd(got.get(2)), dd(got.get(3))
            delta = d2 if d2 is not None else (-d3 if d3 is not None else None)
            ev = {"item2": got.get(2), "item3": got.get(3), "md": rec["md"]}
        elif fb and (fb.get("tier1") or fb.get("tier2")):
            t1, t2 = fb.get("tier1"), fb.get("tier2")
            d2 = None if not t1 or t1[0] is None or t1[1] is None else round(t1[1] - t1[0], 4)
            d3 = None if not t2 or t2[0] is None or t2[1] is None else round(t2[1] - t2[0], 4)
            if d2 is not None or d3 is not None:
                src = "B(MD fallback)"
                delta = d2 if d2 is not None else -d3
                ev = {"tier1": t1, "tier2": t2, "md": rec["md"],
                      "hdr_line": fb.get("_hdr_line")}
        if src is None:
            scan = pdf_scan(code, q)
            rec["pdf_text_chars"] = scan["text_chars"]
            rec["pdf_anchor_pages"] = scan["anchor_pages"]
            rec["pdfs"] = scan["pdfs"]
            pair = pdf_tier_pair(scan)
            if pair:
                t1, t2 = pair.get("tier1"), pair.get("tier2")
                d2 = None if not t1 else (None if t1[0] is None or t1[1] is None
                                          else round(t1[1] - t1[0], 4))
                d3 = None if not t2 else (None if t2[0] is None or t2[1] is None
                                          else round(t2[1] - t2[0], 4))
                if d2 is not None or d3 is not None:
                    src = "E(raw PDF)"
                    delta = d2 if d2 is not None else -d3
                    ev = {"tier1": t1, "tier2": t2, "pdfs": scan["pdfs"]}
        if src is None:
            d2m = dd(rec.get("m2"))
            d3m = dd(rec.get("m3"))
            if (d2m is not None and abs(d2m) > TOL) or (d3m is not None and abs(d3m) > TOL):
                src = "D(master item2/3)"
                delta = d2m if d2m is not None else -d3m
                ev = {"m2": rec.get("m2"), "m3": rec.get("m3")}

        rec["tier_src"] = src
        rec["tier_delta"] = delta
        rec["tier_evidence"] = ev

        if src and delta is not None and abs(delta) > TOL:
            rec["verdict"] = "CONTAMINATED"
        elif src and delta is not None:
            rec["verdict"] = "BENIGN_TIER_EQUAL"
        elif rec["TFI"] in ("X", "NA") or rec.get("md_negation"):
            rec["verdict"] = "BENIGN_TFI_NOT_APPLIED"
        else:
            rec["verdict"] = ("UNMEASURED_TFI_O" if rec["TFI"] == "O"
                              else "UNMEASURED_TFI_UNKNOWN")

        # identity residual on both columns (item2 = item4 - item12 - item13)
        def mv(n, col):
            p = rec.get(f"m{n}")
            return num(p[col]) if p else None
        for col, tag in ((0, "pre"), (1, "post")):
            i4, i12, i13, i2 = mv(4, col), mv(12, col), mv(13, col), mv(2, col)
            if None not in (i4, i12, i13, i2):
                rec[f"identity_{tag}_resid"] = round(i4 - i12 - i13 - i2, 3)
        rows.append(rec)

    counts, cells = {}, {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        cells[r["verdict"]] = cells.get(r["verdict"], 0) + len(r["mirrored_items"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "buckets": len(rows), "cells": sum(len(r["mirrored_items"]) for r in rows),
        "verdict_buckets": counts, "verdict_cells": cells, "rows": rows,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["code", "name", "quarter", "item", "label_short", "mirror_value(값_적용후)",
                    "pre_value(값)", "verdict", "tier_delta(억원)", "tier_src", "TFI",
                    "identity_pre_resid", "identity_post_resid", "direction"])
        lab = {4: "Ⅰ순자산", 12: "Ⅱ불인정", 13: "Ⅲ보완자본재분류"}
        for r in rows:
            for it in r["mirrored_items"]:
                pair = r.get(f"m{it}") or [None, None]
                if r["verdict"] == "CONTAMINATED":
                    d = r["tier_delta"]
                    direction = (f"미러링 triple 이 item2_적용후와 {d:+.2f}억원 불일치; "
                                 f"Ⅲ(재분류) 과대 -> 파생 기본자본 과소")
                else:
                    direction = ""
                w.writerow([r["code"], r["name"], r["q"], it, lab.get(it, ""),
                            pair[1], pair[0], r["verdict"], r["tier_delta"],
                            r["tier_src"], r["TFI"],
                            r.get("identity_pre_resid"), r.get("identity_post_resid"),
                            direction])

    print("buckets:", len(rows), "cells:", sum(len(r['mirrored_items']) for r in rows))
    print("verdict buckets:", json.dumps(counts, ensure_ascii=False))
    print("verdict cells:  ", json.dumps(cells, ensure_ascii=False))
    print("wrote", OUT)
    print("wrote", OUT_CSV)


if __name__ == "__main__":
    main()
