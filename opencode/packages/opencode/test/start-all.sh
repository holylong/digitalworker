#!/bin/bash
# OpenCode Web Client 完整启动脚本
# 同时启动 opencode 服务器和 Web 客户端 HTTP 服务器

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENCODE_BIN="$PROJECT_ROOT/dist/opencode-linux-x64/bin/opencode"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
OPENCODE_PORT=${OPENCODE_PORT:-4096}
WEB_PORT=${WEB_PORT:-8080}
OPENCODE_HOST=${OPENCODE_HOST:-0.0.0.0}

echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}OpenCode Web Client 完整启动${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""
echo -e "${BLUE}配置信息:${NC}"
echo -e "  OpenCode 端口: ${GREEN}$OPENCODE_PORT${NC}"
echo -e "  Web 客户端端口: ${GREEN}$WEB_PORT${NC}"
echo -e "  OpenCode 监听: ${GREEN}$OPENCODE_HOST${NC}"
echo ""

# 检查 opencode 二进制文件
if [ ! -f "$OPENCODE_BIN" ]; then
    echo -e "${RED}错误: 找不到 opencode 二进制文件${NC}"
    echo -e "${YELLOW}请先运行: cd $PROJECT_ROOT && bun run script/build.ts --single${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} 找到 opencode 二进制文件"
echo ""

# 检查端口是否已被占用
check_port() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
        echo -e "${YELLOW}⚠${NC} 端口 $port 已被占用 (PID: $pid)"
        echo -e "${YELLOW}  这意味着 $name 可能已经在运行${NC}"
        return 0
    fi
    return 1
}

# 检查服务是否已运行
OPENCODE_RUNNING=false
WEB_RUNNING=false

if check_port $OPENCODE_PORT "OpenCode 服务器"; then
    OPENCODE_RUNNING=true
fi

if check_port $WEB_PORT "Web 服务器"; then
    WEB_RUNNING=true
fi

if $OPENCODE_RUNNING && $WEB_RUNNING; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}服务已在运行！${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo -e "${BLUE}访问地址:${NC}"
    echo ""
    echo -e "  本地访问:"
    echo -e "    ${CYAN}http://localhost:$WEB_PORT${NC}"
    echo ""
    echo -e "  网络访问:"
    echo -e "    ${CYAN}http://$(hostname -I | awk '{print $1}'):$WEB_PORT${NC}"
    echo ""
    echo -e "${YELLOW}查看日志:${NC}"
    echo -e "  OpenCode: ${CYAN}tail -f /tmp/opencode-remote.log${NC}"
    echo -e "  Web 客户端: ${CYAN}tail -f /tmp/web-client.log${NC}"
    echo ""
    echo -e "${YELLOW}停止服务:${NC}"
    echo -e "  运行: ${CYAN}./stop-all.sh${NC}"
    echo ""
    exit 0
fi

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止本次启动的服务...${NC}"

    # 只停止本次脚本启动的进程
    if [ -n "$OPENCODE_PID" ]; then
        kill $OPENCODE_PID 2>/dev/null && echo -e "${GREEN}✓${NC} OpenCode 服务器已停止" || true
    fi

    if [ -n "$WEB_PID" ]; then
        kill $WEB_PID 2>/dev/null && echo -e "${GREEN}✓${NC} Web 服务器已停止" || true
    fi

    # 等待进程结束
    wait 2>/dev/null
    exit 0
}

trap cleanup INT TERM EXIT

# 启动 opencode 服务器（如果未运行）
if ! $OPENCODE_RUNNING; then
    echo -e "${YELLOW}正在启动 OpenCode 远程服务器...${NC}"
    if [ -z "$OPENCODE_PASSWORD" ]; then
        echo -e "${YELLOW}警告: 未设置 OPENCODE_PASSWORD，服务器将不安全${NC}"
        echo -e "${YELLOW}      设置密码: export OPENCODE_PASSWORD=your_password${NC}"
    fi

    nohup "$OPENCODE_BIN" remote --port $OPENCODE_PORT --hostname $OPENCODE_HOST > /tmp/opencode-remote.log 2>&1 &
    OPENCODE_PID=$!

    echo -e "${GREEN}✓${NC} OpenCode 服务器已启动 (PID: $OPENCODE_PID)"
    echo -e "  日志文件: ${BLUE}/tmp/opencode-remote.log${NC}"

    # 等待 OpenCode 服务器启动
    echo -e "${YELLOW}等待 OpenCode 服务器就绪...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:$OPENCODE_PORT/remote/health >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} OpenCode 服务器已就绪!"
            break
        fi
        sleep 1
    done
    echo ""
fi

# 启动 Web 客户端 HTTP 服务器（如果未运行）
if ! $WEB_RUNNING; then
    echo -e "${YELLOW}正在启动 Web 客户端 HTTP 服务器...${NC}"

    WEB_CLIENT_DIR="$SCRIPT_DIR/web-client"
    cd "$WEB_CLIENT_DIR"

    if command -v python3 >/dev/null 2>&1; then
        nohup python3 -m http.server $WEB_PORT > /tmp/web-client.log 2>&1 &
        WEB_PID=$!
        echo -e "${GREEN}✓${NC} Web 服务器已启动 (PID: $WEB_PID, Python 3)"
    elif command -v python >/dev/null 2>&1; then
        nohup python -m SimpleHTTPServer $WEB_PORT > /tmp/web-client.log 2>&1 &
        WEB_PID=$!
        echo -e "${GREEN}✓${NC} Web 服务器已启动 (PID: $WEB_PID, Python 2)"
    else
        echo -e "${RED}错误: 找不到 Python，无法启动 Web 服务器${NC}"
        echo -e "${YELLOW}请安装 Python: sudo apt-get install python3${NC}"
        exit 1
    fi

    echo -e "  日志文件: ${BLUE}/tmp/web-client.log${NC}"
    echo ""
fi

# 获取本机 IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}启动成功！${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${BLUE}访问地址:${NC}"
echo ""
echo -e "  本地访问:"
echo -e "    ${CYAN}http://localhost:$WEB_PORT${NC}"
echo ""
echo -e "  网络访问 (可以从其他设备访问):"
echo -e "    ${CYAN}http://$LOCAL_IP:$WEB_PORT${NC}"
echo ""
echo -e "${BLUE}OpenCode 服务器配置:${NC}"
echo -e "  地址: ${CYAN}http://localhost:$OPENCODE_PORT${NC}"
echo -e "  或使用 IP: ${CYAN}http://$LOCAL_IP:$OPENCODE_PORT${NC}"
echo ""
echo -e "${YELLOW}使用方法:${NC}"
echo -e "  1. 在浏览器中打开: ${CYAN}http://localhost:$WEB_PORT${NC}"
echo -e "  2. 在页面中配置:"
echo -e "     - 服务器地址: ${CYAN}http://$LOCAL_IP:$OPENCODE_PORT${NC}"
echo -e "     - 用户名: ${CYAN}opencode${NC}"
echo -e "     - 密码: ${CYAN}${OPENCODE_PASSWORD:+(已设置)}${NC}"
echo -e "  3. 点击 \"连接\" 按钮"
echo -e "  4. 开始对话!"
echo ""
echo -e "${YELLOW}查看实时日志:${NC}"
echo -e "  OpenCode: ${CYAN}tail -f /tmp/opencode-remote.log${NC}"
echo -e "  Web 客户端: ${CYAN}tail -f /tmp/web-client.log${NC}"
echo ""
echo -e "${YELLOW}停止服务:${NC}"
echo -e "  运行: ${CYAN}./stop-all.sh${NC}"
echo ""

# 尝试自动打开浏览器
if command -v xdg-open >/dev/null 2>&1; then
    echo -e "${YELLOW}正在打开浏览器...${NC}"
    sleep 1
    xdg-open "http://localhost:$WEB_PORT" 2>/dev/null &
elif command -v open >/dev/null 2>&1; then
    echo -e "${YELLOW}正在打开浏览器...${NC}"
    sleep 1
    open "http://localhost:$WEB_PORT" 2>/dev/null &
fi

echo ""
echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}服务运行中...${NC}"
echo -e "${YELLOW}按 Ctrl+C 查看菜单${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# 保持脚本运行，等待用户输入
while true; do
    echo -e "${CYAN}按 Enter 刷新状态，输入 'logs' 查看日志，输入 'stop' 停止服务，输入 'bg' 后台运行${NC}"
    read -t 300 input  # 5分钟超时

    if [ $? -ne 0 ]; then
        # 超时，继续等待
        continue
    fi

    case "$input" in
        stop)
            cleanup
            ;;
        logs)
            echo -e "${CYAN}=== OpenCode 服务器日志 (最近 20 行) ===${NC}"
            tail -20 /tmp/opencode-remote.log
            echo ""
            echo -e "${CYAN}=== Web 服务器日志 (最近 20 行) ===${NC}"
            tail -20 /tmp/web-client.log 2>/dev/null || echo "无日志"
            echo ""
            ;;
        bg)
            echo -e "${GREEN}切换到后台运行...${NC}"
            # 移除 EXIT trap，让脚本在后台继续运行
            trap - INT TERM EXIT
            disown
            exit 0
            ;;
        *)
            # 刷新状态
            clear
            echo -e "${CYAN}======================================${NC}"
            echo -e "${CYAN}OpenCode 服务状态${NC}"
            echo -e "${CYAN}======================================${NC}"
            echo ""

            # 检查 OpenCode 服务器
            if curl -s http://localhost:$OPENCODE_PORT/remote/health >/dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} OpenCode 服务器: ${GREEN}运行中${NC}"
                echo -e "  URL: ${CYAN}http://localhost:$OPENCODE_PORT${NC}"
            else
                echo -e "${RED}✗${NC} OpenCode 服务器: ${RED}已停止${NC}"
            fi
            echo ""

            # 检查 Web 服务器
            if lsof -Pi :$WEB_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} Web 服务器: ${GREEN}运行中${NC}"
                echo -e "  URL: ${CYAN}http://localhost:$WEB_PORT${NC}"
            else
                echo -e "${RED}✗${NC} Web 服务器: ${RED}已停止${NC}"
            fi
            echo ""
            ;;
    esac
done
