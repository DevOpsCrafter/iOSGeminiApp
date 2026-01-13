<#
PowerShell helper to safely purge a leaked secret from a repository using BFG.

USAGE (run from a PowerShell prompt):
  1) Install Git and Java if missing.
  2) Open repo root and run: pwsh .\scripts\clean_and_purge_secrets.ps1
  3) Follow prompts. This will:
     - Commit any sanitized local changes
     - Prompt you to revoke/rotate the leaked key before proceeding
     - Create a mirror clone, download BFG, and run replacement (safe)
     - Force-push cleaned history to the remote

CAUTION: This script will rewrite git history and force-push. Coordinate with your team; everyone must re-clone after the operation.
#>

set-strictmode -version Latest

function Confirm-OrExit([string]$msg){
    $ans = Read-Host "$msg (y/N)"
    if ($ans -ne 'y' -and $ans -ne 'Y'){
        Write-Host "Cancelled by user." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Starting secret purge helper..." -ForegroundColor Cyan

# Basic checks
if (-not (Get-Command git -ErrorAction SilentlyContinue)){
    Write-Error "git is required but not found in PATH. Please install Git for Windows and re-run this script."; exit 2
}
if (-not (Get-Command java -ErrorAction SilentlyContinue)){
    Write-Error "Java (JRE) is required by BFG but not found. Please install a JRE and re-run."; exit 3
}

# Ensure we are in the repo root
$repoRoot = (git rev-parse --show-toplevel) 2>$null
if (-not $repoRoot){
    Write-Error "This folder is not inside a git repository. Run this script from within your repo."; exit 4
}
Set-Location $repoRoot
Write-Host "Repository root detected: $repoRoot" -ForegroundColor Green

# Show current status and prompt to review
git status --porcelain
Confirm-OrExit "I reviewed the working tree and want to proceed to commit sanitized changes"

# Commit sanitized changes (if any)
git add .gitignore list_models.py secrets.env secrets.env.template .github/workflows/secret-scan.yml README.md 2>$null
if ((git status --porcelain) -ne ''){
    git commit -m "chore(security): remove embedded API key, add secret-scan and .gitignore, placeholders for local secrets" -a || Write-Host "No commit was necessary or commit failed." -ForegroundColor Yellow
} else {
    Write-Host "No local changes to commit." -ForegroundColor Green
}

# Prompt user to rotate the exposed key BEFORE rewriting history
Write-Host "IMPORTANT: You must revoke/rotate the leaked key in Google Cloud (or AI Studio) BEFORE running the purge."
Confirm-OrExit "Have you rotated/revoked the leaked API key?"

# Prompt for the actual leaked token/value to remove
$secret = Read-Host -AsSecureString "Enter the leaked secret to purge from history (it will not be stored in the repo)"
$plainSecret = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret))
if (-not $plainSecret){ Write-Error "No secret provided. Exiting."; exit 5 }

# Mirror clone
$cwd = Get-Location
$mirrorDir = Join-Path $env:TEMP "repo-mirror-$(Get-Date -Format yyyyMMddHHmmss)"
Write-Host "Creating mirror clone at $mirrorDir" -ForegroundColor Cyan
git clone --mirror $(git config --get remote.origin.url) $mirrorDir
if ($LASTEXITCODE -ne 0){ Write-Error "Failed to create mirror clone."; exit 6 }

# Download BFG
$bfgUrl = 'https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar'
$bfgJar = Join-Path $mirrorDir 'bfg.jar'
Write-Host "Downloading BFG (this may take a moment)..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $bfgUrl -OutFile $bfgJar

# Create replacement file
$secretsFile = Join-Path $mirrorDir 'secrets-to-delete.txt'
Set-Content -Path $secretsFile -Value "# BFG replacement file - lines have the format: 'secret_to_remove==>replacement'`n$plainSecret==>***REMOVED***"

# Run BFG
Set-Location $mirrorDir
Write-Host "Running BFG to replace occurrences of the secret..." -ForegroundColor Cyan
java -jar $bfgJar --replace-text $secretsFile
if ($LASTEXITCODE -ne 0){ Write-Error "BFG run failed."; exit 7 }

# Cleanup and push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
Write-Host "Force-pushing the cleaned history to origin (remote)" -ForegroundColor Yellow
git push --force
if ($LASTEXITCODE -ne 0){ Write-Error "Force-push failed. Inspect the mirror repo at $mirrorDir"; exit 8 }

Write-Host "✅ History purge complete. IMPORTANT: All collaborators must re-clone the repo." -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  - Revoke any remaining compromised credentials."
Write-Host "  - Replace the old key in GitHub Secrets with a rotated key."
Write-Host "  - Ask all collaborators to re-clone the repository."