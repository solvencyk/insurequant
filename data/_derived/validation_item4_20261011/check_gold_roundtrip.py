import json
p = "data/_gold/user_pl_confirmed_cells.json"
raw = open(p, "rb").read()
d = json.loads(raw.decode("utf-8"))
for nl in ("\n", "\r\n"):
    out = json.dumps(d, ensure_ascii=False, indent=2) + "\n"
    out = out.replace("\n", nl)
    print(repr(nl), out.encode("utf-8") == raw, len(out.encode()), len(raw), raw[:3], raw.count(b"\r\n"))
print([k for k in d if k != "cells"], len(d["cells"]))
