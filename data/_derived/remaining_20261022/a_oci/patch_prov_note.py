"""Guarded fix: the harness first wrote its note under the key of the earlier refresh (merge_note_20261022_kr0073_pl_refresh) and so overwrote it.
Restore that key to the git HEAD text and put this refresh's note under its own key; update apply_manifest_oci.json after_sha256 for the file."""
import importlib.util, json, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
spec = importlib.util.spec_from_file_location("ak", str(ROOT / "data/_derived/kyobo_csm_basis_fix_20261021/apply_kr0073_fix.py"))
ak = importlib.util.module_from_spec(spec); spec.loader.exec_module(ak)
HERE = Path(__file__).resolve().parent
man_p = HERE / "apply_manifest_oci.json"
man = json.loads(man_p.read_text(encoding="utf-8"))
rel = "PL_breakdown_provenance.json"
jf = ak.JsonFile(rel)
if jf.sha0 != man["after_sha256"][rel]:
    raise SystemExit("ABORT: provenance changed since the apply")
head = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True).stdout.decode("utf-8"))
OLD, NEW = "merge_note_20261022_kr0073_pl_refresh", "merge_note_20261022_kr0073_oci_refresh"
note = jf.obj[OLD]
assert NEW not in jf.obj and OLD in head
jf.obj[OLD] = head[OLD]
jf.obj[NEW] = note
# keep key order: NEW directly after OLD
items = list(jf.obj.items())
items = [kv for kv in items if kv[0] != NEW]
out = {}
for k, v in items:
    out[k] = v
    if k == OLD:
        out[NEW] = note
data = ak._dump if False else None
raw = ak.JsonFile._dump(out, *jf.fmt)
ak.write_atomic(ROOT / rel, raw)
man["after_sha256"][rel] = ak.sha(raw)
man_p.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("patched", rel, ak.sha(raw))
