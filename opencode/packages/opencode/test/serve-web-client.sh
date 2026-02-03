#!/bin/bash
# 启动一个简单的 HTTP 服务器来托管 Web 客户端

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_CLIENT_DIR="$SCRIPT_DIR/web-client"
PORT=${WEB_CLIENT_PORT:-8080}

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Web 客户端 HTTP 服务器${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

if [ ! -d "$WEB_CLIENT_DIR" ]; then
    echo "错误: 找不到 web-client 目录"
    exit 1
fi

echo -e "${GREEN}Web 客户端目录:${NC} $WEB_CLIENT_DIR"
echo -e "${GREEN}服务器地址:${NC} http://localhost:$PORT"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo ""

# 检查可用的 HTTP 服务器
if command -v python3 >/dev/null 2>&1; then
    echo -e "${GREEN}使用 Python 3 启动服务器...${NC}"
    cd "$WEB_CLIENT_DIR"
    python3 -m http.server $PORT
elif command -v python >/dev/null 2>&1; then
    echo -e "${GREEN}使用 Python 2 启动服务器...${NC}"
    cd "$WEB_CLIENT_DIR"
    python -m SimpleHTTPServer $PORT
elif command -v php >/dev/null 2>&1; then
    echo -e "${GREEN}使用 PHP 启动服务器...${NC}"
    cd "$WEB_CLIENT_DIR"
    php -S localhost:$PORT
else
    echo "错误: 找不到可用的 HTTP 服务器"
    echo "请安装 Python 或 PHP"
    exit 1
fi
