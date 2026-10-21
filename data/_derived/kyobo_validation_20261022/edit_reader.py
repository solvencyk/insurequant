from pathlib import Path
p = Path("data/_derived/kyobo_validation_20261022/v_reread_pl.py")
s = p.read_text(encoding="utf-8")
s = s.replace('''def row(t, label, nth=0):
    hits = [r for r in t["rows"] if r["cells"] and nz(r["cells"][0]).startswith(nz(label))]
    return hits[nth] if len(hits) > nth else None''', '''def base(lbl):
    return re.sub(r"\(.*?\)", "", nz(lbl))

def row(t, label, nth=0):
    labels = label if isinstance(label, (list, tuple)) else [label]
    hits = [r for r in t["rows"] if r["cells"] and base(r["cells"][0]) in [nz(x) for x in labels]]
    return hits[nth] if len(hits) > nth else None''')
s = s.replace('out[24] = v("당기순이익")', 'out[24] = v(["당기순이익", "분기순이익", "반기순이익"])')
s = s.replace('out[31] = v("총포괄손익")', 'out[31] = v(["총포괄손익", "분기총포괄손익", "반기총포괄손익", "당기총포괄손익"])')
s = s.replace('out[1] = v("보험손익")', 'out[1] = v("보험손익")')
s = s.replace('out[20] = v("영업이익")', 'out[20] = v("영업이익")')
s = s.replace('out[22] = v("법인세차감전순이익")', 'out[22] = v(["법인세차감전순이익", "법인세비용차감전순이익"])')
s = s.replace('out[23] = v("법인세비용")', 'out[23] = v(["법인세비용", "법인세수익(비용)", "법인세비용(수익)"])')
s = s.replace('ri, l1 = v("재보험금융수익"); fe, l2 = v("보험금융비용"); re_, l3 = v("재보험금융비용"); fi, l4 = v("보험금융수익")',
              'ri, l1 = v("재보험금융수익"); fe, l2 = v("보험금융비용"); re_, l3 = v("재보험금융비용"); fi, l4 = v("보험금융수익")')
p.write_text(s, encoding="utf-8", newline="")
