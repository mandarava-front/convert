# 🚀 MP3 转换服务 - 部署快速指南

## 📝 部署前准备

### 1. 服务器环境要求
- **操作系统**: Ubuntu 18.04+ / CentOS 7+ / Debian 9+
- **Python**: 3.9+
- **内存**: 建议 2GB+
- **磁盘**: 建议 10GB+

### 2. 本地环境要求
- **SSH 客户端**: openssh-client
- **rsync**: 用于文件同步

## ⚡ 一键部署（推荐）

### 步骤 1: 配置服务器信息
```bash
# 复制配置模板
cp deploy.config.example deploy.config

# 编辑配置（必须修改的项目已标注 ⚠️）
vim deploy.config
```

**必须修改的配置项：**
```bash
SERVER_IP="your.server.ip.address"    # ⚠️ 服务器 IP 地址
SERVER_USER="root"                     # ⚠️ SSH 用户名
SERVER_PORT="22"                       # ⚠️ SSH 端口（如果不是22）
```

### 步骤 2: 执行部署
```bash
# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 步骤 3: 验证部署
```bash
# 等待部署完成后，访问服务
curl http://your.server.ip:8000

# 查看 API 文档
open http://your.server.ip:8000/docs
```

## 🔧 手动部署

如果一键部署失败，可以使用手动部署：

### 1. 上传文件
```bash
# 打包项目
tar -czf mp3-converter.tar.gz --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' .

# 上传到服务器
scp mp3-converter.tar.gz root@your.server.ip:/tmp/

# 解压到目标目录
ssh root@your.server.ip << 'EOF'
mkdir -p /opt/mp3-converter
cd /opt/mp3-converter
tar -xzf /tmp/mp3-converter.tar.gz
rm /tmp/mp3-converter.tar.gz
EOF
```

### 2. 安装依赖
```bash
ssh root@your.server.ip << 'EOF'
cd /opt/mp3-converter

# 安装系统依赖
apt update
apt install -y python3 python3-pip ffmpeg libsndfile1

# 安装 Python 依赖
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 创建目录
mkdir -p uploads midis wavs logs
chmod +x *.sh
EOF
```

### 3. 设置系统服务
```bash
ssh root@your.server.ip << 'EOF'
cd /opt/mp3-converter

# 安装服务文件
cp mp3-converter.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable mp3-converter
systemctl start mp3-converter

# 检查状态
systemctl status mp3-converter
EOF
```

## 🎛️ 服务管理

部署完成后，在服务器上可以使用以下命令管理服务：

```bash
cd /opt/mp3-converter

# 启动服务
./manage.sh start

# 停止服务
./manage.sh stop

# 重启服务
./manage.sh restart

# 查看状态
./manage.sh status

# 查看日志
./manage.sh logs

# 实时日志
./manage.sh follow

# 测试服务
./manage.sh test
```

## 🔍 故障排除

### 1. 端口被占用
```bash
# 查看端口占用
netstat -tlnp | grep :8000

# 杀死占用进程
sudo kill -9 <PID>
```

### 2. 权限问题
```bash
# 设置正确权限
sudo chown -R root:root /opt/mp3-converter
sudo chmod +x /opt/mp3-converter/*.sh
```

### 3. 依赖安装失败
```bash
# 更新包管理器
sudo apt update

# 手动安装依赖
sudo apt install -y python3-dev python3-pip build-essential

# 重新安装 Python 包
cd /opt/mp3-converter
python3 -m pip install --no-cache-dir -r requirements.txt
```

### 4. 服务启动失败
```bash
# 查看详细日志
journalctl -u mp3-converter -f

# 查看应用日志
tail -f /opt/mp3-converter/logs/mp3-converter.log

# 手动启动测试
cd /opt/mp3-converter
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📚 常用命令速查

| 操作 | 命令 |
|------|------|
| 启动服务 | `./manage.sh start` |
| 停止服务 | `./manage.sh stop` |
| 重启服务 | `./manage.sh restart` |
| 查看状态 | `./manage.sh status` |
| 查看日志 | `./manage.sh logs` |
| 实时日志 | `./manage.sh follow` |
| 测试服务 | `./manage.sh test` |
| 清理日志 | `./manage.sh clean` |

## 🔗 访问地址

部署成功后，服务将在以下地址可用：

- **API 服务**: http://your.server.ip:8000
- **API 文档**: http://your.server.ip:8000/docs
- **交互式文档**: http://your.server.ip:8000/redoc

## 🆘 获取帮助

如果遇到问题，可以：

1. 查看日志文件：`/opt/mp3-converter/logs/mp3-converter.log`
2. 检查系统日志：`journalctl -u mp3-converter`
3. 运行服务测试：`./manage.sh test`
4. 查看服务状态：`./manage.sh status` 