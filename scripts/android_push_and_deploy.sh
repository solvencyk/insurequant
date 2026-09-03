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

BRANCH="fix/csm-product-segmented-columns"
BUNDLE="${1:-}"
DEPLOY=1
[ "${2:-}" = "--no-deploy" ] && DEPLOY=0

die() { printf '\n[중단] %s\n' "$1" >&2; exit 1; }
step() { printf '\n=== %s ===\n' "$1"; }

[ -n "$BUNDLE" ] || die "번들 파일 경로를 인자로 줘라.
  예: bash scripts/android_push_and_deploy.sh ~/storage/downloads/insurequant_10commits.bundle
  (다운로드 폴더가 안 보이면 먼저 termux-setup-storage 실행)"
[ -f "$BUNDLE" ] || die "번들 파일이 없다: $BUNDLE"

cd "$(git rev-parse --show-toplevel)" || die "git 저장소 안에서 실행해라."

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

[ "$DEPLOY" -eq 1 ] || { printf '\n--no-deploy 라 라이브 배포는 건너뛴다.\n'; exit 0; }

step "라이브 배포 대상 계산 (main 에 있는 파일 중 브랜치와 다른 것만)"
CHANGED=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  [ "$f" = ".gitignore" ] && continue
  a=$(git rev-parse "origin/main:$f" 2>/dev/null) || continue
  b=$(git rev-parse "$BRANCH:$f" 2>/dev/null) || continue
  [ "$a" = "$b" ] || CHANGED="$CHANGED$f
"
done <<EOF
$(git ls-tree -r --name-only origin/main)
EOF

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
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    git checkout "$BRANCH" -- "$f" || exit 1      # 리다이렉션 금지 — 블롭 그대로
  done <<< "$CHANGED"
  git add -A

  # 커밋 전에 blob 해시 대조 — 하나라도 다르면 중단
  bad=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    want=$(git rev-parse "$BRANCH:$f")
    got=$(git ls-files -s -- "$f" | awk '{print $2}')
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
    *.json|*.css|*.js) printf '  https://www.insurequant.com/%s?cb=%s
' "$f" "$RANDOM";;
  esac
done <<< "$CHANGED"
