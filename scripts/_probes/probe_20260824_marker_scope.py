"""Read-only: measure marker occurrences WITHIN the pages the gate actually opens.

The gate concatenates the cited pages and does a whitespace-stripped substring test.
A bare-number present_marker therefore proves "this number appears somewhere in the
cited pages", not "this row prints this value".  This probe counts occurrences.
Nothing is written.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_kics_disclosure as V  # noqa: E402

LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"
LETTER = re.compile(r"[A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ]")


def main():
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = {(e.get("registry"), e.get("company"), e.get("quarter")): e
               for e in led.get("entries") or []}
    regs = V._exemption_registries()
    import fitz

    n_numeric = n_lab = 0
    n_multi = 0
    rows = []
    for reg, cells in sorted(regs.items()):
        for c, q in sorted(cells):
            e = entries.get((reg, c, q)) or {}
            ver = e.get("verify") or {}
            f = ver.get("file")
            if not f or not (ROOT / f).exists():
                rows.append((reg, c, q, "NO_VERIFY", []))
                continue
            pages = ver.get("pages")
            doc = fitz.open(ROOT / f)
            idx = [n - 1 for n in pages] if pages else range(doc.page_count)
            text = "".join(doc[n].get_text() for n in idx if 0 <= n < doc.page_count)
            doc.close()
            flat = text.replace(" ", "").replace("\n", "")
            det = []
            for kind in ("absent_markers", "present_markers"):
                for m in (ver.get(kind) or []):
                    mm = m.replace(" ", "")
                    cnt = flat.count(mm)
                    cls = "LABELLED" if LETTER.search(m) else "NUMERIC"
                    if cls == "NUMERIC":
                        n_numeric += 1
                        if cnt > 1:
                            n_multi += 1
                    else:
                        n_lab += 1
                    det.append((kind, cls, m, cnt))
            rows.append((reg, c, q, f"pages={pages}", det))
    print(f"markers in scope: NUMERIC={n_numeric} LABELLED={n_lab} "
          f"NUMERIC appearing >1x inside cited pages = {n_multi}")
    print()
    for reg, c, q, st, det in rows:
        multi = [d for d in det if d[1] == "NUMERIC" and d[3] > 1]
        zero = [d for d in det if d[3] == 0 and d[0] == "present_markers"]
        print(f"{reg:<32} {c} {q} {st}  markers={len(det)} "
              f"numeric_multi={len(multi)} present_missing={len(zero)}")
        for d in multi:
            print(f"      NUMERIC '{d[2]}' occurs {d[3]}x within cited pages")
        for d in zero:
            print(f"      !! present_marker '{d[2]}' NOT FOUND")


if __name__ == "__main__":
    main()
