"""READ-ONLY: resolve the residual UNMEASURED buckets of the 4/12/13 mirror audit
straight from the raw 정기경영공시 PDF (fitz text layer), so that 'MD keyword miss'
is never reported as 'source absent'.

For each bucket: find pages mentioning 공통적용 / 경과조치, pull the 기본자본·보완자본 line
and report every number on it, plus the surrounding lines for eyeballing.

Writes data/_derived/_probe_20260919_pdf_resolve.json + prints a digest.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs, period_of  # noqa: E402
import fitz  # noqa: E402

SRC = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v3.json"
OUT = ROOT / "data" / "_derived" / "_probe_20260919_pdf_resolve.json"

NUM = re.compile(r"-?[\d,]+\.?\d*")
ANCHOR = re.compile(r"공통\s*적용|경과조치\s*적용\s*후|적용\s*후")


def norm(s):
    return re.sub(r"\s+", "", s or "")


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    rows = [r for r in d["rows"] if r["verdict"].startswith("UNMEASURED")]
    out = []
    for r in rows:
        rec = {"code": r["code"], "name": r["name"], "q": r["q"],
               "TFI": r["TFI"], "mirrored_items": r["mirrored_items"]}
        pdfs = disclosure_pdfs(period_of(r["q"]), r["code"])
        rec["pdfs"] = [str(p.relative_to(ROOT)).replace("\\", "/") for p in pdfs]
        if not pdfs:
            rec["pdf_status"] = "NO_PDF"
            out.append(rec)
            continue
        hits = []
        for p in pdfs:
            try:
                doc = fitz.open(str(p))
            except Exception as exc:
                rec.setdefault("errors", []).append(f"{p.name}: {exc}")
                continue
            rec["pages"] = doc.page_count
            txt_chars = 0
            for pno in range(doc.page_count):
                t = doc[pno].get_text()
                txt_chars += len(t)
                if "공통적용" not in norm(t) and "경과조치" not in norm(t):
                    continue
                lines = t.splitlines()
                for i, ln in enumerate(lines):
                    n = norm(ln)
                    if n.startswith("기본자본") or n.startswith("보완자본"):
                        nums = NUM.findall(ln)
                        if len(nums) >= 1:
                            hits.append({"pdf": p.name, "page": pno + 1,
                                         "line": ln.strip(), "nums": nums,
                                         "ctx": [x.strip() for x in lines[max(0, i - 4):i + 4]]})
            rec["text_chars"] = txt_chars
            doc.close()
        rec["hits"] = hits[:40]
        rec["n_hits"] = len(hits)
        rec["pdf_status"] = "HITS" if hits else ("NO_TEXT" if rec.get("text_chars", 0) < 500
                                                 else "NO_TIER_LINE")
        out.append(rec)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(Counter(r["pdf_status"] for r in out))
    for r in out:
        print(f"{r['code']} {r['name']} {r['q']} TFI={r['TFI']} {r['pdf_status']} "
              f"hits={r.get('n_hits')} chars={r.get('text_chars')} pdfs={r['pdfs']}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
