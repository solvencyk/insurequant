import json, glob, sys
sys.stdout.reconfigure(encoding="utf-8")
for f in sorted(glob.glob("data/dart/_fs_api_cache/*_2024_11011_OFS.json")):
    d=json.load(open(f,encoding="utf-8"))
    lst=d.get("list") or []
    if not lst: continue
    # find corp name via meta
    s=json.dumps(d,ensure_ascii=False)
    if "교보생명" in s:
        print(f, list(d.keys()), lst[0].get("corp_code"), len(lst))
