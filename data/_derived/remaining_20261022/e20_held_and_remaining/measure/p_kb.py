"""p_kb: prototype of the Tier-2 PRIOR-column reader for KB손해보험 (KR0010) using the production handler extract_tier2_kb on the LATER filing,
steering the table choice with the later (prior-column) item 1 -- the handler's own item1-matching picks the 전기/전분기 twin.
Fidelity check: the same call on the ORIGINAL filing (item1 = original Tier-1) must reproduce the master legs.  READ-ONLY."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import fsapi as F  # noqa: E402
import prod as P  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0010"
pl, names, inames = M.load_pl()
qs = sys.argv[1].split(",") if len(sys.argv) > 1 else ["2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"]
res = {}
txt = []
cache = {}


def tabs(fy):
    if fy not in cache:
        cache.clear()
        cache[fy] = P.tables_for(CODE, fy)
    return cache[fy]


for q in qs:
    m = pl[(CODE, q)]
    t_same, _ = F.same(CODE, q)
    t_prior, _ = F.prior(CODE, q)
    # fidelity: same filing, item1 = FS-API same item1 (else master item 1)
    i1_same = (t_same or {}).get(1) if t_same else m.get(1)
    o = P.C.extract_tier2_kb(tabs(M.fy_of(q)), item1=i1_same)
    # prior: later filing, item1 = later prior item 1
    i1_prior = t_prior.get(1) if t_prior else None
    p = P.C.extract_tier2_kb(tabs(M.later_fy(q)), item1=i1_prior)
    def leg(d):
        return {"2": d.get("_jang_net"), "13": d.get(13), "14": d.get(14), "4": d.get(4), "5": d.get(5), "6": d.get(6), "9": d.get(9), "10": d.get(10), "11": d.get(11)}
    lo, lp = leg(o), leg(p)
    m_leg = {"2": m.get(2), "13": m.get(13), "14": m.get(14), "4": m.get(4), "5": m.get(5), "6": m.get(6), "9": m.get(9), "10": m.get(10), "11": m.get(11)}
    s_p = sum(v for k, v in lp.items() if k in ("2", "13", "14") and v is not None)
    s_m = sum(v for k, v in m_leg.items() if k in ("2", "13", "14") and v is not None)
    res[q] = {"item1_same": i1_same, "item1_prior": i1_prior, "same_run_legs": lo, "master_legs": m_leg, "prior_run_legs": lp,
              "sum_master": s_m, "sum_prior": s_p, "resid_prior_vs_item1_later": None if i1_prior is None else s_p - i1_prior,
              "item16_later": (t_prior or {}).get(16), "item15_later": (t_prior or {}).get(15)}
    txt.append(f"=== {q}: later filing {M.later_fy(q)}  item1 same={i1_same} prior={i1_prior}")
    txt.append(f"   master legs      {m_leg}")
    txt.append(f"   same-filing run  {lo}  (fidelity: {'OK' if all(abs((lo[k] or 0) - (m_leg[k] or 0)) < 1e-6 for k in ('2','13','14')) else 'DIFF'})")
    txt.append(f"   prior-col run    {lp}")
    txt.append(f"   sum legs: master {s_m:,.1f}  prior {s_p:,.1f}  item1_later {i1_prior}  resid(prior legs - item1_later) = {None if i1_prior is None else round(s_p - i1_prior, 3)}")
M.MEASURE.joinpath("p_kb.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("p_kb.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt))
