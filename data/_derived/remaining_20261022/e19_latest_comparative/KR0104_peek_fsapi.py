# -*- coding: utf-8 -*-
import json
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
d = json.loads((ROOT/"data/dart/_fs_api_cache/00909349_2024_11014_OFS.json").read_text(encoding="utf-8"))
out = ["keys: " + ",".join(d.keys()), "status " + str(d.get("status"))]
for a in d.get("list", []):
    if a.get("sj_div") in ("IS", "CIS"):
        out.append("%s|%s|%s|%s|th=%s|thadd=%s|fr=%s|fradd=%s" % (a.get("sj_div"), a.get("account_id"), a.get("account_nm"), a.get("ord"), a.get("thstrm_amount"), a.get("thstrm_add_amount"), a.get("frmtrm_amount"), a.get("frmtrm_add_amount")))
(HERE/"KR0104_peek_fsapi.txt").write_text("\n".join(out)+"\n", encoding="utf-8", newline="\n")
