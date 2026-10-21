"""Independent re-read of ALL cited raw cells in csm_vectors_raw.json (does not use xmltab.py).

For each spec/cell: reads the raw line, strips tags, compares with the stored text, walks up to the enclosing <TR> and checks the first <TD> label
against the expected row label, and checks the cell lies in the separate (SEP) notes section (after the '재무제표 주석' title) except the explicit
consolidated spec.  Then recomputes the vector (억원) from the re-read values and compares with the stored vec_eok.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
sys.stdout.reconfigure(encoding="utf-8")
vec = json.loads((EV / "csm_vectors_raw.json").read_text(encoding="utf-8"))
TAG = re.compile(r"<[^>]+>")
LABEL = {
    "open": r"^(1\. 기초 보험계약자산 및 부채|기초 보험계약순부채\(자산\)|\(2\) 기초보험계약부채)",
    "est": r"^\(1\) 보험계약마진을 조정하는 추정치의 변동분",
    "loss": r"^\(2\) 손실부담계약집합의 손실",
    "new": r"^\(3\) 최초 인식한 계약의 효과",
    "release": r"^\(1\) 서비스 이전을 반영하기 위해 당기손익으로 인식한 보험계약마진",
    "fin": r"^6\. 보험금융손익",
    "other": r"^7\. 기타",
    "close": r"^(8\. \S*말 보험계약자산 및 부채|\S*말 보험계약순부채\(자산\)|\(2\) \S*말보험계약부채)",
}
cache = {}


def lines_of(rel):
    if rel not in cache:
        cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return cache[rel]


def text(L, i):
    return re.sub(r"\s+", " ", TAG.sub("", L[i - 1]).replace("&nbsp;", " ")).strip()


def num(s):
    s = s.replace(",", "").strip()
    if s in ("-", ""):
        return 0
    neg = s.startswith("(") and s.endswith(")")
    v = int(s.strip("()"))
    return -v if neg else v


def row_label(L, i):
    j = i
    while j > 0 and "<TR" not in L[j - 1]:
        j -= 1
    k = j + 1
    while "<TD" not in L[k - 1]:
        k += 1
    return text(L, k), j


def sep_start(L):
    last = 0
    for n, ln in enumerate(L, start=1):
        if "<TITLE" in ln and re.search(r">\s*\d+\.\s*재무제표 주석", TAG.sub(">", ln) if False else ln):
            last = n
    return last


total_cells = bad = 0
for sid, spec in vec.items():
    L = lines_of(spec["file"])
    sep_title = None
    for n, ln in enumerate(L, start=1):
        if "<TITLE" in ln and re.search(r"\d+\.\s*재무제표 주석", ln) and "연결" not in ln:
            sep_title = n
    vals = {}
    spec_bad = 0
    for blk in spec["cells"]:
        for key, c in blk.items():
            total_cells += 1
            t = text(L, c["line"])
            lab, trl = row_label(L, c["line"])
            ok_txt = (t == c["txt"].strip())
            ok_lab = re.search(LABEL[key], lab) is not None
            # section: audit-report attachments have no TITLE for notes -> skip the section test when no separate title exists
            ok_sec = True if (sep_title is None or "CONS" in spec["vintage"]) else (c["line"] > sep_title)
            if not (ok_txt and ok_lab and ok_sec):
                spec_bad += 1
                bad += 1
                print(f"  !! {sid} {key} L{c['line']}: txt_ok={ok_txt} ({t!r} vs {c['txt']!r}) label_ok={ok_lab} ({lab[:40]!r}) sec_ok={ok_sec}")
            vals.setdefault(key, []).append(num(t))
    mn = {k: sum(v) for k, v in vals.items()}
    g = lambda k: mn.get(k, 0)
    gap = g("open") + g("est") + g("loss") + g("new") + g("release") + g("fin") + g("other") - g("close")
    i1, i2, i3, i5, i6 = (g("open") / 100, g("new") / 100, g("fin") / 100, g("release") / 100, g("close") / 100)
    i4 = round(i6 - i1 - i2 - i3 - i5, 2)
    mine = [round(i1, 2), round(i2, 2), round(i3, 2), i4, round(i5, 2), round(i6, 2)]
    same = all(abs(a - b) < 1e-6 for a, b in zip(mine, spec["vec_eok"]))
    print(f"{'OK ' if (spec_bad == 0 and same) else 'BAD'} {sid:36s} cells_checked={sum(len(b) for b in spec['cells']):3d} closure_gap_mn={gap:+d} vec={mine} same_as_extractor={same}")
print(f"\nTOTAL cells re-read: {total_cells}; mismatches: {bad}")
