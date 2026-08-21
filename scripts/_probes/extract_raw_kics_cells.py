# -*- coding: utf-8 -*-
"""원문 PDF에서 지급여력 표를 통째로 뽑아 캐시한다 (read-only, 마스터를 보지 않는다).

목적: 게이트는 '숫자끼리 아귀가 맞는가'만 본다. 그건 스케일 오차·날조된 셀처럼
**항등식을 만족시키면서 원문과 다른** 값을 통과시킨다(2026-08-21 교보 4셀, 흥국생명 item24).
그래서 원문을 독립적으로 뽑아 마스터와 셀 단위로 대조할 재료를 만든다.

docling MD 를 쓰지 않는다 — MD 는 페이지를 통째로 떨어뜨린 전례가 있고(교보 p15·p16),
그 유실을 '원문에 표가 없다'로 오독한 것이 이번 주 거짓 면제 2건의 원인이다. fitz 로 raw 를 읽는다.

산출: data/_derived/kics_raw_cells.json

사용: python scripts/_probes/extract_raw_kics_cells.py [--only KR0069] [--fy FY2026_Q1]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import fitz

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "data" / "_derived" / "kics_raw_cells.json"
DISC = REPO / "data" / "disclosure"
sys.stdout.reconfigure(encoding="utf-8")

# 라벨 -> 항목번호. **서수(1./2./3.)에 의존하지 않는다** — 동양생명은 조정준비금이 "6." 이고
# 다른 회사는 "7." 이다. 구별되는 어간으로만 잡는다. 리스트 순서가 곧 우선순위.
LABEL_MAP: list[tuple[str, int]] = [
    ("지급여력금액으로불인정하는항목", 12),
    ("보완자본으로재분류하는항목", 13),
    ("건전성감독기준재무상태표상의순자산", 4),
    ("업권별자본규제를활용한종속회사", 24),
    ("비례성원칙을적용한종속회사", 25),
    ("업권별자본규제를활용한관계회사", 26),
    ("생명장기손해보험위험액", 17),
    ("생명·장기손해보험위험액", 17),
    ("일반손해보험위험액", 18),
    ("기본요구자본", 15),
    ("기타요구자본", 23),
    ("법인세조정액", 22),
    ("분산효과", 16),
    ("지급여력기준금액", 14),
    ("지급여력비율", 27),
    ("기본자본비율", 28),
    ("지급여력금액", 1),
    ("자본항목중보통주이외의자본증권", 6),
    ("보통주이외의자본증권", 6),
    ("보통주", 5),
    ("이익잉여금", 7),
    ("자본조정", 8),
    ("기타포괄손익누계액", 9),
    ("비지배지분", 10),
    ("조정준비금", 11),
    ("기본자본", 2),
    ("보완자본", 3),
    ("시장위험액", 19),
    ("신용위험액", 20),
    ("운영위험액", 21),
    ("사망위험", 29),
    ("장수위험", 30),
    ("장해·질병위험", 31),
    ("장해질병위험", 31),
    ("장기재물·기타위험", 32),
    ("장기재물기타위험", 32),
    ("해지위험", 33),
    ("사업비위험", 34),
    ("금리위험", 36),
    ("주식위험", 37),
    ("부동산위험", 38),
    ("외환위험", 39),
    ("자산집중위험", 40),
    ("보험가격및준비금위험", -1),   # 일반손해 하위 — 마스터에 대응 항목 없음
]
# 위 어간을 접두사로 갖지만 **다른 행**인 것들. LABEL_MAP 보다 먼저 본다 —
# 안 그러면 경과조치표의 '보완자본 한도' 3행이 전부 item3 으로 뭉친다(동양생명 2024.2Q 실측).
EXCLUDE_PREFIX = (
    "보완자본한도", "기본자본자본증권", "기발행", "해약환급금",
    "지급여력금액불인정", "보험가격",
)
CATASTROPHE = "대재해위험"          # 생명(35) vs 일반(대응없음) — 직전 라벨로 가른다
LIFE_PREV = {29, 30, 31, 32, 33, 34}
QRE = re.compile(r"(\d{2})[.\s]*(\d)Q")
NUMRE = re.compile(r"^\(?-?[\d,]+(?:\.\d+)?\)?$")


ENUM = re.compile(r"^(?:[가나다라마바]\.|\d{1,2}\.|[ⅠⅡⅢⅣ①②③④⑤]\.?|[-–—·]\s*)")


def _norm(s: str) -> str:
    """라벨 정규화. 선행 서수(가./1./Ⅰ./-)는 **반복해서** 벗긴다.

    서수를 남기면 '가.지급여력금액'·'1.보통주' 가 어간 매칭에 안 걸린다(동양생명 실측에서
    12개 행이 통째로 unmapped 였다). 항목 판정 자체는 서수가 아니라 어간으로만 한다 —
    조정준비금이 어떤 회사는 '7.' 이고 동양생명은 '6.' 이다."""
    s = re.sub(r"주\d*\)", "", s or "")
    s = s.replace("\n", "").replace(" ", "").replace("‧", "·").replace("∙", "·").strip()
    s = s.lstrip("(")
    for _ in range(4):
        t = ENUM.sub("", s)
        if t == s:
            break
        s = t
    return s


def _num(tok: str):
    """'(3,962)' -> -3962.0 · '-' -> None(미기재) · '0' -> 0.0"""
    t = (tok or "").replace("\n", "").replace(" ", "").replace("%", "")
    if t in ("", "-", "–", "—", "─"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    if neg:
        t = t[1:-1]
    if not NUMRE.match(t):
        return None
    try:
        v = float(t.replace(",", "").replace("(", "").replace(")", ""))
    except ValueError:
        return None
    return -v if neg else v


DASHES = ("-", "–", "—", "─")


def _value_groups(rows):
    """값이 실린 열을 찾아 **인접한 것끼리 묶는다.**

    find_tables 는 같은 논리열을 물리열 2~3개로 쪼개 놓기도 한다(동양생명 2023.2Q p12 는
    3개 분기가 11/12/13 · 15/16 · 18/19/20 으로 흩어진다). 안 묶으면 열 개수가 6으로 세어져
    연속분 인식이 깨지고 표가 통째로 버려진다. '-' 도 값으로 센다 — 전전분기가 전부 '-' 인
    K-ICS 도입 초기 분기에서 열이 사라지기 때문."""
    cnt = {}
    for r in rows:
        for i, c in enumerate(r):
            t = str(c or "").replace("\n", "").replace(" ", "")
            if _num(t) is not None or t in DASHES:
                cnt[i] = cnt.get(i, 0) + 1
    # 후보는 1회 등장부터 모으고, **묶은 뒤에** 그룹 합계로 거른다. 등장횟수로 먼저 자르면
    # 한 행만 그 물리열을 쓰는 경우(동양생명 item4 '순자산' 값이 홀로 index 10 에 있다)가
    # 그룹에서 빠져 그 행만 통째로 None 이 된다.
    groups = []
    for i in sorted(cnt):
        if groups and i - groups[-1][-1] <= 1:
            groups[-1].append(i)
        else:
            groups.append([i])
    return [g for g in groups if sum(cnt[i] for i in g) >= 2]


def _group_val(row, group):
    for i in group:
        if i < len(row):
            v = _num(str(row[i] or ""))
            if v is not None:
                return v
    return None


def _quarter(cell: str):
    m = QRE.search((cell or "").replace(" ", ""))
    if not m:
        return None
    yy, q = m.groups()
    return "20%s.%sQ" % (yy, q)


def _unit_for(text: str):
    if "단위" not in text:
        return None
    i = text.find("단위")
    seg = text[max(0, i - 40): i + 40]
    for u in ("백만원", "천원", "억원", "원"):
        if u in seg:
            return u
    return None


def _classify(rows):
    """헤더에서 열의 정체를 읽는다. 분기 3개면 main3q, 경과조치 전/후면 transition."""
    joined = " ".join(" ".join(str(c or "") for c in row) for row in rows[:3])
    joined_n = joined.replace(" ", "").replace("\n", "")
    ncol = max((len(r) for r in rows), default=0)
    cols = []
    for ci in range(ncol):
        lab = " ".join(str(rows[ri][ci] or "") for ri in range(min(3, len(rows)))
                       if ci < len(rows[ri])).strip()
        norm = lab.replace(" ", "").replace("\n", "")
        q = _quarter(lab)
        if "경과조치적용후" in norm or ("적용후" in norm and "경과조치" in joined_n):
            cols.append({"label": lab, "role": "post"})
        elif "경과조치적용전" in norm or ("적용전" in norm and "경과조치" in joined_n):
            cols.append({"label": lab, "role": "pre"})
        elif q:
            cols.append({"label": lab, "role": "quarter", "quarter": q})
        else:
            cols.append({"label": lab, "role": None})
    # 경과조치표 헤더는 '구분 | 경과조치 | 경과조치' 와 '적용 전 | 적용 후' 가 두 줄로 쪼개져
    # 한쪽만 잡히는 일이 잦다. 헤더 전체에 전·후가 둘 다 있고 값열이 정확히 2개면 순서대로 준다.
    roles = [c["role"] for c in cols]
    if "적용전" in joined_n and "적용후" in joined_n and roles.count("pre") + roles.count("post") == 1:
        vi = []
        for ci in range(ncol):
            n = sum(1 for r in rows if ci < len(r) and _num(str(r[ci] or "")) is not None)
            if n >= 3:
                vi.append(ci)
        if len(vi) == 2:
            cols[vi[0]] = dict(cols[vi[0]], role="pre")
            cols[vi[1]] = dict(cols[vi[1]], role="post")
    if any(c["role"] in ("pre", "post") for c in cols):
        kind = "transition"
    elif any(c["role"] == "quarter" for c in cols):
        kind = "main3q"
    else:
        kind = "unknown"
    return kind, cols


def _inherit(rows, cols, prev_cols):
    """헤더 없는 **표 연속분**에 직전 표의 열 정체를 물려준다.

    총괄표는 페이지를 넘어가면서 헤더를 다시 안 찍는다 — 동양생명 2023.2Q 는 항목 1~11 이
    p11, 12~28 이 p12 에 있는데 p12 쪽에 분기 헤더가 없어 통째로 버려졌다(마스터에 26개 항목
    결측 = RED 7건의 원인). 흥국화재 ④금리표도 같은 모양이다. 값이 실린 열 개수가 직전 표와
    같을 때만 물려준다."""
    if not prev_cols:
        return None, cols
    groups = _value_groups(rows)
    if len(groups) != len(prev_cols):
        return None, cols
    new = [{"label": "", "role": None} for _ in range(max((len(r) for r in rows), default=0))]
    for g, pc in zip(groups, prev_cols):
        for i in g:
            while len(new) <= i:
                new.append({"label": "", "role": None})
            new[i] = dict(pc, label=pc.get("label", "") + " (연속분)")
    kind = "transition" if prev_cols[0]["role"] in ("pre", "post") else "main3q"
    return kind, new


def _map_table(rows, cols):
    """행 라벨 -> 항목번호. 값은 정체가 확인된 열 순서대로 담는다."""
    groups = _value_groups(rows)
    group_cols = []
    for g in groups:
        role = next((cols[i] for i in g if i < len(cols) and cols[i].get("role")), None)
        group_cols.append(role or {"label": "", "role": None})
    first_val = min((g[0] for g in groups), default=1)
    cells, unmapped, last_item = {}, [], None
    for r in rows:
        labs = [_norm(str(c or "")) for c in r[:max(1, first_val)]]
        lab = max(labs, key=len) if labs else ""
        if not lab:
            continue
        item = None
        if lab.startswith(EXCLUDE_PREFIX):
            item = -1
        elif lab.startswith(CATASTROPHE):
            item = 35 if last_item in LIFE_PREV else -1
        else:
            for pat, it in LABEL_MAP:
                if lab.startswith(pat):
                    item = it
                    break
        vals = [_group_val(r, g) for g in groups]
        if item is None:
            if any(v is not None for v in vals):
                unmapped.append(lab[:48])
            continue
        last_item = item
        if item < 0:
            continue
        cells.setdefault(str(item), []).append(vals)
    return cells, unmapped, group_cols


def extract_pdf(pdf: Path) -> dict:
    doc = fitz.open(pdf)
    out = {"pdf": str(pdf.relative_to(REPO)).replace("\\", "/"),
           "pages": doc.page_count, "tables": [], "textlayer": 0}
    prev_cols = None
    try:
        for pno in range(doc.page_count):
            page = doc[pno]
            text = page.get_text()
            out["textlayer"] += len(text)
            if not any(k in text for k in ("지급여력기준금액", "기본요구자본", "지급여력금액")):
                continue
            try:
                found = page.find_tables()
            except Exception:
                continue
            unit = _unit_for(text)
            for tb in found.tables:
                try:
                    rows = tb.extract()
                except Exception:
                    continue
                if len(rows) < 2:
                    continue
                kind, cols = _classify(rows)
                inherited = False
                if kind == "unknown":
                    kind, cols = _inherit(rows, cols, prev_cols)
                    if kind is None:
                        continue
                    inherited = True
                cells, unmapped, group_cols = _map_table(rows, cols)
                if not cells or not any(c.get("role") for c in group_cols):
                    continue
                if not inherited:
                    prev_cols = group_cols
                out["tables"].append({
                    "page": pno + 1,
                    "kind": kind,
                    "inherited": inherited,
                    "unit": unit,
                    "columns": group_cols,
                    "cells": cells,
                    "unmapped": unmapped[:12],
                })
    finally:
        doc.close()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="company code, e.g. KR0069")
    ap.add_argument("--fy", help="e.g. FY2026_Q1")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    pat = str(DISC / (args.fy or "FY*") / "raw" / ((args.only or "KR") + "*.pdf"))
    pdfs = sorted(glob.glob(pat))
    print("대상 PDF %d개" % len(pdfs))
    data, errs = {}, 0
    for n, p in enumerate(pdfs, 1):
        p = Path(p)
        key = "%s/%s" % (p.parents[1].name, p.stem.split("_")[0])
        try:
            data[key] = extract_pdf(p)
        except Exception as e:
            errs += 1
            data[key] = {"pdf": p.name, "error": "%s: %s" % (type(e).__name__, e)}
        if n % 25 == 0 or n == len(pdfs):
            print("  %d/%d ..." % (n, len(pdfs)), flush=True)
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tabs = sum(len(v.get("tables", [])) for v in data.values())
    print("\n완료: %d (분기,회사) · 표 %d · 오류 %d -> %s" % (len(data), tabs, errs, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
