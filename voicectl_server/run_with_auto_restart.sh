#!/bin/bash
# 服务器自动重启监控脚本
# 当app.py崩溃时自动重启

# 配置
APP_NAME="voicectl_server"
PYTHON_CMD="python"
APP_SCRIPT="app.py"
LOG_DIR="tmp"
PID_FILE="tmp/server.pid"
START_DELAY=3  # 重启前等待秒数

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查并杀死旧进程
kill_old_process() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            log_info "发现旧进程 PID: $OLD_PID，正在终止..."
            kill "$OLD_PID"
            sleep 2
            # 如果还没死，强制杀死
            if ps -p "$OLD_PID" > /dev/null 2>&1; then
                log_warn "强制终止进程 PID: $OLD_PID"
                kill -9 "$OLD_PID"
            fi
        fi
        rm -f "$PID_FILE"
    fi

    # 查找所有相关进程并终止
    pkill -f "$PYTHON_CMD.*$APP_SCRIPT" 2>/dev/null
    sleep 1
}

# 启动应用
start_app() {
    log_info "正在启动 $APP_NAME..."
    nohup $PYTHON_CMD $APP_SCRIPT > "$LOG_DIR/server_stdout.log" 2>&1 &
    APP_PID=$!
    echo $APP_PID > "$PID_FILE"
    log_info "$APP_NAME 已启动，PID: $APP_PID"
    log_info "标准输出日志: $LOG_DIR/server_stdout.log"
    log_info "应用日志: $LOG_DIR/server.log"
}

# 检查应用是否在运行
is_app_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # 正在运行
        fi
    fi
    return 1  # 未运行
}

# 主监控循环
monitor_app() {
    RESTART_COUNT=0
    MAX_RESTART_PER_MINUTE=5  # 每分钟最多重启次数
    RESTART_TIMES=()

    log_info "===== $APP_NAME 自动重启监控启动 ====="
    log_info "监控脚本 PID: $$"
    log_info "应用启动日志: $LOG_DIR/server_stdout.log"
    log_info "应用日志: $LOG_DIR/server.log"
    log_info "按 Ctrl+C 停止监控（应用将继续运行）"

    # 首次启动
    kill_old_process
    start_app

    # 监控循环
    while true; do
        sleep 5  # 每5秒检查一次

        if ! is_app_running; then
            CURRENT_TIME=$(date +%s)

            # 记录重启时间
            RESTART_TIMES+=("$CURRENT_TIME")

            # 清理1分钟前的重启记录
            RESTART_TIMES=($(for time in "${RESTART_TIMES[@]}"; do
                [ $((time - CURRENT_TIME)) -le 60 ] && echo $time
            done))

            # 检查重启频率
            if [ ${#RESTART_TIMES[@]} -ge $MAX_RESTART_PER_MINUTE ]; then
                log_error "！！！警告：$APP_NAME 在1分钟内重启了 ${#RESTART_TIMES[@]} 次 ！！！"
                log_error "可能存在严重问题，暂停自动重启以避免无限循环"
                log_error "请检查日志：$LOG_DIR/server_stdout.log"
                log_error "将在60秒后重试..."

                # 等待60秒
                sleep 60

                # 清空重启记录
                RESTART_TIMES=()
            fi

            RESTART_COUNT=$((RESTART_COUNT + 1))
            log_warn "检测到 $APP_NAME 已停止！"
            log_warn "这是第 $RESTART_COUNT 次重启"

            # 显示最后的日志行
            if [ -f "$LOG_DIR/server_stdout.log" ]; then
                log_warn "最后的日志输出:"
                tail -5 "$LOG_DIR/server_stdout.log" | sed 's/^/  | /'
            fi

            log_info "等待 $START_DELAY 秒后重启..."
            sleep $START_DELAY

            # 重启应用
            start_app
        fi
    done
}

# 信号处理
cleanup() {
    log_info "收到停止信号，正在退出监控..."
    log_info "应用将继续运行（PID: $(cat $PID_FILE 2>/dev/null || echo 'unknown')）"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 启动监控
monitor_app
