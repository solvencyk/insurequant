# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(__file__).resolve().parents[3]

cl = root / "docs/changelog_publishing.md"
t = cl.read_text(encoding="utf-8")
marker = "## 2026-10-11 \u2014 \ub9c8\uac10 \ub77c\uc6b4\ub4dc"
entry = """## 2026-10-11 \u2014 \ubbf8\ub2c8 \uc7ac\ub3d9\uae30\ud654: \ub77c\uc774\ub098 CSM\u00b7PL \ud56d\ubaa9 4\u00b7\uc0c1\uac01 \uc815\uc815 \ubc18\uc601 (\ucee4\ubc0b\ub9cc, push\u00b7\ubc30\ud3ec \ubcf4\ub958)

- **xlsx**(`5d320c9`): \uc190\uc775\ubd84\ud574PL +33\ud589\u00b72\uce78 \u00b7 CSM\uc6cc\ud130\ud3f4 +54\ud589\u00b715\uce78 \u00b7 CSM\uc0c1\uac01 +50\ud589\u00b7172\uce78 \u00b7 \uc2e0\uacc4\uc57dCSM\ubc30\uc218 +9\ud589\u00b76\uce78, \uc0ad\uc81c 0. \ub9c8\uc2a4\ud130 diff \uc640 \ub9de\uace0 \ub098\uba38\uc9c0 13\uc2dc\ud2b8\ub294 \uac12 SHA \ub3d9\uc77c. \ub4dc\ub9ac\ud504\ud2b8 189 -> 0.
- **NB \ub9c8\uc2a4\ud130**: `build_nb_csm_multiple.py` \uc7ac\ube4c\ub4dc 381 -> 390\ud589. \ub77c\uc774\ub098 +9\ud589\u00b7\ube48\uce78 3\uac1c \ucc44\uc6c0\ub9cc \ubc14\ub01c, \ub2e4\ub978 \ud68c\uc0ac 0 \ubcc0\uacbd. `NB_CENSUS_MISSING` 0.
- **\ud328\ub110**: IFRS17 viz 4\uac1c\u00b7csm_waterfall \ubc14\uc774\ud2b8 \ub3d9\uc77c(\ub77c\uc774\ub098\ub294 DART \ud589\uc774\ub77c \ub9c8\uc2a4\ud130 \uc0c1\uac01\uc774 \ud328\ub110\uc5d0 \uc548 \uac04\ub2e4), csm_combo \ub77c\uc774\ub098 nb_csm 11\uce78, compare 53\uce78(\ub77c\uc774\ub098 + \uc7ac\ubcf4\uc0ac \uc2e0\uacc4\uc57d CSM 18\uce78).
- **\uacf5\uac1c \uc2a4\ub0c5\uc0f7**(`812b007`): 4\uc2dc\ud2b8 + manifest(`build_id` 5d320c9). \uac8c\uc774\ud2b8 data-contract RED 0 \u00b7 live_artifacts RED 8(`INSPL_CENSUS_MISSING` \ubfd0). \uace8\ub4e0 `csm_amort_schedule` \ud574\uc2dc\ub9cc \uc5b4\uae0b\ub0a8(validation `--update` \ub300\uae30). \uc0c1\uc138 `data/disclosure/_meta/mini_resync_runlog_20261011.md`.

"""
if "\ubbf8\ub2c8 \uc7ac\ub3d9\uae30\ud654" not in t:
    t = t.replace(marker, entry + marker, 1)
    cl.write_text(t, encoding="utf-8")

td = root / "TODO_publishing.md"
s = td.read_text(encoding="utf-8")
status_head = "## Status (\ucd5c\uc2e0 3\uac1c)\n\n"
new = ("- **2026-10-11 \ubbf8\ub2c8 \uc7ac\ub3d9\uae30\ud654(\ub77c\uc774\ub098 CSM\u00b7PL \ud56d\ubaa9 4\u00b7\uc0c1\uac01 \uc815\uc815, \ucee4\ubc0b\ub9cc \u00b7 push \ubcf4\ub958)** \u2014 xlsx 4\uc2dc\ud2b8(`5d320c9`)\u00b7NB \ub9c8\uc2a4\ud130 \uc7ac\ube4c\ub4dc\u00b7combo/compare \uc7ac\ube4c\ub4dc\u00b7`public_exports`(`812b007`). \ub4dc\ub9ac\ud504\ud2b8 0, data-contract RED 0, live_artifacts RED 8(`INSPL_CENSUS_MISSING` \ubfd0, `NB_CENSUS_MISSING` 0).\n"
       "  \ub0a8\uc740 \uac83: \u2460 \uace8\ub4e0 `test_viz_ifrs17_panels_golden`(`csm_amort_schedule` \ud574\uc2dc\ub9cc)\u00b7\uc9c0\ubb38 `--update` \ub294 validation \u2461 \ub77c\uc774\ub098 \uc0c1\uac01 \uc2a4\ucf00\uc904\uc740 \ud328\ub110\uc5d0 \uc548 \uac04\ub2e4(\ud328\ub110 \ud589\uc774 DART \uc6d0\ucc9c) \u2014 \ud654\uba74\uc5d0 \uc2f8\uc9c0 owner \ud310\ub2e8. \uc0c1\uc138 `data/disclosure/_meta/mini_resync_runlog_20261011.md`.\n\n")
if "\ubbf8\ub2c8 \uc7ac\ub3d9\uae30\ud654" not in s:
    s = s.replace(status_head, status_head + new, 1)
    td.write_text(s, encoding="utf-8")
print("ok")
