# -*- coding: utf-8 -*-
"""scratch probe: notes, CSM tables, old-layout statements, summaries of kr0070_verify.py (read-only)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kr0070_verify as V  # noqa

sys.stdout.reconfigure(encoding="utf-8")
for key in ["N1", "N2", "N3", "N4", "O1", "O2", "O3", "O4"]:
    print("=====", key)
    try:
        n3 = V.pl4_note3(key, "prior" if key.startswith("N") else "cur")
        print("  note3 :", n3["printed"], "L", n3["line"], n3["unit"], n3["heads"], n3["table"])
    except Exception as e:  # noqa
        print("  note3 ERR", e)
    try:
        n1 = V.pl4_note1(key)
        print("  note1 :", n1["printed"], "L", n1["line"], n1["unit"], "n_numeric", n1["n_numeric"], n1["table"])
    except Exception as e:  # noqa
        print("  note1 ERR", e)
    try:
        T = V.csm_tables(V.F[key])
        for role, t in sorted(T.items()):
            print("  csm", role, t["table"], t["caption"], t["unit"], "col", t["col"])
            for i in range(1, 7):
                c = t["rows"][i]
                print("     ", i, None if c is None else (c["label"][:40], c["printed"], c["line"], c["mn"]))
    except Exception as e:  # noqa
        print("  csm ERR", e)
for key in ["O1", "O2"]:
    for which, sec in (("별도", r"^4\.\s*재무제표$"), ("연결", r"^2\.\s*연결재무제표$")):
        try:
            S = V.OldStmt(key, sec)
            print("==", key, which, "unit", S.unit, "table", S.tab[0] + 1)
            for lab in ["보험서비스결과", "보험수익", "보험서비스비용", "재보험손익", "영업이익", "영업외손익", "법인세비용차감전순이익", "법인세비용", "분기순이익", "반기순이익", "기타포괄손익"]:
                try:
                    print("    ", lab, [(s["printed"], s["line"]) for s in S.slots(lab)])
                except Exception as e:  # noqa
                    print("    ", lab, "ERR", str(e)[-60:])
        except Exception as e:  # noqa
            print("==", key, which, "ERR", e)
    for which in ("연결", "별도"):
        try:
            sm = V.summary_pl(key, which)
            print("  summary", which, {k: v["printed"] for k, v in sm.items()})
        except Exception as e:  # noqa
            print("  summary", which, "ERR", e)
