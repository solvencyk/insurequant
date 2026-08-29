"""validation 2026-08-30 — same as probe_20260830_val_raw_csm_table_scan.py but for
DART filings delivered as HTML (no ACODE attributes; rows keyed by label text).

Used to read the 2026.2Q half-year report's PRIOR-HALF comparative column, which
independently restates 2025.2Q — the decisive cross-check in the KR0079
item4/item5 adjudication (inbox/validation/20260830T0400Z). Read-only.

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe       scripts/_probes/probe_20260830_val_raw_csm_html_scan.py <filing.xml> <row-label-needle>
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TABLE_RE = re.compile(r"<TABLE\b.*?</TABLE>", re.S | re.I)
TR_RE = re.compile(r"<TR\b.*?</TR>", re.S | re.I)
TD_RE = re.compile(r"<T[DH]\b([^>]*)>(.*?)</T[DH]>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")


def txt(s):
    t = TAG_RE.sub("", s or "")
    t = t.replace("&nbsp;", " ").replace("　", " ").replace("&amp;", "&")
    return " ".join(t.split())


def isnum(s):
    s = (s or "").strip()
    if s in ("", "-", "—"):
        return False
    s2 = re.sub(r"[(),\s]", "", s)
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", s2))


def num(s):
    s = (s or "").strip()
    neg = s.startswith("(") and s.endswith(")")
    v = float(re.sub(r"[(),\s]", "", s))
    return -v if neg else v


def main():
    path = Path(sys.argv[1])
    needle = sys.argv[2]
    doc = path.read_text(encoding="utf-8", errors="replace")
    n = 0
    for m in TABLE_RE.finditer(doc):
        tbl = m.group(0)
        if needle not in tbl:
            continue
        n += 1
        pre = doc[max(0, m.start() - 2000):m.start()]
        ps = [txt(p) for p in re.findall(r"<P[^>]*>(.*?)</P>", pre, re.S | re.I)]
        ps = [p for p in ps if p]
        print("=" * 100)
        print(f"[{n}] charpos={m.start()}")
        print("   CTX:", " | ".join(ps[-5:])[:400])
        for tr in TR_RE.findall(tbl):
            cells = [txt(c[1]) for c in TD_RE.findall(tr)]
            if not cells:
                continue
            labels = [c for c in cells if not isnum(c)]
            vals = [c for c in cells if isnum(c)]
            if not vals:
                print(f"   LBLROW {cells}")
                continue
            line = f"   {labels} n={len(vals)}"
            if len(vals) % 5 == 0 and len(vals) >= 5:
                ng = len(vals) // 5
                tot = sum(num(vals[g * 5 + 2]) + num(vals[g * 5 + 3]) + num(vals[g * 5 + 4]) for g in range(ng))
                line += f"  CSMsum({ng}grp)={tot/1e8:.2f}억"
            print(line)
            print(f"       vals={vals}")
    print(f"\n[tables with needle: {n}]")


if __name__ == "__main__":
    main()
