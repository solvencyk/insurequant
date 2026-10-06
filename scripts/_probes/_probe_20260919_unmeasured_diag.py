"""READ-ONLY: for each UNMEASURED bucket, show what the MD actually contains around
the 공통적용 경과조치 section (so 'no table' is never asserted from a keyword miss)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v2.json"

MARK = re.compile(r"공통\s*적용|경과조치\s*적용\s*전|적용\s*전\s*경과조치|경과조치")


def main():
    only_code = sys.argv[1] if len(sys.argv) > 1 else None
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    d = json.loads(SRC.read_text(encoding="utf-8"))
    rows = [r for r in d["rows"] if r["verdict"].startswith("UNMEASURED")]
    seen = {}
    for r in rows:
        if only_code and r["code"] != only_code:
            continue
        seen.setdefault(r["code"], 0)
        if seen[r["code"]] >= per:
            continue
        seen[r["code"]] += 1
        md = ROOT / r["md"]
        print("=" * 90)
        print(f"{r['code']} {r['name']} {r['q']}  md={r['md']}  exists={md.exists()}")
        if not md.exists():
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        print(f"  lines={len(lines)}  '공통적용' hits={text.count('공통적용')}  "
              f"'경과조치' hits={text.count('경과조치')}  '기본자본' hits={text.count('기본자본')}")
        anchors = [i for i, ln in enumerate(lines)
                   if "공통적용" in ln.replace(" ", "") or "공통 적용" in ln]
        if not anchors:
            anchors = [i for i, ln in enumerate(lines)
                       if "경과조치" in ln and ln.lstrip().startswith("#")]
        for a in anchors[:2]:
            lo, hi = a, min(len(lines), a + 22)
            for k in range(lo, hi):
                print(f"   {k+1:5d}| {lines[k]}")
            print("   ---")


if __name__ == "__main__":
    main()
