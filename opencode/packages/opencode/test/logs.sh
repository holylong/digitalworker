#!/bin/bash
# OpenCode 日志查看脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}OpenCode 日志查看${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

# 菜单
show_menu() {
    echo -e "${BLUE}选择要查看的日志:${NC}"
    echo ""
    echo -e "  ${GREEN}1${NC}. OpenCode 服务器日志 (实时)"
    echo -e "  ${GREEN}2${NC}. Web 服务器日志 (实时)"
    echo -e "  ${GREEN}3${NC}. 所有日志 (分屏)"
    echo -e "  ${GREEN}4${NC}. OpenCode 最近 50 行"
    echo -e "  ${GREEN}5${NC}. Web 服务器最近 50 行"
    echo -e "  ${GREEN}6${NC}. OpenCode 完整日志"
    echo -e "  ${GREEN}7${NC}. Web 服务器完整日志"
    echo -e "  ${GREEN}q${NC}. 退出"
    echo ""
    echo -ne "${CYAN}请选择 [1-7/q]: ${NC}"
}

# 主循环
while true; do
    show_menu
    read choice

    case $choice in
        1)
            echo -e "${YELLOW}=== OpenCode 服务器日志 (实时，Ctrl+C 退出) ===${NC}"
            echo ""
            tail -f /tmp/opencode-remote.log
            ;;
        2)
            echo -e "${YELLOW}=== Web 服务器日志 (实时，Ctrl+C 退出) ===${NC}"
            echo ""
            tail -f /tmp/web-client.log 2>/dev/null || echo -e "${RED}日志文件不存在${NC}"
            ;;
        3)
            echo -e "${YELLOW}=== 所有日志 (分屏，按 q 退出) ===${NC}"
            echo ""
            if command -v multitail >/dev/null 2>&1; then
                multitail /tmp/opencode-remote.log /tmp/web-client.log
            else
                echo -e "${YELLOW}提示: 安装 multitail 可以更好地查看多个日志文件${NC}"
                echo -e "${YELLOW}     sudo apt-get install multitail${NC}"
                echo ""
                echo -e "${CYAN}使用 tail -f 查看两个日志文件...${NC}"
                echo ""
                tail -f /tmp/opencode-remote.log /tmp/web-client.log 2>/dev/null
            fi
            ;;
        4)
            echo -e "${YELLOW}=== OpenCode 服务器日志 (最近 50 行) ===${NC}"
            echo ""
            tail -50 /tmp/opencode-remote.log
            echo ""
            ;;
        5)
            echo -e "${YELLOW}=== Web 服务器日志 (最近 50 行) ===${NC}"
            echo ""
            tail -50 /tmp/web-client.log 2>/dev/null || echo -e "${RED}日志文件不存在${NC}"
            echo ""
            ;;
        6)
            echo -e "${YELLOW}=== OpenCode 服务器完整日志 ===${NC}"
            echo ""
            cat /tmp/opencode-remote.log | less
            ;;
        7)
            echo -e "${YELLOW}=== Web 服务器完整日志 ===${NC}"
            echo ""
            cat /tmp/web-client.log 2>/dev/null | less || echo -e "${RED}日志文件不存在${NC}"
            ;;
        q|Q)
            echo -e "${GREEN}退出${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择，请重试${NC}"
            echo ""
            ;;
    esac
done
