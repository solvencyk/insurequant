# -*- coding: utf-8 -*-
import json, io, sys, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Run the real validator against the REAL (unmodified) master to capture the
# current KR0010 2026.2Q baseline findings (the "before" state).
result = subprocess.run(
    [r"C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe",
     "scripts/validate_kics_disclosure.py"],
    capture_output=True, text=True, encoding="utf-8", cwd=r"C:\Users\sangwook.cho\Desktop\insurequant"
)
print("returncode:", result.returncode)
print("--- stdout tail ---")
print(result.stdout[-3000:])
print("--- stderr tail ---")
print(result.stderr[-3000:])
