"""Read-only: run the golden-input fingerprint check for ONE spec (viz_ifrs17_panels) against the working tree."""
import json, sys, time
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
import validate_golden_input_fingerprints as V
name = sys.argv[1] if len(sys.argv) > 1 else "viz_ifrs17_panels"
t = time.time()
spec = V.SPECS[name]
actual = V.compute(name, spec)
stored = json.loads(V.RECORD.read_text(encoding="utf-8"))["specs"].get(name)
reds = V.check(name, spec, stored, actual)
print(f"{name}: inputs {actual['input_files']} files, {time.time()-t:.1f}s; stored inputs_sha256 {stored['inputs_sha256'][:12]} actual {actual['inputs_sha256'][:12]}")
print("RED lines:", len(reds))
for r in reds:
    print("  RED", r[:600])
