"""Second pass for the cells without a row in the summary pages: scan the WHOLE pdf for the income statement rows."""
import sys, os, re, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from lib_pdf import page_rows, is_num, to_num
here = os.path.dirname(os.path.abspath(__file__))
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
prev = [r for r in csv.DictReader(open(here + "/h3_undecided.csv", encoding="utf-8-sig"))]
todo = [r for r in prev if r["verdict"] in ("NOROW", "MISMATCH")]
def lab_nums(ws):
    lab = []; nums = []
    for x0, x1, t in ws:
        if is_num(t) and (lab or x0 > 150): nums.append(to_num(t))
        elif t in ("-", "–", "—") and lab: nums.append(0.0)
        elif not nums: lab.append(t)
    return "".join(lab).replace(" ", ""), nums
def match_item(it, lab):
    if it == 1: return lab in ("보험손익", "보험서비스결과", "보험영업손익") or bool(re.fullmatch(r"[ⅠI]\.?(보험손익|보험서비스결과)", lab))
    if it == 16: return lab.endswith("기타사업비용")
    if it == 22: return bool(re.search(r"법인세(비용)?차감전", lab))
    if it == 23: return bool(re.fullmatch(r"(Ⅶ|VII|Ⅵ|VI|Ⅷ|VIII|Ⅸ|IX|\d+\.)?\.?법인세(비용|수익)?(\(.*\))?", lab)) or lab in ("법인세비용", "법인세")
    if it == 24: return bool(re.search(r"^(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVX]+\.)?(당기|분기|반기|당분기|당반기)?순(이익|손실|손익)", lab))
    return False
pdfcache = {}
out = open(here + "/h5_fullpl.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/h5_fullpl.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "quarter", "item", "master", "pdf", "page", "label", "numbers", "scale", "col", "verdict"])
cnt = {}
for r in todo:
    code, q, it = r["code"], r["quarter"], int(r["item"]); master = float(r["master(백만원)"])
    pdf = REPO + "/" + r["pdf"]
    if pdf not in pdfcache:
        doc = fitz.open(pdf)
        pdfcache[pdf] = (doc, [re.sub(r"\s+", "", doc[i].get_text()) for i in range(len(doc))])
    doc, flats = pdfcache[pdf]
    found = []
    for pn, flat in enumerate(flats, 1):
        if not (re.search(r"법인세(비용)?차감전|법인세차감전", flat) and re.search(r"순이익|순손실|순손익", flat)): continue
        if len(flat) < 300: continue
        prs = page_rows(doc, pn)
        for ri, (y, ws) in enumerate(prs):
            lab, nums = lab_nums(ws)
            if match_item(it, lab):
                if not nums and ri + 1 < len(prs):
                    lab2, nums2 = lab_nums(prs[ri + 1][1])
                    if nums2 and (lab2 == "" or lab2.startswith("(또는") or lab2.startswith("(") or lab2.startswith("또는")): nums = nums2
                if nums: found.append((pn, lab, nums))
    hit = None
    def dedupe(nums):
        if len(nums) >= 4 and len(nums) % 2 == 0 and all(nums[i] == nums[i + 1] for i in range(0, len(nums), 2)): return nums[::2]
        return nums
    found = [(pn, lab, dedupe(nums)) for pn, lab, nums in found]
    for pn, lab, nums in found:
        for sc in (1e-6, 1e-3, 1.0, 100.0):  # value*scale -> 백만원 ; 억원 prints use 100
            for ci, v in enumerate(nums[:6]):
                cand = v * sc
                if abs(cand - master) <= (60 if abs(master) >= 100 or sc == 100.0 else 0.6) or (it == 23 and abs(abs(cand) - abs(master)) <= 60):
                    hit = (pn, lab, nums, sc, ci); break
            if hit: break
        if hit: break
    if hit:
        pn, lab, nums, sc, ci = hit
        res.writerow([code, q, it, master, r["pdf"], pn, lab, nums[:6], sc, ci, "MATCH"]); cnt["MATCH"] = cnt.get("MATCH", 0) + 1
        out.write(f"{code} {q} i{it} master={master}: p{pn} {lab!r} nums={nums[:6]} scale={sc} col{ci} -> MATCH\n")
    else:
        v = "NOROW" if not found else "MISMATCH"
        res.writerow([code, q, it, master, r["pdf"], found[0][0] if found else "", found[0][1] if found else "", found[0][2][:6] if found else "", "", "", v]); cnt[v] = cnt.get(v, 0) + 1
        out.write(f"{code} {q} i{it} master={master}: {v} {found[:2]}\n")
out.write(str(cnt) + "\n")
