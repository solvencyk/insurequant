"""READ-ONLY: print slices of _probe_20260919_mirror_audit_v2.json"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v2.json"


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else "CONTAMINATED"
    mode = sys.argv[2] if len(sys.argv) > 2 else "full"
    d = json.loads(SRC.read_text(encoding="utf-8"))
    rows = [r for r in d["rows"] if r["verdict"].startswith(want)]
    print(f"== {want}: {len(rows)} buckets, {sum(len(r['mirrored_items']) for r in rows)} cells ==")
    if mode == "short":
        for r in rows:
            print(f"{r['code']}\t{r['name']}\t{r['q']}\titems={r['mirrored_items']}\tmd={r.get('md')}")
        return
    for r in rows:
        print(f"{r['code']} {r['name']} {r['q']} elective={r['elective_applier']} "
              f"items={r['mirrored_items']}")
        print(f"   raw={json.dumps(r.get('raw', {}), ensure_ascii=False)}")
        print(f"   raw_delta={json.dumps(r.get('raw_delta', {}), ensure_ascii=False)} "
              f"id_pre={r.get('identity_pre_resid')} id_post={r.get('identity_post_resid')}")
        print(f"   m1={r.get('m1')} m2={r.get('m2')} m3={r.get('m3')} m14={r.get('m14')} m28={r.get('m28')}")
        print(f"   m4={r.get('m4')} m12={r.get('m12')} m13={r.get('m13')} md={r.get('md')}")


if __name__ == "__main__":
    main()
