import sys, json, io, contextlib, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
import validate_master_tables as V
_orig = pathlib.Path.write_text
pathlib.Path.write_text = lambda self, *a, **k: (len(a[0]) if self.name in ("qoq_warn.json", "pl_oci_vs_bs_aoci_warn.json") else _orig(self, *a, **k))
SC = pathlib.Path(__file__).resolve().parent / "hybrid"
def rows(path):
    V.WF_PATH = path
    wf = V.load_long(path)
    with contextlib.redirect_stdout(io.StringIO()):
        r = V._check_qoq_warn(wf)
    return {(c, q, it): (round(d*100,1), round(a,1), round(b,1)) for c, q, it, d, t, a, b, bs in r}
new = rows("CSM_waterfall.json"); old = rows(str(SC / "CSM_waterfall.json"))
print("old(hybrid=pre-commit KR0073)", len(old), "new", len(new))
print("gone:", sorted(k for k in old if k not in new))
print("appeared:", sorted(k for k in new if k not in old))
print("changed value:", sorted((k, old[k], new[k]) for k in new if k in old and old[k] != new[k])[:10])
