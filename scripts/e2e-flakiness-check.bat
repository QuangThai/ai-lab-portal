@echo off
REM E2E flakiness detection pre-commit script (Windows)
REM Delegates to the unified Node.js check script

set "SCRIPT_DIR=%~dp0..\frontend\scripts"
node "%SCRIPT_DIR%\e2e-flakiness-check.cjs"
exit /b %ERRORLEVEL%
