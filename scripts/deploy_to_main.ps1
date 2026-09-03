<#
.SYNOPSIS
  작업 브랜치 -> main(라이브) 배포를 한 번에. 격리 워크트리 + 블롭 그대로 복사 + 해시 검증.

.WHY
  2026-09-03 에 이 절차를 손으로 하다 두 번 사고가 났다:
    1) `git show ... | Out-File -Encoding utf8` 로 파일을 옮겼더니 PowerShell 이 BOM 을 붙이고
       **긴 줄을 임의로 줄바꿈**해서 JSON 문자열 안에 개행이 들어갔다 -> 라이브에서
       `Bad control character in string literal` 로 페이지가 통째로 깨졌다.
    2) 그걸 되돌리느라 커밋이 두 개 더 쌓였고 Pages 빌드가 밀렸다.
  => JSON/xlsx 같은 파일은 **리다이렉션을 절대 거치지 않는다.** `git checkout <branch> -- <path>`
     로 블롭을 그대로 가져오고, 끝나고 blob 해시로 동일성을 확인한다.

.USAGE
  # 깃허브 접속이 되는 PC 에서, 저장소 루트에서:
  powershell -ExecutionPolicy Bypass -File scripts\deploy_to_main.ps1
  powershell -ExecutionPolicy Bypass -File scripts\deploy_to_main.ps1 -DryRun
  powershell -ExecutionPolicy Bypass -File scripts\deploy_to_main.ps1 -Message "deploy: ..."

.NOTES
  배포 대상은 자동 계산한다 — **main 에 이미 존재하는 파일** 중 작업 브랜치와 다른 것만.
  main 은 slim 이라 브랜치 전체를 merge 하면 안 된다(수백만 줄 차이). 그래서 cherry-push 다.
#>
[CmdletBinding()]
param(
    [string]$Branch = 'fix/csm-product-segmented-columns',
    [string]$Message,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
function Fail($m) { Write-Host "[중단] $m" -ForegroundColor Red; exit 1 }
function Step($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan }

$repo = (& git rev-parse --show-toplevel 2>$null)
if (-not $repo) { Fail "git 저장소 안에서 실행해라." }
Set-Location $repo

Step "원격 동기화"
& git fetch origin main $Branch
if ($LASTEXITCODE -ne 0) { Fail "fetch 실패 — 깃허브 접속이 되는 PC 에서 실행해야 한다." }

# main 에 존재하는 파일 목록 (배포 대상 후보)
$mainFiles = (& git ls-tree -r --name-only "origin/main") -split "`n" | Where-Object { $_ }
if (-not $mainFiles) { Fail "origin/main 파일 목록을 못 읽었다." }

Step "배포 대상 계산 (main 에 있는 파일 중 브랜치와 다른 것)"
$changed = @()
foreach ($f in $mainFiles) {
    if ($f -eq '.gitignore') { continue }          # 배포물 아님
    $a = (& git rev-parse "origin/main:$f" 2>$null)
    $b = (& git rev-parse "${Branch}:$f" 2>$null)
    if ($LASTEXITCODE -eq 0 -and $a -and $b -and ($a -ne $b)) { $changed += $f }
}
if ($changed.Count -eq 0) { Write-Host "배포할 변경 없음 — main 이 이미 최신이다."; exit 0 }
$changed | ForEach-Object { Write-Host "  $_" }

if ($DryRun) { Write-Host "`n[DryRun] 여기까지." -ForegroundColor Yellow; exit 0 }

Step "격리 워크트리 준비"
$wt = Join-Path ([IO.Path]::GetTempPath()) ("iq_main_" + (Get-Date -Format 'yyyyMMddHHmmss'))
& git worktree add --detach $wt "origin/main" | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "worktree 생성 실패" }

try {
    Push-Location $wt
    & git checkout -B main "origin/main" | Out-Null

    Step "파일 복사 (블롭 그대로 — 리다이렉션 금지)"
    foreach ($f in $changed) {
        & git checkout $Branch -- $f
        if ($LASTEXITCODE -ne 0) { Fail "checkout 실패: $f" }
        Write-Host "  복사 $f"
    }

    Step "무결성 검증 (blob 해시 대조)"
    & git add -- $changed
    $bad = @()
    foreach ($f in $changed) {
        $want = (& git rev-parse "${Branch}:$f")
        $got = (& git ls-files -s -- $f) -split '\s+' | Select-Object -Index 1
        if ($want -ne $got) { $bad += "$f (기대 $want / 실제 $got)" }
    }
    if ($bad.Count -gt 0) { $bad | ForEach-Object { Write-Host "  불일치 $_" -ForegroundColor Red }; Fail "블롭이 손상됐다 — 배포 중단" }
    Write-Host "  전 파일 블롭 일치" -ForegroundColor Green

    Step "커밋 & push"
    if (-not $Message) { $Message = "deploy: $(($changed | ForEach-Object { Split-Path $_ -Leaf }) -join ', ') 갱신" }
    & git commit -m $Message | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "commit 실패" }
    & git push origin main
    if ($LASTEXITCODE -ne 0) { Fail "push 실패 (인증은 토큰=PAT 이다. 깃허브 비밀번호 아님)" }

    $sha = (& git rev-parse --short HEAD)
    Write-Host "`n배포 완료: $sha" -ForegroundColor Green
    Write-Host "라이브 확인은 몇 분 뒤:" -ForegroundColor Yellow
    foreach ($f in $changed) {
        if ($f -like '*.json') { Write-Host "  https://www.insurequant.com/$($f -replace '\\','/')?cb=$(Get-Random)" }
    }
}
finally {
    Pop-Location
    & git worktree remove --force $wt 2>$null | Out-Null
}
