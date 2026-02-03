"""
Opus解码工具类
将Opus音频数据解码为PCM格式
"""

import logging
import traceback

from opuslib_next import Decoder
from typing import Optional


class OpusDecoderUtils:
    """Opus到PCM的解码器（单例模式）"""

    _instance = None
    _decoder = None
    _sample_rate = 16000
    _channels = 1
    _frame_size = 960  # 60ms @ 16kHz

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._init_decoder()

    def _init_decoder(self):
        """初始化解码器"""
        try:
            self._decoder = Decoder(self._sample_rate, self._channels)
            logging.info(f"Opus解码器初始化成功: {self._sample_rate}Hz, {self._channels}通道")
        except Exception as e:
            logging.error(f"初始化Opus解码器失败: {e}")
            raise RuntimeError("初始化失败") from e

    def reset_decoder(self):
        """重置解码器状态"""
        try:
            if self._decoder:
                self._decoder.reset_state()
                logging.debug("Opus解码器状态已重置")
        except Exception as e:
            logging.error(f"重置Opus解码器失败: {e}")

    def decode_opus_to_pcm(self, opus_data: bytes) -> Optional[bytes]:
        """
        将Opus数据解码为PCM格式

        Args:
            opus_data: Opus字节数据

        Returns:
            PCM字节数据（16位小端）
        """
        try:
            if not opus_data:
                logging.warning("Opus数据为空")
                return None

            # 解码Opus数据
            pcm_data = self._decoder.decode(opus_data, self._frame_size)
            return pcm_data
        except Exception as e:
            logging.error(f"Opus解码失败: {e}")
            traceback.print_exc()
            return None

    def decode_opus_list_to_pcm(self, opus_list: list) -> Optional[bytes]:
        """
        将Opus数据列表解码为PCM格式

        Args:
            opus_list: Opus字节数据列表

        Returns:
            PCM字节数据（16位小端）
        """
        try:
            if not opus_list:
                logging.warning("Opus数据列表为空")
                return None

            pcm_data_list = []
            for opus_data in opus_list:
                pcm_data = self.decode_opus_to_pcm(opus_data)
                if pcm_data:
                    pcm_data_list.append(pcm_data)

            if not pcm_data_list:
                logging.warning("没有有效的PCM数据")
                return None

            # 合并所有PCM数据
            return b"".join(pcm_data_list)
        except Exception as e:
            logging.error(f"Opus列表解码失败: {e}")
            traceback.print_exc()
            return None

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
