"""READ-ONLY: pretty-print slices of the mirror raw-audit probe output."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "data" / "_derived" / "_probe_20260919_mirror_raw_audit.json"


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else "RAW_TIER_MOVED"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    d = json.loads(SRC.read_text(encoding="utf-8"))
    rows = [r for r in d["rows"] if r["verdict"] == want]
    print(f"== {want}: {len(rows)} buckets ==")
    for r in rows[:limit]:
        raw = r.get("raw", {})
        dl = r.get("raw_delta", {})
        print(f"{r['code']} {r['name']} {r['q']} appl={r['applier']} items={r['items_with_post']} "
              f"unit={r.get('raw_unit','')!r} line={r.get('raw_line')}")
        print(f"   raw t1 {raw.get('tier1',{}).get('pre')}->{raw.get('tier1',{}).get('post')} "
              f"t2 {raw.get('tier2',{}).get('pre')}->{raw.get('tier2',{}).get('post')} "
              f"amt {raw.get('amount',{}).get('pre')}->{raw.get('amount',{}).get('post')} "
              f"scr {raw.get('scr',{}).get('pre')}->{raw.get('scr',{}).get('post')} "
              f"delta={dl}")
        print(f"   master i1 {r.get('m1_pre')}/{r.get('m1_post')} i2 {r.get('m2_pre')}/{r.get('m2_post')} "
              f"i3 {r.get('m3_pre')}/{r.get('m3_post')} i14 {r.get('m14_pre')}/{r.get('m14_post')} "
              f"i28 {r.get('m28_pre')}/{r.get('m28_post')}")
        print(f"   master i4 {r.get('m4_pre')}/{r.get('m4_post')} i12 {r.get('m12_pre')}/{r.get('m12_post')} "
              f"i13 {r.get('m13_pre')}/{r.get('m13_post')}  md={r.get('md')}")


if __name__ == "__main__":
    main()
