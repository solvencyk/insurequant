"""116 PL cells (경영공시 PDF lineage) that the parser's automatic label check could not decide: own re-read of the PL summary page."""
import sys, os, re, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from lib_pdf import page_rows, is_num, to_num
here = os.path.dirname(os.path.abspath(__file__))
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
rows = [r for r in csv.DictReader(open(src + "pdf_scan_final.csv", encoding="utf-8-sig")) if r["final_class"] in ("NOLABEL", "NONE")]
SYN = {
 1: ["보험손익", "보험서비스결과", "보험영업손익"],
 16: ["기타사업비용"],
 22: ["법인세비용차감전순이익", "법인세차감전순이익", "세전이익", "법인세비용차감전이익", "법인세비용차감전당기순이익", "법인세비용차감전순손익", "법인세차감전이익", "법인세비용차감전순이익(손실)", "법인세비용차감전순이익(또는법인세비용차감전순손실)"],
 23: ["법인세비용", "법인세", "법인세비용(수익)", "법인세수익", "법인세(비용)"],
 24: ["당기순이익", "당기순손익", "분기순이익", "반기순이익", "당기순이익(손실)", "분기순이익(손실)", "반기순이익(손실)", "당기순이익(또는당기순손실)"],
}
cache = {}
def pages_rows(pdf):
    if pdf not in cache:
        doc = fitz.open(REPO + "/" + pdf)
        res = []
        for pn in range(1, min(len(doc), 14) + 1):
            res.append((pn, page_rows(doc, pn)))
        cache[pdf] = res
    return cache[pdf]
def label_and_nums(ws):
    lab = []; nums = []
    for x0, x1, t in ws:
        if is_num(t) and (x0 > 150 or lab): nums.append(to_num(t))
        elif t in ("-", "–", "—") and lab: nums.append(0.0)
        else:
            if not nums: lab.append(t)
    return "".join(lab).replace(" ", ""), nums
out = open(here + "/h3_undecided.txt", "w", encoding="utf-8")
res = csv.writer(open(here + "/h3_undecided.csv", "w", encoding="utf-8-sig", newline=""))
res.writerow(["code", "quarter", "item", "master(백만원)", "pdf", "page", "label", "numbers", "chosen(억)", "x100", "verdict"])
tot = {"MATCH": 0, "MISMATCH": 0, "NOROW": 0}
for r in rows:
    code, q, it = r["code"], r["quarter"], int(r["item"]); master = float(r["master"])
    pdf = r["pdf"]; own = r["own_filing_pdf"] == "True"
    best = None
    for pn, prs in pages_rows(pdf):
        for y, ws in prs:
            lab, nums = label_and_nums(ws)
            if not nums: continue
            hit = False
            if it == 1: hit = lab in ("보험손익", "보험서비스결과", "보험영업손익")
            elif it == 16: hit = lab == "기타사업비용"
            elif it == 22: hit = bool(re.match(r"^(법인세비용|법인세)차감전", lab))
            elif it == 23: hit = bool(re.fullmatch(r"법인세(비용|수익)?(\(.*\))?", lab))
            elif it == 24: hit = bool(re.match(r"^(당기|분기|반기|당분기|당반기)?순(이익|손실|손익)", lab))
            if hit:
                best = (pn, lab, nums)
            if best: break
        if best: break
    if not best:
        tot["NOROW"] += 1
        res.writerow([code, q, it, master, pdf, "", "", "", "", "", "NOROW"]); out.write(f"{code} {q} i{it} master={master}: NO ROW in first 14 pages of {pdf}\n"); continue
    pn, lab, nums = best
    col = 0 if own else 1
    v = nums[col] if len(nums) > col else None
    ok = v is not None and abs(v * 100 - master) <= 60
    # tax rows printed positive/negative: also accept sign flip for item 23
    if not ok and it == 23 and v is not None and abs(abs(v) * 100 - abs(master)) <= 60: ok = True
    tot["MATCH" if ok else "MISMATCH"] += 1
    res.writerow([code, q, it, master, pdf, pn, lab, nums, v, v * 100 if v is not None else "", "MATCH" if ok else "MISMATCH"])
    out.write(f"{code} {q} i{it} master={master}: p{pn} {lab!r} nums={nums[:4]} chosen={v} -> {'MATCH' if ok else 'MISMATCH'}\n")
out.write(str(tot) + "\n")
