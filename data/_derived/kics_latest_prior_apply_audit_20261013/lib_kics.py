"""Independent K-ICS headline-table reader (20261013 audit)."""
import re, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from lib_pdf import page_rows, is_num, to_num, DASHES

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
QS = [f"{y}.{q}Q" for y in range(2022, 2028) for q in (1, 2, 3, 4)]

def qadd(q, n):
    i = QS.index(q) + n
    return QS[i] if 0 <= i < len(QS) else None

def filing_dir(fq):
    return f"{REPO}/data/disclosure/FY{fq[:4]}_Q{fq[5]}/raw"

def filing_pdfs(code, fq):
    return sorted(glob.glob(f"{filing_dir(fq)}/{code}_*.pdf"))

LABELS = [
    (12, r"불인정"), (13, r"재분류"), (6, r"보통주이외"), (5, r"^(1\.)?보통주"),
    (10, r"비지배지분"), (11, r"조정준비금"), (7, r"이익잉여금"), (8, r"자본조정"), (9, r"기타포괄손익누계액"),
    (4, r"건전성감독기준재무상태표상의순자산|^Ⅰ\.건전성감독기준"), (14, r"지급여력기준금액"), (16, r"분산효과"),
    (15, r"기본요구자본"), (17, r"생명.{0,3}장기손해보험위험액|^1\.생명장기"), (18, r"일반손해보험위험액"), (19, r"시장위험액"),
    (20, r"신용위험액"), (21, r"운영위험액"), (22, r"법인세조정액"), (23, r"기타요구자본"),
    (24, r"종속회사의요구자본환산치|^1\.업권별.*종속"), (25, r"비례성원칙"), (26, r"관계회사의요구자본환산치|^3\.업권별.*관계"),
    (27, r"지급여력비율"), (28, r"기본자본비율"),
]

def classify(label):
    s = re.sub(r"\s+", "", label)
    if not s: return None
    if s in ("기본자본", "기본자본주)", "기본자본주1)", "기본자본주2)", "기본자본주3)") or re.fullmatch(r"기본자본주?\d?\)?", s): return 2
    if re.fullmatch(r"보완자본주?\d?\)?", s): return 3
    if re.match(r"^(가\.)?지급여력금액", s) and "불인정" not in s: return 1
    for it, rx in LABELS:
        if re.search(rx, s): return it
    return None

QPATS = [
    (re.compile(r"\((?:20)?(\d\d)\.(\d)Q\)"), lambda m: f"20{m.group(1)}.{m.group(2)}Q"),
    (re.compile(r"(20\d\d)년(\d)/4분기"), lambda m: f"{m.group(1)}.{m.group(2)}Q"),
    (re.compile(r"(20\d\d)년(\d)분기"), lambda m: f"{m.group(1)}.{m.group(2)}Q"),
    (re.compile(r"\((20\d\d)년(\d+)월\)"), lambda m: f"{m.group(1)}.{(int(m.group(2)) + 2) // 3}Q"),
]

def header_quarters(rows):
    """quarters named in the header rows (rows above the first numeric row), in reading order"""
    found = []
    for y, ws in rows:
        if any(is_num(t) and x0 > 250 and len(t.replace(',', '')) >= 3 for x0, x1, t in ws if True) and found:
            break
        s = re.sub(r"\s+", "", "".join(t for _, _, t in ws))
        hits = []
        for rx, fn in QPATS:
            for m in rx.finditer(s):
                hits.append((m.start(), fn(m)))
        hits.sort()
        for _, q in hits:
            if q not in found: found.append(q)
        if len(found) >= 3: break
    return found

def cluster(centers, gap=40):
    cs = sorted(centers); groups = []
    for c in cs:
        if groups and c - groups[-1][-1] <= gap: groups[-1].append(c)
        else: groups.append([c])
    return groups

def read_page(doc, pno):
    rows = page_rows(doc, pno)
    flat = re.sub(r"\s+", "", " ".join(t for _, ws in rows for _, _, t in ws))
    if not ("지급여력금액" in flat and "건전성감독기준" in flat and "보완자본" in flat):
        # continuation page of a split table (e.g. 14~27 on next page) is detected by label census below
        if not ("지급여력기준금액" in flat and "기본요구자본" in flat): return None
    phase = "single"
    m = re.search(r"경과조치적용(전|후)", flat)
    # only trust a bracketed title like [경과조치적용전지급여력비율세부]
    m2 = re.search(r"\[경과조치적용(전|후)지급여력비율세부\]", flat)
    if m2: phase = "pre" if m2.group(1) == "전" else "post"
    nums = []
    for y, ws in rows:
        for x0, x1, t in ws:
            if (is_num(t) and len(t) >= 1) or t in DASHES:
                nums.append(((x0 + x1) / 2, t))
    # drop obvious label digits (x0 < 180 and short)
    centers = [c for c, t in nums if c > 200]
    groups = [g for g in cluster(centers) if len(g) >= 8]
    colc = [sum(g) / len(g) for g in groups]
    hq = header_quarters(rows)
    pending = ""
    items = {}
    unknown = []
    for y, ws in rows:
        lab_toks = []; val_toks = []
        for x0, x1, t in ws:
            c = (x0 + x1) / 2
            if ((is_num(t) or t in DASHES) and colc and min(abs(c - cc) for cc in colc) <= 45 and c > 200):
                val_toks.append((c, t))
            else:
                lab_toks.append(t)
        lab = " ".join(lab_toks)
        if not val_toks:
            pending = (pending + " " + lab).strip() if len(pending) < 250 else lab
            continue
        it = classify(lab)
        if it is None: it = classify((pending + " " + lab).strip())
        # row carrying values only; pending holds the label
        cols = {}
        for c, t in val_toks:
            k = min(range(len(colc)), key=lambda i: abs(colc[i] - c))
            cols.setdefault(k, t)
        if it is None:
            unknown.append(((pending + " " + lab).strip()[:60], [cols.get(k) for k in range(len(colc))]))
        elif it not in items:
            items[it] = [cols.get(k) for k in range(len(colc))]
        pending = ""
    return {"page": pno, "phase": phase, "ncols": len(colc), "hq": hq, "items": items, "unknown": unknown}

def headline_pages(pdf):
    doc = fitz.open(pdf)
    out = []
    for p in range(1, len(doc) + 1):
        try:
            pg = read_page(doc, p)
        except Exception as e:
            pg = None
        if pg and len(pg["items"]) >= 4 and pg["ncols"] >= 1:
            out.append(pg)
    doc.close()
    return out
