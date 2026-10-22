# -*- coding: utf-8 -*-
"""KR0032 restatement-note tables (수정 전 / 수정금액 / 수정 후) read independently from the raw DART XML, with line numbers."""
import re, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import KR0032_xml as X
ROOT = X.ROOT
OUT = Path(__file__).resolve().parent
NOTE_START = {"FY2024_Q4": 32411, "FY2025_Q1": 26063, "FY2025_Q2": 26373, "FY2025_Q3": 24272}
RE_TD = re.compile(r"<T[DH][^>]*>(.*?)</T[DH]>")
RE_TAG = re.compile(r"<[^>]+>")

def num(t):
    t = t.replace(",", "").replace("\u3000", " ").strip()
    if t in ("", "-"):
        return 0.0 if t == "-" else None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v

def read_note(fy):
    lines = X.load_lines(fy)
    s = NOTE_START[fy]
    assert ("재무제표 재작성" in lines[s - 1] or "(2) 포괄손익계산서" in lines[s - 1]), (fy, lines[s - 1][:80])
    out, cur_table_hdr, stop = [], None, None
    for i in range(s, min(s + 900, len(lines))):
        l = lines[i]
        if l.startswith("<P>") and i + 1 > s and re.match(r"<P>\(\d\)", l):
            stop = i + 1
            break
        if l.startswith("<TR"):
            cells, j = [], i + 1
            while j < len(lines) and not lines[j].startswith("</TR"):
                m = RE_TD.search(lines[j])
                if m:
                    cells.append((RE_TAG.sub("", m.group(1)).replace("\u3000", " ").strip(), j + 1))
                j += 1
            if cells:
                out.append(cells)
    return s, stop, out

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    res, txt = {}, []
    for fy in NOTE_START:
        s, stop, rows = read_note(fy)
        res[fy] = dict(note_start_line=s, table_end_line=stop, rows=[[(t, ln) for t, ln in r] for r in rows])
        txt.append(f"== {fy} {X.FILES[fy]} note start L{s} table end L{stop}")
        for r in rows:
            txt.append("   " + " | ".join(f"{t}@{ln}" for t, ln in r))
    (OUT / "KR0032_s1_note.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (OUT / "KR0032_s1_note.txt").write_text("\n".join(txt) + "\n", encoding="utf-8", newline="\n")
