#!/bin/bash

# ================================
# MP3 转换服务部署脚本
# ================================

# 🔧 配置项（请根据实际情况修改）
SERVER_IP="45.63.8.153"              # 服务器 IP 地址
SERVER_USER="root"                           # SSH 用户名
SERVER_PORT="22"                             # SSH 端口
TARGET_DIR="/home/mp3-converter"              # 服务器目标目录
SERVICE_NAME="mp3-converter"                 # 服务名称

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

# 检查依赖
check_dependencies() {
    log_info "检查本地依赖..."
    
    if ! command -v rsync &> /dev/null; then
        log_error "rsync 未安装，请先安装 rsync"
        exit 1
    fi
    
    if ! command -v ssh &> /dev/null; then
        log_error "ssh 未安装，请先安装 openssh-client"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 打包项目
package_project() {
    log_info "打包项目文件..."
    
    # 创建临时目录
    TEMP_DIR="/tmp/mp3-converter-deploy"
    rm -rf $TEMP_DIR
    mkdir -p $TEMP_DIR
    
    # 复制项目文件（排除不需要的文件）
    rsync -av --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='.git' \
              --exclude='uploads/' \
              --exclude='midis/' \
              --exclude='wavs/' \
              --exclude='deploy.sh' \
              --exclude='项目结构.md' \
              ./ $TEMP_DIR/
    
    log_success "项目打包完成: $TEMP_DIR"
}

# 上传到服务器
upload_to_server() {
    log_info "上传文件到服务器..."
    
    # SSH 连接字符串（只包含 user@host，不包含 -p）
    SSH_CONN="$SERVER_USER@$SERVER_IP"
    
    # 创建目标目录
    ssh -p $SERVER_PORT $SSH_CONN "mkdir -p $TARGET_DIR"
    
    # 上传文件
    rsync -avz --delete \
          -e "ssh -p $SERVER_PORT" \
          $TEMP_DIR/ \
          $SSH_CONN:$TARGET_DIR/
    
    log_success "文件上传完成"
}

# 在服务器上安装依赖
install_dependencies() {
    log_info "在服务器上安装 Python 依赖..."
    
    SSH_CONN="$SERVER_USER@$SERVER_IP -p $SERVER_PORT"
    
    ssh $SSH_CONN << 'EOF'
        cd /
        cd /home/mp3-converter
        
        # 确保 Python3 和 pip 已安装
        if ! command -v python3 &> /dev/null; then
            echo "安装 Python3..."
            apt update && apt install -y python3 python3-pip
        fi
        
        # 安装系统依赖
        echo "安装系统依赖..."
        apt update && apt install -y ffmpeg libsndfile1
        
        # 安装 Python 依赖
        echo "安装 Python 依赖..."
        python3 -m pip install --upgrade pip
        python3 -m pip install -r requirements.txt
        
        # 创建必要目录
        mkdir -p uploads midis wavs logs
        
        # 设置权限
        chmod +x server_start.sh
        
        echo "依赖安装完成"
EOF
    
    log_success "服务器依赖安装完成"
}

# 设置系统服务
setup_systemd_service() {
    log_info "设置 systemd 服务..."
    
    SSH_CONN="$SERVER_USER@$SERVER_IP"
    
    ssh -p $SERVER_PORT $SSH_CONN << EOF
        # 复制服务文件到系统目录
        cp $TARGET_DIR/$SERVICE_NAME.service /etc/systemd/system/
        
        # 重载 systemd
        systemctl daemon-reload
        
        # 启用服务（开机自启）
        systemctl enable $SERVICE_NAME
        
        echo "systemd 服务设置完成"
EOF
    
    log_success "systemd 服务设置完成"
}

# 启动服务
start_service() {
    log_info "启动 MP3 转换服务..."
    
    SSH_CONN="$SERVER_USER@$SERVER_IP"
    
    ssh -p $SERVER_PORT $SSH_CONN << EOF
        # 停止现有服务（如果在运行）
        systemctl stop $SERVICE_NAME 2>/dev/null || true
        
        # 启动服务
        systemctl start $SERVICE_NAME
        
        # 检查服务状态
        sleep 3
        systemctl status $SERVICE_NAME --no-pager
        
        echo ""
        echo "服务启动完成！"
        echo "访问地址: http://$SERVER_IP:8000"
        echo "API 文档: http://$SERVER_IP:8000/docs"
EOF
    
    log_success "服务启动完成"
}

# 显示服务状态
show_status() {
    log_info "检查服务状态..."
    
    SSH_CONN="$SERVER_USER@$SERVER_IP"
    
    ssh -p $SERVER_PORT $SSH_CONN << EOF
        echo "=== 服务状态 ==="
        systemctl status $SERVICE_NAME --no-pager
        
        echo ""
        echo "=== 最近日志 ==="
        journalctl -u $SERVICE_NAME -n 10 --no-pager
        
        echo ""
        echo "=== 端口监听 ==="
        netstat -tlnp | grep :8000 || echo "端口 8000 未监听"
EOF
}

# 清理临时文件
cleanup() {
    log_info "清理临时文件..."
    rm -rf $TEMP_DIR
    log_success "清理完成"
}

# 主函数
main() {
    echo "🚀 MP3 转换服务部署脚本"
    echo "=========================="
    echo ""
    
    log_warning "请确保已修改脚本中的服务器配置信息！"
    echo "服务器: $SERVER_USER@$SERVER_IP:$SERVER_PORT"
    echo "目标目录: $TARGET_DIR"
    echo ""
    
    read -p "是否继续部署？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi
    
    # 执行部署步骤
    check_dependencies
    package_project
    upload_to_server
    install_dependencies
    setup_systemd_service
    start_service
    
    echo ""
    log_success "🎉 部署完成！"
    echo ""
    show_status
    
    cleanup
}

# 捕获错误并清理
trap cleanup EXIT

# 运行主函数
main "$@" 