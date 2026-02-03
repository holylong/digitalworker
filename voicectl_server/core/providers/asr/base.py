import os
import wave
import uuid
import queue
import asyncio
import traceback
import threading
import opuslib_next
import json
import io
import time
import concurrent.futures
from abc import ABC, abstractmethod
from config.logger import setup_logging
from typing import Optional, Tuple, List, Dict, Any
from core.handle.receiveAudioHandle import startToChat
from core.handle.reportHandle import enqueue_asr_report
from core.utils.util import remove_punctuation_and_length
from core.handle.receiveAudioHandle import handleAudioMessage
from core.utils.voiceprint_provider import VoiceprintProvider

TAG = __name__
logger = setup_logging()

import time
import wave
import json
import threading
from pathlib import Path


class ASRProviderBase(ABC):
    def __init__(self):
        self.voiceprint_provider = None
        logger.bind(tag=TAG).debug(f'====>> asr provider')
    
    # 在类中添加以下方法
    def setup_audio_recording(self, conn):
        """创建音频保存目录和文件"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        conn.audio_save_dir = Path("asr_audio_recordings") / f"session_{timestamp}"
        conn.audio_save_dir.mkdir(parents=True, exist_ok=True)
        logger.bind(tag=TAG).debug(f'===>> path {conn.audio_save_dir}')
        
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

    def init_voiceprint(self, voiceprint_config: dict):
        """初始化声纹识别"""
        if voiceprint_config:
            self.voiceprint_provider = VoiceprintProvider(voiceprint_config)
            logger.bind(tag=TAG).info("声纹识别模块已初始化")

    # 打开音频通道
    async def open_audio_channels(self, conn):
        conn.asr_priority_thread = threading.Thread(
            target=self.asr_text_priority_thread, args=(conn,), daemon=True
        )
        conn.asr_priority_thread.start()

    # 有序处理ASR音频
    def asr_text_priority_thread(self, conn):
        self.setup_audio_recording(conn)
        while not conn.stop_event.is_set():
            try:
                message = conn.asr_audio_queue.get(timeout=1)
                # 保存音频数据（假设message直接包含音频bytes）
                self.save_audio_data(conn, message)
                future = asyncio.run_coroutine_threadsafe(
                    handleAudioMessage(conn, message),
                    conn.loop,
                )
                future.result()
            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"处理ASR文本失败: {str(e)}, 类型: {type(e).__name__}, 堆栈: {traceback.format_exc()}"
                )
                continue

    # 接收音频
    async def receive_audio(self, conn, audio, audio_have_voice):
        if conn.client_listen_mode == "auto" or conn.client_listen_mode == "realtime":
            have_voice = audio_have_voice
        else:
            have_voice = conn.client_have_voice
        
        conn.asr_audio.append(audio)
        if not have_voice and not conn.client_have_voice:
            conn.asr_audio = conn.asr_audio[-10:]
            return

        if conn.client_voice_stop:
            asr_audio_task = conn.asr_audio.copy()
            conn.asr_audio.clear()
            conn.reset_vad_states()

            if len(asr_audio_task) > 15:
                await self.handle_voice_stop(conn, asr_audio_task)

    # 处理语音停止
    async def handle_voice_stop(self, conn, asr_audio_task: List[bytes]):
        """并行处理ASR和声纹识别"""
        try:
            total_start_time = time.monotonic()
            logger.bind(tag=TAG).info(f'=======================================>> handle voicde')
            # 准备音频数据
            if conn.audio_format == "pcm":
                pcm_data = asr_audio_task
            else:
                logger.bind(tag=TAG).info(f'=======================================>> decode opus')
                pcm_data = self.decode_opus(asr_audio_task)
            
            combined_pcm_data = b"".join(pcm_data)
            
            # 预先准备WAV数据
            wav_data = None
            logger.bind(tag=TAG).info(f'=======================================>> wav data none')
            if self.voiceprint_provider and combined_pcm_data:
                logger.bind(tag=TAG).info(f'=======================================>> pcm to wav')
                wav_data = self._pcm_to_wav(combined_pcm_data)
                self.save_wav(wav_data, "abd.wav")
            
            # 定义ASR任务
            def run_asr():
                logger.bind(tag=TAG).info(f'=======================================>> run asr')
                start_time = time.monotonic()
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        logger.bind(tag=TAG).info(f'=======================================>> speech_to_text {conn.session_id}  {conn.audio_format}')
                        result = loop.run_until_complete(
                            self.speech_to_text(asr_audio_task, conn.session_id, conn.audio_format, conn)
                        )
                        end_time = time.monotonic()
                        logger.bind(tag=TAG).info(f"ASR耗时: {end_time - start_time:.3f}s")
                        return result
                    finally:
                        loop.close()
                except Exception as e:
                    end_time = time.monotonic()
                    logger.bind(tag=TAG).error(f"ASR失败: {e}")
                    return ("", None)
            
            # 定义声纹识别任务
            def run_voiceprint():
                if not wav_data:
                    return None
                start_time = time.monotonic()
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            self.voiceprint_provider.identify_speaker(wav_data, conn.session_id)
                        )
                        return result
                    finally:
                        loop.close()
                except Exception as e:
                    logger.bind(tag=TAG).error(f"声纹识别失败: {e}")
                    return None
            
            # 使用线程池执行器并行运行
            parallel_start_time = time.monotonic()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as thread_executor:
                asr_future = thread_executor.submit(run_asr)
                
                if self.voiceprint_provider and wav_data:
                    voiceprint_future = thread_executor.submit(run_voiceprint)
                    
                    # 等待两个线程都完成
                    asr_result = asr_future.result(timeout=15)
                    voiceprint_result = voiceprint_future.result(timeout=15)
                    
                    results = {"asr": asr_result, "voiceprint": voiceprint_result}
                else:
                    asr_result = asr_future.result(timeout=15)
                    results = {"asr": asr_result, "voiceprint": None}
            
            parallel_execution_time = time.monotonic() - parallel_start_time
            
            # 处理结果
            raw_text, file_path = results.get("asr", ("", None))
            speaker_name = results.get("voiceprint", None)
            
            # 记录识别结果
            if raw_text:
                logger.bind(tag=TAG).info(f"识别文本: {raw_text}")
            if speaker_name:
                logger.bind(tag=TAG).info(f"识别说话人: {speaker_name}")
            
            # 性能监控
            total_time = time.monotonic() - total_start_time
            logger.bind(tag=TAG).info(f"总处理耗时: {total_time:.3f}s")
            
            # 检查文本长度
            text_len, _ = remove_punctuation_and_length(raw_text)
            self.stop_ws_connection()
            
            if text_len > 0:
                # 构建包含说话人信息的JSON字符串
                enhanced_text = self._build_enhanced_text(raw_text, speaker_name)
                
                # 使用自定义模块进行上报（非阻塞，避免阻塞音频处理线程）
                asyncio.create_task(startToChat(conn, enhanced_text))
                enqueue_asr_report(conn, enhanced_text, asr_audio_task)
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"处理语音停止失败: {e}")
            import traceback
            logger.bind(tag=TAG).debug(f"异常详情: {traceback.format_exc()}")

    def _build_enhanced_text(self, text: str, speaker_name: Optional[str]) -> str:
        """构建包含说话人信息的文本"""
        if speaker_name and speaker_name.strip():
            return json.dumps({
                "speaker": speaker_name,
                "content": text
            }, ensure_ascii=False)
        else:
            return text


    def save_wav(self, wav_data: bytes, output_path: str) -> bool:
        """
        将频数据保存为WAV文件
        :param wav_data: WAV格式的原始音频数据
        :param output_path: 输出的WAV文件路径
        :return: 成功返回True，失败返回False
        """
        # 检查输入数据
        if not wav_data:
            logger.bind(tag=TAG).debug("错误：WAV数据为空")
            return False

        # 写入WAV文件
        try:
            with open(output_path, 'wb') as wav_file:
                wav_file.write(wav_data)
            logger.bind(tag=TAG).debug(f"WAV文件保存成功: {output_path}")
            return True
        except Exception as e:
            logger.bind(tag=TAG).debug(f"保存失败: {str(e)}")
            return False

    def _pcm_to_wav(self, pcm_data: bytes) -> bytes:
        """将PCM数据转换为WAV格式"""
        if len(pcm_data) == 0:
            logger.bind(tag=TAG).warning("PCM数据为空，无法转换WAV")
            return b""
        
        # 确保数据长度是偶数（16位音频）
        if len(pcm_data) % 2 != 0:
            pcm_data = pcm_data[:-1]
        
        # 创建WAV文件头
        wav_buffer = io.BytesIO()
        try:
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)      # 单声道
                wav_file.setsampwidth(2)      # 16位
                wav_file.setframerate(16000)  # 16kHz采样率
                wav_file.writeframes(pcm_data)
            
            wav_buffer.seek(0)
            wav_data = wav_buffer.read()
            
            return wav_data
        except Exception as e:
            logger.bind(tag=TAG).error(f"WAV转换失败: {e}")
            return b""

    def stop_ws_connection(self):
        pass

    def save_audio_to_file(self, pcm_data: List[bytes], session_id: str) -> str:
        """PCM数据保存为WAV文件"""
        module_name = __name__.split(".")[-1]
        file_name = f"asr_{module_name}_{session_id}_{uuid.uuid4()}.wav"
        file_path = os.path.join(self.output_dir, file_name)

        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 2 bytes = 16-bit
            wf.setframerate(16000)
            wf.writeframes(b"".join(pcm_data))

        return file_path

    @abstractmethod
    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, audio_format="opus", conn=None
    ) -> Tuple[Optional[str], Optional[str]]:
        """将语音数据转换为文本"""
        pass

    @staticmethod
    def decode_opus(opus_data: List[bytes]) -> List[bytes]:
        """将Opus音频数据解码为PCM数据"""
        try:
            decoder = opuslib_next.Decoder(16000, 1)
            pcm_data = []
            buffer_size = 960  # 每次处理960个采样点 (60ms at 16kHz)
            
            for i, opus_packet in enumerate(opus_data):
                try:
                    if not opus_packet or len(opus_packet) == 0:
                        continue
                    
                    pcm_frame = decoder.decode(opus_packet, buffer_size)
                    if pcm_frame and len(pcm_frame) > 0:
                        pcm_data.append(pcm_frame)
                        
                except opuslib_next.OpusError as e:
                    logger.bind(tag=TAG).warning(f"Opus解码错误，跳过数据包 {i}: {e}")
                except Exception as e:
                    logger.bind(tag=TAG).error(f"音频处理错误，数据包 {i}: {e}")
            
            return pcm_data
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"音频解码过程发生错误: {e}")
            return []
