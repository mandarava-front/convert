#!/bin/bash

# ================================
# MP3 转换服务 - 服务器启动脚本
# ================================

# 配置项
APP_DIR="/opt/mp3-converter"          # 应用目录
APP_USER="root"                       # 运行用户
HOST="0.0.0.0"                        # 监听地址
PORT="8000"                           # 监听端口
WORKERS="1"                           # 工作进程数
LOG_DIR="$APP_DIR/logs"               # 日志目录
PID_FILE="$LOG_DIR/mp3-converter.pid" # PID 文件

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境
check_environment() {
    log_info "检查运行环境..."
    
    # 检查 Python3
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查应用目录
    if [ ! -d "$APP_DIR" ]; then
        log_error "应用目录不存在: $APP_DIR"
        exit 1
    fi
    
    # 检查 main.py
    if [ ! -f "$APP_DIR/main.py" ]; then
        log_error "主程序文件不存在: $APP_DIR/main.py"
        exit 1
    fi
    
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    # 创建必要目录
    mkdir -p "$APP_DIR/uploads" "$APP_DIR/midis" "$APP_DIR/wavs"
    
    log_success "环境检查完成"
}

# 启动应用
start_app() {
    log_info "启动 MP3 转换服务..."
    
    cd "$APP_DIR"
    
    # 检查端口是否被占用
    if netstat -tlnp | grep -q ":$PORT "; then
        log_error "端口 $PORT 已被占用"
        return 1
    fi
    
    # 启动应用
    nohup python3 -m uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --access-log \
        --log-level info \
        > "$LOG_DIR/mp3-converter.log" 2>&1 &
    
    # 记录 PID
    echo $! > "$PID_FILE"
    
    # 等待启动
    sleep 3
    
    # 检查是否启动成功
    if check_status; then
        log_success "服务启动成功，PID: $(cat $PID_FILE)"
        log_info "访问地址: http://localhost:$PORT"
        log_info "API 文档: http://localhost:$PORT/docs"
        log_info "日志文件: $LOG_DIR/mp3-converter.log"
        return 0
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 停止应用
stop_app() {
    log_info "停止 MP3 转换服务..."
    
    if [ ! -f "$PID_FILE" ]; then
        log_warning "PID 文件不存在，尝试通过端口查找进程..."
        local pids=$(lsof -ti:$PORT)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -TERM
            sleep 2
            echo "$pids" | xargs kill -KILL 2>/dev/null || true
            log_success "服务已停止"
        else
            log_warning "未找到运行中的服务"
        fi
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    
    if kill -0 "$pid" 2>/dev/null; then
        log_info "正在停止进程 $pid..."
        kill -TERM "$pid"
        
        # 等待进程结束
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # 强制杀死进程（如果还在运行）
        if kill -0 "$pid" 2>/dev/null; then
            log_warning "进程未响应，强制终止..."
            kill -KILL "$pid" 2>/dev/null
        fi
        
        log_success "服务已停止"
    else
        log_warning "进程 $pid 不存在"
    fi
    
    rm -f "$PID_FILE"
}

# 重启应用
restart_app() {
    log_info "重启 MP3 转换服务..."
    stop_app
    sleep 2
    start_app
}

# 检查状态
check_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "服务正在运行，PID: $pid"
            if netstat -tlnp | grep -q ":$PORT "; then
                echo "端口 $PORT 正在监听"
                return 0
            else
                echo "端口 $PORT 未监听"
                return 1
            fi
        else
            echo "PID 文件存在但进程不在运行"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo "服务未运行"
        return 1
    fi
}

# 显示日志
show_logs() {
    local lines=${1:-50}
    if [ -f "$LOG_DIR/mp3-converter.log" ]; then
        echo "=== 最近 $lines 行日志 ==="
        tail -n "$lines" "$LOG_DIR/mp3-converter.log"
    else
        echo "日志文件不存在: $LOG_DIR/mp3-converter.log"
    fi
}

# 实时查看日志
follow_logs() {
    if [ -f "$LOG_DIR/mp3-converter.log" ]; then
        echo "=== 实时日志（按 Ctrl+C 退出）==="
        tail -f "$LOG_DIR/mp3-converter.log"
    else
        echo "日志文件不存在: $LOG_DIR/mp3-converter.log"
    fi
}

# 显示帮助
show_help() {
    echo "MP3 转换服务管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|follow|help}"
    echo ""
    echo "命令说明:"
    echo "  start    - 启动服务"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
    echo "  status   - 检查服务状态"
    echo "  logs     - 显示最近日志（默认50行）"
    echo "  follow   - 实时查看日志"
    echo "  help     - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start           # 启动服务"
    echo "  $0 logs 100        # 显示最近100行日志"
}

# 主函数
main() {
    case "$1" in
        start)
            check_environment
            start_app
            ;;
        stop)
            stop_app
            ;;
        restart)
            check_environment
            restart_app
            ;;
        status)
            check_status
            ;;
        logs)
            show_logs "$2"
            ;;
        follow)
            follow_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|logs|follow|help}"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 