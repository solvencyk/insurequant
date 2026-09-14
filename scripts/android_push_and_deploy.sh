#!/usr/bin/env bash
# 안드로이드(Termux) 전용 — 번들 받아서 브랜치 push + main(라이브) 배포까지 한 번에.
#
# 왜 이게 필요한가 (2026-09-03):
#   작업 PC 가 보안 에이전트(eCrmHE-B_git / eCrmHE-B_ssh)에 막혀 깃허브로 못 나간다.
#   그래서 커밋은 작업 PC 에서 만들고, **업로드는 폰에서** 한다. owner 결정: 집 PC 안 쓰고
#   안드로이드로만 한다.
#
# 사용법 (Termux):
#   pkg install git
#   git clone https://github.com/solvencyk/insurequant.git   # 최초 1회
#   cd insurequant
#   bash scripts/android_push_and_deploy.sh ~/storage/downloads/insurequant_XX.bundle
#
#   브랜치만 올리고 라이브 배포는 안 할 때:
#   bash scripts/android_push_and_deploy.sh <번들> --no-deploy
#
#   **브랜치가 이미 origin 에 올라가 있을 때**(클라우드 세션이 직접 push 한 경우 등):
#   번들이 필요 없다 — origin 에서 바로 읽어 라이브 배포만 한다.
#   bash scripts/android_push_and_deploy.sh --from-origin --branch <브랜치명>
#
#   브랜치 지정(생략하면 아래 기본값). 기본값이 옛 브랜치로 굳어 있으면 엉뚱한 걸 배포하므로
#   스크립트가 매 실행 브랜치명을 인쇄하고, origin 에 없으면 중단한다.
#
# 인증: HTTPS 는 비밀번호가 아니라 **토큰(PAT)** 이다.
#   Username = solvencyk / Password = 토큰
#   매번 묻는 게 귀찮으면: git config --global credential.helper store  (최초 1회만 입력)
#
# 절대 하지 않는 것:
#   - `git show ... > file` / `Out-File` 류 리다이렉션으로 파일 옮기기.
#     2026-09-03 에 PowerShell 리다이렉션이 BOM 을 붙이고 긴 줄을 잘라 JSON 문자열 안에
#     개행을 넣었고, 라이브가 `Bad control character in string literal` 로 깨졌다.
#     -> 반드시 `git checkout <branch> -- <path>` 로 블롭을 그대로 가져온다.
#   - main 에 브랜치 통째 merge. main 은 slim 이라 수백만 줄 차이가 난다 -> cherry-push 만.

set -eu

# 배포 브랜치. 하드코딩 기본값은 반드시 썩는다 — 2026-09-14 기준으로 기본값이 옛
# fix/csm-product-segmented-columns 에 멈춰 있었고, 인자 없이 돌렸으면 엉뚱한 브랜치를
# 라이브에 올렸을 것이다. 그래서 **기본값을 없앴다**:
#   --from-origin → --branch (또는 DEPLOY_BRANCH) 필수
#   번들 모드     → 번들 안의 ref 에서 브랜치명을 읽는다(번들이 정답을 들고 있다)
BRANCH="${DEPLOY_BRANCH:-}"
# jp 비공개 프리뷰 (owner 2026-09-12): 저장소의 `jp/` 는 main 에서 아래 폴더명으로 배포한다(추측 불가 경로 + noindex).
# 공개 시점에는 이 값을 빈 문자열로 바꾸고, main 의 옛 비공개 폴더는 그 라운드에서 `git rm -r` 로 지운다.
# 주의: 이 저장소는 공개 repo 라 폴더명 자체는 repo 를 읽는 사람에게는 보인다 — "링크·검색으로 안 드러남" 수준의 비공개다.
JP_PRIVATE_DIR="jp-f9027362"
# 저장소 경로 -> main 배포 경로
deploy_path() {
  case "$1" in
    jp/*) if [ -n "$JP_PRIVATE_DIR" ]; then printf '%s/%s' "$JP_PRIVATE_DIR" "${1#jp/}"; else printf '%s' "$1"; fi ;;
    *) printf '%s' "$1" ;;
  esac
}
BUNDLE=""
FROM_ORIGIN=0
DEPLOY=1
while [ $# -gt 0 ]; do
  case "$1" in
    --from-origin) FROM_ORIGIN=1 ;;
    --no-deploy)   DEPLOY=0 ;;
    --branch)      shift; BRANCH="${1:-}" ;;
    --branch=*)    BRANCH="${1#--branch=}" ;;
    -*)            printf '모르는 옵션: %s\n' "$1" >&2; exit 2 ;;
    *)             BUNDLE="$1" ;;
  esac
  shift
done

die() { printf '\n[중단] %s\n' "$1" >&2; exit 1; }
step() { printf '\n=== %s ===\n' "$1"; }

cd "$(git rev-parse --show-toplevel)" || die "git 저장소 안에서 실행해라."

if [ "$FROM_ORIGIN" -eq 0 ]; then
  [ -n "$BUNDLE" ] || die "번들 파일 경로를 인자로 줘라(또는 --from-origin).
  예: bash scripts/android_push_and_deploy.sh ~/storage/downloads/insurequant_10commits.bundle
  브랜치가 이미 origin 에 있으면: bash scripts/android_push_and_deploy.sh --from-origin --branch <브랜치명>
  (다운로드 폴더가 안 보이면 먼저 termux-setup-storage 실행)"
  [ -f "$BUNDLE" ] || die "번들 파일이 없다: $BUNDLE"
  if [ -z "$BRANCH" ]; then
    # 번들이 브랜치명을 갖고 있다 — 썩은 하드코딩 기본값을 쓰느니 번들에서 읽는다.
    BRANCH=$(git bundle list-heads "$BUNDLE" 2>/dev/null | sed -n 's#^[0-9a-f]* refs/heads/##p')
    case "$BRANCH" in
      "") die "번들에 refs/heads/* 가 없다 — --branch 로 직접 지정해라." ;;
      *"
"*) die "번들에 브랜치가 여러 개다. --branch 로 하나만 골라라:
$BRANCH" ;;
    esac
    printf '번들에서 브랜치명을 읽었다: %s\n' "$BRANCH"
  fi
else
  [ -z "$BUNDLE" ] || die "--from-origin 과 번들 경로를 같이 주지 마라. 하나만 골라라."
  [ -n "$BRANCH" ] || die "--from-origin 은 브랜치명이 필요하다(기본값 없음 — 썩어서 없앴다):
  bash scripts/android_push_and_deploy.sh --from-origin --branch <브랜치명>
  (origin 의 브랜치 목록: git ls-remote --heads origin)"
fi

printf '\n배포 브랜치: %s%s\n' "$BRANCH" "$([ "$FROM_ORIGIN" -eq 1 ] && printf ' (origin 에서 직접, 번들 없음)')"

if [ "$FROM_ORIGIN" -eq 1 ]; then
  step "원격 동기화"
  git fetch origin "$BRANCH" main || die "fetch 실패 — 브랜치명이 맞나? ($BRANCH)"
  git rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1 \
    || die "origin 에 그 브랜치가 없다: $BRANCH  (git ls-remote --heads origin 로 확인)"
  # 로컬 브랜치를 origin 에 맞춘다(폰 클론은 작업 이력이 없으므로 -B 가 안전).
  git checkout -B "$BRANCH" "origin/$BRANCH" >/dev/null 2>&1 || die "브랜치 체크아웃 실패"
  printf '브랜치 동기: %s\n' "$(git rev-parse --short HEAD)"
else
  step "번들 검증"
  git bundle verify "$BUNDLE" >/dev/null 2>&1 || die "번들이 깨졌다. 다시 받아라."

  step "원격 동기화"
  git fetch origin "$BRANCH" main

  step "번들에서 커밋 가져오기"
  git fetch "$BUNDLE" "$BRANCH:bundle_tmp" -f

  step "브랜치에 반영"
  git checkout -B "$BRANCH" "origin/$BRANCH" >/dev/null 2>&1 || git checkout "$BRANCH"
  git merge --ff-only bundle_tmp || die "fast-forward 불가 — 브랜치가 갈라졌다. 작업 PC 에 알려라."
  git branch -D bundle_tmp >/dev/null 2>&1 || true

  step "브랜치 push"
  git push origin "$BRANCH" || die "push 실패. 인증은 토큰(PAT)이다 — 깃허브 비밀번호 아님."
  printf '브랜치 완료: %s\n' "$(git rev-parse --short HEAD)"
fi

[ "$DEPLOY" -eq 1 ] || { printf '\n--no-deploy 라 라이브 배포는 건너뛴다.\n'; exit 0; }

step "라이브 배포 대상 계산 (main 에 있는 파일 중 브랜치와 다른 것만)"
CHANGED=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  [ "$f" = ".gitignore" ] && continue
  src="$f"
  case "$f" in "$JP_PRIVATE_DIR"/*) [ -n "$JP_PRIVATE_DIR" ] && src="jp/${f#"$JP_PRIVATE_DIR"/}" ;; esac
  a=$(git rev-parse "origin/main:$f" 2>/dev/null) || continue
  b=$(git rev-parse "$BRANCH:$src" 2>/dev/null) || continue
  [ "$a" = "$b" ] || CHANGED="$CHANGED$src
"
done <<EOF
$(git -c core.quotePath=false ls-tree -r --name-only origin/main)
EOF

# main 에 아직 없는 신규 배포 파일 (HTML 이 참조하지 않아 위 순회에 안 걸린다 — 2026-09-11 발견:
# 위 루프는 origin/main 에 이미 있는 파일만 돌기 때문에 LICENSE 같은 신규 파일이 영원히 빠졌다).
# 여기 적힌 파일은 브랜치에 있고 main 에 없으면 배포 목록에 넣는다.
NEW_FILES="LICENSE theme.js jp/index.html jp/jesr_esr.json jp/jesr.html jp/jgaap.html jp/disclosure.html jp/jesr_app.js jp/jp.css jp/jesr_detail.json jp/terms.html jp/report-widget.ja.js"
for f in $NEW_FILES; do
  git rev-parse "origin/main:$(deploy_path "$f")" >/dev/null 2>&1 && continue
  git rev-parse "$BRANCH:$f" >/dev/null 2>&1 || continue
  CHANGED="$CHANGED$f
"
done

[ -n "$CHANGED" ] || { printf '배포할 변경 없음 — main 이 이미 최신이다.\n'; exit 0; }
printf '%s' "$CHANGED" | sed 's/^/  /'

step "격리 워크트리에서 배포"
WT="$(mktemp -d)/iq_main"
git worktree add --detach "$WT" origin/main >/dev/null 2>&1 || die "worktree 실패"
cleanup() { cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)" 2>/dev/null || true
            git worktree remove --force "$WT" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# 루프를 파이프에 넣지 마라 — 파이프 오른쪽은 서브셸이라 bad=1 도 exit 1 도 바깥으로
# 전달되지 않는다(2026-09-03 발견). BOM 사고를 막아 준 해시 검증이 그래서 무력했다.
# here-string 으로 돌려 같은 셸에서 실행한다.
( cd "$WT"
  git checkout -B main origin/main >/dev/null 2>&1
  # 비공개 프리뷰: main 에 공개 경로 jp/ 가 남아 있으면 지운다(첫 전환 라운드에만 해당).
  if [ -n "$JP_PRIVATE_DIR" ] && [ -d jp ]; then git rm -r -q jp; fi
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    git checkout "$BRANCH" -- "$f" || exit 1      # 리다이렉션 금지 — 블롭 그대로
    d=$(deploy_path "$f")
    if [ "$d" != "$f" ]; then mkdir -p "$(dirname "$d")"; git mv -f "$f" "$d" || exit 1; fi
  done <<< "$CHANGED"
  git add -A

  # 커밋 전에 blob 해시 대조 — 하나라도 다르면 중단
  bad=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    want=$(git rev-parse "$BRANCH:$f")
    got=$(git ls-files -s -- "$(deploy_path "$f")" | awk '{print $2}')
    if [ "$want" != "$got" ]; then
      printf '  불일치 %s (기대 %s / 실제 %s)
' "$f" "$want" "$got"; bad=1
    fi
  done <<< "$CHANGED"
  [ "$bad" -eq 0 ] || exit 1
  printf '  전 파일 블롭 일치
'

  git commit -m "deploy: $(printf '%s' "$CHANGED" | tr '\n' ' ' | sed 's/ *$//') 갱신" >/dev/null
  git push origin main
  printf '\n라이브 배포 완료: %s\n' "$(git rev-parse --short HEAD)"
) || die "배포 실패 — main 은 건드려지지 않았다."

step "라이브 확인 (몇 분 뒤)"
while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in
    *.json|*.css|*.js|*.html) printf '  https://www.insurequant.com/%s?cb=%s
' "$(deploy_path "$f")" "$RANDOM";;
  esac
done <<< "$CHANGED"
