# Security Cleanup Steps — Automated helper

I created a PowerShell helper script `scripts/clean_and_purge_secrets.ps1` to automate committing sanitized changes and purging a leaked secret from git history using BFG.

Before you run the script:

1. **Rotate the exposed API key now** in Google Cloud Console / AI Studio and create a new key. This script assumes you have already rotated/revoked the leaked key before purging history.
2. **Coordinate with collaborators**: This script rewrites git history and force-pushes — all collaborators must re-clone the repository after the operation.

How to run (from a PowerShell prompt):

```powershell
cd C:\path\to\repo\AntiGravity\iOSGeminiApp
pwsh .\scripts\clean_and_purge_secrets.ps1
```

The script will:
- Commit the sanitized changes I already prepared (placeholders, .gitignore, gitleaks workflow).
- Prompt you to confirm you rotated/revoked the leaked key.
- Ask for the leaked secret string (entered securely) and run BFG to replace it with `***REMOVED***` in history.
- Force-push the cleaned history back to origin.

After the script completes:
- Replace the compromised secret in GitHub Actions Secrets with the new rotated key.
- Ask all collaborators to re-clone the repo.
- Optionally run `gitleaks` CI to confirm no leaks remain.

If you'd like, I can also prepare an alternative script that uses `git-filter-repo` instead of BFG — tell me which you prefer.