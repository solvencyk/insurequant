# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

path = "data/_derived/_patch_2026q2_KR0074.json"
raw = open(path, "rb").read()
print("BOM present:", raw[:3] == b"\xef\xbb\xbf")
print("file size bytes:", len(raw))

data = json.loads(raw.decode("utf-8"))
print("company_code:", data["company_code"])
print("company_name:", data["company_name"])
print("quarter:", data["quarter"])
print("n cells:", len(data["cells"]))
print("sample item36 항목명:", data["cells"][28]["항목명"] if len(data["cells"])>28 else None)
print()
# print item numbers covered, sorted
nums = sorted(c["항목번호"] for c in data["cells"])
print("item numbers covered:", nums)
print("notes length chars:", len(data["notes"]))
print("unfixable:", data["unfixable"])
