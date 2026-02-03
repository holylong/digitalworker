import json
import asyncio
import time
from core.providers.tts.dto.dto import SentenceType
from core.utils.util import get_string_no_punctuation_or_emoji, analyze_emotion
from loguru import logger

TAG = __name__

emoji_map = {
    "neutral": "😶",
    "happy": "🙂",
    "laughing": "😆",
    "funny": "😂",
    "sad": "😔",
    "angry": "😠",
    "crying": "😭",
    "loving": "😍",
    "embarrassed": "😳",
    "surprised": "😲",
    "shocked": "😱",
    "thinking": "🤔",
    "winking": "😉",
    "cool": "😎",
    "relaxed": "😌",
    "delicious": "🤤",
    "kissy": "😘",
    "confident": "😏",
    "sleepy": "😴",
    "silly": "😜",
    "confused": "🙄",
}


async def sendAudioMessage(conn, sentenceType, audios, text):
    # 发送句子开始消息
    conn.logger.bind(tag=TAG).info(f"发送音频消息: {sentenceType}, {text}")
    
    # 检查是否是ASR错误，如果是则不发送TTS和文字
    if text is not None:
        asr_error_indicators = [
            "检测到ASR识别可能出错",
            "内容不完整且无明确意图",
            "保持静默等待用户继续输入",
            "无法理解您的输入",
            "请重新说一遍"
        ]
        
        # 检查文本是否包含ASR错误指示
        is_asr_error = any(indicator in text for indicator in asr_error_indicators)
        
        # 检查文本是否只包含无意义的字符（如"그"、"也"等单字）
        if len(text.strip()) <= 2 and not is_asr_error:
            is_asr_error = True
        
        if is_asr_error:
            conn.logger.bind(tag=TAG).info(f"检测到ASR错误，不发送TTS和文字: {text}")
            # 清空TTS队列，不播放任何音频
            if sentenceType == SentenceType.LAST:
                conn.client_is_speaking = False
                if conn.close_after_chat:
                    await conn.close()
            return
    
    if text is not None:
        # 检查是否启用表情发送
        enable_emoji = conn.config.get("enable_emoji", True)
        if enable_emoji:
            emotion = analyze_emotion(text)
            emoji = emoji_map.get(emotion, "🙂")  # 默认使用笑脸
            await conn.websocket.send(
                json.dumps(
                    {
                        "type": "llm",
                        "text": emoji,
                        "emotion": emotion,
                        "session_id": conn.session_id,
                    }
                )
            )
    pre_buffer = False
    if conn.tts.tts_audio_first_sentence and text is not None:
        conn.logger.bind(tag=TAG).info(f"发送第一段语音: {text}")
        conn.tts.tts_audio_first_sentence = False
        pre_buffer = True

    await send_tts_message(conn, "sentence_start", text)

    await sendAudio(conn, audios, pre_buffer)

    await send_tts_message(conn, "sentence_end", text)

    # 发送结束消息（如果是最后一个文本）
    if conn.llm_finish_task and sentenceType == SentenceType.LAST:
        await send_tts_message(conn, "stop", None)
        conn.client_is_speaking = False
        if conn.close_after_chat:
            await conn.close()


# 播放音频
async def sendAudio(conn, audios, pre_buffer=True):
    if audios is None or len(audios) == 0:
        return
    
    # 流控参数优化
    frame_duration = 60  # 帧时长（毫秒），匹配 Opus 编码
    start_time = time.perf_counter()
    play_position = 0
    
    # 对于长音频（如音乐文件），禁用预缓冲
    # 阈值：超过 100 帧认为是长音频（约 6 秒）
    is_long_audio = len(audios) > 100
    if is_long_audio:
        pre_buffer = False
        conn.logger.bind(tag=TAG).info(f"检测到长音频({len(audios)}帧)，禁用预缓冲")

    # 仅当第一句话时执行预缓冲
    if pre_buffer:
        pre_buffer_frames = min(3, len(audios))
        for i in range(pre_buffer_frames):
            await conn.websocket.send(audios[i])
        remaining_audios = audios[pre_buffer_frames:]
    else:
        remaining_audios = audios

    # 播放剩余音频帧
    total_frames = len(remaining_audios)
    sent_frames = 0
    
    for opus_packet in remaining_audios:
        if conn.client_abort:
            conn.logger.bind(tag=TAG).info(f"客户端中断，停止发送音频（已发送{sent_frames}/{total_frames}帧）")
            break

        # 重置没有声音的状态
        conn.last_activity_time = time.time() * 1000

        # 计算预期发送时间
        expected_time = start_time + (play_position / 1000)
        current_time = time.perf_counter()
        delay = expected_time - current_time
        
        # 优化流控逻辑：
        # 1. 限制最大延迟时间，避免长时间阻塞
        # 2. 对于长音频，减少延迟时间，加快发送速度
        max_delay = 0.1 if is_long_audio else 0.5  # 长音频最大延迟100ms，短音频500ms
        if delay > max_delay:
            delay = max_delay
        if delay > 0:
            await asyncio.sleep(delay)

        try:
            await conn.websocket.send(opus_packet)
            sent_frames += 1
            
            # 对于长音频，每发送 100 帧记录一次进度
            if is_long_audio and sent_frames % 100 == 0:
                conn.logger.bind(tag=TAG).info(f"音频发送进度: {sent_frames}/{total_frames}帧 ({sent_frames*100//total_frames}%)")
        except Exception as e:
            conn.logger.bind(tag=TAG).error(f"发送音频帧失败（第{sent_frames}帧）: {e}")
            break

        play_position += frame_duration
    
    if sent_frames == total_frames:
        conn.logger.bind(tag=TAG).info(f"音频发送完成: {sent_frames}帧，耗时{time.perf_counter()-start_time:.2f}秒")


async def send_tts_message(conn, state, text=None):
    """发送 TTS 状态消息"""
    message = {"type": "tts", "state": state, "session_id": conn.session_id}
    if text is not None:
        message["text"] = text

    # TTS播放结束
    if state == "stop":
        # 播放提示音
        tts_notify = conn.config.get("enable_stop_tts_notify", False)
        if tts_notify:
            stop_tts_notify_voice = conn.config.get(
                "stop_tts_notify_voice", "config/assets/tts_notify.mp3"
            )
            audios, _ = conn.tts.audio_to_opus_data(stop_tts_notify_voice)
            await sendAudio(conn, audios)
        # 清除服务端讲话状态
        conn.clearSpeakStatus()

    # 发送消息到客户端
    await conn.websocket.send(json.dumps(message))


async def send_stt_message(conn, text):
    end_prompt_str = conn.config.get("end_prompt", {}).get("prompt")
    if end_prompt_str and end_prompt_str == text:
        await send_tts_message(conn, "start")
        return

    """发送 STT 状态消息"""
    
    # 检查是否是 ASR 错误，如果是则不发送消息
    asr_error_indicators = [
        "检测到ASR识别可能出错",
        "内容不完整且无明确意图",
        "保持静默等待用户继续输入",
        "无法理解您的输入",
        "请重新说一遍"
    ]
    
    # 检查文本是否包含 ASR 错误指示
    is_asr_error = any(indicator in text for indicator in asr_error_indicators)
    
    # 检查文本是否只包含无意义的字符（如"그"、"也"等单字）
    if len(text.strip()) <= 2 and not is_asr_error:
        is_asr_error = True
    
    if is_asr_error:
        conn.logger.bind(tag=TAG).info(f"检测到ASR错误，不发送STT消息: {text}")
        return
    
    # 解析JSON格式，提取实际的用户说话内容
    display_text = text
    try:
        # 尝试解析JSON格式
        if text.strip().startswith('{') and text.strip().endswith('}'):
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and "content" in parsed_data:
                # 如果是包含说话人信息的JSON格式，只显示content部分
                display_text = parsed_data["content"]
    except (json.JSONDecodeError, TypeError):
        # 如果不是JSON格式，直接使用原始文本
        display_text = text
    
    stt_text = get_string_no_punctuation_or_emoji(display_text)
    await conn.websocket.send(
        json.dumps({"type": "stt", "text": stt_text, "session_id": conn.session_id})
    )
    conn.client_is_speaking = True
    await send_tts_message(conn, "start")
