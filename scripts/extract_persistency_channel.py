#!/usr/bin/env python3
"""판매채널별 계약유지율 추출기 -- 정기경영공시 PDF 의 `7-6 불완전판매비율, (청약철회비율 및) 유지율 현황` 안 유지율 표.

산출 (루트 마스터가 아니라 data/persistency/ 안에만 쓴다 -- 홈페이지 표시는 owner 미정):
  data/persistency/persistency_channel.json   long format, 1행 = (회사, 분기, 회차, 채널)
  data/persistency/census.csv                 기대그리드(회사 x 반기·결산 7분기) 전 칸의 상태 + 근거
  data/persistency/selfcheck.csv              항등식 불일치 · 보정 · 채널합 대조 · 범위/단조성 플래그 (무답지 자기검증)

원천 / 설계 결정
----------------
* 1차 = raw PDF 텍스트층(fitz). docling MD 는 K-ICS 키워드 창만 잘라 7장을 떨구므로 쓰지 않는다
  (텍스트층이 아예 없는 사본만 MD 폴백, 추출방식="md"). 스캔본은 즉흥 OCR 하지 않는다 -> SCAN_PENDING
  (별도 vision 에이전트가 data/persistency/vision_cells*.json 에 쓰고, 이 스크립트는 재실행만으로 병합한다).
* 1Q·3Q 분기공시는 축약본이라 이 표가 없다 -- 대상은 2Q·4Q 7개 분기(2023.2Q ... 2026.2Q).
* 표 모양이 사/분기마다 다르다(8열 옛 서식 · 9열 · 11열, 열 머리가 2~3줄로 쪼개지거나 `금융/기관/보험/대리점` 처럼
  세로로 흩어짐, 회차 라벨이 값과 y 가 5pt 어긋남, 유지/계약액 라벨 자체가 조각남). 그래서 `find_tables()` 를 쓰지 않고
  단어 좌표 + 세로 괘선으로 직접 격자를 세운다:
    1) 행: 라벨(유지계약액/대상신계약액/NN회차/유지율) 앵커 -> 못 찾는 블록은 위치(R 다음 두 숫자행)로 보충
    2) 열: 데이터 y 구간을 덮는 세로 괘선 군집(coverage>=60%) = 열 경계. 오른쪽/왼쪽 끝 괘선이 안 그려진 표는
       토큰 끝에서 경계를 추가. 괘선이 점선이어도(삼성화재) 실선 세로선만 모아 쓴다.
    3) 칸 안 토큰: 인접 칸 숫자가 붙어 나오면(`524,581262,552`) 문자 좌표로 열 경계에서 쪼갠다.
    4) 열 이름: 머리 토큰을 열 구간에 모아 `채널_원문` 으로 남기고, 표준 11코드로 매핑(실패 시 열 수 템플릿, 그래도
       안 되면 채널=UNMAPPED_n + 원문).
* 값 보정은 항등식으로 확증될 때만 한다: 원문 오탈자 `63,43`(쉼표가 소수점) · `378.787`(점이 천단위)처럼
  유지율 = 유지계약액/대상신계약액x100 을 다시 맞추는 읽기만 채택하고 `repair` 를 남긴다. 확증 안 되면 그대로 두고
  항등식 RED 로 보고한다(원문 인쇄 오류 추정은 RED 목록 + 근거에 남는다). "틀린 값을 싣느니 빈 칸".
* 원문 인쇄 오기: 항등식이 깨져도 PDF 쪽을 직접 보고(렌더 확인) 파서 오류(열·행 밀림)가 아니라 원문이 그렇게 인쇄된 것으로 확정한
  칸은 값을 그대로 두고 data/persistency/source_errata.csv 에 근거와 함께 등재한다 -> 행에 `source_misprint`(유형)·`identity_note`.
  등재부에 없는 break 는 selfcheck 에 `[미등재]` 로 남아 계속 RED 다. 등재했는데 break 가 아니게 된 칸은 경고를 낸다.
* 같은 칸 안에서 줄바꿈된 숫자(`1,204,6`+`34`)는 이어 붙인 값이 항등식으로 확증될 때만 채택(`repair`=`wrap[...]`). 표 안에서
  숫자·대시가 아니라 버려진 토큰은 note 로 올린다. `대상없음`(NA 글자)은 `-` 와 같이 null + dash(+`na_text`).
* 항등식 등급: ok(|편차|<=0.06, 정수 인쇄는 인쇄 정밀도만큼) / round(금액이 백만원 단위 반올림이라 오차구간 안) /
  trunc(회사가 소수를 반올림이 아니라 절삭 인쇄) / break(RED). 원문 `-` 는 0 이 아니라 null + dash.
* 항등식 재계산(2026-10-07 P4, YELLOW-2): 텍스트·vision 구분 없이 마지막에 모든 행을 identity_status() 로 다시 계산한다.
  vision 파일의 identity 라벨은 참고용 -- 재계산 등급과 종류(good=ok/round/trunc · break · na)가 다르면 selfcheck 에
  IDENTITY_RELABEL 로 남기고 값은 재계산 결과로 덮는다(라벨이 없는 vision 행도 재계산으로 채운다). 재계산의 금액 반올림 구간은
  금액 인쇄 소수 자릿수에 맞춘다(소수 1자리 금액은 ±0.05) -- 정수 ±0.5 로 판정하면 break 가 round 로 묻힌다.
* 규모 검사(P4, RED-1·YELLOW-8): 회사별 Σ대상신계약액(표 머리 단위 -> 백만원 환산, 천원=÷1000)을 같은 회사 다른 분기 중앙값과
  비교해 [0.25, 4] 밖이면 SCALE_OUTLIER, 표 머리 단위가 금액 단위가 아닌 '건' 인데 규모가 밴드 안이면 UNIT_LABEL(라벨 오기 추정).
  다른 분기가 3개 미만인 회사는 검사하지 않는다. 걸린 칸의 행에 `규모비`·`규모점검` 을 달아 마스터 플래그가 되게 한다.
  원문을 보고 확정한 칸은 source_errata.csv 에 **회사·분기 단위**(회차·채널 = `*`)로 등재한다:
    UNIT_SCALE_MISPRINT  표 머리 단위(백만원)와 실제 금액 규모가 1000배 어긋남(원문 인쇄 오기 추정). 값은 인쇄 그대로
    AMOUNT_BASIS_DIFFERS 원문 인쇄 그대로이고 오기라는 증거는 없으나 금액 산출 기준이 달라 다른 분기와 규모가 다름
  등재된 칸은 행에 `scale_misprint`(유형)·`scale_note`(근거)가 붙는다. 등재 안 된 SCALE_OUTLIER 는 selfcheck 에 `[미등재]` 로 남는다.

census 상태: FILLED / FILLED(vision) / ABSENT_IN_SOURCE(근거=표 머리·문장) / UNREADABLE / SCAN_PENDING 에
  NO_RAW_PDF(디스크에 그 분기 PDF 없음) · RAW_TRUNCATED(PDF 가 6장 앞에서 잘려 7장이 없음 -- 추출기가 마지막 절 제목·목차로
  스스로 판정하고, vision census 근거에 '잘린'/'truncated' 가 있어도 승격) 를 더했다 -- 둘은 "원천에 없다"가
  아니라 downloader 소관이라 ABSENT 로 뭉개지 않는다.
  우선순위: 텍스트 FILLED > vision FILLED > vision ABSENT/UNREADABLE > SCAN_PENDING.
  텍스트와 vision 이 같은 (회사, 분기)를 둘 다 가지면 텍스트를 쓰고 값 차이를 selfcheck.csv 에 남긴다.

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_persistency_channel.py
      (인자 없이 = 전체 + 쓰기. --companies/--periods 는 디버그용이라 쓰지 않는다. 가능하면 --no-write 와 함께.)
"""
from __future__ import annotations

import argparse
import csv
import glob
import io
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT_DIR = REPO / "data" / "persistency"
OUT_JSON = OUT_DIR / "persistency_channel.json"
OUT_CENSUS = OUT_DIR / "census.csv"
OUT_SELFCHECK = OUT_DIR / "selfcheck.csv"
MI_PATH = REPO / "management_indicators.json"
KICS_PATH = REPO / "kics_disclosure.json"
ERRATA_PATH = OUT_DIR / "source_errata.csv"  # 원문 인쇄 오기로 확정한 항등식 break 등재부 (사람이 원문 쪽을 보고 작성)
TRUNC_RE = re.compile(r"잘린|truncat", re.I)  # vision census 근거에 이 말이 있으면 RAW_TRUNCATED 로 승격
VISION_IDENTITY_MAP = {"ok_precision": "round", "n/a": "na"}  # V1 파일의 identity 어휘 -> 추출기 어휘(ok/round/trunc/break/na)
IDENT_CLASS = {"ok": "good", "round": "good", "trunc": "good", "break": "break", "na": "na"}  # 라벨 비교는 종류 단위(ok<->round 는 같은 종류)
TO_MW = {"천만원": 10.0, "백만원": 1.0, "억원": 100.0, "만원": 0.01, "천원": 0.001, "원": 1e-6}  # 표 머리 단위 -> 백만원 (규모 검사 전용, 값은 안 바꾼다)
SCALE_BAND = (0.25, 4.0)  # 같은 회사 다른 분기 중앙값 대비 Σ대상신계약액 비율이 이 밖이면 규모 이상
SCALE_MIN_OTHERS = 3      # 비교할 다른 분기가 이보다 적은 회사는 검사하지 않는다 (카카오페이처럼 3분기뿐인 신생사)
SCALE_ERRATA_TYPES = ("UNIT_SCALE_MISPRINT", "AMOUNT_BASIS_DIFFERS")

PERIODS = ["FY2023_Q2", "FY2023_Q4", "FY2024_Q2", "FY2024_Q4", "FY2025_Q2", "FY2025_Q4", "FY2026_Q2"]
ROUNDS = (13, 25, 37, 61)

CH11 = ["설계사", "개인대리점", "법인대리점_금융기관", "법인대리점_TM", "법인대리점_홈쇼핑", "법인대리점_기타",
        "직영_임직원", "직영_복합", "직영_다이렉트", "중개사", "기타"]
CH8 = ["설계사", "개인대리점", "법인대리점_금융기관", "법인대리점_TM", "법인대리점_홈쇼핑", "법인대리점_기타",
       "직영_복합", "직영_다이렉트"]
CH_ORDER = {c: i for i, c in enumerate(CH11)}

# kics_disclosure.json 에 없는 회사(캐롯손해 -- 2025 합병 소멸). PDF 가 디스크에 있는 칸만 그리드에 넣는다.
EXTRA_COMPANIES = {"KR1059": ("캐롯손해보험", "손해보험")}

# U+3161 = 한글 자모 `ㅡ` -- 라이나생명 2023.2Q 옛 통합 서식이 대시를 이 글자로 인쇄한다(눈으로는 `-` 와 같다).
DASHES = {"-", "\uff0d", "\u2013", "\u2014", "\u2500", "_", "\u2212", "\u30fc", "\u2015", "\u3161"}
WS_RE = re.compile(r"[\s\u3000\u00a0]+")
NUM_RE = re.compile(r"^(?:\(\d[\d,]*(?:\.\d+)?%?\)|[\u25b3\u25b2\u25bd\u25bc\-+]?\d[\d,]*(?:\.\d+)?%?|\d{1,3}\.\.\d{1,2}%?)$")
# 표 안에 `-` 대신 글자로 인쇄된 명시적 N/A (NH농협손해 2025.4Q·2026.2Q 의 유지율 칸 -- 대상신계약액=0 이라 `대상없음`)
NA_TEXT = {"대상없음"}
LABEL_RE = re.compile(r"^(유지계약액|대상신계약액)(?:\(?[A-Za-z]\)?|주?\d+\)?|\(\d+\))?$")
R_LABEL_RE = re.compile(r"^유지율(?:\(?[A-Za-z]\)?|주?\d+\)?|\(\d+\))?$")
LABEL_GLUE_RE = re.compile(r"^(유지계약액|대상신계약액|유지율)(?=[\d\-\u2010-\u2015\uff0d\u3161])")
HEAD_RE = re.compile(r"불완전판매비율.{0,24}?유지율.{0,6}?현황")
GROUP_WORDS = {"법인", "대리점", "법인대리점", "직영"}


def norm(s):
    return WS_RE.sub("", s or "")


def quarter_of(period):
    return f"{period[2:6]}.{period[-1]}Q"


def rel(p):
    try:
        return Path(p).resolve().relative_to(REPO).as_posix()
    except ValueError:
        return Path(p).as_posix()


def atomic_write(path, data, mode="w", encoding="utf-8", newline=None):
    path = Path(path)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, mode, encoding=None if "b" in mode else encoding, newline=newline) as f:
        f.write(data)
    os.replace(tmp, path)


# ======================================================================================
# 1. 페이지 토큰화 / 세로 괘선
# ======================================================================================
def _flush(cur, toks):
    if not cur:
        return
    text = "".join(c["c"] for c in cur)
    m = LABEL_GLUE_RE.match(text)
    parts = [cur[:len(m.group(1))], cur[len(m.group(1)):]] if m and len(text) > len(m.group(1)) else [cur]
    for part in parts:
        if not part:
            continue
        toks.append({
            "x0": round(min(c["bbox"][0] for c in part), 2), "y0": round(min(c["bbox"][1] for c in part), 2),
            "x1": round(max(c["bbox"][2] for c in part), 2), "y1": round(max(c["bbox"][3] for c in part), 2),
            "t": "".join(c["c"] for c in part),
            "cx": [(c["bbox"][0] + c["bbox"][2]) / 2 for c in part],
        })


def tokenize_page(page, gap_split=1.5):
    """rawdict 글자 -> 토큰. 공백(전각 U+3000 · NBSP 포함) · 큰 x 간격에서 끊고, `대상신계약액1,038,620` 처럼 라벨에
    숫자가 붙은 것은 라벨/숫자로 가른다."""
    toks = []
    for blk in page.get_text("rawdict").get("blocks", []):
        if blk.get("type", 0) != 0:
            continue
        for ln in blk.get("lines", []):
            chars = []
            for sp in ln.get("spans", []):
                chars.extend(sp.get("chars", []))
            cur = []
            for ch in chars:
                c = ch["c"]
                if c.isspace() or c in ("\u3000", "\u00a0"):
                    _flush(cur, toks)
                    cur = []
                    continue
                if cur and ch["bbox"][0] - cur[-1]["bbox"][2] > gap_split:
                    _flush(cur, toks)
                    cur = []
                cur.append(ch)
            _flush(cur, toks)
    return toks


def vertical_rules(page, min_len=6.0):
    out = []
    try:
        drawings = page.get_drawings()
    except Exception:  # noqa: BLE001
        return out
    for d in drawings:
        for it in d["items"]:
            k = it[0]
            if k == "l":
                p1, p2 = it[1], it[2]
                if abs(p1.x - p2.x) < 0.6 and abs(p1.y - p2.y) >= min_len:
                    out.append((round((p1.x + p2.x) / 2, 2), round(min(p1.y, p2.y), 2), round(max(p1.y, p2.y), 2)))
            elif k == "re":
                r = it[1]
                if r.width < 1.6 and r.height >= min_len:
                    out.append((round((r.x0 + r.x1) / 2, 2), round(r.y0, 2), round(r.y1, 2)))
            elif k == "qu":
                r = it[1].rect
                if r.width < 1.6 and r.height >= min_len:
                    out.append((round((r.x0 + r.x1) / 2, 2), round(r.y0, 2), round(r.y1, 2)))
    return out


def yc(t):
    return (t["y0"] + t["y1"]) / 2


def xc(t):
    return (t["x0"] + t["x1"]) / 2


def is_numlike(t):
    s = t["t"]
    return s in DASHES or s in NA_TEXT or bool(NUM_RE.match(s))


def dedupe(tokens):
    """같은 글자가 같은 자리에 두 번 그려진 PDF(한화생명)를 한 번으로."""
    toks = sorted(tokens, key=lambda t: (round(t["y0"]), t["x0"]))
    out = []
    for t in toks:
        if not any(o["t"] == t["t"] and abs(o["x0"] - t["x0"]) < 1.5 and abs(o["y0"] - t["y0"]) < 1.5 for o in out[-10:]):
            out.append(t)
    return out


def cluster_rows(tokens, tol=5.5):
    rows = []
    for t in sorted(tokens, key=lambda t: (yc(t), t["x0"])):
        if rows and abs(rows[-1]["y"] - yc(t)) <= tol:
            rows[-1]["tokens"].append(t)
            rows[-1]["y"] = sum(yc(x) for x in rows[-1]["tokens"]) / len(rows[-1]["tokens"])
        else:
            rows.append({"y": yc(t), "tokens": [t]})
    for r in rows:
        r["tokens"].sort(key=lambda t: t["x0"])
    return rows


# ======================================================================================
# 2. 행 앵커 (R=유지율 / M=유지계약액 / D=대상신계약액)
# ======================================================================================
def label_kind(n):
    m = LABEL_RE.match(n)
    if not m:
        return None
    return "M" if m.group(1) == "유지계약액" else "D"


def find_anchors(tokens):
    rows = cluster_rows(tokens)
    anchors = []
    round_heads = []
    for r in rows:
        ts = r["tokens"]
        names = [norm(t["t"]) for t in ts]
        if any(n in ("=", "/", "\u00d7", "x", "X") for n in names):
            continue  # 주석 수식 `유지율 = 유지계약액 / 대상신계약액 x 100`
        got = False
        for i, (t, n) in enumerate(zip(ts, names)):
            k = label_kind(n)
            if k and i + 1 < len(ts) and is_numlike(ts[i + 1]):
                if len([x for x in ts[i + 1:] if is_numlike(x)]) >= 2:
                    anchors.append({"type": k, "y": r["y"], "label_x1": t["x1"], "label_x0": t["x0"], "round": None})
                    got = True
                break
        if got:
            continue
        lab = None
        for i, (t, n) in enumerate(zip(ts, names)):
            m = re.match(r"^(\d{2})회차$", n)
            if m:
                lab = ("round", int(m.group(1)), t, i)
                break
            if n == "회차" and i > 0 and re.fullmatch(r"\d{2}", names[i - 1]):
                lab = ("round", int(names[i - 1]), ts[i - 1], i)
                break
        if lab is None:
            for i, (t, n) in enumerate(zip(ts, names)):
                if R_LABEL_RE.match(n):
                    lab = ("rate", None, t, i)
                    break
        if lab is not None:
            kind, rnd, t, i = lab
            nn = [x for x in ts if x["x0"] >= t["x1"] + 0.5 and is_numlike(x) and x is not t
                  and not re.fullmatch(r"\d\)", norm(x["t"]))]
            lx1 = t["x1"]
            for x in ts[i + 1:i + 3]:
                if re.fullmatch(r"\d\)", norm(x["t"])) and x["x0"] - lx1 < 4:
                    lx1 = x["x1"]
            if len(nn) >= 2:
                anchors.append({"type": "R", "y": r["y"], "label_x1": lx1, "label_x0": t["x0"], "round": rnd})
            elif kind == "round":
                round_heads.append((r["y"], rnd))
    anchors.sort(key=lambda a: a["y"])
    return anchors, round_heads, rows


def positional_fill(anchors, rows):
    """M/D 라벨이 조각난 표(`유지`/`계약액` 세로 분리, 악사·하나손보): R 다음 두 개의 순수 숫자행을 M, D 로."""
    Rs = [a for a in anchors if a["type"] == "R"]
    if not Rs:
        return anchors
    ms_ds = [a for a in anchors if a["type"] in "MD"]
    xlab = max([a["label_x1"] for a in ms_ds] or [a["label_x1"] for a in Rs])
    drows = []
    for r in rows:
        if any(abs(r["y"] - a["y"]) < 3.0 for a in anchors):
            continue
        data = [t for t in r["tokens"] if t["x0"] >= xlab + 1.0]
        if len(data) >= 3 and all(is_numlike(t) for t in data):
            drows.append(r)
    added = []
    for i, a in enumerate(Rs):
        lo = a["y"]
        hi = Rs[i + 1]["y"] if i + 1 < len(Rs) else lo + 400
        have = {b["type"]: b for b in ms_ds if lo < b["y"] < hi}
        cand = [r for r in drows if lo + 6 < r["y"] < hi - 6]
        if "M" in have and "D" in have:
            continue
        base = {"label_x1": xlab, "label_x0": xlab, "round": None, "positional": True}
        if "M" not in have and "D" not in have:
            if len(cand) >= 2:
                added.append({"type": "M", "y": cand[0]["y"], **base})
                added.append({"type": "D", "y": cand[1]["y"], **base})
        elif "M" in have:
            c2 = [r for r in cand if r["y"] > have["M"]["y"] + 6]
            if c2:
                added.append({"type": "D", "y": c2[0]["y"], **base})
        else:
            c2 = [r for r in cand if r["y"] < have["D"]["y"] - 6]
            if c2:
                added.append({"type": "M", "y": c2[-1]["y"], **base})
    anchors = anchors + added
    anchors.sort(key=lambda a: a["y"])
    return anchors


def analyze_page(tokens):
    toks = dedupe(tokens)
    anchors, round_heads, rows = find_anchors(toks)
    if not anchors:
        return None
    anchors = positional_fill(anchors, rows)
    Ms = [a["y"] for a in anchors if a["type"] == "M"]
    Ds = [a["y"] for a in anchors if a["type"] == "D"]
    gaps = []
    for m in Ms:
        nd = [d for d in Ds if d > m]
        if nd:
            gaps.append(nd[0] - m)
    h = median(gaps) if gaps else 16.0
    xl = max([a["label_x1"] for a in anchors if a["type"] in "MD"] or [a["label_x1"] for a in anchors])
    for a in list(anchors):  # M 만 있고 바로 위 R 행이 없는 블록 -> 라벨 없는 R 행을 위치로
        if a["type"] != "M":
            continue
        if any(b["type"] == "R" and a["y"] - 1.7 * h < b["y"] < a["y"] - 0.4 * h for b in anchors):
            continue
        ry = a["y"] - h
        cand = [t for t in toks if abs(yc(t) - ry) <= 0.45 * h and is_numlike(t) and xc(t) > xl + 2]
        if len(cand) >= 2:
            anchors.append({"type": "R", "y": ry, "label_x1": a["label_x1"], "label_x0": a["label_x0"], "round": None, "synthetic": True})
    anchors.sort(key=lambda a: a["y"])
    for y, rnd in round_heads:  # `< 13회차 >` 처럼 값 없는 제목행 -> 아래 첫 R 행의 회차
        nxt = [a for a in anchors if a["type"] == "R" and a["y"] > y and a["round"] is None and a["y"] - y < 90]
        if nxt:
            nxt[0]["round"] = rnd
    ys = [a["y"] for a in anchors]
    return {"toks": toks, "anchors": anchors, "h": h, "y_top": min(ys) - 0.6 * h, "y_bot": max(ys) + 0.6 * h,
            "x_label_right": xl}


# ======================================================================================
# 3. 열 경계 / 칸 배정
# ======================================================================================
def union_len(segs, lo, hi, gap=2.5):
    segs = sorted((max(a, lo), min(b, hi)) for a, b in segs if b > lo and a < hi)
    tot = 0.0
    cur = None
    for a, b in segs:
        if cur is None:
            cur = [a, b]
        elif a <= cur[1] + gap:
            cur[1] = max(cur[1], b)
        else:
            tot += cur[1] - cur[0]
            cur = [a, b]
    if cur:
        tot += cur[1] - cur[0]
    return tot


def column_bounds(vr, y_top, y_bot, x_min, cover=0.6, xtol=1.6):
    cl = []
    for x, y0, y1 in sorted(vr):
        if cl and abs(cl[-1]["x"] - x) <= xtol:
            cl[-1]["segs"].append((y0, y1))
            cl[-1]["xs"].append(x)
        else:
            cl.append({"x": x, "xs": [x], "segs": [(y0, y1)]})
    need = cover * (y_bot - y_top)
    out = [sum(c["xs"]) / len(c["xs"]) for c in cl if union_len(c["segs"], y_top, y_bot) >= need]
    return [x for x in out if x >= x_min]


def page_bounds(vr, pa):
    xl = pa["x_label_right"]
    b = column_bounds(vr, pa["y_top"], pa["y_bot"], xl - 1.5)
    notes = []
    dt = [t for t in pa["toks"] if is_numlike(t) and xc(t) > xl + 1
          and any(abs(yc(t) - a["y"]) <= 0.45 * pa["h"] for a in pa["anchors"])]
    if len(b) >= 2 and dt:
        xmax = max(t["x1"] for t in dt)
        xmin = min(t["x0"] for t in dt)
        if xmax > b[-1] + 1.0:
            b.append(xmax + 4.0)
            notes.append("right-edge-added")
        if xmin < b[0] - 1.0:
            b.insert(0, xmin - 4.0)
            notes.append("left-edge-added")
    return b, notes


RATE_OK = re.compile(r"^\d{1,3}(?:\.\d+)?%?$")
AMT_OK = re.compile(r"^(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$")


def valid_token(text, ftype):
    if text in DASHES or text in NA_TEXT:
        return True
    return bool((RATE_OK if ftype == "R" else AMT_OK).match(text))


def col_of(x, bounds):
    for j in range(len(bounds) - 1):
        if bounds[j] <= x < bounds[j + 1]:
            return j
    return None


def split_by_bounds(t, bounds, ftype):
    """칸이 붙어 한 토큰이 된 경우(`524,581262,552`)를 문자 좌표로 열 경계에서 쪼갠다. 조각이 전부 유효 숫자일 때만."""
    text, cx = t["t"], t["cx"]
    if len(text) != len(cx):
        return None
    cols = [col_of(x, bounds) for x in cx]
    if any(c is None for c in cols) or len(set(cols)) < 2:
        return None
    segs = []
    for ch, x, c in zip(text, cx, cols):
        if segs and segs[-1][0] == c:
            segs[-1][1].append(ch)
            segs[-1][2].append(x)
        else:
            segs.append([c, [ch], [x]])
    parts = []
    for c, chs, xs in segs:
        s = "".join(chs)
        if not valid_token(s, ftype):
            return None
        parts.append({"x0": min(xs) - 2, "x1": max(xs) + 2, "y0": t["y0"], "y1": t["y1"], "t": s, "cx": xs})
    return parts


def assign_cells(pa, bounds):
    """숫자 토큰 -> 가장 가까운 앵커 행(반 피치 이내) -> 열 경계로 칸. 붙은 토큰은 쪼갠다."""
    anchors, toks, h = pa["anchors"], pa["toks"], pa["h"]
    ys = [a["y"] for a in anchors]
    per = [[] for _ in anchors]
    xmin = bounds[0] - 2
    dropped = []  # 데이터 행 위치에 있는데 숫자도 대시도 아니라 버려진 토큰 -- note 로 올려 `ㅡ` 같은 미지의 대시가 조용히 묻히지 않게
    for t in toks:
        if xc(t) < xmin:
            continue
        numlike = is_numlike(t)
        if not numlike and xc(t) > bounds[-1] + 3:
            continue
        best = min(range(len(anchors)), key=lambda i: abs(ys[i] - yc(t)))
        neigh = [abs(ys[best] - y) for j, y in enumerate(ys) if j != best]
        lim = min(0.55 * (min(neigh) if neigh else h), 0.6 * h)
        if abs(ys[best] - yc(t)) > lim:
            continue
        if not numlike:
            if t["t"] != "%" and not re.fullmatch(r"\d{1,2}\)", norm(t["t"])):  # 따로 떨어진 `%` · 각주 번호는 정상
                dropped.append(t["t"])
            continue
        per[best].append(t)
    cells = []
    nleft = 0
    for a, ts in zip(anchors, per):
        ftype = "R" if a["type"] == "R" else "A"
        cell = {}
        for t in ts:
            parts = [t]
            if not valid_token(t["t"], ftype):
                parts = split_by_bounds(t, bounds, ftype) or [t]
            for p in parts:
                c = col_of(xc(p), bounds)
                if c is None:
                    nleft += 1
                    continue
                cell.setdefault(c, []).append(p)
        cells.append(cell)
    return cells, nleft, dropped


# ======================================================================================
# 4. 열 이름(채널) / 단위
# ======================================================================================
def header_labels(pa, bounds):
    """열 구간마다 머리 토큰을 모아 이어 붙인다. 가로로 여러 열에 걸친 토큰(`복합8)다이렉트9)`)은 문자 좌표로 쪼갠다."""
    toks, h = pa["toks"], pa["h"]
    first_y = min(a["y"] for a in pa["anchors"])
    y_bot = first_y - 0.5 * h
    unit_rows = [yc(t) for t in toks if "단위" in norm(t["t"]) and y_bot - 170 < yc(t) < y_bot]
    y_top = (max(unit_rows) + 4) if unit_rows else (y_bot - 110)
    cand = [t for t in toks if y_top <= yc(t) < y_bot and bounds[0] <= xc(t) <= bounds[-1]
            and not re.fullmatch(r"\d{1,2}\)?", norm(t["t"]))]
    N = len(bounds) - 1
    if not cand:
        return [""] * N
    ymin = min(yc(t) for t in cand)
    cols = [[] for _ in range(N)]
    for t in cand:
        if norm(t["t"]) in GROUP_WORDS and yc(t) <= ymin + 3.0:
            continue  # 법인대리점/직영 묶음 머리
        text, cx = t["t"], t["cx"]
        if len(text) == len(cx):
            cs = [col_of(x, bounds) for x in cx]
            if None not in cs and len(set(cs)) > 1:
                segs = []
                for ch, c in zip(text, cs):
                    if segs and segs[-1][0] == c:
                        segs[-1][1].append(ch)
                    else:
                        segs.append([c, [ch]])
                for c, chs in segs:
                    cols[c].append({"t": "".join(chs), "x0": t["x0"], "y0": t["y0"], "y1": t["y1"]})
                continue
        c = col_of(xc(t), bounds)
        if c is not None:
            cols[c].append(t)
    labels = []
    for ts in cols:
        kept = []
        for t in ts:
            nt = norm(t["t"])
            if any(o is not t and abs(o["x0"] - t["x0"]) <= 3 and abs(yc(o) - yc(t)) <= 5
                   and len(norm(o["t"])) > len(nt) and norm(o["t"]).startswith(nt) for o in ts):
                continue  # 같은 글자의 각주 없는 중복 레이어
            kept.append(t)
        kept.sort(key=lambda t: (round(yc(t) / 3.0), t["x0"]))
        labels.append("".join(t["t"] for t in kept))
    return labels


def canon_label(txt):
    n0 = re.sub(r"[\d\)\(주]+", "", norm(txt))
    u = n0.upper()
    if "설계사" in n0:
        return "설계사"
    if "홈쇼핑" in n0 or "쇼핑" in n0 or ("홈" in n0 and "핑" in n0):
        return "법인대리점_홈쇼핑"
    if "TM" in u or u == "T":
        return "법인대리점_TM"
    if "임직" in n0:
        return "직영_임직원"
    if "복합" in n0:
        return "직영_복합"
    if "다이렉트" in n0 or "렉트" in n0 or "다이" in n0:
        return "직영_다이렉트"
    if "중개" in n0 or "중계" in n0:
        return "중개사"
    if "방카" in n0 or "금융" in n0 or "기관" in n0 or "보험대리점" in n0 or "보험점" in n0:
        return "법인대리점_금융기관"
    if "개인" in n0:
        return "개인대리점"
    if n0 in ("기타", "기"):
        return "기타?"
    return None


def map_channels(labels):
    seen_direct = False
    out = []
    for c in (canon_label(x) for x in labels):
        if c == "기타?":
            c = "기타" if seen_direct else "법인대리점_기타"
        if c and (c.startswith("직영_") or c == "중개사"):
            seen_direct = True
        out.append(c)
    ok = all(c is not None for c in out) and len(set(out)) == len(out)
    if ok:
        idx = [CH_ORDER[c] for c in out]
        ok = all(idx[i] < idx[i + 1] for i in range(len(idx) - 1))
    return out, ok


UNIT_RE = re.compile(r"(천만원|백만원|억원|만원|천원|원|건)")


def unit_of(pa):
    toks = pa["toks"]
    first_y = min(a["y"] for a in pa["anchors"])
    ys = [yc(t) for t in toks if yc(t) < first_y and "단위" in norm(t["t"])]
    if not ys:
        return None, None
    y = max(ys)
    seg = sorted([t for t in toks if abs(yc(t) - y) <= 3.5], key=lambda t: t["x0"])
    txt = "".join(t["t"] for t in seg)
    m = re.search(r"단위[:：]?(.*)", txt)
    tail = m.group(1) if m else txt
    mm = UNIT_RE.search(tail)
    if mm:
        return mm.group(1), txt
    if re.match(r"\s*천(?![만원])", tail):  # 삼성생명 2023.4Q `(단위: 천, %)` -- `천` 만 인쇄(천원; 같은 회사 백만원 분기 대비 값이 1000배라 천원)
        return "천원", txt
    return None, txt


# ======================================================================================
# 5. 값 해석 / 항등식 / 보정
# ======================================================================================
def interpret(field, text):
    """-> (state, value, alt). state: ok | dash | malformed | bad. alt = 항등식으로만 채택할 대체 읽기."""
    if text in DASHES or text in NA_TEXT:
        return "dash", None, None
    z = text.strip()
    neg = False
    if z and z[0] in "\u25b3\u25b2\u25bd\u25bc":
        neg, z = True, z[1:]
    if z.startswith("(") and z.endswith(")"):
        neg, z = True, z[1:-1]
    if field == "유지율":
        if RATE_OK.match(z):
            v = float(z.rstrip("%"))
            return "ok", (-v if neg else v), None
        m = re.fullmatch(r"(\d{1,3}),(\d{1,2})%?", z)  # `63,43` (쉼표가 소수점)
        if m:
            return "malformed", None, float(f"{m.group(1)}.{m.group(2)}")
        m = re.fullmatch(r"(\d{1,3})\.\.(\d{1,2})%?", z)  # `10..00` (마침표 두 개)
        if m:
            return "malformed", None, float(f"{m.group(1)}.{m.group(2)}")
        return "bad", None, None
    if AMT_OK.match(z):
        v = float(z.replace(",", ""))
        alt = float(z.replace(".", "")) if re.fullmatch(r"\d{1,3}\.\d{3}", z) else None
        return "ok", (-v if neg else v), alt
    return "malformed", None, None  # `319,76` 처럼 천단위가 깨진 것 -- 복원 불가


def decimals_of(s):
    m = re.search(r"\.(\d+)", s or "")
    return len(m.group(1)) if m else 0


def identity_status(r, m, d, dec, half=0.5):
    """-> (status, dev). dev = r - 100*m/d. half = 금액 반올림 반단위(정수 백만원 인쇄 0.5, 소수 n자리 인쇄 0.5*10^-n)."""
    if r is None or m is None or d is None or d == 0:
        return "na", None
    dev = r - 100.0 * m / d
    if abs(dev) <= max(0.06, 0.5 * 10 ** (-dec) + 0.011):
        return "ok", dev
    lo = 100.0 * (m - half) / (d + half)
    hi = 100.0 * (m + half) / (d - half) if d - half > 0 else 1e9
    pt = 0.5 * 10 ** (-dec) + 0.011
    if lo - pt <= r <= hi + pt:
        return "round", dev
    if -(10 ** (-dec)) - 0.011 <= dev <= 0.0:
        return "trunc", dev
    return "break", dev


GOOD = ("ok", "round", "trunc")


def amount_half_unit(*amts):
    """금액 인쇄 소수 자릿수(float repr 에서 뒤쪽 0 제외)로 반올림 반단위: 정수 인쇄 0.5, 소수 1자리 0.05, 2자리 0.005 ...
    (뒤쪽 0 인쇄 `756.0` 은 정수로 보므로 실제보다 느슨한 쪽으로만 틀린다)"""
    n = 0
    for a in amts:
        s = repr(float(a)) if a is not None else ""
        if "." in s and "e" not in s:
            n = max(n, len(s.split(".")[1].rstrip("0")))
    return 0.5 * 10 ** (-n)


def recheck_identity(r):
    """라벨을 믿지 않고 (유지율, 유지계약액, 대상신계약액, 표기소수)로 항등식을 다시 계산한다 -- 텍스트·vision 공통.
    표기소수가 빈 vision 행은 유지율 값의 소수 자릿수로 추정하고, 금액 반올림 구간은 금액의 소수 자릿수에 맞춘다
    (소수 1자리 금액이 정수 백만원 구간으로 판정돼 break 가 round 로 묻히던 KR0097 2024.4Q 37 설계사 1칸이 전 행 중 유일한 영향). -> (status, dev)"""
    rate, m, d = r.get("유지율"), r.get("유지계약액"), r.get("대상신계약액")
    dec = r.get("유지율_표기소수")
    if dec is None:
        dec = decimals_of(repr(rate)) if isinstance(rate, float) else 0
    if re.search(r"(?:^|; )R:", r.get("repair") or ""):
        dec = max(dec, 2)  # resolve_cell 이 유지율을 보정한 칸은 소수 2자리로 판정했다
    return identity_status(rate, m, d, dec, half=amount_half_unit(m, d))


def resolve_cell(tok_r, tok_m, tok_d):
    """세 토큰 -> 값 · 항등식 · 보정. 반환 dict."""
    info = {}
    st = {}
    val = {}
    alt = {}
    for key, field, tok in (("R", "유지율", tok_r), ("M", "유지계약액", tok_m), ("D", "대상신계약액", tok_d)):
        if tok is None:
            st[key], val[key], alt[key] = "blank", None, None
        else:
            st[key], val[key], alt[key] = interpret(field, tok)
    dec = decimals_of(tok_r)
    ident, dev = identity_status(val["R"], val["M"], val["D"], dec)
    repair = None
    needs = ident == "break" or (st["R"] == "malformed" and alt["R"] is not None)
    if needs and any(alt[k] is not None for k in "RMD"):
        # 대체 읽기 조합 중 항등식을 만족하는 첫 번째만 채택 (확증 없이는 안 바꾼다)
        for combo in ((1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 1, 1), (1, 1, 0), (1, 0, 1), (1, 1, 1)):
            cand = {}
            for flag, key in zip(combo, "RMD"):
                if flag and alt[key] is None:
                    break
                cand[key] = alt[key] if flag else val[key]
            else:
                rr, mm, dd = cand["R"], cand["M"], cand["D"]
                s2, d2 = identity_status(rr, mm, dd, 2 if combo[0] else dec)
                if s2 in GOOD:
                    val.update(cand)
                    ident, dev = s2, d2
                    repair = "; ".join(f"{k}:{tok}->{val[k]:g}" for flag, k, tok in
                                       zip(combo, "RMD", (tok_r, tok_m, tok_d)) if flag)
                    for flag, key in zip(combo, "RMD"):
                        if flag:
                            st[key] = "repaired"
                    break
    info.update({"val": val, "st": st, "ident": ident, "dev": dev, "dec": dec, "repair": repair})
    return info


# ======================================================================================
# 6. 표 그룹 파싱 (페이지 묶음 -> 블록 -> 채널 행)
# ======================================================================================
def parse_group(page_data):
    """page_data: [(pno, tokens, vrules)]. 연속 페이지 한 묶음. -> dict(rows=..., notes=...) 또는 None."""
    notes = []
    pas = []
    for pno, tokens, vr in page_data:
        pa = analyze_page(tokens)
        if pa is None:
            continue
        b, n = page_bounds(vr, pa)
        if n:
            notes.append(f"p{pno}:{','.join(n)}")
        pas.append({"pno": pno, "pa": pa, "bounds": b})
    if not pas:
        return None
    with_b = [x for x in pas if len(x["bounds"]) >= 2]
    if not with_b:
        return {"error": "열 경계(세로 괘선)를 못 찾음", "notes": notes, "pnos": [x["pno"] for x in pas]}
    model = next((x for x in with_b if any("설계사" in norm(t["t"]) for t in x["pa"]["toks"])), with_b[0])
    N = len(model["bounds"]) - 1
    seq = []
    last_b = None
    for x in pas:
        b = x["bounds"] if len(x["bounds"]) >= 2 else last_b
        if b is None:
            continue
        last_b = b
        if len(b) - 1 != N:
            notes.append(f"p{x['pno']}:열 수 {len(b) - 1} != {N} (이 쪽 행은 제외)")
            continue
        cells, nleft, dropped = assign_cells(x["pa"], b)
        if nleft:
            notes.append(f"p{x['pno']}:표 밖 숫자 토큰 {nleft}개 무시")
        if dropped:
            notes.append(f"p{x['pno']}:표 안 비숫자 토큰 {len(dropped)}개 무시 {sorted(set(dropped))[:6]}")
        for a, c in zip(x["pa"]["anchors"], cells):
            seq.append({"pno": x["pno"], "type": a["type"], "y": a["y"], "round": a.get("round"), "cells": c})
    blocks = []
    cur = None
    for r in seq:
        if r["type"] == "R":
            cur = {"R": r, "M": None, "D": None, "round": r["round"]}
            blocks.append(cur)
        else:
            if cur is None or cur[r["type"]] is not None:
                cur = {"R": None, "M": None, "D": None, "round": None}
                blocks.append(cur)
                notes.append(f"p{r['pno']}:R 행 없는 블록({r['type']})")
            cur[r["type"]] = r
    for i, bk in enumerate(blocks):
        if bk["round"] is None:
            bk["round"] = ROUNDS[i] if i < len(ROUNDS) else None
    rounds = [bk["round"] for bk in blocks]
    if rounds != list(ROUNDS):
        notes.append(f"회차 순서={rounds}")
    labels = header_labels(model["pa"], model["bounds"])
    codes, ok = map_channels(labels)
    method = "label"
    if not ok:
        if N == 11:
            codes, method = list(CH11), "template11"
        elif N == 8:
            codes, method = list(CH8), "template8"
        else:
            codes, method = [f"UNMAPPED_{j + 1}" for j in range(N)], "unmapped"
    unit, unit_txt = unit_of(model["pa"])
    rows = build_rows(blocks, N, codes, labels)
    return {"rows": rows, "N": N, "codes": codes, "labels": labels, "method": method, "unit": unit,
            "unit_txt": unit_txt, "notes": notes, "pnos": [x["pno"] for x in pas], "n_blocks": len(blocks)}


def build_rows(blocks, N, codes, labels):
    out = []
    for bk in blocks:
        for j in range(N):
            toks = {}
            multi = {}
            wrap = {}
            for key in "RMD":
                row = bk[key]
                ts = row["cells"].get(j) if row is not None else None
                if not ts:
                    toks[key] = None
                elif len(ts) > 1:
                    toks[key] = None
                    parts = [t["t"] for t in sorted(ts, key=lambda t: (round(yc(t) / 3.0), t["x0"]))]
                    multi[key] = f"{key}:{parts}"
                    wrap[key] = parts
                else:
                    toks[key] = ts[0]["t"]
            info = resolve_cell(toks["R"], toks["M"], toks["D"])
            if len(wrap) == 1:
                # 좁은 칸에서 숫자가 두 줄로 꺾인 경우(`1,204,6` / `34` -> 1,204,634): 이어 붙인 값이 항등식으로
                # 확증될 때만 채택한다. 확증이 안 되면(한화손해 2023.4Q `319,76` 처럼 글자가 빠진 원문) 비워 둔다.
                (wkey, wparts), = wrap.items()
                cand = "".join(wparts)
                if valid_token(cand, "R" if wkey == "R" else "A") and cand not in DASHES:
                    t2 = dict(toks)
                    t2[wkey] = cand
                    info2 = resolve_cell(t2["R"], t2["M"], t2["D"])
                    if info2["ident"] in GOOD and all(info2["val"][k] is not None for k in "RMD"):
                        info2["st"][wkey] = "repaired"
                        info2["repair"] = "; ".join(x for x in (info2["repair"], f"{wkey}:wrap{wparts}->{cand}") if x)
                        info = info2
                        toks = t2
                        multi.pop(wkey)
            st = info["st"]
            names = {"R": "유지율", "M": "유지계약액", "D": "대상신계약액"}
            dash_f = [names[k] for k in "RMD" if st[k] == "dash"]
            blank_f = [names[k] for k in "RMD" if st[k] == "blank"]
            bad_f = [f"{names[k]}={toks[k]!r}" for k in "RMD" if st[k] in ("bad", "malformed")] + list(multi.values())
            na_txt = [toks[k] for k in "RMD" if toks[k] in NA_TEXT]
            out.append({
                "회차": bk["round"], "col": j, "채널": codes[j], "채널_원문": labels[j] if j < len(labels) else "",
                "유지율": info["val"]["R"], "유지계약액": info["val"]["M"], "대상신계약액": info["val"]["D"],
                "dash_fields": dash_f, "blank_fields": blank_f, "malformed": bad_f, "repair": info["repair"],
                "na_text": na_txt[0] if na_txt else None,
                "dec": info["dec"], "identity": info["ident"], "dev": info["dev"],
                "page": (bk["R"] or bk["M"] or bk["D"])["pno"],
            })
    return out


def group_score(res):
    return sum(1 for r in res["rows"] if any(r[k] is not None for k in ("유지율", "유지계약액", "대상신계약액")))


# ======================================================================================
# 7. PDF 한 개 -> 칸 결과
# ======================================================================================
def has_images_low_text(page, nchar):
    try:
        return nchar < 400 and len(page.get_images()) >= 1
    except Exception:  # noqa: BLE001
        return False


def na_evidence(nt):
    """`불완전판매비율 ... 유지율 현황` 머리 뒤 80자 안에 `해당사항 없음` 이 있으면 그 문장 -- 표 없음의 원문 근거."""
    for m in HEAD_RE.finditer(nt):
        win = nt[m.end(): m.end() + 80]
        if "해당사항없음" in win and "설계사" not in win:
            return nt[max(0, m.start() - 8): m.end() + 40]
    return None


def scan_pdf(pdf_path):
    import fitz  # noqa: PLC0415  (--help 에서는 PyMuPDF 가 없어도 되게)

    doc = fitz.open(str(pdf_path))
    n = len(doc)
    info = {"n": n, "chars": 0, "cand": [], "na": None, "na_page": None, "img_low": [], "head_pages": [],
            "sec7": False, "texts_low": 0, "last_head": None, "toc_roman": 0}
    for i in range(n):
        try:
            page = doc[i]
            t = page.get_text()
        except Exception:  # noqa: BLE001
            t = ""
            page = None
        nc = len(t.strip())
        info["chars"] += nc
        if nc < 60:
            info["texts_low"] += 1
        if page is not None and has_images_low_text(page, nc):
            info["img_low"].append(i + 1)
        if nc == 0:
            continue
        nt = norm(t)
        if "회차" in nt and (("유지계약액" in nt and "대상신계약액" in nt)
                            or ("유지율" in nt and "설계사" in nt and "법인대리점" in nt)):
            info["cand"].append(i + 1)
        if HEAD_RE.search(nt):
            info["head_pages"].append(i + 1)
            ev = na_evidence(nt)
            if ev and not info["na"]:
                info["na"], info["na_page"] = ev, i + 1
        if re.search(r"(?:^|\n)\s*7-\d{1,2}[\.\)]", t):
            info["sec7"] = True
        for m in re.finditer(r"(?:^|\n)\s*(\d)-(\d{1,2})[\.\)]", t):
            info["last_head"] = (f"{m.group(1)}-{m.group(2)}", i + 1)  # 문서 순서상 마지막 절 제목 (잘림 판정 근거)
        if i < 6 and not info["toc_roman"] and re.search("[ⅦⅧ]", t):  # 목차가 Ⅶ·Ⅷ 를 열거하는 쪽
            info["toc_roman"] = i + 1
    return doc, info


def truncation_evidence(info, n):
    """표를 못 찾았고, `7-n.` 절 제목이 하나도 없고, 본문 마지막 절이 6장 이하이며, 이미지 쪽이 소수(표지·차트)면
    스캔본이 아니라 7장 앞에서 잘린 사본이다. -> 근거 문자열 또는 None"""
    lh = info.get("last_head")
    if info["sec7"] or info["head_pages"] or not lh or int(lh[0].split("-")[0]) >= 7:
        return None
    if len(info["img_low"]) > max(5, 0.2 * n):
        return None
    ev = f"PDF {n}쪽, 본문 마지막 절 제목 {lh[0]}(p{lh[1]}) 이후 절 없음(`7-n.` 절 제목 0개)"
    if info.get("toc_roman"):
        ev += f", 목차(p{info['toc_roman']})는 Ⅶ·Ⅷ 열거"
    return ev + " -> 유지율 표가 있는 7장이 파일에 없는 잘린 사본"


def find_truncation_ticket(code, q):
    """잘린 사본 건으로 downloader 에 발주한 티켓(있으면): 파일명에 `<코드>_<분기>` 와 `truncat` 이 들어 있는 것."""
    hits = []
    for sub in ("downloader", "_resolved"):
        hits += glob.glob(str(REPO / "inbox" / sub / f"*{code}_{q}*truncat*.md"))
    return [Path(h).resolve().relative_to(REPO).as_posix() for h in sorted(hits)]


def process_pdf(code, period, pdf_path):
    """-> dict(status, mode, pages, rows, evidence, unit, notes ...)"""
    res = {"status": None, "mode": "text", "pages": [], "rows": [], "evidence": "", "unit": None, "notes": [],
           "N": None, "method": None, "file": rel(pdf_path), "dup": 0}
    try:
        doc, info = scan_pdf(pdf_path)
    except Exception as e:  # noqa: BLE001
        res.update(status="UNREADABLE", evidence=f"PDF 열기 실패: {type(e).__name__}: {e}")
        return res
    n = info["n"]
    res["n_pages"], res["chars"] = n, info["chars"]
    pages = sorted({p + d for p in info["cand"] for d in (-1, 0, 1) if 1 <= p + d <= n})
    groups = []
    if pages:
        data = {}
        for p in pages:
            page = doc[p - 1]
            data[p] = (p, tokenize_page(page), vertical_rules(page))
        cur = []
        for p in pages:
            if analyze_page(data[p][1]) is None:
                if cur:
                    groups.append(cur)
                cur = []
                continue
            if cur and p != cur[-1] + 1:
                groups.append(cur)
                cur = []
            cur.append(p)
        if cur:
            groups.append(cur)
        parsed = []
        for g in groups:
            # 1-2 요약표(13/25/37/... 회차 한 줄씩)는 R 행만 있다 -- 유지계약액/대상신계약액 행이 하나라도 있어야 채널표
            if not any(a["type"] in "MD" for p in g for a in analyze_page(data[p][1])["anchors"]):
                continue
            r = parse_group([data[p] for p in g])
            if r is not None and "rows" in r:
                parsed.append(r)
            elif r is not None:
                res["notes"].append(f"묶음 {g}: {r.get('error')}")
        if parsed:
            parsed.sort(key=lambda r: -group_score(r))
            best = parsed[0]
            res["dup"] = len(parsed) - 1
            if len(parsed) > 1:
                res["notes"].append("표가 여러 쪽 묶음에 있음: " + ", ".join(
                    f"p{','.join(map(str, r['pnos']))}(값 {group_score(r)}칸)" for r in parsed))
                same = all(_rows_equal(parsed[0]["rows"], r["rows"]) for r in parsed[1:])
                res["notes"].append("다른 묶음과 값 동일" if same else "다른 묶음과 값이 다름 -- 확인 필요")
            res.update(rows=best["rows"], pages=best["pnos"], unit=best["unit"], unit_txt=best["unit_txt"],
                       N=best["N"], method=best["method"])
            res["notes"].extend(best["notes"])
            if best["method"] != "label":
                res["notes"].append(f"채널 매핑={best['method']} (머리 라벨 {best['labels']})")
            if best["n_blocks"] != 4:
                res["notes"].append(f"블록 {best['n_blocks']}개")
            nonnull = group_score(best)
            doc.close()
            if nonnull == 0:
                res["status"] = "ABSENT_IN_SOURCE"
                res["evidence"] = (f"표는 있으나({rel(pdf_path)} p{','.join(map(str, best['pnos']))}) "
                                   f"{best['N']}열 x 4회차 x 3행 전부 '-' (값 없음)")
            else:
                res["status"] = "FILLED"
                res["evidence"] = f"p{','.join(map(str, best['pnos']))} {best['N']}열 채널매핑={best['method']}"
            return res
    doc.close()
    # --- 표를 못 찾음: 이유를 가른다 ---
    if info["na"]:
        res.update(status="ABSENT_IN_SOURCE", evidence=f"p{info['na_page']} 원문: {info['na']}")
        return res
    if info["chars"] == 0:
        res.update(status="SCAN_PENDING", mode="scan",
                   evidence=f"텍스트층 0자 PDF({n}쪽) -- 렌더 판독 필요")
        return res
    tev = truncation_evidence(info, n)
    if tev:  # 이미지 쪽이 몇 개 있어도(표지·차트) 본문이 6장에서 끝나면 스캔본이 아니라 잘린 사본 -- SCAN_PENDING 보다 먼저
        res.update(status="RAW_TRUNCATED", mode="none", evidence=tev)
        return res
    if info["img_low"]:
        res.update(status="SCAN_PENDING", mode="scan",
                   evidence=(f"이미지 쪽 {len(info['img_low'])}개(텍스트 400자 미만) p{info['img_low'][:6]}.. / "
                             f"유지율 머리 쪽 {info['head_pages']} / 표 본문 텍스트 없음"))
        return res
    if not info["sec7"]:
        res.update(status="RAW_TRUNCATED", mode="none",
                   evidence=f"본문에 `7-n.` 절 제목이 하나도 없음({n}쪽, 마지막 쪽까지 텍스트층 정상) -- PDF 가 7장 앞에서 잘렸을 가능성")
        return res
    res.update(status="PARSE_FAILED",
               evidence=f"텍스트 PDF({n}쪽)인데 표를 못 읽음: 후보쪽 {info['cand']} 머리쪽 {info['head_pages']}")
    return res


def _rows_equal(a, b):
    ka = {(r["회차"], r["채널"]): (r["유지율"], r["유지계약액"], r["대상신계약액"]) for r in a}
    kb = {(r["회차"], r["채널"]): (r["유지율"], r["유지계약액"], r["대상신계약액"]) for r in b}
    return ka == kb


# ======================================================================================
# 8. vision 병합
# ======================================================================================
KIND_MAP = (("생", "생명보험"), ("손", "손해보험"))


def norm_kind(v, fallback):
    s = str(v or "")
    for k, out in KIND_MAP:
        if k in s:
            return out
    return fallback


def load_vision_rows(registry):
    rows, used = [], []
    for f in sorted(glob.glob(str(OUT_DIR / "vision_cells*.json"))):
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001  (vision 에이전트가 쓰는 중일 수 있다)
            print(f"  [경고] {Path(f).name} 읽기 실패({type(e).__name__}) -- 이 파일만 건너뜀")
            continue
        if isinstance(data, dict):
            data = data.get("rows") or data.get("cells") or []
        used.append(Path(f).name)
        for r in data:
            code = r.get("원보험사코드")
            q = r.get("공시분기")
            if not code or not q:
                continue
            nm, kd = registry.get(code, (r.get("원수사명"), None))
            rr = dict(r)
            rr["원수사명"] = nm or r.get("원수사명")  # 레지스트리 이름 우선(vision 파일마다 `흥국화재`/`흥국화재해상보험` 처럼 표기가 갈린다)
            rr["생손보여부"] = norm_kind(r.get("생손보여부"), kd)
            rr["추출방식"] = "vision"
            rr.setdefault("dash", False)
            rr.setdefault("blank", False)
            idn = r.get("identity")
            if isinstance(idn, dict):  # V2·V3 는 dict(strict_ok·rounding_interval_ok) -- 텍스트 행과 같은 문자열 라벨로 맞춘다
                rr["identity_detail"] = idn
                if idn.get("strict_ok", idn.get("ok")):
                    rr["identity"] = "ok"
                elif idn.get("rounding_interval_ok"):
                    rr["identity"] = "round"
                else:
                    rr["identity"] = "break"
            elif isinstance(idn, str):  # V1 은 `ok_precision`·`n/a` -- 추출기 어휘로
                rr["identity"] = VISION_IDENTITY_MAP.get(idn.strip().lower(), idn)
            rr["_src"] = Path(f).name
            rows.append(rr)
    return rows, used


def load_vision_census():
    out = {}
    for f in sorted(glob.glob(str(OUT_DIR / "vision_census_v*.csv"))):
        try:
            with open(f, encoding="utf-8-sig", newline="") as fh:
                for r in csv.DictReader(fh):
                    tbl = (r.get("표") or "")
                    if not ("7-6" in tbl or "유지율" in tbl):
                        continue
                    out[(r.get("원보험사코드"), r.get("공시분기"))] = {**r, "_src": Path(f).name}
        except Exception as e:  # noqa: BLE001
            print(f"  [경고] {Path(f).name} 읽기 실패({type(e).__name__}) -- 이 파일만 건너뜀")
    return out


# ======================================================================================
# 9. 레지스트리 / management_indicators
# ======================================================================================
def load_registry():
    reg = {}
    try:
        data = json.loads(KICS_PATH.read_text(encoding="utf-8"))
        for r in data:
            c = r.get("원보험사코드")
            if c and c not in reg:
                reg[c] = (r.get("원수사명"), r.get("생손보여부"))
    except Exception as e:  # noqa: BLE001
        print(f"  [경고] kics_disclosure.json 읽기 실패: {e}")
    return reg


def load_mi():
    out = {}
    try:
        for r in json.loads(MI_PATH.read_text(encoding="utf-8")):
            m = re.match(r"^계약유지율_(\d+)회차$", r.get("항목명", ""))
            if m and r.get("값") is not None:
                out[(r["원보험사코드"], r["공시분기"], int(m.group(1)))] = float(r["값"])
    except Exception as e:  # noqa: BLE001
        print(f"  [경고] management_indicators.json 읽기 실패: {e}")
    return out


def load_errata():
    """원문 인쇄 오기 등재부 -> {(코드, 분기, 회차, 채널): (유형, 근거)}. 파일이 없으면 빈 dict.
    회차·채널이 둘 다 `*`(또는 빈칸)이면 회사·분기 단위(그 칸 전체) 등재 -> 키 (코드, 분기, None, None)."""
    out = {}
    if not ERRATA_PATH.exists():
        return out
    with open(ERRATA_PATH, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            rnd, ch = (r["회차"] or "").strip(), (r["채널"] or "").strip()
            whole = rnd in ("", "*") and ch in ("", "*")
            out[(r["원보험사코드"], r["공시분기"], None if whole else int(rnd), None if whole else ch)] = (r["유형"], r["근거"])
    return out


# ======================================================================================
# 10. main
# ======================================================================================
CH_IDX = {c: i for i, c in enumerate(CH11)}


def row_sort_key(r):
    return (r["원보험사코드"], r["공시분기"], r["회차"] if r["회차"] is not None else 0,
            CH_IDX.get(r["채널"], 99), r["채널"])


def to_json_row(code, name, kind, q, r, res):
    return {
        "원보험사코드": code, "원수사명": name, "생손보여부": kind, "공시분기": q, "회차": r["회차"],
        "채널": r["채널"], "채널_원문": r["채널_원문"],
        "유지율": r["유지율"], "유지계약액": r["유지계약액"], "대상신계약액": r["대상신계약액"],
        "단위": res["unit"], "단위_원문": res.get("unit_txt"), "dash": bool(r["dash_fields"]),
        "blank": bool(r["blank_fields"]),
        "dash_fields": r["dash_fields"],
        "출처": {"file": res["file"], "page": r["page"]}, "추출방식": res["mode_out"],
        "유지율_표기소수": r["dec"], "identity": r["identity"],
        "identity_break": r["identity"] == "break",
        "항등식_편차": None if r["dev"] is None else round(r["dev"], 4),
        **({"repair": r["repair"]} if r["repair"] else {}),
        **({"malformed": r["malformed"]} if r["malformed"] else {}),
        **({"na_text": r["na_text"]} if r.get("na_text") else {}),
    }


def scale_check(rows):
    """회사별 Σ대상신계약액(표 머리 단위 -> 백만원 환산)을 같은 회사 다른 분기 중앙값과 비교한다.
    비율이 SCALE_BAND 밖이면 kind='이상', 표 머리 단위가 금액 단위가 아닌 '건' 인데 밴드 안이면 '단위라벨불일치'.
    다른 분기가 SCALE_MIN_OTHERS 개 미만인 회사는 건너뛴다. -> {(코드, 분기): {ratio, ref, sum, unit, kind}}"""
    tot, unit = defaultdict(float), {}
    for r in rows:
        k = (r["원보험사코드"], r["공시분기"])
        m = UNIT_RE.search(r.get("단위") or "")
        unit.setdefault(k, m.group(1) if m else None)
        if r.get("대상신계약액") is not None:
            tot[k] += r["대상신계약액"] * TO_MW.get(unit[k], 1.0)
    byc = defaultdict(dict)
    for (c, q), v in tot.items():
        if v > 0:
            byc[c][q] = v
    out = {}
    for c, d in byc.items():
        for q, v in d.items():
            others = [x for qq, x in d.items() if qq != q]
            if len(others) < SCALE_MIN_OTHERS:
                continue
            ref = median(others)
            ratio = v / ref
            kind = None
            if not (SCALE_BAND[0] <= ratio <= SCALE_BAND[1]):
                kind = "이상"
            elif unit[(c, q)] == "건":
                kind = "단위라벨불일치"
            if kind:
                out[(c, q)] = {"ratio": ratio, "ref": ref, "sum": v, "unit": unit[(c, q)], "kind": kind}
    return out


def main():
    ap = argparse.ArgumentParser(description="판매채널별 계약유지율 추출 (정기경영공시 7-6 유지율 표)")
    ap.add_argument("--companies", help="디버그용: KR 코드 콤마 구분")
    ap.add_argument("--periods", help="디버그용: FY2024_Q2,... (쓰기 안 함)")
    ap.add_argument("--no-write", action="store_true", help="파일을 쓰지 않고 요약만")
    args = ap.parse_args()
    filtered = bool(args.companies or args.periods)
    do_write = not (args.no_write or filtered)

    t0 = time.time()
    registry = load_registry()
    for c, v in EXTRA_COMPANIES.items():
        registry.setdefault(c, v)
    periods = args.periods.split(",") if args.periods else PERIODS
    # 그리드: 레지스트리 전 회사 x 7분기 (+ 레지스트리 밖 회사는 PDF 가 있는 칸만)
    codes = sorted(registry)
    if args.companies:
        codes = [c for c in codes if c in args.companies.split(",")]

    results = {}
    for code in codes:
        for period in periods:
            pdfs = disclosure_pdfs(period, code)
            if not pdfs:
                if code in EXTRA_COMPANIES:
                    continue
                results[(code, period)] = {"status": "NO_RAW_PDF", "mode": "none", "pages": [], "rows": [], "unit": None,
                                           "evidence": f"data/disclosure/{period}/{{raw,pdf}}/{code}_*.pdf 없음",
                                           "notes": [], "file": "", "N": None, "method": None, "dup": 0}
                continue
            amended = [p for p in pdfs if "amended" in p.stem.lower() or "정정" in p.stem]
            pdf = (amended or pdfs)[-1]
            r = process_pdf(code, period, pdf)
            results[(code, period)] = r
            print(f"  {code} {period} {r['status']:<17} {pdf.name[:34]:<34} "
                  f"{('p' + ','.join(map(str, r['pages']))) if r['pages'] else '':<10} "
                  f"N={r['N']} rows={len(r['rows'])} {'; '.join(r['notes'])[:100]}", flush=True)

    # ---- vision 병합 -------------------------------------------------------------
    vrows, vfiles = load_vision_rows(registry)
    vcensus = load_vision_census()
    v_by_cell = defaultdict(list)
    seen = set()
    for r in vrows:
        k = (r["원보험사코드"], r["공시분기"], r.get("회차"), r.get("채널"))
        if k in seen:
            print(f"  [경고] vision 행 중복 {k} ({r['_src']}) -- 먼저 읽은 것 유지")
            continue
        seen.add(k)
        v_by_cell[(r["원보험사코드"], r["공시분기"])].append(r)

    json_rows = []
    census = []
    selfcheck = []
    mi = load_mi()
    errata = load_errata()
    errata_seen = set()
    idc = Counter()  # 항등식 재계산 집계: (추출방식, 라벨있음/없음/종류다름)
    for (code, period), res in sorted(results.items()):
        q = quarter_of(period)
        name, kind = registry.get(code, ("", ""))
        vr = v_by_cell.get((code, q), [])
        vc = vcensus.get((code, q))
        status, mode_out, evidence, pages = res["status"], res["mode"], res["evidence"], res["pages"]
        text_rows = res["rows"]
        use_rows = []
        note_extra = []
        if status in ("FILLED",) or (status == "ABSENT_IN_SOURCE" and text_rows):
            res["mode_out"] = "text"
            use_rows = [to_json_row(code, name, kind, q, r, res) for r in text_rows]
            if vr:  # 텍스트 우선 -- 값 차이만 남긴다
                tv = {(r["회차"], r["채널"]): r for r in text_rows}
                diffs = 0
                for r in vr:
                    t = tv.get((r.get("회차"), r.get("채널")))
                    if not t:
                        continue
                    for f in ("유지율", "유지계약액", "대상신계약액"):
                        a, b = t[f], r.get(f)
                        if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-6):
                            diffs += 1
                            selfcheck.append({"kind": "VISION_VS_TEXT", "code": code, "name": name, "quarter": q,
                                              "round": r.get("회차"), "channel": r.get("채널"), "field": f,
                                              "a": a, "b": b, "detail": "텍스트 값 사용 / vision 값 다름"})
                note_extra.append(f"vision 도 있음(값 차이 {diffs}건 -- 텍스트 사용)")
        elif vr:
            res["mode_out"] = "vision"
            for r in vr:
                rr = {
                    "원보험사코드": code, "원수사명": name or r.get("원수사명"), "생손보여부": r["생손보여부"] or kind,
                    "공시분기": q, "회차": r.get("회차"), "채널": r.get("채널"), "채널_원문": r.get("채널_원문"),
                    "유지율": r.get("유지율"), "유지계약액": r.get("유지계약액"), "대상신계약액": r.get("대상신계약액"),
                    "단위": r.get("단위"), "dash": bool(r.get("dash")), "blank": bool(r.get("blank")),
                    "출처": r.get("출처"), "추출방식": "vision",
                }
                for k in ("dash_fields", "유지율_표기소수", "identity", "identity_break", "항등식_편차", "단위_원문",
                          "identity_note", "repair"):
                    if k in r:
                        rr[k] = r[k]
                use_rows.append(rr)
            vnon = sum(1 for r in vr if any(r.get(f) is not None for f in ("유지율", "유지계약액", "대상신계약액")))
            if vc and vc.get("상태") in ("ABSENT_IN_SOURCE", "UNREADABLE"):
                status, evidence = vc["상태"], f"[{vc['_src']}] {vc.get('근거', '')}"
            elif vnon == 0:
                status, evidence = "ABSENT_IN_SOURCE", f"[vision] 44칸 전부 '-' ({vc.get('근거', '') if vc else ''})"
            else:
                status = "FILLED(vision)"
                evidence = f"[{vr[0]['_src']}] " + ((vc.get("근거") or "") if vc else "")
            mode_out = "vision"
            pages = [str((vr[0].get("출처") or {}).get("page", ""))]
            res["file"] = (vr[0].get("출처") or {}).get("file", res["file"])
        else:
            res["mode_out"] = None
            v_trunc = bool(vc and vc.get("상태") in ("ABSENT_IN_SOURCE", "UNREADABLE") and TRUNC_RE.search(vc.get("근거") or ""))
            if res["status"] == "RAW_TRUNCATED" or v_trunc:
                # 원문에 표가 없다는 뜻이 아니라 우리가 가진 파일이 잘렸다는 뜻 -> downloader 소관. 추출기 자체 판정(PDF 가 6장에서 끝남)이
                # 우선이고, vision census 근거에 '잘린'/'truncated' 가 있으면 그것으로도 승격한다(vision census 행 자체는 안 건드린다).
                status = "RAW_TRUNCATED"
                mode_out = "none"
                own = res["evidence"] if res["status"] == "RAW_TRUNCATED" else f"[{vc['_src']}] {vc.get('근거', '')}"
                peers = {pp: results[(code, pp)]["n_pages"] for pp in PERIODS
                         if (code, pp) in results and results[(code, pp)].get("n_pages")
                         and results[(code, pp)]["status"] != "RAW_TRUNCATED"}
                parts = [own]
                if peers:
                    parts.append("같은 회사 다른 분기 쪽수: " + " · ".join(f"{quarter_of(pp)} {pn}쪽" for pp, pn in sorted(peers.items())))
                tix = find_truncation_ticket(code, q)
                if tix:
                    parts.append("downloader 티켓: " + ", ".join(tix))
                if vc and res["status"] == "RAW_TRUNCATED":
                    parts.append(f"[{vc['_src']}] vision 판정={vc.get('상태')} (파일이 잘려 있어 원문에 표가 없다는 근거로 쓰지 않는다)")
                evidence = " | ".join(x for x in parts if x)
            elif vc and vc.get("상태") in ("ABSENT_IN_SOURCE", "UNREADABLE"):
                status, evidence = vc["상태"], f"[{vc['_src']}] {vc.get('근거', '')}"
                mode_out = "vision"
            elif vc and vc.get("상태") == "FILLED":
                status = "SCAN_PENDING"
                evidence = f"vision census FILLED 인데 vision_cells 행이 아직 없음({vc['_src']}) -- " + evidence
            elif vc and vc.get("상태") == "TEXT_COPY":
                status = res["status"] if res["status"] != "SCAN_PENDING" else "PARSE_FAILED"
                evidence = f"vision 이 TEXT_COPY 로 표시({vc.get('근거', '')}) -- 텍스트 추출 재확인 필요. " + evidence
        for r in use_rows:  # 항등식 재계산 -- 텍스트·vision 공통. 파일/추출 라벨은 참고용, 종류가 다르면 selfcheck 에 남기고 재계산 값으로 덮는다
            st, dev = recheck_identity(r)
            old, how = r.get("identity"), r.get("추출방식")
            if old is None:
                idc[(how, "라벨없음")] += 1
            elif IDENT_CLASS.get(old) != IDENT_CLASS.get(st):
                idc[(how, "종류다름")] += 1
                selfcheck.append({"kind": "IDENTITY_RELABEL", "code": code, "name": name, "quarter": q, "round": r.get("회차"),
                                  "channel": r.get("채널"), "field": "유지율", "a": old, "b": st,
                                  "detail": f"[{how}] 기존 라벨={old} -> 재계산={st} 편차={None if dev is None else round(dev, 4)} "
                                            f"(유지율={r.get('유지율')} 유지계약액={r.get('유지계약액')} 대상신계약액={r.get('대상신계약액')})"})
            else:
                idc[(how, "일치")] += 1
            r["identity"], r["identity_break"] = st, st == "break"
            r["항등식_편차"] = None if dev is None else round(dev, 4)
        for r in use_rows:  # 원문 인쇄 오기 등재부(원문 쪽을 보고 확정한 break)를 행에 붙인다
            k = (code, q, r.get("회차"), r.get("채널"))
            if k in errata:
                errata_seen.add(k)
                if r.get("identity") == "break" or r.get("identity_break"):
                    r["source_misprint"], r["identity_note"] = errata[k]
                else:
                    print(f"  [경고] 원문오기 등재 {k} 인데 항등식이 break 가 아님({r.get('identity')}) -- 등재부 점검")
        json_rows.extend(use_rows)

        # 칸 집계
        cnt = Counter(r.get("identity") for r in use_rows)
        n_nonnull = sum(1 for r in use_rows if any(r.get(f) is not None for f in ("유지율", "유지계약액", "대상신계약액")))
        n_dash_only = sum(1 for r in use_rows if r.get("dash") and not any(r.get(f) is not None for f in ("유지율", "유지계약액", "대상신계약액")))
        census.append({
            "원보험사코드": code, "원수사명": name, "생손보여부": kind, "공시분기": q, "상태": status,
            "추출방식": mode_out if mode_out != "none" else "", "쪽": ",".join(map(str, pages)), "파일": res["file"],
            "채널열수": res["N"] if res["N"] is not None else (len({r.get("채널") for r in use_rows}) if use_rows else ""),
            "행수": len(use_rows), "값있는행수": n_nonnull, "dash만행수": n_dash_only,
            "항등식_ok": cnt.get("ok", 0), "항등식_반올림": cnt.get("round", 0), "항등식_절삭": cnt.get("trunc", 0),
            "항등식_불일치": cnt.get("break", 0), "보정": sum(1 for r in use_rows if r.get("repair")),
            "원문오기": sum(1 for r in use_rows if r.get("source_misprint")),
            "근거": " | ".join(x for x in [evidence] + res["notes"] + note_extra if x),
        })
        # selfcheck: 항등식 break / 보정 / 범위
        for r in use_rows:
            base = {"code": code, "name": name, "quarter": q, "round": r.get("회차"), "channel": r.get("채널")}
            rr, mm, dd = r.get("유지율"), r.get("유지계약액"), r.get("대상신계약액")
            if r.get("identity") == "break" or r.get("identity_break"):
                calc = None if (mm is None or not dd) else round(100.0 * mm / dd, 3)
                tag = f"[원문오기:{r['source_misprint']}] " if r.get("source_misprint") else "[미등재] "
                selfcheck.append({**base, "kind": "IDENTITY_BREAK", "field": "유지율", "a": rr, "b": calc,
                                  "detail": tag + f"유지계약액={mm} 대상신계약액={dd} 편차={r.get('항등식_편차')} [{r.get('추출방식')}]"})
            if r.get("repair"):
                selfcheck.append({**base, "kind": "REPAIR", "field": "", "a": "", "b": "", "detail": r["repair"]})
            if r.get("malformed"):
                selfcheck.append({**base, "kind": "MALFORMED", "field": "", "a": "", "b": "", "detail": str(r["malformed"])})
            for f, v in (("유지율", rr), ("유지계약액", mm), ("대상신계약액", dd)):
                if v is not None and v < 0:
                    selfcheck.append({**base, "kind": "RANGE", "field": f, "a": v, "b": "", "detail": "음수"})
            if rr is not None and rr > 100.0 + 1e-9:
                selfcheck.append({**base, "kind": "RANGE", "field": "유지율", "a": rr, "b": "", "detail": "유지율 100 초과"})
            if mm is not None and dd is not None and mm > dd + 1e-9:
                selfcheck.append({**base, "kind": "RANGE", "field": "유지계약액", "a": mm, "b": dd, "detail": "유지계약액 > 대상신계약액"})

        # selfcheck: 회차가 올라갈수록 유지율이 뛰는 채널 (플래그만)
        by_ch = defaultdict(dict)
        for r in use_rows:
            if r.get("유지율") is not None:
                by_ch[r.get("채널")][r.get("회차")] = r["유지율"]
        for ch, d in by_ch.items():
            prev = None
            for rnd in ROUNDS:
                if rnd in d:
                    if prev is not None and d[rnd] > prev[1] + 0.005:
                        selfcheck.append({"kind": "NONMONOTONIC", "code": code, "name": name, "quarter": q, "round": rnd,
                                          "channel": ch, "field": "유지율", "a": d[rnd], "b": prev[1],
                                          "detail": f"{prev[0]}회차 {prev[1]} -> {rnd}회차 {d[rnd]} 상승"})
                    prev = (rnd, d[rnd])

        # selfcheck: 채널 합 vs management_indicators (1-2 표 회사 단위 유지율)
        if use_rows:
            for rnd in ROUNDS:
                sm = sd = 0.0
                ncell = 0
                for r in use_rows:
                    if r.get("회차") == rnd and r.get("유지계약액") is not None and r.get("대상신계약액") is not None:
                        sm += r["유지계약액"]
                        sd += r["대상신계약액"]
                        ncell += 1
                ref = mi.get((code, q, rnd))
                if sd > 0 and ref is not None:
                    selfcheck.append({"kind": "COMPANY_SUM", "code": code, "name": name, "quarter": q, "round": rnd,
                                      "channel": "ALL", "field": "유지율", "a": round(100.0 * sm / sd, 3), "b": ref,
                                      "detail": f"채널합 {ncell}열 Σ유지계약액={sm:g} Σ대상신계약액={sd:g} 차이={100.0 * sm / sd - ref:+.3f}"})

    json_rows.sort(key=row_sort_key)

    # ---- 규모 검사(회사별 Σ대상신계약액) + 회사·분기 단위 등재 연결 --------------------------
    scale = scale_check(json_rows)
    n_scale_reg = n_scale_unreg = n_label = 0
    for (code, q), s in sorted(scale.items()):
        reg = errata.get((code, q, None, None))
        if s["kind"] == "이상":
            kind, tag = "SCALE_OUTLIER", f"[등재:{reg[0]}] " if reg else "[미등재] "
            n_scale_reg, n_scale_unreg = n_scale_reg + bool(reg), n_scale_unreg + (not reg)
        else:
            kind, tag = "UNIT_LABEL", "[자동플래그] "
            n_label += 1
        selfcheck.append({"kind": kind, "code": code, "name": registry.get(code, ("", ""))[0], "quarter": q, "round": "",
                          "channel": "ALL", "field": "대상신계약액", "a": round(s["sum"], 3), "b": round(s["ref"], 3),
                          "detail": tag + f"Σ대상신계약액(백만원 환산) / 같은 회사 다른 분기 중앙값 = {s['ratio']:.4g}배 "
                                          f"(밴드 {SCALE_BAND[0]}~{SCALE_BAND[1]}) 표 머리 단위={s['unit']}"
                                          + ("" if s["kind"] == "이상" else " -- 단위 라벨은 금액 단위가 아닌데 규모는 백만원 (라벨 오기 추정)")})
    for r in json_rows:
        k = (r["원보험사코드"], r["공시분기"])
        if k in scale:
            r["규모비"], r["규모점검"] = float(f"{scale[k]['ratio']:.3g}"), scale[k]["kind"]
        reg = errata.get(k + (None, None))
        if reg:
            errata_seen.add(k + (None, None))
            r["scale_misprint"], r["scale_note"] = reg
    if not filtered:
        for k, (typ, _) in sorted(errata.items(), key=lambda kv: str(kv[0])):
            if k[2] is None:
                if typ not in SCALE_ERRATA_TYPES:
                    print(f"  [경고] 회사·분기 단위 등재 {k} 의 유형 {typ} 은 알 수 없음 (허용: {SCALE_ERRATA_TYPES})")
                elif scale.get((k[0], k[1]), {}).get("kind") != "이상":
                    print(f"  [경고] 규모 등재 {k} 인데 규모 검사(이상)에 안 걸림 -- 등재부 점검")

    # ---- 요약 출력 -----------------------------------------------------------------
    cs = Counter(c["상태"] for c in census)
    print(f"\n=== census ({len(census)}칸) === {dict(cs)}")
    print(f"규모 검사(밴드 {SCALE_BAND[0]}~{SCALE_BAND[1]}, 다른 분기 {SCALE_MIN_OTHERS}개 이상): 이상 {n_scale_reg + n_scale_unreg}건"
          f"(등재 {n_scale_reg} / 미등재 {n_scale_unreg}) / 단위라벨불일치 {n_label}건 -- "
          + (", ".join(f"{c} {q} x{s['ratio']:.3g}({s['kind']})" for (c, q), s in sorted(scale.items())) or "없음"))
    print("항등식 재계산(추출방식/라벨 대비): " + ", ".join(f"{how}/{kind}={n}" for (how, kind), n in sorted(idc.items(), key=str)))
    brk = [s for s in selfcheck if s["kind"] == "IDENTITY_BREAK"]
    n_known = sum(1 for s in brk if s["detail"].startswith("[원문오기"))
    if not filtered:
        for k in sorted(set(errata) - errata_seen, key=str):
            print(f"  [경고] 원문오기 등재 {k} 가 이번 실행 결과에 없음 -- 등재부 점검")
    print(f"항등식 break {len(brk)}건(원문오기 등재 {n_known} / 미등재 {len(brk) - n_known}) / 보정 {sum(1 for s in selfcheck if s['kind'] == 'REPAIR')}건 / "
          f"vision-텍스트 차이 {sum(1 for s in selfcheck if s['kind'] == 'VISION_VS_TEXT')}건 / 행 {len(json_rows)}")
    sums = [abs(float(s["a"]) - float(s["b"])) for s in selfcheck if s["kind"] == "COMPANY_SUM"]
    if sums:
        sums.sort()
        print(f"채널합 vs MI: {len(sums)}건, 중앙 |차| {sums[len(sums) // 2]:.3f}, 90% {sums[int(len(sums) * 0.9)]:.3f}, 최대 {sums[-1]:.3f}")
    print(f"vision 파일: {vfiles}  소요 {time.time() - t0:.0f}s")

    if do_write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        atomic_write(OUT_JSON, json.dumps(json_rows, ensure_ascii=False, indent=1))
        cols = list(census[0].keys())
        buf = io.StringIO(newline="")
        w = csv.DictWriter(buf, fieldnames=cols)
        w.writeheader()
        w.writerows(census)
        atomic_write(OUT_CENSUS, buf.getvalue(), encoding="utf-8-sig", newline="")
        scols = ["kind", "code", "name", "quarter", "round", "channel", "field", "a", "b", "detail"]
        buf = io.StringIO(newline="")
        w = csv.DictWriter(buf, fieldnames=scols, extrasaction="ignore")
        w.writeheader()
        w.writerows(selfcheck)
        atomic_write(OUT_SELFCHECK, buf.getvalue(), encoding="utf-8-sig", newline="")
        print(f"WROTE {rel(OUT_JSON)} ({len(json_rows)}행) / {rel(OUT_CENSUS)} / {rel(OUT_SELFCHECK)}")
    else:
        print("(쓰기 생략: --no-write 또는 필터 실행)")


if __name__ == "__main__":
    main()
