# Commit and push sanitized changes (simple helper)
# Usage: pwsh .\scripts\commit_sanitized_changes.ps1
set-strictmode -version latest

if (-not (Get-Command git -ErrorAction SilentlyContinue)){
    Write-Error "git not found in PATH. Please install Git for Windows or add it to PATH, then re-run this script."; exit 1
}

$repoRoot = (git rev-parse --show-toplevel) 2>$null
if (-not $repoRoot){ Write-Error "Not inside a git repo. Run this from inside a git repository."; exit 2 }
Set-Location $repoRoot
Write-Host "Repository root: $repoRoot" -ForegroundColor Green

Write-Host "Staging sanitized files..." -ForegroundColor Cyan
$files = @(
    ".gitignore",
    "list_models.py",
    "secrets.env",
    "secrets.env.template",
    ".github/workflows/secret-scan.yml",
    "README.md"
)

foreach ($f in $files){
    if (Test-Path $f){ git add $f }
}

$changes = git status --porcelain
if (-not $changes){
    Write-Host "No changes staged. Nothing to commit." -ForegroundColor Yellow
    exit 0
}

$branch = (git rev-parse --abbrev-ref HEAD)
Write-Host "Committing changes on branch $branch..." -ForegroundColor Cyan
git commit -m "chore(security): remove embedded Gemini key; add secret-scan and placeholders; add cleanup helper" -a || Write-Host "Commit may have failed or nothing to commit." -ForegroundColor Yellow

Write-Host "Pushing to origin/$branch..." -ForegroundColor Cyan
git push origin $branch
if ($LASTEXITCODE -ne 0){ Write-Error "Push failed. Check remote settings and credentials."; exit 3 }

Write-Host "✅ Changes pushed. Next: rotate keys and run history purge script when ready." -ForegroundColor Green
