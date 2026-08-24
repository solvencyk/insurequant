"""Read-only: marker-quality measurement for the 26 live exemption cells.

For each verify marker, classify:
  NUMERIC_ONLY   marker is a bare number/punctuation string (no Korean/Latin letters)
  LABELLED       marker contains text (row label / heading / sentence)
and measure how many pages of the cited PDF contain the marker (uniqueness).
A NUMERIC_ONLY marker that appears on many pages is a weak anchor.
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

    tot = {"NUMERIC_ONLY": 0, "LABELLED": 0}
    per_entry = []
    for reg, cells in sorted(regs.items()):
        for c, q in sorted(cells):
            e = entries.get((reg, c, q)) or {}
            ver = e.get("verify") or {}
            f = ver.get("file")
            marks = [(m, "absent") for m in (ver.get("absent_markers") or [])] + \
                    [(m, "present") for m in (ver.get("present_markers") or [])]
            if not f or not (ROOT / f).exists():
                per_entry.append((reg, c, q, "NO_VERIFY_FILE", 0, 0, []))
                continue
            doc = fitz.open(ROOT / f)
            flat = [doc[i].get_text().replace(" ", "").replace("\n", "")
                    for i in range(doc.page_count)]
            doc.close()
            num, lab, weak = 0, 0, []
            for m, kind in marks:
                cls = "LABELLED" if LETTER.search(m) else "NUMERIC_ONLY"
                tot[cls] += 1
                hits = sum(1 for t in flat if m.replace(" ", "") in t)
                if cls == "NUMERIC_ONLY":
                    num += 1
                    if hits > 1:
                        weak.append((m, hits))
                else:
                    lab += 1
            per_entry.append((reg, c, q, "ok", num, lab, weak))
    print(f"markers overall: NUMERIC_ONLY={tot['NUMERIC_ONLY']} LABELLED={tot['LABELLED']}")
    print()
    for reg, c, q, st, num, lab, weak in per_entry:
        flag = ""
        if st != "ok":
            flag = f"  <<< {st}"
        elif num and not lab:
            flag = "  <<< ALL_MARKERS_NUMERIC (no row label anchors)"
        print(f"{reg:<32} {c} {q}  numeric={num:<3} labelled={lab:<3}"
              f" non_unique_numeric={len(weak)}{flag}")
        for m, h in weak:
            print(f"      weak marker '{m}' appears on {h} pages of the cited file")


if __name__ == "__main__":
    main()
