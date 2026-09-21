#!/usr/bin/env python3
"""배포 HTML 의 JS 가 **실행될 수 있는가** 를 검사한다 (2026-09-21 신설).

**왜 있나.** 2026-09-20 designer 커밋 `2dbc4ca` 가 `K-ICS.html` 의
`function IQP(){...}` 정의만 지우고 호출부 2곳(`renderSensDetail`)을 남겼다. 라이브에서
`ReferenceError: IQP is not defined` 로 금리민감도 패널이 39사 중 36사에서 죽은 채 하루 넘게
배포됐고, **모든 게이트는 초록이었다.** 데이터는 100% 정상이었다 — 순수한 렌더링 사망이다.
owner 가 눈으로 잡았다.

통과한 이유는 단순하다: `prepush_check.py` 의 어느 단계도 **배포 HTML 의 JS 를 읽지 않는다.**
`tests/test_deploy_assets.py` 는 keep-list(참조 파일 존재)·인라인 데이터 금지·BOM·삭제경로
참조만 본다. 즉 `CLAUDE.md` 불변식 1번("게이트가 검사하는 파일 = 사용자가 보는 파일")을
**데이터 축에서는** 지켜 왔지만 **화면 축에서는 한 번도 지킨 적이 없었다.**

**무엇을 검사하나 (`DEPLOYED_JS_UNDEFINED_CALL`).**
페이지가 로드하는 모든 스크립트(인라인 `<script>` + 같은 저장소의 `<script src>`)를 렉서로
토큰화해 ① **어디에든 바인딩되는 이름**(함수·클래스·var/let/const·파라미터·catch·화살표
파라미터·메서드 축약·`window.X =`)과 ② **값으로 읽히는 이름**을 모은다. ②는 세 자리다 —
호출 `name(`·`new name(` · 객체리터럴 값 `{k: name}` · 인자 `f(name)`·`f(a, name)`.
②−①−(브라우저 내장)−(CDN 전역) 이 비어 있지 않으면 **RED**.

**설계 원칙 — 오탐 0 을 위해 일부러 한쪽으로 치우쳐 있다.**
  · `defined` 는 **과대**추정한다(스코프를 안 본다. IIFE 안에서 정의하고 밖에서 부르는 진짜
    버그는 못 잡는다 = 거짓음성).
  · `refs` 는 **과소**추정한다(멤버 접근 `a.b` · 옵셔널체이닝 · 메서드 축약 정의는 뺀다.
    자유 식별자 전수 해석은 안 한다 — 오탐이 거기서 나온다).
두 방향 다 "못 잡는 쪽"으로 틀려 있고, 그래서 **잡았다면 진짜다.** 게이트는 오탐이 한 번
나는 순간 꺼지는 물건이라 이 비대칭이 설계의 전부다.

**노이즈 처리.** 문자열·템플릿리터럴·주석·정규식 리터럴은 렉서가 전부 제거한다 — 그래서
CSS `var()`/`rgba()`(문자열 안) · 한국어 산문(주석 안) 은 토큰에 아예 안 들어온다. 단
템플릿의 `${...}` **안쪽은 진짜 코드**라 재귀적으로 토큰화한다(거기서 함수를 부르는 코드가
실제로 있다). 렉서가 못 읽는 스크립트(미종료 문자열 등)는 조용히 넘기지 않고
`DEPLOYED_JS_UNSCANNABLE` **RED** 다 — fail-closed.

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_deployed_js.py
    (감사용) … scripts/validate_deployed_js.py --git-ref origin/main
exit 0 = RED 0 · exit 2 = RED 있음(push 차단).
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

# 배포 4종. `tests/test_deploy_assets.PAGES` 와 같은 목록이다(같은 배포본을 본다).
PAGES = ["index.html", "K-ICS.html", "IFRS17.html", "공시보고서.html"]

# ---------------------------------------------------------------------------
# 전역 allowlist
# ---------------------------------------------------------------------------
# CDN 스크립트가 심는 전역. **URL 조각 → 전역 이름**으로 선언한다. 페이지가 그 CDN 을 실제로
# 로드할 때만 허용된다 — `<script src>` 를 지우면 그 전역은 다시 미정의로 떨어진다(그게 이
# 게이트가 잡아야 하는 바로 그 사고형태다: 정의를 지우고 호출을 남기는 것).
CDN_GLOBALS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("chart.umd.js", ("Chart",)),
    ("chartjs-plugin-annotation", ("ChartAnnotation",)),
    ("echarts", ("echarts",)),
    ("xlsx.full.min.js", ("XLSX",)),
)

# 브라우저·ECMAScript 내장 중 **호출/생성자 위치에 나타나는** 것들. 멤버 접근만 하는 것
# (`Math.max` · `JSON.parse` · `console.log`)은 이 게이트가 애초에 안 보므로 넣을 필요가 없다.
BROWSER_GLOBALS = frozenset("""
Array ArrayBuffer AbortController Blob Boolean BigInt CustomEvent DataView Date
DocumentFragment Error EvalError Event FileReader Float32Array Float64Array FormData
Function Headers Image Int8Array Int16Array Int32Array IntersectionObserver Intl
Map MutationObserver Number Object Promise Proxy Range RangeError ReferenceError RegExp
Request Response ResizeObserver Set SharedWorker String Symbol SyntaxError TextDecoder
TextEncoder TypeError URIError URL URLSearchParams Uint8Array Uint16Array Uint32Array
Uint8ClampedArray WeakMap WeakRef WeakSet Worker XMLHttpRequest
alert atob btoa cancelAnimationFrame clearInterval clearTimeout confirm decodeURI
decodeURIComponent encodeURI encodeURIComponent escape eval fetch getComputedStyle
isFinite isNaN matchMedia parseFloat parseInt print prompt queueMicrotask
requestAnimationFrame requestIdleCallback setInterval setTimeout structuredClone unescape
console document history localStorage location navigator performance screen sessionStorage
window globalThis self top parent frames crypto
""".split())

# 예약어·문맥키워드. 호출 판정에서 뺀다(`if(` · `for(` · `catch(` 가 호출로 읽히면 안 된다).
# `get`/`set`/`of`/`async` 같은 문맥키워드도 넣는다 — 같은 이름의 진짜 함수를 놓치는 쪽
# (거짓음성)이지 오탐 쪽이 아니다.
RESERVED = frozenset("""
await async break case catch class const continue debugger default delete do else enum
export extends false finally for from function get if implements import in instanceof
interface let new null of package private protected public return set static super switch
this throw true try typeof undefined var void while with yield arguments
""".split())

# 정규식 리터럴이 올 수 있는 직전 키워드. 이 외에 직전 토큰이 이름·숫자·`)`·`]`·`}` 면
# `/` 는 나눗셈으로 읽는다(안전한 쪽 — 코드를 통째로 삼키지 않는다).
_REGEX_PREV_KW = frozenset(
    "return typeof instanceof in of new delete void case do else yield await throw".split())

_ID_START = re.compile(r"[A-Za-z_$\u0080-\uffff]")
_ID_RE = re.compile(r"[A-Za-z_$\u0080-\uffff][A-Za-z0-9_$\u0080-\uffff]*")
_NUM_RE = re.compile(r"(0[xXbBoO][0-9a-fA-F_]+|(\d[\d_]*)?\.?\d[\d_]*([eE][+-]?\d+)?)n?")
# 길이 긴 것부터 — `=>` 가 `=`+`>` 로, `?.` 가 `?`+`.` 로 쪼개지면 판정이 틀어진다.
_PUNCT = tuple(sorted(
    (">>>=", "...", "===", "!==", "**=", "<<=", ">>=", ">>>", "&&=", "||=", "??=",
     "=>", "==", "!=", "<=", ">=", "&&", "||", "??", "?.", "++", "--", "+=", "-=",
     "*=", "/=", "%=", "&=", "|=", "^=", "**", "<<", ">>",
     "{", "}", "(", ")", "[", "]", ";", ",", ".", ":", "?", "=", "+", "-", "*", "/",
     "%", "&", "|", "^", "!", "~", "<", ">", "#", "@"),
    key=len, reverse=True))


class ScanError(ValueError):
    """렉서가 소스를 끝까지 못 읽었다 — 조용히 넘기지 않고 RED 로 올린다."""


@dataclass(frozen=True)
class Tok:
    kind: str      # "name" | "num" | "punct"
    val: str
    line: int


def _tmpl_body(src: str, i: int) -> tuple[int, bool]:
    """템플릿 리터럴 본문을 `${` 또는 종료 백틱까지 읽는다 → (다음위치, 표현식시작여부)."""
    n = len(src)
    while i < n:
        c = src[i]
        if c == "\\":
            i += 2
            continue
        if c == "`":
            return i + 1, False
        if c == "$" and i + 1 < n and src[i + 1] == "{":
            return i + 2, True
        i += 1
    raise ScanError("템플릿 리터럴이 종료되지 않았다")


def scan_tokens(src: str) -> list[Tok]:
    """JS 소스 → 토큰. 주석·문자열·정규식은 버리고 템플릿의 `${}` 안쪽만 살려 재귀 처리한다."""
    toks: list[Tok] = []
    i, n, line = 0, len(src), 1
    brace_depth = 0
    tmpl_stack: list[int] = []        # `${` 가 열린 시점의 brace_depth

    def prev() -> Tok | None:
        return toks[-1] if toks else None

    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c in " \t\r\f\v\u00a0\ufeff":
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                raise ScanError("블록 주석이 종료되지 않았다")
            line += src.count("\n", i, j)
            i = j + 2
            continue
        if c in "'\"":
            j, q = i + 1, c
            while j < n and src[j] != q:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "\n":
                    raise ScanError("문자열 리터럴이 줄 안에서 종료되지 않았다")
                j += 1
            if j >= n:
                raise ScanError("문자열 리터럴이 종료되지 않았다")
            i = j + 1
            continue
        if c == "`":
            j, expr = _tmpl_body(src, i + 1)
            line += src.count("\n", i, j)
            if expr:
                tmpl_stack.append(brace_depth)
            i = j
            continue
        if c == "/":
            p = prev()
            div = p is not None and (
                p.kind in ("num",)
                or (p.kind == "name" and p.val not in _REGEX_PREV_KW)
                or (p.kind == "punct" and p.val in (")", "]", "}", "++", "--")))
            if not div:
                j = i + 1
                in_class = False
                while j < n:
                    d = src[j]
                    if d == "\\":
                        j += 2
                        continue
                    if d == "\n":
                        raise ScanError("정규식 리터럴이 줄 안에서 종료되지 않았다")
                    if d == "[":
                        in_class = True
                    elif d == "]":
                        in_class = False
                    elif d == "/" and not in_class:
                        break
                    j += 1
                if j >= n:
                    raise ScanError("정규식 리터럴이 종료되지 않았다")
                j += 1
                while j < n and _ID_START.match(src[j] or " "):   # 플래그
                    j += 1
                i = j
                continue
        if _ID_START.match(c):
            m = _ID_RE.match(src, i)
            toks.append(Tok("name", m.group(0), line))
            i = m.end()
            continue
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            m = _NUM_RE.match(src, i)
            if m:
                toks.append(Tok("num", m.group(0), line))
                i = m.end()
                continue
        for op in _PUNCT:
            if src.startswith(op, i):
                if op == "{":
                    brace_depth += 1
                elif op == "}":
                    if tmpl_stack and brace_depth == tmpl_stack[-1]:
                        # 템플릿 표현식의 닫는 중괄호 — 리터럴 본문으로 돌아간다.
                        tmpl_stack.pop()
                        j, expr = _tmpl_body(src, i + 1)
                        line += src.count("\n", i, j)
                        if expr:
                            tmpl_stack.append(brace_depth)
                        i = j
                        break
                    brace_depth -= 1
                toks.append(Tok("punct", op, line))
                i += len(op)
                break
        else:
            raise ScanError(f"모르는 문자 {c!r} (line {line})")
    if tmpl_stack:
        raise ScanError("템플릿 표현식이 닫히지 않았다")
    return toks


def _match(toks: list[Tok], i: int, open_: str, close: str) -> int:
    """`toks[i]` 가 여는 괄호일 때 짝 인덱스. 못 찾으면 len(toks)."""
    d = 0
    for j in range(i, len(toks)):
        if toks[j].kind == "punct":
            if toks[j].val == open_:
                d += 1
            elif toks[j].val == close:
                d -= 1
                if d == 0:
                    return j
    return len(toks)


def _names_in(toks: list[Tok], a: int, b: int) -> set[str]:
    """`a..b` 구간의 이름 토큰(예약어 제외). 구조분해 파라미터를 통째로 바인딩으로 본다 —
    과대추정이지만 **오탐이 아니라 거짓음성 쪽**이라 의도한 방향이다."""
    return {t.val for t in toks[a:b]
            if t.kind == "name" and t.val not in RESERVED}


def collect(toks: list[Tok]) -> tuple[set[str], list[tuple[str, int]]]:
    """토큰 → (바인딩되는 이름 전부, 호출 위치의 (이름, 줄) 목록)."""
    defined: set[str] = set()
    calls: list[tuple[str, int]] = []
    n = len(toks)

    def tk(i: int) -> Tok | None:
        return toks[i] if 0 <= i < n else None

    def is_p(i: int, *vals: str) -> bool:
        t = tk(i)
        return t is not None and t.kind == "punct" and t.val in vals

    i = 0
    while i < n:
        t = toks[i]
        if t.kind != "name":
            # 화살표 함수 파라미터는 `=>` 를 보고 **뒤로** 읽어야 한다.
            if t.kind == "punct" and t.val == "=>":
                if is_p(i - 1, ")"):
                    d, j = 0, i - 1
                    while j >= 0:                       # 짝 `(` 를 역방향으로
                        if toks[j].kind == "punct":
                            if toks[j].val == ")":
                                d += 1
                            elif toks[j].val == "(":
                                d -= 1
                                if d == 0:
                                    break
                        j -= 1
                    if j >= 0:
                        defined |= _names_in(toks, j + 1, i - 1)
                else:
                    p = tk(i - 1)
                    if p is not None and p.kind == "name" and p.val not in RESERVED:
                        defined.add(p.val)
            i += 1
            continue

        v = t.val
        # 키워드처럼 생겼지만 **멤버 이름**인 자리(`p.catch(cb)` · `obj.class`)는 키워드 규칙을
        # 태우면 안 된다. 실측(2026-09-21): `.catch(err => {…})` 를 catch 절로 읽어 콜백 본문의
        # 이름 전부를 바인딩으로 삼켰고, 그 결과 `render`·`setMapStatus`·`fetchFirst` 의 정의를
        # 지워도 게이트가 안 물었다(거짓음성 3건). 스코프를 안 보는 설계라 `defined` 과대추정은
        # 원래 의도지만, **한 토큰이 함수 하나를 통째로 삼키는 것**은 의도가 아니다.
        kw_ok = not (tk(i - 1) is not None and toks[i - 1].kind == "punct"
                     and toks[i - 1].val in (".", "?.", "#"))
        if v == "function" and kw_ok:
            j = i + 1
            nx = tk(j)
            if nx is not None and nx.kind == "name" and nx.val not in RESERVED:
                defined.add(nx.val)
                j += 1
            if is_p(j, "("):
                end = _match(toks, j, "(", ")")
                defined |= _names_in(toks, j + 1, end)
                i = end + 1
                continue
            i = j
            continue

        if v == "class" and kw_ok:
            nx = tk(i + 1)
            if nx is not None and nx.kind == "name" and nx.val not in RESERVED:
                defined.add(nx.val)
            i += 2
            continue

        if v == "catch" and kw_ok and is_p(i + 1, "("):
            end = _match(toks, i + 1, "(", ")")
            defined |= _names_in(toks, i + 2, end)
            i = end + 1
            continue

        if v in ("var", "let", "const") and kw_ok:
            k = i + 1
            while k < n:
                nx = tk(k)
                if nx is None:
                    break
                if nx.kind == "name" and nx.val not in RESERVED:
                    defined.add(nx.val)
                    k += 1
                elif nx.kind == "punct" and nx.val in ("{", "["):
                    close = "}" if nx.val == "{" else "]"
                    end = _match(toks, k, nx.val, close)
                    defined |= _names_in(toks, k + 1, end)
                    k = end + 1
                else:
                    break
                # 초기화식은 **건너뛰지 않는다** — 그 안의 호출을 세야 하므로 다음 선언자
                # 구분자까지 위치만 찾고, 본문은 바깥 루프가 그대로 다시 훑는다.
                d = 0
                j = k
                while j < n:
                    tj = toks[j]
                    if tj.kind == "punct":
                        if tj.val in ("(", "[", "{"):
                            d += 1
                        elif tj.val in (")", "]", "}"):
                            if d == 0:
                                break
                            d -= 1
                        elif d == 0 and tj.val in (",", ";"):
                            break
                    j += 1
                if j < n and toks[j].kind == "punct" and toks[j].val == ",":
                    k = j + 1
                    continue
                break
            i += 1
            continue

        # `window.X = …` / `globalThis.X = …` → 전역 X 를 만든다.
        if v in ("window", "globalThis", "self") and is_p(i + 1, "."):
            nx = tk(i + 2)
            if nx is not None and nx.kind == "name" and is_p(i + 3, "="):
                defined.add(nx.val)

        prev_t = tk(i - 1)
        member = prev_t is not None and prev_t.kind == "punct" and prev_t.val in (".", "?.", "#")

        # 선언 없는 전역 할당(`foo = 1`) 도 바인딩이다. 멤버 대입은 제외.
        if not member and v not in RESERVED and is_p(i + 1, "="):
            defined.add(v)

        if not member and v not in RESERVED and is_p(i + 1, "("):
            end = _match(toks, i + 1, "(", ")")
            after = tk(end + 1)
            if after is not None and after.kind == "punct" and after.val == "{":
                # `foo(a){ … }` = 객체 메서드 축약 / 클래스 메서드 / get·set 접근자.
                # 호출이 아니라 **정의**다.
                defined.add(v)
            else:
                calls.append((v, t.line))
        elif (not member and v not in RESERVED
                and ((is_p(i - 1, ":") and is_p(i + 1, ",", "}"))
                     or (is_p(i - 1, "(", ",") and is_p(i + 1, ")", ",")))):
            # **값으로 건네지는 함수 참조** — `{ get: plOciResidual }` · `{ onClick: redraw }`.
            # 호출 괄호가 없을 뿐 정의가 사라지면 그 자리에서 똑같이 ReferenceError 다
            # (실측: IFRS17.html L781 `get:plOciResidual` · L1398 `requestAnimationFrame(step)`).
            # 분해대입(`const {값: v} = row`)은 바인딩이지 참조지만, 그 v 는 var/param 규칙의
            # 과대추정으로 이미 `defined` 에 들어가 있어 오탐이 안 난다(전수 실측 RED=0).
            calls.append((v, t.line))
        i += 1
    return defined, calls


# ---------------------------------------------------------------------------
# HTML → 스크립트 조각
# ---------------------------------------------------------------------------
# 비탐욕 매칭이라 JS 문자열 안의 **이스케이프된** 닫는 태그(`<\/script>`)는 안 걸린다 —
# 그게 그 이스케이프를 쓰는 이유다. 이스케이프 안 한 리터럴은 브라우저도 똑같이 블록을 끊으므로
# 여기서 끊는 것이 오히려 브라우저와 같은 해석이다.
_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script\s*>", re.S | re.I)
_ATTR_RE = re.compile(r"""(\w[\w-]*)\s*=\s*["']([^"']*)["']""")
_JS_TYPES = ("", "text/javascript", "application/javascript", "module")


@dataclass
class Piece:
    label: str        # 화면에 찍는 이름
    src: str          # JS 소스
    base_line: int    # 페이지 파일 기준 시작 줄(인라인만 의미 있다)


@dataclass
class Finding:
    rule: str
    page: str
    where: str
    name: str
    line: int
    message: str


_GIT_READ: dict[tuple[str, str], str | None] = {}


def _read(rel: str, git_ref: str | None) -> str | None:
    if git_ref:
        # 같은 .js 를 페이지 수만큼 다시 꺼내면 git 호출이 20회가 된다(Windows 에서 6초).
        # ref 는 실행 중 안 바뀌므로 메모이즈한다.
        key = (git_ref, rel)
        if key not in _GIT_READ:
            p = subprocess.run(["git", "show", f"{git_ref}:{rel}"], cwd=str(ROOT),
                               capture_output=True)
            _GIT_READ[key] = (None if p.returncode != 0
                              else p.stdout.decode("utf-8", errors="replace"))
        return _GIT_READ[key]
    f = ROOT / rel
    if not f.exists():
        return None
    return f.read_text(encoding="utf-8")


def page_pieces(page: str, html: str, git_ref: str | None):
    """(JS 조각들, CDN 전역, 없는 로컬 스크립트) — 페이지가 실제로 로드하는 것만."""
    pieces: list[Piece] = []
    cdn: set[str] = set()
    missing: list[str] = []
    for m in _SCRIPT_RE.finditer(html):
        attrs = dict(_ATTR_RE.findall(m.group(1)))
        if attrs.get("type", "").lower() not in _JS_TYPES:
            continue                       # JSON·템플릿 블록은 JS 가 아니다
        src_url = attrs.get("src", "").strip()
        if not src_url:
            base_line = html.count("\n", 0, m.start(2)) + 1
            pieces.append(Piece(f"{page}(inline @{base_line})", m.group(2), base_line))
            continue
        if src_url.startswith(("http://", "https://", "//")):
            for frag, names in CDN_GLOBALS:
                if frag in src_url:
                    cdn |= set(names)
            continue
        rel = src_url.split("?", 1)[0].lstrip("./")
        body = _read(rel, git_ref)
        if body is None:
            missing.append(rel)
            continue
        pieces.append(Piece(rel, body, 1))
    return pieces, cdn, missing


_ANALYSIS: dict[str, tuple[int, frozenset, tuple]] = {}


def _analyze(src: str) -> tuple[int, frozenset, tuple]:
    """`scan_tokens`+`collect` 를 소스 문자열로 메모이즈한다. 순수함수라 안전하고, 변이시험이
    한 페이지를 수백 번 재분석할 때 바뀌지 않는 외부 .js 를 다시 안 읽게 한다(13.6초 → 6초)."""
    got = _ANALYSIS.get(src)
    if got is None:
        toks = scan_tokens(src)
        d, c = collect(toks)
        got = (len(toks), frozenset(d), tuple(c))
        _ANALYSIS[src] = got
    return got


def check_page(page: str, git_ref: str | None = None,
               html: str | None = None) -> tuple[list[Finding], dict]:
    """`html=` 를 주면 디스크 대신 그 본문을 검사한다 — 회귀시험이 **저장소 파일을 건드리지
    않고** 변이(정의 삭제)를 걸 수 있게 하는 유일한 구멍이다(`tests/test_deployed_js_gate.py`).
    게이트 본체는 항상 `html=None` 으로 부른다(= 사용자가 보는 그 파일)."""
    if html is None:
        html = _read(page, git_ref)
    if html is None:
        return [], {"page": page, "skipped": True}
    pieces, cdn, missing = page_pieces(page, html, git_ref)
    findings = [Finding("DEPLOYED_JS_SCRIPT_MISSING", page, rel, rel, 0,
                        f"<script src=\"{rel}\"> 파일이 없다 — 그 페이지의 JS 는 통째로 안 돈다")
                for rel in missing]

    defined: set[str] = set(BROWSER_GLOBALS) | cdn
    calls: list[tuple[str, int, str]] = []
    scanned, n_tok = [], 0
    for pc in pieces:
        try:
            n_t, d, c = _analyze(pc.src)
        except ScanError as e:
            findings.append(Finding("DEPLOYED_JS_UNSCANNABLE", page, pc.label, "-", 0,
                                    f"렉서가 스크립트를 못 읽었다: {e}"))
            continue
        n_tok += n_t
        defined |= d
        off = pc.base_line - 1
        calls += [(name, ln + off, pc.label) for name, ln in c]
        scanned.append(pc.label)

    seen: set[tuple[str, int]] = set()
    for name, ln, label in calls:
        if name in defined or (name, ln) in seen:
            continue
        seen.add((name, ln))
        findings.append(Finding(
            "DEPLOYED_JS_UNDEFINED_CALL", page, label, name, ln,
            f"`{name}(…)` 를 부르는데 이 페이지의 어떤 스크립트에도 정의가 없다 "
            f"— 라이브에서 ReferenceError 로 그 렌더 경로가 통째로 죽는다"))
    stats = {"page": page, "skipped": False, "pieces": len(pieces), "scanned": len(scanned),
             "tokens": n_tok, "defined": len(defined), "calls": len(calls),
             "cdn": sorted(cdn)}
    return findings, stats


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    git_ref = None
    if "--git-ref" in argv:
        k = argv.index("--git-ref")
        if k + 1 >= len(argv):
            print("사용법: validate_deployed_js.py [--no-live] [--git-ref REF]")
            return 2                      # 인자 오류를 0 으로 돌려주면 그게 false-green 이다
        git_ref = argv[k + 1]
    unknown = [a for a in argv if a.startswith("-") and a not in ("--no-live", "--git-ref")]
    if unknown:
        print(f"알 수 없는 인자: {unknown}")
        print("사용법: validate_deployed_js.py [--no-live] [--git-ref REF]")
        return 2
    print("=" * 72)
    print("DEPLOYED JS RUNTIME GATE  (scripts/validate_deployed_js.py)")
    print(f"  대상 = {'git ' + git_ref if git_ref else '워킹트리'} · 배포 4종")
    print("=" * 72)
    red: list[Finding] = []
    for page in PAGES:
        f, st = check_page(page, git_ref)
        if st.get("skipped"):
            print(f"  {page}: (트리에 없음 — slim 워크트리)")
            continue
        print(f"  {page}: 스크립트 {st['scanned']}/{st['pieces']}개 · 토큰 {st['tokens']:,} · "
              f"바인딩 {st['defined']:,} · 참조지점 {st['calls']:,} · "
              f"CDN 전역 {','.join(st['cdn']) or '-'}")
        red += f
    if red:
        print("\n  RED:")
        for x in red:
            print(f"    [{x.rule}] {x.page}:{x.line}  {x.name}  ({x.where})")
            print(f"        {x.message}")
    print(f"\n  → RED={len(red)}  ({'BLOCK' if red else 'clear'})")
    if git_ref is None and "--no-live" not in argv:
        _live_audit()
    return 2 if red else 0


def _live_audit(ref: str = "origin/main") -> None:
    """**지금 라이브가 깨져 있는지**를 같이 인쇄한다 — 비차단, exit code 에 안 들어간다.

    왜 필요한가: 이 게이트는 "내가 밀려는 것"을 본다. 그런데 2026-09-21 사고의 본질은
    **이미 배포된 것이 하루 넘게 깨진 채였고 아무 기계도 그 말을 안 했다**는 것이다(owner 가
    눈으로 잡았다). 라이브 축을 차단으로 걸면 designer 가 main 에 고칠 때까지 무관한 작업까지
    전부 막히므로 일부러 정보로만 둔다. **비차단으로 남긴 이 판단이 UH-27 이고 후속 티켓이
    열려 있다** — "안 막는다" 를 조용히 하지 않으려고 매 실행 인쇄한다.
    """
    sha = subprocess.run(["git", "rev-parse", "--short", ref], cwd=str(ROOT),
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if sha.returncode != 0:
        print(f"\n  [라이브 감사] {ref} 를 못 읽는다(슬림/무리모트) — 생략. "
              f"'생략'은 '깨끗'이 아니다.")
        return
    when = subprocess.run(["git", "log", "-1", "--format=%cs", ref], cwd=str(ROOT),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    live: list[Finding] = []
    for page in PAGES:
        live += check_page(page, ref)[0]
    head = (f"\n  [라이브 감사 · 비차단] {ref}@{sha.stdout.strip()}"
            f"({(when.stdout or '').strip()}) RED={len(live)}")
    print(head)
    for x in live:
        print(f"      {x.page}:{x.line}  {x.name}  [{x.rule}]")
    if live:
        print("      ↑ **지금 사이트에서 이 렌더 경로가 죽어 있다.** 이 줄은 exit code 에 "
              "안 들어간다(UH-27) — 고치는 것은 designer 소관이고, 고친 커밋이 main 에 "
              "올라가면 저절로 사라진다.")


if __name__ == "__main__":
    raise SystemExit(main())
