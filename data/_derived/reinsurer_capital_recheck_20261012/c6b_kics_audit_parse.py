import io, sys, glob, os, re, json
import fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OUT = "data/_derived/reinsurer_capital_recheck_20261012"
NUMTOK = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?$|^-$")
def first_val(tokens, start):
    for t in tokens[start + 1: start + 6]:
        t = t.strip()
        if NUMTOK.match(t): return t
    return "?"
res = {}
for p in sorted(glob.glob("data/disclosure/FY*/raw_aux/KR110*__kics_audit.pdf")):
    parts = p.replace(os.sep, "/").split("/")
    fy, base = parts[-3], parts[-1]
    doc = fitz.open(p)
    txt = "\n".join(doc[i].get_text("text") for i in range(min(len(doc), 25)))
    flat = re.sub(r"\s*\n\s*", " | ", txt)
    m = re.search(r"Ⅲ\s*\.\s*보완자본으로\s*재분류하는\s*항목", flat)
    if not m:
        res[f"{fy}/{base}"] = {"status": "NO_MATCH", "chars": len(txt)}
        print(fy, base, "NO_MATCH chars", len(txt)); continue
    seg = flat[m.start(): m.start() + 2600]
    tokens = [t.strip() for t in seg.split(" | ")]
    out = {"status": "OK"}
    # identify unit
    um = re.search(r"\(단위\s*:\s*([^)]+)\)", flat[max(0, m.start()-3000): m.start()])
    out["unit"] = um.group(1).strip() if um else "?"
    def grab(key, regex, occ=0):
        idxs = [i for i, t in enumerate(tokens) if re.search(regex, t)]
        out[key] = first_val(tokens, idxs[occ]) if len(idxs) > occ else "NOLABEL"
    grab("III_total", r"^Ⅲ\s*\.\s*보완자본으로")
    grab("III_1_tier1_excess", r"^1\.\s*기본자본 자본증권의 인정한도", 0)
    grab("III_2_tier2_securities", r"^2\.\s*보완자본 자본증권", 0)
    grab("III_3_lapse_excess", r"^3\.\s*해약환급금 부족분", 0)
    grab("III_4_collateral", r"^4\.\s*담보제공자산", 0)
    grab("III_5_pension_dta", r"^5\.\s*순 확정급여형", 0) if False else None
    grab("IV_basic", r"^Ⅳ\s*\.\s*기본자본")
    grab("V_supp", r"^Ⅴ\s*\.\s*보완자본")
    grab("V_1", r"^1\.\s*기본자본 자본증권의 인정한도", 1)
    grab("V_2_tier2_securities", r"^2\.\s*보완자본 자본증권", 1)
    grab("V_3_lapse_excess", r"^3\.\s*해약환급금 부족분", 1)
    grab("VI_total", r"^Ⅵ\s*\.\s*지급여력금액")
    res[f"{fy}/{base}"] = out
    print(fy, base, out)
json.dump(res, open(OUT + "/c6b_kics_audit_parse.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
