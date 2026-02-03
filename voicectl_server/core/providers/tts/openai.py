import aiohttp
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.api_key = config.get("api_key")
        self.api_url = config.get("api_url", "https://api.openai.com/v1/audio/speech")
        self.model = config.get("model", "tts-1")
        if config.get("private_voice"):
            self.voice = config.get("private_voice")
        else:
            self.voice = config.get("voice", "alloy")
        self.response_format = config.get("format", "wav")
        self.audio_file_type = config.get("format", "wav")

        speed = config.get("speed", "1.0")
        self.speed = float(speed) if speed else 1.0

        self.output_file = config.get("output_dir", "tmp/")
        model_key_msg = check_model_key("TTS", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

    async def text_to_speak(self, text, output_file):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "input": text,
            "voice": self.voice,
            "response_format": "wav",
            "speed": self.speed,
        }
        try:
            timeout = aiohttp.ClientTimeout(total=self.tts_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.api_url, json=data, headers=headers) as response:
                    if response.status == 200:
                        content = await response.read()
                        if output_file:
                            with open(output_file, "wb") as audio_file:
                                audio_file.write(content)
                        else:
                            return content
                    else:
                        error_text = await response.text()
                        raise Exception(
                            f"OpenAI TTS请求失败: {response.status} - {error_text}"
                        )
        except aiohttp.ClientError as e:
            error_msg = f"OpenAI TTS网络请求失败: {str(e)}"
            logger.bind(tag=TAG).error(error_msg)
            raise Exception(error_msg)
