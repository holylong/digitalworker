import time
import os
import sys
import io
import psutil
from config.logger import setup_logging
from typing import Optional, Tuple, List
from core.providers.asr.base import ASRProviderBase
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import shutil
from core.providers.asr.dto.dto import InterfaceType

TAG = __name__
logger = setup_logging()

MAX_RETRIES = 2
RETRY_DELAY = 1  # 重试延迟（秒）

# 日志限流相关
_log_throttle_map = {}
_log_throttle_interval = 2.0  # 日志限流间隔2秒


def _should_log(log_key: str) -> bool:
    """检查是否应该输出日志（限流）"""
    import time
    current_time = time.time()
    last_log_time = _log_throttle_map.get(log_key, 0)
    if current_time - last_log_time >= _log_throttle_interval:
        _log_throttle_map[log_key] = current_time
        return True
    return False


# 捕获标准输出
class CaptureOutput:
    def __enter__(self):
        self._output = io.StringIO()
        self._original_stdout = sys.stdout
        sys.stdout = self._output

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self._original_stdout
        self.output = self._output.getvalue()
        self._output.close()

        # 将捕获到的内容通过 logger 输出
        if self.output:
            logger.bind(tag=TAG).info(self.output.strip())


class ASRProvider(ASRProviderBase):
    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__()

        logger.bind(tag=TAG).debug(f'====>> asr provider')
        
        # 内存检测，要求大于2G
        min_mem_bytes = 2 * 1024 * 1024 * 1024
        total_mem = psutil.virtual_memory().total
        if total_mem < min_mem_bytes:
            logger.bind(tag=TAG).error(f"可用内存不足2G，当前仅有 {total_mem / (1024*1024):.2f} MB，可能无法启动FunASR")
        
        self.interface_type = InterfaceType.LOCAL
        self.model_dir = config.get("model_dir")
        self.output_dir = config.get("output_dir")  # 修正配置键名
        self.delete_audio_file = delete_audio_file

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        with CaptureOutput():
            self.model = AutoModel(
                model=self.model_dir,
                vad_kwargs={"max_single_segment_time": 30000},
                disable_update=True,
                hub="hf",
                # device="cuda:0",  # 启用GPU加速
            )

    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, audio_format="opus", conn=None
    ) -> Tuple[Optional[str], Optional[str]]:
        """语音转文本主处理逻辑"""
        file_path = None
        retry_count = 0
        logger.bind(tag=TAG).debug(f'======================================>> speech to text')
        while retry_count < MAX_RETRIES:
            try:
                # 合并所有opus数据包
                if audio_format == "pcm":
                    pcm_data = opus_data
                else:
                    pcm_data = self.decode_opus(opus_data)

                combined_pcm_data = b"".join(pcm_data)

                # 检查磁盘空间
                if not self.delete_audio_file:
                    free_space = shutil.disk_usage(self.output_dir).free
                    if free_space < len(combined_pcm_data) * 2:  # 预留2倍空间
                        raise OSError("磁盘空间不足")

                # 判断是否保存为WAV文件
                if self.delete_audio_file:
                    pass
                else:
                    file_path = self.save_audio_to_file(pcm_data, session_id)

                logger.bind(tag=TAG).debug(f'======================================>> {file_path}')
                # 语音识别 - 使用conn.asr_cache来提高连续识别准确率
                start_time = time.time()
                
                # 获取缓存，如果没有conn则使用空字典
                cache = conn.asr_cache if conn and hasattr(conn, 'asr_cache') else {}
                
                result = self.model.generate(
                    input=combined_pcm_data,
                    cache=cache,
                    language="zn",
                    use_itn=True,
                    batch_size_s=60,
                )
                text = rich_transcription_postprocess(result[0]["text"])
                logger.bind(tag=TAG).debug(
                    f"语音识别耗时: {time.time() - start_time:.3f}s | 结果: {text}"
                )

                return text, file_path

            except OSError as e:
                retry_count += 1
                if retry_count >= MAX_RETRIES:
                    logger.bind(tag=TAG).error(
                        f"语音识别失败（已重试{retry_count}次）: {e}", exc_info=True
                    )
                    return "", file_path
                logger.bind(tag=TAG).warning(
                    f"语音识别失败，正在重试（{retry_count}/{MAX_RETRIES}）: {e}"
                )
                time.sleep(RETRY_DELAY)

            except Exception as e:
                logger.bind(tag=TAG).error(f"语音识别失败: {e}", exc_info=True)
                return "", file_path

            finally:
                # 文件清理逻辑
                if self.delete_audio_file and file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.bind(tag=TAG).debug(f"已删除临时音频文件: {file_path}")
                    except Exception as e:
                        logger.bind(tag=TAG).error(
                            f"文件删除失败: {file_path} | 错误: {e}"
                        )

    async def receive_audio(self, conn, audio, audio_have_voice):
        logger.bind(tag=TAG).debug(f"FunASR接收音频，长度: {len(conn.asr_audio)}，检测到语音: {audio_have_voice}")

        # 记录语音活动时间
        current_time = time.time() * 1000  # 毫秒

        # 将音频添加到缓冲区
        conn.asr_audio.append(audio)

        # 会议模式下的特殊处理
        if hasattr(conn, 'is_in_meeting') and conn.is_in_meeting:
            # 初始化语音帧计数器
            if not hasattr(conn, 'meeting_voice_frame_count'):
                conn.meeting_voice_frame_count = 0
            
            # 统计语音帧数量
            if audio_have_voice:
                conn.meeting_voice_frame_count += 1
            
            # 会议模式下最多缓存50帧音频数据
            MEETING_MAX_BUFFER_SIZE = 50
            if len(conn.asr_audio) >= MEETING_MAX_BUFFER_SIZE:
                # 检查语音帧数是否大于2
                if conn.meeting_voice_frame_count > 2:
                    logger.bind(tag=TAG).info(
                        f"会议模式：缓冲区达到{len(conn.asr_audio)}帧，语音帧数{conn.meeting_voice_frame_count}，送入ASR处理"
                    )
                    asr_audio_task = conn.asr_audio.copy()
                    conn.asr_audio.clear()
                    conn.reset_vad_states()
                    conn.meeting_voice_frame_count = 0
                    await self.handle_voice_stop(conn, asr_audio_task)
                else:
                    # 语音帧数不足，清空缓冲区继续等待
                    logger.bind(tag=TAG).debug(
                        f"会议模式：缓冲区达到{len(conn.asr_audio)}帧，但语音帧数{conn.meeting_voice_frame_count}不足，清空缓冲区"
                    )
                    conn.asr_audio.clear()
                    conn.meeting_voice_frame_count = 0
            return
        
        # 非会议模式：防止缓冲区无限增长，设置最大缓冲区大小（500帧约30秒）
        MAX_BUFFER_SIZE = 500
        if len(conn.asr_audio) > MAX_BUFFER_SIZE:
            logger.bind(tag=TAG).warning(
                f"缓冲区过大（{len(conn.asr_audio)}帧），送入ASR处理"
            )
            asr_audio_task = conn.asr_audio.copy()
            conn.asr_audio.clear()
            conn.reset_vad_states()
            if hasattr(conn, 'last_voice_time'):
                del conn.last_voice_time
            await self.handle_voice_stop(conn, asr_audio_task)



