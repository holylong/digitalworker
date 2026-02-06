@echo off
REM OpenClaw Dev Launcher - Uses local development version with custom plugins
REM This allows you to run openclaw with your custom extensions like qqbot

set "OPENCLAW_ROOT=%~dp0"
node "%OPENCLAW_ROOT%openclaw.mjs" %*
