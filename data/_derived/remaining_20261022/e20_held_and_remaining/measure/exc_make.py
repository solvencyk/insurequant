"""exc_make: build a SANDBOX variant of the two gates that read WFY_EXCEPTIONS (validate_master_tables.py, validate_csm_continuity.py) in which two extra documented-restatement entries
are registered: ("KB라이프생명", "2023") and ("롯데손해보험", "2023").  Nothing in the repo is written; the copies live in exc_sandbox/ of this folder.
Used only to simulate 'option A / adopt 롯데 2023.4Q + register the WFY exemption' (decision tables D1/D2).  Run once; then use run_gates_exc.sh <scenario>."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
SB = HERE / "exc_sandbox"
SB.mkdir(exist_ok=True)

mt = (ROOT / "scripts" / "validate_master_tables.py").read_text(encoding="utf-8")
n0 = len(mt)
mt = mt.replace("ROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(Path(__file__).resolve().parent))",
                'ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")\nsys.path.insert(0, str(ROOT / "scripts"))', 1)
assert 'ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")' in mt, "ROOT patch failed"
mt = mt.replace("    here = str(Path(__file__).resolve().parent)\n", '    here = str(ROOT / "scripts")\n', 1)
assert 'here = str(ROOT / "scripts")' in mt, "here patch failed"
old = '    ("메리츠화재해상보험", "2023"), ("에이비엘생명보험", "2023"),\n}'
assert old in mt, "WFY_EXCEPTIONS tail not found"
mt = mt.replace(old, '    ("메리츠화재해상보험", "2023"), ("에이비엘생명보험", "2023"),\n    ("KB라이프생명", "2023"), ("롯데손해보험", "2023"),   # SANDBOX ADDITION (e20 simulation only)\n}', 1)
assert "__file__" not in re.sub(r"#.*", "", mt.replace('Path(__file__)', 'X')) or True
(SB / "validate_master_tables.py").write_text(mt, encoding="utf-8", newline="\n")

cc = (ROOT / "scripts" / "validate_csm_continuity.py").read_text(encoding="utf-8")
cc = cc.replace('ROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "scripts"))',
                'ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")\nsys.path.insert(0, str(ROOT / "scripts"))\nsys.path.insert(0, "' + str(SB).replace("\\", "/") + '")', 1)
assert 'sys.path.insert(0, "' in cc, "continuity patch failed"
(SB / "validate_csm_continuity.py").write_text(cc, encoding="utf-8", newline="\n")

go = (HERE / "gate_overlay.py").read_text(encoding="utf-8")
go = go.replace('"master_tables": ("validate_master_tables.py", ["--no-build"]),', '"master_tables": ("exc_sandbox/validate_master_tables.py", ["--no-build"]),', 1)
go = go.replace('"csm_continuity": ("validate_csm_continuity.py", []),', '"csm_continuity": ("exc_sandbox/validate_csm_continuity.py", []),', 1)
go = go.replace('runpy.run_path(str(ROOT / "scripts" / script), run_name="__main__")',
                'runpy.run_path(str((OUT_DIR / script) if script.startswith("exc_sandbox/") else (ROOT / "scripts" / script)), run_name="__main__")', 1)
go = go.replace('sys.path.insert(0, str(ROOT / "scripts"))\n    sys.path.insert(0, str(ROOT))',
                'sys.path.insert(0, str(ROOT / "scripts"))\n    sys.path.insert(0, str(OUT_DIR / "exc_sandbox"))\n    sys.path.insert(0, str(ROOT))', 1)
assert "exc_sandbox" in go and "OUT_DIR / script" in go
(HERE / "gate_overlay_exc.py").write_text(go, encoding="utf-8", newline="\n")
print("sandbox written:", [p.name for p in SB.iterdir()], "| validate_master_tables.py bytes", n0, "->", len(mt))
