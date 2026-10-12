"""HEAD vs working tree key diff for the reinsurer label standardization (read-only; uses `git show HEAD:`)."""
import csv
import io
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
NEW = [f"KR110{i}" for i in range(1, 8)]
COLS = ["원보험사코드", "원수사명", "티커", "생손보여부", "공시분기", "경과차년", "구분", "상품구분", "포트폴리오", "위험보험료", "예상보험금", "손해율",
        "원문구분", "원문포트폴리오", "세그먼트", "단위", "출처", "추출방식", "플래그"]
log = []


def P(s=""):
    log.append(s)
    print(s)


def head(path: str) -> bytes:
    return subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, check=True).stdout


h_json = head("data/loss_ratio/master_loss_ratio.json")
w_json = (ROOT / "data/loss_ratio/master_loss_ratio.json").read_bytes()
h = json.loads(h_json.decode("utf-8"))
w = json.loads(w_json.decode("utf-8"))
P(f"master JSON rows HEAD {len(h)} -> working {len(w)}  (added/deleted by count: {len(w) - len(h)})")
# key = identity of a row independent of the two standardized fields
def k_other(r):
    return tuple(json.dumps(r[c], ensure_ascii=False) for c in COLS if c not in ("세그먼트", "상품구분"))
ch, cw = Counter(k_other(r) for r in h), Counter(k_other(r) for r in w)
P(f"rows added {sum((cw - ch).values())} / deleted {sum((ch - cw).values())} (identity = all fields except 세그먼트·상품구분)")
hm = {k_other(r): r for r in h}
changed = Counter()
non_re_changed = 0
other_field_changed = 0
for r in w:
    o = hm[k_other(r)]
    fs = tuple(c for c in ("세그먼트", "상품구분") if o[c] != r[c])
    if fs:
        changed[fs] += 1
        if r["원보험사코드"] not in NEW:
            non_re_changed += 1
P(f"rows with changed fields: {dict((('+'.join(k)), v) for k, v in changed.items())}; changed rows outside KR1101~KR1107: {non_re_changed}")
hn = [r for r in h if r["원보험사코드"] not in NEW]
wn = [r for r in w if r["원보험사코드"] not in NEW]
P(f"non-reinsurer rows (36344 expected) HEAD {len(hn)} / working {len(wn)} identical (order+values): {hn == wn}")
# keys used by the panel builder: (code, quarter, segment, 구분, 상품구분, 포트폴리오, 경과차년) unique?
kk = Counter((r["원보험사코드"], r["공시분기"], r["세그먼트"], r["경과차년"], r["구분"], r["상품구분"], r["포트폴리오"]) for r in w)
P(f"working master key duplicates: {sum(1 for v in kk.values() if v > 1)}")
# CSV vs JSON
h_csv = head("data/loss_ratio/master_loss_ratio.csv").decode("utf-8-sig")
w_csv = (ROOT / "data/loss_ratio/master_loss_ratio.csv").read_bytes().decode("utf-8-sig")
rows_w = list(csv.reader(io.StringIO(w_csv, newline="")))
P(f"master CSV rows HEAD {len(list(csv.reader(io.StringIO(h_csv, newline=''))))-1} -> working {len(rows_w)-1}; header ok: {rows_w[0] == COLS}")
ok = True
for r, j in zip(rows_w[1:], w):
    for c, v in zip(COLS, r):
        if c in ("위험보험료", "예상보험금", "손해율"):
            if (None if v == "" else float(v)) != (None if j[c] is None else float(j[c])) and abs((0 if v == "" else float(v)) - (0 if j[c] is None else float(j[c]))) > 1e-9:
                ok = False
        elif (j[c] if j[c] is not None else "") != v:
            ok = False
P(f"master CSV cell-by-cell equals master JSON: {ok}")
# taxonomy
# taxonomy (CRLF in the working tree because core.autocrlf=true; the blob is LF -> compare normalized)
NL = chr(13) + chr(10)
LF = chr(10)
h_tax = head("data/loss_ratio/portfolio_taxonomy.csv").decode("utf-8-sig").replace(NL, LF).splitlines(keepends=True)
w_tax = (ROOT / "data/loss_ratio/portfolio_taxonomy.csv").read_bytes().decode("utf-8-sig").replace(NL, LF).splitlines(keepends=True)
P(f"taxonomy lines HEAD {len(h_tax)} -> working {len(w_tax)}; first 234 lines (header + 233 committed non-reinsurer rows) identical: {h_tax[:234] == w_tax[:234]}")
tail_codes = set()
for line in w_tax[234:]:
    row = next(csv.reader([line]))
    tail_codes.update(row[4].split(","))
P(f"taxonomy appended rows {len(w_tax) - 234}; company codes in them: {sorted(tail_codes)}")
for fn in ("claims_ae_ratio.json", "census.csv", "period_adoption.csv", "master_census.csv", "source_errata.csv", "panel_loss_ratio.json"):
    a = head(f"data/loss_ratio/{fn}").replace(NL.encode(), LF.encode())
    b = (ROOT / "data/loss_ratio" / fn).read_bytes().replace(NL.encode(), LF.encode())
    P(f"{fn}: identical to HEAD (line endings normalized): {a == b}")
(OUT / "head_keydiff_std.txt").write_text("\n".join(log), encoding="utf-8")
