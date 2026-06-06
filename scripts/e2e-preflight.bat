@echo off
REM Windows wrapper for scripts/e2e-preflight.sh (Git Bash required).
setlocal
set REPO_ROOT=%~dp0..
cd /d "%REPO_ROOT%"

where bash >nul 2>&1
if errorlevel 1 (
  echo e2e-preflight: ERROR: bash not found. Run from Git Bash or install Git for Windows.
  exit /b 1
)

bash "%REPO_ROOT%\scripts\e2e-preflight.sh" %*
exit /b %ERRORLEVEL%
