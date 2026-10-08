#!/usr/bin/env python3
"""판매채널별 유지율 마스터 변환기 (owner 결정 2026-10-07, handoff §5-1).

추출 원본(long, 출처 포함) `data/persistency/persistency_channel.json` 은 그대로 두고, 마스터 양식으로 바꿔 쓴다:
  data/persistency/master_persistency.json   list of dict (루트 마스터와 같은 indent=2 UTF-8)
  data/persistency/master_persistency.csv    같은 내용, utf-8-sig (Excel)

열 순서(고정): 원보험사코드 · 원수사명 · 티커 · 생손보여부 · 공시분기 · 회차구분("13회차") · 채널대분류 · 채널소분류 ·
               대상신계약액 · 유지계약액 · 유지율   -- 그 뒤 보조열: 단위 · 출처(파일:쪽) · 추출방식 · 플래그

규칙
----
* 1행 = (회사, 공시분기, 회차, 채널). 원본 행과 1:1 (행 수·값 동일). 숫자는 변환하지 않는다(단위 환산 금지 -- 단위는 보조열에 인쇄 그대로).
* 원문 `-` 는 0 이 아니라 null(JSON) / 빈 칸(CSV), 플래그에 `대시(-)`. 인쇄 공란도 null + `공란`.
* 채널: 설계사 · 개인대리점 · 법인대리점{금융기관보험대리점·TM·홈쇼핑·기타} · 직영{임직원·복합·다이렉트} · 중개사 · 기타.
  소분류 없는 채널(설계사·개인대리점·중개사·기타)은 소분류 공란. 표준코드 `법인대리점_금융기관` -> 대분류 `법인대리점` / 소분류 `금융기관보험대리점`.
  (옛 서식의 `방카`·`방카슈랑스` 는 추출기가 이미 금융기관 코드로 매핑했다.) 표준코드가 아닌 채널은 버리지 않고 대분류 `UNMAPPED` + 소분류=원문.
* 티커: 루트 kics_disclosure.json -> management_indicators.json -> IFRS17_BS.json 의 `티커` 를 회사코드로 조회(읽기만).
  기존 마스터에서 비상장은 `X` 로 적혀 있다 -> 여기서는 owner 지시대로 **공란**. 원수사명도 같은 레지스트리 이름을 쓴다(vision 파일마다 표기가 갈렸다).
* 단위: 원본 `단위` 에서 금액 단위 하나만 뽑는다(`백만원, %` -> `백만원`). 표 머리에 단위가 없거나(`단위미표기`) 건/천원 처럼 백만원이 아닌 경우는
  플래그에 이유를 남긴다. 값은 환산하지 않았으므로 단위가 다른 분기끼리 금액을 더하면 안 된다.
* 플래그(`; ` 구분 토큰): 대시(-)[:필드] · 공란 · 대상없음 · 원문표기불량:… · 보정:… · 원문오기:<유형> · 항등식주석 · 단위미표기 · 단위=건(원문 표기) · 단위=천원(원문 `천` 해석) · 단위추정
  · 대상신계약액=0(유지율 숫자가 있는데 분모가 0 -- 0/0 은 정의되지 않는 값이라 0% 로 그리면 안 된다)
  · 단위=건(원문 표기, 금액 규모 백만원 -- 오기 추정)(규모 검사가 건 라벨인데 규모는 백만원이라고 확인한 칸; 금액이 없는 칸은 `단위=건(원문 표기)`)
  · 단위오기추정(원문 <단위>, 실제 규모 약 1/1000)(source_errata.csv UNIT_SCALE_MISPRINT 등재 칸 -- 값은 인쇄 그대로, 환산하지 않았다)
  · 금액기준상이:…(AMOUNT_BASIS_DIFFERS 등재 칸 -- 원문 인쇄 그대로, 금액 산출 기준이 달라 다른 분기와 규모가 다름) · 금액규모이상:미등재…(규모 검사에 걸렸는데 등재 안 된 칸).
  긴 근거(identity_note 등)는 원본 long JSON 에 있다 -- (공시분기, 회차, 채널, 출처)로 찾는다.
* 마지막에 원본 JSON 과 1:1 자체 검산(행 수 · 키 · 값 · JSON/CSV 재독 일치 · 키 중복 0)을 하고, 하나라도 어긋나면 비정상 종료한다.

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_persistency_master.py [--verify-only]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "persistency"
SRC_JSON = OUT_DIR / "persistency_channel.json"
OUT_JSON = OUT_DIR / "master_persistency.json"
OUT_CSV = OUT_DIR / "master_persistency.csv"
REGISTRY_FILES = ("kics_disclosure.json", "management_indicators.json", "IFRS17_BS.json")
UNLISTED_MARK = "X"  # 기존 마스터의 비상장 표기 -> 이 마스터에서는 공란

if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER_COLS = ["원보험사코드", "원수사명", "티커", "생손보여부", "공시분기", "회차구분", "채널대분류", "채널소분류",
               "대상신계약액", "유지계약액", "유지율"]
AUX_COLS = ["단위", "출처", "추출방식", "플래그"]
ALL_COLS = MASTER_COLS + AUX_COLS

# 추출기 표준 11코드 -> (대분류, 소분류)
CHANNEL_SPLIT = {
    "설계사": ("설계사", ""),
    "개인대리점": ("개인대리점", ""),
    "법인대리점_금융기관": ("법인대리점", "금융기관보험대리점"),
    "법인대리점_TM": ("법인대리점", "TM"),
    "법인대리점_홈쇼핑": ("법인대리점", "홈쇼핑"),
    "법인대리점_기타": ("법인대리점", "기타"),
    "직영_임직원": ("직영", "임직원"),
    "직영_복합": ("직영", "복합"),
    "직영_다이렉트": ("직영", "다이렉트"),
    "중개사": ("중개사", ""),
    "기타": ("기타", ""),
}
CH_ORDER = {c: i for i, c in enumerate(CHANNEL_SPLIT)}
SPLIT_BACK = {v: k for k, v in CHANNEL_SPLIT.items()}
UNIT_RE = re.compile(r"(천만원|백만원|억원|만원|천원|원|건)")
NUM_FIELDS = ("대상신계약액", "유지계약액", "유지율")
GUN_MISPRINT_FLAG = "단위=건(원문 표기, 금액 규모 백만원 -- 오기 추정)"


def atomic_write(path, text, encoding="utf-8"):
    path = Path(path)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, "w", encoding=encoding, newline="") as f:
        f.write(text)
    os.replace(tmp, path)


def load_registry():
    """-> {코드: {name, kind, ticker}} (읽기만). ticker 는 비어 있지 않고 `X` 가 아닌 첫 값, 없으면 ''."""
    reg = {}
    for fn in REGISTRY_FILES:
        p = REPO / fn
        if not p.exists():
            print(f"  [경고] {fn} 없음 -- 건너뜀")
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            c = r.get("원보험사코드")
            if not c:
                continue
            e = reg.setdefault(c, {"name": None, "kind": None, "ticker": ""})
            e["name"] = e["name"] or r.get("원수사명")
            e["kind"] = e["kind"] or r.get("생손보여부")
            t = (r.get("티커") or "").strip()
            if t and t != UNLISTED_MARK and not e["ticker"]:
                e["ticker"] = t
    return reg


def unit_of(raw):
    """원본 단위 문자열 -> (정규화 단위, 플래그 목록)."""
    flags = []
    if not raw:
        return "", ["단위미표기"]
    m = UNIT_RE.search(raw)
    unit = m.group(1) if m else ""
    if not unit:
        flags.append("단위미표기")
    if "추정" in raw or "미표기" in raw:
        flags.append("단위추정")
    if unit == "건":
        flags.append("단위=건(원문 표기)")
    return unit, flags


def source_text(src):
    if not isinstance(src, dict):
        return ""
    pages = src.get("pages")
    pg = ",".join(str(x) for x in pages) if pages else src.get("page")
    return f"{src.get('file', '')}:{pg}"


def convert_row(r, reg):
    c = r["원보험사코드"]
    e = reg.get(c) or {"name": None, "kind": None, "ticker": ""}
    major, minor = CHANNEL_SPLIT.get(r["채널"], ("UNMAPPED", r.get("채널_원문") or r["채널"]))
    unit, uflags = unit_of(r.get("단위"))
    if unit == "천원" and "천원" not in re.sub(r"\s+", "", r.get("단위_원문") or ""):
        uflags.append("단위=천원(원문 `천` 해석)")
    if r.get("규모점검") == "단위라벨불일치":  # 추출기 규모 검사: 표 머리는 '건' 인데 Σ대상신계약액 규모는 회사의 다른 분기(백만원)와 같다
        uflags = [GUN_MISPRINT_FLAG if f == "단위=건(원문 표기)" else f for f in uflags]
    flags = []
    df = r.get("dash_fields") or []
    if df:
        flags.append("대시(-):" + "/".join(df))
    elif r.get("dash"):
        flags.append("대시(-)")
    if r.get("blank"):
        flags.append("공란")
    if r.get("na_text"):
        flags.append("대상없음")
    if r.get("malformed"):
        flags.append("원문표기불량:" + "; ".join(r["malformed"]))
    if r.get("repair"):
        flags.append("보정:" + r["repair"])
    if r.get("source_misprint"):
        flags.append("원문오기:" + r["source_misprint"])
    elif r.get("identity") == "break" or r.get("identity_break"):
        flags.append("항등식불일치(미등재)")
    elif r.get("identity_note") and r.get("identity") != "round":
        flags.append("항등식주석")
    ratio = f"(회사 다른 분기 중앙값 대비 {r['규모비']:g}배)" if r.get("규모비") is not None else ""
    if r.get("scale_misprint") == "UNIT_SCALE_MISPRINT":  # 값은 인쇄 그대로 -- 환산하지 않는다
        flags.append(f"단위오기추정(원문 {unit or '단위미표기'}, 실제 규모 약 1/1000)")
    elif r.get("scale_misprint") == "AMOUNT_BASIS_DIFFERS":
        flags.append(f"금액기준상이:원문 인쇄 그대로{ratio}")
    elif r.get("규모점검") == "이상":
        flags.append(f"금액규모이상:미등재{ratio}")
    if r.get("대상신계약액") == 0 and r.get("유지율") is not None:  # 0/0 율은 정의되지 않는 값 -- 화면이 0% 로 그리면 틀린 신호
        flags.append("대상신계약액=0")
    flags += [f for f in uflags if f not in flags]
    row = {
        "원보험사코드": c,
        "원수사명": e["name"] or r.get("원수사명"),
        "티커": e["ticker"],
        "생손보여부": e["kind"] or r.get("생손보여부"),
        "공시분기": r["공시분기"],
        "회차구분": f"{r['회차']}회차",
        "채널대분류": major,
        "채널소분류": minor,
        "대상신계약액": r.get("대상신계약액"),
        "유지계약액": r.get("유지계약액"),
        "유지율": r.get("유지율"),
        "단위": unit,
        "출처": source_text(r.get("출처")),
        "추출방식": r.get("추출방식"),
        "플래그": "; ".join(flags),
    }
    return row


def fmt_num(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return repr(v) if isinstance(v, float) else str(v)


def sort_key(r):
    ch = SPLIT_BACK.get((r["채널대분류"], r["채널소분류"]), None)
    return (r["원보험사코드"], r["공시분기"], int(r["회차구분"][:-2]), CH_ORDER.get(ch, 99), r["채널소분류"])


def build():
    src = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    reg = load_registry()
    missing = sorted({r["원보험사코드"] for r in src} - set(reg))
    if missing:
        print(f"  [경고] 레지스트리에 없는 회사코드(티커·이름은 원본 행 값 사용, 티커 공란): {missing}")
    rows = [convert_row(r, reg) for r in src]
    # 원본 순서(추출기가 코드·분기·회차·채널순으로 정렬해 둠)를 유지하되, 같은 키 순서로 안정 정렬
    order = sorted(range(len(rows)), key=lambda i: (sort_key(rows[i]), i))
    rows = [rows[i] for i in order]
    src = [src[i] for i in order]
    return rows, src


def write_outputs(rows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write(OUT_JSON, json.dumps([{k: r[k] for k in ALL_COLS} for r in rows], ensure_ascii=False, indent=2))
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(ALL_COLS)
    for r in rows:
        w.writerow([fmt_num(r[k]) if k in NUM_FIELDS else ("" if r[k] is None else r[k]) for k in ALL_COLS])
    atomic_write(OUT_CSV, buf.getvalue(), encoding="utf-8-sig")


def same_num(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= 1e-9


def verify(src_rows=None):
    """원본 JSON <-> 마스터 JSON <-> 마스터 CSV 1:1 대조. -> 오류 문자열 목록."""
    errs = []
    src = src_rows if src_rows is not None else json.loads(SRC_JSON.read_text(encoding="utf-8"))
    mj = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    with open(OUT_CSV, encoding="utf-8-sig", newline="") as fh:
        rd = csv.reader(fh)
        header = next(rd)
        mc = list(rd)
    if header != ALL_COLS:
        errs.append(f"CSV 헤더 불일치: {header}")
    if [list(r.keys()) for r in mj[:1]] != [ALL_COLS]:
        errs.append(f"JSON 키 순서 불일치: {list(mj[0].keys()) if mj else None}")
    if not (len(src) == len(mj) == len(mc)):
        errs.append(f"행 수 불일치 원본 {len(src)} / 마스터 JSON {len(mj)} / 마스터 CSV {len(mc)}")
        return errs
    # 원본을 마스터와 같은 키로 정렬해 대조 (원본 행 키는 (코드, 분기, 회차, 채널))
    by_src = {}
    for r in src:
        k = (r["원보험사코드"], r["공시분기"], r["회차"], r["채널"])
        if k in by_src:
            errs.append(f"원본 키 중복 {k}")
        by_src[k] = r
    seen = set()
    for i, (m, cs) in enumerate(zip(mj, mc)):
        ch = SPLIT_BACK.get((m["채널대분류"], m["채널소분류"]))
        if ch is None:
            errs.append(f"행{i}: 채널 역매핑 실패 {(m['채널대분류'], m['채널소분류'])}")
            continue
        k = (m["원보험사코드"], m["공시분기"], int(m["회차구분"][:-2]), ch)
        if k in seen:
            errs.append(f"마스터 키 중복 {k}")
        seen.add(k)
        s = by_src.get(k)
        if s is None:
            errs.append(f"행{i}: 원본에 없는 키 {k}")
            continue
        for f in NUM_FIELDS:
            if not same_num(m[f], s.get(f)):
                errs.append(f"행{i} {k} {f}: 마스터 {m[f]!r} != 원본 {s.get(f)!r}")
        if m["추출방식"] != s.get("추출방식"):
            errs.append(f"행{i} {k} 추출방식 {m['추출방식']!r} != {s.get('추출방식')!r}")
        if m["출처"] != source_text(s.get("출처")):
            errs.append(f"행{i} {k} 출처 불일치")
        # CSV 재독: 모든 열이 JSON 과 같아야 한다(숫자는 값 비교, 빈 칸 = null)
        for j, col in enumerate(ALL_COLS):
            cv = cs[j]
            if col in NUM_FIELDS:
                ok = same_num(m[col], None if cv == "" else float(cv))
            else:
                ok = (m[col] if m[col] is not None else "") == cv
            if not ok:
                errs.append(f"행{i} {k} CSV {col}: {cv!r} != JSON {m[col]!r}")
    if len(seen) != len(by_src):
        errs.append(f"키 집합 크기 마스터 {len(seen)} != 원본 {len(by_src)}")
    for k in by_src:
        if k not in seen:
            errs.append(f"원본 키가 마스터에 없음 {k}")
            break
    return errs


def summarize(rows):
    print(f"마스터 {len(rows)}행 / 회사 {len({r['원보험사코드'] for r in rows})} / 분기 {sorted({r['공시분기'] for r in rows})}")
    print("회차구분:", dict(sorted(Counter(r["회차구분"] for r in rows).items())))
    print("채널(대분류/소분류):", dict(Counter((r["채널대분류"], r["채널소분류"]) for r in rows).most_common()))
    print("추출방식:", dict(Counter(r["추출방식"] for r in rows)))
    print("단위:", dict(Counter(r["단위"] for r in rows)))
    print("티커 공란(비상장) 행:", sum(1 for r in rows if not r["티커"]), "/ 티커 있는 회사:",
          sorted({(r["원보험사코드"], r["티커"]) for r in rows if r["티커"]}))
    ft = Counter()
    for r in rows:
        for tok in filter(None, (t.strip() for t in r["플래그"].split(";"))):
            ft[tok.split(":")[0]] += 1
    print("플래그 토큰:", dict(ft.most_common()))
    print("값 3개 모두 null 행:", sum(1 for r in rows if all(r[f] is None for f in NUM_FIELDS)),
          "/ 일부 null 행:", sum(1 for r in rows if any(r[f] is None for f in NUM_FIELDS)))


def main():
    ap = argparse.ArgumentParser(description="유지율 마스터 변환기 (persistency_channel.json -> master_persistency.json/csv)")
    ap.add_argument("--verify-only", action="store_true", help="쓰지 않고 기존 산출만 원본과 1:1 대조")
    args = ap.parse_args()
    if not args.verify_only:
        rows, _ = build()
        write_outputs(rows)
        summarize(rows)
        print(f"WROTE {OUT_JSON.relative_to(REPO).as_posix()} / {OUT_CSV.relative_to(REPO).as_posix()}")
    errs = verify()
    if errs:
        print(f"[검산 실패] {len(errs)}건")
        for e in errs[:30]:
            print("  ", e)
        sys.exit(1)
    print("[검산 통과] 원본 JSON <-> 마스터 JSON <-> 마스터 CSV 행 수·키·값 1:1, 키 중복 0")


if __name__ == "__main__":
    main()
