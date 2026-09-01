# -*- coding: utf-8 -*-
"""Full-PDF backfill of 생명장기 하위위험 (29-35) for cells the keyword-localized MD
missed (the 위험액 현황/경과조치 page wasn't near a 지급여력 keyword, e.g. 롯데손 p24).

For each (company, quarter) with item17>0 and any of 29-35 missing, scan the full
정기경영공시 PDF (pypdf text) for the 생명장기 sub-risk block (사망위험 … 대재해위험,
ending BEFORE 일반손해보험위험액) and take the 적용전/당기 (first) value per sub-risk.
Image-only / 간이공시 (no block in text) yield nothing → naturally skipped.
Gated on item17>0 (protects K3 parent-zero). UPSERT only missing items.
"""
import argparse, io, json, re, sys, logging
from pathlib import Path
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
logging.getLogger("pypdf").setLevel(logging.ERROR)
from pypdf import PdfReader

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

JSON_PATH = REPO / "kics_disclosure.json"

SUBMAP = [("사망위험", 29), ("장수위험", 30), ("장해", 31), ("장기재물", 32),
          ("해지위험", 33), ("사업비위험", 34), ("대재해", 35)]
SUBNAME = {29: "1-1. 사망위험액", 30: "1-2. 장수위험액", 31: "1-3. 장해·질병위험액",
           32: "1-4. 장기재물·기타위험액", 33: "1-5. 해지위험액", 34: "1-6. 사업비위험액",
           35: "1-7. 대재해위험액"}
NUM = re.compile(r"△?\(?-?[\d,]+(?:\.\d+)?\)?")


def _period_dir(quarter):
    y, q = quarter.split("."); return f"FY{y}_Q{q.rstrip('Q')}"


def _num(tok):
    c = tok.strip().replace(",", "")
    neg = c.startswith("△") or (c.startswith("(") and c.endswith(")"))
    c = c.strip("△()")
    if c in ("", "-"):
        return None
    if not re.fullmatch(r"-?\d+(\.\d+)?", c):
        return None
    v = float(c)
    return -v if neg else v


def _block_from_text(text):
    """Parse 생명장기 sub-risk block from a page's plain text. Returns {item:value_백만}."""
    out = {}
    in_life = False
    started = False
    for line in text.splitlines():
        nl = line.replace(" ", "")
        if re.search(r"생명.{0,2}장기.{0,4}손해보험위험", nl):
            in_life = True
            continue
        if "사망위험" in nl and not started:
            in_life = True
        if re.search(r"일반손해보험위험", nl) and started:
            break
        if not in_life:
            continue
        for key, itno in SUBMAP:
            if key in nl:
                if itno in out:
                    break
                # numbers after the label on this line; take the first (적용전/당기)
                after = line[line.find(key.split("·")[0] if "·" in key else key):] if key in line else line
                nums = [m.group(0) for m in NUM.finditer(after)]
                vals = [_num(n) for n in nums]
                vals = [v for v in vals if v is not None]
                if vals:
                    out[itno] = vals[0]
                    started = True
                break
    return out if len([i for i in out if 29 <= i <= 34]) >= 5 else {}


def _scan_pdf(pdf_path):
    try:
        rd = PdfReader(str(pdf_path))
    except Exception:
        return {}
    for i in range(len(rd.pages)):
        try:
            t = rd.pages[i].extract_text() or ""
        except Exception:
            continue
        if "사망위험" in t and "대재해" in t and ("해지위험" in t):
            blk = _block_from_text(t)
            if blk:
                return blk
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--unit", choices=["백만원", "억원"], default="백만원")
    a = ap.parse_args()
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    present = defaultdict(set); item17 = {}; meta = {}
    for r in rows:
        cq = (r.get("원보험사코드"), r.get("공시분기")); n = r.get("항목번호")
        if isinstance(n, int) and 29 <= n <= 35: present[cq].add(n)
        if n == 17:
            try: item17[cq] = float(str(r.get("값")).replace(",", ""))
            except (TypeError, ValueError): item17[cq] = None
        meta.setdefault(r.get("원보험사코드"), {k: r.get(k) for k in ("원수사명", "티커", "생손보여부")})

    resid = [(cq, set(range(29, 36)) - present.get(cq, set()))
             for cq, p in item17.items() if p and p > 0 and set(range(29, 36)) - present.get(cq, set())]
    div = 100.0 if a.unit == "백만원" else 1.0
    new = []; summ = []; scanned = 0; nofile = 0
    for (code, q), miss in sorted(resid):
        pdfs = disclosure_pdfs(_period_dir(q), code)
        if not pdfs:
            nofile += 1; continue
        scanned += 1
        blk = _scan_pdf(pdfs[0])
        if not blk:
            continue
        added = []
        for itno in sorted(miss):
            if itno in blk:
                val = round(blk[itno] / div, 2)
                val = int(val) if abs(val - round(val)) < 1e-9 else val
                m = meta.get(code, {})
                new.append({"원보험사코드": code, "원수사명": m.get("원수사명"), "티커": m.get("티커"),
                            "생손보여부": m.get("생손보여부"), "항목번호": itno, "항목명": SUBNAME[itno],
                            "공시분기": q, "값": str(val)})
                added.append(itno)
        if added:
            summ.append((code, q, added))
    print(f"residual={len(resid)} scanned_pdfs={scanned} no_pdf={nofile} "
          f"-> backfill {len(new)} rows across {len(summ)} cells")
    for code, q, added in summ:
        nm = meta.get(code, {}).get("원수사명", "?")
        print(f"  {code} {nm} {q}: +{added}")
    if a.dry_run:
        print("(dry-run)"); return
    if not new:
        print("nothing"); return
    rows.extend(new)
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (added {len(new)})")


if __name__ == "__main__":
    main()
