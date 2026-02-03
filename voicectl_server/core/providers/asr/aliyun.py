import http.client
import json
import asyncio
from typing import Optional, Tuple, List
import os
import uuid
import hmac
import hashlib
import base64
import requests
from urllib import parse
import time
from datetime import datetime
from config.logger import setup_logging
from core.providers.asr.base import ASRProviderBase
from core.providers.asr.dto.dto import InterfaceType

TAG = __name__
logger = setup_logging()

# 日志限流相关
_log_throttle_map = {}
_log_throttle_interval = 2.0  # 日志限流间隔2秒


def _should_log(log_key: str) -> bool:
    """检查是否应该输出日志（限流）"""
    current_time = time.time()
    last_log_time = _log_throttle_map.get(log_key, 0)
    if current_time - last_log_time >= _log_throttle_interval:
        _log_throttle_map[log_key] = current_time
        return True
    return False


class AccessToken:
    @staticmethod
    def _encode_text(text):
        encoded_text = parse.quote_plus(text)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def _encode_dict(dic):
        keys = dic.keys()
        dic_sorted = [(key, dic[key]) for key in sorted(keys)]
        encoded_text = parse.urlencode(dic_sorted)
        return encoded_text.replace("+", "%20").replace("*", "%2A").replace("%7E", "~")

    @staticmethod
    def create_token(access_key_id, access_key_secret):
        parameters = {
            "AccessKeyId": access_key_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid1()),
            "SignatureVersion": "1.0",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "Version": "2019-02-28",
        }
        # 构造规范化的请求字符串
        query_string = AccessToken._encode_dict(parameters)
        # print('规范化的请求字符串: %s' % query_string)
        # 构造待签名字符串
        string_to_sign = (
            "GET"
            + "&"
            + AccessToken._encode_text("/")
            + "&"
            + AccessToken._encode_text(query_string)
        )
        # print('待签名的字符串: %s' % string_to_sign)
        # 计算签名
        secreted_string = hmac.new(
            bytes(access_key_secret + "&", encoding="utf-8"),
            bytes(string_to_sign, encoding="utf-8"),
            hashlib.sha1,
        ).digest()
        signature = base64.b64encode(secreted_string)
        # print('签名: %s' % signature)
        # 进行URL编码
        signature = AccessToken._encode_text(signature)
        # print('URL编码后的签名: %s' % signature)
        # 调用服务
        full_url = "http://nls-meta.cn-shanghai.aliyuncs.com/?Signature=%s&%s" % (
            signature,
            query_string,
        )
        # print('url: %s' % full_url)
        # 提交HTTP GET请求
        response = requests.get(full_url)
        if response.ok:
            root_obj = response.json()
            key = "Token"
            if key in root_obj:
                token = root_obj[key]["Id"]
                expire_time = root_obj[key]["ExpireTime"]
                return token, expire_time
        # print(response.text)
        return None, None


class ASRProvider(ASRProviderBase):
    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__()
        self.interface_type = InterfaceType.NON_STREAM
        """阿里云ASR初始化"""
        # 新增空值判断逻辑
        self.access_key_id = config.get("access_key_id")
        self.access_key_secret = config.get("access_key_secret")

        self.app_key = config.get("appkey")
        self.host = "nls-gateway-cn-shanghai.aliyuncs.com"
        self.base_url = f"https://{self.host}/stream/v1/asr"
        self.sample_rate = 16000
        self.format = "wav"
        self.output_dir = config.get("output_dir", "./audio_output")
        self.delete_audio_file = delete_audio_file

        if self.access_key_id and self.access_key_secret:
            # 使用密钥对生成临时token
            self._refresh_token()
        else:
            # 直接使用预生成的长期token
            self.token = config.get("token")
            self.expire_time = None

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

    def _refresh_token(self):
        """刷新Token并记录过期时间"""
        if self.access_key_id and self.access_key_secret:
            self.token, expire_time_str = AccessToken.create_token(
                self.access_key_id, self.access_key_secret
            )
            if not expire_time_str:
                raise ValueError("无法获取有效的Token过期时间")

            try:
                # 统一转换为字符串处理
                expire_str = str(expire_time_str).strip()

                if expire_str.isdigit():
                    expire_time = datetime.fromtimestamp(int(expire_str))
                else:
                    expire_time = datetime.strptime(expire_str, "%Y-%m-%dT%H:%M:%SZ")
                self.expire_time = expire_time.timestamp() - 60
            except Exception as e:
                raise ValueError(f"无效的过期时间格式: {expire_str}") from e

        else:
            self.expire_time = None

        if not self.token:
            raise ValueError("无法获取有效的访问Token")

    def _is_token_expired(self):
        """检查Token是否过期"""
        if not self.expire_time:
            return False  # 长期Token不过期
        # 新增调试日志
        # current_time = time.time()
        # remaining = self.expire_time - current_time
        # print(f"Token过期检查: 当前时间 {datetime.fromtimestamp(current_time)} | "
        #              f"过期时间 {datetime.fromtimestamp(self.expire_time)} | "
        #              f"剩余 {remaining:.2f}秒")
        return time.time() > self.expire_time

    def _construct_request_url(self) -> str:
        """构造请求URL，包含参数"""
        request = f"{self.base_url}?appkey={self.app_key}"
        request += f"&format={self.format}"
        request += f"&sample_rate={self.sample_rate}"
        request += "&enable_punctuation_prediction=true"
        request += "&enable_inverse_text_normalization=true"
        request += "&enable_voice_detection=false"
        return request

    async def _send_request(self, pcm_data: bytes) -> Optional[str]:
        """发送请求到阿里云ASR服务"""
        try:
            # 设置HTTP头
            headers = {
                "X-NLS-Token": self.token,
                "Content-type": "application/octet-stream",
                "Content-Length": str(len(pcm_data)),
            }

            # 创建连接并发送请求
            conn = http.client.HTTPSConnection(self.host)
            request_url = self._construct_request_url()

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: conn.request(
                    method="POST", url=request_url, body=pcm_data, headers=headers
                ),
            )

            # 获取响应
            response = await loop.run_in_executor(None, conn.getresponse)
            body = await loop.run_in_executor(None, response.read)
            conn.close()

            # 解析响应
            try:
                body_json = json.loads(body)
                status = body_json.get("status")

                if status == 20000000:
                    result = body_json.get("result", "")
                    logger.bind(tag=TAG).debug(f"ASR结果: {result}")
                    return result
                else:
                    logger.bind(tag=TAG).error(f"ASR失败，状态码: {status}")
                    return None

            except ValueError:
                logger.bind(tag=TAG).error("响应不是JSON格式")
                return None

        except Exception as e:
            logger.bind(tag=TAG).error(f"ASR请求失败: {e}", exc_info=True)
            return None

    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, audio_format="opus", conn=None
    ) -> Tuple[Optional[str], Optional[str]]:
        """将语音数据转换为文本"""
        if self._is_token_expired():
            logger.warning("Token已过期，正在自动刷新...")
            self._refresh_token()

        file_path = None
        try:
            # 解码Opus为PCM
            if audio_format == "pcm":
                pcm_data = opus_data
            else:
                pcm_data = self.decode_opus(opus_data)
            combined_pcm_data = b"".join(pcm_data)

            # 判断是否保存为WAV文件
            if self.delete_audio_file:
                pass
            else:
                file_path = self.save_audio_to_file(pcm_data, session_id)

            # 发送请求并获取文本
            text = await self._send_request(combined_pcm_data)

            if text:
                return text, file_path

            return "", file_path

        except Exception as e:
            logger.bind(tag=TAG).error(f"语音识别失败: {e}", exc_info=True)
            return "", file_path
            
    async def receive_audio(self, conn, audio, audio_have_voice):
        """完全重写音频接收方法，处理实时音频流，确保送入完整的语音给ASR"""
        logger.bind(tag=TAG).debug(f"FunASR接收音频，长度: {len(audio)}，检测到语音: {audio_have_voice}")

        # 记录语音活动时间
        current_time = time.time() * 1000  # 毫秒

        # 将音频添加到缓冲区
        conn.asr_audio.append(audio)

        # 更新语音状态
        if audio_have_voice:
            conn.client_have_voice = True
            conn.client_voice_stop = False
            conn.last_voice_time = current_time
            logger.bind(tag=TAG).debug("检测到语音，更新状态")
        else:
            # 检查语音是否停止（超过一定时间没有语音）
            if hasattr(conn, 'last_voice_time'):
                silence_duration = current_time - conn.last_voice_time
                # 增加静默检测时间到2.5秒，避免说话中间的停顿被误判为语音结束
                if silence_duration > 1500:
                    conn.client_voice_stop = True
                    logger.bind(tag=TAG).info(f"检测到静默 {silence_duration}ms，标记语音停止")

        # 记录调试信息
        buffer_size = len(conn.asr_audio)
        if _should_log("audio_buffer_size"):
            logger.bind(tag=TAG).debug(f"音频缓冲区大小: {buffer_size}")

        # 自动模式或实时模式
        if conn.client_listen_mode == "auto" or conn.client_listen_mode == "realtime":
            have_voice = audio_have_voice
        else:
            have_voice = conn.client_have_voice

        if not have_voice and not conn.client_have_voice:
            # 没有语音，保留最后10帧作为前置缓冲，确保捕获语音开头
            conn.asr_audio = conn.asr_audio[-10:]

        # 只在检测到语音停止标记时处理音频
        if conn.client_voice_stop:
            logger.bind(tag=TAG).info("检测到语音停止标记，开始处理音频")
            
            # 先检查缓冲区长度，避免不必要的拷贝操作，送入asr的门槛长度越高 检测越不容易截断用户的话 但是体验将不够快，这里取2s的opus 16khz编码帧率
            # 开头预留10个无语音包+2*16语音包
            if len(conn.asr_audio) > 42:
                asr_audio_task = conn.asr_audio.copy()
                
                # 清空缓冲区并重置状态
                conn.asr_audio.clear()
                conn.reset_vad_states()
                conn.client_have_voice = False
                conn.client_voice_stop = False
                if hasattr(conn, 'last_voice_time'):
                    del conn.last_voice_time
                
                await self.handle_voice_stop(conn, asr_audio_task)
            else:
                # 音频片段过短，不清空缓冲区，保留数据继续等待更多音频
                # 只重置停止标记，让系统继续累积音频数据
                conn.client_voice_stop = False
                #logger.bind(tag=TAG).warning(f"音频片段过短（{len(conn.asr_audio)}帧），保留缓冲区继续等待")
        if len(conn.asr_audio) > 200:
            asr_audio_task = conn.asr_audio.copy()
            conn.asr_audio.clear()
            conn.reset_vad_states()
            conn.client_voice_stop = False
            conn.client_have_voice = False
            if hasattr(conn, 'last_voice_time'):
                del conn.last_voice_time
            await self.handle_voice_stop(conn, asr_audio_task)
        