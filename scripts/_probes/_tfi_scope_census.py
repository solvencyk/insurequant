# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
path = Path(sys.argv[1])
rows = json.loads(path.read_text(encoding="utf-8"))
in_scope = [r for r in rows if isinstance(r.get("항목번호"), int) and 47 <= r["항목번호"] <= 54]
combos = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in in_scope}
post_present = sum(1 for r in in_scope if r.get("값_적용후") is not None)
print(f"{path.name}: item47-54 rows={len(in_scope)} combos={len(combos)} with_post={post_present}")
