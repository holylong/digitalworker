#!/bin/bash
# OpenCode Web Client 停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}停止 OpenCode 服务${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

OPENCODE_PORT=${OPENCODE_PORT:-4096}
WEB_PORT=${WEB_PORT:-8080}

# 停止 OpenCode 服务器
OPENCODE_PID=$(lsof -ti :$OPENCODE_PORT 2>/dev/null)
if [ -n "$OPENCODE_PID" ]; then
    echo -e "${YELLOW}正在停止 OpenCode 服务器 (PID: $OPENCODE_PID)...${NC}"
    kill $OPENCODE_PID 2>/dev/null
    sleep 1

    # 如果进程还在，强制杀死
    if ps -p $OPENCODE_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}强制停止 OpenCode 服务器...${NC}"
        kill -9 $OPENCODE_PID 2>/dev/null
    fi

    echo -e "${GREEN}✓${NC} OpenCode 服务器已停止"
else
    echo -e "${YELLOW}⚠${NC} OpenCode 服务器未运行"
fi

# 停止 Web 服务器
WEB_PID=$(lsof -ti :$WEB_PORT 2>/dev/null)
if [ -n "$WEB_PID" ]; then
    echo -e "${YELLOW}正在停止 Web 服务器 (PID: $WEB_PID)...${NC}"
    kill $WEB_PID 2>/dev/null
    sleep 1

    # 如果进程还在，强制杀死
    if ps -p $WEB_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}强制停止 Web 服务器...${NC}"
        kill -9 $WEB_PID 2>/dev/null
    fi

    echo -e "${GREEN}✓${NC} Web 服务器已停止"
else
    echo -e "${YELLOW}⚠${NC} Web 服务器未运行"
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}所有服务已停止${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${YELLOW}查看日志:${NC}"
echo -e "  OpenCode: ${CYAN}tail -f /tmp/opencode-remote.log${NC}"
echo -e "  Web 客户端: ${CYAN}tail -f /tmp/web-client.log${NC}"
echo ""
