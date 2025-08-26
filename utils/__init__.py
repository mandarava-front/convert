"""
音频转换工具包
包含 MP3 → MIDI 和 MP3 → WAV 转换功能
"""

from .convert import mp3_to_midi
from .audio_tools import mp3_to_wav, get_audio_info, convert_audio_format
from .video_tools import extract_first_frame

__all__ = [
    "mp3_to_midi",
    "mp3_to_wav", 
    "get_audio_info",
    "convert_audio_format",
    "extract_first_frame",
] 