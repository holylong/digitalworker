import time
import json
import random
import asyncio
from core.utils.dialogue import Message
from core.utils.util import audio_to_data
from core.handle.sendAudioHandle import sendAudioMessage, send_stt_message
from core.utils.util import remove_punctuation_and_length, opus_datas_to_wav_bytes
from core.providers.tts.dto.dto import ContentType, SentenceType
from core.providers.tools.device_mcp import (
    MCPClient,
    send_mcp_initialize_message,
    send_mcp_tools_list_request,
)
from core.utils.wakeup_word import WakeupWordsConfig

TAG = __name__

WAKEUP_CONFIG = {
    "refresh_time": 5,
    "words": ["你好", "你好啊", "嘿，你好", "嗨"],
}

# 创建全局的唤醒词配置管理器
wakeup_words_config = WakeupWordsConfig()

# 用于防止并发调用wakeupWordsResponse的锁
_wakeup_response_lock = asyncio.Lock()

async def handleHelloMessage(conn, msg_json):
    """处理hello消息"""
    try:
        conn.logger.bind(tag=TAG).info(f"收到客户端hello消息: {msg_json}")
        
        # 获取设备配置信息
        device_id = msg_json.get("device_id", "")
        device_name = msg_json.get("device_name", "")
        token = msg_json.get("token", "")
        
        conn.device_id = device_id
        
        # 获取客户端工作模式
        client_listen_mode = msg_json.get("client_listen_mode", "auto")
        conn.client_listen_mode = client_listen_mode
        conn.logger.bind(tag=TAG).info(f"客户端工作模式: {client_listen_mode}")
        
        # 获取音频参数
        audio_params = msg_json.get("audio_params")
        if audio_params:
            format = audio_params.get("format")
            conn.logger.bind(tag=TAG).info(f"客户端音频格式: {format}")
            conn.audio_format = format
            if hasattr(conn, 'welcome_msg') and conn.welcome_msg:
                conn.welcome_msg["audio_params"] = audio_params
        
        # 获取特性配置
        features = msg_json.get("features")
        if features:
            conn.logger.bind(tag=TAG).info(f"客户端特性: {features}")
            conn.features = features
            if features.get("mcp"):
                conn.logger.bind(tag=TAG).info("客户端支持MCP")
                conn.mcp_client = MCPClient()
                # 发送初始化
                asyncio.create_task(send_mcp_initialize_message(conn))
                # 发送mcp消息，获取tools列表
                asyncio.create_task(send_mcp_tools_list_request(conn))
        
        # 构建hello响应
        response = {
            "type": "hello",
            "session_id": conn.session_id,
            "status": "success",
            "keepalive": True,
            "keepalive_interval": 30,
            "timestamp": int(time.time() * 1000)
        }
        
        # 如果有欢迎消息，添加到响应中
        if hasattr(conn, 'welcome_msg') and conn.welcome_msg:
            if isinstance(conn.welcome_msg, dict):
                response.update(conn.welcome_msg)
            else:
                response["welcome"] = conn.welcome_msg
        
        # 添加设备信息到响应
        if device_id:
            response["device_id"] = device_id
        if device_name:
            response["device_name"] = device_name
            
        conn.logger.bind(tag=TAG).info(f"发送hello响应: {response}")
        await conn.websocket.send(json.dumps(response))
        
        # 更新活动时间
        conn.last_activity_time = time.time() * 1000
        conn.last_heartbeat_time = time.time()
        
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"处理hello消息失败: {e}")
        # 发送错误响应
        try:
            await conn.websocket.send(json.dumps({
                "type": "error",
                "code": 5000,
                "message": "处理hello消息失败",
                "details": str(e)
            }))
        except Exception as send_error:
            conn.logger.bind(tag=TAG).error(f"发送错误响应失败: {send_error}")

async def checkWakeupWords(conn, text):
    enable_wakeup_words_response_cache = conn.config[
        "enable_wakeup_words_response_cache"
    ]

    if not enable_wakeup_words_response_cache or not conn.tts:
        return False

    _, filtered_text = remove_punctuation_and_length(text)
    if filtered_text not in conn.config.get("wakeup_words"):
        return False

    conn.just_woken_up = True
    await send_stt_message(conn, text)

    # 获取当前音色
    voice = getattr(conn.tts, "voice", "default")
    if not voice:
        voice = "default"

    # 获取唤醒词回复配置
    response = wakeup_words_config.get_wakeup_response(voice)
    if not response or not response.get("file_path"):
        response = {
            "voice": "default",
            "file_path": "config/assets/wakeup_words.wav",
            "time": 0,
            "text": "你好，我是会会，一位专业且富有亲和力的会议秘书，有什么日程安排都可以跟我说，我会给你安排好的",
        }



    # 播放唤醒词回复
    conn.client_abort = False
    opus_packets, _ = audio_to_data(response.get("file_path"))

    conn.logger.bind(tag=TAG).info(f"播放唤醒词回复: {response.get('text')}")
    await sendAudioMessage(conn, SentenceType.FIRST, opus_packets, response.get("text"))
    await sendAudioMessage(conn, SentenceType.LAST, [], None)

    # 补充对话
    conn.dialogue.put(Message(role="assistant", content=response.get("text")))

    # 检查是否需要更新唤醒词回复
    if time.time() - response.get("time", 0) > WAKEUP_CONFIG["refresh_time"]:
        if not _wakeup_response_lock.locked():
            asyncio.create_task(wakeupWordsResponse(conn))
    return True


async def wakeupWordsResponse(conn):
    if not conn.tts or not conn.llm or not conn.llm.response_no_stream:
        return

    try:
        # 尝试获取锁，如果获取不到就返回
        if not await _wakeup_response_lock.acquire():
            return

        # 生成唤醒词回复
        wakeup_word = random.choice(WAKEUP_CONFIG["words"])
        question = (
            "此刻用户正在和你说```"
            + wakeup_word
            + "```。\n请你根据以上用户的内容进行20-30字回复。要符合系统设置的角色情感和态度，不要像机器人一样说话。\n"
            + "请勿对这条内容本身进行任何解释和回应，请勿返回表情符号，仅返回对用户的内容的回复。"
        )

        result = conn.llm.response_no_stream(conn.config["prompt"], question)
        if not result or len(result) == 0:
            return

        # 生成TTS音频
        tts_result = await asyncio.to_thread(conn.tts.to_tts, result)
        if not tts_result:
            return

        # 获取当前音色
        voice = getattr(conn.tts, "voice", "default")

        wav_bytes = opus_datas_to_wav_bytes(tts_result, sample_rate=16000)
        file_path = wakeup_words_config.generate_file_path(voice)
        with open(file_path, "wb") as f:
            f.write(wav_bytes)
        # 更新配置
        wakeup_words_config.update_wakeup_response(voice, file_path, result)
    finally:
        # 确保在任何情况下都释放锁
        if _wakeup_response_lock.locked():
            _wakeup_response_lock.release()
