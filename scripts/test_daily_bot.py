#!/usr/bin/env python3
"""Simple test runner that executes daily_bot.py with --dry-run and checks exit code.
Usage: python scripts/test_daily_bot.py
"""
import subprocess
import sys
import os

script = os.path.join(os.path.dirname(__file__), '..', 'daily_bot.py')
script = os.path.abspath(script)

print(f"Running dry-run test for: {script}")
proc = subprocess.run([sys.executable, script, '--dry-run', '--mock'], capture_output=True, text=True)
print('--- STDOUT ---')
print(proc.stdout)
print('--- STDERR ---')
print(proc.stderr)
print('--- EXIT CODE ---')
print(proc.returncode)

if proc.returncode == 0:
    print("✅ Test passed: dry-run validation succeeded.")
    sys.exit(0)
else:
    print("❌ Test failed: dry-run validation failed. Inspect output above.")
    sys.exit(proc.returncode)