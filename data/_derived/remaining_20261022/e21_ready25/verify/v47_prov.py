import json,sys,collections; sys.stdout.reconfigure(encoding="utf-8")
blocks=json.load(open("v01_PL_breakdown_provenance_blocks.json",encoding="utf-8"))
cnt=collections.Counter()
for k,o,n in blocks:
    cnt[(o.get("source_id"),n.get("source_id"))]+=1
print(dict(cnt))
for k,o,n in blocks:
    if o.get("source_id")!=n.get("source_id") or k[0] in ("KR0003","KR0104") and k[1]=="2023.1Q":
        print(k,o.get("source_id"),"->",n.get("source_id"),"| src_file:",str(o.get("source_file"))[-50:],"->",str(n.get("source_file"))[-60:],"| published_items",o.get("published_items"),"->",n.get("published_items"),"| unresolved",o.get("unresolved_reason"),"->",n.get("unresolved_reason"))
