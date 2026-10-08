#!/usr/bin/env python3
"""손해율 마스터 변환기 (owner 결정 2026-10-07, handoff §5-1).

「위험보험료 대비 예상보험금」(표 B) 추출 원본 `data/loss_ratio/risk_premium_vs_expected_claims.json`(long, 출처 포함)은 그대로 두고,
마스터 양식으로 바꿔 쓴다. 추출기(`extract_loss_ratio.py`)는 고치지도 실행하지도 않는다 -- 디스크 산출을 입력으로만 읽는다.
입력이 바뀌어도(추출기 재실행) 이 스크립트를 다시 돌리면 그대로 반영된다(회사·라벨·분기 하드코딩 없음).

산출 (모두 data/loss_ratio/, 임시파일 -> os.replace):
  master_loss_ratio.json / .csv   list of dict (루트 마스터와 같은 indent=2 UTF-8) / utf-8-sig CSV
  portfolio_taxonomy.csv          원문 라벨(구분·포트폴리오·세그먼트) 고유값 census + 39사 공통 표준 3단 매핑
  period_adoption.csv             회사 x 공시분기 채택 원천(§5-1), 정정(RESTATED) 대조 결과
  master_census.csv               회사 x 공시분기 그리드(채택/결측과 사유)

열 순서(고정): 원보험사코드 · 원수사명 · 티커 · 생손보여부 · 공시분기 · 경과차년 · 구분 · 상품구분 · 포트폴리오 · 위험보험료 · 예상보험금 · 손해율
              -- 그 뒤 보조열: 원문구분 · 원문포트폴리오 · 세그먼트 · 단위 · 출처(파일:쪽) · 추출방식 · 플래그

규칙
----
* 표준 3단(구분/상품구분/포트폴리오)은 이 파일의 사전(원문 -> 표준)으로만 정한다. 사전에 없는 새 라벨은 표준 공란 + 플래그 `분류미정`
  (행을 버리지 않는다). 라벨은 어떤 회사에도 같은 기준으로 적용하고, 생보 `건강` 과 손보 `상해`·`질병` 처럼 인쇄가 다른 것은 합치지 않는다.
* 공시분기(§5-1): Y.4Q = Y.4Q PDF 의 <Y년> 블록. 같은 <Y년> 블록이 (Y+1).4Q PDF 에도 있고 칸 값이 다르면 정정으로 보고 (Y+1) 블록 채택 + 플래그
  `RESTATED(...)`. Y.4Q PDF 에 표가 없거나 그 블록을 못 읽었으면 (Y+1) 블록 -> `FROM_NEXT_YEAR_PRIOR_BLOCK`. 채택 블록이 같은 PDF 의 <Y-1> 블록과
  거의 전 칸 같으면 `SAME_AS_PRIOR_YEAR`(인쇄값 그대로). 추출 census 가 FILLED_CHECK_FLAGS·PARSE_FAILED 인 블록은 넣되 그 상태를 플래그로 남긴다.
  두 블록 대조는 "인쇄 정밀도"를 고려한다: 한쪽이 정수·한쪽이 소수 둘째 자리로 인쇄한 같은 값(104 vs 103.93), 영(0) 채움 유무(null vs 0),
  같은 숫자가 라벨만 바뀐 행(무배당기타 <-> 기타)은 정정이 아니다. 금액 칸(예상보험금·위험보험료)에 값 차이가 남을 때만 RESTATED 로 센다.
  인쇄된 비율 칸만 다르고 금액이 같으면 마스터 숫자(손해율은 금액으로 재계산)가 같으므로 RESTATED 가 아니다(period_adoption.csv 비고에만 기록).
  RESTATED 마다 차이의 성격을 `정정판정` 으로 가른다: 양 블록이 내부 검산(비율 ≈ A÷B, 합계 = Σ포트폴리오)을 통과하면 `진짜 정정`,
  블록 검산 실패·census 이상·한쪽 null 에 몰린 차이면 `추출 확인 필요`(마스터 플래그 `추출확인필요`).
* 경과차년: `1년`~`10년` · `11~15년` · `16~20년` · `21~25년` · `26~30년` · `30년 이후` · `현재가치`.
* 손해율 = 예상보험금 ÷ 위험보험료 x 100 재계산(소수 둘째 자리). 위험보험료가 0 이거나 둘 중 하나가 null 이면 null. 원문 비율(정수 반올림 인쇄)과 반올림 허용
  구간 밖으로 어긋나면 플래그 `비율검산불일치`(값은 재계산 그대로).
* 단위는 억원으로 통일한다. 원문이 백만원이면 값을 환산(÷100)하고 `단위` 열에는 원문 단위(백만원)를, 플래그에 `단위환산(백만원->억원)` 를 남긴다.
  원문 `-`/빗금(해당없음)은 0 이 아니라 null(JSON) / 빈 칸(CSV), 플래그 `대시(-)`.
* 같은 칸이 원본에 두 번 나오면(예: 한 블록 안에 같은 세그먼트의 표가 두 개) 첫 값을 채택하고 플래그 `원본중복칸` 에 버린 값을 남긴다. 조용히 버리지 않는다.
* 티커 = 루트 kics_disclosure.json(없으면 management_indicators.json · IFRS17_BS.json)의 `티커`, 비상장(`X`) 은 공란. 읽기만 한다.
* 마지막에 원본 JSON 과 1:1 자체 검산(행 수 · 키 · 값 · JSON/CSV 재독 일치 · 키 중복 0 · 합계=Σ포트폴리오 · 손해율 재계산)을 하고,
  하나라도 어긋나면 비정상 종료한다. `--verify-only` 는 쓰지 않고 기존 산출만 원본과 대조한다.

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_loss_ratio_master.py [--verify-only] [--no-write]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "loss_ratio"
SRC_B = OUT_DIR / "risk_premium_vs_expected_claims.json"
SRC_CENSUS = OUT_DIR / "census.csv"
OUT_JSON = OUT_DIR / "master_loss_ratio.json"
OUT_CSV = OUT_DIR / "master_loss_ratio.csv"
OUT_TAXONOMY = OUT_DIR / "portfolio_taxonomy.csv"
OUT_ADOPTION = OUT_DIR / "period_adoption.csv"
OUT_MCENSUS = OUT_DIR / "master_census.csv"
REGISTRY_FILES = ("kics_disclosure.json", "management_indicators.json", "IFRS17_BS.json")
UNLISTED_MARK = "X"          # 기존 마스터의 비상장 표기 -> 여기서는 공란

if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER_COLS = ["원보험사코드", "원수사명", "티커", "생손보여부", "공시분기", "경과차년", "구분", "상품구분", "포트폴리오",
               "위험보험료", "예상보험금", "손해율"]
AUX_COLS = ["원문구분", "원문포트폴리오", "세그먼트", "단위", "출처", "추출방식", "플래그"]
ALL_COLS = MASTER_COLS + AUX_COLS
NUM_COLS = ("위험보험료", "예상보험금", "손해율")

PERIOD_ORDER = [f"{i}년" for i in range(1, 11)] + ["11~15년", "16~20년", "21~25년", "26~30년", "30년 이후", "현재가치"]
PERIOD_IDX = {p: i for i, p in enumerate(PERIOD_ORDER)}
METRICS = ("예상보험금", "위험보험료", "비율")
AMT = ("예상보험금", "위험보험료")

# ------------------------------------------------------------------------------------------------
# 표준 분류 사전 (원문 -> 표준). owner 결정: 39사에 같은 기준. 억지 매핑 금지, 모르면 분류미정.
# ------------------------------------------------------------------------------------------------
STD_GUBUN_ORDER = ["합계", "Non-Par", "Direct-Par", "Indirect-Par"]
STD_PRODUCT_ORDER = ["유배당", "무배당", "변액", ""]
STD_PORT_ORDER = ["사망", "건강", "상해", "질병", "재물", "연금저축", "자산연계형연금저축", "기타", "합계"]
PRODUCT_PREFIXES = ("유배당", "무배당", "변액")
PORT_CATEGORIES = ("사망", "건강", "상해", "질병", "재물", "연금저축", "기타")

_PUNCT = re.compile(r"[\s\u00b7\u2219\u318d\u2022\u30fb\u2027\u22c5\u119e.,]")      # 공백·가운뎃점 변형(· ∙ ㆍ • ・ ‧ ⋅ ᆞ)·마침표·쉼표
_HYPHENS = re.compile(r"[\s\-\u2013\u2014\u2212\u2010\u2011\uff0d]")


def norm_pf_key(s: str | None) -> str:
    return _PUNCT.sub("", s or "")


def norm_gb_key(s: str | None) -> str:
    return _HYPHENS.sub("", s or "").lower()


# 구분: 인쇄 변형(DirectPar · directPar · Indirect-PAR · NonPAR ...)은 하이픈·공백 제거 + 소문자로 같은 키가 된다.
GUBUN_DICT = {"합계": "합계", "nonpar": "Non-Par", "directpar": "Direct-Par", "indirectpar": "Indirect-Par"}

# 포트폴리오: 정규화(공백·가운뎃점 제거) 키 -> (상품구분, 포트폴리오).
#  문법 = (유배당|무배당|변액) x (사망|건강|상해|질병|재물|연금저축|기타) + 접두어 없는 `기타` + `자산연계형연금저축`(접두어 없음) + `합계`.
PORT_DICT: dict[str, tuple[str, str]] = {}
for _p in PRODUCT_PREFIXES:
    for _c in PORT_CATEGORIES:
        PORT_DICT[_p + _c] = (_p, _c)
PORT_DICT["기타"] = ("", "기타")
PORT_DICT["자산연계형연금저축"] = ("", "자산연계형연금저축")
PORT_DICT["합계"] = ("", "합계")
# 원문이 훼손된 변형(쪽 경계·각주 문구가 라벨 칸에 붙음). 근거: KR0087 동양생명 PDF 를 열어 확인 -- 라벨은 `변액 연금·저축` 이고
# `및 수재보험계약의` 는 표 바로 아래 각주(`주) 원수보험 및 수재보험계약의 잔여보장요소에 대하여 작성됨`) 글자가 라벨에 섞인 것이다.
PORT_DICT["변액연금저축및"] = ("변액", "연금저축")
PORT_DICT["변액연금저축및수재보험계약의"] = ("변액", "연금저축")
PORT_DICT_NOTES = {
    "변액연금저축및": "원문 라벨 훼손 -- 표 아래 각주('수재보험계약의') 글자가 라벨 칸에 섞임(쪽 경계). 라벨은 변액 연금·저축",
    "변액연금저축및수재보험계약의": "원문 라벨 훼손 -- 표 아래 각주('주) 원수보험 및 수재보험계약의 ...') 글자가 라벨 칸에 섞임. 라벨은 변액 연금·저축",
}
# 표준 라벨별 판단 근거(애매한 것). taxonomy 비고에 붙인다.
STD_NOTES = {
    ("", "기타"): "접두어 없는 `기타`: 유배당/무배당 어느 쪽인지 원문에 없음 -> 상품구분 공란 유지(추정해 붙이지 않음)",
    ("", "자산연계형연금저축"): "`자산연계형` 은 유/무배당·변액과 다른 상품군 라벨이라 접두어가 없음 -> 상품구분 공란, 포트폴리오로 둠",
    ("유배당", "건강"): "생보 `건강` 은 손보 `상해`·`질병` 과 합치지 않음(인쇄 라벨 그대로)",
    ("무배당", "건강"): "생보 `건강` 은 손보 `상해`·`질병` 과 합치지 않음(인쇄 라벨 그대로)",
    ("변액", "건강"): "생보 `건강` 은 손보 `상해`·`질병` 과 합치지 않음(인쇄 라벨 그대로)",
    ("유배당", "상해"): "손보 `상해`·`질병`·`재물` 은 생보 `건강`·`사망` 과 합치지 않음(인쇄 라벨 그대로)",
    ("무배당", "상해"): "손보 `상해`·`질병`·`재물` 은 생보 `건강`·`사망` 과 합치지 않음(인쇄 라벨 그대로)",
}


def std_concat(pv: str, pf: str) -> str:
    """표준 (상품구분, 포트폴리오) -> 추출기 canon 포트폴리오 표기(접두어+분류)와 같은 문자열."""
    return pf if pf == "합계" else pv + pf


def classify(raw_gb: str | None, raw_pf: str | None, canon_pf: str | None, fix_note: str | None = None):
    """-> (구분, 상품구분, 포트폴리오, 플래그 목록, 비고). 사전에 없으면 해당 단 공란 + `분류미정`.
    원문 라벨(raw_pf)의 사전 결과와 추출기 canon 라벨(canon_pf)의 사전 결과가 다르면, 추출기가 문맥으로 보정한 행이다
    (같은 구분에 같은 라벨이 두 번 인쇄돼 순서상 둘째를 보정 등) -> 보정된 라벨을 쓰고 `라벨보정` 플래그 + 비고에 근거를 남긴다."""
    flags: list[str] = []
    notes: list[str] = []
    gb = GUBUN_DICT.get(norm_gb_key(raw_gb))
    if gb is None:
        flags.append("분류미정:구분")
    key = norm_pf_key(raw_pf) if raw_pf else ("합계" if gb == "합계" else "")
    hit = PORT_DICT.get(key)
    if hit is None:
        flags.append("분류미정:포트폴리오")
        pv, pf = "", ""
    else:
        pv, pf = hit
        ckey = norm_pf_key(canon_pf) if canon_pf else None
        chit = PORT_DICT.get(ckey) if ckey else None
        if chit is not None and chit != hit:
            pv, pf = chit
            flags.append("라벨보정")
            notes.append(f"추출기 라벨보정: 원문 `{raw_pf}` -> `{canon_pf}`" + (f" ({fix_note})" if fix_note else " (추출 단계에서 순서·문맥으로 보정)")
                         + " -- 원문만으로는 확정 불가, 오기 가능성")
        if key in PORT_DICT_NOTES:
            notes.append(PORT_DICT_NOTES[key])
    return gb or "", pv, pf, flags, "; ".join(notes)


# ------------------------------------------------------------------------------------------------
# 입출력 유틸
# ------------------------------------------------------------------------------------------------
def retry(fn, what: str, tries: int = 8, wait: float = 5.0):
    """추출기가 산출을 다시 쓰는 도중일 수 있다(JSONDecodeError·PermissionError·빈 파일) -> 몇 초 뒤 재시도."""
    last = None
    for i in range(tries):
        try:
            return fn()
        except (json.JSONDecodeError, PermissionError, OSError, UnicodeDecodeError, csv.Error) as e:   # noqa: PERF203
            last = e
            print(f"  [재시도 {i + 1}/{tries}] {what}: {type(e).__name__} {str(e)[:80]} -- {wait:.0f}s 후", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"{what} 읽기 실패: {last}")


def read_json(path: Path):
    def f():
        txt = path.read_text(encoding="utf-8")
        if not txt.strip():
            raise json.JSONDecodeError("빈 파일", txt, 0)
        return json.loads(txt)
    return retry(f, path.name)


def read_csv(path: Path) -> list[dict]:
    def f():
        with open(path, encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))
    return retry(f, path.name)


def stat_sig(path: Path) -> tuple:
    st = path.stat()
    return (st.st_mtime_ns, st.st_size)


def atomic_write(path: Path, text: str, encoding: str = "utf-8"):
    path = Path(path)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, "w", encoding=encoding, newline="") as f:
        f.write(text)
    last = None
    for _ in range(10):          # Windows: 다른 프로세스가 대상 파일을 잠시 열고 있으면 WinError 5
        try:
            os.replace(tmp, path)
            return
        except PermissionError as e:
            last = e
            time.sleep(1.0)
    raise last


def csv_text(cols: list[str], rows: list[dict], fmt=None) -> str:
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(cols)
    for r in rows:
        w.writerow([(fmt(c, r.get(c)) if fmt else ("" if r.get(c) is None else r.get(c))) for c in cols])
    return buf.getvalue()


def load_registry() -> dict[str, dict]:
    """-> {코드: {name, kind, ticker, in_kics}} (읽기만). ticker 는 비어 있지 않고 `X` 가 아닌 첫 값, 없으면 ''."""
    reg: dict[str, dict] = {}
    for fn in REGISTRY_FILES:
        p = REPO / fn
        if not p.exists():
            print(f"  [경고] {fn} 없음 -- 건너뜀")
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            c = r.get("원보험사코드")
            if not c:
                continue
            e = reg.setdefault(c, {"name": None, "kind": None, "ticker": "", "in_kics": False})
            e["name"] = e["name"] or r.get("원수사명")
            e["kind"] = e["kind"] or r.get("생손보여부")
            if fn == "kics_disclosure.json":
                e["in_kics"] = True
            t = (r.get("티커") or "").strip()
            if t and t != UNLISTED_MARK and not e["ticker"]:
                e["ticker"] = t
    return reg


def fmt_num(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return repr(v) if isinstance(v, float) else str(v)


def num_clean(v):
    """정수형 실수 -> int, 그 외 float (JSON/CSV 표기 통일). 단위 환산에서 생긴 부동소수 잡음은 소수 6자리에서 자른다."""
    if v is None:
        return None
    if isinstance(v, float):
        v = round(v, 6)
        if v.is_integer():
            return int(v)
    return v


def decimals_of(v) -> int:
    if v is None:
        return 0
    s = repr(float(v))
    if "e" in s or "E" in s:
        return 6
    frac = s.split(".")[1].rstrip("0") if "." in s else ""
    return len(frac)


def same_print(a: float, da: int, b: float, db: int) -> bool:
    """두 인쇄값이 같은 값의 다른 인쇄 정밀도인가. 자릿수가 같으면 정확히 같아야 한다(2261 != 2262). 자릿수가 다르면 각 값이 속하는 반올림 구간
    [v-0.5*10^-d, v+0.5*10^-d] 이 겹치면 같다(104 ~ 103.93, 0.012 ~ 0.0119, 5 ~ 5.2). 겹침 길이가 0(경계만 닿음)이면 다른 값이다."""
    if abs(a - b) < 1e-9:
        return True
    if da == db:
        return False
    ua, ub = 0.5 * 10 ** (-da), 0.5 * 10 ** (-db)
    return max(a - ua, b - ub) < min(a + ua, b + ub) - 1e-12


UNIT_TO_EOK = {"억원": 1.0, "천만원": 0.1, "백만원": 0.01, "만원": 0.0001, "천원": 1e-5, "원": 1e-8}
UNIT_DEC_SHIFT = {"억원": 0, "천만원": 1, "백만원": 2, "만원": 4, "천원": 5, "원": 8}


def pdf_q_of_file(path: str) -> str | None:
    m = re.search(r"FY(\d{4})_Q([1-4])", path or "")
    return f"{m.group(1)}.{m.group(2)}Q" if m else None


def amount_dec(orig_val, orig_unit: str | None) -> int:
    """억원으로 본 인쇄 자릿수 = 원문 인쇄 소수 자리 + 단위 이동(백만원 -> +2)."""
    return (decimals_of(orig_val) if orig_val is not None else 0) + UNIT_DEC_SHIFT.get(orig_unit or "억원", 0)


# 한 회사 안의 추가 축(코리안리: 부문 생명/장기손해 x 사업구분 전통형재보험/공동재보험). 마스터 `세그먼트` 열 = 있는 축을 `/` 로 이은 값.
SEGMENT_FIELDS = ("부문", "사업구분")
KNOWN_FIELDS = {"원보험사코드", "원수사명", "생손보여부", "공시분기", "기준연도", "구분", "구분_원문", "포트폴리오", "포트폴리오_원문", "경과기간", "지표", "값",
                "단위", "dash", "출처", "추출방식", "원천위치", "라벨보정", "원값", "원단위", "숫자출처", "원문오기", "텍스트층보정"} | set(SEGMENT_FIELDS)


def seg_of(r: dict) -> str:
    return "/".join(str(r[f]) for f in SEGMENT_FIELDS if r.get(f))


# ------------------------------------------------------------------------------------------------
# 블록 조립: (회사, PDF 공시분기, 기준연도) -> 셀
# ------------------------------------------------------------------------------------------------
def norm_cells(rows: list[dict]):
    """원본 long 행 -> 블록 {(코드, PDF분기, 연도): {...}}. 각 셀 = {지표: 값정보}. 라벨 표준화·단위 환산을 여기서 한다.
    + taxonomy census {(원문구분, 원문포트폴리오, 세그먼트, 표준3단, 비고, 플래그): {codes, n}}."""
    blocks: dict[tuple, dict] = {}
    tax: dict[tuple, dict] = {}
    for r in rows:
        code, pq, yr = r["원보험사코드"], r["공시분기"], r["기준연도"]
        raw_gb, raw_pf = r.get("구분_원문") or r.get("구분"), r.get("포트폴리오_원문")
        seg = seg_of(r)
        gb, pv, pf, clsflags, note = classify(raw_gb, raw_pf, r.get("포트폴리오"), r.get("라벨보정"))
        # 추출기 canon 라벨과 사전 결과가 어긋나면(사전 오류 또는 canon 오류) 플래그: 어느 한쪽이 틀렸다는 뜻이라 조용히 넘기지 않는다
        if not any(f.startswith("분류미정") for f in clsflags):
            if r.get("구분") != gb or (r.get("포트폴리오") is not None and r.get("포트폴리오") != std_concat(pv, pf)):
                clsflags = clsflags + [f"분류불일치(추출기 canon {r.get('구분')}|{r.get('포트폴리오')} / 사전 {gb}|{std_concat(pv, pf)})"]
        tkey = (raw_gb or "", raw_pf or "", seg, gb, pv, pf, note, tuple(f for f in clsflags if f != "라벨보정"))
        t = tax.setdefault(tkey, {"codes": set(), "n": 0})
        t["codes"].add(code)
        t["n"] += 1
        k = (code, pq, yr)
        blk = blocks.setdefault(k, {"cells": {}, "n_src": 0, "n_used": 0, "dup_list": [], "files": set(), "pages": set()})
        blk["n_src"] += 1
        kg = gb if gb else f"?{raw_gb}"
        kpf = pf if pf else f"?{raw_pf}"
        ck = (seg, kg, pv, kpf, r["경과기간"])
        cell = blk["cells"].setdefault(ck, {"g": gb, "pv": pv, "pf": pf, "seg": seg, "period": r["경과기간"], "raw_gb": raw_gb or "",
                                            "raw_pf": raw_pf or "", "canon_gb": r.get("구분"), "canon_pf": r.get("포트폴리오"),
                                            "cls": list(clsflags), "m": {}, "dups": []})
        m = r["지표"]
        val = r["값"]
        unit = r["단위"]
        orig_unit = r.get("원단위") or unit
        orig_val = r.get("원값", val)
        conv_note = None
        if m in AMT:
            if val is not None and unit not in ("억원", None):
                if unit in UNIT_TO_EOK:
                    val = round(val * UNIT_TO_EOK[unit], 6)
                    conv_note = f"단위환산({unit}->억원)"
                else:
                    conv_note = f"단위미상({unit})"
            elif r.get("원단위") and r.get("원단위") != "억원" and unit == "억원":
                conv_note = f"단위환산({r['원단위']}->억원)"          # 추출기가 이미 환산함
            dec = amount_dec(orig_val, orig_unit)
        else:
            if r.get("원단위") == "배(소수)":
                conv_note = "비율단위환산(배->%)"
                dec = max(decimals_of(orig_val) - 2, 0)
            else:
                dec = decimals_of(val)
        if m in cell["m"]:                            # 같은 칸 두 번: 첫 값 채택, 버린 값은 플래그로
            prev = cell["m"][m]
            blk["dup_list"].append((ck, m, prev["v"], val, r["출처"]["page"]))
            cell["dups"].append(f"{m}(채택 {fmt_num(prev['v'])} / 버림 {fmt_num(val)})")
            continue
        cell["m"][m] = {"v": val, "orig_v": orig_val, "orig_unit": orig_unit, "dec": dec, "dash": bool(r.get("dash")), "conv": conv_note,
                        "errata": r.get("원문오기"), "textfix": r.get("텍스트층보정"), "numsrc": r.get("숫자출처"),
                        "src": r["출처"], "how": r["추출방식"], "where": r.get("원천위치"), "unit": unit}
        blk["n_used"] += 1
        blk["pages"].add((r["출처"]["file"], r["출처"]["page"]))
        blk["files"].add(r["출처"]["file"])
    return blocks, tax


def block_usable(blk) -> bool:
    return bool(blk) and any(c["v"] is not None for cell in blk["cells"].values() for m, c in cell["m"].items() if m in AMT)


def row_cells(blk: dict) -> dict:
    """행키(세그먼트, 구분, 상품구분, 포트폴리오) -> {(경과차년, 지표): (값, 자릿수)} -- null 칸은 뺀다(행은 유지)."""
    rows: dict[tuple, dict] = defaultdict(dict)
    for ck, cell in blk["cells"].items():
        rk = ck[:4]
        rows.setdefault(rk, {})
        for m, c in cell["m"].items():
            if c["v"] is not None:
                rows[rk][(cell["period"], m)] = (c["v"], c["dec"])
    return rows


def ratio_consistent(a, b, printed, dec_a, dec_b, dec_r) -> bool | None:
    """원문 인쇄 비율이 A÷B x 100 의 반올림 허용 구간 안인가. None = 검산 불가(분모 구간이 0 을 지남)."""
    if a is None or b is None or printed is None:
        return None
    uA, uB, uR = 0.5 * 10 ** (-dec_a), 0.5 * 10 ** (-dec_b), 0.5 * 10 ** (-dec_r)
    if b - uB <= 0:
        return None
    cors = [(a + sa * uA) / (b + sb * uB) * 100 for sa in (-1, 1) for sb in (-1, 1)]
    return min(cors) - uR - 1e-9 <= printed <= max(cors) + uR + 1e-9


def total_tol(vals_dec: list[int]) -> float:
    """합계 = Σ 포트폴리오 허용오차: (항목 수+1) x 가장 거친 인쇄 자릿수의 반올림 반폭."""
    return len(vals_dec) * 0.5 * 10 ** (-min(vals_dec)) + 1e-9


def block_checks(blk: dict) -> dict:
    """블록 내부 검산(추출 정합성): 비율 ≈ A÷B x 100(반올림 허용 구간), 합계 = Σ 포트폴리오(원문오기 칸 제외). 둘 다 통과해야 '내부 일관'."""
    st = {"ratio_checked": 0, "ratio_fail": 0, "total_checked": 0, "total_fail": 0, "skipped_errata": 0}
    parts = defaultdict(lambda: {"tot": None, "parts": []})
    for ck, cell in blk["cells"].items():
        m = cell["m"]
        a, b, q = m.get("예상보험금"), m.get("위험보험료"), m.get("비율")
        if a and b and q and a["v"] is not None and b["v"] is not None and q["v"] is not None:
            if a["errata"] or b["errata"] or q["errata"]:
                st["skipped_errata"] += 1
            else:
                ok = ratio_consistent(a["v"], b["v"], q["v"], a["dec"], b["dec"], q["dec"])
                if ok is not None:
                    st["ratio_checked"] += 1
                    if not ok:
                        st["ratio_fail"] += 1
        for mm in AMT:
            c = m.get(mm)
            if c is None or c["v"] is None:
                continue
            slot = parts[(ck[0], cell["period"], mm)]
            if cell["g"] == "합계":
                slot["tot"] = c
            else:
                slot["parts"].append(c)
    for slot in parts.values():
        t = slot["tot"]
        if t is None or not slot["parts"]:
            continue
        if t["errata"] or any(p["errata"] for p in slot["parts"]):
            st["skipped_errata"] += 1
            continue
        s = sum(p["v"] for p in slot["parts"])
        tol = total_tol([t["dec"]] + [p["dec"] for p in slot["parts"]])
        st["total_checked"] += 1
        if abs(s - t["v"]) > tol:
            st["total_fail"] += 1
    st["consistent"] = st["ratio_fail"] == 0 and st["total_fail"] == 0
    return st


def cell_cmp(pa, na):
    """한 칸 비교. pa/na = (값, 자릿수) | None. -> eq | prec(정밀도만 다름) | zero(null<->0) | diff | none(둘 다 0/없음)."""
    if pa is None and na is None:
        return "none"
    if pa is None or na is None:
        v = (pa or na)[0]
        return "zero" if v == 0 else "diff"
    if abs(pa[0] - na[0]) < 1e-9:
        return "eq" if pa[0] != 0 else "none"
    return "prec" if same_print(pa[0], pa[1], na[0], na[1]) else "diff"


def compare_blocks(pb: dict, nb: dict) -> dict:
    """두 블록(같은 회사·같은 기준연도, 다른 공시)의 칸 단위 대조. 인쇄 정밀도·영채움·라벨 변경을 정정에서 뺀다."""
    P, N = row_cells(pb), row_cells(nb)
    cells: dict[tuple, tuple] = {}
    for rk in set(P) | set(N):
        pc, nc = P.get(rk, {}), N.get(rk, {})
        for k in set(pc) | set(nc):
            cells[(rk, k)] = (cell_cmp(pc.get(k), nc.get(k)), pc.get(k), nc.get(k))

    def lost(side: dict, other: dict) -> dict:
        """이 쪽에서 0 아닌 금액칸이 전부 반대쪽 같은 행키에서는 비어(없음/null/0) 있는 행."""
        out = {}
        for rk, cs in side.items():
            nz = {k: v for k, v in cs.items() if k[1] in AMT and v[0] != 0}
            if nz and all(k not in other.get(rk, {}) or other[rk][k][0] == 0 for k in nz):
                out[rk] = nz
        return out
    lostP, lostN = lost(P, N), lost(N, P)
    relabel: list[tuple] = []
    used_n: set = set()
    for rp, sp_ in sorted(lostP.items(), key=lambda kv: str(kv[0])):
        for rn, sn in sorted(lostN.items(), key=lambda kv: str(kv[0])):
            if rn in used_n or rp[:2] != rn[:2] or set(sp_) != set(sn):
                continue
            if all(same_print(sp_[k][0], sp_[k][1], sn[k][0], sn[k][1]) for k in sp_):
                relabel.append((rp, rn))
                used_n.add(rn)
                break
    moved = {rk for pair in relabel for rk in pair}
    n_cmp = n_prec = n_zero = n_eq = 0
    diffs = []
    for (rk, k), (cls, a, b) in cells.items():
        if rk in moved or cls == "none":
            continue
        if cls == "zero":
            n_zero += 1
            continue
        n_cmp += 1
        if cls == "eq":
            n_eq += 1
        elif cls == "prec":
            n_prec += 1
        else:
            diffs.append(((rk, k[0], k[1]), a[0] if a else None, b[0] if b else None))
    diffs.sort(key=lambda x: (str(x[0][0]), PERIOD_IDX.get(x[0][1], 99), x[0][2]))
    amt = [x for x in diffs if x[0][2] in AMT]
    rat = [x for x in diffs if x[0][2] == "비율"]
    amt_both = [abs(a - b) for _, a, b in amt if a is not None and b is not None]
    rat_both = [abs(a - b) for _, a, b in rat if a is not None and b is not None]
    return {"n": n_cmp, "n_eq": n_eq, "n_prec": n_prec, "n_zero": n_zero, "diffs": diffs, "amt_diffs": amt, "ratio_diffs": rat,
            "relabel": relabel,
            "amt_one_sided": len(amt) - len(amt_both), "ratio_one_sided": len(rat) - len(rat_both),
            "max_amt": max(amt_both) if amt_both else (None if amt else 0.0),          # None = 차이가 전부 한쪽 null 이라 크기를 못 잼
            "max_ratio": max(rat_both) if rat_both else (None if rat else 0.0)}


def block_values_for_same(blk: dict) -> dict:
    """SAME_AS_PRIOR_YEAR 판정용: {(셀키 중 세그먼트·구분·상품구분·포트폴리오·경과차년, 지표): (값, 자릿수)} 값 있는 칸."""
    out = {}
    for ck, cell in blk["cells"].items():
        for m, c in cell["m"].items():
            if c["v"] is not None:
                out[(ck, m)] = (c["v"], c["dec"])
    return out


def same_fraction(va: dict, vb: dict) -> tuple[int, int]:
    same = sum(1 for k, v in va.items() if k in vb and same_print(v[0], v[1], vb[k][0], vb[k][1]))
    return same, max(len(va), len(vb))


# ------------------------------------------------------------------------------------------------
# 공시분기 채택 (§5-1)
# ------------------------------------------------------------------------------------------------
STATUS_PRIORITY = ["PARSE_FAILED", "UNREADABLE", "SCAN_PENDING", "FILLED_CHECK_FLAGS", "FILLED(vision)", "FILLED", "ABSENT_IN_SOURCE", "NO_PDF"]


def agg_census(rows: list[dict]) -> dict:
    """같은 (회사, PDF분기, 기준연도)에 census 행이 여럿(코리안리: 기준연도 `2024|공동재보험` 처럼 사업별)이면 하나로 합친다.
    상태는 STATUS_PRIORITY 앞쪽(문제 있는 쪽) 우선 -- 단 FILLED 계열과 ABSENT 가 섞이면 FILLED 계열을 따른다."""
    if len(rows) == 1:
        return rows[0]
    st = min((r["상태"] for r in rows), key=lambda s: STATUS_PRIORITY.index(s) if s in STATUS_PRIORITY else -1)

    def num(r, k):
        try:
            return int(r.get(k) or 0)
        except ValueError:
            return 0
    return {**rows[0], "상태": st, "셀수": str(sum(num(r, "셀수") for r in rows)), "값있는셀수": str(sum(num(r, "값있는셀수") for r in rows)),
            "근거": " || ".join(f"[{r.get('_sub') or '-'}] {r['상태']}: {(r.get('근거') or '')[:110]}" for r in rows)}


def census_index(census: list[dict]) -> dict:
    """표 B census -> {(코드, PDF분기, 기준연도 or ''): 행}. 기준연도 칸이 `2024|공동재보험` 이면 연도만 키로 쓰고 사업 이름은 `_sub`."""
    grp: dict[tuple, list] = defaultdict(list)
    for r in census:
        if not (r.get("표") or "").startswith("B"):
            continue
        yr_raw = (r.get("기준연도") or "").strip()
        yr, _, sub = yr_raw.partition("|")
        r = dict(r)
        r["기준연도"], r["_sub"] = yr.strip(), sub.strip()
        grp[(r["원보험사코드"], r["공시분기"], r["기준연도"])].append(r)
    return {k: agg_census(v) for k, v in grp.items()}


def cen_of(census: dict, code: str, pq: str, yr: int):
    return census.get((code, pq, str(yr))) or census.get((code, pq, ""))


def valid_block_keys(blocks: dict) -> tuple[dict, list]:
    """§5-1 이 쓰는 블록만: Y.4Q PDF 의 <Y> · <Y-1> 블록. 그 밖의 블록(가짜 연도·분기 어긋남)은 따로 모아 보고한다."""
    ok, unused = {}, []
    for k, b in blocks.items():
        code, pq, yr = k
        if pq.endswith(".4Q") and yr in (int(pq[:4]), int(pq[:4]) - 1):
            ok[k] = b
        else:
            unused.append(k)
    return ok, sorted(unused)


def adopt_periods(blocks: dict, census: dict):
    """-> {(코드, 공시분기): 결정 dict}. 결정 = {adopted: (코드,PDF분기,연도)|None, flags, compare, ...}."""
    codes = sorted({k[0] for k in blocks})
    years = sorted({k[2] for k in blocks})
    if not years:
        return {}
    qs = [f"{y}.4Q" for y in range(min(years), max(years) + 1)]
    out = {}
    for code in codes:
        for q in qs:
            y = int(q[:4])
            pk = (code, q, y)                                # 당기 블록(Y.4Q PDF 의 <Y년>)
            nk = (code, f"{y + 1}.4Q", y)                    # 후속 공시의 전기 블록
            pb, nb = blocks.get(pk), blocks.get(nk)
            pu, nu = block_usable(pb), block_usable(nb)
            pc, nc = cen_of(census, code, q, y), cen_of(census, code, f"{y + 1}.4Q", y)
            if not pu and not nu:
                if pb or nb:
                    out[(code, q)] = {"adopted": None, "flags": ["NO_USABLE_BLOCK"], "cands": [k for k, b in ((pk, pb), (nk, nb)) if b],
                                      "compare": None, "primary": None, "next": None, "primary_cen": pc, "next_cen": nc}
                continue
            d = {"adopted": None, "flags": [], "compare": None, "primary": pk if pu else None, "next": nk if nu else None,
                 "primary_cen": pc, "next_cen": nc}
            if pu and nu:
                cmp_ = compare_blocks(pb, nb)
                d["compare"] = cmp_
                if cmp_["amt_diffs"]:
                    d["adopted"] = nk
                    d["flags"].append("RESTATED")
                else:
                    d["adopted"] = pk
            elif pu:
                d["adopted"] = pk
                if y < max(years):
                    d["flags"].append("정정미확인(후속 공시에 전기 블록 없음)")
            else:
                d["adopted"] = nk
                d["flags"].append("FROM_NEXT_YEAR_PRIOR_BLOCK")
            ak = d["adopted"]
            ev = census.get(ak) or cen_of(census, ak[0], ak[1], ak[2])
            if ev is None:
                d["flags"].append("census칸없음")          # 행은 있는데 추출 census 에 그 블록이 없다 -> 추출기 산출이 어긋남
            elif ev["상태"] not in ("FILLED", "FILLED(vision)"):
                d["flags"].append(ev["상태"])
            sib = blocks.get((ak[0], ak[1], ak[2] - 1))
            if sib and block_usable(sib):
                same, tot = same_fraction(block_values_for_same(blocks[ak]), block_values_for_same(sib))
                if tot >= 50 and same / tot >= 0.99:
                    d["flags"].append("SAME_AS_PRIOR_YEAR")
                    d["same_prior"] = (same, tot)
            out[(code, q)] = d
    return out


def classify_restatement(d: dict, blocks: dict) -> tuple[str, str]:
    """RESTATED 판정의 성격: (정정판정, 근거). 진짜 정정 = 양 블록이 내부 검산을 통과했고 차이가 한쪽 null 에 몰리지 않음.
    그렇지 않으면 `추출 확인 필요`(라벨 어긋남·열 밀림·판독 오류로 생긴 가짜 차이 가능성)."""
    cmp_ = d["compare"]
    pb, nb = blocks[d["primary"]], blocks[d["next"]]
    cp, cn = block_checks(pb), block_checks(nb)
    uncertain, info = [], []
    for tag, chk in (("당기", cp), ("전기", cn)):
        if not chk["consistent"]:
            uncertain.append(f"{tag} 블록 내부 검산 실패(비율 {chk['ratio_fail']}/{chk['ratio_checked']}·합계 {chk['total_fail']}/{chk['total_checked']})")
    for tag, blk, cen in (("당기", pb, d.get("primary_cen")), ("전기", nb, d.get("next_cen"))):
        if cen and cen["상태"] not in ("FILLED", "FILLED(vision)"):
            uncertain.append(f"{tag} 블록 census {cen['상태']}")
        if blk["dup_list"]:
            uncertain.append(f"{tag} 블록에 원본 중복칸 {len(blk['dup_list'])}건")
        if any(c["how"] == "vision" for cell in blk["cells"].values() for c in cell["m"].values()):
            info.append(f"{tag} 블록은 vision 판독(내부 검산은 통과)")
    amt = cmp_["amt_diffs"]
    one_sided = [x for x in amt if x[1] is None or x[2] is None]
    if amt and len(one_sided) == len(amt):
        uncertain.append("금액 차이가 전부 한쪽 null(대시) 칸")
    fixed = []
    for (rk, per, m), a, b in amt:
        for cell in pb["cells"].values():
            if (cell["seg"], cell["g"], cell["pv"], cell["pf"]) == rk and cell["period"] == per:
                c = cell["m"].get(m)
                if c and c.get("errata") and a is not None and b is not None:
                    fixed.append(f"{'/'.join(x for x in rk if x)} {per} {m}: {a:g}->{b:g}")
    reasons = []
    if fixed:
        reasons.append(f"원문오기 정정 {len(fixed)}칸(당기 공시의 인쇄 오기를 후속 공시가 정정): " + "; ".join(fixed[:3]))
    if amt and cmp_["max_amt"] is not None and cmp_["max_amt"] <= 1.0 and not one_sided:
        reasons.append("금액 차이 전부 ±1억원 이내(반올림 수준 재계산)")
    rows = {x[0][0] for x in amt}
    mx_txt = f"최대 {cmp_['max_amt']:g}억원" if cmp_["max_amt"] is not None else "양쪽에 값이 있는 차이 칸 없음"
    reasons.append(f"금액 차이 행 {len(rows)}개·{len(amt)}칸({mx_txt}" + (f", 한쪽 null {len(one_sided)}칸" if one_sided and cmp_["max_amt"] is not None else "") + ")")
    if uncertain:
        return "추출 확인 필요", "; ".join(uncertain + reasons + info)
    return "진짜 정정(양 블록 내부 검산 통과)", "; ".join(reasons + info)


# ------------------------------------------------------------------------------------------------
# 마스터 행
# ------------------------------------------------------------------------------------------------
def master_rows_for_block(code: str, q: str, blk: dict, reg: dict, blockflags: list[str]) -> list[dict]:
    e = reg.get(code) or {"name": None, "kind": None, "ticker": ""}
    rows = []
    units = Counter(c["orig_unit"] for cell in blk["cells"].values() for mm, c in cell["m"].items() if mm in AMT and c["v"] is not None)
    block_unit = units.most_common(1)[0][0] if units else "억원"          # 금액 지표가 아예 없는 칸의 단위 표기용
    for ck, cell in blk["cells"].items():
        m = cell["m"]
        ca, cb, cq = m.get("예상보험금"), m.get("위험보험료"), m.get("비율")
        a = ca["v"] if ca else None
        b = cb["v"] if cb else None
        pr = cq["v"] if cq else None
        loss = round(a / b * 100, 2) if (a is not None and b is not None and b != 0) else None
        flags = list(blockflags)
        if b == 0 and a not in (None, 0):
            flags.append("위험보험료0(손해율 null)")
        if cq and pr is not None and ca and cb and a is not None and b is not None:
            if ratio_consistent(a, b, pr, ca["dec"], cb["dec"], cq["dec"]) is False:
                exp = (a / b * 100) if b else float("nan")
                flags.append(f"비율검산불일치(원문 {fmt_num(pr)} / 재계산 {exp:.2f})")
        dash_fields = [mm for mm in METRICS if mm in m and m[mm]["v"] is None]
        absent_fields = [mm for mm in METRICS if mm not in m]
        if dash_fields:
            flags.append("대시(-):" + "/".join(dash_fields))
        if absent_fields:
            flags.append("지표없음:" + "/".join(absent_fields))
        for mm in METRICS:
            c = m.get(mm)
            if not c:
                continue
            if c["errata"]:
                flags.append(f"원문오기:{mm}")
            if c["textfix"]:
                flags.append(f"텍스트층보정:{mm}")
            if c["numsrc"]:
                flags.append(f"숫자출처:{c['numsrc']}")
            if c["conv"] and c["conv"] not in flags:
                flags.append(c["conv"])
            if c["where"] == "뒤쪽사본" and "원천=뒤쪽사본" not in flags:
                flags.append("원천=뒤쪽사본")
        if cell["dups"]:
            flags.append("원본중복칸:" + "/".join(cell["dups"]))
        if cell["period"] not in PERIOD_IDX:
            flags.append(f"경과차년표준외({cell['period']})")          # 예: 1~10년 합산 열 -- owner 가 정한 경과차년 목록 밖이라 쪼개지 않고 원문 그대로 둔다
        flags += [f for f in cell["cls"] if f not in flags]
        by_file = defaultdict(set)
        for c in m.values():
            by_file[c["src"]["file"]].add(c["src"]["page"])
        src_txt = "; ".join(f"{f_}:{','.join(str(p) for p in sorted(ps))}" for f_, ps in sorted(by_file.items()))
        hows = sorted({c["how"] for c in m.values()})
        orig_units = sorted({c["orig_unit"] for mm, c in m.items() if mm in AMT and c["v"] is not None}) or \
            sorted({c["orig_unit"] for mm, c in m.items() if mm in AMT}) or [block_unit]
        rows.append({
            "원보험사코드": code,
            "원수사명": e["name"] or blk.get("name") or "",
            "티커": e["ticker"],
            "생손보여부": e["kind"] or blk.get("kind") or "",
            "공시분기": q,
            "경과차년": cell["period"],
            "구분": cell["g"],
            "상품구분": cell["pv"],
            "포트폴리오": cell["pf"],
            "위험보험료": num_clean(b),
            "예상보험금": num_clean(a),
            "손해율": loss,
            "원문구분": cell["raw_gb"],
            "원문포트폴리오": cell["raw_pf"],
            "세그먼트": cell["seg"],
            "단위": "/".join(orig_units),
            "출처": src_txt,
            "추출방식": "+".join(hows),
            "플래그": "; ".join(dict.fromkeys(flags)),
        })
    return rows


def sort_key(r: dict):
    g = STD_GUBUN_ORDER.index(r["구분"]) if r["구분"] in STD_GUBUN_ORDER else 9
    pv = STD_PRODUCT_ORDER.index(r["상품구분"]) if r["상품구분"] in STD_PRODUCT_ORDER else 9
    pf = STD_PORT_ORDER.index(r["포트폴리오"]) if r["포트폴리오"] in STD_PORT_ORDER else 9
    return (r["원보험사코드"], r["공시분기"], r["세그먼트"], g, pv, pf, r["원문포트폴리오"], PERIOD_IDX.get(r["경과차년"], 99))


def format_cell(col, v):
    if v is None:
        return ""
    if col == "손해율":
        return f"{v:.2f}"
    if col in NUM_COLS:
        return fmt_num(v)
    return v


def restated_flag_text(d: dict) -> str:
    cmp_ = d["compare"]
    s = f"차이 {len(cmp_['amt_diffs'])}/{cmp_['n']}칸(금액)"
    if cmp_["max_amt"] is not None:
        s += f", 최대차 {cmp_['max_amt']:g}억원"
    if cmp_["amt_one_sided"]:
        s += f", 한쪽 null {cmp_['amt_one_sided']}칸"
    if cmp_["ratio_diffs"]:
        s += f", 비율칸 차이 {len(cmp_['ratio_diffs'])}"
    return f"RESTATED({s})"


def block_desc(key, blocks: dict) -> str:
    if not key:
        return ""
    blk = blocks[key]
    files = sorted(blk["files"])
    pages = sorted({p for _, p in blk["pages"]})
    pg = f"p{pages[0]}" if len(pages) == 1 else f"p{pages[0]}-{pages[-1]}"
    return f"{files[0] if files else key[1]} <{key[2]}년> {pg}"


# ------------------------------------------------------------------------------------------------
# 전체 빌드
# ------------------------------------------------------------------------------------------------
def build():
    sig0 = (stat_sig(SRC_B), stat_sig(SRC_CENSUS))
    src_rows = read_json(SRC_B)
    census_rows = read_csv(SRC_CENSUS)
    sig1 = (stat_sig(SRC_B), stat_sig(SRC_CENSUS))
    if sig0 != sig1:
        print("  [경고] 읽는 도중 입력 파일이 바뀌었다(추출기 실행 중) -- 이번 산출은 두 입력이 어긋날 수 있다. 추출기가 끝난 뒤 다시 실행하라.")
    return build_from(src_rows, census_rows, load_registry())


def build_from(src_rows: list[dict], census_rows: list[dict], reg: dict):
    keys_seen: Counter = Counter()
    for r in src_rows:
        keys_seen.update(r.keys())
    unknown = {k: n for k, n in keys_seen.items() if k not in KNOWN_FIELDS}
    if unknown:
        print(f"  [경고] 원본 행에 이 변환기가 모르는 필드가 있다(마스터에 안 실림 -- 새 축이면 SEGMENT_FIELDS/사전 보강 필요): {unknown}")
    blocks_all, tax = norm_cells(src_rows)
    blocks, unused = valid_block_keys(blocks_all)
    cidx = census_index(census_rows)
    fallback = {}
    for r in src_rows:
        fallback.setdefault(r["원보험사코드"], (r.get("원수사명"), r.get("생손보여부")))
    for blk_key, blk in blocks_all.items():
        blk["name"], blk["kind"] = fallback.get(blk_key[0], ("", ""))
    decisions = adopt_periods(blocks, cidx)
    master = []
    for (code, q), d in sorted(decisions.items()):
        ak = d["adopted"]
        if ak is None:
            continue
        flags = list(d["flags"])
        if "RESTATED" in flags:
            verdict, why = classify_restatement(d, blocks)
            d["verdict"], d["verdict_why"] = verdict, why
            flags[flags.index("RESTATED")] = restated_flag_text(d)
            if verdict.startswith("추출 확인 필요"):
                flags.append("추출확인필요")
        if "SAME_AS_PRIOR_YEAR" in flags and d.get("same_prior"):
            flags[flags.index("SAME_AS_PRIOR_YEAR")] = f"SAME_AS_PRIOR_YEAR({d['same_prior'][0]}/{d['same_prior'][1]}칸 동일)"
        d["flag_text"] = flags
        master += master_rows_for_block(code, q, blocks[ak], reg, flags)
    master.sort(key=sort_key)
    return {"master": master, "decisions": decisions, "blocks": blocks, "blocks_all": blocks_all, "unused_blocks": unused, "tax": tax,
            "census_idx": cidx, "reg": reg, "src_rows": src_rows, "census_rows": census_rows, "unknown_fields": unknown}


# ------------------------------------------------------------------------------------------------
# 보조 산출: taxonomy / period_adoption / master_census
# ------------------------------------------------------------------------------------------------
TAX_COLS = ["원문구분", "원문포트폴리오", "세그먼트", "회사수", "회사목록", "표준_구분", "표준_상품구분", "표준_포트폴리오", "비고"]


def bare_other_evidence(res: dict) -> str:
    """접두어 없는 `기타` 의 정체를 가리는 근거(owner 판단용): 값이 있는 회사, 같은 블록에 유/무배당 기타도 값이 있는 회사, 후속 공시에서 같은 숫자가 접두어 붙은 기타로 재인쇄된 회사."""
    withvals, both = set(), set()
    for (code, pq, yr), blk in res["blocks"].items():
        has = defaultdict(set)
        for cell in blk["cells"].values():
            if cell["pf"] == "기타" and any(c["v"] is not None for c in cell["m"].values()):
                has[(cell["seg"], cell["g"])].add(cell["pv"])
        for pvs in has.values():
            if "" in pvs:
                withvals.add(code)
                if len(pvs) > 1:
                    both.add(code)
    reprinted: dict[str, set] = defaultdict(set)
    for (code, q), d in res["decisions"].items():
        for rp, rn in (d.get("compare") or {}).get("relabel", []):
            if rp[2:] == ("", "기타") and rn[3] == "기타" and rn[2]:
                reprinted[code].add(rn[2])
    if not withvals:
        return ""
    s = f"값이 있는 접두어 없는 `기타` 행이 나온 회사 {len(withvals)}곳({','.join(sorted(withvals))})"
    if both:
        s += f"; 그중 {','.join(sorted(both))} 는 같은 블록에 유배당기타·무배당기타(또는 변액기타)도 값이 있어 별도 행이라 합칠 수 없음"
    if reprinted:
        s += "; " + ",".join(f"{c}({'/'.join(sorted(v))})" for c, v in sorted(reprinted.items())) + " 는 후속 공시가 같은 숫자를 접두어 붙은 기타로 재인쇄(라벨만 변경) -> 접두어 없는 기타가 그쪽일 수 있으나 회사별 확정 불가"
    return s


def taxonomy_rows(res: dict) -> list[dict]:
    tax = res["tax"]
    bare_note = bare_other_evidence(res)
    rows = []
    for (raw_gb, raw_pf, seg, gb, pv, pf, note, flags), t in tax.items():
        notes = []
        if any(f.startswith("분류미정") for f in flags):
            notes.append("분류미정 -- 사전에 없는 라벨(표준 공란, 원문 유지). 사전 보강 여부는 owner 판단")
        notes += [f for f in flags if not f.startswith("분류미정")]
        if note:
            notes.append(note)
        if gb and raw_gb and raw_gb != gb and raw_gb != "합계":
            notes.append("구분 인쇄 변형(대소문자·하이픈) -> 같은 표준")
        std_pf = std_concat(pv, pf)
        if pf and raw_pf and raw_pf != std_pf and not note:
            notes.append("포트폴리오 인쇄 변형(가운뎃점 · ∙ ㆍ 또는 글자 분리) -> 정규화 후 같은 표준")
        if (pv, pf) in STD_NOTES and not any(f.startswith("분류미정") for f in flags):
            notes.append(STD_NOTES[(pv, pf)])
        if (pv, pf) == ("", "기타") and bare_note:
            notes.append(bare_note)
        if seg:
            notes.append(f"세그먼트 `{seg}`: 한 회사 안의 추가 축(부문/사업구분) -- 마스터 키 = 세그먼트+구분+상품구분+포트폴리오(세그먼트별 합계 행이 따로 있음)")
        rows.append({"원문구분": raw_gb, "원문포트폴리오": raw_pf, "세그먼트": seg, "회사수": len(t["codes"]),
                     "회사목록": ",".join(sorted(t["codes"])), "표준_구분": gb, "표준_상품구분": pv, "표준_포트폴리오": pf,
                     "비고": "; ".join(dict.fromkeys(notes))})

    def k(r):
        g = STD_GUBUN_ORDER.index(r["표준_구분"]) if r["표준_구분"] in STD_GUBUN_ORDER else 9
        pv = STD_PRODUCT_ORDER.index(r["표준_상품구분"]) if r["표준_상품구분"] in STD_PRODUCT_ORDER else 9
        pf = STD_PORT_ORDER.index(r["표준_포트폴리오"]) if r["표준_포트폴리오"] in STD_PORT_ORDER else 9
        return (r["표준_구분"] == "", g, pv, pf, r["원문구분"], r["원문포트폴리오"], r["세그먼트"])
    rows.sort(key=k)
    return rows


ADOPT_COLS = ["원보험사코드", "원수사명", "공시분기", "채택원천", "대조원천", "비교칸수", "차이칸수", "금액차이칸", "비율차이칸", "최대차", "최대차_비율pp",
              "정밀도차이칸", "영채움칸", "라벨변경행수", "정정판정", "플래그", "비고"]


def census_text(cen) -> str:
    if not cen:
        return "census 칸 없음"
    nv = f" [셀 {cen.get('셀수')}·값 있는 셀 {cen.get('값있는셀수')}]" if (cen.get("셀수") or "") != "" else ""
    return f"{cen['공시분기']} PDF <{cen.get('기준연도') or '-'}년> {cen['상태']}{nv}: {(cen.get('근거') or '')[:150]}"


def adoption_rows(res: dict) -> list[dict]:
    blocks, reg = res["blocks"], res["reg"]
    out = []
    for (code, q), d in sorted(res["decisions"].items()):
        nm = (reg.get(code) or {}).get("name") or ""
        ak = d["adopted"]
        cmp_ = d["compare"]
        other = None
        if ak and cmp_:
            other = d["primary"] if ak == d["next"] else d["next"]
        r = {"원보험사코드": code, "원수사명": nm, "공시분기": q, "채택원천": block_desc(ak, blocks) if ak else "",
             "대조원천": block_desc(other, blocks) if other else "", "플래그": "; ".join(d.get("flag_text", d["flags"])), "정정판정": d.get("verdict", "")}
        notes = []
        if cmp_:
            r.update({"비교칸수": cmp_["n"], "차이칸수": len(cmp_["diffs"]), "금액차이칸": len(cmp_["amt_diffs"]), "비율차이칸": len(cmp_["ratio_diffs"]),
                      "최대차": "" if cmp_["max_amt"] is None else round(cmp_["max_amt"], 6),
                      "최대차_비율pp": "" if cmp_["max_ratio"] is None else round(cmp_["max_ratio"], 6), "정밀도차이칸": cmp_["n_prec"],
                      "영채움칸": cmp_["n_zero"], "라벨변경행수": len(cmp_["relabel"])})
            notes.append(f"{d['primary'][1]} PDF <{q[:4]}년> vs {d['next'][1]} PDF <{q[:4]}년> 대조 {cmp_['n']}칸: 동일 {cmp_['n_eq']}"
                         f"(+인쇄 정밀도만 다름 {cmp_['n_prec']}), 값 차이 {len(cmp_['diffs'])}(금액 {len(cmp_['amt_diffs'])}·비율 {len(cmp_['ratio_diffs'])}), 영(0) 채움 유무 {cmp_['n_zero']}칸 무시")
            if cmp_["relabel"]:
                notes.append("라벨만 바뀐 행(값 동일, 정정 아님): " + "; ".join(f"{'/'.join(x for x in a if x)} -> {'/'.join(x for x in b if x)}" for a, b in cmp_["relabel"][:4]))
            if "RESTATED" in d["flags"]:
                notes.append(f"{d['verdict']}: {d['verdict_why']}")
                notes.append(f"-> {d['next'][1]} PDF 전기 블록 채택")
            elif cmp_["ratio_diffs"]:
                mxr = f"최대 {cmp_['max_ratio']:g}%p" if cmp_["max_ratio"] is not None else "전부 한쪽 null"
                notes.append(f"금액 동일·인쇄 비율 칸만 {len(cmp_['ratio_diffs'])}칸 상이({mxr}) -> 마스터 숫자 영향 없음(손해율 재계산), 당기 블록 채택")
            else:
                notes.append("값 동일 -> 당기 블록(Y.4Q PDF) 채택")
        else:
            if ak and "FROM_NEXT_YEAR_PRIOR_BLOCK" in d["flags"]:
                notes.append("당기 원천 없음 -> 후속 공시 전기 블록으로 채움. " + census_text(d.get("primary_cen")))
            elif ak and any(f.startswith("정정미확인") for f in d["flags"]):
                notes.append("정정 확인 불가: " + census_text(d.get("next_cen")))
            elif ak:
                notes.append("최신 결산(후속 공시 없음)")
            else:
                notes.append("사용 가능한 블록 없음(블록은 있으나 금액 칸이 전부 대시 -> 값 없음): "
                             + "; ".join(f"{k[1]} PDF <{k[2]}년> ({census_text(cen_of(res['census_idx'], k[0], k[1], k[2]))})" for k in d.get("cands", [])))
        if ak and "SAME_AS_PRIOR_YEAR" in " ".join(d["flags"]):
            notes.append(f"같은 PDF 의 <{ak[2] - 1}년> 블록과 {d['same_prior'][0]}/{d['same_prior'][1]}칸 동일 -- 인쇄값 그대로(전년 수치 재인쇄 또는 가정 미변경)")
        st = (d.get("primary_cen") or {}).get("상태") if d.get("primary") else None
        if ak and ak[1] != q:
            pass
        r["비고"] = " | ".join(notes)
        out.append(r)
    return out


MC_COLS = ["원보험사코드", "원수사명", "생손보여부", "kics39사", "공시분기", "상태", "채택원천", "마스터행수", "값있는행수", "플래그", "결측사유", "비고"]


def reason_class(cen) -> str:
    """census 한 칸의 상태·근거 -> 짧은 사유 범주(필터용). 근거 원문은 비고에 그대로 둔다."""
    if not cen:
        return "census 칸 없음"
    st, why = cen["상태"], (cen.get("근거") or "")
    if st == "NO_PDF":
        return "원본 PDF 없음(다운로더 소관)"
    if "미산출을 명시" in why:
        return "회사가 표 미산출 명시(연금보험 단종 등)"
    if "산출 불가를 명시" in why:
        return "회사가 전기 비교공시 산출 불가 명시"
    if "해당사항 없음으로 명시" in why:
        return "회사가 최적가정 절을 해당사항 없음으로 명시(장기보험 미영위 등)"
    if "캡션 없음" in why or "인쇄돼 있지 않다" in why or "prints only" in why:
        return "공시본이 당기 블록만 인쇄(해당 연도 블록 미인쇄)"
    if st == "ABSENT_IN_SOURCE" and "vision 판독" in why and "없다" in why:
        return "스캔 렌더 판독: 해당 결산 공시에 표 없음"
    if "전 칸 '-'" in why or (st == "FILLED" and str(cen.get("값있는셀수")) == "0" and str(cen.get("셀수")) not in ("", "0")):
        return "표는 인쇄됐으나 전 칸 대시(값 없음)"
    if "키워드 0건" in why and "신설" in why:
        return "결산본에 표 없음(2024.4Q 결산본부터 신설)"
    if "키워드 0건" in why:
        return "결산본에 표 키워드 0건(표 없음)"
    if st in ("SCAN_PENDING", "UNREADABLE", "PARSE_FAILED"):
        return f"추출 미완({st})"
    return f"{st}: {why[:50]}"


def census_grid(res: dict) -> list[dict]:
    reg, blocks, decisions, cidx = res["reg"], res["blocks"], res["decisions"], res["census_idx"]
    master = res["master"]
    n_rows = Counter((r["원보험사코드"], r["공시분기"]) for r in master)
    n_val = Counter((r["원보험사코드"], r["공시분기"]) for r in master if r["예상보험금"] is not None or r["위험보험료"] is not None)
    codes = sorted(set(reg) | {k[0] for k in blocks} | {k[0] for k in cidx})
    years = sorted({k[2] for k in blocks} | {int(k[1][:4]) for k in cidx if k[1].endswith(".4Q") and k[2]} | {int(k[1][:4]) for k in cidx if k[1].endswith(".4Q")})
    qs = [f"{y}.4Q" for y in range(min(years), max(years) + 1)] if years else []
    out = []
    for code in codes:
        info = reg.get(code) or {}
        nm = info.get("name") or next((b.get("name") for k, b in blocks.items() if k[0] == code), "") or next(
            (c.get("원수사명") for c in res["census_rows"] if c["원보험사코드"] == code), "")
        kind = info.get("kind") or next((c.get("생손보여부") for c in res["census_rows"] if c["원보험사코드"] == code), "")
        for q in qs:
            y = int(q[:4])
            d = decisions.get((code, q))
            base = {"원보험사코드": code, "원수사명": nm, "생손보여부": kind, "kics39사": "O" if info.get("in_kics") else "X", "공시분기": q}
            if d and d["adopted"]:
                base.update({"상태": "채택", "채택원천": block_desc(d["adopted"], blocks), "마스터행수": n_rows[(code, q)], "값있는행수": n_val[(code, q)],
                             "플래그": "; ".join(d.get("flag_text", d["flags"])), "결측사유": "", "비고": ""})
            else:
                parts = []
                cens = []
                for pq, yr in ((q, y), (f"{y + 1}.4Q", y)):
                    cen = cen_of(cidx, code, pq, yr)
                    cens.append(cen)
                    parts.append(census_text(cen) if cen else f"{pq} PDF <{yr}년>: census 칸 없음")
                # 사유 범주: 후속 공시(전기 블록) 쪽이 마지막 시도라 그쪽을 우선, 없으면 당기 쪽. 당기 PDF 가 표 신설 전이면 앞에 붙인다
                cur, nxt = cens
                if cur and "신설" in (cur.get("근거") or "") and nxt:
                    main_cat = "2023.4Q 결산본엔 표 없음 + " + reason_class(nxt)
                else:
                    main_cat = reason_class(cur) if cur else (reason_class(nxt) if nxt else "census 칸 없음")
                    if cur and nxt and reason_class(nxt) != main_cat:
                        main_cat += f" (후속 공시: {reason_class(nxt)})"
                if d and "NO_USABLE_BLOCK" in d["flags"]:
                    main_cat = "표는 인쇄됐으나 전 칸 대시(값 없음)"
                base.update({"상태": "결측", "채택원천": "", "마스터행수": 0, "값있는행수": 0, "플래그": "", "결측사유": main_cat,
                             "비고": " | ".join(parts) + ((" | " + "NO_USABLE_BLOCK(전 칸 대시)") if d and "NO_USABLE_BLOCK" in d["flags"] else "")})
            out.append(base)
    return out


# ------------------------------------------------------------------------------------------------
# 자체 검산
# ------------------------------------------------------------------------------------------------
def parse_source_field(s: str) -> list[tuple[str, list[int]]]:
    out = []
    for part in (s or "").split("; "):
        f, _, p = part.rpartition(":")
        out.append((f, [int(x) for x in p.split(",") if x.strip().isdigit()]))
    return out


def same_num(a, b, tol=1e-6):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= tol


def verify(src_rows: list[dict], mj: list[dict], mc: list[list[str]] | None = None, header: list[str] | None = None):
    """원본 JSON <-> 마스터 JSON(<-> 마스터 CSV) 1:1 대조. -> (오류 목록, 경고 목록, 통계)."""
    errs: list[str] = []
    warns: list[str] = []
    stats: dict = {}
    if mc is not None:
        if header != ALL_COLS:
            errs.append(f"CSV 헤더 불일치: {header}")
        if len(mc) != len(mj):
            errs.append(f"행 수 불일치 JSON {len(mj)} / CSV {len(mc)}")
    bad_keys = [i for i, r in enumerate(mj) if list(r.keys()) != ALL_COLS]
    if bad_keys:
        errs.append(f"JSON 키 순서 불일치 {len(bad_keys)}행(예 행{bad_keys[0]})")
    # --- 원본 색인(추출기 canon 라벨 기준 = 이 변환기의 사전과 독립)
    idx: dict[tuple, dict] = {}
    ridx: dict[tuple, dict] = {}
    block_rows: Counter = Counter()
    dup_src: Counter = Counter()
    for r in src_rows:
        bk = (r["원보험사코드"], r["공시분기"], r["기준연도"])
        key = bk + (seg_of(r), r["구분"], r["포트폴리오"], r["경과기간"])
        d = idx.setdefault(key, {})
        rkey = bk + (seg_of(r), r.get("구분_원문") or r["구분"], r.get("포트폴리오_원문") or "", r["경과기간"])
        rd = ridx.setdefault(rkey, {})
        if r["지표"] in d:
            dup_src[bk] += 1
            continue
        d[r["지표"]] = r
        rd[r["지표"]] = r
        block_rows[bk] += 1
    consumed: Counter = Counter()
    seen_keys: dict[tuple, int] = {}
    used_blocks: dict[tuple, set] = defaultdict(set)
    n_loss_bad = n_val_bad = n_ratio_flag_bad = 0
    for i, m in enumerate(mj):
        code = m["원보험사코드"]
        files = parse_source_field(m["출처"])
        pqs = {pdf_q_of_file(f) for f, _ in files}
        if len(pqs) != 1 or None in pqs:
            errs.append(f"행{i} {code} {m['공시분기']}: 출처 파일이 하나의 PDF 분기로 안 읽힘 {m['출처'][:80]}")
            continue
        pq = next(iter(pqs))
        yr = int(m["공시분기"][:4])
        if pq not in (m["공시분기"], f"{yr + 1}.4Q"):
            errs.append(f"행{i} {code} {m['공시분기']}: 채택 원천 {pq} 는 §5-1 허용(Y.4Q·(Y+1).4Q) 밖")
        used_blocks[(code, m["공시분기"])].add((code, pq, yr))
        mk = (code, m["공시분기"], m["세그먼트"], m["경과차년"], m["구분"], m["상품구분"], m["포트폴리오"])
        if mk in seen_keys:
            errs.append(f"마스터 키 중복 {mk} (행{seen_keys[mk]}, 행{i}) -- 원문포트폴리오 {m['원문포트폴리오']!r}")
        seen_keys[mk] = i
        if m["구분"] and m["포트폴리오"]:
            key = (code, pq, yr, m["세그먼트"], m["구분"], std_concat(m["상품구분"], m["포트폴리오"]), m["경과차년"])
            s = idx.get(key)
        else:
            s = ridx.get((code, pq, yr, m["세그먼트"], m["원문구분"], m["원문포트폴리오"], m["경과차년"]))
        if s is None:
            errs.append(f"행{i} {code} {m['공시분기']} {m['구분']}|{m['상품구분']}{m['포트폴리오']}|{m['경과차년']}: 원본에 대응 칸 없음")
            continue
        consumed[(code, pq, yr)] += len(s)
        for col, met in (("위험보험료", "위험보험료"), ("예상보험금", "예상보험금")):
            sr = s.get(met)
            exp = None
            if sr is not None and sr["값"] is not None:
                u = sr["단위"]
                exp = sr["값"] * UNIT_TO_EOK.get(u, 1.0) if u != "억원" else sr["값"]
            if not same_num(m[col], exp):
                n_val_bad += 1
                errs.append(f"행{i} {mk} {col}: 마스터 {m[col]!r} != 원본 {exp!r}")
        a, b = m["예상보험금"], m["위험보험료"]
        exp_loss = round(a / b * 100, 2) if (a is not None and b is not None and b != 0) else None
        if not same_num(m["손해율"], exp_loss, 1e-9):
            n_loss_bad += 1
            errs.append(f"행{i} {mk} 손해율 {m['손해율']!r} != 재계산 {exp_loss!r}")
        # 플래그 일관성: 비율검산불일치 ↔ 원문 인쇄 비율이 허용 구간 밖
        sq, sa, sb = s.get("비율"), s.get("예상보험금"), s.get("위험보험료")
        flagged = "비율검산불일치" in m["플래그"]
        if sq is not None and sq["값"] is not None and a is not None and b is not None and sa and sb:
            da = amount_dec(sa.get("원값", sa["값"]), sa.get("원단위") or sa["단위"])
            db = amount_dec(sb.get("원값", sb["값"]), sb.get("원단위") or sb["단위"])
            dq = max(decimals_of(sq.get("원값", sq["값"])) - 2, 0) if sq.get("원단위") == "배(소수)" else decimals_of(sq["값"])
            ok = ratio_consistent(a, b, sq["값"], da, db, dq)
            if (ok is False) != flagged:
                n_ratio_flag_bad += 1
                errs.append(f"행{i} {mk}: 비율검산불일치 플래그 {'있음' if flagged else '없음'} / 재검산 {'구간 밖' if ok is False else '구간 안 또는 검산 불가'} -- 서로 어긋남")
        elif flagged:
            errs.append(f"행{i} {mk}: 비율검산불일치 플래그인데 원문 비율/금액이 없음")
        if m["구분"] == "" or m["포트폴리오"] == "":
            if "분류미정" not in m["플래그"]:
                errs.append(f"행{i} {mk}: 표준 공란인데 분류미정 플래그 없음")
        if mc is not None:
            cs = mc[i] if i < len(mc) else None
            if cs is None:
                continue
            for j, col in enumerate(ALL_COLS):
                cv = cs[j]
                if col in NUM_COLS:
                    ok = same_num(m[col], None if cv == "" else float(cv), 1e-9)
                else:
                    ok = (m[col] if m[col] is not None else "") == cv
                if not ok:
                    errs.append(f"행{i} {mk} CSV {col}: {cv!r} != JSON {m[col]!r}")
    # --- 한 (회사, 공시분기) 는 정확히 한 블록에서만 채워져야 한다 + 그 블록의 원본 행을 빠짐없이 소비했는가
    for k, blks in used_blocks.items():
        if len(blks) != 1:
            errs.append(f"{k}: 채택 원천 블록이 {len(blks)}개 {sorted(blks)}")
            continue
        bk = next(iter(blks))
        kept = block_rows[bk]
        if consumed[bk] != kept:
            errs.append(f"{bk}: 원본 행 {kept} 중 마스터가 소비한 것 {consumed[bk]}")
        if dup_src.get(bk):
            warns.append(f"{bk}: 원본에 같은 칸 중복 {dup_src[bk]}건(첫 값 채택, 플래그 `원본중복칸`)")
    # --- 합계 = Σ포트폴리오 (마스터 값 기준, 원문오기·중복칸·분류미정·검산실패 census 행은 설명 가능한 예외)
    grp: dict[tuple, dict] = defaultdict(lambda: {"tot": None, "parts": [], "flags": ""})
    for m in mj:
        for col in ("예상보험금", "위험보험료"):
            v = m[col]
            if v is None:
                continue
            g = grp[(m["원보험사코드"], m["공시분기"], m["세그먼트"], m["경과차년"], col)]
            g["flags"] += m["플래그"]
            if m["구분"] == "합계":
                g["tot"] = v
            else:
                g["parts"].append(v)
    n_chk = n_fail = n_expl = 0
    unexpl = []
    for k, g in grp.items():
        if g["tot"] is None or not g["parts"]:
            continue
        dec = [decimals_of(g["tot"])] + [decimals_of(p) for p in g["parts"]]
        tol = total_tol(dec)
        n_chk += 1
        if abs(sum(g["parts"]) - g["tot"]) > tol:
            n_fail += 1
            if re.search(r"원문오기|원본중복칸|분류미정|FILLED_CHECK_FLAGS|PARSE_FAILED|추출확인필요", g["flags"]):
                n_expl += 1
            else:
                unexpl.append((k, round(sum(g["parts"]), 4), g["tot"]))
    for k, s_, t_ in unexpl[:20]:
        errs.append(f"합계≠Σ포트폴리오(설명 불가) {k}: Σ={s_} 합계={t_}")
    stats.update({"rows": len(mj), "sum_checked": n_chk, "sum_fail": n_fail, "sum_fail_explained": n_expl,
                  "loss_bad": n_loss_bad, "val_bad": n_val_bad, "ratio_flag_bad": n_ratio_flag_bad,
                  "src_dups": dict(dup_src)})
    return errs, warns, stats


# ------------------------------------------------------------------------------------------------
# 쓰기 / 요약 / main
# ------------------------------------------------------------------------------------------------
def public_row(r: dict) -> dict:
    return {k: r[k] for k in ALL_COLS}


def write_outputs(res: dict):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pub = [public_row(r) for r in res["master"]]
    atomic_write(OUT_JSON, json.dumps(pub, ensure_ascii=False, indent=2))
    atomic_write(OUT_CSV, csv_text(ALL_COLS, pub, format_cell), encoding="utf-8-sig")
    atomic_write(OUT_TAXONOMY, csv_text(TAX_COLS, taxonomy_rows(res)), encoding="utf-8-sig")
    atomic_write(OUT_ADOPTION, csv_text(ADOPT_COLS, adoption_rows(res)), encoding="utf-8-sig")
    atomic_write(OUT_MCENSUS, csv_text(MC_COLS, census_grid(res)), encoding="utf-8-sig")


def summarize(res: dict):
    master = res["master"]
    print(f"마스터 {len(master)}행 / 회사 {len({r['원보험사코드'] for r in master})}")
    for q in sorted({r["공시분기"] for r in master}):
        cs = {r["원보험사코드"] for r in master if r["공시분기"] == q}
        print(f"  {q}: 회사 {len(cs)}사, {sum(1 for r in master if r['공시분기'] == q)}행")
    fl = Counter()
    for (code, q), d in res["decisions"].items():
        for f in d.get("flag_text", d["flags"]):
            fl[f.split("(")[0]] += 1
    print("공시분기 단위 플래그(회사x분기 수):", dict(fl.most_common()))
    rt = Counter()
    for r in master:
        for tok in filter(None, (t.strip() for t in r["플래그"].split(";"))):
            rt[tok.split("(")[0].split(":")[0]] += 1
    print("행 단위 플래그 토큰:", dict(rt.most_common()))
    print("추출방식:", dict(Counter(r["추출방식"] for r in master)), "/ 단위:", dict(Counter(r["단위"] for r in master)))
    un = sorted({(r["원문구분"], r["원문포트폴리오"]) for r in master if "분류미정" in r["플래그"]})
    print("분류미정 라벨:", un or "없음")
    if res["unused_blocks"]:
        print("§5-1 밖 블록(마스터에 안 쓰임):", res["unused_blocks"])
    grid = census_grid(res)
    miss = [(g["원보험사코드"], g["공시분기"]) for g in grid if g["상태"] == "결측"]
    print(f"그리드 결측 {len(miss)}칸 / 채택 {sum(1 for g in grid if g['상태'] == '채택')}칸 (회사 {len({g['원보험사코드'] for g in grid})}사 x 공시분기 {len({g['공시분기'] for g in grid})})")
    for q in sorted({g["공시분기"] for g in grid}):
        print(f"  {q}: 채택 {sum(1 for g in grid if g['공시분기'] == q and g['상태'] == '채택')}사 / 결측 {sum(1 for g in grid if g['공시분기'] == q and g['상태'] == '결측')}사 "
              f"(결측 사유: {dict(Counter(g['결측사유'] for g in grid if g['공시분기'] == q and g['상태'] == '결측').most_common())})")
    bad = []
    for (code, q), d in sorted(res["decisions"].items()):
        if d["adopted"]:
            ck = block_checks(res["blocks"][d["adopted"]])
            if not ck["consistent"]:
                bad.append((code, q, d["adopted"][1], ck["ratio_fail"], ck["total_fail"], d.get("flag_text", d["flags"])[:2]))
    print("채택 블록 중 내부 검산(비율·합계) 실패:", bad or "없음")
    nm = Counter()
    for r in master:
        for tok in r["플래그"].split("; "):
            if tok.startswith("지표없음"):
                nm[(r["원보험사코드"], r["공시분기"], tok)] += 1
    print("지표 행이 원본에 없는 칸(지표없음):", dict(nm) or "없음")


def run_verify_files() -> tuple[list[str], list[str], dict]:
    src_rows = read_json(SRC_B)
    mj = read_json(OUT_JSON)
    with open(OUT_CSV, encoding="utf-8-sig", newline="") as fh:
        rd = csv.reader(fh)
        header = next(rd)
        mc = list(rd)
    return verify(src_rows, mj, mc, header)


def main():
    ap = argparse.ArgumentParser(description="손해율 마스터 변환기 (risk_premium_vs_expected_claims.json -> master_loss_ratio.json/csv)")
    ap.add_argument("--verify-only", action="store_true", help="쓰지 않고 기존 산출만 원본과 1:1 대조")
    ap.add_argument("--no-write", action="store_true", help="산출 파일을 쓰지 않고 요약·메모리 검산만")
    args = ap.parse_args()
    t0 = time.time()
    if args.verify_only:
        errs, warns, stats = run_verify_files()
    else:
        res = build()
        summarize(res)
        if args.no_write:
            errs, warns, stats = verify(res["src_rows"], [public_row(r) for r in res["master"]])
        else:
            write_outputs(res)
            print("WROTE", ", ".join(p.relative_to(REPO).as_posix() for p in (OUT_JSON, OUT_CSV, OUT_TAXONOMY, OUT_ADOPTION, OUT_MCENSUS)))
            errs, warns, stats = run_verify_files()
    print("검산 통계:", {k: v for k, v in stats.items() if k != "src_dups"}, f"({time.time() - t0:.0f}s)")
    for w in warns[:30]:
        print("  [경고]", w)
    if errs:
        print(f"[검산 실패] {len(errs)}건")
        for e in errs[:40]:
            print("  ", e)
        sys.exit(1)
    print("[검산 통과] 원본 JSON <-> 마스터 JSON <-> 마스터 CSV 값·키 1:1, 키 중복 0, 채택 블록 원본 행 전부 소비, 손해율 재계산 일치")


if __name__ == "__main__":
    main()
