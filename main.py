"""
FastAPI 主程序：MP3 转换服务
提供 MP3 → MIDI 和 MP3 → WAV 转换功能
"""

import os
import uuid
import aiofiles
from typing import Optional, Union
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import requests

import logging



from utils.convert import mp3_to_midi
from utils.audio_tools import mp3_to_wav
from utils.video_tools import extract_first_frame, extract_last_frame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="MP3 转换服务",
    description="将 MP3 文件转换为 MIDI 或 WAV 格式",
    version="1.0.0"
)

# 确保必要目录存在（在挂载静态目录之前执行）
os.makedirs("uploads", exist_ok=True)
os.makedirs("midis", exist_ok=True)
os.makedirs("wavs", exist_ok=True)
os.makedirs("frames", exist_ok=True)

# 挂载静态文件路由
app.mount("/midis", StaticFiles(directory="midis"), name="midis")
app.mount("/wavs", StaticFiles(directory="wavs"), name="wavs")
app.mount("/frames", StaticFiles(directory="frames"), name="frames")

# Pydantic 模型
class URLRequest(BaseModel):
    """URL 请求模型"""
    url: str

class ConvertResponse(BaseModel):
    """转换响应模型"""
    success: bool
    message: str
    download_url: Optional[str] = None
    filename: Optional[str] = None


async def download_file_from_url(url: str) -> str:
    """
    从 URL 下载视频/媒体文件到 uploads 目录，返回本地文件路径。

    会尽量使用 URL 后缀或 Content-Type 推断扩展名，默认使用 .mp4。
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # 推断扩展名
        from urllib.parse import urlparse
        import os as _os

        parsed = urlparse(url)
        path_ext = _os.path.splitext(parsed.path)[1].lower()
        allowed_exts = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}

        if path_ext in allowed_exts:
            ext = path_ext
        else:
            content_type = response.headers.get("Content-Type", "").lower()
            if "video/mp4" in content_type:
                ext = ".mp4"
            elif "video/webm" in content_type:
                ext = ".webm"
            elif "video/quicktime" in content_type:
                ext = ".mov"
            elif "video/x-matroska" in content_type:
                ext = ".mkv"
            else:
                ext = ".mp4"

        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{ext}"
        filepath = os.path.join("uploads", filename)

        # 保存文件
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath

    except requests.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"下载视频文件失败: {str(e)}"
        )

async def download_mp3_from_url(url: str) -> str:
    """
    从 URL 下载 MP3 文件
    
    Args:
        url: MP3 文件的 URL
        
    Returns:
        str: 保存的本地文件路径
        
    Raises:
        HTTPException: 下载失败时抛出异常
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.mp3"
        filepath = os.path.join("uploads", filename)
        
        # 保存文件
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return filepath
        
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400, 
            detail=f"下载 MP3 文件失败: {str(e)}"
        )

async def save_uploaded_file(file: UploadFile) -> str:
    """
    保存上传的文件
    
    Args:
        file: 上传的文件对象
        
    Returns:
        str: 保存的本地文件路径
    """
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp3"
    filepath = os.path.join("uploads", filename)
    
    # 异步保存文件
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    return filepath

def cleanup_file(filepath: str) -> None:
    """
    清理临时文件
    
    Args:
        filepath: 要删除的文件路径
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass  # 忽略删除失败的情况

@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "message": "MP3 转换服务",
        "endpoints": {
            "convert_to_midi": "/convert",
            "convert_to_wav": "/convert/wav",
            "video_first_frame": "/convert/video/first-frame/json",
            "video_last_frame": "/convert/video/last-frame/json"
        }
    }

@app.post("/convert", response_model=ConvertResponse)
async def convert_mp3_to_midi(
    request: Request,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None)
):
    """
    将 MP3 转换为 MIDI
    支持两种输入方式：
    1. 文件上传 (multipart/form-data)
    2. URL 链接 (form data)
    """
    mp3_filepath = None
    try:
        # 检查输入参数
        if not file and not url:
            raise HTTPException(
                status_code=400,
                detail="请提供 MP3 文件或 URL"
            )
        if file and url:
            raise HTTPException(
                status_code=400,
                detail="只能提供文件或 URL 中的一种"
            )
        # 获取 MP3 文件
        if file:
            # 检查文件类型
            if not file.filename.lower().endswith('.mp3'):
                raise HTTPException(
                    status_code=400,
                    detail="只支持 MP3 文件"
                )
            mp3_filepath = await save_uploaded_file(file)
        else:
            # 从 URL 下载
            mp3_filepath = await download_mp3_from_url(url)
        # 转换为 MIDI
        midi_filename = await mp3_to_midi(mp3_filepath)
        # 清理原始文件
        cleanup_file(mp3_filepath)
        # 构造完整下载链接
        host = request.headers.get("host", "")
        if "localhost" in host or "127.0.0.1" in host:
            base_url = f"http://{host}/mp3-converter"
        elif "accentoracle.online" in host:
            base_url = "https://accentoracle.online/mp3-converter"
        else:
            base_url = f"http://{host}/mp3-converter"
        download_url = f"{base_url}/midis/{midi_filename}"
        return ConvertResponse(
            success=True,
            message="转换成功",
            download_url=download_url,
            filename=midi_filename
        )
    except HTTPException:
        if mp3_filepath:
            cleanup_file(mp3_filepath)
        raise
    except Exception as e:
        if mp3_filepath:
            cleanup_file(mp3_filepath)
        raise HTTPException(
            status_code=500,
            detail=f"转换失败: {str(e)}"
        )

@app.post("/convert/wav", response_model=ConvertResponse)
async def convert_mp3_to_wav_endpoint(
    request: Request,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None)
):
    """
    将 MP3 转换为 WAV
    支持两种输入方式：
    1. 文件上传 (multipart/form-data)
    2. URL 链接 (form data)
    """
    mp3_filepath = None
    try:
        if not file and not url:
            raise HTTPException(
                status_code=400,
                detail="请提供 MP3 文件或 URL"
            )
        if file and url:
            raise HTTPException(
                status_code=400,
                detail="只能提供文件或 URL 中的一种"
            )
        if file:
            if not file.filename.lower().endswith('.mp3'):
                raise HTTPException(
                    status_code=400,
                    detail="只支持 MP3 文件"
                )
            mp3_filepath = await save_uploaded_file(file)
        else:
            mp3_filepath = await download_mp3_from_url(url)
        wav_filename = await mp3_to_wav(mp3_filepath)
        cleanup_file(mp3_filepath)
        host = request.headers.get("host", "")
        if "localhost" in host or "127.0.0.1" in host:
            base_url = f"http://{host}/mp3-converter"
        elif "accentoracle.online" in host:
            base_url = "https://accentoracle.online/mp3-converter"
        else:
            base_url = f"http://{host}/mp3-converter"
        download_url = f"{base_url}/wavs/{wav_filename}"
        return ConvertResponse(
            success=True,
            message="转换成功",
            download_url=download_url,
            filename=wav_filename
        )
    except HTTPException:
        if mp3_filepath:
            cleanup_file(mp3_filepath)
        raise
    except Exception as e:
        if mp3_filepath:
            cleanup_file(mp3_filepath)
        raise HTTPException(
            status_code=500,
            detail=f"转换失败: {str(e)}"
        )


@app.post("/convert/video/first-frame/json")
async def video_first_frame_json(request: Request, background_tasks: BackgroundTasks):
    """
    接收 JSON: {"url": "..."}，提取视频首帧并返回图片文件。
    """
    try:
        data = await request.json()
    except Exception:
        data = {}
    url = (data or {}).get("url")
    width = data.get("width") if isinstance(data.get("width"), int) else None
    height = data.get("height") if isinstance(data.get("height"), int) else None
    image_format = data.get("format") if isinstance(data.get("format"), str) else "png"
    quality = data.get("quality") if isinstance(data.get("quality"), int) else None
    sws_flags = data.get("sws_flags") if isinstance(data.get("sws_flags"), str) else None
    if not url:
        raise HTTPException(status_code=400, detail="请提供视频 URL")

    video_filepath = None
    frame_path = None
    try:
        video_filepath = await download_file_from_url(url)
        frame_filename = await extract_first_frame(
            video_filepath,
            width=width,
            height=height,
            image_format=image_format,
            quality=quality,
            sws_flags=sws_flags,
        )
        frame_path = os.path.join("frames", frame_filename)
        cleanup_file(video_filepath)
        video_filepath = None

        # 响应完成后清理生成的帧文件
        background_tasks.add_task(cleanup_file, frame_path)
        return FileResponse(
            frame_path,
            media_type="image/png",
            filename=frame_filename,
            background=background_tasks,
        )
    except HTTPException:
        if video_filepath:
            cleanup_file(video_filepath)
        if frame_path:
            cleanup_file(frame_path)
        raise
    except Exception as e:
        if video_filepath:
            cleanup_file(video_filepath)
        if frame_path:
            cleanup_file(frame_path)
        raise HTTPException(status_code=500, detail=f"提取首帧失败: {str(e)}")


@app.post("/convert/video/last-frame/json")
async def video_last_frame_json(request: Request, background_tasks: BackgroundTasks):
    """
    接收 JSON: {"url": "..."}，提取视频尾帧并返回图片文件。
    参数与首帧接口一致：width、height、format(jpg/png)、quality、sws_flags。
    """
    try:
        data = await request.json()
    except Exception:
        data = {}
    url = (data or {}).get("url")
    width = data.get("width") if isinstance(data.get("width"), int) else None
    height = data.get("height") if isinstance(data.get("height"), int) else None
    image_format = data.get("format") if isinstance(data.get("format"), str) else "png"
    quality = data.get("quality") if isinstance(data.get("quality"), int) else None
    sws_flags = data.get("sws_flags") if isinstance(data.get("sws_flags"), str) else None
    if not url:
        raise HTTPException(status_code=400, detail="请提供视频 URL")

    video_filepath = None
    frame_path = None
    try:
        video_filepath = await download_file_from_url(url)
        frame_filename = await extract_last_frame(
            video_filepath,
            width=width,
            height=height,
            image_format=image_format,
            quality=quality,
            sws_flags=sws_flags,
        )
        frame_path = os.path.join("frames", frame_filename)
        cleanup_file(video_filepath)
        video_filepath = None

        background_tasks.add_task(cleanup_file, frame_path)
        return FileResponse(
            frame_path,
            media_type="image/png",
            filename=frame_filename,
            background=background_tasks,
        )
    except HTTPException:
        if video_filepath:
            cleanup_file(video_filepath)
        if frame_path:
            cleanup_file(frame_path)
        raise
    except Exception as e:
        if video_filepath:
            cleanup_file(video_filepath)
        if frame_path:
            cleanup_file(frame_path)
        raise HTTPException(status_code=500, detail=f"提取尾帧失败: {str(e)}")

# 支持 JSON 格式的 URL 请求
@app.post("/convert/json", response_model=ConvertResponse)
async def convert_mp3_to_midi_json(request: Request):
    body = await request.body()
    logger.info(f"Received body: {body}")
    try:
        data = await request.json()
        logger.info(f"Parsed JSON: {data}")
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        data = {}
    # 复用 convert_mp3_to_midi 逻辑
    class DummyUploadFile:
        filename = None
    return await convert_mp3_to_midi(request, file=None, url=data.get("url"))

@app.post("/convert/wav/json", response_model=ConvertResponse)
async def convert_mp3_to_wav_json(request: Request):
    body = await request.body()
    logger.info(f"Received body: {body}")
    try:
        data = await request.json()
        logger.info(f"Parsed JSON: {data}")
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        data = {}
    return await convert_mp3_to_wav_endpoint(request, file=None, url=data.get("url"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 