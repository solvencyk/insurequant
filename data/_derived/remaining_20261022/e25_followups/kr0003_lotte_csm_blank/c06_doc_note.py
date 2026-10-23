# -*- coding: utf-8 -*-
"""Append one sentence about the new `null_dangi` section to the top-level `_doc` of data/_gold/user_csm_cells.json (the file's own description; the PL twin documents null_dangi / set_dangi there).
Byte-exact JSON rewrite (same JsonFile helper as the applier); only the `_doc` string changes; the c02 manifest 'after_sha256' of that file is updated so --revert stays possible."""
import importlib.util
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data/_derived/remaining_20261022/e25_followups/kr0003_lotte_csm_blank"
spec = importlib.util.spec_from_file_location("ak_helpers", str(ROOT / "data/_derived/kyobo_csm_basis_fix_20261021/apply_kr0073_fix.py"))
ak = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ak)
REL = "data/_gold/user_csm_cells.json"
ADD = (" null_dangi.cells: [code, quarter, item] whose derived single-quarter 값_당분기 is forced to null while 값 (연누계) is kept -- for single quarters whose two cumulatives come from "
       "different disclosure vintages (a blank cell beats a wrong cell; build_root_masters._csm_null_dangi_keys; the CSM twin of the PL null_dangi; set_dangi is not implemented for CSM and is refused).")
f = ak.JsonFile(REL)
if ADD.strip() in f.obj["_doc"]:
    raise SystemExit("already documented")
f.obj["_doc"] = f.obj["_doc"] + ADD
new = ak.JsonFile._dump(f.obj, *f.fmt)
man_p = EV / "apply_manifest_e25_csm.json"
man = json.loads(man_p.read_text(encoding="utf-8"))
if ak.sha(f.raw) != man["after_sha256"][REL]:
    raise SystemExit("ABORT: the gold file changed since the c02 apply")
ak.write_atomic(ROOT / REL, new)
man["after_sha256"][REL] = ak.sha(new)
man["note"] = "after_sha256 of the gold file updated by c06_doc_note.py (only the top-level _doc string was extended)"
man_p.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("done; new sha", ak.sha(new)[:12])
