"""
MP3 到 MIDI 转换模块
使用 Spotify 的 Basic Pitch 库进行音频转 MIDI 转换
"""

import os
import uuid
import asyncio
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH

async def mp3_to_midi(mp3_filepath: str) -> str:
    """
    将 MP3 文件转换为 MIDI 文件
    
    Args:
        mp3_filepath: MP3 文件的路径
        
    Returns:
        str: 生成的 MIDI 文件名
        
    Raises:
        Exception: 转换失败时抛出异常
    """
    try:
        # 生成唯一的输出文件名
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}.mid"
        
        # 确保输出目录存在
        output_dir = "midis"
        os.makedirs(output_dir, exist_ok=True)
        
        # 使用 asyncio 在线程池中运行阻塞的转换操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            _convert_to_midi_sync,
            mp3_filepath,
            output_dir,
            file_id
        )
        
        return output_filename
        
    except Exception as e:
        raise Exception(f"MIDI 转换失败: {str(e)}")

def _convert_to_midi_sync(mp3_filepath: str, output_dir: str, file_id: str) -> None:
    """
    同步版本的 MIDI 转换函数
    
    Args:
        mp3_filepath: MP3 文件路径
        output_dir: 输出目录
        file_id: 文件 ID
    """
    try:
        # 使用 Basic Pitch 进行转换
        # predict_and_save 会自动生成 .mid 文件
        predict_and_save(
            [mp3_filepath],                    # 输入音频文件列表
            output_dir,                        # 输出目录
            save_midi=True,                    # 保存 MIDI 文件
            sonify_midi=False,                 # 不生成音频预览
            save_model_outputs=False,          # 不保存模型中间输出
            save_notes=False,                  # 不保存音符文本文件
            model_path=ICASSP_2022_MODEL_PATH  # 使用预训练模型
        )
        
        # Basic Pitch 会根据输入文件名生成输出文件
        # 需要重命名为我们指定的文件名
        input_basename = os.path.splitext(os.path.basename(mp3_filepath))[0]
        generated_midi = os.path.join(output_dir, f"{input_basename}_basic_pitch.mid")
        target_midi = os.path.join(output_dir, f"{file_id}.mid")
        
        # 重命名文件
        if os.path.exists(generated_midi):
            os.rename(generated_midi, target_midi)
        else:
            # 如果找不到生成的文件，尝试其他可能的命名方式
            possible_files = [
                os.path.join(output_dir, f"{input_basename}.mid"),
                os.path.join(output_dir, f"{input_basename}_transcription.mid"),
            ]
            
            for possible_file in possible_files:
                if os.path.exists(possible_file):
                    os.rename(possible_file, target_midi)
                    break
            else:
                # 如果所有可能的文件都不存在，抛出异常
                raise Exception("Basic Pitch 转换完成但找不到输出的 MIDI 文件")
                
    except Exception as e:
        raise Exception(f"Basic Pitch 转换错误: {str(e)}")

def cleanup_generated_files(output_dir: str, input_basename: str) -> None:
    """
    清理 Basic Pitch 可能生成的其他文件
    
    Args:
        output_dir: 输出目录
        input_basename: 输入文件的基础名称
    """
    try:
        # Basic Pitch 可能生成的其他文件
        cleanup_patterns = [
            f"{input_basename}_basic_pitch.csv",
            f"{input_basename}_basic_pitch.json",
            f"{input_basename}_basic_pitch_sonified.wav",
        ]
        
        for pattern in cleanup_patterns:
            filepath = os.path.join(output_dir, pattern)
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception:
        # 忽略清理失败
        pass 