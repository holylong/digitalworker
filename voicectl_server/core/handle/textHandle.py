import json
from core.handle.abortHandle import handleAbortMessage
from core.handle.helloHandle import handleHelloMessage
from core.providers.tools.device_mcp import handle_mcp_message
from core.utils.util import remove_punctuation_and_length, filter_sensitive_info
from core.handle.receiveAudioHandle import startToChat, handleAudioMessage
from core.handle.sendAudioHandle import send_stt_message, send_tts_message
from core.providers.tools.device_iot import handleIotDescriptors, handleIotStatus
from core.handle.reportHandle import enqueue_asr_report
from core.utils.dialogue import Message
from core.providers.tts.dto.dto import SentenceType
import asyncio
import time

TAG = __name__


async def send_terminal_mode_message(conn, mode: str):
    """发送终端模式消息给客户端"""
    try:
        message = {
            "type": "terminal_mode",
            "mode": mode
        }
        await conn.websocket.send(json.dumps(message))
        conn.logger.bind(tag=TAG).info(f"已发送终端模式消息给客户端: {mode}")
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"发送终端模式消息失败: {e}")


async def handleHeartbeatMessage(conn, msg_json):
    """处理心跳消息"""
    try:
        conn.logger.bind(tag=TAG).debug("收到心跳消息")

        # 更新活动时间
        conn.last_activity_time = time.time() * 1000
        conn.last_heartbeat_time = time.time()

        # 回复心跳响应
        response = {
            "type": "heartbeat",
            "timestamp": int(time.time() * 1000),
            "session_id": conn.session_id
        }

        await conn.websocket.send(json.dumps(response))
        conn.logger.bind(tag=TAG).debug("发送心跳响应")

    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"处理心跳消息失败: {e}")

async def handleTextMessage(conn, message):
    """处理文本消息"""
    try:
        # 更新心跳时间（任何消息都视为心跳）
        conn.last_heartbeat_time = time.time()
        
        msg_json = json.loads(message)
        if isinstance(msg_json, int):
            conn.logger.bind(tag=TAG).info(f"收到文本消息：{message}")
            await conn.websocket.send(message)
            return

        if msg_json["type"] == "hello":
            conn.logger.bind(tag=TAG).info(f"收到hello消息：{message}")
            await handleHelloMessage(conn, msg_json)
        elif msg_json["type"] == "heartbeat":
            conn.logger.bind(tag=TAG).info(f"收到heartbeat消息：{message}")
            await handleHeartbeatMessage(conn, msg_json)
        elif msg_json["type"] == "listen_mode_update":
            conn.logger.bind(tag=TAG).info(f"收到工作模式更新消息：{message}")
            # 更新客户端工作模式
            client_listen_mode = msg_json.get("client_listen_mode", "auto")
            conn.client_listen_mode = client_listen_mode
            conn.logger.bind(tag=TAG).info(f"工作模式已更新: {client_listen_mode}")
        elif msg_json["type"] == "terminal_mode_sync":
            conn.logger.bind(tag=TAG).info(f"收到终端模式同步消息：{message}")
            # 客户端同步实际设置的模式
            mode = msg_json.get("mode", "work")
            conn.terminal_mode = mode
            conn.logger.bind(tag=TAG).info(f"终端模式已同步: {mode}")
        elif msg_json["type"] == "abort":
            conn.logger.bind(tag=TAG).info(f"收到abort消息：{message}")
            await handleAbortMessage(conn)
        elif msg_json["type"] == "listen":
            conn.logger.bind(tag=TAG).info(f"收到listen消息：{message}")
            if "mode" in msg_json:
                conn.client_listen_mode = msg_json["mode"]
                conn.logger.bind(tag=TAG).debug(
                    f"客户端拾音模式：{conn.client_listen_mode}"
                )
            
            # 处理会议模式
            if msg_json.get("mode") == "meeting":
                if msg_json["state"] == "start":
                    conn.is_in_meeting = True
                    conn.client_have_voice = True
                    conn.client_voice_stop = False
                    conn.logger.bind(tag=TAG).info("进入会议模式，开始接收音频")
                elif msg_json["state"] == "end":
                    conn.is_in_meeting = False
                    conn.client_have_voice = False
                    conn.client_voice_stop = True
                    conn.logger.bind(tag=TAG).info("退出会议模式")
                return
            
            if msg_json["state"] == "start":
                conn.client_have_voice = True
                conn.client_voice_stop = False
                
                # 标记为正在监听
                conn.is_listening = True
                
            elif msg_json["state"] == "stop":
                conn.client_have_voice = True
                conn.client_voice_stop = False
                
                # 标记为未在监听
                conn.is_listening = False
                
                if len(conn.asr_audio) > 0:
                    # 直接送入ASR处理
                    conn.logger.bind(tag=TAG).info(
                        f"手动模式监听结束，送入ASR处理"
                    )
                    asr_audio_task = conn.asr_audio.copy()
                    conn.asr_audio.clear()
                    conn.reset_vad_states()
                    conn.client_have_voice = False
                    conn.client_voice_stop = False
                    await conn.asr.handle_voice_stop(conn, asr_audio_task)
            elif msg_json["state"] == "detect":
                conn.client_have_voice = False
                conn.asr_audio.clear()
                if "text" in msg_json:
                    original_text = msg_json["text"]  # 保留原始文本
                    filtered_len, filtered_text = remove_punctuation_and_length(
                        original_text
                    )

                    # 识别是否是唤醒词
                    is_wakeup_words = filtered_text in conn.config.get("wakeup_words")
                    # 是否开启唤醒词回复
                    enable_greeting = conn.config.get("enable_greeting", True)

                    if is_wakeup_words and not enable_greeting:
                        # 如果是唤醒词，且关闭了唤醒词回复，就不用回答
                        await send_stt_message(conn, original_text)
                        await send_tts_message(conn, "stop", None)
                        conn.client_is_speaking = False
                    elif is_wakeup_words:
                        conn.just_woken_up = True
                        # 上报纯文字数据（复用ASR上报功能，但不提供音频数据）
                        enqueue_asr_report(conn, "嘿，你好呀", [])
                        await startToChat(conn, "嘿，你好呀")
                    else:
                        # 上报纯文字数据（复用ASR上报功能，但不提供音频数据）
                        enqueue_asr_report(conn, original_text, [])
                        # 否则需要LLM对文字内容进行答复
                        await startToChat(conn, original_text)
        elif msg_json["type"] == "iot":
            conn.logger.bind(tag=TAG).info(f"收到iot消息：{message}")
            if "descriptors" in msg_json:
                asyncio.create_task(handleIotDescriptors(conn, msg_json["descriptors"]))
            if "states" in msg_json:
                asyncio.create_task(handleIotStatus(conn, msg_json["states"]))
        elif msg_json["type"] == "mcp":
            conn.logger.bind(tag=TAG).info(f"收到mcp消息：{message[:100]}")
            if "payload" in msg_json and conn.mcp_client is not None:
                asyncio.create_task(
                    handle_mcp_message(conn, conn.mcp_client, msg_json["payload"])
                )
            elif conn.mcp_client is None:
                conn.logger.bind(tag=TAG).warning("MCP客户端未初始化，忽略MCP消息")
        elif msg_json["type"] == "active_chat":
            conn.logger.bind(tag=TAG).info(f"收到active_chat消息：{message}")
            if "topic" in msg_json:
                topic = msg_json["topic"]
                user_name = msg_json.get("user_name", "")
                conn.logger.bind(tag=TAG).info(f"主动聊天话题: {topic}, 用户: {user_name}")
                # 将话题作为assistant消息添加到对话历史（LLM自己说的话）
                conn.dialogue.put(Message(role="assistant", content=topic))
                # 直接调用TTS播放话题内容
                await handle_active_chat(conn, topic)
        elif msg_json["type"] == "meeting_reminder":
            conn.logger.bind(tag=TAG).info(f"收到会议提醒消息：{message}")
            asyncio.create_task(handle_meeting_reminder(conn, msg_json))
        elif msg_json["type"] == "server":
            # 记录日志时过滤敏感信息
            conn.logger.bind(tag=TAG).info(
                f"收到服务器消息：{filter_sensitive_info(msg_json)}"
            )
            # 如果配置是从API读取的，则需要验证secret
            if not conn.read_config_from_api:
                return
            # 获取post请求的secret
            post_secret = msg_json.get("content", {}).get("secret", "")
            secret = conn.config["manager-api"].get("secret", "")
            # 如果secret不匹配，则返回
            if post_secret != secret:
                await conn.websocket.send(
                    json.dumps(
                        {
                            "type": "server",
                            "status": "error",
                            "message": "服务器密钥验证失败",
                        }
                    )
                )
                return
            # 动态更新配置
            if msg_json["action"] == "update_config":
                try:
                    # 更新WebSocketServer的配置
                    if not conn.server:
                        await conn.websocket.send(
                            json.dumps(
                                {
                                    "type": "server",
                                    "status": "error",
                                    "message": "无法获取服务器实例",
                                    "content": {"action": "update_config"},
                                }
                            )
                        )
                        return

                    if not await conn.server.update_config():
                        await conn.websocket.send(
                            json.dumps(
                                {
                                    "type": "server",
                                    "status": "error",
                                    "message": "更新服务器配置失败",
                                    "content": {"action": "update_config"},
                                }
                            )
                        )
                        return

                    # 发送成功响应
                    await conn.websocket.send(
                        json.dumps(
                            {
                                "type": "server",
                                "status": "success",
                                "message": "配置更新成功",
                                "content": {"action": "update_config"},
                            }
                        )
                    )
                except Exception as e:
                    conn.logger.bind(tag=TAG).error(f"更新配置失败: {str(e)}")
                    await conn.websocket.send(
                        json.dumps(
                            {
                                "type": "server",
                                "status": "error",
                                "message": f"更新配置失败: {str(e)}",
                                "content": {"action": "update_config"},
                            }
                        )
                    )
            # 重启服务器
            elif msg_json["action"] == "restart":
                await conn.handle_restart(msg_json)
        else:
            conn.logger.bind(tag=TAG).error(f"收到未知类型消息：{message}")
    except json.JSONDecodeError:
        await conn.websocket.send(message)

async def handle_active_chat(conn, topic):
    """处理主动聊天，直接调用TTS播放话题内容"""
    try:
        conn.logger.bind(tag=TAG).info(f"开始播放主动聊天内容: {topic}")
        
        # 如果客户端正在说话，先打断
        if conn.client_is_speaking:
            await handleAbortMessage(conn)
        
        # 更新活动时间
        conn.last_activity_time = time.time() * 1000
        
        # 发送文字回显到终端软件（使用 llm 类型，表示是会会助手说的话）
        await conn.websocket.send(
            json.dumps({
                "type": "llm",
                "text": topic,
                "session_id": conn.session_id
            })
        )
        
        # 将文本转换为音频数据（直接调用异步方法，避免 asyncio.run() 错误）
        audio_bytes = await conn.tts.text_to_speak(topic, None)
        
        if audio_bytes is None:
            conn.logger.bind(tag=TAG).error(f"主动聊天TTS生成失败: {topic}")
            return
        
        # 转换为音频数据
        from core.utils.util import audio_bytes_to_data
        opus_packets, _ = audio_bytes_to_data(audio_bytes, file_type=conn.tts.audio_file_type, is_opus=True)
        
        if opus_packets is None or len(opus_packets) == 0:
            conn.logger.bind(tag=TAG).error(f"主动聊天音频数据转换失败: {topic}")
            return
        
        # 发送TTS开始消息
        await send_tts_message(conn, "start")
        
        # 发送音频数据
        await sendAudio(conn, opus_packets, pre_buffer=True)
        
        # 发送TTS结束消息
        await send_tts_message(conn, "stop", None)
        
        # 重置client_abort标志，允许后续用户语音被处理
        conn.client_abort = False
        
        conn.logger.bind(tag=TAG).info(f"主动聊天播放完成: {topic}")
        
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"处理主动聊天失败: {e}")

async def handle_meeting_reminder(conn, msg_json):
    """处理会议提醒，查询历史会议总结并主动播报"""
    try:
        meeting_id = msg_json.get("meeting_id", "")
        meeting_type = msg_json.get("meeting_type", "")
        meeting_number = msg_json.get("meeting_number", "")
        meeting_time = msg_json.get("meeting_time", "")
        meeting_name = msg_json.get("meeting_name", "")
        
        conn.logger.bind(tag=TAG).info(f"处理会议提醒: {meeting_name} ({meeting_number})")
        
        # 构建会议提醒文本（TTS播报用，包含会议ID）
        reminder_text = f"[会议提醒] 您有一个会议即将开始，会议主题：{meeting_name}，会议时间：{meeting_time}。"
        
        # 初始化会议总结数据库
        from core.utils.meeting_summary_db import get_meeting_summary_database, init_default_summaries
        init_default_summaries()
        
        # 使用大模型查询会议总结数据库（使用会议主题匹配）
        summary_info = ""
        if meeting_name and hasattr(conn, 'llm') and conn.llm:
            db = get_meeting_summary_database()
            
            # 使用大模型匹配相关会议总结
            summary = db.find_related_by_llm(meeting_name, conn.llm)
            
            if summary:
                conn.logger.bind(tag=TAG).info(f"找到相关会议总结: {summary.meeting_theme}")
                
                # 构建包含会议总结信息的提示文本
                summary_info = f"\n\n[历史会议参考]\n会议主题：{summary.meeting_theme}\n会议时间：{summary.meeting_time}\n会议总结：{summary.summary}\n"
        
        # 构建完整的播报文本
        broadcast_text = reminder_text + summary_info
        
        conn.logger.bind(tag=TAG).info(f"会议提醒播报文本: {broadcast_text}")
        
        # 如果客户端正在说话，先打断
        if conn.client_is_speaking:
            await handleAbortMessage(conn)
        
        # 更新活动时间
        conn.last_activity_time = time.time() * 1000
        
        # 发送文字回显到终端软件（使用 llm 类型，表示是会会助手说的话）
        await conn.websocket.send(
            json.dumps({
                "type": "llm",
                "text": broadcast_text,
                "session_id": conn.session_id
            })
        )
        
        # 将文本转换为音频数据（直接调用异步方法，避免 asyncio.run() 错误）
        audio_bytes = await conn.tts.text_to_speak(broadcast_text, None)
        
        if audio_bytes is None:
            conn.logger.bind(tag=TAG).error(f"会议提醒TTS生成失败: {broadcast_text}")
            return
        
        # 转换为音频数据
        from core.utils.util import audio_bytes_to_data
        opus_packets, _ = audio_bytes_to_data(audio_bytes, file_type=conn.tts.audio_file_type, is_opus=True)
        
        if opus_packets is None or len(opus_packets) == 0:
            conn.logger.bind(tag=TAG).error(f"会议提醒音频数据转换失败: {broadcast_text}")
            return
        
        # 发送TTS开始消息
        await send_tts_message(conn, "start")
        
        # 发送音频数据
        await sendAudio(conn, opus_packets, pre_buffer=True)
        
        # 发送TTS结束消息
        await send_tts_message(conn, "stop", None)
        
        # 重置client_abort标志，允许后续用户语音被处理
        conn.client_abort = False
        
        conn.logger.bind(tag=TAG).info(f"会议提醒播放完成: {meeting_name}")
        
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"处理会议提醒失败: {e}")

async def sendAudio(conn, audios, pre_buffer=True):
    """发送音频数据"""
    if audios is None or len(audios) == 0:
        return
    
    frame_duration = 60  # 帧时长（毫秒），匹配 Opus 编码
    start_time = time.perf_counter()
    play_position = 0
    
    # 仅当第一句话时执行预缓冲
    if pre_buffer:
        pre_buffer_frames = min(3, len(audios))
        for i in range(pre_buffer_frames):
            await conn.websocket.send(audios[i])
        remaining_audios = audios[pre_buffer_frames:]
    else:
        remaining_audios = audios
    
    # 播放剩余音频帧
    for opus_packet in remaining_audios:
        if conn.client_abort:
            break
        
        # 重置没有声音的状态
        conn.last_activity_time = time.time() * 1000
        
        # 计算预期发送时间
        expected_time = start_time + (play_position / 1000)
        current_time = time.perf_counter()
        delay = expected_time - current_time
        if delay > 0:
            await asyncio.sleep(delay)
        
        await conn.websocket.send(opus_packet)
        
        play_position += frame_duration

