"""
视频工具：使用系统 ffmpeg 提取视频首帧

依赖：系统已安装 ffmpeg，可通过 `ffmpeg -version` 验证。
输出：将首帧保存为 PNG 文件，存放在 frames/ 目录，文件名为 UUID.png。
"""

import os
import uuid
import asyncio
import subprocess
from typing import Optional
from functools import partial


async def extract_first_frame(
    video_filepath: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    image_format: str = "png",
    quality: Optional[int] = None,
    sws_flags: Optional[str] = None,
) -> str:
    """
    提取视频文件的首帧为 PNG 图片，返回生成的文件名（不含路径）。

    Args:
        video_filepath: 本地视频文件路径

    Returns:
        str: 生成的 PNG 文件名（如 123e4567-e89b-12d3-a456-426614174000.png）

    Raises:
        Exception: 当 ffmpeg 执行失败或输出文件不存在时抛出
    """
    # 确保输出目录存在
    output_dir = "frames"
    os.makedirs(output_dir, exist_ok=True)

    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    fmt = image_format.lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt not in {"png", "jpg"}:
        fmt = "png"
    output_filename = f"{file_id}.{fmt}"
    output_path = os.path.join(output_dir, output_filename)

    # 在后台线程中执行阻塞的子进程调用
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        partial(
            _run_ffmpeg_extract_first_frame,
            video_filepath,
            output_path,
            width=width,
            height=height,
            image_format=image_format,
            quality=quality,
            sws_flags=sws_flags,
        ),
    )

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise Exception("ffmpeg 执行完成但未生成有效的首帧文件")

    return output_filename


def _run_ffmpeg_extract_first_frame(
    input_path: str,
    output_path: str,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    image_format: str = "png",
    quality: Optional[int] = None,
    sws_flags: Optional[str] = None,
) -> None:
    """
    同步执行 ffmpeg 提取首帧：
    ffmpeg -y -ss 0 -i input -frames:v 1 -q:v 2 output.png
    使用 -y 覆盖输出、-frames:v 1 只输出一帧。
    """
    # 构建命令
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        "0",
        "-i",
        input_path,
        "-frames:v",
        "1",
    ]

    # 处理缩放
    scale_filter = None
    if width or height:
        # -1 表示按比例自适应
        w = width if (isinstance(width, int) and width > 0) else -1
        h = height if (isinstance(height, int) and height > 0) else -1
        scale_filter = f"scale={w}:{h}"
        cmd.extend(["-vf", scale_filter])
        if sws_flags:
            cmd.extend(["-sws_flags", sws_flags])

    # 格式与质量
    fmt = image_format.lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt == "jpg":
        # 2(高质量)-31(低质量)
        q = quality if (isinstance(quality, int) and 2 <= quality <= 31) else 2
        cmd.extend(["-q:v", str(q)])
    elif fmt == "png":
        # 最高“清晰度”采用无压缩（仅影响体积与编码时间，不损失质量）
        # 强制 24 位色彩避免调色板/低位深
        cmd.extend(["-compression_level", "0", "-pix_fmt", "rgb24"])

    cmd.append(output_path)

    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
        if completed.returncode != 0:
            raise Exception(f"ffmpeg 失败: {completed.stderr.strip()}")
    except FileNotFoundError:
        raise Exception("未找到 ffmpeg，请先安装并确保在 PATH 中可用")



async def extract_last_frame(
    video_filepath: str,
    width: Optional[int] = None,
    height: Optional[int] = None,
    image_format: str = "png",
    quality: Optional[int] = None,
    sws_flags: Optional[str] = None,
) -> str:
    """
    提取视频文件的尾帧为图片，返回生成的文件名（不含路径）。

    参数与 `extract_first_frame` 一致。
    """
    output_dir = "frames"
    os.makedirs(output_dir, exist_ok=True)

    file_id = str(uuid.uuid4())
    fmt = image_format.lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt not in {"png", "jpg"}:
        fmt = "png"
    output_filename = f"{file_id}.{fmt}"
    output_path = os.path.join(output_dir, output_filename)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        partial(
            _run_ffmpeg_extract_last_frame,
            video_filepath,
            output_path,
            width=width,
            height=height,
            image_format=image_format,
            quality=quality,
            sws_flags=sws_flags,
        ),
    )

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise Exception("ffmpeg 执行完成但未生成有效的尾帧文件")

    return output_filename


def _run_ffmpeg_extract_last_frame(
    input_path: str,
    output_path: str,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    image_format: str = "png",
    quality: Optional[int] = None,
    sws_flags: Optional[str] = None,
) -> None:
    """
    同步执行 ffmpeg 提取尾帧：
    通过从结尾处 seek（-sseof -0.1）再输出 1 帧实现。
    例：ffmpeg -y -sseof -0.1 -i input -frames:v 1 output.png
    """
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-sseof",
        "-0.1",
        "-i",
        input_path,
        "-frames:v",
        "1",
    ]

    # 处理缩放
    if width or height:
        w = width if (isinstance(width, int) and width > 0) else -1
        h = height if (isinstance(height, int) and height > 0) else -1
        scale_filter = f"scale={w}:{h}"
        cmd.extend(["-vf", scale_filter])
        if sws_flags:
            cmd.extend(["-sws_flags", sws_flags])

    fmt = image_format.lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt == "jpg":
        q = quality if (isinstance(quality, int) and 2 <= quality <= 31) else 2
        cmd.extend(["-q:v", str(q)])
    elif fmt == "png":
        cmd.extend(["-compression_level", "0", "-pix_fmt", "rgb24"]) 

    cmd.append(output_path)

    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
        if completed.returncode != 0:
            raise Exception(f"ffmpeg 失败: {completed.stderr.strip()}")
    except FileNotFoundError:
        raise Exception("未找到 ffmpeg，请先安装并确保在 PATH 中可用")

