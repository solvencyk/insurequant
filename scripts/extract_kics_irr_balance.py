# -*- coding: utf-8 -*-
"""[금리위험액 현황] 표에서 시나리오별 자산총계·부채총계·순자산가치 추출 (MD + raw PDF).

확정 절차
  1) 앵커: 표의 순자산가치 행 숫자열이 마스터 항목41/43/44(억원)와 일치해야 한다.
     이 매칭이 컬럼->시나리오 사상과 단위 배율을 동시에 확정한다.
  2) 라벨 매칭: 자산총계/부채총계 행을 라벨로 찾는다(반복 글리프 dedupe 포함).
  3) 라벨 실패 시 항등식 탐색: 같은 컬럼수를 가진 두 행 (A, L) 중
     A[p] - L[p] == nav[p] 가 모든 시나리오에서 성립하는 쌍을 채택한다.
     (OCR 로 행 라벨이 통째 날아간 표 대응)
  4) 최종 검산: 자산총계 - 부채총계 == 순자산가치.
"""
import json
import os
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
import fitz

ITEMS = (41, 42, 43, 44, 45, 46)
Q2DIR = {"2023.2Q": "FY2023_Q2", "2023.4Q": "FY2023_Q4", "2024.2Q": "FY2024_Q2",
         "2024.4Q": "FY2024_Q4", "2025.2Q": "FY2025_Q2", "2025.4Q": "FY2025_Q4",
         "2026.2Q": "FY2026_Q2"}
NUMTOK = re.compile(r"^\(?[-−△Δ]?[\d,]+(\.\d+)?\)?$")
ASSET_LAB = ("자산총계", "총자산", "자산계")
LIAB_LAB = ("부채총계", "총부채", "부채계")


def to_num(s):
    s = s.strip().replace(",", "").replace("△", "-").replace("Δ", "-").replace("−", "-")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    v = float(s)
    return -v if neg else v


def squash(s):
    s = re.sub(r"[\s\.:·•,()]|[ⅠⅡⅢⅣⅤⅥIVl]|^[0-9]+", "", s or "")
    n = len(s)
    for k in range(1, n):
        if n % k == 0 and s == s[:k] * (n // k):
            return s[:k]
    return s


def split_row(tokens):
    labs, nums = [], []
    for t in tokens:
        v = to_num(t) if NUMTOK.match(t) else None
        if v is None:
            labs.append(t)
        else:
            nums.append(v)
    return squash("".join(labs)), nums


def pdf_rows(page):
    ws = page.get_text("words")
    if not ws:
        return []
    ws.sort(key=lambda w: (w[1], w[0]))
    rows, cur, ytop = [], [], None
    for w in ws:
        h = w[3] - w[1]
        if ytop is None or abs(w[1] - ytop) <= max(2.0, h * 0.6):
            cur.append(w)
            ytop = w[1] if ytop is None else ytop
        else:
            rows.append(sorted(cur, key=lambda x: x[0]))
            cur, ytop = [w], w[1]
    if cur:
        rows.append(sorted(cur, key=lambda x: x[0]))
    return stitch([split_row([w[4] for w in r]) for r in rows])


def md_blocks(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    out, cur = [], []
    for ln in lines:
        if ln.strip().startswith("|"):
            cs = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cs):
                cur.append(split_row([c for c in cs if c]))
        else:
            if len(cur) >= 2:
                out.append(stitch(cur))
            cur = []
    if len(cur) >= 2:
        out.append(stitch(cur))
    return out


def stitch(rows):
    """라벨이 숫자행과 다른 줄로 분리된 표(예: 'Ⅲ.' / 숫자 / '순자산가치') 보정.

    숫자행의 라벨이 비었으면 앞뒤의 '라벨만 있는 행'을 끌어와 합성 라벨을 만든다.
    합성 라벨은 자산총계/부채총계/순자산가치 매칭에만 쓰이므로 오합성은 미스로 끝난다.
    """
    out = []
    for i, (lab, nums) in enumerate(rows):
        if nums and not lab:
            pre = nxt = ""
            for j in range(i - 1, max(-1, i - 3), -1):
                if rows[j][1]:
                    break
                if rows[j][0]:
                    pre = rows[j][0]
                    break
            for j in range(i + 1, min(len(rows), i + 3)):
                if rows[j][1]:
                    break
                if rows[j][0]:
                    nxt = rows[j][0]
                    break
            lab = squash(pre + nxt)
        out.append((lab, nums))
    return out


def match(nav, m, tol_rel=3e-4):
    for scale in (1.0, 0.01, 1e-5, 1e-4, 1e-8, 100.0, 10000.0):
        pos, used, ok = {}, set(), True
        for it in (41, 43, 44):
            mv = m.get(it)
            if mv is None:
                ok = False
                break
            tol = max(0.55, abs(mv) * tol_rel)
            c = [p for p, v in enumerate(nav) if p not in used and abs(v * scale - mv) <= tol]
            if not c:
                ok = False
                break
            pos[it] = c[0]
            used.add(c[0])
        if not ok:
            continue
        for it in (42, 45, 46):
            mv = m.get(it)
            if mv is None:
                continue
            tol = max(0.55, abs(mv) * tol_rel)
            c = [p for p, v in enumerate(nav) if p not in used and abs(v * scale - mv) <= tol]
            if c:
                pos[it] = c[0]
                used.add(c[0])
        return pos, scale
    return None


def ident_ok(a, l, nav, pos, scale):
    for _it, p in pos.items():
        if p >= len(a) or p >= len(l):
            return False
        lhs = (a[p] - l[p]) * scale
        rhs = nav[p] * scale
        if abs(lhs - rhs) > max(1.0, abs(rhs) * 6e-4):
            return False
    return True


def pack(pos, scale, nav, a, l, how, ok):
    res = {"scale": scale, "how": how, "identity_ok": ok, "nav": {}, "asset": {}, "liab": {}}
    for it, p in pos.items():
        res["nav"][str(it)] = round(nav[p] * scale, 4)
        res["asset"][str(it)] = round(a[p] * scale, 4) if p < len(a) else None
        res["liab"][str(it)] = round(l[p] * scale, 4) if p < len(l) else None
    return res


def find(rows, m):
    best = None
    for i, (lab, nav) in enumerate(rows):
        if not lab.endswith("순자산가치") or len(nav) < 3:
            continue
        got = match(nav, m)
        if not got:
            continue
        pos, scale = got
        n = len(nav)
        window = rows[max(0, i - 70):i]
        pair, how = None, None
        A = [r for r in window if r[0] in ASSET_LAB and len(r[1]) == n]
        L = [r for r in window if r[0] in LIAB_LAB and len(r[1]) == n]
        for a in A:
            for l in L:
                if ident_ok(a[1], l[1], nav, pos, scale):
                    pair, how = (a[1], l[1]), "label"
                    break
            if pair:
                break
        if not pair:
            cand = [r for r in window if len(r[1]) == n]
            found = []
            for ai in range(len(cand)):
                for li in range(ai + 1, len(cand)):
                    if ident_ok(cand[ai][1], cand[li][1], nav, pos, scale):
                        found.append((cand[ai][1], cand[li][1]))
            if found:
                pair = found[0]
                how = "identity" if len(found) == 1 else "identity_multi"
        if pair:
            return pack(pos, scale, nav, pair[0], pair[1], how, True)
        if A and L and best is None:
            best = pack(pos, scale, nav, A[0][1], L[0][1], "label_no_identity", False)
    return best


def scan_pdf(path, m):
    doc = fitz.open(path)
    hit = None
    for pi in range(doc.page_count):
        ts = doc[pi].get_text().replace(" ", "").replace(chr(10), "")
        if "순자산가치" not in ts:
            continue
        rows = pdf_rows(doc[pi])
        r = find(rows, m)
        if not (r and r["identity_ok"]) and pi > 0:
            r2 = find(pdf_rows(doc[pi - 1]) + rows, m)
            if r2 and (r2["identity_ok"] or not r):
                r = r2
        if r:
            r["src"] = "pdf:" + os.path.basename(path) + "#p" + str(pi + 1)
            if r["identity_ok"]:
                doc.close()
                return r
            hit = hit or r
    doc.close()
    return hit


def scan_md(path, m):
    hit = None
    for blk in md_blocks(path):
        r = find(blk, m)
        if r:
            r["src"] = "md:" + os.path.basename(path)
            if r["identity_ok"]:
                return r
            hit = hit or r
    return hit


def main(outpath):
    kd = json.load(open("kics_disclosure.json", encoding="utf-8"))
    master, meta = {}, {}
    for r in kd:
        meta[r["원보험사코드"]] = (r["원수사명"], r["생손보여부"])
        if r["항목번호"] in ITEMS:
            try:
                master.setdefault((r["공시분기"], r["원보험사코드"]), {})[r["항목번호"]] =                     float(str(r["값"]).replace(",", ""))
            except (TypeError, ValueError):
                pass
    QS = list(Q2DIR)
    files = {}          # (q, code) -> {"pdf": path, "md": path}
    for q, d in Q2DIR.items():
        base = os.path.join("data/disclosure", d)
        for sub, key, ext in (("parsed", "md", ".md"), ("raw", "pdf", ".pdf")):
            dd = os.path.join(base, sub)
            if not os.path.isdir(dd):
                continue
            for f in sorted(os.listdir(dd)):
                if f.lower().endswith(ext) and "_" in f:
                    files.setdefault((q, f.split("_")[0]), {}).setdefault(key, os.path.join(dd, f))
    out, miss = {}, []
    for qi, q in enumerate(QS):
        for (qq, c), m in sorted(master.items()):
            if qq != q or 41 not in m:
                continue
            # 자기 분기 -> 다음 짝수분기(직전반기 컬럼) -> 그 다음 -> 이전 분기 순으로 탐색.
            # 어느 문서에서 찾든 앵커(항목41/43/44 일치)가 해당 분기임을 보증한다.
            order = [q] + QS[qi + 1:qi + 3] + QS[max(0, qi - 1):qi][::-1]
            hit = None
            for src_q in order:
                fs = files.get((src_q, c), {})
                for key, fn in (("pdf", scan_pdf), ("md", scan_md)):
                    if not fs.get(key):
                        continue
                    r = fn(fs[key], m)
                    if r:
                        r["src_quarter"] = src_q
                        if r["identity_ok"]:
                            hit = r
                            break
                        hit = hit or r
                if hit and hit["identity_ok"]:
                    break
            if hit:
                out[q + "|" + c] = hit
            else:
                miss.append((q, c, meta[c][0]))
        print(q + ": 누적 " + str(len(out)) + " / 미추출 " + str(len(miss)), flush=True)
    json.dump(out, open(outpath, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    ok = sum(1 for v in out.values() if v["identity_ok"])
    print(chr(10) + "대상 " + str(len(out) + len(miss)) + " · 추출 " + str(len(out))
          + " (항등식OK " + str(ok) + ") · 미추출 " + str(len(miss)))
    print("경로:", dict(Counter(v["how"] for v in out.values())))
    print("출처분기:", dict(Counter(("자기" if v.get("src_quarter") == k.split("|")[0] else "타분기")
                                 for k, v in out.items())))
    for q, c, n in sorted(miss):
        print("  MISS " + q + " " + c + " " + n)


main(sys.argv[1] if len(sys.argv) > 1 else "data/_derived/kics_irr_balance.json")
