"""READ-ONLY: resolve residual UNMEASURED buckets from raw PDFs by reconstructing
table ROWS from fitz word boxes (y-banding), not from naive get_text() lines.

Finds pages whose text mentions 공통적용/경과조치, rebuilds rows, and reports the
기본자본 / 보완자본 / 지급여력금액 / 지급여력기준금액 rows with every numeric token so the
two-column (적용 전 | 적용 후) layout can be read by eye and by rule.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs, period_of  # noqa: E402
import fitz  # noqa: E402

SRC = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v3.json"
OUT = ROOT / "data" / "_derived" / "_probe_20260919_pdf_resolve2.json"

NUMTOK = re.compile(r"^\(?-?[\d,]+\.?\d*\)?%?$")
LABELS = ("기본자본", "보완자본", "지급여력금액", "지급여력기준금액", "지급여력비율")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def page_rows(page, band=3.0):
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    bands = defaultdict(list)
    for w in words:
        key = round(w[1] / band)
        bands[key].append(w)
    rows = []
    for key in sorted(bands):
        ws = sorted(bands[key], key=lambda w: w[0])
        rows.append([(w[4], w[0]) for w in ws])
    return rows


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    targets = [r for r in d["rows"] if r["verdict"].startswith("UNMEASURED")]
    out = []
    for r in targets:
        rec = {"code": r["code"], "name": r["name"], "q": r["q"], "TFI": r["TFI"],
               "mirrored_items": r["mirrored_items"],
               "m2": r.get("m2"), "m3": r.get("m3")}
        pdfs = disclosure_pdfs(period_of(r["q"]), r["code"])
        rec["pdfs"] = [str(p.relative_to(ROOT)).replace("\\", "/") for p in pdfs]
        if not pdfs:
            rec["status"] = "NO_PDF"
            out.append(rec)
            continue
        found = []
        total_chars = 0
        scanned_pages = 0
        for p in pdfs:
            doc = fitz.open(str(p))
            for pno in range(doc.page_count):
                page = doc[pno]
                t = page.get_text()
                total_chars += len(t)
                nt = norm(t)
                if "공통적용" not in nt and "경과조치적용후" not in nt and "경과조치적용전" not in nt:
                    continue
                scanned_pages += 1
                rows = page_rows(page)
                for row in rows:
                    joined = norm("".join(w for w, _ in row))
                    if not any(joined.startswith(L) for L in LABELS):
                        continue
                    nums = [w for w, _ in row if NUMTOK.match(w)]
                    xs = [x for w, x in row if NUMTOK.match(w)]
                    found.append({"pdf": p.name, "page": pno + 1,
                                  "row": " ".join(w for w, _ in row),
                                  "nums": nums, "x": [round(v, 1) for v in xs]})
            doc.close()
        rec["text_chars"] = total_chars
        rec["anchor_pages"] = scanned_pages
        rec["rows"] = found[:60]
        rec["n_rows"] = len(found)
        if found:
            rec["status"] = "ROWS"
        elif scanned_pages:
            rec["status"] = "ANCHOR_NO_ROWS"
        elif total_chars < 2000:
            rec["status"] = "SCANNED_OR_EMPTY_TEXTLAYER"
        else:
            rec["status"] = "NO_ANCHOR_IN_PDF"
        out.append(rec)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(Counter(x["status"] for x in out))
    for x in out:
        print(f"{x['code']} {x['q']} TFI={x['TFI']} {x['status']} rows={x.get('n_rows')} "
              f"chars={x.get('text_chars')} anchorpages={x.get('anchor_pages')}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
