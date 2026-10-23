# -*- coding: utf-8 -*-
import hashlib, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
man = json.loads(Path("apply_manifest_e23_lotte.json").read_text(encoding="utf-8"))
ok = True
for rel, h in man["after_sha256"].items():
    c = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == h
    ok &= c
    print(f"{rel}: live sha256 == manifest after_sha256 {c}")
print("revert path valid (live files still carry the post-apply hashes)" if ok else "LIVE FILES MOVED SINCE THE APPLY")
