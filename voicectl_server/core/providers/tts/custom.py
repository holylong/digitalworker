import os
import json
import uuid
import aiohttp
from config.logger import setup_logging
from datetime import datetime
from core.providers.tts.base import TTSProviderBase

TAG = __name__
logger = setup_logging()

class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.url = config.get("url")
        self.method = config.get("method", "GET")
        self.headers = config.get("headers", {})
        self.format = config.get("format", "wav")
        self.audio_file_type = config.get("format", "wav")
        self.output_file = config.get("output_dir", "tmp/")
        self.params = config.get("params")

        if isinstance(self.params, str):
            try:
                self.params = json.loads(self.params)
            except json.JSONDecodeError:
                raise ValueError("Custom TTS配置参数出错,无法将字符串解析为对象")
        elif not isinstance(self.params, dict):
            raise TypeError("Custom TTS配置参数出错, 请参考配置说明")

    def generate_filename(self):
        return os.path.join(self.output_file, f"tts-{datetime.now().date()}@{uuid.uuid4().hex}.{self.format}")

    async def text_to_speak(self, text, output_file):
        request_params = {}
        for k, v in self.params.items():
            if isinstance(v, str) and "{prompt_text}" in v:
                v = v.replace("{prompt_text}", text)
            request_params[k] = v

        try:
            timeout = aiohttp.ClientTimeout(total=self.tts_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if self.method.upper() == "POST":
                    async with session.post(self.url, json=request_params, headers=self.headers) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            if output_file:
                                with open(output_file, "wb") as file:
                                    file.write(content)
                            else:
                                return content
                        else:
                            error_text = await resp.text()
                            error_msg = f"Custom TTS请求失败: {resp.status} - {error_text}"
                            logger.bind(tag=TAG).error(error_msg)
                            raise Exception(error_msg)
                else:
                    async with session.get(self.url, params=request_params, headers=self.headers) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            if output_file:
                                with open(output_file, "wb") as file:
                                    file.write(content)
                            else:
                                return content
                        else:
                            error_text = await resp.text()
                            error_msg = f"Custom TTS请求失败: {resp.status} - {error_text}"
                            logger.bind(tag=TAG).error(error_msg)
                            raise Exception(error_msg)
        except aiohttp.ClientError as e:
            error_msg = f"Custom TTS网络请求失败: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            raise Exception(error_msg)
