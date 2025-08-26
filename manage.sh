#!/bin/bash

# ================================
# MP3 转换服务管理脚本
# ================================

SERVICE_NAME="mp3-converter"
LOG_DIR="/opt/mp3-converter/logs"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 启动服务
start_service() {
    log_info "启动 MP3 转换服务..."
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_warning "服务已在运行"
        return 0
    fi
    
    systemctl start $SERVICE_NAME
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止 MP3 转换服务..."
    
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        log_warning "服务未在运行"
        return 0
    fi
    
    systemctl stop $SERVICE_NAME
    
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        log_success "服务停止成功"
    else
        log_error "服务停止失败"
        return 1
    fi
}

# 重启服务
restart_service() {
    log_info "重启 MP3 转换服务..."
    systemctl restart $SERVICE_NAME
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_success "服务重启成功"
    else
        log_error "服务重启失败"
        return 1
    fi
}

# 查看服务状态
status_service() {
    echo "=== 服务状态 ==="
    systemctl status $SERVICE_NAME --no-pager
    
    echo ""
    echo "=== 端口监听 ==="
    netstat -tlnp | grep :8000 || echo "端口 8000 未监听"
    
    echo ""
    echo "=== 磁盘使用 ==="
    df -h /opt/mp3-converter
}

# 查看日志
logs_service() {
    local lines=${1:-50}
    
    if [ -f "$LOG_DIR/mp3-converter.log" ]; then
        echo "=== 应用日志（最近 $lines 行）==="
        tail -n "$lines" "$LOG_DIR/mp3-converter.log"
    fi
    
    echo ""
    echo "=== 系统日志（最近 $lines 行）==="
    journalctl -u $SERVICE_NAME -n "$lines" --no-pager
}

# 实时日志
follow_logs() {
    echo "=== 实时日志（按 Ctrl+C 退出）==="
    
    if [ -f "$LOG_DIR/mp3-converter.log" ]; then
        tail -f "$LOG_DIR/mp3-converter.log"
    else
        journalctl -u $SERVICE_NAME -f
    fi
}

# 启用开机自启
enable_service() {
    log_info "启用开机自启..."
    systemctl enable $SERVICE_NAME
    
    if systemctl is-enabled --quiet $SERVICE_NAME; then
        log_success "开机自启已启用"
    else
        log_error "开机自启启用失败"
        return 1
    fi
}

# 禁用开机自启
disable_service() {
    log_info "禁用开机自启..."
    systemctl disable $SERVICE_NAME
    
    if ! systemctl is-enabled --quiet $SERVICE_NAME; then
        log_success "开机自启已禁用"
    else
        log_error "开机自启禁用失败"
        return 1
    fi
}

# 重载服务配置
reload_service() {
    log_info "重载服务配置..."
    systemctl daemon-reload
    log_success "配置重载完成"
}

# 清理日志
clean_logs() {
    log_info "清理日志文件..."
    
    if [ -f "$LOG_DIR/mp3-converter.log" ]; then
        # 保留最近1000行日志
        tail -n 1000 "$LOG_DIR/mp3-converter.log" > "$LOG_DIR/mp3-converter.log.tmp"
        mv "$LOG_DIR/mp3-converter.log.tmp" "$LOG_DIR/mp3-converter.log"
        log_success "应用日志已清理"
    fi
    
    # 清理系统日志（保留最近7天）
    journalctl --vacuum-time=7d
    log_success "系统日志已清理"
}

# 测试服务
test_service() {
    log_info "测试服务..."
    
    local url="http://localhost:8000"
    
    if curl -s "$url" > /dev/null; then
        log_success "服务响应正常"
        echo "访问地址: $url"
        echo "API 文档: $url/docs"
    else
        log_error "服务无响应"
        return 1
    fi
}

# 显示帮助
show_help() {
    echo "MP3 转换服务管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|follow|enable|disable|reload|clean|test|help}"
    echo ""
    echo "命令说明:"
    echo "  start     - 启动服务"
    echo "  stop      - 停止服务"
    echo "  restart   - 重启服务"
    echo "  status    - 查看服务状态"
    echo "  logs      - 查看日志（默认50行）"
    echo "  follow    - 实时查看日志"
    echo "  enable    - 启用开机自启"
    echo "  disable   - 禁用开机自启"
    echo "  reload    - 重载服务配置"
    echo "  clean     - 清理日志文件"
    echo "  test      - 测试服务响应"
    echo "  help      - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start           # 启动服务"
    echo "  $0 logs 100        # 查看最近100行日志"
    echo "  $0 test            # 测试服务"
}

# 主函数
main() {
    case "$1" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            status_service
            ;;
        logs)
            logs_service "$2"
            ;;
        follow)
            follow_logs
            ;;
        enable)
            enable_service
            ;;
        disable)
            disable_service
            ;;
        reload)
            reload_service
            ;;
        clean)
            clean_logs
            ;;
        test)
            test_service
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|logs|follow|enable|disable|reload|clean|test|help}"
            exit 1
            ;;
    esac
}

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    log_error "请以 root 权限运行此脚本"
    exit 1
fi

# 运行主函数
main "$@" 