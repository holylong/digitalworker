"""
Opus编码工具类
将PCM音频数据编码为Opus格式
"""

import logging
import traceback

import numpy as np
from typing import List, Optional
from opuslib_next import Encoder
from opuslib_next import constants


class OpusEncoderUtils:
    """PCM到Opus的编码器（单例模式）"""

    _instance = None
    _encoder = None
    _sample_rate = 16000
    _channels = 1
    _frame_size_ms = 60
    _frame_size = 960  # 60ms @ 16kHz
    _total_frame_size = 960  # 单声道
    _bitrate = 16000
    _complexity = 5
    _buffer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, sample_rate: int = 16000, channels: int = 1, frame_size_ms: int = 60):
        if self._initialized:
            return

        self._initialized = True
        self._sample_rate = sample_rate
        self._channels = channels
        self._frame_size_ms = frame_size_ms
        # 计算每帧样本数 = 采样率 * 帧大小(毫秒) / 1000
        self._frame_size = (sample_rate * frame_size_ms) // 1000
        # 总帧大小 = 每帧样本数 * 通道数
        self._total_frame_size = self._frame_size * channels

        # 比特率和复杂度设置（与终端匹配）
        self._bitrate = 16000  # bps，与终端的 16 kbps 匹配
        self._complexity = 5  # 中等复杂度，与终端匹配

        # 缓冲区初始化为空
        import numpy as np
        self._buffer = np.array([], dtype=np.int16)

        self._init_encoder()

    def _init_encoder(self):
        """初始化编码器"""
        try:
            # 创建Opus编码器
            self._encoder = Encoder(
                self._sample_rate, self._channels, constants.APPLICATION_VOIP  # VOIP模式，与终端匹配
            )
            self._encoder.bitrate = self._bitrate
            self._encoder.complexity = self._complexity
            self._encoder.signal = constants.SIGNAL_VOICE  # 语音信号优化
            logging.info(f"Opus编码器初始化成功: {self._sample_rate}Hz, {self._channels}通道")
        except Exception as e:
            logging.error(f"初始化Opus编码器失败: {e}")
            raise RuntimeError("初始化失败") from e

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reset_state(self):
        """重置编码器状态"""
        self.encoder.reset_state()
        self.buffer = np.array([], dtype=np.int16)

    def encode_pcm_to_opus(self, pcm_data: bytes, end_of_stream: bool) -> List[bytes]:
        """
        将PCM数据编码为Opus格式

        Args:
            pcm_data: PCM字节数据
            end_of_stream: 是否为流的结束

        Returns:
            Opus数据包列表
        """
        # 将字节数据转换为short数组
        new_samples = self._convert_bytes_to_shorts(pcm_data)

        # 校验PCM数据
        self._validate_pcm_data(new_samples)

        # 将新数据追加到缓冲区
        self._buffer = np.append(self._buffer, new_samples)

        opus_packets = []
        offset = 0

        # 处理所有完整帧
        while offset <= len(self._buffer) - self._total_frame_size:
            frame = self._buffer[offset : offset + self._total_frame_size]
            output = self._encode(frame)
            if output:
                opus_packets.append(output)
            offset += self._total_frame_size

        # 保留未处理的样本
        self._buffer = self._buffer[offset:]

        # 流结束时处理剩余数据
        # 注意：不编码零填充的帧，避免客户端解码器崩溃
        # 如果剩余数据不足一帧，直接丢弃
        if end_of_stream:
            self._buffer = np.array([], dtype=np.int16)

        return opus_packets

    def _encode(self, frame: np.ndarray) -> Optional[bytes]:
        """编码一帧音频数据"""
        try:
            # 将numpy数组转换为bytes
            frame_bytes = frame.tobytes()
            # opuslib要求输入字节数必须是channels*2的倍数
            encoded = self._encoder.encode(frame_bytes, self._frame_size)
            return encoded
        except Exception as e:
            logging.error(f"Opus编码失败: {e}")
            traceback.print_exc()
            return None

    def _convert_bytes_to_shorts(self, bytes_data: bytes) -> np.ndarray:
        """将字节数组转换为short数组 (16位PCM)"""
        # 假设输入是小端字节序的16位PCM
        return np.frombuffer(bytes_data, dtype=np.int16)

    def _validate_pcm_data(self, pcm_shorts: np.ndarray) -> None:
        """验证PCM数据是否有效"""
        # 16位PCM数据范围是 -32768 到 32767
        if np.any((pcm_shorts < -32768) | (pcm_shorts > 32767)):
            invalid_samples = pcm_shorts[(pcm_shorts < -32768) | (pcm_shorts > 32767)]
            logging.warning(f"发现无效PCM样本: {invalid_samples[:5]}...")
            # 在实际应用中可以选择裁剪而不是抛出异常
            # np.clip(pcm_shorts, -32768, 32767, out=pcm_shorts)

    def close(self):
        """关闭编码器并释放资源"""
        # opuslib没有明确的关闭方法，Python的垃圾回收会处理
        pass
