#!/usr/bin/env python3
"""정기경영공시 PDF 에서 손해율 3개 표를 전사 x 전기간 추출 -> data/loss_ratio/ (신규 도메인, 2026-10-07).

  표 A  「① 보험금 예실차비율」      (결산본 최적가정 절)  예상손해율(A) / 실제손해율(B) / 예실차(C=A-B), 당기·전기 2개 연도
  표 B  「② 위험보험료 대비 예상보험금」 (결산본)  구분 x 포트폴리오 x {예상보험금(A), 위험보험료(B), 비율(A/B)} x 경과기간 1~30년+현재가치
  표 C  「가격설정(pricing)의 적정성」 합산비율 표 (손보, 2Q·4Q 공시)  종목 x {손해율, 사업비율, 합산비율} x 연도·분기

산출 (모두 data/loss_ratio/, 원자적 교체):
  claims_ae_ratio.json · risk_premium_vs_expected_claims.json · combined_ratio_nonlife.json
  census.csv         기대그리드 전 칸의 상태 (FILLED / FILLED(vision) / ABSENT_IN_SOURCE / UNREADABLE / SCAN_PENDING ...)
  pdf_survey.csv     PDF 549개 전수 조사(쪽 수 · 텍스트쪽 비율 · 키워드 쪽 번호) = ABSENT 근거 원장
  diffs.csv          같은 기준연도가 두 공시(또는 본문 vs 뒤쪽 사본)에 나올 때의 값 차이

원천 우선순위 (칸 단위):
  1. fitz 텍스트층 (추출방식 "text") - 본문 절이 정본. 본문이 스캔이어도 PDF 안 다른 쪽(뒤쪽 감사보고서·부록)에
     텍스트층 사본이 있으면 그 사본에서 읽는다(출처 쪽 = 사본 쪽). 일반 규칙이라 회사 하드코딩 없음.
  2. docling MD (추출방식 "md") - raw PDF 에 텍스트가 전혀 없고 md_inbox 에만 있을 때(예: KB손해 2026.2Q Print-To-PDF 사본).
  3. data/loss_ratio/vision_cells*.json (추출방식 "vision") - 스캔본을 사람이/비전 에이전트가 렌더 판독한 행. glob 으로 전부 병합.
  vision 이 덮지 않은 스캔 칸은 SCAN_PENDING. 우선순위: 텍스트 FILLED > vision FILLED > vision ABSENT/UNREADABLE > SCAN_PENDING.

입력(읽기 전용): data/loss_ratio/source_errata.csv = 원문 PDF 가 인쇄 자체를 틀린 칸의 등재부(렌더 PNG 로 직접 확인한 칸만).
  값은 인쇄 그대로 두고, 그 칸이 걸린 검산(비율 ≈ A÷B · 합계 = Σ포트폴리오)만 제외하며 행에 '원문오기' 를 단다.
같은 공시에 사업별 표가 따로 있으면(코리안리: [전통형재보험] · [공동재보험]) 행에 '사업구분' 을 달고 census 기준연도 칸을 `2024|공동재보험` 으로 쓴다.
인자 없이 재실행하면 새 vision 파일까지 다시 병합한다(PDF 쪽 색인은 디스크 캐시라 재실행은 1분 안팎).
읽기 전용: 루트 마스터 JSON(kics_disclosure.json 은 회사명 조회만) · 게이트 · 테스트는 건드리지 않는다.

사용:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_loss_ratio.py
  ... --only KR0001,KR0008 --quarters 2025.4Q   (부분 실행 - 산출 파일은 쓰지 않고 요약만 인쇄)
"""
from __future__ import annotations

import argparse
import bisect
import csv
import io
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DISC = ROOT / "data" / "disclosure"
MD_DIR = ROOT / "md_inbox"
OUT_DIR = ROOT / "data" / "loss_ratio"
PERSIST_DIR = ROOT / "data" / "persistency"
KICS_JSON = ROOT / "kics_disclosure.json"
CACHE_PATH = ROOT / "data" / "_derived" / "_probe_loss_ratio_pageindex.json"   # gitignore: data/_derived/_probe_*

try:  # raw/ 우선 pdf/ 폴백 규칙은 이 헬퍼가 정본
    from _disclosure_pdf_paths import SUBDIRS as PDF_SUBDIRS
except Exception:  # noqa: BLE001
    PDF_SUBDIRS = ("raw", "pdf")

OUT_A = OUT_DIR / "claims_ae_ratio.json"
OUT_B = OUT_DIR / "risk_premium_vs_expected_claims.json"
OUT_C = OUT_DIR / "combined_ratio_nonlife.json"
ERRATA_PATH = OUT_DIR / "source_errata.csv"          # 원문 인쇄 오기 등재부(렌더 PNG 로 직접 확인한 칸만). 읽기 전용 입력
OUT_CENSUS = OUT_DIR / "census.csv"
OUT_SURVEY = OUT_DIR / "pdf_survey.csv"
OUT_DIFFS = OUT_DIR / "diffs.csv"

QUARTERS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
ANNUAL_QUARTERS = ["2023.4Q", "2024.4Q", "2025.4Q"]          # 표 A·B 기대그리드(결산본)
# 표 B 값의 단위·종류 규약은 원문 그대로. 비율은 % 로 통일(소수 인쇄는 변환 + 플래그).

NONLIFE_CODES = {"KR0001", "KR0002", "KR0003", "KR0004", "KR0005", "KR0008", "KR0009", "KR0010", "KR0011",
                 "KR0029", "KR0032", "KR0049", "KR0050", "KR0051", "KR0150", "KR1000", "KR1059", "KR1098"}
EXTRA_META = {"KR1059": ("캐롯손해보험", "손해보험")}          # kics_disclosure.json(39사) 밖 회사. 마스터에 없다.
NAME_TO_CODE_FALLBACK = {"한화생명": "KR0068"}                 # 파일명이 KR코드로 시작하지 않는 경우('(한화생명) 2026년 1분기 ...')


# ---------------------------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------------------------
def q_to_period(q: str) -> str:
    return f"FY{q[:4]}_Q{q[5]}"


def period_to_q(p: str) -> str:
    return f"{p[2:6]}.{p[-1]}Q"


def nz(s: str) -> str:
    """공백(전각·NBSP 포함) 전부 제거."""
    return re.sub(r"[\s\u3000\u00a0]+", "", s or "")


def load_company_meta() -> dict[str, tuple[str, str]]:
    meta: dict[str, tuple[str, str]] = {}
    if KICS_JSON.exists():
        for r in json.loads(KICS_JSON.read_text(encoding="utf-8")):
            c = r.get("원보험사코드")
            if c and c not in meta:
                meta[c] = (r.get("원수사명", ""), r.get("생손보여부", ""))
    for c, v in EXTRA_META.items():
        meta.setdefault(c, v)
    return meta


def load_errata(path: Path | None = None) -> dict:
    """source_errata.csv -> {(회사코드, 공시분기): {(기준연도|None, 사업구분, 부문, 구분, 포트폴리오, 경과기간, 지표): 근거}}  (사업구분·부문은 빈칸이면 '').
    원문 PDF 가 인쇄 자체를 잘못한 칸(렌더 PNG 로 직접 확인)만 등재한다. 값은 인쇄 그대로 두고, 이 칸이 걸린 검산(비율 · 합계=Σ)만 제외하며 행에 '원문오기' 를 단다."""
    path = path or ERRATA_PATH
    out: dict = {}
    if not path.exists():
        return out
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if not (r.get("원보험사코드") or "").strip():
                continue
            yr = int(r["기준연도"]) if (r.get("기준연도") or "").strip() else None
            note = f"원문오기 인쇄 {r.get('인쇄값', '')} -> 추정 {r.get('추정값', '')}: {r.get('근거', '')}"
            out.setdefault((r["원보험사코드"].strip(), r["공시분기"].strip()), {})[
                (yr, (r.get("사업구분") or "").strip(), (r.get("부문") or "").strip(), r["구분"].strip(), r["포트폴리오"].strip(),
                 r["경과기간"].strip(), r["지표"].strip())] = note
    return out


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding=encoding, newline="") as f:
        f.write(text)
    last: Exception | None = None
    for _ in range(60):                    # Windows: 다른 프로세스(백신·인덱서·열람 중인 에이전트)가 대상 파일을 잠깐 열고 있으면 WinError 5 -> 재시도
        try:
            os.replace(tmp, path)
            return
        except PermissionError as e:
            last = e
            time.sleep(1.0)
    raise last  # type: ignore[misc]


def atomic_write_json(path: Path, obj) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


# ---------------------------------------------------------------------------------------------
# PDF 탐색: (공시분기, 회사코드) -> 파일. raw/ 우선, 없으면 pdf/. 같은 칸에 여러 파일이면 정정본(_amended*) 우선.
# ---------------------------------------------------------------------------------------------
def _code_of(stem: str, meta: dict) -> str | None:
    m = re.match(r"^(KR\d{4})_", stem)
    if m:
        return m.group(1)
    for name, code in NAME_TO_CODE_FALLBACK.items():
        if name in stem:
            return code
    return None


def _amend_rank(p: Path) -> tuple:
    s = p.stem
    return (len(re.findall("amended", s)), sum(int(d) for d in re.findall(r"amended(\d+)", s)), p.stat().st_mtime)


def discover_pdfs(meta: dict) -> dict[tuple[str, str], Path]:
    found: dict[tuple[str, str], Path] = {}
    for pdir in sorted(DISC.glob("FY20*_Q[1-4]")):
        q = period_to_q(pdir.name)
        taken: dict[str, tuple[str, list[Path]]] = {}
        for sub in PDF_SUBDIRS:           # 한 회사 파일은 먼저 잡은 하위폴더(raw 우선)에서만 취한다
            d = pdir / sub
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.pdf")):
                code = _code_of(f.stem, meta)
                if not code or (code in taken and taken[code][0] != sub):
                    continue
                taken.setdefault(code, (sub, []))[1].append(f)
        for code, (_sub, fs) in taken.items():
            found[(q, code)] = max(fs, key=_amend_rank)
    return found


# ---------------------------------------------------------------------------------------------
# PDF 쪽 색인 (디스크 캐시) - 표별 키워드가 어느 쪽에 있는지 + 쪽별 텍스트 글자수.
# 키워드 부재 = 원천 부재 단정은 금지(스캔 쪽은 글자수 0). 그래서 글자수를 같이 저장해 텍스트쪽 비율로 판정한다.
# ---------------------------------------------------------------------------------------------
IDX_PATTERNS = {
    "A_cols": re.compile(r"예상손해율.{0,200}실제손해율|실제손해율.{0,200}예상손해율"),
    "A_head": re.compile(r"보험금예실차비율"),
    "B_head": re.compile(r"위험보험료대비예상보험금"),
    "B_lab": re.compile(r"예상보험금.{0,3000}위험보험료|위험보험료.{0,3000}예상보험금"),
    "B_next": re.compile(r"예정유지비"),
    "C_kw": re.compile(r"합산비율"),
    "C_gs": re.compile(r"가격설정"),
    "not_calc": re.compile(r"산출하지않"),
    "opt": re.compile(r"최적가정"),
}
TEXT_MIN_CHARS = 30      # 이보다 적으면 그 쪽은 텍스트층 없음(스캔·이미지)


def _index_one(path: Path) -> dict:
    import fitz  # noqa: PLC0415  (PyMuPDF; 인자 --help 등에서는 불필요)
    rec: dict = {}
    try:
        doc = fitz.open(str(path))
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}
    n = doc.page_count
    chars: list[int] = []
    hits: dict[str, list[int]] = {k: [] for k in IDX_PATTERNS}
    for i in range(n):
        try:
            t = doc[i].get_text()
        except Exception:  # noqa: BLE001
            t = ""
        chars.append(len(t))
        if not t.strip():
            continue
        tt = nz(t)
        for k, pat in IDX_PATTERNS.items():
            if pat.search(tt):
                hits[k].append(i + 1)
    doc.close()
    rec.update(pages=n, chars=chars, hits=hits)
    return rec


def load_index(pdfs: dict[tuple[str, str], Path], log=print) -> dict[str, dict]:
    """경로(ROOT 기준 상대, '/' 구분) -> 색인. size+mtime_ns 가 같으면 캐시 재사용."""
    cache: dict = {}
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            cache = {}
    out: dict[str, dict] = {}
    dirty = False
    todo = sorted(set(pdfs.values()))
    t0 = time.time()
    for i, p in enumerate(todo, 1):
        key = p.relative_to(ROOT).as_posix()
        st = p.stat()
        c = cache.get(key)
        if c and c.get("size") == st.st_size and c.get("mtime_ns") == st.st_mtime_ns and "error" not in c:
            out[key] = c
            continue
        rec = _index_one(p)
        rec["size"], rec["mtime_ns"] = st.st_size, st.st_mtime_ns
        cache[key] = out[key] = rec
        dirty = True
        if i % 25 == 0 or time.time() - t0 > 60:
            log(f"  [index] {i}/{len(todo)} {key}")
            t0 = time.time()
            atomic_write_text(CACHE_PATH, json.dumps(cache, ensure_ascii=False))   # 중간 저장(중단 대비)
            dirty = False
    if dirty:
        atomic_write_text(CACHE_PATH, json.dumps(cache, ensure_ascii=False))
    return out


# ---------------------------------------------------------------------------------------------
# 단어 / 줄 / 숫자 유틸 (좌표 기반 - 표 선 검출에 의존하지 않는다)
# ---------------------------------------------------------------------------------------------
class Wd:
    __slots__ = ("x0", "y0", "x1", "y1", "t")

    def __init__(self, x0, y0, x1, y1, t):
        self.x0, self.y0, self.x1, self.y1, self.t = x0, y0, x1, y1, t

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def yc(self) -> float:
        return (self.y0 + self.y1) / 2

    def __repr__(self) -> str:  # 디버그용
        return f"Wd({self.t!r}@{self.x0:.0f},{self.yc:.0f})"


def get_words(page) -> list[Wd]:
    """공백 제거 + 같은 자리 중복 제거(한화생명 등 텍스트를 이중으로 그린 PDF). 읽는 순서는 y,x."""
    out: list[Wd] = []
    seen: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for x0, y0, x1, y1, t, *_ in page.get_text("words"):
        t = t.replace("\u3000", " ").replace("\u00a0", " ").strip()
        if not t:
            continue
        if any(abs(x0 - a) < 1.6 and abs(y0 - b) < 1.6 for a, b in seen[t]):
            continue
        seen[t].append((x0, y0))
        out.append(Wd(x0, y0, x1, y1, t))
    out.sort(key=lambda w: (round(w.yc, 0), w.x0))
    return out


def group_lines(ws: list[Wd], tol: float = 3.0) -> list[list[Wd]]:
    """같은 y 줄로 묶는다(줄 평균 y 와 tol 이내). 각 줄은 x 오름차순."""
    lines: list[list[Wd]] = []
    for w in sorted(ws, key=lambda w: w.yc):
        if lines and abs(sum(x.yc for x in lines[-1]) / len(lines[-1]) - w.yc) <= tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    for ln in lines:
        ln.sort(key=lambda w: w.x0)
    return lines


def line_text(ln: list[Wd], sep: str = " ") -> str:
    return sep.join(w.t for w in ln)


_DASHES = set("-–—−‐‑－ー")
_NUM_RE = re.compile(r"^(\(-\)|\(\+\)|[△▲\-\+−–(])?(\d[\d,]*(?:\.\d+)?)(%p?|p)?(\))?$")
_GROUPED = re.compile(r"^\d{1,3}(,\d{3})+(\.\d+)?$")


def is_dash(tok: str) -> bool:
    t = tok.strip().lstrip("ㅁ□▯")           # 원문에 대시 앞에 빈 사각형 글리프가 같이 인쇄된 칸(DB생명 2025.4Q p33 '□-')도 대시
    return bool(t) and all(c in _DASHES for c in t) and len(t) <= 2


def parse_num(tok: str):
    """'(14)' '△19%' '-5.1%p' '+2.68' '1,831' '77.38%' -> (value, decimals, has_pct). 숫자가 아니면 None.
    천단위 쉼표 위치가 틀리면(예: '25,2' = 줄바꿈으로 잘린 조각) None."""
    t = tok.strip()
    m = _NUM_RE.match(t)
    if not m:
        return None
    sign, num, pct, close = m.groups()
    if (sign == "(") != bool(close):
        return None
    if "," in num and not _GROUPED.match(num):
        return None
    val = float(num.replace(",", ""))
    if sign in ("△", "▲", "-", "−", "–", "(", "(-)") and val != 0:
        val = -val
    dec = len(num.split(".")[1]) if "." in num else 0
    return (val, dec, bool(pct))


def is_fragment(tok: str) -> bool:
    """줄바꿈으로 잘린 숫자 조각 후보: 숫자·쉼표·소수점만 있고 parse_num 이 거부(또는 짧은 정수)."""
    return bool(re.fullmatch(r"[\d,\.]+%?", tok.strip()))


def fmt_num(v: float | None):
    if v is None:
        return None
    if v == 0:
        return 0.0
    return round(v, 6)


# ---------------------------------------------------------------------------------------------
# 표 B 공통: 경과기간 열 라벨, 구분/포트폴리오 라벨 정규화
# ---------------------------------------------------------------------------------------------
PERIOD_ORDER = [f"{i}년" for i in range(1, 11)] + ["11~15년", "16~20년", "21~25년", "26~30년", "30년 이후", "현재가치"]
AGG_PERIOD_ORDER = ["1~10년"] + PERIOD_ORDER[10:]
_HDR_VOCAB = re.compile(r"^[\d년~이후현재가치합계/\.]+$")
_YEAR_TOKEN = re.compile(r"^(?:FY)?20\d\d(?:년도?)?$")


def canon_period(s: str) -> str | None:
    s = nz(s)
    if not s:
        return None
    if "이후" in s and re.search(r"30", s):
        return "30년 이후"
    if re.fullmatch(r"30년?~", s):          # 세로쓰기 머리말 '30'+'년'+'~' (KB라이프생명)
        return "30년 이후"
    if re.search(r"현재가치|^합계$|^계$|^합$", s) or s in ("현재", "가치"):
        return "현재가치"
    m = re.fullmatch(r"(\d{1,2})년?~(\d{1,2})년?", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return f"{a}~{b}년" if a < b else None
    m = re.fullmatch(r"(\d{1,2})년?", s)
    if m and 1 <= int(m.group(1)) <= 10:
        return f"{int(m.group(1))}년"
    return None


def canon_portfolio(s: str) -> str:
    s = nz(s)
    s = re.sub(r"\(\*\d+\)|\*\d+|주\d+\)", "", s)
    return re.sub(r"[∙ㆍ·•・\.]", "", s)


_PF_OK = re.compile(r"^(?:(?:유배당|무배당|변액)?(?:상해|질병|재물|사망|건강|연금저축|기타)|자산연계형연금저축|기타|합계)$")
_GB_RE = re.compile(r"indirect[-–—−‐‑－]?par|direct[-–—−‐‑－]?par|non[-–—−‐‑－]?par|합계", re.I)


def canon_gubun(tok: str) -> str:
    t = re.sub(r"[-–—−‐‑－]", "", tok.lower())
    if t.startswith("indirect"):
        return "Indirect-Par"
    if t.startswith("direct"):
        return "Direct-Par"
    if t.startswith("non"):
        return "Non-Par"
    return "합계"


METRIC_PATTERNS = (
    ("예상보험금", re.compile(r"^(?:예상)?보험금(?:\(A\))?$")),
    ("위험보험료", re.compile(r"^(?:위험)?보험료\(B\)$|^위험보험료(?:\(B\))?$")),
    ("비율", re.compile(r"^(?:비율|손해율차)(?:\(A/B\))?$")),      # 신한이지손해보험: 비율 행 라벨이 '손해율차(A/B)' 로 인쇄
)


def metric_of(t: str) -> str | None:
    t = nz(t)
    for name, pat in METRIC_PATTERNS:
        if pat.match(t):
            return name
    return None


def parse_unit(text: str) -> str | None:
    m = re.search(r"단위\s*:?\s*(억원|백만원|천원|원|만원)", nz(text).replace("단위:", "단위:"))
    if not m:
        m = re.search(r"단위:?(억원|백만원|천원|만원|원)", nz(text))
    return m.group(1) if m else None


# ---------------------------------------------------------------------------------------------
# 표 B 쪽 파서 (단어 좌표)
# ---------------------------------------------------------------------------------------------
_CAPTION_SKIP = re.compile(r"경영공시|결산|보고서|예상손해율|실제손해율")
_YEAR_IN_LINE = re.compile(r"(?:FY)?(20\d\d)\s*년?")


def _cluster_x(ws: list[Wd], tol: float = 5.0) -> list[list[Wd]]:
    cl: list[list[Wd]] = []
    for w in sorted(ws, key=lambda w: w.xc):
        if cl and abs(sum(x.xc for x in cl[-1]) / len(cl[-1]) - w.xc) <= tol:
            cl[-1].append(w)
        else:
            cl.append([w])
    return cl


_GLUED_HDR = re.compile(r"^(?:\d{1,2}년){2,}$")


def _split_glued_header(w: Wd) -> list[Wd]:
    """'1년2년3년4년5년6년7년8년9년' 처럼 열 머리말 여러 개가 한 단어로 붙어 추출된 경우 -> 열마다 한 단어.
    글자폭은 균등하다고 보고, 첫·마지막 라벨의 중심은 텍스트 끝에서 라벨 폭의 절반 안쪽, 그 사이는 등간격(표 열 폭이 같다는 가정 - 숫자 열 x 와 어긋나면 검산이 잡는다)."""
    t = nz(w.t)
    if not _GLUED_HDR.match(t):
        return [w]
    parts = re.findall(r"\d{1,2}년", t)
    n, total = len(parts), sum(len(p) for p in parts)
    cw = (w.x1 - w.x0) / total
    c1, cn = w.x0 + len(parts[0]) * cw / 2, w.x1 - len(parts[-1]) * cw / 2
    out = []
    for i, p in enumerate(parts):
        xc = c1 + (cn - c1) * i / (n - 1)
        half = len(p) * cw / 2
        out.append(Wd(xc - half, w.y0, xc + half, w.y1, p))
    return out


def _header_columns(ws: list[Wd], y_lo: float, y_hi: float, x_min: float):
    """머리말 열 라벨 군집 -> ([(x중심, 라벨)], carry). 군집 토큰을 y 순으로 이어 붙여 라벨로 만든다('1'+'년', '11'+'년'+'~'+'15'+'년').
    라벨에는 단위 표지('년'·'이후'·'가치'·'계')가 있어야 하고, 라벨이 되는 가장 긴 앞부분만 쓴다.
    인접한 두 군집이 따로는 라벨이 안 되고 합치면 되는 경우('30년' | '이후' 가 나란히)는 합친다.
    머리말 아래에 남는 숫자 토큰은 carry = 이전 쪽 마지막 칸 텍스트가 줄바꿈으로 넘어온 조각(가장 가까운 열에 귀속)."""
    toks = [p for w in ws if y_lo < w.yc < y_hi and w.x0 >= x_min - 6 and _HDR_VOCAB.match(nz(w.t))
            and not _YEAR_TOKEN.match(nz(w.t)) for p in _split_glued_header(w)]
    cols: list[tuple[float, str]] = []
    left: list[Wd] = []
    unres: list[list[Wd]] = []
    seen: set[str] = set()
    hdr_bottom = -1e9
    for cl in _cluster_x(toks):
        cl = sorted(cl, key=lambda w: (round(w.yc / 3), w.x0))
        k, lab = len(cl), None
        while k > 0:
            text = "".join(w.t for w in cl[:k])
            if re.search(r"년|이후|가치|계", text):
                lab = canon_period(text)
                if lab:
                    break
            k -= 1
        # 라벨 뒤에 붙은 숫자 조각(앞 쪽에서 줄바꿈으로 넘어온 칸 끝자리)은 라벨에 넣지 않는다: '30년이후'+'42' -> '30년 이후', '현재가치'+'12' -> '현재가치'
        while lab and k > 1 and re.fullmatch(r"[\d,\.]+", cl[k - 1].t) and canon_period("".join(w.t for w in cl[:k - 1])) == lab:
            k -= 1
        if not lab or lab in seen:     # 같은 라벨이 두 군집으로 쪼개지면(예: '30년'+'이후' 가 다른 x) 앞의 것만 유지
            unres.append(cl)
            continue
        seen.add(lab)
        cols.append((sum(w.xc for w in cl[:k]) / k, lab))
        hdr_bottom = max(hdr_bottom, cl[k - 1].yc)
        left += cl[k:]
    # 인접한 미해결 군집 두 개를 합쳐 라벨이 되는지('30년' + '이후')
    unres.sort(key=lambda c: sum(w.xc for w in c) / len(c))
    i = 0
    merged_idx: set[int] = set()
    while i + 1 < len(unres):
        took = False
        for run in (3, 2):            # '11'|'년~15'|'년' 처럼 가로로 나란히 갈라진 머리말(코리안리)은 3개, '30년'|'이후' 는 2개
            if i + run > len(unres):
                continue
            grp = unres[i:i + run]
            gx = [sum(w.xc for w in c) / len(c) for c in grp]
            if any(b_ - a_ > 34 for a_, b_ in zip(gx, gx[1:])):
                continue
            allw = sorted([w for c in grp for w in c], key=lambda w: (round(w.yc / 3), w.x0))
            text = "".join(w.t for w in allw)
            lab = canon_period(text) if re.search(r"년|이후|가치|계", text) else None
            if lab and lab not in seen:
                seen.add(lab)
                cols.append((sum(w.xc for w in allw) / len(allw), lab))
                hdr_bottom = max(hdr_bottom, max(w.yc for w in allw))
                merged_idx.update(range(i, i + run))
                i += run
                took = True
                break
        if not took:
            i += 1
    for j, cl in enumerate(unres):
        if j not in merged_idx:
            left += cl
    cols.sort(key=lambda c: c[0])
    carry: list[tuple[Wd, str]] = []
    for w in left:
        if w.yc > hdr_bottom and re.fullmatch(r"[\d,\.]+", w.t) and cols:
            j = min(range(len(cols)), key=lambda i: abs(cols[i][0] - w.xc))
            if abs(cols[j][0] - w.xc) <= 9.0:
                carry.append((w, cols[j][1]))
    return cols, carry


def _find_caption(lines: list[list[Wd]], y_above: float, y_floor: float) -> tuple[int | None, str | None, str | None]:
    """블록 머리말(경과기간 줄) 위쪽에서 가장 가까운 연도 캡션 -> (연도, 단위, 부문)."""
    year = unit = seg = None
    for ln in reversed(lines):
        y = sum(w.yc for w in ln) / len(ln)
        if not (y_floor <= y < y_above):
            continue
        txt = line_text(ln)
        tz = nz(txt)
        if sum(1 for w in ln if parse_num(w.t) is not None or is_dash(w.t)) >= 3:      # 데이터 행(숫자 붙임 '...2019' 가 연도로 오인되는 것 방지)
            continue
        if unit is None:
            unit = parse_unit(txt)
        if year is None and not _CAPTION_SKIP.search(tz) and len(tz) < 70:
            m = _YEAR_IN_LINE.search(tz)
            if m and "단위" not in tz[:3]:
                year = int(m.group(1))
                ms = re.search(r":\s*(생명|장기손해|장기|일반|자동차)", tz)
                if ms:
                    seg = ms.group(1)
            else:                      # 감사보고서 주석 사본: '<당기>' '1) 당기' '2) 전기' (연도 대신) -> -1 당기 / -2 전기
                mc = re.fullmatch(r"[<(]?(?:\d+\)|[가나다]\.)?(당기말?|전기말?)[>)]?", tz)
                if mc:
                    year = -1 if mc.group(1).startswith("당") else -2
        if year is not None and unit is not None:
            break
    return year, unit, seg


_SPLIT_RE = re.compile(r"[△▲\-\(]?\d{1,3}(?:,\d{3})+(?:\.\d+)?%?\)?|[△▲\-\(]?\d+(?:\.\d+)?%?\)?")


def _split_ws_words(ws: list[Wd]) -> list[Wd]:
    """한 단어 안에 공백(NBSP)으로 이어진 숫자 둘 이상('0  0' - 하나손해보험 2025.4Q 5·6년 칸)을 글자 위치 비례로 쪼갠다. 안 쪼개면 두 칸이 통째로 버려진다."""
    out: list[Wd] = []
    changed = False
    for w in ws:
        if re.search(r"\s", w.t):
            pcs = w.t.split()
            if len(pcs) >= 2 and all(is_dash(p) or parse_num(p) is not None or is_fragment(p) for p in pcs):
                total, pos = len(w.t), 0
                for pc in pcs:
                    i = w.t.index(pc, pos)
                    out.append(Wd(w.x0 + (w.x1 - w.x0) * i / total, w.y0, w.x0 + (w.x1 - w.x0) * (i + len(pc)) / total, w.y1, pc))
                    pos = i + len(pc)
                changed = True
                continue
        out.append(w)
    return out if changed else ws


def _recalibrate_cols(ws: list[Wd], cols: list[tuple[float, str]], y_lo: float, y_hi: float, x_min: float):
    """머리말 없는 이어짐 쪽의 열 x 재보정. 쪽마다 표가 좌우로 밀려 있을 수 있어(하나손해보험 2024.4Q p31 은 머리말 x 보다 +12~17pt)
    상속한 x 로는 한 칸 옆 열에 붙는다. 이 쪽 숫자·대시 토큰의 x 군집 수가 열 수와 같을 때만 군집 중심을 열 x 로 쓴다(순서대로 라벨).
    반환 (cols, 바뀌었는지)."""
    xs = sorted(w.xc for w in ws if y_lo <= w.yc <= y_hi and w.xc > x_min + 8 and (is_dash(w.t) or parse_num(w.t) is not None))
    if len(xs) < len(cols) or len(cols) < 4:
        return cols, False
    pitches = [b[0] - a[0] for a, b in zip(cols, cols[1:])]
    gap = 0.5 * min(pitches)
    clusters: list[list[float]] = [[xs[0]]]
    for x in xs[1:]:
        if x - clusters[-1][-1] > gap:
            clusters.append([x])
        else:
            clusters[-1].append(x)
    if len(clusters) != len(cols):
        return cols, False
    new = [(sum(c) / len(c), cols[i][1]) for i, c in enumerate(clusters)]
    if max(abs(n[0] - o[0]) for n, o in zip(new, cols)) < 2.5:
        return cols, False
    return new, True


def _cols_from_data(ws: list[Wd], cols: list[tuple[float, str]], y_lo: float, y_hi: float, x_min: float):
    """머리말을 일부밖에 못 읽었을 때(NH농협손해보험 2025.4Q: '5년6년7년8년9년10년11년~' 이 한 단어로 붙음) 열 x 를 데이터에서 구한다.
    데이터 숫자·대시 토큰의 x 군집이 정확히 16개(표의 열 수)이고, 읽은 머리말 열들이 표준 순서(1~10년, 11~15, 16~20, 21~25, 26~30, 30년 이후, 현재가치)의
    같은 번호 군집 근처(0.6 열폭)에 있을 때만 군집 중심 + 표준 라벨 16개를 쓴다. 아니면 None."""
    if len(cols) < 2 or len(cols) >= len(PERIOD_ORDER):
        return None
    pit = sorted(b[0] - a[0] for a, b in zip(cols, cols[1:]) if b[0] - a[0] > 5)
    pmin = pit[0] if pit else 19.0
    xs = sorted(w.xc for w in ws if y_lo <= w.yc <= y_hi and w.xc > x_min + 8 and (is_dash(w.t) or parse_num(w.t) is not None))
    if len(xs) < len(PERIOD_ORDER):
        return None
    clusters: list[list[float]] = [[xs[0]]]
    for x in xs[1:]:
        if x - clusters[-1][-1] > 0.5 * pmin:
            clusters.append([x])
        else:
            clusters[-1].append(x)
    if len(clusters) != len(PERIOD_ORDER):
        return None
    new = [(sum(c) / len(c), PERIOD_ORDER[i]) for i, c in enumerate(clusters)]
    for x, lab in cols:
        if lab not in PERIOD_ORDER:
            return None
        if abs(new[PERIOD_ORDER.index(lab)][0] - x) > 0.6 * pmin:
            return None
    return new


def _merge_split_metric_labels(ws: list[Wd]) -> list[Wd]:
    """지표 라벨이 좁은 칸에서 줄바꿈으로 갈라진 경우('예상보'/'험금(A)', '위험보'/'험료(B)', '비율(A'/'/B)')를 한 단어로 합친다.
    아래 줄 단어와 x 중심이 12pt 이내이고 두 단어를 이은 글자가 지표 라벨이 될 때만(각각은 지표가 아님) 합친다 - 롯데손해보험 2025.4Q."""
    cands = [w for w in ws if metric_of(w.t) is None and re.search(r"[예위비][상험율]", w.t) and len(w.t) <= 8]
    used: set[int] = set()
    merged: list[Wd] = []
    for w1 in cands:
        if id(w1) in used:
            continue
        best = None
        for w2 in ws:
            if w2 is w1 or id(w2) in used or metric_of(w2.t) is not None:
                continue
            dy = w2.y0 - w1.y0
            if not (4.0 <= dy <= 26.0) or abs(w1.xc - w2.xc) > 12.0:
                continue
            if metric_of(w1.t + w2.t) is None:
                continue
            if best is None or dy < best[0]:
                best = (dy, w2)
        if best is not None:
            w2 = best[1]
            used.update((id(w1), id(w2)))
            merged.append(Wd(min(w1.x0, w2.x0), w1.y0, max(w1.x1, w2.x1), w2.y1, nz(w1.t + w2.t)))
    if not merged:
        return ws
    out = [w for w in ws if id(w) not in used] + merged
    out.sort(key=lambda w: (round(w.yc, 0), w.x0))
    return out


def get_hsegs(page) -> list[tuple[float, float, float]]:
    """쪽의 가로 괘선 조각 (y, x0, x1). 직선('l')·얇은 사각형('re')·채움 사각형의 위/아래 변('reT'/'reB')을 모두 모은다."""
    segs: list[tuple[float, float, float]] = []
    try:
        drawings = page.get_drawings()
    except Exception:  # noqa: BLE001
        return segs
    for d in drawings:
        for it in d["items"]:
            if it[0] == "l":
                p1, p2 = it[1], it[2]
                if abs(p1.y - p2.y) < 0.6:
                    segs.append(((p1.y + p2.y) / 2, min(p1.x, p2.x), max(p1.x, p2.x)))
            elif it[0] == "re":
                r = it[1]
                if r.width > 6:
                    if r.height < 1.6:
                        segs.append(((r.y0 + r.y1) / 2, r.x0, r.x1))
                    else:
                        segs.append((r.y0, r.x0, r.x1))
                        segs.append((r.y1, r.x0, r.x1))
    return segs


def _rules_over(segs: list[tuple[float, float, float]], x_lo: float, x_hi: float) -> list[float]:
    """데이터 열 범위 [x_lo, x_hi] 의 70% 이상을 덮는 가로 괘선의 y 목록(같은 y 조각들은 x 구간을 합쳐서 판정)."""
    if not segs or x_hi - x_lo < 50:
        return []
    ys = sorted({round(y, 1) for y, _, _ in segs})
    groups: list[list[float]] = []
    for y in ys:
        if groups and y - groups[-1][-1] < 0.8:
            groups[-1].append(y)
        else:
            groups.append([y])
    out: list[float] = []
    for g in groups:
        lo_g, hi_g = g[0] - 0.4, g[-1] + 0.4
        ivs = sorted((max(a, x_lo), min(b, x_hi)) for y, a, b in segs if lo_g <= y <= hi_g and b > x_lo and a < x_hi)
        cov, cur_lo, cur_hi = 0.0, None, None
        for a, b in ivs:
            if cur_hi is None or a > cur_hi + 1.0:
                if cur_hi is not None:
                    cov += cur_hi - cur_lo
                cur_lo, cur_hi = a, b
            else:
                cur_hi = max(cur_hi, b)
        if cur_hi is not None:
            cov += cur_hi - cur_lo
        if cov >= 0.7 * (x_hi - x_lo):
            out.append(sum(g) / len(g))
    return out


def _row_intervals(label_ys: list[float], rules: list[float]):
    """행 라벨 y 마다 그 라벨을 품은 괘선 구간 (lo, hi). 모든 라벨이 서로 다른 구간에 있고 첫~끝 라벨 사이에 라벨 없는 구간이 없을 때만 유효(아니면 None)."""
    if len(rules) < 3 or not label_ys:
        return None
    ivs = []
    for y in label_ys:
        ivs.append(bisect.bisect_right(rules, y) - 1)         # -1 = 첫 괘선 위, len-1 = 마지막 괘선 아래(쪽 경계라 윗/아랫 테두리가 없는 행)
    if len(set(ivs)) != len(ivs):
        return None
    if max(ivs) - min(ivs) + 1 != len(ivs):
        return None
    out = []
    for y, i in zip(label_ys, ivs):
        lo = rules[i] if i >= 0 else 2 * y - rules[0]         # 열린 쪽은 라벨 대칭으로 닫는다
        hi = rules[i + 1] if i + 1 < len(rules) else 2 * y - rules[-1]
        out.append((lo, hi))
    return out


def parse_B_page(ws: list[Wd], state: dict, y_stop: float | None = None, segs: list | None = None) -> list[dict]:
    """한 쪽의 표 B 블록들. state(year/unit/segment/cols)는 쪽 사이 상속(캡션·머리말이 없는 이어짐 쪽).
    그룹 = 같은 포트폴리오의 (예상보험금, 위험보험료, 비율) 3행. 쪽 경계에서 3행이 갈라지면 한 쪽엔 일부 행만 있다(extract_B_sections 가 이어 붙인다)."""
    if y_stop is not None:
        ws = [w for w in ws if w.yc < y_stop]
    ws = _split_ws_words(ws)
    ws = _merge_split_metric_labels(ws)
    cand = [(w, metric_of(w.t)) for w in ws]
    cand = [(w, m) for w, m in cand if m]
    # 이중으로 그린 지표 라벨('비율' + '비율(A/B)' 가 같은 자리) -> 같은 지표가 y·x0 3pt 이내에 둘이면 긴 쪽만(한화생명)
    cand.sort(key=lambda t: (t[1], t[0].yc, t[0].x0))
    dd: list = []
    for w, m in cand:
        if dd and dd[-1][1] == m and abs(dd[-1][0].yc - w.yc) < 3.0 and abs(dd[-1][0].x0 - w.x0) < 3.0:
            if len(w.t) > len(dd[-1][0].t):
                dd[-1] = (w, m)
            continue
        dd.append((w, m))
    cand = dd
    # 제목 줄의 '위험보험료 대비 예상보험금' 같은 서술 속 단어를 버린다. 진짜 지표 행 라벨은 같은 줄(줄바꿈된 숫자는 ±9pt) 오른쪽에 숫자·대시가 3개 이상 있다.
    # 전 칸이 빗금인 행(숫자 없음)의 라벨은 같은 지표의 '숫자 있는 행 라벨' x0 범위(±6pt) 안이고 머리말 아래면 남긴다.
    # (라벨 x 위치는 칸 가운데/왼쪽 정렬이 행마다 달라 x 최빈값으로만 거르면 합계 행 라벨을 잃는다)
    def _has_values(w0: Wd) -> bool:
        n = 0
        for t in ws:
            if abs(t.yc - w0.yc) <= 9.0 and t.x0 >= w0.x1 + 4 and (is_dash(t.t) or parse_num(t.t) is not None or is_fragment(t.t)):
                n += 1
                if n >= 3:
                    return True
        return False

    valued = [(w, mm) for w, mm in cand if _has_values(w)]
    keep: list = []
    if valued:
        vid = {id(w) for w, _ in valued}
        bands = {m: (min(w.x0 for w, mm in valued if mm == m) - 6.0, max(w.x0 for w, mm in valued if mm == m) + 6.0)
                 for m in {mm for _, mm in valued}}
        hdr_ys = [w.yc for w in ws if nz(w.t) in ("경과기간", "경과", "경과기")]
        y_floor = min(hdr_ys) if hdr_ys else -1e9
        # 값 있는 라벨이 없는 지표(그 쪽에서 전 칸이 빈 칸인 행 - 흥국화재 2025.4Q p28)는 값 있는 라벨 전체의 x0 범위로 거른다
        all_band = (min(bd[0] for bd in bands.values()), max(bd[1] for bd in bands.values()))
        keep = [(w, mm) for w, mm in cand if id(w) in vid or ((bands.get(mm) or all_band)[0] <= w.x0 <= (bands.get(mm) or all_band)[1] and w.yc > y_floor)]
    else:                                  # 숫자가 전혀 없는 쪽(전 칸 빗금 등): 예전 방식(지표별 x0 최빈값)으로 폴백
        for m in _METRICS3:
            xs = [round(w.x0 / 3) for w, mm in cand if mm == m]
            if not xs:
                continue
            mode = Counter(xs).most_common(1)[0][0]
            keep += [(w, mm) for w, mm in cand if mm == m and abs(round(w.x0 / 3) - mode) <= 2]
    cand = keep
    bw = [w for w, m in cand if m == "위험보험료"]
    if not bw:
        return []
    anchors = sorted(w.yc for w in ws if nz(w.t) in ("경과기간", "경과", "경과기"))
    anc: list[float] = []
    for y in anchors:                      # 40pt 이내 = 같은 머리말
        if not anc or y - anc[-1] > 40:
            anc.append(y)
    # 구간: 첫 머리말 위(머리말 없이 이어진 행) + 머리말마다 1구간
    regions: list[tuple[float, float, float | None]] = []
    if anc:
        if min(w.yc for w in bw) < anc[0] - 45:
            regions.append((-1e9, anc[0] - 45, None))
        for i, a in enumerate(anc):
            regions.append((a - 1, (anc[i + 1] - 1) if i + 1 < len(anc) else 1e9, a))
    else:
        regions.append((-1e9, 1e9, None))
    blocks: list[dict] = []
    lines_all = group_lines(ws)
    for y_lo, y_hi, anchor in regions:
        rows_w = [(w, m) for w, m in cand if y_lo < w.yc < y_hi]
        bw_r = [w for w, m in rows_w if m == "위험보험료"]
        if not bw_r:
            continue
        xr0, xr1 = min(w.x0 for w in bw_r) - 4, max(w.x1 for w in bw_r) + 4
        rows_w = [(w, m) for w, m in rows_w if xr0 - 14 <= w.xc <= xr1 + 14]
        rows_w.sort(key=lambda t: t[0].yc)
        groups: list[dict] = []
        for w, m in rows_w:
            if m == "예상보험금":
                groups.append({"rows": {"예상보험금": w}, "cells": defaultdict(list)})
            elif groups and m not in groups[-1]["rows"] and w.yc - max(x.yc for x in groups[-1]["rows"].values()) < 90 \
                    and not (m == "비율" and "위험보험료" not in groups[-1]["rows"] and "예상보험금" in groups[-1]["rows"]
                             and False):
                groups[-1]["rows"][m] = w
            else:
                groups.append({"rows": {m: w}, "cells": defaultdict(list)})
        if not groups:
            continue
        for g in groups:
            ys = [w.yc for w in g["rows"].values()]
            g["y0"], g["y1"], g["yc"] = min(ys), max(ys), sum(ys) / len(ys)
        first_y = min(w.yc for w, _ in rows_w)
        last_y = max(w.yc for w, _ in rows_w)
        pitch = (last_y - first_y) / max(len(rows_w) - 1, 1) if len(rows_w) > 1 else 11.0
        # --- 머리말 열
        hdr_lo = (anchor - 42) if anchor is not None else (first_y - 60)
        if blocks and blocks[-1]["page_y1"] > hdr_lo:
            hdr_lo = blocks[-1]["page_y1"] + 2
        cols, carry = _header_columns(ws, hdr_lo, first_y - 3.5, xr1) if anchor is not None else ([], [])
        flags: list[str] = []
        if cols:
            state["cols"] = cols
        elif state.get("cols"):
            cols = state["cols"]
            flags.append("cols_inherited")
        else:
            flags.append("no_header")
        # --- 캡션(연도·단위·부문)
        yr, unit, seg = _find_caption(lines_all, (anchor - 8) if anchor is not None else first_y - 5,
                                      (blocks[-1]["page_y1"] if blocks else -1e9)) if anchor is not None else (None, None, None)
        if yr is not None:
            state["year"] = yr
            state["segment"] = seg
        if unit is not None:
            state["unit"] = unit
        if "cols_inherited" in flags or (cols and len(cols) == len(PERIOD_ORDER)):      # 머리말이 있어도 머리말 x 가 데이터 x 와 밀려 있을 수 있다(하나손해보험 2025.4Q: 11~15년 열이 -13pt)
            cols, changed = _recalibrate_cols(ws, cols, first_y - pitch * 0.6, last_y + pitch * 0.7, xr1)
            if changed:
                flags.append("cols_recalibrated")
        elif cols and len(cols) < len(PERIOD_ORDER):
            c2 = _cols_from_data(ws, cols, first_y - pitch * 0.6, last_y + pitch * 0.7, xr1)
            if c2:
                cols = c2
                state["cols"] = cols
                flags.append("cols_from_data")
        # --- 숫자 토큰 -> (그룹, 지표, 열) 칸
        row_ys = sorted((w.yc, g_i, m) for g_i, g in enumerate(groups) for m, w in g["rows"].items())
        ylist = [t[0] for t in row_ys]
        # 행별 허용 거리: 평균 행 간격(pitch)이 아니라 이웃 행 라벨까지의 거리의 절반 - 3줄로 줄바꿈된 키 큰 행(합계 행)의 첫·끝 줄이 평균 간격으론 고아가 된다(한화생명 2024.4Q p31).
        # 옛 규칙(0.62*pitch+1.5)보다 좁아지지는 않는다. 앞 쪽에서 넘어온 carry 줄(이웃 행 거리의 0.65배)은 0.5배+1.5 밖이라 여전히 제외된다.
        row_tol: list[float] = []
        for kk in range(len(ylist)):
            nb = [abs(ylist[kk] - ylist[jj]) for jj in (kk - 1, kk + 1) if 0 <= jj < len(ylist) and abs(ylist[kk] - ylist[jj]) > 1.0]
            row_tol.append(max(pitch * 0.62 + 1.5, (0.5 * min(nb) + 1.5) if nb else 0.0))
        lo_y = min(first_y - pitch * 0.6, ylist[0] - row_tol[0])
        hi_y = max(last_y + pitch * 0.7, ylist[-1] + row_tol[-1])
        # 괘선이 있으면 행 = 괘선 구간. 행마다 키가 다르고(1~3줄 줄바꿈) 라벨은 구간 가운데라서, 라벨 거리만으로는 이웃 행 칸이 섞인다(한화생명 2024.4Q p32)
        ivs = None
        rules: list[float] = []
        if segs and cols:
            rules = _rules_over(segs, min(c[0] for c in cols) - 8, max(c[0] for c in cols) + 8)
            ivs = _row_intervals(ylist, rules)
            if ivs is not None:
                lo_y, hi_y = min(lo_y, ivs[0][0]), max(hi_y, ivs[-1][1])
        # 머리말 없는 이어짐 쪽(첫 블록): 첫 행 라벨 위쪽에 남은 숫자 조각 = 앞 쪽 마지막 칸 내용의 이어짐(carry). 머리말이 있는 쪽은 _header_columns 가 이미 잡았다.
        if anchor is None and not blocks and cols and not carry and ivs is not None:      # 괘선이 있을 때만: 첫 행 구간 '위'에 있는 숫자만 carry (첫 행 자신의 줄바꿈 윗줄과 구분)
            for w in ws:
                if ivs[0][0] - 45.0 < w.yc < ivs[0][0] - 0.3 and w.xc > xr1 and (re.fullmatch(r"[\d,\.]+", w.t) or is_dash(w.t)):
                    j = min(range(len(cols)), key=lambda i: abs(cols[i][0] - w.xc))
                    if abs(cols[j][0] - w.xc) <= 9.0:
                        carry.append((w, cols[j][1]))
        orphans = 0
        glued_bad = 0
        for w in ws:
            if not (lo_y <= w.yc <= hi_y):
                continue
            if w.x0 < xr1 - 6 or w.xc < xr1:
                continue
            tok = w.t
            if not (is_dash(tok) or parse_num(tok) or is_fragment(tok) or _SPLIT_RE.fullmatch(tok) or re.fullmatch(r"(?:%|%p)", tok)):
                if not re.fullmatch(r"[\d,\.△▲\-\(\)%]+", tok):
                    continue
            if ivs is not None:
                k = next((i for i, (lo_, hi_) in enumerate(ivs) if lo_ - 0.3 <= w.yc <= hi_ + 0.3), None)
                if k is None:
                    orphans += 1
                    continue
            else:
                k = min(range(len(ylist)), key=lambda i: abs(ylist[i] - w.yc))
                if abs(ylist[k] - w.yc) > row_tol[k]:
                    orphans += 1
                    continue
            _, g_i, m = row_ys[k]
            if not cols:
                orphans += 1
                continue
            spanned = [j for j, (xc, _) in enumerate(cols) if w.x0 - 3 <= xc <= w.x1 + 3]
            if len(spanned) >= 2:           # 인접 열 숫자가 붙어 한 단어로 추출된 경우('30,755149,239129,153')
                parts = _SPLIT_RE.findall(tok)
                if not (len(parts) == len(spanned) and "".join(parts) == tok):      # 소수 인쇄 비율이 붙은 경우('0.00.0' '41.439.3'): 소수 자릿수가 같다고 보고 자른다
                    for dd in (1, 2, 3):
                        p2 = re.findall(rf"[△▲\-\(]?\d+\.\d{{{dd}}}%?\)?", tok)
                        if len(p2) == len(spanned) and "".join(p2) == tok:
                            parts = p2
                            break
                if len(parts) == len(spanned) and "".join(parts) == tok:
                    for jj, part in zip(spanned, parts):
                        groups[g_i]["cells"][(m, cols[jj][1])].append(Wd(w.x0, w.y0, w.x1, w.y1, part))
                else:
                    glued_bad += 1
                continue
            j = min(range(len(cols)), key=lambda i: abs(cols[i][0] - w.xc))
            pitch_x = min([abs(cols[j][0] - c[0]) for i, c in enumerate(cols) if i != j] or [40.0])
            if abs(cols[j][0] - w.xc) > max(pitch_x * 0.62, 6.0):
                orphans += 1
                continue
            groups[g_i]["cells"][(m, cols[j][1])].append(w)
        lab_ws = [w for w in ws if w.xc < xr0 + 2 and first_y - pitch * 0.6 <= w.yc <= last_y + pitch * 0.6
                  and not (is_dash(w.t) or parse_num(w.t))]
        # 캡션에 연도가 없고 왼쪽 열에 '당기'·'전기' 만 인쇄된 표(미래에셋생명 감사보고서 사본): 라벨 글자가 아니라 연도 표지로 따로 둔다
        # (좁은 칸에서 '무배'|'당기'|'타' 처럼 갈라진 포트폴리오 라벨 조각과 구별: 연도 표지는 '구분' 머리말보다 왼쪽 열에 있다)
        _PM = ("당기", "전기", "당기말", "전기말")
        gx_l = [w.xc for w in ws if hdr_lo < w.yc < first_y and w.xc < xr0 + 2 and nz(w.t) == "구분"]
        if gx_l:
            state["gx"] = min(gx_l)
        gx_ = state.get("gx")
        pmarks = sorted((w.yc, nz(w.t)) for w in lab_ws if gx_ is not None and nz(w.t) in _PM and w.xc < gx_ - 6.0)
        lab_ws = [w for w in lab_ws if not (gx_ is not None and nz(w.t) in _PM and w.xc < gx_ - 6.0)]
        # 쪽 맨 앞 이어짐 구간: 세로쓰기 라벨 열에서 첫 행 위로 넘쳐 온 글자(앞 쪽 마지막 그룹 라벨의 뒷부분)
        spill_ws: list[Wd] = []
        if anchor is None and not blocks:
            xs_lab = sorted(w.xc for w in lab_ws if len(w.t) == 1 and _HANGUL.search(w.t))
            if xs_lab:
                mx = xs_lab[len(xs_lab) // 2]
                spill_ws = [w for w in ws if len(w.t) == 1 and _HANGUL.search(w.t) and abs(w.xc - mx) <= 4.0
                            and first_y - pitch * 3.2 <= w.yc < first_y - pitch * 0.6]
        # 가로쓰기 라벨이 쪽 경계에서 갈라진 경우('무배당' | '연금ㆍ저축'): 첫 행 구간 위에 남은 한글 조각 = 앞 쪽 마지막 그룹 라벨의 뒷부분
        spill_h = ""
        if anchor is None and not blocks:
            top_y = ivs[0][0] if ivs is not None else first_y - pitch * 0.6
            sh = [w for w in ws if _HANGUL.search(w.t) and w.xc < xr0 + 2 and top_y - 45.0 < w.yc < top_y - 0.3
                  and metric_of(w.t) is None and nz(w.t) not in _B_HDR_WORDS]
            spill_h = "".join(w.t for w in sorted(sh, key=lambda w: (round(w.yc / 3.0), w.x0)))
        blocks.append({"groups": groups, "cols": cols, "year": state.get("year"), "carry": (carry if not blocks else []),
                       "pf_spill_h": spill_h, "period_marks": pmarks,
                       "unit": state.get("unit"), "segment": state.get("segment"), "lab_ws": lab_ws, "spill_ws": spill_ws,
                       "xr0": xr0, "xr1": xr1, "page_y0": first_y, "page_y1": last_y, "flags": flags,
                       "orphans": orphans, "glued_bad": glued_bad, "hdr_y": anchor, "n_rules": len(rules), "ivs_ok": ivs is not None,
                       "label_ys": ylist, "rules": rules,
                       "header_ws": [w for w in ws if hdr_lo < w.yc < first_y and w.xc < xr0 + 2]})
    return blocks


def _gubun_tokens(gub_ws: list[Wd]) -> list[tuple[str, float]]:
    """구분 열 단어를 y,x 순으로 이어붙여 'Non-Par' 'Indirect-Par' 'Direct-Par' 토큰과 y중심을 뽑는다
    (줄바꿈으로 'In'/'direct'/'-Par' 처럼 쪼개져 있어도 텍스트로 분절하므로, 인접한 두 구분 라벨이 붙어 있어도 안전)."""
    chars: list[tuple[str, float]] = []
    for w in sorted(gub_ws, key=lambda w: (round(w.yc / 2.5), w.x0)):
        for c in re.sub(r"\(\*\d+\)|\*\d+", "", w.t):
            if not c.isspace():
                chars.append((c, w.yc))
    s = "".join(c for c, _ in chars)
    out = []
    for m in _GB_RE.finditer(s):
        ys = [chars[i][1] for i in range(m.start(), m.end())]
        out.append((canon_gubun(m.group(0)), sum(ys) / len(ys), m.group(0)))
    return out


def _gub_chars(gub_ws: list[Wd]) -> list[tuple[str, float]]:
    """구분 열 글자(y,x 순)와 글자별 y. 라벨이 쪽 경계에서 'Indir' | 'ect-Par' 로 갈라져도 표의 연속 블록 글자열을 이으면 한 라벨이 된다."""
    chars: list[tuple[str, float]] = []
    for w in sorted(gub_ws, key=lambda w: (round(w.yc / 2.5), w.x0)):
        for c in re.sub(r"\(\*\d+\)|\*\d+", "", w.t):
            if not c.isspace():
                chars.append((c, w.yc))
    return chars


def _gub_stream(gub_ws: list[Wd]) -> str:
    return "".join(c for c, _ in _gub_chars(gub_ws))


def _partition_cost(groups: list[dict], toks: list[tuple[str, float]], cuts: tuple[int, ...]) -> float:
    edges = (0, *cuts, len(groups))
    cost = 0.0
    for j, tk in enumerate(toks):
        ty = tk[1]
        seg = groups[edges[j]:edges[j + 1]]
        mid = (seg[0]["y0"] + seg[-1]["y1"]) / 2
        cost += abs(ty - mid)
    return cost


_HANGUL = re.compile(r"[가-힣]")
_B_HDR_WORDS = {"구분", "포트폴리오", "포트", "폴리오", "폴리", "경과기간", "경과기", "경과", "간", "구", "분", "포", "트", "폴", "리", "오"}
_PF_CATS = ("상해", "질병", "재물", "사망", "건강", "연금저축", "기타")
_PF_TOK = re.compile(r"(?:유배당|무배당|변액)?(?:" + "|".join(_PF_CATS) + r")|자산연계형연금저축")
_PF_FULLS = [pre + c for pre in ("유배당", "무배당", "변액", "") for c in _PF_CATS] + ["자산연계형연금저축"]
_PF_CAT_ORDER = {"상해": 0, "질병": 1, "재물": 2, "사망": 3, "건강": 4, "연금저축": 5, "기타": 7}
_PF_PRE_ORDER = {"유배당": 0, "무배당": 1, "변액": 2, None: 3}


def _is_pf_frag(s: str, lead: bool) -> bool:
    """s 가 표준 라벨의 진부분 접미(lead=True, 쪽 앞 조각) / 접두(lead=False, 쪽 끝 조각)인가 - 쪽을 넘어 이어질 수 있는 라벨 조각."""
    return bool(s) and any(f != s and (f.endswith(s) if lead else f.startswith(s)) for f in _PF_FULLS)


def _pf_clean(raw: str | None) -> str | None:
    """포트폴리오 원문 -> 표준 라벨. 표준 라벨이 정확히 하나 들어 있고 나머지가 잡음(주석 문장·옆 라벨의 글자)이면 라벨만 남기고,
    나머지가 쪽을 넘어 이어질 조각이면 원문(공백·주석 제거본)을 그대로 둔다(쪽 병합 뒤 다시 정리된다)."""
    s = canon_portfolio(raw or "")
    if not s:
        return None
    toks = list(_PF_TOK.finditer(s))
    if len(toks) != 1:
        return s
    t = toks[0]
    lead, tail = s[:t.start()], s[t.end():]
    if not _is_pf_frag(lead, True) and not _is_pf_frag(tail, False):
        return t.group(0)
    return s


def _pf_order(pf: str | None):
    if not pf:
        return None
    if pf == "자산연계형연금저축":
        return (6, 0)
    m = re.fullmatch(r"(유배당|무배당|변액)?(" + "|".join(_PF_CATS) + r")", pf)
    return (_PF_CAT_ORDER[m.group(2)], _PF_PRE_ORDER[m.group(1)]) if m else None


def _pf_stream_assign(groups: list[dict], pf_ws: list[Wd], total_g, spill_ws: list[Wd] | None = None):
    """세로쓰기 라벨(글자마다 한 단어): 글자를 y 순으로 이어 붙여 표준 라벨로 분절하고, 조각 수가 그룹 수와 같으면 순서대로 귀속.
    셀 높이가 제각각이라 글자 y 로 그룹을 정하면 경계 글자가 이웃 그룹으로 새기 때문. 반환 ({그룹 인덱스: 라벨 원문}, 넘침) 또는 None.
    넘침 = 앞 쪽 마지막 그룹 라벨의 뒷부분이 이 쪽 맨 위에 남은 글자(그룹 수보다 조각이 하나 많고 첫 조각이 라벨 접미일 때).
    쪽 맨 앞 이어지는 그룹의 라벨 조각('당'+'건강')은 표준 라벨 접미가 되면 한 조각으로 합친다."""
    tg = total_g if isinstance(total_g, set) else ({total_g} if total_g is not None else set())
    idx = [i for i in range(len(groups)) if i not in tg]
    if not pf_ws or not idx:
        return None
    if sum(1 for w in pf_ws if len(canon_portfolio(w.t)) <= 1) < 0.6 * len(pf_ws):
        return None
    allw = list(spill_ws or []) + list(pf_ws)
    s = "".join(canon_portfolio(w.t) for w in sorted(allw, key=lambda w: (round(w.yc / 2.0), w.x0)))
    items: list[tuple[str, bool]] = []
    pos = 0
    for m in _PF_TOK.finditer(s):
        if m.start() > pos:
            items.append((s[pos:m.start()], False))
        items.append((m.group(0), True))
        pos = m.end()
    if pos < len(s):
        items.append((s[pos:], False))
    if len(items) >= 2 and not items[0][1] and items[1][1] and not re.match(r"(유배당|무배당|변액)", items[1][0])             and _is_pf_frag(items[0][0] + items[1][0], True):
        items[:2] = [(items[0][0] + items[1][0], False)]
    texts = [t for t, _ in items]
    spill = ""
    if len(texts) == len(idx) + 1 and spill_ws and _is_pf_frag(texts[0], True):
        spill, texts = texts[0], texts[1:]
    if len(texts) != len(idx):
        return None
    return dict(zip(idx, texts)), spill


def assign_labels(block: dict, state: dict | None = None) -> list[str]:
    """block['groups'] 각 그룹에 gubun/pf 를 채운다. 문제는 플래그 문자열로 반환.
    구분(Non-Par 등)은 병합셀이라 라벨이 span 중앙에 한 번만 찍힌다. span 은 그룹 단위 연속 구간이므로
    '라벨 y 중심 = span 중심' 이 되는 분할을 찾는다. 쪽을 넘어 이어지는 span 은 앞/뒤에 라벨 없는 span 이 붙을 수 있고,
    앞쪽 이어짐은 직전 쪽의 마지막 구분을 물려받는다(state['last_gubun'])."""
    from itertools import combinations
    state = state if state is not None else {}
    flags: list[str] = []
    groups = block["groups"]
    # 머리말 글자('구분' '포트폴리오' 세로쓰기 '포 트 폴 리 오' 등)가 첫 그룹 라벨 영역으로 새어 드는 것을 거른다
    lab_ws = [w for w in block["lab_ws"] if nz(w.t) not in _B_HDR_WORDS]
    hdr = block["header_ws"]
    a = [w.xc for w in hdr if nz(w.t) == "구분"]
    b = [w.xc for w in hdr if nz(w.t) in ("포트폴리오", "포트", "폴리오", "폴리", "오")]
    if a and b:
        mid = (min(a) + sum(b) / len(b)) / 2
        state["mid"] = mid
    elif state.get("mid") is not None:
        mid = state["mid"]
    else:
        xs = sorted({round(w.x0 / 6) * 6 for w in lab_ws if nz(w.t) != "합계"})
        mid = (xs[0] + xs[1]) / 2 + 1 if len(xs) >= 2 else -1e9
        flags.append("label_split_guess")
    # 합계(두 라벨 열에 걸쳐 가운데 정렬; '합 계' 처럼 두 단어로 쪼개져도 그룹 단위로 이어붙여 판정)
    total_g = None
    total_gs: set[int] = set()            # 한 블록에 합계 그룹이 둘 이상(머리말 없이 이어진 당기·전기 두 표)일 수 있다
    near: dict[int, list[Wd]] = defaultdict(list)
    for w in lab_ws:
        near[min(range(len(groups)), key=lambda i: abs(groups[i]["yc"] - w.yc))].append(w)
    tot_ws: set[int] = set()
    for gi, wl in near.items():
        if nz("".join(w.t for w in sorted(wl, key=lambda w: (round(w.yc / 3), w.x0)))) == "합계":
            groups[gi]["gubun"], groups[gi]["pf"] = "합계", "합계"
            groups[gi]["gubun_raw"] = "합계"
            total_g = gi
            total_gs.add(gi)
            tot_ws.update(id(w) for w in wl)
    # 구분 열 단어 = 라틴 글자뿐인 단어(Non/-Par/direct...) 또는 mid 왼쪽 단어, 포트폴리오 열 단어 = mid 오른쪽의 한글 단어
    # (x 경계만으로 나누면 줄바꿈된 'Non' '-Par' 조각이 포트폴리오 라벨에 섞인다)
    gub_ws = [w for w in lab_ws if id(w) not in tot_ws and (not _HANGUL.search(w.t) or w.xc < mid)]
    pf_ws = [w for w in lab_ws if id(w) not in tot_ws and _HANGUL.search(w.t) and w.xc >= mid]
    # 포트폴리오: 라벨이 놓인 y 가 속한 그룹(행 y 구간 [y0,y1])에 귀속, 구간 밖이면 구간까지 거리가 가장 가까운 그룹.
    # 세로쓰기 라벨은 글자 순서로 표준 라벨 분절 -> 그룹 순서대로 귀속(_pf_stream_assign)
    buckets: dict[int, list[Wd]] = defaultdict(list)
    for w in pf_ws:
        gi = min(range(len(groups)), key=lambda i: (max(groups[i]["y0"] - w.yc, 0.0, w.yc - groups[i]["y1"]), abs(groups[i]["yc"] - w.yc)))
        buckets[gi].append(w)
    stream = _pf_stream_assign(groups, pf_ws, total_gs, block.get("spill_ws"))
    block["pf_spill"] = stream[1] if stream is not None else block.get("pf_spill_h", "")
    for gi, g in enumerate(groups):
        if gi in total_gs:
            continue
        if stream is not None:
            g["pf_raw"] = stream[0][gi]
        else:
            ws_ = sorted(buckets.get(gi, []), key=lambda w: (round(w.yc / 3), w.x0))
            g["pf_raw"] = "".join(w.t for w in ws_)
        g["pf"] = _pf_clean(g["pf_raw"])
        if g["pf"] is None:
            flags.append(f"no_pf_label@y{g['yc']:.0f}")
        elif not _PF_OK.match(g["pf"]):
            flags.append(f"pf_unknown:{g['pf']}")
    # 구분
    body = [g for i, g in enumerate(groups) if i not in total_gs]
    toks = _gubun_tokens(gub_ws)
    block["gub_toks"] = toks                  # relabel_gubun_joint 가 연도 블록 전체(여러 쪽)로 다시 배정할 때 쓴다
    block["gub_stream"] = _gub_stream(gub_ws)
    block["gub_chars"] = _gub_chars(gub_ws)
    if not body:
        return flags
    lead_name = state.get("last_gubun")
    best = None   # (cost, lead, edges)
    m = len(body)
    # 병합셀 라벨은 span 이 '시작하는 쪽'의 보이는 구간 중앙에 한 번만 찍힌다(이어지는 쪽에는 없음) ->
    # 라벨 없는 span 은 쪽 맨 앞의 이어짐(lead) 하나뿐이고, 이어짐이 아닌 모든 span 은 이 쪽에 라벨이 있다.
    for lead in (0, 1):
        n = len(toks) + lead
        if n < 1 or n > m:
            continue
        for cuts in (combinations(range(1, m), n - 1) if n > 1 else [()]):
            edges = (0, *cuts, m)
            cost = 1.5 * lead
            for j, tk in enumerate(toks):
                ty = tk[1]
                s_, e_ = edges[j + lead], edges[j + lead + 1]
                seg = body[s_:e_]
                cost += abs(ty - (seg[0]["y0"] + seg[-1]["y1"]) / 2)
            if best is None or cost < best[0]:
                best = (cost, lead, edges)
    if best is None:
        for g in body:
            g["gubun"] = None
        flags.append("no_gubun_label")
        return flags
    _, lead, edges = best
    names = ([lead_name] if lead else []) + [t[0] for t in toks]
    raws = ([state.get("last_gubun_raw")] if lead else []) + [t[2] for t in toks]
    if lead and not lead_name:
        flags.append("gubun_lead_unknown")
    for j, name in enumerate(names):
        for g in body[edges[j]:edges[j + 1]]:
            g["gubun"] = name
            g["gubun_raw"] = raws[j]
    state["last_gubun"] = body[-1].get("gubun") or state.get("last_gubun")
    state["last_gubun_raw"] = body[-1].get("gubun_raw") or state.get("last_gubun_raw")
    return flags


def block_rows(block: dict, meta_row: dict) -> tuple[list[dict], list[str]]:
    """블록 -> 셀 행(공통 키는 meta_row). 숫자 파싱 불가 칸은 bad 로 보고만 한다."""
    rows: list[dict] = []
    bad: list[tuple] = []
    for gi, g in enumerate(block["groups"]):
        for m in ("예상보험금", "위험보험료", "비율"):
            for _xc, col in block["cols"]:
                toks = g["cells"].get((m, col))
                if not toks:
                    continue
                toks = sorted(toks, key=lambda w: (round(w.yc / 2.0), w.x0))
                txt = "".join(w.t for w in toks)
                row = dict(meta_row)
                row.update({"기준연도": g.get("year", block["year"]), "구분": g.get("gubun"), "포트폴리오": g.get("pf"),
                            "구분_원문": g.get("gubun_raw"), "포트폴리오_원문": g.get("pf_raw"),
                            "경과기간": col, "지표": m, "단위": ("%" if m == "비율" else block["unit"] or "억원")})
                if block.get("segment"):
                    row["부문"] = block["segment"]
                if g.get("pf_fix"):
                    row["라벨보정"] = g["pf_fix"]
                if all(is_dash(w.t) for w in toks):
                    row.update({"값": None, "dash": True})
                else:
                    pn = parse_num(txt)
                    if pn is None:
                        txt2 = re.sub(r"(?<=\d)\.{2,}(?=\d)", ".", txt)      # 텍스트층 '94..9' (렌더 확인: 94.9)
                        pn = parse_num(txt2) if txt2 != txt else None
                        if pn is None:
                            bad.append((g.get("year", block["year"]), f"{g.get('gubun')}/{g.get('pf')}/{m}/{col}:{txt!r}"))
                            continue
                        row["텍스트층보정"] = f"{txt!r} -> {txt2!r}"
                    row.update({"값": fmt_num(pn[0]), "dash": False, "_dec": pn[1]})
                rows.append(row)
    return rows, bad


# ---------------------------------------------------------------------------------------------
# 표 B 구간(섹션) 드라이버 + 항등식 자기검증
# ---------------------------------------------------------------------------------------------
def _stop_y_of_next_section(ws: list[Wd]) -> float | None:
    """'③ 예정유지비 ...' 제목의 y. 그 아래는 다른 표라 읽지 않는다."""
    ys = [w.yc for w in ws if "예정유지비" in w.t and w.x0 < 200]
    return min(ys) if ys else None


def _attach_carry(prev: dict, nxt: dict) -> None:
    """다음 쪽 맨 위로 넘어온 숫자 조각을 앞 쪽 마지막 그룹의 마지막 지표 행 칸에 붙인다(y 는 쪽을 넘어 정렬되도록 1e4 가산)."""
    carry = nxt.get("carry") or []
    if not carry or not prev["groups"]:
        return
    g = prev["groups"][-1]
    ms = [m for m in _METRICS3 if m in g["rows"]]
    if not ms:
        return
    m_last = ms[-1]
    for w, col in carry:
        g["cells"][(m_last, col)].append(Wd(w.x0, w.y0 + 1e4, w.x1, w.y1 + 1e4, w.t))
    nxt["carry"] = []


_METRICS3 = ("예상보험금", "위험보험료", "비율")


def _attach_spill(prev: dict, nxt: dict) -> None:
    """다음 쪽 맨 위로 넘친 세로쓰기 라벨 글자를 앞 쪽 마지막 그룹의 라벨 뒤에 붙인다."""
    sp = nxt.get("pf_spill") or ""
    if not sp or not prev["groups"]:
        return
    g = prev["groups"][-1]
    if _PF_OK.match(canon_portfolio(g.get("pf_raw") or "")):      # 앞 쪽 마지막 라벨이 이미 완결이면 위쪽 조각은 이 그룹 라벨의 일부가 아니다
        return
    g["pf_raw"] = (g.get("pf_raw") or "") + sp
    g["pf"] = _pf_clean(g["pf_raw"])
    prev["flags"] = [f for f in prev["flags"] if not f.startswith(("pf_unknown", "no_pf_label"))]
    if g["pf"] and not _PF_OK.match(g["pf"]):
        prev["flags"].append(f"pf_unknown:{g['pf']}")
    nxt["pf_spill"] = ""


def _merge_split_group(prev: dict, nxt: dict) -> bool:
    """쪽 경계에서 갈라진 그룹(앞 쪽 마지막 그룹 = 앞 지표 행, 뒤 쪽 첫 그룹 = 나머지 행)을 앞 블록으로 합친다."""
    if not prev["groups"] or not nxt["groups"]:
        return False
    pg, ng = prev["groups"][-1], nxt["groups"][0]
    kp, kn = [m for m in _METRICS3 if m in pg["rows"]], [m for m in _METRICS3 if m in ng["rows"]]
    if not kp or not kn or len(kp) + len(kn) != 3 or kp != list(_METRICS3[:len(kp)]) or kn != list(_METRICS3[len(kp):]):
        return False
    pg["rows"].update(ng["rows"])
    for k, v in ng["cells"].items():
        pg["cells"][k].extend(v)
    raw = (pg.get("pf_raw") or "") + (ng.get("pf_raw") or "")
    if pg.get("pf") == "합계" or ng.get("pf") == "합계" or nz(raw) == "합계":
        pg["gubun"], pg["pf"] = "합계", "합계"
    elif raw:
        pg["pf_raw"] = raw
        pg["pf"] = _pf_clean(raw)
    pg["y1"] = max(pg["y1"], ng["y1"])
    pg["gubun"] = pg.get("gubun") or ng.get("gubun")
    # 합쳐진 그룹에 대한 구분/포트폴리오 알림 플래그는 이제 무의미 -> 제거
    prev["flags"] = [f for f in prev["flags"] if not f.startswith(("pf_unknown", "no_pf_label"))]
    nxt["flags"] = [f for f in nxt["flags"] if not f.startswith(("pf_unknown", "no_pf_label", "no_A_row"))]
    if pg["pf"] and not _PF_OK.match(pg["pf"]):
        prev["flags"].append(f"pf_unknown:{pg['pf']}")
    nxt["groups"].pop(0)
    return True



def relabel_gubun_joint(blocks: list[dict]) -> None:
    """쪽을 가로질러 구분(Non-Par/Indirect-Par/Direct-Par) span 을 다시 정한다. 표 = 합계 그룹으로 시작하는 연속 그룹열.
    한 표 안에서 포트폴리오 순서(상해<질병<재물<사망<건강<연금저축<자산연계형<기타, 유<무<변)가 되돌아가면 새 구분.
    구분 이름은 표에 속한 블록들의 라벨 토큰 순서(연속 중복은 하나로). span 수 == 이름 수일 때만 덮어쓴다 - 쪽마다 라벨 위치가 달라
    쪽 단위 분할(assign_labels)이 틀리는 표를 구조(순서 되돌림)로 바로잡는다."""
    tables: list[dict] = []
    cur = None
    for b in blocks:
        for g in b["groups"]:
            if g.get("pf") == "합계" or cur is None:
                cur = {"groups": [], "blocks": [], "bg": {}}
                tables.append(cur)
            if not cur["blocks"] or cur["blocks"][-1] is not b:
                cur["blocks"].append(b)
            cur["bg"].setdefault(id(b), []).append(g)
            if g.get("pf") != "합계":
                cur["groups"].append(g)
    ntab_in_block: Counter = Counter(id(b) for t in tables for b in t["blocks"])
    for t in tables:
        gs = t["groups"]
        if not gs:
            continue
        spans: list[list[dict]] = [[gs[0]]]
        seen = {gs[0].get("pf")} - {None}
        prev = _pf_order(gs[0].get("pf"))
        for g in gs[1:]:
            pf = g.get("pf")
            o = _pf_order(pf)
            new = o is not None and prev is not None and o < prev      # 같은 순서(=같은 라벨 중복)는 원문 오기일 수 있어 새 구분으로 보지 않는다
            if new:
                spans.append([g])
                seen = {pf} - {None}
            else:
                spans[-1].append(g)
                if pf:
                    seen.add(pf)
            if o is not None:
                prev = o
        names: list[tuple[str, str]] = []
        parts = []
        for b in t["blocks"]:
            if ntab_in_block[id(b)] > 1 and b.get("gub_chars"):      # 한 블록에 표가 둘 이상이면 이 표 그룹들의 세로 범위 안 글자만(다른 표의 라벨을 가져오지 않도록)
                gl = t["bg"][id(b)]
                y_lo, y_hi = min(g["y0"] for g in gl) - 10.0, max(g["y1"] for g in gl) + 10.0
                parts.append("".join(c for c, y in b["gub_chars"] if y_lo <= y <= y_hi))
            else:
                parts.append(b.get("gub_stream") or "")
        stream = "".join(parts)      # 쪽 경계에서 갈라진 라벨('Indir'|'ect-Par')은 이어 붙인 문자열에서 찾는다
        for m in _GB_RE.finditer(stream):
            nm = canon_gubun(m.group(0))
            if nm == "합계":
                continue
            if not names or names[-1][0] != nm:
                names.append((nm, m.group(0)))
        if names and len(names) == len(spans):
            for sp, (nm, raw) in zip(spans, names):
                for g in sp:
                    g["gubun"], g["gubun_raw"] = nm, raw
        elif names or len(spans) > 1:
            t["blocks"][0]["flags"].append(f"gubun_joint_mismatch:spans={len(spans)},names={len(names)}")
        # 같은 구분 안에서 '유배당X' 가 두 번 인쇄되고 '무배당X' 가 없으면 원문 오기 -> 순서상 둘째를 '무배당X' 로(원문 라벨은 그대로 보관, 라벨보정 표시)
        for sp in spans:
            seen_pf: set = set()
            for g in sp:
                pf = g.get("pf")
                if pf and pf in seen_pf and pf.startswith("유배당"):
                    alt = "무배당" + pf[3:]
                    if not any(x.get("pf") == alt for x in sp):
                        g["pf_fix"] = f"원문 라벨 '{pf}' 가 같은 구분에 두 번 인쇄 -> 순서상 둘째를 '{alt}' 로 보정"
                        g["pf"] = alt
                        pf = alt
                if pf:
                    seen_pf.add(pf)


def assign_table_years(blocks: list[dict]) -> None:
    """캡션에 연도가 하나도 없고 '당기'·'전기' 표지(왼쪽 열)만 있는 구간: 표(합계 그룹으로 시작하는 연속 그룹열)를 읽는 순서대로 표지와 짝지어
    그룹에 year(-1 당기 / -2 전기)를 단다. 표 수와 표지 수가 다르면 건드리지 않는다(연도 미상으로 남는다)."""
    if any(b["year"] is not None for b in blocks):
        return
    tables: list[list[dict]] = []
    cur = None
    for b in blocks:
        for g in b["groups"]:
            if g.get("pf") == "합계" or cur is None:
                cur = []
                tables.append(cur)
            cur.append(g)
    marks = [m for b in blocks for m in b.get("period_marks", [])]
    if not marks or len(marks) != len(tables):
        return
    for tb, (_y, txt) in zip(tables, marks):
        for g in tb:
            g["year"] = -1 if txt.startswith("당기") else -2


def extract_B_sections(doc, cand_pages: list[int]) -> list[dict]:
    """cand_pages(오름차순)에서 표 B 구간들을 찾는다. 각 구간 = 연속 쪽, 블록 목록."""
    sections: list[dict] = []
    covered: set[int] = set()
    npages = doc.page_count
    for s in sorted(set(cand_pages)):
        if s in covered or s > npages:
            continue
        state: dict = {}
        pages: list[int] = []
        blocks: list[dict] = []
        p = s
        miss = 0
        while p <= npages:
            ws = get_words(doc[p - 1])
            y_stop = _stop_y_of_next_section(ws)
            bl = parse_B_page(ws, state, y_stop, get_hsegs(doc[p - 1]))
            if not bl:
                miss += 1
                if pages or miss > 1:
                    break
                p += 1
                continue
            for b in bl:
                b["page"] = p
                b["flags"] = b["flags"] + assign_labels(b, state)
            if blocks and bl:
                _attach_carry(blocks[-1], bl[0])
                _attach_spill(blocks[-1], bl[0])
                _merge_split_group(blocks[-1], bl[0])
            pages.append(p)
            blocks.extend(bl)
            if y_stop is not None:
                p += 1
                break
            p += 1
        if blocks:
            relabel_gubun_joint(blocks)
            assign_table_years(blocks)
            sections.append({"pages": pages, "blocks": blocks})
            covered.update(range(s, p + 1))
    return sections


def _u(dec: int) -> float:
    return 0.5 * 10 ** (-dec)


def check_B_rows(rows: list[dict], errata: dict | None = None) -> dict:
    """비율 ≈ A/B x 100 (원문 반올림 구간 검사), 합계 = Σ 포트폴리오. rows 는 한 (회사, 공시) 의 표 B 셀들.
    errata = {(구분, 포트폴리오, 경과기간, 지표): 근거} - 원문 인쇄 오기로 등재된 칸. 그 칸이 걸린 비율·합계 검산은 건너뛰고(ratio_errata/total_errata) 행에 '원문오기' 를 단다."""
    errata = errata or {}          # {(부문, 구분, 포트폴리오, 경과기간, 지표): 근거}
    cell: dict[tuple, dict] = {}
    for r in rows:
        key = (r["기준연도"], r.get("부문"), r["구분"], r["포트폴리오"], r["경과기간"])
        cell.setdefault(key, {})[r["지표"]] = r
    stats = {"ratio_checked": 0, "ratio_fail": 0, "ratio_trivial": 0, "ratio_skip": 0, "ratio_errata": 0, "total_errata": 0,
             "total_checked": 0, "total_fail": 0, "fails": [], "errata_hit": [], "errata_unmatched": []}
    if errata:
        hit: set = set()
        for r in rows:
            ek = (r.get("부문") or "", r["구분"], r["포트폴리오"], r["경과기간"], r["지표"])
            if ek in errata:
                r["원문오기"] = errata[ek]
                hit.add(ek)
        stats["errata_hit"] = sorted(hit)
        stats["errata_unmatched"] = sorted(set(errata) - hit)
    # 구조 검사: 같은 칸 중복(라벨 오귀속) · 열 누락(머리말 못 읽음) · 비표준 구분/포트폴리오 라벨
    cnt = Counter((r["기준연도"], r.get("부문"), r["구분"], r["포트폴리오"], r["경과기간"], r["지표"]) for r in rows)
    stats["dup_keys"] = sum(1 for n in cnt.values() if n > 1)
    cols_seen = {r["경과기간"] for r in rows}
    # 1~10년 을 한 열로 묶어 인쇄한 표(미래에셋생명 감사보고서 사본)는 7열이 정상 - 인쇄 그대로 둔다(쪼개거나 안분하지 않음)
    exp_cols = AGG_PERIOD_ORDER if ("1~10년" in cols_seen and not (cols_seen & set(PERIOD_ORDER[:10]))) else PERIOD_ORDER
    stats["missing_cols"] = [c for c in exp_cols if c not in cols_seen] if rows else []
    stats["nonstd"] = sorted({f"{r['구분']}|{r['포트폴리오']}" for r in rows
                              if r["구분"] not in STD_GUBUN or not (r["포트폴리오"] and _PF_OK.match(r["포트폴리오"]))})
    if stats["missing_cols"]:
        stats["fails"].append(f"열 누락 {','.join(stats['missing_cols'])}")
    if stats["dup_keys"]:
        stats["fails"].append(f"같은 칸 중복 {stats['dup_keys']}건(구분·포트폴리오 오귀속)")
    if stats["nonstd"]:
        stats["fails"].append(f"비표준 라벨 {len(stats['nonstd'])}종 {stats['nonstd'][:4]}")
    # 비율
    for key, d in cell.items():
        a, b, q = d.get("예상보험금"), d.get("위험보험료"), d.get("비율")
        if q is None or q["값"] is None:
            continue
        if a is None or b is None or a["값"] is None or b["값"] is None:
            if q["값"] == 0 and (a is not None and a["dash"] or b is not None and b["dash"]):
                stats["ratio_trivial"] += 1
            else:
                stats["ratio_skip"] += 1
            continue
        if errata and any((key[1] or "", key[2], key[3], key[4], mm) in errata for mm in ("예상보험금", "위험보험료", "비율")):
            stats["ratio_errata"] += 1
            continue
        uA, uB, uR = _u(a["_dec"]), _u(b["_dec"]), _u(q["_dec"])
        if b["값"] - uB <= 0:       # 분모 구간이 0 을 지난다(반올림으로 0 인쇄) -> 비율은 정의되지 않음, 검산 불가
            stats["ratio_trivial"] += 1
            continue
        cors = [(a["값"] + sa * uA) / (b["값"] + sb * uB) * 100 for sa in (-1, 1) for sb in (-1, 1)]
        lo, hi = min(cors) - uR, max(cors) + uR
        stats["ratio_checked"] += 1
        ok = lo <= q["값"] <= hi
        q["_ratio_ok"] = ok
        if not ok:
            stats["ratio_fail"] += 1
            if len(stats["fails"]) < 12:
                exp = (a["값"] / b["값"] * 100) if b["값"] else float("nan")
                stats["fails"].append(f"ratio {key} A={a['값']} B={b['값']} R={q['값']} (expect {exp:.2f})")
    # 합계 = Σ 포트폴리오
    by_col: dict[tuple, dict] = defaultdict(lambda: {"tot": None, "parts": []})
    for key, d in cell.items():
        yr, seg, gb, pf, col = key
        for m in ("예상보험금", "위험보험료"):
            r = d.get(m)
            if r is None:
                continue
            slot = by_col[(yr, seg, col, m)]
            if gb == "합계":
                slot["tot"] = r
            else:
                slot["parts"].append(r)
    for (yr, seg, col, m), slot in by_col.items():
        t = slot["tot"]
        if t is None or t["값"] is None:
            continue
        vals = [r for r in slot["parts"] if r["값"] is not None]
        if not vals:
            continue
        if errata and any((r.get("부문") or "", r["구분"], r["포트폴리오"], r["경과기간"], r["지표"]) in errata for r in [t] + slot["parts"]):
            stats["total_errata"] += 1
            continue
        s = sum(r["값"] for r in vals)
        dmin = min([t["_dec"]] + [r["_dec"] for r in vals])
        tol = (len(vals) + 1) * _u(dmin) + 1e-9
        stats["total_checked"] += 1
        if abs(s - t["값"]) > tol:
            stats["total_fail"] += 1
            if len(stats["fails"]) < 12:
                stats["fails"].append(f"total {(yr, seg, col, m)} sum={s:.4g} printed={t['값']} tol={tol:.3g}")
    return stats


# ---------------------------------------------------------------------------------------------
# 표 A 쪽 파서 - ① 본문(행 = 연도, 열 = 예상·실제·예실차)  ② 전치(행 = 지표, 열 = 연도: 신한라이프 본문·흥국화재 사본)
#               ③ 감사보고서 주석 사본(당기/전기 맥락 줄 + 값만 있는 줄, 한 줄에 당·전기 6칸인 사본 포함)
# ---------------------------------------------------------------------------------------------
_C_NOTE = re.compile(r"주\d+\)|\(\*\d+\)|\*\d+")
_A_MARK = re.compile(r"예상손해율|실제손해율|예실차")
_A_HEAD_SKIP = re.compile(r"^(?:주\d*\)|\(주|\(\*|\*|※|\(\d+\)|\d+\))")
_A_ROW_LABELS = (
    re.compile(r"^(20\d\d)년도?"),
    re.compile(r"^(당기말|전기말|당기|전기)"),
    re.compile(r"^제\d+\((당|전)\)기"),
)
_A_METRIC = (("예상손해율", re.compile(r"^예상손해율")), ("실제손해율", re.compile(r"^실제손해율")),
             ("예실차비율", re.compile(r"^(?:보험금)?예실차")))


def _peel_label(ln: list[Wd], pats) -> tuple[re.Match | None, int]:
    """줄 맨 앞 라벨(공백 제거 기준)이 pats 중 하나와 맞으면 (match, 소비한 토큰 수)."""
    tz = [nz(w.t) for w in ln]
    full = "".join(tz)
    for pat in pats:
        m = pat.match(full)
        if not m:
            continue
        need, acc, k = len(m.group(0)), 0, 0
        while k < len(tz) and acc < need:
            acc += len(tz[k])
            k += 1
        if acc >= need:
            return m, k
    return None, 0


def _values_of(toks: list[Wd]):
    """토큰 -> [(값|None, 소수자리, 대시여부, 원문)]. 숫자·대시 외 토큰이 있으면 None."""
    out = []
    for w in toks:
        t = w.t
        if is_dash(t):
            out.append((None, 0, True, t))
            continue
        pn = parse_num(t)
        if pn is None:
            return None
        out.append((pn[0], pn[1], False, t))
    return out


def _year_of_label(label: str, year_cur: int) -> int | None:
    m = re.match(r"^(20\d\d)", label)
    if m:
        return int(m.group(1))
    if label.startswith("당") or "(당)" in label:
        return year_cur
    if label.startswith("전") or "(전)" in label:
        return year_cur - 1
    return None


def _a_row(year: int | None, vals, text: str, flags: list[str]) -> dict:
    a, b, c = vals
    return {"기준연도": year, "예상손해율": a[0], "실제손해율": b[0], "예실차비율": c[0],
            "_dec": min(v[1] for v in vals if not v[2]) if any(not v[2] for v in vals) else 0,
            "_dash": [v[2] for v in vals], "원문": text, "_flags": flags}


def parse_A_page(ws: list[Wd], year_cur: int) -> list[dict]:
    lines = group_lines(ws)
    texts = [nz(line_text(l)) for l in lines]
    ys = [sum(w.yc for w in l) / len(l) for l in lines]
    anchors = [i for i, t in enumerate(texts) if _A_MARK.search(t) and len(t) < 140 and not _A_HEAD_SKIP.match(t)]
    if not anchors:
        return []
    # 앵커 군집(머리말이 2~3줄에 걸친다) - 군집 안 줄 사이 간격 70pt 이내
    clusters: list[list[int]] = []
    for i in anchors:
        if clusters and ys[i] - ys[clusters[-1][-1]] <= 70:
            clusters[-1].append(i)
        else:
            clusters.append([i])
    rows: list[dict] = []
    for ci, cl in enumerate(clusters):
        i0, i1 = cl[0], cl[-1]
        y_next = ys[clusters[ci + 1][0]] if ci + 1 < len(clusters) else 1e9
        # ---------- 전치: 지표 라벨로 시작하는 줄이 2개 이상 + 숫자
        metric_rows: dict[str, tuple[int, list]] = {}
        for i in range(i0, min(i1 + 6, len(lines))):
            if ys[i] >= y_next:
                break
            m, k = _peel_label(lines[i], [p for _, p in _A_METRIC])
            if not m:
                continue
            name = next(n for n, p in _A_METRIC if p.match(texts[i]))
            vals = _values_of(lines[i][k:]) if k < len(lines[i]) else None
            if vals is None:
                # 라벨 뒤에 '(A)' '(주2)' '(*1)' 같은 꼬리 토큰이 붙은 경우: 값 구간만 오른쪽에서 뽑는다
                tail = []
                for w in reversed(lines[i]):
                    if is_dash(w.t) or parse_num(w.t) is not None:
                        tail.append(w)
                    else:
                        break
                tail.reverse()
                vals = _values_of(tail) if tail else None
            if vals:
                metric_rows[name] = (i, vals)
        if len(metric_rows) >= 2:
            hdr_years = []
            for i in range(max(0, i0 - 3), i1 + 1):
                if ys[i0] - ys[i] > 45:
                    continue
                for w in lines[i]:
                    tt = _C_NOTE.sub("", nz(w.t))
                    yy = _year_of_label(tt, year_cur) if re.fullmatch(r"20\d\d년도?|제\d+\((?:당|전)\)기|당기말?|전기말?", tt) else None
                    if yy is not None:
                        hdr_years.append((w.xc, yy))
            hdr_years = sorted(set(hdr_years))
            ncol = min(len(v) for _, v in metric_rows.values())
            if hdr_years and len(hdr_years) >= ncol and ncol >= 1 and {"예상손해율", "실제손해율", "예실차비율"} <= set(metric_rows):
                yrs = [y for _, y in hdr_years][:ncol] if len(hdr_years) == ncol else [y for _, y in hdr_years]
                if len(yrs) == ncol:
                    for j, yy in enumerate(yrs):
                        trip = [metric_rows[n][1][j] for n in ("예상손해율", "실제손해율", "예실차비율")]
                        rows.append(_a_row(yy, trip, " | ".join(t[3] for t in trip), ["transposed"]))
                    continue
        # ---------- 행 = 연도/당기·전기 라벨 줄, 또는 값만 있는 줄
        found_here = 0
        for i in range(i1 + 1, min(i1 + 12, len(lines))):
            if ys[i] >= y_next - 1 or ys[i] - ys[i1] > 170:
                break
            if _A_HEAD_SKIP.match(texts[i]) and not _A_ROW_LABELS[1].match(texts[i]):
                if found_here:
                    break
                continue
            m, k = _peel_label(lines[i], list(_A_ROW_LABELS))
            label = m.group(0) if m else ""
            vals = _values_of(lines[i][k:])
            if not vals:
                continue
            if len(vals) == 6 and not m:       # 한 줄에 당기·전기 두 묶음(아이엠라이프 사본)
                yrs = [year_cur, year_cur - 1]
                for jj in (0, 1):
                    rows.append(_a_row(yrs[jj], vals[jj * 3:(jj + 1) * 3], " | ".join(t[3] for t in vals[jj * 3:(jj + 1) * 3]), ["two_periods_in_row"]))
                found_here += 2
                continue
            if len(vals) != 3:
                continue
            flags: list[str] = []
            yr = _year_of_label(label, year_cur) if m else None
            if yr is None:
                # 라벨 없는 줄(사본): 머리말 위 90pt 안의 연도 캡션('<2024 년>', '(2024년)') -> 없으면 '당기/전기' 맥락 줄
                ctx = None
                for j in range(i1, -1, -1):
                    if ys[i0] - ys[j] > 90:
                        break
                    mm = re.search(r"[<(]\s*(20\d\d)\s*년도?\s*[>)]", texts[j])
                    if mm:
                        yr = int(mm.group(1))
                        flags.append("year_from_caption")
                        break
                for j in range(i0 - 1, -1, -1):
                    if ys[i0] - ys[j] > 90:
                        break
                    mm = re.search(r"(당기말|전기말|당기|전기|\(당\)기|\(전\)기)", texts[j])
                    if mm and not re.search(r"당기말?및전기말?", texts[j]):
                        ctx = mm.group(1)
                        break
                if ctx is None and yr is None:
                    # 머리말 사이 줄에서도 찾는다(예: '<당기말>' 이 머리말 바로 위가 아닌 경우)
                    for j in range(i0, i1 + 1):
                        mm = re.search(r"(당기말|전기말|당기|전기|\(당\)기|\(전\)기)", texts[j])
                        if mm:
                            ctx = mm.group(1)
                            break
                if yr is not None:
                    pass
                elif ctx is not None:
                    yr = year_cur if (ctx.startswith("당") or ctx == "(당)기") else year_cur - 1
                    flags.append("year_from_context")
                else:
                    flags.append("no_year_label")
            rows.append(_a_row(yr, vals, " | ".join(t[3] for t in vals), flags))
            found_here += 1
    return rows


def check_A_row(r: dict) -> dict:
    a, b, c = r["예상손해율"], r["실제손해율"], r["예실차비율"]
    if a is None or b is None or c is None:
        return {"computed": None, "diff": None, "ok": None, "tol": None}
    comp = a - b
    tol = max(0.02, 1.5 * 10 ** (-r["_dec"]) + 1e-9)
    return {"computed": round(comp, 6), "diff": round(c - comp, 6), "ok": abs(c - comp) <= tol, "tol": round(tol, 6)}


# ---------------------------------------------------------------------------------------------
# 표 C 쪽 파서 (손보 합산비율 표)
#   행: [종목] [지표] 값... / 열: 연도 라벨 + 분기·누계 부라벨 (머리말 1~3줄). 열 -> 연도 귀속은 '연도 라벨 중심 = 그 묶음 열들의 중심' 이 되는 연속 분할.

# ---------------------------------------------------------------------------------------------
# 표 C 파서 (손보 합산비율 표)
#   행: [종목] [지표] 값... / 열: 연도 라벨 + 분기·누계 부라벨(머리말 1~3줄).
#   열 라벨 배정: ① 부라벨(1분기·누계 ...)·연도+부라벨 칸은 가장 가까운 열에(머리말은 가운데 정렬, 숫자는 오른쪽 정렬이라 중앙값 편차 δ 를 보정)
#                ② 남은 열 중 연도 라벨과 맞닿은 열 = 그 연도의 열 ③ 맞닿지 않은 연도 라벨 = 묶음 머리글 -> 부라벨 열들을 연속 분할로 귀속.
# ---------------------------------------------------------------------------------------------
_C_YEAR = re.compile(r"^(?:FY)?['’]?(20\d\d)(?:년도?)?$")
_C_YEAR2 = re.compile(r"^FY['’]?(\d\d)$|^(\d\d)년도?$")
_C_SUBTXT = r"(?:[1-4]분기)?(?:\(?\d{1,2}월\)?)?(?:누계|누적|상반기|하반기|반기|연간계|연간|전체|계)?"
_C_YSUB_A = re.compile(r"^(20\d\d)\.?([1-4])(?:Q|분기)$")
_C_YSUB_B = re.compile(r"^(\d\d)\.([1-4])Q$")
_C_YSUB_C = re.compile(r"^(20\d\d)(?:년도?)?\(?(" + _C_SUBTXT + r")\)?$")
_C_SUB = re.compile(r"^\(?(" + _C_SUBTXT + r")\)?$")


def _norm_sub(s: str) -> str:
    return s.replace("사분기", "분기").strip("()")


def classify_hdr(text: str, year_cur: int):
    """('year', Y) | ('ysub', Y, sub) | ('sub', sub) | None. 공백·주석 제거 후 판정."""
    t = _C_NOTE.sub("", nz(text))
    if not t:
        return None
    m = _C_YEAR.match(t)
    if m:
        return ("year", int(m.group(1)))
    m = _C_YEAR2.match(t)
    if m:
        return ("year", 2000 + int(m.group(1) or m.group(2)))
    m = _C_YSUB_A.match(t)
    if m:
        return ("ysub", int(m.group(1)), f"{m.group(2)}분기")
    m = _C_YSUB_B.match(t)
    if m:
        return ("ysub", 2000 + int(m.group(1)), f"{m.group(2)}분기")
    t2 = _norm_sub(t)
    m = _C_YSUB_C.match(t2)
    if m and m.group(2):
        return ("ysub", int(m.group(1)), _norm_sub(m.group(2)))
    m = _C_SUB.match(t2)
    if m and m.group(1) and not re.fullmatch(r"\d+", m.group(1)):
        return ("sub", _norm_sub(m.group(1)))
    return None


_HDR_LABEL_WORDS = {"구분", "구", "분", "보종", "종목", "구분(주1)"}


def _header_cells(ln: list[Wd], year_cur: int, gap: float = 14.0):
    """한 줄의 토큰을 왼쪽부터 '분류 가능한 가장 긴 연속 병합'으로 칸 라벨로 만든다('2024'+'년'+'6월'+'누계', '1'+'분기', '2024'+'1Q').
    인접한 '1분기주2)' '2분기주2)' 처럼 합치면 분류가 안 되는 경우는 낱개로 남는다.
    반환 (칸 목록, 칸이 된 토큰 수, 라벨어('구분' 등)를 뺀 전체 토큰 수)."""
    toks = sorted((w for w in ln if nz(w.t) not in _HDR_LABEL_WORDS), key=lambda w: w.x0)
    out: list[tuple[Wd, tuple]] = []
    used = 0
    i = 0
    while i < len(toks):
        best = None
        for j in range(min(len(toks), i + 5), i, -1):
            if any(toks[k + 1].x0 - toks[k].x1 > gap for k in range(i, j - 1)):
                continue
            txt = "".join(t.t for t in toks[i:j])
            pieces = _split_multi_year(Wd(toks[i].x0, toks[i].y0, toks[j - 1].x1, toks[j - 1].y1, txt))
            typed = [(pc, classify_hdr(pc.t, year_cur)) for pc in pieces]
            if all(t for _, t in typed):
                best = (j, typed)
                break
        if best:
            out += best[1]
            used += best[0] - i
            i = best[0]
        else:
            i += 1
    return out, used, len(toks)


def _split_multi_year(c: Wd) -> list[Wd]:
    """'2022년2021년' 처럼 붙어 추출된 연도 라벨을 둘로 가른다(글자 비율로 x 배분)."""
    ms = list(re.finditer(r"20\d\d\s*년도?", c.t))
    if len(ms) < 2:
        return [c]
    L = len(c.t)
    out = []
    for m in ms:
        a, b = m.start() / L, m.end() / L
        out.append(Wd(c.x0 + (c.x1 - c.x0) * a, c.y0, c.x0 + (c.x1 - c.x0) * b, c.y1, m.group(0)))
    return out


def _c_data_line(ln: list[Wd], relaxed: bool = False):
    """C 데이터 줄 -> (라벨 토큰, 값 목록, 값 토큰). 값 = 소수점·% 가 있는 숫자 1개 이상 + 대시. 문장·쪽번호·큰 정수는 제외."""
    k = 0
    while k < len(ln) and not (is_dash(ln[k].t) or parse_num(ln[k].t) is not None):
        k += 1
    if k >= len(ln):
        return None
    vals = _values_of(ln[k:])
    if not vals:
        return None
    real_ratio = sum(1 for v in vals if (not v[2]) and ("." in v[3] or "%" in v[3]))
    if relaxed:      # 카카오페이류: 정수만 인쇄(%·소수점 없음). 호출 쪽이 캡션·머리말 라벨을 이미 확인한 표에서만 쓴다
        if len(vals) < 3 or sum(1 for v in vals if not v[2]) < 3 or any((not v[2]) and (abs(v[0]) > 1e7 or v[0] < 0) for v in vals):
            return None
    else:
        if real_ratio < 1:
            return None
        if any((not v[2]) and abs(v[0]) > 1e6 for v in vals):
            return None
        if any("," in v[3] and "%" not in v[3] for v in vals):
            return None
        if any((not v[2]) and "." not in v[3] and "%" not in v[3] for v in vals) and sum(1 for v in vals if not v[2]) > real_ratio + 1:
            return None
    label = ln[:k]
    if len(nz("".join(w.t for w in label))) > 14:
        return None
    return label, vals, ln[k:]


def _partition_groups(xs: list[float], head_x: list[float]) -> tuple[int, ...] | None:
    """xs(열 보정 중심, 오름차순)를 머리글 개수만큼 연속 분할 -> 각 묶음 시작 인덱스. 비용 = Σ|묶음 중심 - 머리글 중심|."""
    from itertools import combinations
    n, k = len(xs), len(head_x)
    if k < 1 or n < k:
        return None
    best = None
    for cuts in combinations(range(1, n), k - 1):
        edges = (0, *cuts, n)
        cost = sum(abs((xs[edges[j]] + xs[edges[j + 1] - 1]) / 2 - head_x[j]) for j in range(k))
        if best is None or cost < best[0]:
            best = (cost, edges)
    return best[1] if best else None


def assign_col_labels(col_x: list[float], cells: list[tuple[Wd, tuple]], year_cur: int):
    n = len(col_x)
    flags: list[str] = []
    pitch = min([b - a for a, b in zip(col_x, col_x[1:])] or [60.0])
    sub_like = [c for c in cells if c[1][0] in ("sub", "ysub")]
    ycells = [c for c in cells if c[1][0] == "year"]
    ref = sub_like or ycells
    diffs = []
    for c, _ in ref:
        j = min(range(n), key=lambda i: abs(col_x[i] - c.xc))
        if abs(col_x[j] - c.xc) <= 0.8 * pitch:
            diffs.append(col_x[j] - c.xc)
    delta = sorted(diffs)[len(diffs) // 2] if diffs else 0.0
    delta = max(-10.0, min(delta, 40.0))
    lx = [x - delta for x in col_x]
    labels: list[dict | None] = [None] * n
    # ① 부라벨/연도+부라벨 -> 열
    cand = sorted((abs(lx[j] - c.xc), ci, j) for ci, (c, _) in enumerate(sub_like) for j in range(n) if abs(lx[j] - c.xc) <= 0.55 * pitch)
    used_c: set[int] = set()
    used_j: set[int] = set()
    for _d, ci, j in cand:
        if ci in used_c or j in used_j:
            continue
        used_c.add(ci)
        used_j.add(j)
        c, t = sub_like[ci]
        labels[j] = {"연도": None, "sub": t[1], "원문": c.t} if t[0] == "sub" else {"연도": t[1], "sub": t[2], "원문": c.t}
    if len(used_c) < len(sub_like):
        flags.append("c_unmatched_sub_label")
    # ② 연도 라벨이 맞닿은(미라벨) 열 = 연도 열
    candy = sorted((abs(lx[j] - c.xc), yi, j) for yi, (c, _) in enumerate(ycells) for j in range(n)
                   if labels[j] is None and abs(lx[j] - c.xc) <= 0.4 * pitch)
    used_y: set[int] = set()
    for _d, yi, j in candy:
        if yi in used_y or labels[j] is not None:
            continue
        used_y.add(yi)
        c, t = ycells[yi]
        labels[j] = {"연도": t[1], "sub": None, "원문": c.t}
    heads = sorted((ycells[yi] for yi in range(len(ycells)) if yi not in used_y), key=lambda t: t[0].xc)
    # ③ 묶음 머리글 -> 남은 열(부라벨만 있거나 미라벨)을 연속 분할로 귀속
    gb = [j for j in range(n) if labels[j] is None or labels[j]["연도"] is None]
    if gb:
        if not heads:
            for j in gb:
                if labels[j] is None:
                    flags.append("c_unlabeled_columns")
                else:
                    labels[j]["연도"] = year_cur
                    flags.append("year_from_disclosure")
        elif len(gb) < len(heads):
            flags.append("c_more_headers_than_columns")
        else:
            edges = _partition_groups([lx[j] for j in gb], [h[0].xc for h in heads])
            if edges is None:
                flags.append("c_partition_fail")
            else:
                for gi, (hc, ht) in enumerate(heads):
                    cols = gb[edges[gi]:edges[gi + 1]]
                    unl = [j for j in cols if labels[j] is None]
                    for j in cols:
                        if labels[j] is not None:
                            labels[j]["연도"] = ht[1]
                    if len(unl) == 1:
                        labels[unl[0]] = {"연도": ht[1], "sub": None, "원문": hc.t}
                    elif len(unl) > 1:
                        flags.append("c_ambiguous_unlabeled_cols")
    if any(l is None for l in labels):
        flags.append("c_unlabeled_columns")
    return labels, sorted(set(flags))


def parse_C_page(ws: list[Wd], year_cur: int, relaxed: bool = False) -> list[dict]:
    """페이지에서 합산비율 표(들)를 찾아 셀 행으로. 행 키: 종목·지표·_lab(열 라벨)·값·dash·_dec·_flags·_ncol·_ci.
    strict 로 표가 안 잡히면 호출 쪽이 relaxed=True 로 한 번 더 부른다(정수만 인쇄하는 표)."""
    lines = group_lines(ws)
    ys = [sum(w.yc for w in l) / len(l) for l in lines]
    texts = [nz(line_text(l)) for l in lines]
    data = [(i, _c_data_line(l, relaxed)) for i, l in enumerate(lines)]
    data = [(i, d) for i, d in data if d]
    groups: list[list[tuple[int, tuple]]] = []
    for i, d in data:
        if groups and ys[i] - ys[groups[-1][-1][0]] <= 60 and not any(
                texts[j].startswith(("주", "※", "(주")) for j in range(groups[-1][-1][0] + 1, i)):
            groups[-1].append((i, d))
        else:
            groups.append([(i, d)])
    out: list[dict] = []
    for g in groups:
        i_first = g[0][0]
        has_metric_lbl = any(re.sub(r"\(.*?\)", "", nz("".join(w.t for w in d[0]))).endswith(("손해율", "사업비율", "합산비율")) for _, d in g)
        cap = any("합산비율" in texts[j] for j in range(max(0, i_first - 14), i_first + 1) if ys[i_first] - ys[j] <= 280)
        if not (has_metric_lbl or cap):
            continue
        # 머리말 대역: 첫 데이터 줄 위로 95pt, 단위/캡션 줄에서 멈춤
        cells: list[tuple[Wd, tuple]] = []
        for j in range(i_first - 1, -1, -1):
            if ys[i_first] - ys[j] > 95:
                break
            if texts[j].startswith("(단위") or re.match(r"^\[|^[-ㆍ·∘o]?\s*합산|합산비율(?:시계열)?(?:현황|추이)?$", texts[j]):
                break
            lc, used, tot = _header_cells(lines[j], year_cur)
            if tot == 0:                     # '구 분' 만 있는 줄 - 건너뜀
                continue
            if not lc or used / tot < 0.5:  # 서술문 등 - 머리말 대역 끝
                break
            cells += lc
        if relaxed and (not cap or len(cells) < 2):
            continue
        ref = max(g, key=lambda t: len(t[1][2]))[1][2]
        col_x = sorted(w.xc for w in ref)
        ncol = len(col_x)
        pitch = min([b - a for a, b in zip(col_x, col_x[1:])] or [40.0])
        labels, flags = assign_col_labels(col_x, cells, year_cur)
        # ----- 행 -> (종목, 지표)
        rows_info = []
        for i, d in g:
            lab_toks, vals, vt = d
            labtxt = nz("".join(w.t for w in lab_toks))
            met = None
            t2 = re.sub(r"\(.*?\)", "", labtxt)
            for name in C_METRIC_WORDS:
                if t2.endswith(name):
                    met = name
                    labtxt = t2[: -len(name)]
                    break
            rows_info.append({"i": i, "y": ys[i], "seg_lbl": labtxt, "metric": met, "vals": vals, "toks": vt})
        mets = [r["metric"] for r in rows_info]
        if all(m is None for m in mets):
            for r in rows_info:
                r["metric"] = "합산비율"
                r["seg"] = r["seg_lbl"] or None
        else:
            blocks: list[list[dict]] = []
            for r in rows_info:
                if not blocks or r["metric"] in [b["metric"] for b in blocks[-1]] or r["metric"] == "손해율":
                    blocks.append([r])
                else:
                    blocks[-1].append(r)
            for b in blocks:
                lbl = next((r["seg_lbl"] for r in b if r["seg_lbl"]), "")
                if not lbl:
                    y0, y1 = b[0]["y"] - 8, b[-1]["y"] + 8
                    near = [lines[j] for j in range(len(lines)) if y0 <= ys[j] <= y1 and not _c_data_line(lines[j])]
                    lbl = nz("".join(w.t for ln in near for w in ln if w.x1 < col_x[0] - 8))
                for r in b:
                    r["seg"] = lbl or ("전체" if len(blocks) == 1 else None)
                    if not lbl:
                        flags.append("no_segment_label")
        for r in rows_info:
            pairs = list(zip(r["toks"], r["vals"])) if len(r["toks"]) == ncol else _align_to_cols(r["toks"], r["vals"], col_x, pitch)
            for w, v in pairs:
                ci = min(range(ncol), key=lambda x: abs(col_x[x] - w.xc))
                out.append({"종목": r["seg"], "지표": r["metric"], "_ci": ci, "_lab": labels[ci], "값": v[0], "dash": v[2], "_dec": v[1], "_tok": v[3],
                            "_flags": list(flags), "_ncol": ncol, "_y": r["y"]})
    return out


C_METRIC_WORDS = ("손해율", "사업비율", "합산비율")


def _align_to_cols(toks, vals, col_x, pitch):
    res = []
    for w, v in zip(toks, vals):
        j = min(range(len(col_x)), key=lambda i: abs(col_x[i] - w.xc))
        if abs(col_x[j] - w.xc) <= max(pitch * 0.6, 10.0):
            res.append((Wd(col_x[j], w.y0, col_x[j], w.y1, w.t), v))
    return res


# =============================================================================================
# 드라이버: (회사, 공시분기) PDF 하나에서 표 A·B·C 텍스트 추출 -> 행 + 칸별 진단
# =============================================================================================
ERRATA = load_errata()
BODY_MAX_PAGE = 100          # 이 쪽 이하(또는 전체 200쪽 이하 PDF)는 '본문', 그 뒤는 감사보고서·부록 '뒤쪽사본'
STD_GUBUN = {"Non-Par", "Direct-Par", "Indirect-Par", "합계"}


def is_body_page(page: int, npages: int) -> bool:
    return page <= BODY_MAX_PAGE or npages <= 200


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def meta_row(code: str, q: str, meta: dict) -> dict:
    nm, kind = meta.get(code, ("", ""))
    return {"원보험사코드": code, "원수사명": nm, "생손보여부": kind, "공시분기": q}


def text_page_stats(rec: dict) -> dict:
    ch = rec["chars"]
    n = len(ch)
    tp = sum(1 for c in ch if c >= TEXT_MIN_CHARS)
    n100 = min(n, 100)
    t100 = sum(1 for c in ch[:100] if c >= TEXT_MIN_CHARS)
    return {"pages": n, "text_pages": tp, "text_ratio": tp / max(n, 1), "body_ratio": t100 / max(n100, 1), "body_pages": n100}


# ---------------------------------------------------------------------------------------------
# 표 A
# ---------------------------------------------------------------------------------------------
_BIZ_RE = re.compile(r"\[(전통형재보험|공동재보험)\]")


def biz_heading(doc, p: int) -> str | None:
    """표가 속한 사업 구분 머리글(대괄호 '전통형재보험' · '공동재보험' - 코리안리는 같은 절에 두 사업의 ①② 표가 따로 있다).
    표 쪽 자신 -> 바로 앞 쪽 순으로 찾는다(자신 쪽은 첫 머리글, 앞 쪽은 마지막 머리글). 없으면 None."""
    for pp in (p, p - 1):
        if 1 <= pp <= doc.page_count:
            ms = list(_BIZ_RE.finditer(nz(doc[pp - 1].get_text())))
            if ms:
                return (ms[0] if pp == p else ms[-1]).group(1)
    return None


def run_A(doc, rec: dict, code: str, q: str, mrow: dict, path: Path) -> dict:
    yc = int(q[:4])
    h = rec["hits"]
    pages = sorted(set(h["A_cols"]) | set(h["A_head"]))
    secs: list[tuple[int, list[dict]]] = []
    for p in pages:
        if p > doc.page_count:
            continue
        rows = parse_A_page(get_words(doc[p - 1]), yc)
        if rows:
            secs.append((p, rows))
    n = doc.page_count
    bz_of = {p: biz_heading(doc, p) for p, _ in secs}
    multi = len({b_ for b_ in bz_of.values() if b_}) >= 2          # 사업이 둘 이상이면 (사업, 연도) 로 구분(둘은 사본이 아니라 다른 표)

    def _key(p_: int, y_: int):
        return ((bz_of.get(p_) if multi else None), y_)

    chosen: dict[tuple, tuple[int, dict]] = {}
    copies: list[tuple[int, dict, tuple]] = []
    for p, rows in secs:
        seen_here: dict[int, int] = {}
        for r in rows:
            y = r["기준연도"]
            if y is None:
                continue
            seen_here[y] = seen_here.get(y, 0) + 1
        for r in rows:
            y = r["기준연도"]
            if y is None:
                continue
            if seen_here[y] > 1:               # 한 쪽에 같은 연도 행이 둘 이상(연결/별도 소표 등) - 정본 선택 불가, 사본 대조에서도 제외
                r["_flags"] = list(r["_flags"]) + ["multi_row_same_year"]
                continue
            ky = _key(p, y)
            if ky in chosen:
                if is_body_page(p, n) and not is_body_page(chosen[ky][0], n):
                    copies.append((chosen[ky][0], chosen[ky][1], ky))
                    chosen[ky] = (p, r)
                else:
                    copies.append((p, r, ky))
            else:
                chosen[ky] = (p, r)
    out_rows = []
    for (bz_, y), (p, r) in sorted(chosen.items(), key=lambda kv: (str(kv[0][0] or ""), kv[0][1])):
        d = dict(mrow)
        if bz_:
            d["사업구분"] = bz_
        ck = check_A_row(r)
        d.update({"기준연도": y, "예상손해율": r["예상손해율"], "실제손해율": r["실제손해율"], "예실차비율": r["예실차비율"],
                  "단위": "%, %p", "출처": {"file": rel(path), "page": p}, "추출방식": "text",
                  "원천위치": "본문" if is_body_page(p, n) else "뒤쪽사본", "원문": r["원문"],
                  "identity": ck, "identity_break": (ck["ok"] is False), "플래그": sorted(set(r["_flags"])),
                  "_dec": r["_dec"], "_dash": r["_dash"]})
        if all(r["_dash"]):
            d["dash"] = True
        out_rows.append(d)
    # 사본 대조(정밀도 허용): 같은 연도·같은 쪽 구조가 아닌 사본은 값 차이만 계산
    copy_diffs = []
    for p, r, ky in copies:
        y = r["기준연도"]
        base = chosen[ky][1]
        for k in ("예상손해율", "실제손해율", "예실차비율"):
            a, b = base[k], r[k]
            if a is None or b is None:
                continue
            tol = 0.5 * 10 ** (-min(base["_dec"], r["_dec"])) + 1e-9
            if abs(a - b) > tol + 0.0:
                copy_diffs.append({"기준연도": y, "항목": k, "본문값": a, "사본값": b, "사본쪽": p, "사업구분": ky[0]})
    return {"rows": out_rows, "pages": [p for p, _ in secs], "copy_diffs": copy_diffs, "n_sections": len(secs)}


# ---------------------------------------------------------------------------------------------
# 표 B
# ---------------------------------------------------------------------------------------------
def _fix_year(y, yc):
    if y == -1:
        return yc
    if y == -2:
        return yc - 1
    return y


def run_B(doc, rec: dict, code: str, q: str, mrow: dict, path: Path) -> dict:
    yc = int(q[:4])
    h = rec["hits"]
    cand = sorted(set(h["B_head"]) | set(h["B_lab"]))
    cand = [p for p in cand if 1 <= p <= doc.page_count]
    n = doc.page_count
    res = {"sections": [], "cand": cand}
    if not cand:
        return res
    secs = extract_B_sections(doc, cand)
    for sec in secs:
        biz_sec = biz_heading(doc, sec["pages"][0])
        rows: list[dict] = []
        bads: dict[int, list[str]] = defaultdict(list)
        flags: list[str] = []
        for b in sec["blocks"]:
            rr, bd = block_rows(b, {})
            y = _fix_year(b["year"], yc)
            for r in rr:
                r["기준연도"] = _fix_year(r["기준연도"], yc)       # 그룹 단위 연도(당기/전기 표지)가 있으면 그것, 없으면 블록 연도
                r["_page"] = b["page"]
            rows += rr
            for yb_, txt_ in bd:
                bads[_fix_year(yb_, yc)].append(txt_)
            flags += [f"p{b['page']}:{f}" for f in b["flags"] if f not in ("cols_inherited",)]
            if b["unit"]:
                flags.append(f"unit:{b['unit']}")
        years = sorted({r["기준연도"] for r in rows if r["기준연도"] is not None})
        none_year = [r for r in rows if r["기준연도"] is None]
        per_year = {}
        for y in years:
            ry = _normalize_ratio_scale([r for r in rows if r["기준연도"] == y])
            ey = {k[2:]: note for k, note in ERRATA.get((code, q), {}).items() if k[0] in (None, y) and k[1] in ("", biz_sec or "")}
            st = check_B_rows(ry, ey)
            per_year[y] = {"rows": ry, "stats": st, "bad": bads.get(y, [])}
        res["sections"].append({"pages": sec["pages"], "years": years, "per_year": per_year, "flags": flags,
                                "none_year_rows": len(none_year), "first_page": sec["pages"][0],
                                "body": is_body_page(sec["pages"][0], n), "biz": biz_sec})
    return res


def _normalize_ratio_scale(rows: list[dict]) -> list[dict]:
    """비율 행이 '0.97' 처럼 배(소수)로 인쇄된 블록(카카오페이손해보험)을 %(97)로 바꾼다. 비율 검산이 거의 다 실패하고, 100배하면 거의 다 통과할 때만.
    원문 값은 '원값'·'원단위'(=배(소수))로 남긴다."""
    st = check_B_rows([dict(r) for r in rows])
    if st["ratio_checked"] < 8 or st["ratio_fail"] < 0.8 * st["ratio_checked"]:
        return rows
    conv = [dict(r) for r in rows]
    for r in conv:
        if r["지표"] == "비율" and r["값"] is not None:
            r["_ratio_orig"] = r["값"]
            r["값"] = round(r["값"] * 100, 6)
            r["_dec"] = max(r.get("_dec", 0) - 2, 0)
    st2 = check_B_rows([dict(r) for r in conv])
    if st2["ratio_checked"] >= 8 and st2["ratio_fail"] <= 0.1 * st2["ratio_checked"]:
        return conv
    return rows


def b_year_ok(py: dict) -> bool:
    st = py["stats"]
    return (st["ratio_fail"] == 0 and st["total_fail"] == 0 and not py["bad"] and len(py["rows"]) > 0
            and not st["missing_cols"] and not st["dup_keys"] and not st["nonstd"])


def pick_B(res: dict) -> dict[int, dict]:
    """연도별로 정본 구간 선택. 우선순위: 검산 통과 > 본문 > 쪽 순서. 반환 {연도: {sec, py, ok}}."""
    best: dict[int, dict] = {}
    for si, sec in enumerate(res["sections"]):
        for y, py in sec["per_year"].items():
            ok = b_year_ok(py)
            key = (1 if ok else 0, 1 if sec["body"] else 0, -sec["first_page"], len(py["rows"]))
            cur = best.get(y)
            if cur is None or key > cur["key"]:
                best[y] = {"key": key, "sec": sec, "py": py, "ok": ok, "si": si}
    return best


def finalize_B_rows(py_rows: list[dict], mrow: dict, path: Path, sec: dict, n: int, extra_flags: list[str], biz: str | None = None) -> list[dict]:
    out = []
    for r in py_rows:
        d = dict(mrow)
        if biz:
            d["사업구분"] = biz
        unit = r["단위"]
        val = r["값"]
        d.update({"기준연도": r["기준연도"], "구분": r["구분"], "구분_원문": r.get("구분_원문"), "포트폴리오": r["포트폴리오"],
                  "포트폴리오_원문": r.get("포트폴리오_원문"), "경과기간": r["경과기간"], "지표": r["지표"]})
        if r.get("부문"):
            d["부문"] = r["부문"]
        if r.get("라벨보정"):
            d["라벨보정"] = r["라벨보정"]
        if unit == "백만원" and r["지표"] != "비율":
            d["단위"] = "억원"
            if val is not None:
                d["값"] = round(val / 100, 6)
                d["원값"] = val
                d["원단위"] = "백만원"
            else:
                d["값"] = None
        else:
            d["값"] = val
            d["단위"] = unit
        if r.get("_ratio_orig") is not None:
            d["원값"], d["원단위"] = r["_ratio_orig"], "배(소수)"
        if r.get("원문오기"):
            d["원문오기"] = r["원문오기"]
        if r.get("텍스트층보정"):
            d["텍스트층보정"] = r["텍스트층보정"]
        d["dash"] = r.get("dash", False)
        d["출처"] = {"file": rel(path), "page": r["_page"]}
        d["추출방식"] = "text"
        d["원천위치"] = "본문" if is_body_page(r["_page"], n) else "뒤쪽사본"
        if r.get("_ratio_ok") is False:
            d["검산실패"] = "ratio"
        out.append(d)
    return out


# ---------------------------------------------------------------------------------------------
# 표 C
# ---------------------------------------------------------------------------------------------
def c_period_fields(year: int, sub: str | None, year_disc: int):
    q = None
    if sub is None or sub in ("연간계", "연간", "전체"):
        kind = "연간" if year < year_disc else "당해누적"
        if sub in ("연간계", "연간", "전체"):
            kind = "연간" if year < year_disc else "당해누적"
    else:
        mq = re.fullmatch(r"([1-4])분기", sub)
        if mq:
            q = int(mq.group(1))
            kind = f"{q}분기"
        elif "상반기" in sub or re.fullmatch(r"6월(?:누계|누적)", sub):
            kind = "상반기누적"
        elif re.search(r"누[계적]|^계$", sub):
            kind = "누적"
        else:
            kind = sub
    label = f"{year}년" + (f" {sub}" if sub else "")
    return label, q, kind


def seg_std(seg: str | None) -> str | None:
    if not seg:
        return None
    s = nz(seg)
    if "자동차" in s:
        return "자동차"
    if s.endswith("계") or s in ("합계", "전체") or "합계" in s:
        return "합계"
    if "일반" in s:
        return "일반"
    return s


def parse_c_label_raw(raw: str, year_disc: int):
    """vision 열 라벨 원문('2022년', '2024년 1분기', '연간계', '2025 (12월누적)') -> (연도, sub, 연도추정여부)."""
    t = nz(raw)
    m = re.search(r"20\d\d", t)
    inferred = False
    if m:
        year = int(m.group(0))
        rest = t[:m.start()] + t[m.end():]
    else:
        year, rest, inferred = year_disc, t, True
    rest = re.sub(r"^[년도]+", "", rest)
    rest = _norm_sub(rest.strip("()"))
    return year, (rest or None), inferred


def run_C(doc, rec: dict, code: str, q: str, mrow: dict, path: Path) -> dict:
    yc = int(q[:4])
    h = rec["hits"]
    n = doc.page_count
    pages = sorted(set(h["C_kw"]) | {p + 1 for p in h["C_kw"]} | {p + 1 for p in h["C_gs"]})
    pages = [p for p in pages if 1 <= p <= n]
    got: list[tuple[int, list[dict]]] = []
    last_labels: dict[int, dict] | None = None
    for p in pages:
        ws = get_words(doc[p - 1])
        rows = parse_C_page(ws, yc)
        if not rows:
            rows = parse_C_page(ws, yc, relaxed=True)
        if not rows:
            continue
        # 머리말 없는 이어짐 쪽: 직전 쪽 표와 열 수가 같으면 열 라벨 상속
        if all(r["_lab"] is None for r in rows) and last_labels and all(r["_ncol"] == len(last_labels) for r in rows):
            for r in rows:
                r["_lab"] = last_labels.get(r["_ci"])
                r["_flags"] = sorted(set(r["_flags"]) | {"labels_inherited"})
        else:
            by_ci = {}
            for r in rows:
                if r["_lab"] is not None:
                    by_ci[r["_ci"]] = r["_lab"]
            if by_ci and len(by_ci) == rows[0]["_ncol"]:
                last_labels = by_ci
        got.append((p, rows))
    out_rows: list[dict] = []
    seen_keys: dict[tuple, int] = {}
    for p, rows in got:
        for r in rows:
            lab = r["_lab"]
            if lab is None:
                continue
            label, qn, kind = c_period_fields(lab["연도"], lab["sub"], yc)
            key = (seg_std(r["종목"]) or r["종목"], r["지표"], label)
            if key in seen_keys:
                continue                    # 같은 칸이 여러 쪽에 나오면 첫 쪽이 정본
            seen_keys[key] = p
            d = dict(mrow)
            d.update({"종목": r["종목"], "종목_표준": seg_std(r["종목"]), "지표": r["지표"], "열라벨": label, "열라벨_원문": lab["원문"],
                      "연도": lab["연도"], "분기": qn, "구간": kind, "값": r["값"], "단위": "%", "dash": r["dash"],
                      "출처": {"file": rel(path), "page": p}, "추출방식": "text", "원천위치": "본문",
                      "_dec": r["_dec"], "플래그": sorted(set(r["_flags"]) - {"c_unmatched_sub_label"})})
            out_rows.append(d)
    unlabeled = sum(1 for _, rows in got for r in rows if r["_lab"] is None)
    return {"rows": out_rows, "pages": [p for p, _ in got], "unlabeled": unlabeled, "cand": pages}


def check_C_rows(rows: list[dict]) -> dict:
    """합산비율 = 손해율 + 사업비율 (±0.11, 소수 자릿수가 거칠면 1.5u). rows 는 한 (회사, 공시)."""
    cell: dict[tuple, dict] = {}
    for r in rows:
        cell.setdefault((r["종목"], r["열라벨"]), {})[r["지표"]] = r
    st = {"checked": 0, "fail": 0, "fails": []}
    for key, d in cell.items():
        a, b, c = d.get("손해율"), d.get("사업비율"), d.get("합산비율")
        if not (a and b and c) or a["값"] is None or b["값"] is None or c["값"] is None:
            continue
        dec = min(a["_dec"], b["_dec"], c["_dec"])
        tol = max(0.11, 1.5 * 10 ** (-dec) + 1e-9)
        st["checked"] += 1
        ok = abs(c["값"] - (a["값"] + b["값"])) <= tol
        for x in (a, b, c):
            x["_c_ok"] = ok
        if not ok:
            st["fail"] += 1
            if len(st["fails"]) < 8:
                st["fails"].append(f"{key}: 합산 {c['값']} vs 손해율 {a['값']} + 사업비율 {b['값']}")
    return st


# =============================================================================================
# vision 병합 / 칸별 상태(census) / 공시 간 대조(diffs) / 산출 쓰기
# =============================================================================================
KIND_LONG = {"손보": "손해보험", "생보": "생명보험", "손해보험": "손해보험", "생명보험": "생명보험"}
STATUS_ORDER = ["FILLED", "FILLED(vision)", "FILLED_CHECK_FLAGS", "ABSENT_IN_SOURCE", "UNREADABLE", "SCAN_PENDING", "PARSE_FAILED", "NO_PDF"]
YEAR_SLOT_NAMES = {0: "당기", 1: "전기"}


def norm_company(row: dict, meta: dict) -> dict:
    code = row["원보험사코드"]
    nm, kind = meta.get(code, (row.get("원수사명", ""), KIND_LONG.get(row.get("생손보여부", ""), row.get("생손보여부", ""))))
    row["원수사명"], row["생손보여부"] = nm or row.get("원수사명", ""), kind or KIND_LONG.get(row.get("생손보여부", ""), row.get("생손보여부", ""))
    return row


def load_vision(meta: dict, log=print):
    """data/loss_ratio/vision_cells*.json 전부 + data/persistency/vision_census_v*.csv 중 표 A·B·C 행."""
    rows = {"A": [], "B": [], "C": []}
    files = sorted(OUT_DIR.glob("vision_cells*.json"))
    for fn in files:
        data = json.loads(fn.read_text(encoding="utf-8"))
        for r in data:
            t = r.get("table")
            if t not in rows:
                continue
            r = dict(r)
            r["_vfile"] = fn.name
            rows[t].append(r)
    cen = []
    for fn in sorted(PERSIST_DIR.glob("vision_census_v*.csv")):
        with open(fn, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r.get("표", "").startswith(("A", "B", "C")):
                    r["_vfile"] = fn.name
                    cen.append(r)
    log(f"  [vision] 파일 {len(files)}개: A {len(rows['A'])} / B {len(rows['B'])} / C {len(rows['C'])}행, 칸결과 {len(cen)}행")
    return rows, cen


def vision_to_canon(vrows: dict, meta: dict) -> dict:
    """vision 행 -> 텍스트 행과 같은 스키마(경과기간·단위·열 라벨 정규화). 반환 {'A': [...], 'B': [...], 'C': [...]}."""
    out = {"A": [], "B": [], "C": []}
    for r in vrows["A"]:
        d = norm_company({k: r[k] for k in ("원보험사코드", "원수사명", "생손보여부", "공시분기")}, meta)
        d.update({"기준연도": r["기준연도"], "예상손해율": r["예상손해율"], "실제손해율": r["실제손해율"], "예실차비율": r["예실차비율"],
                  "단위": r.get("단위", "%, %p"), "출처": r["출처"], "추출방식": "vision", "원천위치": "본문(스캔)", "원문": r.get("원문"),
                  "identity": r.get("identity"), "identity_break": bool(r.get("identity_break", False)), "플래그": []})
        if r.get("na_gray"):
            d["플래그"].append("해당없음_빗금")
            d["dash"] = True
        d["_vfile"] = r["_vfile"]
        out["A"].append(d)
    for r in vrows["B"]:
        d = norm_company({k: r[k] for k in ("원보험사코드", "원수사명", "생손보여부", "공시분기")}, meta)
        val, unit = r["값"], r.get("단위")
        extra = {}
        if unit == "배(소수)" and val is not None:
            extra = {"원값": val, "원단위": "배(소수)"}
            val, unit = round(val * 100, 6), "%"
        elif unit == "배(소수)":
            unit = "%"
        d.update({"기준연도": r["기준연도"], "구분": r["구분"], "구분_원문": r["구분"], "포트폴리오": canon_portfolio(r["포트폴리오"]),
                  "포트폴리오_원문": r.get("포트폴리오_원문") or r["포트폴리오"], "경과기간": canon_period(r["경과기간"]) or r["경과기간"],
                  "지표": r["지표"], "값": val, "단위": unit, "dash": bool(r.get("dash")), "출처": r["출처"], "추출방식": "vision",
                  "원천위치": "본문(스캔)"})
        d.update(extra)
        if r.get("숫자출처"):
            d["숫자출처"] = r["숫자출처"]
        d["_vfile"] = r["_vfile"]
        out["B"].append(d)
    for r in vrows["C"]:
        d = norm_company({k: r[k] for k in ("원보험사코드", "원수사명", "생손보여부", "공시분기")}, meta)
        yd = int(r["공시분기"][:4])
        year, sub, inferred = parse_c_label_raw(r["열라벨"], yd)
        label, qn, kind = c_period_fields(year, sub, yd)
        d.update({"종목": r["종목"], "종목_표준": seg_std(r["종목"]), "지표": r["지표"], "열라벨": label, "열라벨_원문": r["열라벨"], "연도": year,
                  "분기": qn, "구간": kind, "값": r["값"], "단위": r.get("단위", "%"), "dash": bool(r.get("dash")), "출처": r["출처"],
                  "추출방식": "vision", "원천위치": "본문(스캔)", "플래그": (["c_year_inferred"] if inferred else [])})
        d["_vfile"] = r["_vfile"]
        out["C"].append(d)
    return out


# ---------------------------------------------------------------------------------------------
# 근거 문장 / 쪽 단위 보조
# ---------------------------------------------------------------------------------------------
def find_not_calculated(doc, pages: list[int], tbl: str | None = None) -> str | None:
    """'<보험금 예실차비율>을 산출하지 않음' 류 문장(원문)을 쪽들에서 찾는다. tbl 'A'/'B' 면 그 표의 이름이 든 문장만."""
    names = {"A": "보험금예실차비율", "B": "위험보험료대비예상보험금"}.get(tbl or "", "보험금예실차비율|위험보험료대비예상보험금")
    pat = re.compile(rf"({names})[^.\n]{{0,80}}산출하지")
    for p in pages:
        if not (1 <= p <= doc.page_count):
            continue
        t = doc[p - 1].get_text()
        tz = nz(t)
        m = pat.search(tz)
        if m:
            tt = re.sub(r"\s+", " ", t)
            i = tt.find("산출하지")
            return f"p{p}: …{tt[max(0, i - 90): i + 30].strip()}…"
    return None


def find_not_applicable(doc, pages: list[int]) -> str | None:
    """'4) 최적가정 □ 해당사항 없음' / '4) 최적가정 : 해당사항 없음' / '당사 장기손해보험 미영위로 4-6-2) ~ 4-6-6) 해당사항 없음' 처럼
    회사가 최적가정 절 전체를 해당 없음으로 적은 문장(원문)을 쪽들에서 찾는다(서울보증보험·캐롯손해보험)."""
    pats = (re.compile(r"최적가정[:\s]*[□ㅁ]?해당사항없음"), re.compile(r"미영위로[^\n]{0,40}해당사항없음"))
    for p in sorted(set(pages)):
        if not (1 <= p <= doc.page_count):
            continue
        t = doc[p - 1].get_text()
        tz = nz(t)
        for pat in pats:
            m = pat.search(tz)
            if m:                      # 공백을 뺀 글에서 일치 위치 주변을 그대로 인용(원문 공백은 없다)
                return f"p{p}: …{tz[max(0, m.start() - 6): m.end() + 4]}…"
    return None


def find_year_noncomparable(doc, pages: list[int], year: int) -> str | None:
    """'2023년 비교 공시 산출 불가' / '<2023년>(비교공시 산출 불가)' 처럼 회사가 그 기준연도를 산출하지 않는다고 적은 문장(원문)을 쪽들에서 찾는다."""
    pat = re.compile(rf"<?{year}년>?[(\[]?(?:비교공시)?산출(?:불가|하지않)")
    for p in sorted(set(pages)):
        if not (1 <= p <= doc.page_count):
            continue
        t = doc[p - 1].get_text()
        m = pat.search(nz(t))
        if m:
            tt = re.sub(r"\s+", " ", t)
            i = tt.find("산출")
            return f"p{p}: …{tt[max(0, i - 30): i + 14].strip()}…"
    return None


def page_has_table_like(ws: list[Wd], min_lines: int = 2) -> bool:
    n = 0
    for ln in group_lines(ws):
        k = sum(1 for w in ln if (parse_num(w.t) is not None and ("." in w.t or "%" in w.t)))
        if k >= 3:
            n += 1
    return n >= min_lines


def stat_text(st: dict) -> str:
    return (f"본문 텍스트쪽 {st['text_pages']}/{st['pages']} (앞 {st['body_pages']}쪽 중 {round(st['body_ratio'] * 100)}%)")


# ---------------------------------------------------------------------------------------------
# census
# ---------------------------------------------------------------------------------------------
CENSUS_FIELDS = ["원보험사코드", "원수사명", "생손보여부", "공시분기", "표", "기준연도", "상태", "추출방식", "원천위치", "쪽", "셀수", "값있는셀수", "근거"]


def cen_row(code, q, meta, table, year, status, how="", where="", pages="", n="", nval="", why=""):
    nm, kind = meta.get(code, ("", ""))
    return {"원보험사코드": code, "원수사명": nm, "생손보여부": kind, "공시분기": q, "표": table, "기준연도": year, "상태": status,
            "추출방식": how, "원천위치": where, "쪽": pages, "셀수": n, "값있는셀수": nval, "근거": why}


def page_list(ps) -> str:
    ps = sorted(set(ps))
    return ",".join(str(p) for p in ps)


def nonnull(rows, key="값") -> int:
    return sum(1 for r in rows if r.get(key) is not None)


# =============================================================================================
# 전체 추출 + 조립
# =============================================================================================
def extract_all(pdfs, idx, meta, only=None, quarters=None, log=print):
    import fitz  # noqa: PLC0415
    results: dict[tuple[str, str], dict] = {}
    t0 = time.time()
    keys = sorted(pdfs, key=lambda k: (k[1], k[0]))
    for i, (q, code) in enumerate(keys, 1):
        if (only and code not in only) or (quarters and q not in quarters):
            continue
        path = pdfs[(q, code)]
        rec = idx[rel(path)]
        res: dict = {"path": path, "rec": rec, "stat": text_page_stats(rec)}
        mrow = meta_row(code, q, meta)
        try:
            doc = fitz.open(str(path))
        except Exception as e:  # noqa: BLE001
            res["error"] = f"{type(e).__name__}: {e}"
            results[(code, q)] = res
            continue
        res["npages"] = doc.page_count
        try:
            if q in ANNUAL_QUARTERS:
                res["A"] = run_A(doc, rec, code, q, mrow, path)
                res["B"] = run_B(doc, rec, code, q, mrow, path)
            if code in NONLIFE_CODES:
                res["C"] = run_C(doc, rec, code, q, mrow, path)
            # 근거 문장(미산출 표기)은 census 에서 필요할 때만 읽는다
            res["doc_path"] = str(path)
        except Exception as e:  # noqa: BLE001
            import traceback
            res["error"] = f"{type(e).__name__}: {e}"
            res["trace"] = traceback.format_exc()[-1500:]
        doc.close()
        results[(code, q)] = res
        if i % 40 == 0:
            log(f"  [extract] {i}/{len(keys)} {code} {q}  t={time.time() - t0:.0f}s")
    return results


def clean_row(r: dict) -> dict:
    return {k: v for k, v in r.items() if not k.startswith("_")}


def expected_years(q: str) -> list[int]:
    y = int(q[:4])
    return [y, y - 1]


def assemble(results, vis, vis_cen, meta, pdfs, log=print):
    """텍스트 + vision 병합 -> 최종 행 / census 행. 우선순위: 텍스트 FILLED > vision FILLED > vision ABSENT/UNREADABLE > SCAN_PENDING."""
    import fitz  # noqa: PLC0415
    final = {"A": [], "B": [], "C": []}
    census: list[dict] = []
    flags_log: list[dict] = []
    codes = sorted({c for _, c in pdfs} | set(meta))
    nonlife = [c for c in codes if c in NONLIFE_CODES]
    vA = defaultdict(list)
    vB = defaultdict(list)
    vC = defaultdict(list)
    for r in vis["A"]:
        vA[(r["원보험사코드"], r["공시분기"], r["기준연도"])].append(r)
    for r in vis["B"]:
        vB[(r["원보험사코드"], r["공시분기"], r["기준연도"])].append(r)
    for r in vis["C"]:
        vC[(r["원보험사코드"], r["공시분기"])].append(r)
    vcen = {}
    for r in vis_cen:
        vcen[(r["원보험사코드"], r["공시분기"], r["표"])] = r

    def vision_note(code, q, table):
        c = vcen.get((code, q, table))
        return c

    for code in codes:
        for q in ANNUAL_QUARTERS:
            res = results.get((code, q))
            path = pdfs.get((q, code))
            if res is None or path is None:
                if path is None:
                    for tb in ("A", "B"):
                        census.append(cen_row(code, q, meta, tb, "", "NO_PDF", why="해당 (회사,분기) PDF 가 data/disclosure 에 없음(다운로더 소관)"))
                continue
            st = res["stat"]
            if "error" in res:
                for tb in ("A", "B"):
                    census.append(cen_row(code, q, meta, tb, "", "PARSE_FAILED", why=f"추출 예외: {res['error']}"))
                continue
            doc = None
            h = res["rec"]["hits"]
            for tb in ("A", "B"):
                tbres = res[tb]
                years = expected_years(q) if q != "2023.4Q" else []
                no_hit = (tb == "A" and not (h["A_cols"] or h["A_head"])) or (tb == "B" and not (h["B_head"] or h["B_lab"]))
                if not years:      # 2023.4Q: 결산본에 표 ①② 없음(2024.4Q 결산본부터)
                    has_vis = any((code, q, y) in (vA if tb == "A" else vB) for y in (2023, 2022))
                    if no_hit and not has_vis:
                        vc0 = vcen.get((code, q, tb))        # 스캔 본문은 vision 이 렌더를 보고 ABSENT/UNREADABLE 을 판정해 둔 칸(V5: KR0079 2023.4Q)
                        if vc0 and vc0["상태"] != "FILLED":
                            census.append(cen_row(code, q, meta, tb, "", vc0["상태"], "vision", "본문(스캔)", vc0.get("쪽", ""), 0, 0, f"vision 판독: {vc0['근거'][:500]}"))
                        elif st["body_ratio"] < 0.6:
                            census.append(cen_row(code, q, meta, tb, "", "SCAN_PENDING", pages="", why=f"키워드 0건이나 {stat_text(st)} - 본문 스캔 쪽에 있을 수 있음"))
                        else:
                            census.append(cen_row(code, q, meta, tb, "", "ABSENT_IN_SOURCE", why=f"전 쪽 키워드 0건(예상손해율·실제손해율·위험보험료 대비 예상보험금), {stat_text(st)}; ①② 표는 2024.4Q 결산본부터 신설"))
                        continue
                    years = [2023, 2022]
                if tb == "A":
                    _assemble_A(final, census, flags_log, code, q, meta, res, tbres, years, vA, vcen, no_hit, st, path)
                else:
                    _assemble_B(final, census, flags_log, code, q, meta, res, tbres, years, vB, vcen, no_hit, st, path)
        for q in QUARTERS:
            if code not in NONLIFE_CODES:
                continue
            res = results.get((code, q))
            path = pdfs.get((q, code))
            if path is None:
                census.append(cen_row(code, q, meta, "C", "", "NO_PDF", why="해당 (회사,분기) PDF 가 data/disclosure 에 없음(다운로더 소관)"))
                continue
            if res is None:
                continue
            _assemble_C(final, census, flags_log, code, q, meta, res, vC, vcen, path)
    return final, census, flags_log


def _doc_for(res):
    import fitz  # noqa: PLC0415
    return fitz.open(res["doc_path"])


def _assemble_A(final, census, flags_log, code, q, meta, res, tbres, years, vA, vcen, no_hit, st, path):
    bizs = sorted({r.get("사업구분") for r in tbres["rows"] if r.get("사업구분")})
    if len(bizs) >= 2:        # 같은 공시에 사업(전통형재보험·공동재보험)별 표가 따로 있으면 사업마다 기대 칸을 센다
        for bz in bizs:
            sub = dict(tbres)
            sub["rows"] = [r for r in tbres["rows"] if r.get("사업구분") == bz]
            sub["copy_diffs"] = [d for d in tbres["copy_diffs"] if d.get("사업구분") == bz]
            _assemble_A_one(final, census, flags_log, code, q, meta, res, sub, years, vA, vcen, no_hit, st, path, biz=bz)
        return
    _assemble_A_one(final, census, flags_log, code, q, meta, res, tbres, years, vA, vcen, no_hit, st, path)


def _assemble_A_one(final, census, flags_log, code, q, meta, res, tbres, years, vA, vcen, no_hit, st, path, biz=None):
    rows = {r["기준연도"]: r for r in tbres["rows"]}
    n = res["npages"]
    for y in years:
        ylab = y if biz is None else f"{y}|{biz}"
        tr = rows.get(y)
        vrs = vA.get((code, q, y), [])
        vc = vcen.get((code, q, "A"))
        if tr is not None and tr.get("dash"):
            tr_status = "ABSENT_IN_SOURCE"
        else:
            tr_status = "FILLED" if tr is not None else None
        if tr is not None and tr_status == "FILLED":
            r = dict(tr)
            if tr["identity_break"]:
                tr_status = "FILLED_CHECK_FLAGS"
            final["A"].append(r)
            why = f"{r['원천위치']} 쪽 {r['출처']['page']}; 예실차=A-B 검산 {'통과' if not r['identity_break'] else '실패'}"
            if r["플래그"]:
                why += f"; 플래그 {','.join(r['플래그'])}"
            if tbres["copy_diffs"]:
                cd = [d for d in tbres["copy_diffs"] if d["기준연도"] == y]
                if cd:
                    why += f"; 뒤쪽 사본과 값 차이 {len(cd)}건({cd[0]['항목']} 본문 {cd[0]['본문값']} vs 사본 {cd[0]['사본값']} p{cd[0]['사본쪽']})"
                    flags_log.append({"유형": "A_사본불일치", "회사": code, "공시분기": q, "내용": why})
            census.append(cen_row(code, q, meta, "A", ylab, tr_status, "text", r["원천위치"], r["출처"]["page"], 1, 1, why))
            continue
        # 텍스트 없음/대시 -> vision
        if vrs:
            vr = vrs[0]
            nonnull_ = any(vr[k] is not None for k in ("예상손해율", "실제손해율", "예실차비율"))
            d = dict(vr)
            final["A"].append(d)
            if not nonnull_:
                note = "빗금(해당없음)" if "해당없음_빗금" in vr["플래그"] else "전 칸 '-'"
                census.append(cen_row(code, q, meta, "A", ylab, "ABSENT_IN_SOURCE", "vision", "본문(스캔)", vr["출처"]["page"], 1, 0, f"vision 판독: {note}. {(vc or {}).get('근거', '')[:300]}"))
            else:
                census.append(cen_row(code, q, meta, "A", ylab, "FILLED(vision)", "vision", "본문(스캔)", vr["출처"]["page"], 1, 1,
                                      f"vision 판독 (원문 {vr.get('원문')}); 예실차=A-B {'통과' if not vr['identity_break'] else '실패'}"))
            continue
        if tr is not None and tr_status == "ABSENT_IN_SOURCE":
            final["A"].append(dict(tr))
            census.append(cen_row(code, q, meta, "A", ylab, "ABSENT_IN_SOURCE", "text", tr["원천위치"], tr["출처"]["page"], 1, 0,
                                  "표에 행은 있으나 세 칸 모두 '-' (회사가 해당 기준연도 값을 공시하지 않음)"))
            continue
        # 텍스트·vision 모두 없음 -> 이유 판정
        if tbres["rows"]:
            pages = tbres["pages"]
            doc = _doc_for(res)
            ev_y = find_year_noncomparable(doc, pages, y)
            doc.close()
            if ev_y:
                census.append(cen_row(code, q, meta, "A", ylab, "ABSENT_IN_SOURCE", "text", "", page_list(pages), 0, 0, f"회사가 {y}년 비교공시 산출 불가를 명시: {ev_y}"))
                continue
            # 표는 읽혔으나 이 기준연도 행이 없다 -> 해당 쪽에 그 연도 표기가 있는지
            census.append(cen_row(code, q, meta, "A", ylab, "ABSENT_IN_SOURCE", "text", "", page_list(pages), 0, 0,
                                  f"표 A 는 읽혔으나({','.join(str(r['기준연도']) for r in tbres['rows'])}년 행) {y}년 행/블록 없음 - 공시본이 {','.join(str(r['기준연도']) for r in tbres['rows'])}년만 인쇄"))
            continue
        doc = _doc_for(res)
        h = res["rec"]["hits"]
        ev = find_not_calculated(doc, sorted(set(h["opt"]) | set(h["A_head"]) | set(h["B_head"])), "A")
        ev_na = None if ev else find_not_applicable(doc, h["opt"])
        doc.close()
        if not no_hit and not ev:
            census.append(cen_row(code, q, meta, "A", ylab, "PARSE_FAILED", "text", "", page_list(set(res['rec']['hits']['A_cols']) | set(res['rec']['hits']['A_head'])), 0, 0,
                                  "표 A 키워드 쪽은 있으나 연도·값 행을 못 읽음"))
            continue
        if ev:
            census.append(cen_row(code, q, meta, "A", ylab, "ABSENT_IN_SOURCE", "text", "", "", 0, 0, f"회사가 표 미산출을 명시: {ev}"))
        elif ev_na:
            census.append(cen_row(code, q, meta, "A", ylab, "ABSENT_IN_SOURCE", "text", "", "", 0, 0, f"회사가 최적가정 절을 해당사항 없음으로 명시: {ev_na}"))
        elif st["body_ratio"] < 0.6:
            census.append(cen_row(code, q, meta, "A", ylab, "SCAN_PENDING", "", "", "", 0, 0,
                                  f"키워드 0건, {stat_text(st)} - 본문이 스캔(텍스트층 없음)이고 뒤쪽 텍스트 사본도 없음 -> vision 필요"))
        else:
            census.append(cen_row(code, q, meta, "A", ylab, "ABSENT_IN_SOURCE", "text", "", "", 0, 0,
                                  f"전 쪽 키워드 0건(예상손해율·실제손해율), 최적가정 쪽 {page_list(h['opt']) or '없음'}; {stat_text(st)}"))


def _assemble_B(final, census, flags_log, code, q, meta, res, tbres, years, vB, vcen, no_hit, st, path):
    bizs = sorted({sec.get("biz") for sec in tbres["sections"] if sec.get("biz")})
    if len(bizs) >= 2:        # 같은 공시에 사업(전통형재보험·공동재보험)별 표가 따로 있으면 사업마다 구간을 고르고 기대 칸을 센다
        for bz in bizs:
            sub = dict(tbres)
            sub["sections"] = [sec for sec in tbres["sections"] if sec.get("biz") == bz]
            _assemble_B_one(final, census, flags_log, code, q, meta, res, sub, years, vB, vcen, no_hit, st, path, biz=bz)
        return
    _assemble_B_one(final, census, flags_log, code, q, meta, res, tbres, years, vB, vcen, no_hit, st, path)


def _assemble_B_one(final, census, flags_log, code, q, meta, res, tbres, years, vB, vcen, no_hit, st, path, biz=None):
    best = pick_B(tbres) if tbres["sections"] else {}
    n = res["npages"]
    h = res["rec"]["hits"]
    for y in years:
        ylab = y if biz is None else f"{y}|{biz}"
        b = best.get(y)
        vrs = vB.get((code, q, y), [])
        vc_prior = vcen.get((code, q, f"B-전년블록({y})"))
        if b is not None and b["ok"]:
            rows = finalize_B_rows(b["py"]["rows"], meta_row(code, q, meta), path, b["sec"], n, [], biz)
            final["B"] += rows
            pgs = sorted({r["출처"]["page"] for r in rows})
            where = "본문" if b["sec"]["body"] else "뒤쪽사본"
            st_ = b["py"]["stats"]
            why = (f"{where} 쪽 {page_list(pgs)}; 비율≈A÷B {st_['ratio_checked'] - st_['ratio_fail']}/{st_['ratio_checked']} 통과, "
                   f"합계=Σ포트폴리오 {st_['total_checked'] - st_['total_fail']}/{st_['total_checked']} 통과")
            fl = [f for f in b["sec"]["flags"] if not f.startswith("unit:")]
            if fl:
                why += f"; 구간플래그 {','.join(fl[:4])}"
            if st_["errata_hit"] or st_["errata_unmatched"]:
                why += (f"; 원문오기 등재 {len(st_['errata_hit'])}칸 플래그(해당 칸의 비율 {st_['ratio_errata']}건·합계 {st_['total_errata']}건 검산 제외)"
                        + (f", 등재했으나 칸을 못 찾음 {st_['errata_unmatched']}" if st_["errata_unmatched"] else ""))
            if vrs:
                why += f"; (vision 값도 있음 {len(vrs)}행 - diffs 참조)"
            census.append(cen_row(code, q, meta, "B", ylab, "FILLED", "text", where, page_list(pgs), len(rows), nonnull(rows), why))
            continue
        if vrs:
            for r in vrs:
                final["B"].append(dict(r))
            vn = nonnull(vrs)
            pgs = sorted({r["출처"]["page"] for r in vrs})
            if vn == 0:
                census.append(cen_row(code, q, meta, "B", ylab, "ABSENT_IN_SOURCE", "vision", "본문(스캔)", page_list(pgs), len(vrs), 0, "vision 판독: 전 칸 '-' (값 없음)"))
            else:
                census.append(cen_row(code, q, meta, "B", ylab, "FILLED(vision)", "vision", "본문(스캔)", page_list(pgs), len(vrs), vn,
                                      "vision 판독 (칸결과표 " + ((vcen.get((code, q, 'B')) or {}).get('_vfile', '')) + ")" +
                                      (f"; 텍스트 구간은 검산 실패라 vision 채택(텍스트 {len(b['py']['rows'])}행)" if b is not None else "")))
            continue
        if b is not None:
            rows = finalize_B_rows(b["py"]["rows"], meta_row(code, q, meta), path, b["sec"], n, [], biz)
            final["B"] += rows
            st_ = b["py"]["stats"]
            why = (f"검산 실패 — 비율 {st_['ratio_fail']}/{st_['ratio_checked']}건, 합계 {st_['total_fail']}/{st_['total_checked']}건, 숫자 파싱불가 {len(b['py']['bad'])}칸; "
                   + " | ".join(st_["fails"][:3]) + (f" | BAD {b['py']['bad'][:2]}" if b['py']['bad'] else ""))
            census.append(cen_row(code, q, meta, "B", ylab, "FILLED_CHECK_FLAGS", "text", "본문" if b["sec"]["body"] else "뒤쪽사본",
                                  page_list(sorted({r['출처']['page'] for r in rows})), len(rows), nonnull(rows), why))
            continue
        if vc_prior and vc_prior["상태"] != "FILLED":
            census.append(cen_row(code, q, meta, "B", ylab, vc_prior["상태"], "vision", "본문(스캔)", vc_prior.get("쪽", ""), 0, 0, f"vision 판독: {vc_prior['근거'][:400]}"))
            continue
        # 텍스트·vision 모두 없음
        if tbres["sections"]:
            pgs = sorted({p for s_ in tbres["sections"] for p in s_["pages"]})
            doc = _doc_for(res)
            has_cap = any(re.search(rf"<{y}년", nz(doc[p - 1].get_text())) for p in pgs if p <= doc.page_count)
            # 표 B 머리말 단어가 서술문에 나와 헛구간이 잡힌 경우: 회사가 '산출하지 않음' 을 명시했는지 먼저 본다(연금보험 단종사 등)
            ev_nc = find_not_calculated(doc, sorted(set(h["opt"]) | set(h["A_head"]) | set(h["B_head"]) | set(h["B_lab"])), "B")
            doc.close()
            found = sorted({yy for s_ in tbres["sections"] for yy in s_["years"]})
            doc = _doc_for(res)
            ev_y = find_year_noncomparable(doc, pgs, y)
            doc.close()
            if ev_y:
                census.append(cen_row(code, q, meta, "B", ylab, "ABSENT_IN_SOURCE", "text", "", page_list(pgs), 0, 0, f"회사가 {y}년 비교공시 산출 불가를 명시: {ev_y}"))
            elif ev_nc and not found:
                census.append(cen_row(code, q, meta, "B", ylab, "ABSENT_IN_SOURCE", "text", "", page_list(pgs), 0, 0, f"회사가 표 미산출을 명시: {ev_nc}"))
            elif has_cap:
                census.append(cen_row(code, q, meta, "B", ylab, "PARSE_FAILED", "text", "", page_list(pgs), 0, 0, f"쪽 {page_list(pgs)} 에 <{y}년> 캡션은 있으나 블록을 못 읽음"))
            else:
                census.append(cen_row(code, q, meta, "B", ylab, "ABSENT_IN_SOURCE", "text", "", page_list(pgs), 0, 0,
                                      f"쪽 {page_list(pgs)} 텍스트에 <{y}년> 캡션 없음 - 공시본은 {','.join(map(str, found)) or '연도 미상'}년 블록만 인쇄"))
            continue
        doc = _doc_for(res)
        ev = find_not_calculated(doc, sorted(set(h["opt"]) | set(h["A_head"]) | set(h["B_head"])), "B")
        ev_na = None if ev else find_not_applicable(doc, h["opt"])
        doc.close()
        if not no_hit and not ev:
            census.append(cen_row(code, q, meta, "B", ylab, "PARSE_FAILED", "text", "", page_list(set(h['B_head']) | set(h['B_lab'])), 0, 0, "표 B 키워드 쪽은 있으나 구간을 못 읽음"))
            continue
        if ev:
            census.append(cen_row(code, q, meta, "B", ylab, "ABSENT_IN_SOURCE", "text", "", "", 0, 0, f"회사가 표 미산출을 명시: {ev}"))
        elif ev_na:
            census.append(cen_row(code, q, meta, "B", ylab, "ABSENT_IN_SOURCE", "text", "", "", 0, 0, f"회사가 최적가정 절을 해당사항 없음으로 명시: {ev_na}"))
        elif st["body_ratio"] < 0.6:
            census.append(cen_row(code, q, meta, "B", ylab, "SCAN_PENDING", "", "", "", 0, 0,
                                  f"키워드 0건, {stat_text(st)} - 본문이 스캔(텍스트층 없음)이고 뒤쪽 텍스트 사본도 없음 -> vision 필요"))
        else:
            census.append(cen_row(code, q, meta, "B", ylab, "ABSENT_IN_SOURCE", "text", "", "", 0, 0,
                                  f"전 쪽 키워드 0건(위험보험료 대비 예상보험금), 최적가정 쪽 {page_list(h['opt']) or '없음'}; {stat_text(st)}"))


def _assemble_C(final, census, flags_log, code, q, meta, res, vC, vcen, path):
    st = res["stat"]
    tr = res.get("C")
    if "error" in res and not tr:
        census.append(cen_row(code, q, meta, "C", "", "PARSE_FAILED", why=f"추출 예외: {res['error']}"))
        return
    rows = tr["rows"] if tr else []
    vrs = vC.get((code, q), [])
    h = res["rec"]["hits"]
    if rows:
        chk = check_C_rows(rows)
        final["C"] += rows
        why = f"쪽 {page_list(tr['pages'])}; 합산=손해율+사업비율 {chk['checked'] - chk['fail']}/{chk['checked']} 통과"
        if tr["unlabeled"]:
            why += f"; 열 라벨 미배정 {tr['unlabeled']}칸(제외)"
        status = "FILLED"
        if chk["fail"] or tr["unlabeled"]:
            status = "FILLED_CHECK_FLAGS"
            why += "; " + " | ".join(chk["fails"][:3])
        if vrs:
            why += f"; (vision 값도 있음 {len(vrs)}행 - diffs 참조)"
        census.append(cen_row(code, q, meta, "C", "", status, "text", "본문", page_list(tr["pages"]), len(rows), nonnull(rows), why))
        return
    if vrs:
        for r in vrs:
            final["C"].append(dict(r))
        census.append(cen_row(code, q, meta, "C", "", "FILLED(vision)", "vision", "본문(스캔)", page_list({r['출처']['page'] for r in vrs}), len(vrs), nonnull(vrs),
                              f"vision 판독 ({(vcen.get((code, q, 'C')) or {}).get('근거', '')[:300]})"))
        return
    vc = vcen.get((code, q, "C"))
    if vc and vc["상태"] != "FILLED":
        census.append(cen_row(code, q, meta, "C", "", vc["상태"], "vision", "본문(스캔)", vc.get("쪽", ""), 0, 0, f"vision 판독: {vc['근거'][:400]}"))
        return
    cand = tr["cand"] if tr else []
    if tr is not None and cand:
        # 후보 쪽(합산비율 키워드 쪽·다음 쪽)에 표 모양 줄이 있는데 못 읽었나?
        doc = _doc_for(res)
        # 합산비율 표는 '손해율'·'사업비율' 행 라벨이 같은 쪽에 있다. 숫자 줄만 있고 그 라벨이 없으면 지급여력 총괄 표 + 서술문('회사합산비율 적용')이다(캐롯 2025.1Q p13).
        tablelike = [p for p in cand if p <= doc.page_count and page_has_table_like(get_words(doc[p - 1]))
                     and "사업비율" in nz(doc[p - 1].get_text()) and "손해율" in nz(doc[p - 1].get_text())]
        doc.close()
        if tablelike:
            census.append(cen_row(code, q, meta, "C", "", "PARSE_FAILED", "text", "", page_list(tablelike), 0, 0, f"합산비율 키워드 쪽에 표 모양 줄이 있으나 열 라벨/행을 못 읽음"))
            return
        gs = h["C_gs"]
        census.append(cen_row(code, q, meta, "C", "", "ABSENT_IN_SOURCE", "text", "", page_list(h["C_kw"]), 0, 0,
                              ("1Q/3Q 분기공시(축약본): " if q[-2] in "13" else "")
                              + f"합산비율 키워드 쪽 {page_list(h['C_kw']) or '-'}(가격설정 절 {page_list(gs) or '-'})에 손해율·사업비율 행의 합산비율 표 없음 — 지급여력 총괄 표·서술문('회사합산비율 적용')의 언급뿐; {stat_text(st)}"))
        return
    if st["body_ratio"] < 0.6 and st["text_ratio"] < 0.9:
        census.append(cen_row(code, q, meta, "C", "", "SCAN_PENDING", "", "", "", 0, 0, f"키워드 0건, {stat_text(st)} - 스캔/무텍스트 PDF -> vision 필요"))
    else:
        why = f"전 쪽 '합산비율' 키워드 0건, 가격설정 절 쪽 {page_list(h['C_gs']) or '없음'}; {stat_text(st)}"
        if q[-2] in "13":
            why = "1Q/3Q 분기공시(축약본): " + why
        census.append(cen_row(code, q, meta, "C", "", "ABSENT_IN_SOURCE", "text", "", "", 0, 0, why))


# =============================================================================================
# 공시 간 대조(diffs) / PDF 조사표(survey) / 쓰기 / main
# =============================================================================================
DIFF_FIELDS = ["표", "원보험사코드", "원수사명", "기준연도_또는_열", "공시분기_a", "공시분기_b", "비교셀수", "차이셀수", "최대차이", "판정", "예시"]


def _dec_of(v, d=None) -> int:
    if d is not None:
        return d
    if v is None:
        return 0
    s = repr(float(v))
    return len(s.split(".")[1].rstrip("0")) if "." in s and s.split(".")[1].strip("0") else 0


def build_diffs(final: dict, meta: dict) -> list[dict]:
    out: list[dict] = []
    # ---- A: 같은 (회사, 기준연도) 가 둘 이상의 공시에 나오면 비교
    by = defaultdict(dict)
    for r in final["A"]:
        by[(r["원보험사코드"], r["기준연도"], r.get("사업구분"))][r["공시분기"]] = r
    for (code, y, bz), d in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1], str(kv[0][2] or ""))):
        qs = sorted(d)
        for i in range(len(qs)):
            for j in range(i + 1, len(qs)):
                a, b = d[qs[i]], d[qs[j]]
                ncmp = ndiff = 0
                mx = 0.0
                ex = []
                for k in ("예상손해율", "실제손해율", "예실차비율"):
                    va, vb = a[k], b[k]
                    if va is None or vb is None:
                        continue
                    ncmp += 1
                    tol = 0.5 * 10 ** (-min(_dec_of(va, a.get("_dec")), _dec_of(vb, b.get("_dec")))) + 1e-9
                    diff = abs(va - vb)
                    if diff > tol:
                        ndiff += 1
                        mx = max(mx, diff)
                        ex.append(f"{k}: {va}→{vb}")
                    elif diff > 1e-9:
                        mx = max(mx, diff)
                if not ncmp:
                    continue
                out.append({"표": "A", "원보험사코드": code, "원수사명": meta.get(code, ("",))[0], "기준연도_또는_열": (y if not bz else f"{y}|{bz}"), "공시분기_a": qs[i], "공시분기_b": qs[j],
                            "비교셀수": ncmp, "차이셀수": ndiff, "최대차이": round(mx, 6), "판정": "동일(반올림 허용)" if not ndiff else "값차이(재작성 의심)",
                            "예시": "; ".join(ex[:3])})
    # ---- B: (회사, 기준연도) 별 공시 간 비교 + 다른 기준연도인데 값이 전부 같은 블록
    byb = defaultdict(lambda: defaultdict(dict))
    sig = {}
    for r in final["B"]:
        key = (r.get("부문"), r["구분"], r["포트폴리오"], r["경과기간"], r["지표"])
        byb[(r["원보험사코드"], r["기준연도"], r.get("사업구분"))][r["공시분기"]][key] = r["값"]
    for (code, y0, bz), d in sorted(byb.items(), key=lambda kv: (kv[0][0], kv[0][1], str(kv[0][2] or ""))):
        y = y0 if not bz else f"{y0}|{bz}"
        qs = sorted(d)
        for q_, cells in d.items():
            sig[(code + ("" if not bz else "|" + bz), q_, y0)] = cells
        for i in range(len(qs)):
            for j in range(i + 1, len(qs)):
                ca, cb = d[qs[i]], d[qs[j]]
                keys = set(ca) | set(cb)
                ncmp = ndiff = 0
                mx = 0.0
                ex = []
                for k in sorted(keys, key=str):
                    va, vb = ca.get(k), cb.get(k)
                    if va is None and vb is None:
                        continue
                    if k not in ca or k not in cb:
                        v_ = va if k in ca else vb
                        if v_ is not None and abs(v_) > 1e-9:       # 한쪽은 칸 없음(빈 칸), 다른 쪽이 0/'-' 면 차이로 세지 않는다
                            ncmp += 1
                            ndiff += 1
                            ex.append(f"{'/'.join(map(str, k))}: {va if k in ca else '(칸없음)'}→{vb if k in cb else '(칸없음)'}")
                        continue
                    ncmp += 1
                    if va is None or vb is None:
                        if (va or 0.0) == 0.0 and (vb or 0.0) == 0.0:      # 한쪽 '-'(null) · 다른 쪽 0 인쇄: 0 채움 유무일 뿐 값 차이가 아니다
                            continue
                        ndiff += 1
                        ex.append(f"{'/'.join(map(str, k))}: {va}→{vb}")
                        continue
                    tol_ = 0.5 * 10 ** (-min(_dec_of(va), _dec_of(vb))) + 1e-9      # 인쇄 자릿수가 다른 공시(소수 2자리 vs 정수)는 반올림 범위 안이면 같은 값
                    if abs(va - vb) > tol_:
                        ndiff += 1
                        mx = max(mx, abs(va - vb))
                        ex.append(f"{'/'.join(map(str, k))}: {va}→{vb}")
                if not ncmp:
                    continue
                out.append({"표": "B", "원보험사코드": code, "원수사명": meta.get(code, ("",))[0], "기준연도_또는_열": y, "공시분기_a": qs[i], "공시분기_b": qs[j],
                            "비교셀수": ncmp, "차이셀수": ndiff, "최대차이": round(mx, 6), "판정": "동일" if not ndiff else "값차이(재작성 의심)", "예시": "; ".join(ex[:5])})
    # 다른 기준연도인데 값이 전부(거의) 같은 블록
    by_code = defaultdict(list)
    for (code, q_, y), cells in sig.items():
        by_code[code].append((q_, y, cells))
    for code, blocks in sorted(by_code.items()):
        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                qa, ya, ca = blocks[i]
                qb, yb, cb = blocks[j]
                if ya == yb:
                    continue
                va = {k: v for k, v in ca.items() if v is not None}
                vb = {k: v for k, v in cb.items() if v is not None}
                if len(va) < 50 or len(vb) < 50:
                    continue
                same = sum(1 for k, v in va.items() if k in vb and abs(vb[k] - v) < 1e-9)
                tot = max(len(va), len(vb))
                if same / tot >= 0.99:
                    code_, _, bz_ = code.partition("|")
                    out.append({"표": "B", "원보험사코드": code_, "원수사명": meta.get(code_, ("",))[0], "기준연도_또는_열": f"{ya} vs {yb}" + (f"|{bz_}" if bz_ else ""), "공시분기_a": qa, "공시분기_b": qb,
                                "비교셀수": tot, "차이셀수": tot - same, "최대차이": "",
                                "판정": "다른기준연도_값전부동일" if same == tot else "다른기준연도_값거의동일(>=99%)",
                                "예시": f"{qa} <{ya}년> 블록 vs {qb} <{yb}년> 블록: 값 있는 칸 {tot}개 중 {same}개 동일"})
    # ---- C: (회사, 종목_표준, 지표, 연간/분기 열) 값이 공시마다 다른가
    byc = defaultdict(dict)
    for r in final["C"]:
        if r["값"] is None:
            continue
        kind = r["구간"]
        yd = int(r["공시분기"][:4])
        if kind == "당해누적":
            if not r["공시분기"].endswith("4Q"):
                continue                 # 2Q 공시의 '당해 누적' 은 4Q 공시의 연간과 다른 개념
            kind = "연간"
        if kind not in ("연간",) and not re.fullmatch(r"[1-4]분기", kind):
            continue
        byc[(r["원보험사코드"], r["종목_표준"] or r["종목"], r["지표"], r["연도"], kind)][r["공시분기"]] = r
    for key, d in sorted(byc.items(), key=lambda kv: str(kv[0])):
        qs = sorted(d)
        for i in range(len(qs)):
            for j in range(i + 1, len(qs)):
                a, b = d[qs[i]], d[qs[j]]
                tol = 0.5 * 10 ** (-min(_dec_of(a["값"], a.get("_dec")), _dec_of(b["값"], b.get("_dec")))) + 1e-9
                diff = abs(a["값"] - b["값"])
                if diff > tol:
                    out.append({"표": "C", "원보험사코드": key[0], "원수사명": meta.get(key[0], ("",))[0],
                                "기준연도_또는_열": f"{key[1]}/{key[2]}/{key[3]}년 {key[4]}", "공시분기_a": qs[i], "공시분기_b": qs[j], "비교셀수": 1, "차이셀수": 1,
                                "최대차이": round(diff, 6), "판정": "값차이(재작성 의심)", "예시": f"{a['값']}→{b['값']}"})
    return out


SURVEY_FIELDS = ["공시분기", "원보험사코드", "원수사명", "파일", "쪽수", "텍스트쪽수", "텍스트쪽비율", "앞100쪽_텍스트비율", "A_예상실제손해율쪽", "A_예실차머리쪽",
                 "B_머리쪽", "B_라벨쪽수", "B_예정유지비쪽", "C_합산비율쪽", "C_가격설정쪽", "산출하지않음쪽", "최적가정쪽", "원문위치주의"]


def build_survey(pdfs, idx, meta) -> list[dict]:
    rows = []
    for (q, code), path in sorted(pdfs.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        rec = idx[rel(path)]
        st = text_page_stats(rec)
        h = rec["hits"]
        lim = lambda v: ",".join(map(str, v[:12])) + ("…" if len(v) > 12 else "")  # noqa: E731
        rows.append({"공시분기": q, "원보험사코드": code, "원수사명": meta.get(code, ("",))[0], "파일": rel(path), "쪽수": st["pages"], "텍스트쪽수": st["text_pages"],
                     "텍스트쪽비율": round(st["text_ratio"], 3), "앞100쪽_텍스트비율": round(st["body_ratio"], 3), "A_예상실제손해율쪽": lim(h["A_cols"]), "A_예실차머리쪽": lim(h["A_head"]),
                     "B_머리쪽": lim(h["B_head"]), "B_라벨쪽수": len(h["B_lab"]), "B_예정유지비쪽": lim(h["B_next"]), "C_합산비율쪽": lim(h["C_kw"]), "C_가격설정쪽": lim(h["C_gs"]),
                     "산출하지않음쪽": lim(h["not_calc"]), "최적가정쪽": lim(h["opt"]),
                     "원문위치주의": "본문 스캔(텍스트 비율 낮음)" if st["body_ratio"] < 0.6 else ""})
    return rows


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    os.replace(tmp, path)


def sort_final(final: dict) -> None:
    po = {p: i for i, p in enumerate(PERIOD_ORDER)}
    final["A"].sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["기준연도"] or 0))
    final["B"].sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["기준연도"] or 0, {"합계": 0, "Non-Par": 1, "Direct-Par": 2, "Indirect-Par": 3}.get(r["구분"], 9),
                                    str(r["포트폴리오"]), {"예상보험금": 0, "위험보험료": 1, "비율": 2}.get(r["지표"], 9), po.get(r["경과기간"], 99)))
    final["C"].sort(key=lambda r: (r["원보험사코드"], r["공시분기"], str(r["종목"]), {"손해율": 0, "사업비율": 1, "합산비율": 2}.get(r["지표"], 9), r["연도"] or 0, r["분기"] or 0))


def census_summary(census: list[dict]) -> dict:
    c = Counter((r["표"].split("-")[0], r["상태"]) for r in census)
    return c


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", default="", help="회사코드 쉼표 구분(부분 실행: 파일은 쓰지 않고 요약만)")
    ap.add_argument("--quarters", default="", help="공시분기 쉼표 구분(예 2025.4Q)")
    ap.add_argument("--no-write", action="store_true", help="산출 파일을 쓰지 않는다")
    args = ap.parse_args()
    only = {c for c in args.only.split(",") if c} or None
    quarters = {c for c in args.quarters.split(",") if c} or None
    partial = bool(only or quarters)
    t0 = time.time()
    meta = load_company_meta()
    pdfs = discover_pdfs(meta)
    print(f"PDF {len(pdfs)}칸, 회사 {len({c for _, c in pdfs})}사")
    idx = load_index(pdfs)
    print(f"쪽 색인 {len(idx)}개 파일 ({time.time() - t0:.0f}s)")
    results = extract_all(pdfs, idx, meta, only, quarters)
    errs = {k: v["error"] for k, v in results.items() if "error" in v}
    if errs:
        print("추출 예외:", errs)
    vrows, vcen = load_vision(meta)
    vis = vision_to_canon(vrows, meta)
    final, census, flags_log = assemble(results, vis, vcen, meta, pdfs)
    if partial:
        keep = {(c, q) for (c, q) in results}
        final = {t: [r for r in rows if (r["원보험사코드"], r["공시분기"]) in keep] for t, rows in final.items()}
        census = [r for r in census if (r["원보험사코드"], r["공시분기"]) in keep]
    sort_final(final)
    diffs = build_diffs(final, meta)
    for d in diffs:        # 다른 기준연도인데 값이 같은 블록(KB손해 2025.4Q <2025> = <2024> 등)은 census 근거에도 플래그(인쇄 그대로)
        if "다른기준연도" in d["판정"]:
            m_ = re.match(r"(\d{4}) vs (\d{4})", str(d["기준연도_또는_열"]))
            if not m_:
                continue
            for r in census:
                if r["표"] == "B" and r["원보험사코드"] == d["원보험사코드"] and r["공시분기"] == d["공시분기_b"] and str(r["기준연도"]).split("|")[0] == m_.group(2):
                    r["근거"] += f"; 플래그 {d['판정']}: {d['예시']} (인쇄 그대로 보관, diffs.csv)"
    survey = build_survey(pdfs, idx, meta)
    print(f"행: A {len(final['A'])} / B {len(final['B'])} / C {len(final['C'])}   census {len(census)}행   diffs {len(diffs)}행   ({time.time() - t0:.0f}s)")
    cs = census_summary(census)
    for tb in ("A", "B", "C"):
        print(f"  표 {tb}: " + ", ".join(f"{st}={cs[(tb, st)]}" for st in STATUS_ORDER if cs.get((tb, st))))
    if not (partial or args.no_write):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        atomic_write_json(OUT_A, [clean_row(r) for r in final["A"]])
        atomic_write_json(OUT_B, [clean_row(r) for r in final["B"]])
        atomic_write_json(OUT_C, [clean_row(r) for r in final["C"]])
        write_csv(OUT_CENSUS, CENSUS_FIELDS, census)
        write_csv(OUT_SURVEY, SURVEY_FIELDS, survey)
        write_csv(OUT_DIFFS, DIFF_FIELDS, diffs)
        print("쓴 파일:", ", ".join(p.name for p in (OUT_A, OUT_B, OUT_C, OUT_CENSUS, OUT_SURVEY, OUT_DIFFS)))
    # 요약 목록
    bad = [r for r in census if r["상태"] in ("FILLED_CHECK_FLAGS", "PARSE_FAILED", "SCAN_PENDING", "UNREADABLE")]
    print(f"\n[주의 칸 {len(bad)}개]")
    for r in bad:
        print(f"  {r['상태']:<18} {r['원보험사코드']} {r['공시분기']} 표{r['표']} {r['기준연도']} :: {r['근거'][:170]}")
    dd = [d for d in diffs if "차이" in d["판정"] or "동일" in d["판정"] and d["표"] == "B" and "다른기준연도" in d["판정"] or "다른기준연도" in d["판정"]]
    print(f"\n[공시 간 값 차이 {len([d for d in diffs if d['차이셀수']])}건 / 다른기준연도 동일블록 {len([d for d in diffs if '다른기준연도' in d['판정']])}건]")
    for d in diffs:
        if d["차이셀수"] or "다른기준연도" in d["판정"]:
            print(f"  {d['표']} {d['원보험사코드']} {d['기준연도_또는_열']} {d['공시분기_a']} vs {d['공시분기_b']} :: {d['판정']} {d['차이셀수']}/{d['비교셀수']} :: {d['예시'][:120]}")
    print(f"\n완료 {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
