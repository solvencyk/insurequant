"""Independent re-read of every raw cell behind the applied 2026.1Q values (does not use xmltab.py / the extractor).

For each cited cell line L it reads the raw line, strips tags, walks upward to the <TR ...> that encloses it, reads the first <TD> text of that row
(the row label) and checks the label against the expected row.  Then it recomputes the 별도 sums and the closing identity from scratch.
"""
import re
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
F = ROOT / "data/dart/FY2026_Q1/raw/KR0073_교보생명보험/xml/20260813001077.xml"
lines = F.read_text(encoding="utf-8", errors="replace").split("\n")
TAG = re.compile(r"<[^>]+>")

# (row key, expected label regex, [line of the 유배당, 무배당, 변액 cell])
CELLS = {
    "open":    (r"^1\. 기초 보험계약자산 및 부채", [43661, 43978, 44295]),
    "est":     (r"^\(1\) 보험계약마진을 조정하는 추정치의 변동분", [43716, 44033, 44350]),
    "new":     (r"^\(3\) 최초 인식한 계약의 효과", [43738, 44055, 44372]),
    "release": (r"^\(1\) 서비스 이전을 반영하기 위해 당기손익으로 인식한 보험계약마진", [43760, 44077, 44394]),
    "fin":     (r"^6\. 보험금융손익", [43848, 44165, 44482]),
    "other":   (r"^7\. 기타", [43881, 44198, 44515]),
    "close":   (r"^8\. 기말 보험계약자산 및 부채", [43892, 44209, 44526]),
}


def text(i):
    return re.sub(r"\s+", " ", TAG.sub("", lines[i - 1])).strip()


def num(s):
    s = s.replace(",", "").strip()
    if s in ("-", ""):
        return 0
    neg = s.startswith("(") and s.endswith(")")
    v = int(s.strip("()"))
    return -v if neg else v


def row_label(i):
    j = i
    while j > 0 and "<TR" not in lines[j - 1]:
        j -= 1
    k = j + 1
    while "<TD" not in lines[k - 1]:
        k += 1
    return text(k), j


sums, ok = {}, True
for key, (rx, ls) in CELLS.items():
    vals = []
    for L in ls:
        lab, trl = row_label(L)
        # the section header (SEP-NOTES) guard: cell must be after the separate-notes title line
        assert L > 34793, "cell is inside the consolidated notes"
        good = re.search(rx, lab) is not None
        ok &= good
        vals.append(num(text(L)))
        print(f"  {key:8s} L{L}: {text(L):>12s}  row@L{trl}: {lab[:50]!r}  label_ok={good}")
    sums[key] = sum(vals)
print()
print("sums (백만원):", sums)
gap = sums["open"] + sums["est"] + sums["new"] + sums["release"] + sums["fin"] + sums["other"] - sums["close"]
print("closing identity gap (open+est+new+release+fin+other-close) =", gap, "백만원 (3 sub-tables, +-1 rounding allowed)")
e5 = {
    "I1_raw": sums["open"] / 100, "I2": sums["new"] / 100, "I3": sums["fin"] / 100, "I5": sums["release"] / 100, "I6": sums["close"] / 100,
    "est_row": (sums["est"] + sums["other"]) / 100,
}
print({k: round(v, 2) for k, v in e5.items()})
I1 = 65109.6
I4 = round(e5["I6"] - I1 - e5["I2"] - e5["I3"] - e5["I5"], 2)
print("I4 residual with I1=65109.6:", I4, "| printed 추정치 변동 (est+other):", round(e5["est_row"], 2))
master = {2: 4159.16, 3: 487.2, 4: -1349.13, 5: -1537.33, 6: 66869.5}
chk = {2: round(e5["I2"], 2), 3: round(e5["I3"], 2), 4: I4, 5: round(e5["I5"], 2), 6: round(e5["I6"], 2)}
print("applied master values:", master)
print("recomputed values    :", chk)
print("ALL MATCH:", master == chk and ok)
