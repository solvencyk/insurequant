# -*- coding: utf-8 -*-
"""Positional backfill of 생명장기 하위위험 (items 29-35) from the 경과조치 적용전/후
table. Fixes the systematic miss where `_is_life_catastrophe_table` dropped item35
(생명장기 대재해) because the same table also lists 일반손해 대재해, and where the
2023 date-header column picker missed the whole block.

Robust rule: within the 생명장기 block (사망위험 … 대재해위험, ending right BEFORE
'일반손해보험위험액'), map each sub-risk label to item 29-35 and take the FIRST numeric
value column (당기 / 경과조치 적용 전). Gated on item17(생명장기)>0 so it never fires for
보증/디지털 손보 with no life book (protects the K3 서울보증/카카오 parent-zero fix).
UPSERT: only fills (code, quarter, item) rows that are missing.
"""
import argparse, io, json, re, sys
from pathlib import Path
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"
_PERIOD_RE = re.compile(r"^FY(\d{4})_Q([1-4])$")

# label (normalised, in 생명장기 block order) -> item number
SUBMAP = [
    ("사망위험", 29),
    ("장수위험", 30),
    ("장해", 31),          # 장해·질병위험
    ("장기재물", 32),       # 장기재물·기타위험
    ("해지위험", 33),
    ("사업비위험", 34),
    ("대재해", 35),
]
SUBNAME = {29: "1-1. 사망위험액", 30: "1-2. 장수위험액", 31: "1-3. 장해·질병위험액",
           32: "1-4. 장기재물·기타위험액", 33: "1-5. 해지위험액", 34: "1-6. 사업비위험액",
           35: "1-7. 대재해위험액"}
LIFE_PARENT = re.compile(r"생명.{0,2}장기.{0,4}손해보험\s*위험")  # item17 parent row
GEN_PARENT = re.compile(r"일반손해보험\s*위험")                  # item18 — ends the life block


def _quarter(period):
    m = _PERIOD_RE.match(period)
    return f"{m.group(1)}.{m.group(2)}Q"


def _split(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _num(cell):
    c = cell.strip().replace(",", "")
    if c in ("", "-", "–", "—"):
        return None  # disclosed '-' = absent for that sub-risk; skip (match existing extractor)
    for ch in ("△", "▲", "▽", "▼", "−"):
        c = c.replace(ch, "-")
    m = re.fullmatch(r"\((-?\d[\d.]*)\)", c)
    if m:
        c = "-" + m.group(1)
    if not re.fullmatch(r"-?\d+(\.\d+)?", c):
        return None
    return float(c)


def _first_value(cells):
    """당기 / 경과조치 적용 전 = the column right after the label (index 1).
    '-' there → None (sub-risk absent). Taking a fixed column (not 'first numeric')
    avoids skipping a dashed 적용전 onto the 적용후 value."""
    if len(cells) < 2:
        return None
    return _num(cells[1])


def _extract_block(md_text):
    """Return {item_no: value_백만} from the FIRST 생명장기 sub-risk block found.
    A block = a contiguous run of table rows starting at/after the 생명장기 parent (or
    the first 사망위험 row) and ending at the 일반손해보험위험액 row."""
    lines = md_text.splitlines()
    # gather contiguous markdown-table blocks
    blocks, cur = [], []
    for ln in lines:
        if ln.strip().startswith("|"):
            cells = _split(ln)
            if all(set(c) <= set("-: ") for c in cells):
                continue
            cur.append(cells)
        elif cur:
            blocks.append(cur); cur = []
    if cur:
        blocks.append(cur)

    for tbl in blocks:
        labels = "".join(r[0] for r in tbl if r)
        if "사망위험" not in labels or "대재해" not in labels:
            continue
        out = {}
        in_life = False
        started = False
        for row in tbl:
            if not row:
                continue
            label = row[0]
            nl = label.replace(" ", "")
            if LIFE_PARENT.search(nl):
                in_life = True
                continue
            if "사망위험" in nl and not started:
                in_life = True
            if GEN_PARENT.search(nl) and started:
                break  # entered 일반손해 — life block done
            if not in_life:
                continue
            for key, itno in SUBMAP:
                if key in nl:
                    # 대재해: only the FIRST one (within life block) counts
                    if itno in out:
                        break
                    v = _first_value(row)
                    if v is not None:
                        out[itno] = v
                        started = True
                    break
        # require a plausible life block (>=5 of the 6 core sub-risks seen)
        if len([i for i in out if 29 <= i <= 34]) >= 5:
            return out
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--unit", choices=["백만원", "억원"], default="백만원")
    a = ap.parse_args()
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    present = defaultdict(set)
    item17 = {}
    meta = {}
    for r in rows:
        cq = (r.get("원보험사코드"), r.get("공시분기"))
        n = r.get("항목번호")
        if isinstance(n, int) and 29 <= n <= 35:
            present[cq].add(n)
        if n == 17:
            try:
                item17[cq] = float(str(r.get("값")).replace(",", ""))
            except (TypeError, ValueError):
                item17[cq] = None
        if r.get("원보험사코드") not in meta:
            meta[r.get("원보험사코드")] = {k: r.get(k) for k in
                                          ("원수사명", "티커", "생손보여부")}

    div = 100.0 if a.unit == "백만원" else 1.0
    new = []
    summary = []
    for pdir in sorted(MD_INBOX.glob("FY*_Q?")):
        q = _quarter(pdir.name)
        for f in sorted(pdir.glob("*.md")):
            code = f.stem.split("_", 1)[0]
            cq = (code, q)
            p17 = item17.get(cq)
            if not (p17 and p17 > 0):
                continue  # parent-zero / absent → never backfill (K3 guard)
            need = {n for n in range(29, 36)} - present.get(cq, set())
            if not need:
                continue
            found = _extract_block(f.read_text(encoding="utf-8", errors="replace"))
            if not found:
                continue
            added = []
            for itno in sorted(need):
                if itno in found:
                    val = found[itno] / div
                    val = round(val, 2)
                    val = int(val) if abs(val - round(val)) < 1e-9 else val
                    m = meta.get(code, {})
                    new.append({
                        "원보험사코드": code, "원수사명": m.get("원수사명"),
                        "티커": m.get("티커"), "생손보여부": m.get("생손보여부"),
                        "항목번호": itno, "항목명": SUBNAME[itno],
                        "공시분기": q, "값": str(val),
                    })
                    added.append(itno)
            if added:
                summary.append((code, q, added))

    print(f"backfill rows: {len(new)} across {len(summary)} (company,quarter)")
    for code, q, added in summary:
        nm = meta.get(code, {}).get("원수사명", "?")
        print(f"  {code} {nm} {q}: +{added}")
    if a.dry_run:
        print("(dry-run; no write)")
        return
    if not new:
        print("nothing to add")
        return
    rows.extend(new)
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (added {len(new)})")


if __name__ == "__main__":
    main()
