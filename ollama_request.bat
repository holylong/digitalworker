curl http://10.184.60.127:11434/v1/models

@echo off
chcp 65001 >nul  :: 设置控制台为UTF-8编码，避免中文乱码（可选）
setlocal enabledelayedexpansion

:: ========== 配置参数 ==========
set SERVER_IP=10.184.60.127
set PORT=11434
set BASE_URL=http://%SERVER_IP%:%PORT%/v1
set MODEL=llama2  :: 请替换为服务器上已拉取的模型名称
:: ==============================

echo 正在测试与Ollama服务器的连接...
echo.

:: 1. 测试连通性：获取模型列表
echo [1] 获取可用模型列表...
curl -s "%BASE_URL%/models"
if %errorlevel% neq 0 (
    echo 连接失败！请检查服务器地址、端口或防火墙设置。
    goto :end
)
echo.
echo.

:: 2. 发送聊天补全请求
echo [2] 发送聊天补全请求（模型：%MODEL%）...
:: 构造JSON请求体（注意Windows命令行中的引号转义）
set "JSON_REQUEST={\"model\": \"%MODEL%\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}], \"stream\": false}"

:: 使用curl发送POST请求
curl -s -X POST "%BASE_URL%/chat/completions" ^
  -H "Content-Type: application/json" ^
  -d "!JSON_REQUEST!"

if %errorlevel% equ 0 (
    echo.
    echo 请求成功。
) else (
    echo 请求失败。
)
echo.

:end
pause