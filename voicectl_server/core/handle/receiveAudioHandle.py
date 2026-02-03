from core.handle.sendAudioHandle import send_stt_message
from core.handle.intentHandler import handle_user_intent
from core.utils.output_counter import check_device_output_limit
from core.handle.abortHandle import handleAbortMessage
from core.utils.meeting_summary_db import get_meeting_summary_database, init_default_summaries
from core.utils.util import audio_to_data, remove_punctuation_and_length
import time
import asyncio
import json
from core.handle.sendAudioHandle import SentenceType

TAG = __name__


async def handleAudioMessage(conn, audio):
    # 更新心跳时间（音频消息也视为心跳）
    conn.last_heartbeat_time = time.time()
    
    # 当前片段是否有人说话
    have_voice = conn.vad.is_vad(conn, audio)
    #conn.logger.bind(tag=TAG).info(f"VAD检测结果: {have_voice}")
    # 如果设备刚刚被唤醒，短暂忽略VAD检测
    if have_voice and hasattr(conn, "just_woken_up") and conn.just_woken_up:
        have_voice = False
        # 设置一个短暂延迟后恢复VAD检测
        conn.asr_audio.clear()
        if not hasattr(conn, "vad_resume_task") or conn.vad_resume_task.done():
            conn.vad_resume_task = asyncio.create_task(resume_vad_detection(conn))
        return

    if have_voice:
        if conn.client_is_speaking:
            await handleAbortMessage(conn)
    # 设备长时间空闲检测，用于say goodbye
    await no_voice_close_connect(conn, have_voice)
    # 接收音频
    await conn.asr.receive_audio(conn, audio, have_voice)


async def resume_vad_detection(conn):
    # 等待2秒后恢复VAD检测
    await asyncio.sleep(1)
    conn.just_woken_up = False


async def startToChat(conn, text, is_closing=False):
    # 检查是否是 ASR 错误，如果是则不处理
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
        conn.logger.bind(tag=TAG).info(f"检测到ASR错误，不发送给LLM处理: {text}")
        return

    # 检查对话历史是否超时，如果超时则清空历史
    timeout_minutes = conn.config.get("dialogue_history_timeout", 0)
    if timeout_minutes > 0:
        cleared = conn.dialogue.check_and_clear_history(
            timeout_minutes, conn.logger.bind(tag=TAG)
        )
        if cleared:
            conn.logger.bind(tag=TAG).info(
                f"对话历史已清空，开始新话题（超时设置：{timeout_minutes}分钟）"
            )

    # 检查输入是否是JSON格式（包含说话人信息）
    speaker_name = None
    actual_text = text
    
    try:
        # 尝试解析JSON格式的输入
        if text.strip().startswith('{') and text.strip().endswith('}'):
            data = json.loads(text)
            if 'speaker' in data and 'content' in data:
                speaker_name = data['speaker']
                actual_text = data['content']
                conn.logger.bind(tag=TAG).info(f"解析到说话人信息: {speaker_name}")
                
                # 直接使用JSON格式的文本，不解析
                actual_text = text
    except (json.JSONDecodeError, KeyError):
        # 如果解析失败，继续使用原始文本
        pass
    
    # 检查文本是否为空，如果为空则不处理
    text_len, _ = remove_punctuation_and_length(actual_text)
    if text_len == 0:
        conn.logger.bind(tag=TAG).debug("ASR识别结果为空，跳过处理")
        return
    
    # 保存说话人信息到连接对象
    if speaker_name:
        conn.current_speaker = speaker_name
    else:
        conn.current_speaker = None

    if conn.need_bind:
        await check_bind_device(conn)
        return

    # 如果当日的输出字数大于限定的字数
    if conn.max_output_size > 0:
        if check_device_output_limit(
            conn.headers.get("device-id"), conn.max_output_size
        ):
            await max_out_size(conn)
            return
    # 只在非关闭流程时检查 client_is_speaking，避免打断正在进行的对话
    if conn.client_is_speaking and not is_closing:
        await handleAbortMessage(conn)

    # 检查是否是会议提醒消息
    if "[会议提醒]" in actual_text:
        conn.logger.bind(tag=TAG).info(f"检测到会议提醒消息: {actual_text}")
        
        # 初始化会议总结数据库
        init_default_summaries()
        
        # 提取会议主题
        meeting_theme = ""
        try:
            if "会议主题：" in actual_text:
                theme_start = actual_text.index("会议主题：") + len("会议主题：")
                theme_end = actual_text.index("，会议时间：")
                meeting_theme = actual_text[theme_start:theme_end].strip()
        except Exception as e:
            conn.logger.bind(tag=TAG).warning(f"提取会议主题失败: {e}")
        
        # 使用大模型查询会议总结数据库
        if meeting_theme and hasattr(conn, 'llm') and conn.llm:
            db = get_meeting_summary_database()
            
            # 使用大模型匹配相关会议总结（response_no_stream是同步函数）
            summary = db.find_related_by_llm(meeting_theme, conn.llm)
            
            if summary:
                conn.logger.bind(tag=TAG).info(f"找到相关会议总结: {summary.meeting_theme}")
                
                # 构建包含会议总结信息的提示文本
                summary_info = f"\n\n[历史会议参考]\n会议主题：{summary.meeting_theme}\n会议时间：{summary.meeting_time}\n会议总结：{summary.summary}\n"
                
                # 将会议总结信息添加到对话中，并明确要求播报
                enhanced_text = actual_text + summary_info + "\n\n请务必在播报会议提醒时，简要介绍历史会议的总结内容，帮助用户了解相关背景。"
                conn.logger.bind(tag=TAG).info(f"增强后的会议提醒文本: {enhanced_text}")
                
                # 发送增强后的文本
                await send_stt_message(conn, "会议即将开始:")
                conn.executor.submit(conn.chat, enhanced_text)
                return
            else:
                conn.logger.bind(tag=TAG).info(f"大模型判断无相关会议总结")
        elif meeting_theme:
            conn.logger.bind(tag=TAG).warning("LLM未初始化，无法使用大模型匹配会议总结")
    
    # 会议模式下的ASR结果处理
    if hasattr(conn, 'is_in_meeting') and conn.is_in_meeting:
        conn.logger.bind(tag=TAG).info(f"会议模式下收到ASR结果: {actual_text}")
        
        # 检查是否包含"结束会议"或"退出会议"
        end_meeting_keywords = ["结束会议", "退出会议"]
        should_end_meeting = any(keyword in actual_text for keyword in end_meeting_keywords)
        
        if should_end_meeting:
            conn.logger.bind(tag=TAG).info(f"检测到结束会议指令，送入LLM处理")
            # 送入LLM触发结束会议流程
            await send_stt_message(conn, actual_text)
            conn.executor.submit(conn.chat, actual_text)
        else:
            # 不包含结束会议指令，丢弃不做任何处理
            conn.logger.bind(tag=TAG).info(f"会议模式下未检测到结束会议指令，丢弃ASR结果")
        return
    
    # 首先进行意图分析，使用实际文本内容
    intent_handled = await handle_user_intent(conn, actual_text)

    if intent_handled:
        # 如果意图已被处理，不再进行聊天
        return

    # 意图未被处理，继续常规聊天流程，使用实际文本内容
    
    # 检查是否是声纹注册成功的消息，如果是则不发送文字回显
    voiceprint_success_keywords = [
        "声纹注册成功",
        "声纹已成功注册"
    ]
    is_voiceprint_success = any(keyword in actual_text for keyword in voiceprint_success_keywords)
    
    if is_voiceprint_success:
        conn.logger.bind(tag=TAG).info(f"检测到声纹注册成功消息，不发送文字回显: {actual_text}")
        # 仍然发送给LLM处理
        conn.executor.submit(conn.chat, actual_text)
        return

    # 检查终端模式
    if hasattr(conn, 'terminal_mode') and conn.terminal_mode == "sleep":
        # 休息模式下，不显示用户消息，但仍然发送给LLM让LLM判断是否唤醒
        conn.logger.bind(tag=TAG).info(f"休息模式下收到用户消息，发送给LLM判断是否唤醒: {actual_text}")
        conn.executor.submit(conn.chat, actual_text)
    else:
        # 工作模式下，正常处理
        await send_stt_message(conn, actual_text)
        conn.executor.submit(conn.chat, actual_text)


async def no_voice_close_connect(conn, have_voice):
    if have_voice:
        conn.last_activity_time = time.time() * 1000
        return
    # 只有在已经初始化过时间戳的情况下才进行超时检查
    if conn.last_activity_time > 0.0:
        no_voice_time = time.time() * 1000 - conn.last_activity_time
        close_connection_no_voice_time = int(
            conn.config.get("close_connection_no_voice_time", 120)
        )
        if (
            not conn.close_after_chat
            and no_voice_time > 1000 * close_connection_no_voice_time
        ):
            conn.close_after_chat = True
            conn.client_abort = False
            end_prompt = conn.config.get("end_prompt", {})
            if end_prompt and end_prompt.get("enable", True) is False:
                conn.logger.bind(tag=TAG).info("结束对话，无需发送结束提示语")
                await conn.close()
                return
            prompt = end_prompt.get("prompt")
            if not prompt:
                prompt = "请你以```时间过得真快```未来头，用富有感情、依依不舍的话来结束这场对话吧。！"
            # 使用 create_task 非阻塞启动 startToChat，避免阻塞音频处理线程
            # 添加标志位防止重复调用
            if not hasattr(conn, 'closing_task') or conn.closing_task.done():
                conn.closing_task = asyncio.create_task(startToChat(conn, prompt, is_closing=True))


async def max_out_size(conn):
    text = "不好意思，我现在有点事情要忙，明天这个时候我们再聊，约好了哦！明天不见不散，拜拜！"
    await send_stt_message(conn, text)
    file_path = "config/assets/max_output_size.wav"
    opus_packets, _ = audio_to_data(file_path)
    conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
    conn.close_after_chat = True


async def check_bind_device(conn):
    if conn.bind_code:
        # 确保bind_code是6位数字
        if len(conn.bind_code) != 6:
            conn.logger.bind(tag=TAG).error(f"无效的绑定码格式: {conn.bind_code}")
            text = "绑定码格式错误，请检查配置。"
            await send_stt_message(conn, text)
            return

        text = f"请登录控制面板，输入{conn.bind_code}，绑定设备。"
        await send_stt_message(conn, text)

        # 播放提示音
        music_path = "config/assets/bind_code.wav"
        opus_packets, _ = audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.FIRST, opus_packets, text))

        # 逐个播放数字
        for i in range(6):  # 确保只播放6位数字
            try:
                digit = conn.bind_code[i]
                num_path = f"config/assets/bind_code/{digit}.wav"
                num_packets, _ = audio_to_data(num_path)
                conn.tts.tts_audio_queue.put((SentenceType.MIDDLE, num_packets, None))
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"播放数字音频失败: {e}")
                continue
        conn.tts.tts_audio_queue.put((SentenceType.LAST, [], None))
    else:
        text = f"没有找到该设备的版本信息，请正确配置 OTA地址，然后重新编译固件。"
        await send_stt_message(conn, text)
        music_path = "config/assets/bind_not_found.wav"
        opus_packets, _ = audio_to_data(music_path)
        conn.tts.tts_audio_queue.put((SentenceType.LAST, opus_packets, text))
