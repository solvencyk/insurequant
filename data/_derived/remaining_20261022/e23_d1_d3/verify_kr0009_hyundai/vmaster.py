import json, subprocess
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
CO = "KR0009"

def head(path):
    r = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + path], capture_output=True)
    return json.loads(r.stdout.decode("utf-8"))

def work(path):
    with open(ROOT + "/" + path, encoding="utf-8") as f:
        return json.load(f)

def idx(rows, co=CO):
    d = {}
    for r in rows:
        if r["원보험사코드"] == co:
            d[(r["공시분기"], r["항목번호"])] = r
    return d

def load_all(name):
    return idx(head(name + ".json")), idx(work(name + ".json"))
