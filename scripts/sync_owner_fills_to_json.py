#!/usr/bin/env python3
"""Sync owner's xlsx 누계(값) fills into the master JSONs, keyed by (원보험사코드, 공시분기, 항목번호),
and recompute 값_당분기 (당분기[Q1]=누계, 당분기[Qn]=누계[Qn]-누계[Qn-1] within FY; left None if the
prior-quarter 누계 is missing). Direct JSON overwrite (owner-requested); durable diag reflection =
parser order 0811Z. Backs up each JSON to .bak. Does NOT run any build script."""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "insurequant_master_tables.xlsx"
KCODE, KQ, KIID, KITEM, KV, KVD = "원보험사코드", "공시분기", "항목번호", "항목명", "값", "값_당분기"
# owner: only these quarters (2023.1~3Q 버림). 2023.2Q 등 out-of-scope는 건드리지 않음.
ALLOWED = {"2023.4Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"}


def qpos(q):
    m = re.match(r"\d{4}\.(\d)Q", q or "")
    return int(m.group(1)) if m else 0


def qkey(q):
    m = re.match(r"(\d{4})\.(\d)Q", q or "")
    return int(m.group(1)) * 10 + int(m.group(2)) if m else -1


def to_f(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    try:
        return float(str(v).replace(",", "").replace("△", "-").replace("−", "-").strip())
    except Exception:
        return None


def read_sheet(title):
    """-> {(code, quarter, item_no_str): 값}"""
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    if title not in [w.title for w in wb.worksheets]:
        return {}
    ws = wb[title]
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it, ()) or ())

    def idx(name):
        return next((i for i, h in enumerate(hdr) if h and str(h).strip() == name), None)

    ci, qi, ii, vi = idx(KCODE), idx(KQ), idx(KIID), idx(KV)
    if None in (ci, qi, ii, vi):
        print(f"  !! {title} 헤더 detect 실패: {hdr}")
        return {}
    out = {}
    for r in it:
        if max(ci, qi, ii, vi) >= len(r):
            continue
        out[(str(r[ci]).strip(), str(r[qi]).strip(), str(r[ii]).strip())] = r[vi]
    return out


MASTERS = [("손익분해PL", "PL_breakdown.json", True),
           ("CSM워터폴", "CSM_waterfall.json", True),
           ("K-ICS공시", "kics_disclosure.json", False)]

all_changes, uncomputed = [], 0
for sheet, fn, has_dangi in MASTERS:
    p = ROOT / fn
    if not p.exists():
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    xl = read_sheet(sheet)
    if not xl:
        print(f"[{sheet}] xlsx 0 — skip")
        continue
    matched = changed = 0
    edited = set()
    for row in data:
        key = (str(row.get(KCODE, "")).strip(), str(row.get(KQ, "")).strip(),
               str(row.get(KIID, "")).strip())
        if key not in xl:
            continue
        if key[1] not in ALLOWED:          # owner: 7 quarters only
            continue
        matched += 1
        xv = to_f(xl[key])
        if xv is None:
            continue
        jv = row.get(KV)
        jvf = to_f(jv)
        # fill (jvf None) → always apply; edit → only if |diff|>2 (skip xlsx rounding noise)
        if jvf is not None and abs(jvf - xv) <= 2.0:
            continue
        all_changes.append((sheet, key[0], key[1], row.get(KITEM), jv, xv))
        row[KV] = xv
        changed += 1
        edited.add((key[0], key[2]))
    # recompute 값_당분기 for edited (code, item_no) series
    if has_dangi and edited:
        cum, ref = defaultdict(dict), defaultdict(dict)
        for row in data:
            sid = (str(row.get(KCODE, "")).strip(), str(row.get(KIID, "")).strip())
            if sid in edited and isinstance(row.get(KV), (int, float)):
                q = str(row.get(KQ, "")).strip()
                cum[sid][q] = row.get(KV)
                ref[sid][q] = row
        for sid, qm in cum.items():
            for q, c in qm.items():
                if qpos(q) == 1:
                    d = c
                else:
                    pq = f"{q[:4]}.{qpos(q) - 1}Q"
                    d = c - qm[pq] if pq in qm else None
                if d is not None:
                    ref[sid][q][KVD] = round(d, 2)
                elif ref[sid][q].get(KVD) is None:
                    uncomputed += 1
    if changed:
        shutil.copy2(p, str(p) + ".bak")
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{sheet}] 키매칭 {matched} · 갱신 {changed}{'  → written(.bak)' if changed else ''}")

print(f"\n총 {len(all_changes)} 셀 누계 갱신 (당분기 미산출 {uncomputed} = 직전분기 누계 부재):")
for c in all_changes:
    print(f"  [{c[0]}] {c[1]} {c[2]} {c[3]}: {c[4]} → {c[5]}")
