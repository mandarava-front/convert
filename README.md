# MP3 转换服务

一个基于 FastAPI 的音频转换服务，支持将 MP3 文件转换为 MIDI 或 WAV 格式。

## 功能特性

- 🎵 **MP3 → MIDI 转换**: 使用 Spotify 的 Basic Pitch 库将 MP3 文件转换为 MIDI
- 🎧 **MP3 → WAV 转换**: 使用 pydub 库将 MP3 文件转换为 WAV 格式
- 📤 **多种输入方式**: 支持文件上传和 URL 链接两种方式
- 🌐 **RESTful API**: 提供标准的 REST API 接口
- 📚 **自动文档**: 自动生成的 API 文档（Swagger/OpenAPI）
- 🛡️ **守护进程**: 支持 systemd 服务管理和自动重启

## 项目结构

```
mp3/
├── main.py                    # FastAPI 主程序
├── utils/
│   ├── __init__.py           # 工具包初始化
│   ├── convert.py            # Basic Pitch MIDI 转换逻辑
│   └── audio_tools.py        # pydub WAV 转换逻辑
├── uploads/                  # 临时上传的 MP3 文件
├── midis/                    # 输出的 MIDI 文件
├── wavs/                     # 输出的 WAV 文件
├── requirements.txt          # Python 依赖
├── deploy.sh                 # 一键部署脚本
├── server_start.sh           # 服务器启动脚本
├── manage.sh                 # 服务管理脚本
├── mp3-converter.service     # systemd 服务配置
├── start.sh                  # 本地启动脚本
├── .gitignore               # Git 忽略文件
└── README.md                # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
# 确保你已安装 Python 3.9+
python3 -m pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 方式1: 使用启动脚本（推荐）
./start.sh

# 方式2: 直接使用 uvicorn
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问服务

- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **交互式文档**: http://localhost:8000/redoc

## API 接口

### 1. MP3 转 MIDI

**接口**: `POST /convert`

**支持的输入方式**:

#### 文件上传 (multipart/form-data)
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@your_music.mp3"
```

#### URL 链接 (form data)
```bash
curl -X POST "http://localhost:8000/convert" \
  -d "url=https://example.com/music.mp3"
```

#### JSON 格式
```bash
curl -X POST "http://localhost:8000/convert/json" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/music.mp3"}'
```

**响应示例**:
```json
{
  "success": true,
  "message": "转换成功",
  "download_url": "/midis/uuid-filename.mid",
  "filename": "uuid-filename.mid"
}
```

### 2. MP3 转 WAV

**接口**: `POST /convert/wav`

**输入方式与 MIDI 转换相同**，只是输出为 WAV 格式：

```bash
curl -X POST "http://localhost:8000/convert/wav" \
  -F "file=@your_music.mp3"
```

**响应示例**:
```json
{
  "success": true,
  "message": "转换成功",
  "download_url": "/wavs/uuid-filename.wav",
  "filename": "uuid-filename.wav"
}
```

### 3. 下载文件

转换完成后，可以通过返回的 `download_url` 直接下载文件：

```bash
# 下载 MIDI 文件
curl -O http://localhost:8000/midis/uuid-filename.mid

# 下载 WAV 文件
curl -O http://localhost:8000/wavs/uuid-filename.wav
```

## 服务器部署

### 一键部署

```bash
# 1. 配置部署参数（二选一）
# 方式1: 直接修改 deploy.sh 中的配置
vim deploy.sh

# 方式2: 使用配置文件（推荐）
cp deploy.config.example deploy.config
vim deploy.config

# 2. 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 配置说明

需要修改的主要配置项：

```bash
SERVER_IP="your.server.ip.address"      # 服务器 IP
SERVER_USER="root"                       # SSH 用户名  
SERVER_PORT="22"                         # SSH 端口
TARGET_DIR="/opt/mp3-converter"          # 部署目录
```

### 手动部署

```bash
# 1. 上传代码到服务器
scp -r ./* root@your.server.ip:/opt/mp3-converter/

# 2. 在服务器上安装依赖
ssh root@your.server.ip
cd /opt/mp3-converter
apt update && apt install -y python3 python3-pip ffmpeg libsndfile1
python3 -m pip install -r requirements.txt

# 3. 设置服务
cp mp3-converter.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable mp3-converter
systemctl start mp3-converter
```

### 服务管理

```bash
# 使用管理脚本（推荐）
./manage.sh start    # 启动服务
./manage.sh stop     # 停止服务
./manage.sh restart  # 重启服务
./manage.sh status   # 查看状态
./manage.sh logs     # 查看日志

# 或使用 systemctl
systemctl start mp3-converter
systemctl stop mp3-converter
systemctl restart mp3-converter
systemctl status mp3-converter
```

### 部署后验证

```bash
# 检查服务状态
./manage.sh status

# 测试服务响应
./manage.sh test

# 查看实时日志
./manage.sh follow
```

服务成功启动后，可以访问：
- **API 服务**: http://your.server.ip:8000
- **API 文档**: http://your.server.ip:8000/docs

## 环境要求

- Python 3.9+
- 系统依赖：
  - macOS: 自动安装
  - Linux: `apt-get install ffmpeg libsndfile1`
  - Windows: 请安装 FFmpeg

## 依赖库

主要依赖：
- `fastapi`: Web 框架
- `uvicorn`: ASGI 服务器
- `basic-pitch`: Spotify 的音频转 MIDI 库
- `pydub`: 音频处理库
- `requests`: HTTP 请求库
- `aiofiles`: 异步文件操作

## 错误处理

所有错误都会返回标准的 JSON 格式：

```json
{
  "detail": "错误描述信息"
}
```

常见错误：
- `400`: 请求参数错误（如未提供文件或 URL）
- `500`: 服务器内部错误（如转换失败）

## 注意事项

1. **文件清理**: 转换完成后，原始 MP3 文件会被自动删除
2. **文件命名**: 输出文件使用 UUID 命名，避免冲突
3. **并发处理**: 支持多个请求同时处理
4. **格式支持**: 目前仅支持 MP3 输入格式

## 开发与贡献

这是一个基于 FastAPI 的项目，欢迎贡献代码！

### 本地开发

```bash
# 克隆项目
git clone <your-repo>
cd mp3

# 安装依赖
python3 -m pip install -r requirements.txt

# 启动开发服务器
python3 -m uvicorn main:app --reload
```

## 许可证

MIT License 