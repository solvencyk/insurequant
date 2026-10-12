import json, csv, subprocess
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
new = {}
for r in json.loads(subprocess.check_output(["git", "-C", REPO, "show", "74a415bf:kics_disclosure.json"]).decode("utf-8")):
    new[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
out = open("a6b.txt", "w", encoding="utf-8")
for code, q in [("KR0009","2023.1Q"),("KR0009","2023.2Q"),("KR0050","2025.3Q"),("KR0069","2024.2Q"),("KR0095","2024.4Q"),("KR0099","2024.3Q"),("KR0080","2026.1Q"),("KR0049","2025.1Q")]:
    for i in range(1, 29):
        r = new.get((code, q, i))
        if not r: continue
        try: d = float(r.get("값")) != float(r.get("값_적용후"))
        except: d = r.get("값") != r.get("값_적용후")
        if d: out.write(f"{code} {q} item{i} pre={r.get('값')} post={r.get('값_적용후')}\n")
