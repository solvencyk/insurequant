# -*- coding: utf-8 -*-
"""inbox 생명주기(`inbox/README.md` §64-71)를 **기계로 강제**한다.

계약 자체는 오래 전부터 문서에 있었지만 검사하는 것이 없어서 아무도 안 지켰다. 특히 4단계
("원 sender 가 `answered` 를 재확인해 `resolved` 로 닫고 `_resolved/` 로 옮긴다")가 통째로
비어서, 이미 끝난 스레드가 활성 폴더에 남아 매 세션 다시 읽히고 다시 언급된다.
이 저장소가 이미 배운 교훈이 그대로 적용된다: **honor 로 지켜지는 규칙은 안 지켜진다. 게이트로 만든다.**

나이는 **`created:` frontmatter(없으면 파일명 접두사)** 로 잰다 — mtime 은 나중에 누가 파일을
한 줄만 고쳐도 오늘로 리셋돼서, 65일 묵은 스레드가 "오늘 것"으로 보인다.

검사 항목
  E1 status 값이 스키마 밖         (RED)
  E2 status: resolved/superseded 인데 활성 폴더에 있음  (RED, --fix 로 자동 이동)
  E3 _resolved/ 안인데 status 가 미종결                 (RED, --fix 로 status 되돌림 없이 보고만)
  E4 status: answered 가 --answered-days 초과           (RED — 원 sender 가 닫을 차례)
  E5 status: open 이 --open-days 초과                   (RED — 방치)
  E6 필수 frontmatter 키 누락      (RED)

사용:
  python scripts/check_inbox_hygiene.py            # 검사만, 위반 있으면 exit 1
  python scripts/check_inbox_hygiene.py --fix      # E2 만 자동 수정(파일 이동) 후 재검사
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INBOX = REPO / "inbox"
RESOLVED = INBOX / "_resolved"
sys.stdout.reconfigure(encoding="utf-8")

OPEN_STATES = {"open", "answered"}
CLOSED_STATES = {"resolved", "superseded"}
VALID = OPEN_STATES | CLOSED_STATES
REQUIRED = ("from", "to", "created", "status")
STAMP = re.compile(r"^(\d{8})T(\d{4})Z")


def _field(text: str, key: str):
    m = re.search(rf"^{key}:\s*(\S+)", text[:1200], re.M)
    return m.group(1) if m else None


def _created(path: Path, text: str):
    """created: frontmatter -> 파일명 접두사 -> None. mtime 은 쓰지 않는다."""
    for cand in (_field(text, "created") or "", path.name):
        m = STAMP.match(cand)
        if m:
            try:
                return dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M")
            except ValueError:
                pass
    return None


def _scan():
    for p in sorted(INBOX.rglob("*.md")):
        if p.name == "README.md":
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        yield p, text, _field(text, "status"), _created(p, text)


def check(open_days: int, answered_days: int):
    now = dt.datetime.now()
    v: list[tuple[str, Path, str]] = []
    movable: list[Path] = []
    active = closed = 0

    for p, text, status, created in _scan():
        in_resolved = RESOLVED in p.parents
        # created 는 UTC 표기(...Z)이고 now 는 로컬이라, 방금 만든 티켓은 음수 나이가 나온다.
        # 0 으로 붙인다 — 갓 만든 스레드를 "-1일"로 보여주면 검사기가 고장 난 것처럼 보인다.
        age = max(0, (now - created).days) if created else None
        agestr = f"{age}d" if age is not None else "나이불명"

        missing = [k for k in REQUIRED if _field(text, k) is None]
        if missing:
            v.append(("E6 필수키 누락 " + ",".join(missing), p, agestr))

        if status not in VALID:
            v.append((f"E1 status 값 이상 '{status}'", p, agestr))
            continue

        if in_resolved:
            closed += 1
            if status in OPEN_STATES:
                v.append((f"E3 _resolved 안인데 status={status}", p, agestr))
            continue

        active += 1
        if status in CLOSED_STATES:
            v.append((f"E2 status={status} 인데 활성 폴더에 있음 (이동 필요)", p, agestr))
            movable.append(p)
        elif status == "answered" and age is not None and age > answered_days:
            sender = _field(text, "from")
            v.append((f"E4 answered {age}일 방치 — 원 sender '{sender}' 가 재확인·종결할 차례", p, agestr))
        elif status == "open" and age is not None and age > open_days:
            v.append((f"E5 open {age}일 방치", p, agestr))

    return v, movable, active, closed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="E2(종결인데 활성 폴더) 파일을 _resolved/ 로 이동")
    ap.add_argument("--open-days", type=int, default=14)
    ap.add_argument("--answered-days", type=int, default=7)
    ap.add_argument("--mechanical-only", action="store_true",
                    help="스키마·폴더 불일치(E1/E2/E3/E6)만 종료코드에 반영. "
                         "방치(E4/E5)는 출력만 — 진행 중인 스레드 하나가 push 를 막으면 안 된다.")
    args = ap.parse_args(argv)

    v, movable, active, closed = check(args.open_days, args.answered_days)

    if args.fix:
        # 폴더와 status 를 일치시킨다. 활성 폴더에 있으면 status 가 정본(옮긴다),
        # _resolved/ 에 있으면 폴더가 정본(누군가 의도적으로 아카이브한 것 = 종결)이라 status 를 맞춘다.
        RESOLVED.mkdir(parents=True, exist_ok=True)
        for p in movable:
            dest = RESOLVED / p.name
            if dest.exists():
                print(f"  SKIP 이미 있음: {dest.name}")
                continue
            p.rename(dest)
            print(f"  MOVED {p.parent.name}/{p.name} -> _resolved/")
        for p, text, status, _created in _scan():
            if RESOLVED not in p.parents or status in CLOSED_STATES:
                continue
            new = re.sub(r"^status:\s*\S+", "status: resolved", text, count=1, flags=re.M)
            if new != text:
                p.write_text(new, encoding="utf-8")
                print(f"  STATUS {status or '(없음)'} -> resolved : {p.name}")
        v, movable, active, closed = check(args.open_days, args.answered_days)

    mech = [x for x in v if x[0][:2] in ("E1", "E2", "E3", "E6")]
    stranded = [x for x in v if x[0][:2] in ("E4", "E5")]
    print(f"활성 {active} · 종결보관 {closed} · 위반 {len(v)}"
          f" (기계적 {len(mech)} · 방치 {len(stranded)})"
          f"  (기준: open>{args.open_days}일, answered>{args.answered_days}일)")
    for why, p, age in sorted(v, key=lambda x: x[0]):
        rel = p.relative_to(INBOX).as_posix()
        print(f"  [{age:>10}] {why}\n               {rel}")
    if mech:
        print("\n기계적 위반은 `--fix` 로 정합된다.")
    if stranded:
        print("방치 스레드는 자동 종결하지 않는다 — 원 sender 가 실제로 재확인해야 한다.")
    return 1 if (mech if args.mechanical_only else v) else 0


if __name__ == "__main__":
    sys.exit(main())
