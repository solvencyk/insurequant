# -*- coding: utf-8 -*-
"""2026-09-01c: 시장위험 36-40 138개 결측 버킷(회사,분기) 전수 (a)/(b)/(c) 분류.

(a) MD 에 세부표 있는데 추출 실패           -> MD_HAS_HEADING
(b) MD 엔 없지만 raw PDF 엔 있음(윈도드롭)   -> PDF_HAS_HEADING_MD_DOESNT
(c) 원문(raw PDF)에도 없음(간이공시 등)      -> GENUINE_ABSENT

각 버킷에 대해 extract_mkt_subs() 를 오늘 고친 그대로 실행해 (a) 중 실제로 채울 수 있는지도
같이 판정(GATE: item19 대비 <2% 재구성).
"""
import io, json, re, sys, glob
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from fill_market_subitems_to_disclosure import (
    extract_mkt_subs, _HEADING_RISK_RE, _parse_value, _to_eok, mkt_est,
)

MD_INBOX = ROOT / "md_inbox"
DISCLOSURE = ROOT / "data" / "disclosure"

data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
idx = {}
names = {}
item19_val = {}
for r in data:
    key = (r["원보험사코드"], r["공시분기"])
    idx.setdefault(key, {})[r["항목번호"]] = r.get("값")
    names[r["원보험사코드"]] = r["원수사명"]
    if r["항목번호"] == 19:
        v = _parse_value(str(r.get("값")))
        item19_val[key] = float(v) if v is not None else None

missing = sorted(k for k in idx if idx[k].get(36) is None)
print(f"missing buckets = {len(missing)}\n")


def quarter_to_period(q):
    y, qn = q.split(".")
    qn = qn.replace("Q", "")
    return f"FY{y}_Q{qn}"


results = []
for (code, quarter) in missing:
    period = quarter_to_period(quarter)
    md_dir = MD_INBOX / period
    md_files = sorted(md_dir.glob(f"{code}_*.md")) if md_dir.is_dir() else []
    md_text = md_files[0].read_text(encoding="utf-8") if md_files else ""
    md_heading_hits = len(_HEADING_RISK_RE.findall(md_text)) if md_text else 0

    subs = extract_mkt_subs(md_text) if md_text else {}

    pdf_dir = DISCLOSURE / period / "raw"
    pdf_dir_fb = DISCLOSURE / period / "pdf"
    pdfs = sorted(glob.glob(str(pdf_dir / f"{code}_*.pdf"))) if pdf_dir.is_dir() else []
    if not pdfs and pdf_dir_fb.is_dir():
        pdfs = sorted(glob.glob(str(pdf_dir_fb / f"{code}_*.pdf")))

    pdf_heading_hits = None
    pdf_pages_with_hit = []
    if pdfs:
        try:
            import fitz
            doc = fitz.open(pdfs[0])
            pdf_heading_hits = 0
            for i in range(doc.page_count):
                t = doc[i].get_text()
                if _HEADING_RISK_RE.search(t):
                    pdf_heading_hits += 1
                    pdf_pages_with_hit.append(i + 1)
            doc.close()
        except Exception as e:
            pdf_heading_hits = f"ERROR:{e}"

    # classify
    if subs:
        v5 = [float(_to_eok(*subs[i])) if i in subs else 0.0 for i in (36, 37, 38, 39, 40)]
        est = mkt_est(v5) if any(v5) else 0.0
        item19 = item19_val.get((code, quarter))
        if item19:
            rel = abs(est - item19) / item19 * 100
        else:
            rel = None
        cls = "A_EXTRACTABLE_NOW" if (item19 and rel is not None and rel < 2) else "A_MD_HAS_DATA_BUT_GATE_FAILS"
    elif md_heading_hits > 0:
        cls = "A_MD_HAS_HEADING_NO_TABLE"
    elif not md_files:
        cls = "NO_MD_FILE"
    elif pdf_heading_hits and isinstance(pdf_heading_hits, int) and pdf_heading_hits > 0:
        cls = "B_PDF_HAS_HEADING_MD_DOESNT"
    elif not pdfs:
        cls = "C_GENUINE_ABSENT_NO_PDF_TO_CHECK"
    else:
        cls = "C_GENUINE_ABSENT"

    results.append({
        "code": code, "name": names.get(code, "?"), "quarter": quarter, "class": cls,
        "md_heading_hits": md_heading_hits, "subs_found": list(subs.keys()),
        "pdf_heading_hits": pdf_heading_hits, "pdf_pages_with_hit": pdf_pages_with_hit,
    })

from collections import Counter
cnt = Counter(r["class"] for r in results)
print("=== classification summary ===")
for k, v in cnt.most_common():
    print(f"  {k}: {v}")

print("\n=== full detail ===")
for r in results:
    print(f"  [{r['class']}] {r['name']}({r['code']}) {r['quarter']}  md_hits={r['md_heading_hits']} "
          f"subs={r['subs_found']} pdf_hits={r['pdf_heading_hits']} pdf_pages={r['pdf_pages_with_hit']}")

out_path = ROOT / "scripts" / "_probes" / "_out_20260901c_classify.json"
out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nwrote detail json: {out_path}")
