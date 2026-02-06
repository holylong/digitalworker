@echo off
REM 使用本地开发版本并启用 qqbot 插件
REM 会临时修改配置文件，使用完成后恢复

set "CONFIG_FILE=%USERPROFILE%\.openclaw\openclaw.json"
set "BACKUP_FILE=%USERPROFILE%\.openclaw\openclaw.json.backup"

REM 备份当前配置
copy "%CONFIG_FILE%" "%BACKUP_FILE%" >nul 2>&1

REM 检查是否已经有 plugins 配置
findstr /C:"\"plugins\"" "%CONFIG_FILE%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Plugins config already exists, skipping...
) else (
    echo Adding qqbot plugin config...
    powershell -Command "$content = Get-Content '%CONFIG_FILE%' -Raw; $content = $content -replace '(\s*)\}', ',`n  \"plugins\": {`n    \"enabled\": true,`n    \"allow\": [\"qqbot\"],`n    \"entries\": {`n      \"qqbot\": {`n        \"enabled\": true`n      }`n    }`n  }`n}'; Set-Content '%CONFIG_FILE%' $content -NoNewline"
)

echo Running with qqbot plugin enabled...
echo.

REM 运行命令
node "%~dp0openclaw.mjs" %*

echo.
echo Restoring original config...
copy "%BACKUP_FILE%" "%CONFIG_FILE%" >nul 2>&1
del "%BACKUP_FILE%" >nul 2>&1

echo Done.
