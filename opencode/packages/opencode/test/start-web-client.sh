#!/bin/bash
# OpenCode Web Client 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENCODE_BIN="$PROJECT_ROOT/dist/opencode-linux-x64/bin/opencode"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}OpenCode Web Client 启动脚本${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 检查 opencode 二进制文件
if [ ! -f "$OPENCODE_BIN" ]; then
    echo -e "${RED}错误: 找不到 opencode 二进制文件${NC}"
    echo -e "${YELLOW}请先运行: cd $PROJECT_ROOT && bun run script/build.ts --single${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} 找到 opencode 二进制文件"

# 检查端口是否被占用
PORT=${OPENCODE_PORT:-4096}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}!${NC} 端口 $PORT 已被使用"
    echo -e "${YELLOW}  如果 opencode 已在运行，可以直接打开浏览器访问 Web 客户端${NC}"
    echo ""
else
    echo -e "${GREEN}✓${NC} 端口 $PORT 可用"
    echo ""
    echo -e "${YELLOW}正在启动 opencode 远程服务器...${NC}"

    # 设置密码（可选）
    if [ -z "$OPENCODE_PASSWORD" ]; then
        echo -e "${YELLOW}警告: 未设置 OPENCODE_PASSWORD，服务器将不安全${NC}"
        echo -e "${YELLOW}      设置密码: export OPENCODE_PASSWORD=your_password${NC}"
    fi

    # 启动 opencode 服务器（后台运行）
    nohup "$OPENCODE_BIN" remote --port $PORT > /tmp/opencode-remote.log 2>&1 &
    OPENCODE_PID=$!

    echo -e "${GREEN}✓${NC} opencode 服务器已启动 (PID: $OPENCODE_PID)"
    echo -e "  日志文件: /tmp/opencode-remote.log"

    # 等待服务器启动
    echo -e "${YELLOW}等待服务器就绪...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:$PORT/remote/health >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} 服务器已就绪!"
            break
        fi
        sleep 1
    done
    echo ""
fi

# 打开 Web 客户端
WEB_CLIENT="$SCRIPT_DIR/web-client/index.html"

if [ ! -f "$WEB_CLIENT" ]; then
    echo -e "${RED}错误: 找不到 Web 客户端文件${NC}"
    exit 1
fi

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Web 客户端信息${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "服务器地址: ${BLUE}http://localhost:$PORT${NC}"
echo -e "Web 客户端: ${BLUE}$WEB_CLIENT${NC}"
echo ""
echo -e "使用方法:"
echo -e "  1. 在浏览器中打开: ${BLUE}file://$WEB_CLIENT${NC}"
echo -e "  2. 点击 \"连接\" 按钮"
echo -e "  3. 开始对话!"
echo ""
echo -e "${YELLOW}提示: 可以将 Web 客户端文件复制到任何位置使用${NC}"
echo ""

# 尝试自动打开浏览器
if command -v xdg-open >/dev/null 2>&1; then
    echo -e "${YELLOW}正在打开浏览器...${NC}"
    xdg-open "file://$WEB_CLIENT"
elif command -v open >/dev/null 2>&1; then
    echo -e "${YELLOW}正在打开浏览器...${NC}"
    open "file://$WEB_CLIENT"
else
    echo -e "${YELLOW}请手动在浏览器中打开 Web 客户端${NC}"
fi

echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器（如果已启动）${NC}"

# 等待用户中断
if [ -n "$OPENCODE_PID" ]; then
    trap "echo ''; echo -e '${YELLOW}正在停止服务器...${NC}'; kill $OPENCODE_PID 2>/dev/null; echo -e '${GREEN}✓${NC} 服务器已停止'; exit 0" INT TERM

    # 保持脚本运行
    wait $OPENCODE_PID 2>/dev/null
else
    echo -e "${YELLOW}服务器已在其他进程运行${NC}"
fi
