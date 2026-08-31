# -*- coding: utf-8 -*-
import io
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
PY = r"C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"

proc = subprocess.run(
    [PY, str(ROOT / "scripts" / "validate_kics_disclosure.py")],
    cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace",
)
out = proc.stdout
print(f"exit_code={proc.returncode}")
for line in out.splitlines():
    if line.strip().startswith("Status counts"):
        print(line)
