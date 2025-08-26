"""
音频转换工具模块
使用 pydub 库进行 MP3 到 WAV 转换
"""

import os
import uuid
import asyncio
from pydub import AudioSegment

async def mp3_to_wav(mp3_filepath: str) -> str:
    """
    将 MP3 文件转换为 WAV 文件
    
    Args:
        mp3_filepath: MP3 文件的路径
        
    Returns:
        str: 生成的 WAV 文件名
        
    Raises:
        Exception: 转换失败时抛出异常
    """
    try:
        # 生成唯一的输出文件名
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}.wav"
        
        # 确保输出目录存在
        output_dir = "wavs"
        os.makedirs(output_dir, exist_ok=True)
        
        # 使用 asyncio 在线程池中运行阻塞的转换操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            _convert_to_wav_sync,
            mp3_filepath,
            output_dir,
            output_filename
        )
        
        return output_filename
        
    except Exception as e:
        raise Exception(f"WAV 转换失败: {str(e)}")

def _convert_to_wav_sync(mp3_filepath: str, output_dir: str, output_filename: str) -> None:
    """
    同步版本的 WAV 转换函数
    
    Args:
        mp3_filepath: MP3 文件路径
        output_dir: 输出目录
        output_filename: 输出文件名
    """
    try:
        # 使用 pydub 加载 MP3 文件
        audio = AudioSegment.from_mp3(mp3_filepath)
        
        # 构建输出文件路径
        output_path = os.path.join(output_dir, output_filename)
        
        # 导出为 WAV 格式
        # 设置常用的 WAV 格式参数
        audio.export(
            output_path,
            format="wav",
            parameters=[
                "-ar", "44100",     # 采样率 44.1kHz
                "-ac", "2",         # 立体声（2声道）
                "-sample_fmt", "s16" # 16位采样
            ]
        )
        
    except Exception as e:
        raise Exception(f"pydub 转换错误: {str(e)}")

async def get_audio_info(mp3_filepath: str) -> dict:
    """
    获取音频文件信息
    
    Args:
        mp3_filepath: MP3 文件路径
        
    Returns:
        dict: 包含音频信息的字典
    """
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None,
            _get_audio_info_sync,
            mp3_filepath
        )
        return info
        
    except Exception as e:
        raise Exception(f"获取音频信息失败: {str(e)}")

def _get_audio_info_sync(mp3_filepath: str) -> dict:
    """
    同步版本的获取音频信息函数
    
    Args:
        mp3_filepath: MP3 文件路径
        
    Returns:
        dict: 音频信息
    """
    try:
        audio = AudioSegment.from_mp3(mp3_filepath)
        
        return {
            "duration_seconds": len(audio) / 1000.0,  # 时长（秒）
            "frame_rate": audio.frame_rate,           # 采样率
            "channels": audio.channels,               # 声道数
            "sample_width": audio.sample_width,       # 采样位深
            "frame_count": audio.frame_count(),       # 帧数
            "max_possible_amplitude": audio.max_possible_amplitude  # 最大振幅
        }
        
    except Exception as e:
        raise Exception(f"读取音频信息错误: {str(e)}")

def convert_audio_format(
    input_filepath: str, 
    output_filepath: str, 
    output_format: str = "wav",
    **kwargs
) -> None:
    """
    通用音频格式转换函数
    
    Args:
        input_filepath: 输入文件路径
        output_filepath: 输出文件路径
        output_format: 输出格式 (wav, mp3, flac, etc.)
        **kwargs: 其他导出参数
    """
    try:
        # 自动检测输入格式
        if input_filepath.lower().endswith('.mp3'):
            audio = AudioSegment.from_mp3(input_filepath)
        elif input_filepath.lower().endswith('.wav'):
            audio = AudioSegment.from_wav(input_filepath)
        elif input_filepath.lower().endswith('.flac'):
            audio = AudioSegment.from_file(input_filepath, "flac")
        else:
            # 尝试自动检测
            audio = AudioSegment.from_file(input_filepath)
        
        # 导出为指定格式
        audio.export(output_filepath, format=output_format, **kwargs)
        
    except Exception as e:
        raise Exception(f"音频格式转换错误: {str(e)}") 