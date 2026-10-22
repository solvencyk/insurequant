"""q14_ast: ast.parse every .py of this folder (warnings as errors) -- READ-ONLY"""
import ast, sys, warnings
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
H = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
bad, n = [], 0
for p in sorted(H.rglob("*.py")):
    n += 1
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    except Exception as e:  # noqa: BLE001
        bad.append((p.name, type(e).__name__, str(e)[:80]))
print("parsed", n, "problems", bad)
