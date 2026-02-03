import os
import time
import wave
import json
import threading
from pathlib import Path

# 在类中添加以下方法
def setup_audio_recording(self, conn):
    """创建音频保存目录和文件"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    conn.audio_save_dir = Path("asr_audio_recordings") / f"session_{timestamp}"
    conn.audio_save_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建原始音频文件
    conn.raw_audio_file = conn.audio_save_dir / "audio.raw"
    conn.param_file = conn.audio_save_dir / "audio_params.json"
    
    # 记录音频参数（需要根据您的实际音频格式修改）
    audio_params = {
        "sample_rate": 16000,     # 采样率
        "sample_width": 2,        # 样本宽度（字节数）
        "channels": 1,            # 通道数
        "format": "pcm",          # 音频格式
        "endian": "little",       # 字节序
        "signed": True            # 是否有符号
    }
    
    # 保存参数到JSON文件
    with open(conn.param_file, "w") as f:
        json.dump(audio_params, f, indent=4)
    
    conn.audio_writer = open(conn.raw_audio_file, "wb")
    conn.write_lock = threading.Lock()

def save_audio_data(self, conn, audio_data):
    """安全地将音频数据写入文件"""
    with conn.write_lock:
        try:
            conn.audio_writer.write(audio_data)
            conn.audio_writer.flush()
        except Exception as e:
            logger.bind(tag=TAG).error(f"音频写入失败: {str(e)}")

def close_audio_writer(self, conn):
    """关闭音频写入器"""
    if hasattr(conn, 'audio_writer'):
        with conn.write_lock:
            conn.audio_writer.close()
        logger.bind(tag=TAG).info(f"ASR音频已保存到: {conn.raw_audio_file}")
        logger.bind(tag=TAG).info(f"音频参数文件: {conn.param_file}")

def convert_to_wav(self, conn):
    """将RAW文件转换为WAV格式（可选）"""
    raw_path = conn.raw_audio_file
    wav_path = raw_path.with_suffix(".wav")
    
    if not raw_path.exists():
        return
    
    # 从参数文件中获取音频参数
    with open(conn.param_file, "r") as f:
        params = json.load(f)
    
    # 读取原始音频数据
    with open(raw_path, "rb") as raw_file:
        raw_data = raw_file.read()
    
    # 写入WAV文件
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(params["channels"])
        wav_file.setsampwidth(params["sample_width"])
        wav_file.setframerate(params["sample_rate"])
        wav_file.writeframes(raw_data)
    
    logger.bind(tag=TAG).info(f"已创建可播放的WAV文件: {wav_path}")