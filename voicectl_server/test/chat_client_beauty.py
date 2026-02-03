import sys
import json
import asyncio
import threading
import wave
import numpy as np
import platform
import pyaudio
import websockets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QTextEdit, QGroupBox, QTabWidget, QComboBox,
                            QFrame, QSizePolicy, QProgressBar, QScrollArea, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QLinearGradient, QBrush, QTextCharFormat, QTextCursor
from opuslib import Encoder, Decoder

# 音频参数
RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 960  # 60ms @ 16kHz

class FadeLabel(QLabel):
    """带有淡入淡出效果的标签"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def showEvent(self, event):
        # 淡入效果
        self.animation.setStartValue(QRect(self.x() - 20, self.y(), self.width(), self.height()))
        self.animation.setEndValue(QRect(self.x(), self.y(), self.width(), self.height()))
        self.animation.start()
        super().showEvent(event)

class AudioRecorder(QThread):
    """音频录制线程"""
    audio_data_signal = pyqtSignal(bytes)
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.p = pyaudio.PyAudio()
        self.stream = None
    
    def run(self):
        self.recording = True
        try:
            self.stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            while self.recording:
                data = self.stream.read(CHUNK)
                self.audio_data_signal.emit(data)
                
        except Exception as e:
            print(f"录音错误: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
    
    def stop(self):
        self.recording = False
        self.wait(1000)

class AudioPlayer(QThread):
    """音频播放线程"""
    def __init__(self):
        super().__init__()
        self.playing = False
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.opus_decoder = Decoder(RATE, CHANNELS)
        self.audio_queue = []
    
    def run(self):
        self.playing = True
        try:
            self.stream = self.p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK
            )
            
            while self.playing or self.audio_queue:
                if self.audio_queue:
                    opus_data = self.audio_queue.pop(0)
                    # 解码Opus音频
                    pcm_data = self.opus_decoder.decode(opus_data, CHUNK)
                    self.stream.write(pcm_data)
                else:
                    self.msleep(10)
                
        except Exception as e:
            print(f"播放错误: {e}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
    
    def add_audio(self, data):
        self.audio_queue.append(data)
    
    def stop(self):
        self.playing = False
        self.wait(1000)

class WebSocketClient(QThread):
    """WebSocket客户端线程"""
    message_received = pyqtSignal(dict)
    audio_received = pyqtSignal(bytes)
    status_changed = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.connected = False
        self.websocket = None
        self.config = {}
        self.loop = asyncio.new_event_loop()
    
    def set_config(self, config):
        self.config = config
    
    async def connect_async(self):
        """异步连接服务器"""
        try:
            uri = f"ws://{self.config['server']}/xiaozhi/v1/"
            headers = {
                "Device-Id": self.config["device_id"],
                "Client-Id": self.config["client_id"],
                "Token": self.config["token"]
            }
            
            self.status_changed.emit("连接中...", "orange")
            self.websocket = await websockets.connect(uri, extra_headers=headers)
            self.connected = True
            self.status_changed.emit("已连接", "green")
            
            # 发送hello消息
            hello_msg = {
                "type": "hello",
                "device_id": self.config["device_id"],
                "device_name": self.config["device_name"],
                "device_mac": self.config["device_mac"],
                "token": self.config["token"],
                "features": {"mcp": True}
            }
            await self.websocket.send(json.dumps(hello_msg))
            
            # 开始接收消息
            while self.connected:
                try:
                    message = await self.websocket.recv()
                    
                    if isinstance(message, str):
                        # 文本消息
                        msg = json.loads(message)
                        self.message_received.emit(msg)
                    else:
                        # 音频消息
                        self.audio_received.emit(message)
                        
                except websockets.ConnectionClosed:
                    self.status_changed.emit("连接已断开", "red")
                    break
                    
        except Exception as e:
            self.status_changed.emit(f"连接失败: {str(e)}", "red")
    
    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_async())
    
    async def send_text_async(self, text):
        """异步发送文本消息"""
        if not self.connected or not self.websocket:
            return
            
        text_msg = {
            "type": "listen",
            "mode": "manual",
            "state": "detect",
            "text": text
        }
        await self.websocket.send(json.dumps(text_msg))
    
    def send_text(self, text):
        """发送文本消息"""
        asyncio.run_coroutine_threadsafe(self.send_text_async(text), self.loop)
    
    async def start_recording_async(self):
        """异步发送开始录音消息"""
        if not self.connected or not self.websocket:
            return
            
        start_msg = {
            "type": "listen",
            "mode": "manual",
            "state": "start"
        }
        await self.websocket.send(json.dumps(start_msg))
    
    def start_recording(self):
        """通知服务器开始录音"""
        asyncio.run_coroutine_threadsafe(self.start_recording_async(), self.loop)
    
    async def stop_recording_async(self):
        """异步发送停止录音消息"""
        if not self.connected or not self.websocket:
            return
            
        stop_msg = {
            "type": "listen",
            "mode": "manual",
            "state": "stop"
        }
        await self.websocket.send(json.dumps(stop_msg))
    
    def stop_recording(self):
        """通知服务器停止录音"""
        asyncio.run_coroutine_threadsafe(self.stop_recording_async(), self.loop)
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)

class RoundedButton(QPushButton):
    """圆角按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

class CardWidget(QFrame):
    """卡片式容器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            CardWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f8f9fa);
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小智语音聊天客户端")
        self.setGeometry(100, 100, 1000, 750)
        
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #6a11cb, stop: 1 #2575fc);
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #dce4ec;
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 15px;
                background: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2980b9, stop: 1 #2573a7);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #21618c, stop: 1 #1b4b72);
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
            QPushButton#connectBtn {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2ecc71, stop: 1 #27ae60);
            }
            QPushButton#connectBtn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #27ae60, stop: 1 #219653);
            }
            QPushButton#recordBtn {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #e74c3c, stop: 1 #c0392b);
            }
            QPushButton#recordBtn:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #a23526);
            }
            QLineEdit, QTextEdit, QComboBox {
                background: white;
                border: 2px solid #dce4ec;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                selection-background-color: #3498db;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #3498db;
            }
            QTabWidget::pane {
                border: 1px solid #dce4ec;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.95);
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 1px solid #dce4ec;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
                color: #3498db;
            }
            QTabBar::tab:hover {
                background: #d6dbdf;
            }
            QLabel#statusLabel {
                padding: 8px 15px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QProgressBar {
                border: 2px solid #dce4ec;
                border-radius: 8px;
                text-align: center;
                background: #ecf0f1;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2ecc71, stop: 1 #27ae60);
                border-radius: 8px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 初始化组件
        self.init_ui()
        
        # 初始化音频组件
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        self.recorder.audio_data_signal.connect(self.send_audio_data)
        
        # 初始化WebSocket客户端
        self.ws_client = WebSocketClient()
        self.ws_client.message_received.connect(self.handle_message)
        self.ws_client.audio_received.connect(self.play_audio)
        self.ws_client.status_changed.connect(self.update_status)
        
        # 配置
        self.config = {
            "server": "10.184.130.161:8000",
            "device_id": "web_test_device",
            "device_name": "PyQt客户端",
            "device_mac": "00:11:22:33:44:55",
            "client_id": "pyqt_client",
            "token": "your-token"
        }

        # 初始化Opus编码器
        self.opus_encoder = Encoder(RATE, CHANNELS, 'audio')
    
    def init_ui(self):
        """初始化UI界面"""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("小智语音聊天客户端")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 使用分割器创建可调整的区域
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("""
            QSplitter::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0), stop:0.2 rgba(255, 255, 255, 0.5),
                    stop:0.5 rgba(255, 255, 255, 0.9), stop:0.8 rgba(255, 255, 255, 0.5),
                    stop:1 rgba(255, 255, 255, 0));
                height: 2px;
            }
        """)
        
        # 服务器配置区域
        server_card = CardWidget()
        server_layout = QVBoxLayout(server_card)
        server_layout.setSpacing(15)
        
        # 标题
        server_title = QLabel("服务器配置")
        server_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 5px;
                border-bottom: 2px solid #3498db;
            }
        """)
        server_layout.addWidget(server_title)
        
        # 创建表单布局
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        
        def create_form_row(label_text, widget, is_password=False):
            row = QHBoxLayout()
            row.setSpacing(15)
            label = QLabel(label_text)
            label.setMinimumWidth(90)
            label.setStyleSheet("font-weight: bold; color: #34495e;")
            row.addWidget(label)
            
            if is_password:
                widget.setEchoMode(QLineEdit.Password)
                
            row.addWidget(widget)
            return row
        
        self.server_edit = QLineEdit("10.184.130.161:8000")
        form_layout.addLayout(create_form_row("服务器地址:", self.server_edit))
        
        self.device_id_edit = QLineEdit("web_test_device")
        form_layout.addLayout(create_form_row("设备ID:", self.device_id_edit))
        
        self.device_name_edit = QLineEdit("PyQt客户端")
        form_layout.addLayout(create_form_row("设备名称:", self.device_name_edit))
        
        self.device_mac_edit = QLineEdit("00:11:22:33:44:55")
        form_layout.addLayout(create_form_row("设备MAC:", self.device_mac_edit))
        
        self.client_id_edit = QLineEdit("pyqt_client")
        form_layout.addLayout(create_form_row("客户端ID:", self.client_id_edit))
        
        self.token_edit = QLineEdit("your-token")
        form_layout.addLayout(create_form_row("认证Token:", self.token_edit, True))
        
        server_layout.addLayout(form_layout)
        
        # 连接按钮和状态
        control_row = QHBoxLayout()
        self.connect_btn = RoundedButton("连接")
        self.connect_btn.setObjectName("connectBtn")
        self.connect_btn.setMinimumHeight(40)
        self.connect_btn.clicked.connect(self.toggle_connection)
        control_row.addWidget(self.connect_btn)
        
        control_row.addStretch()
        
        self.status_label = FadeLabel("状态: 未连接")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("background-color: #e74c3c; color: white;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumWidth(120)
        control_row.addWidget(self.status_label)
        
        server_layout.addLayout(control_row)
        splitter.addWidget(server_card)
        
        # 会话区域
        chat_card = CardWidget()
        chat_layout = QVBoxLayout(chat_card)
        
        # 标题
        chat_title = QLabel("会话")
        chat_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 5px;
                border-bottom: 2px solid #3498db;
            }
        """)
        chat_layout.addWidget(chat_title)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # 文本标签页
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        text_layout.setContentsMargins(10, 10, 10, 10)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                font-size: 14px;
                background: #fcfcfc;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        text_layout.addWidget(self.chat_display)
        
        input_row = QHBoxLayout()
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("输入消息...")
        self.message_edit.returnPressed.connect(self.send_text_message)
        input_row.addWidget(self.message_edit)
        
        self.send_btn = RoundedButton("发送")
        self.send_btn.setMinimumWidth(100)
        self.send_btn.setMinimumHeight(40)
        self.send_btn.clicked.connect(self.send_text_message)
        input_row.addWidget(self.send_btn)
        text_layout.addLayout(input_row)
        
        self.tab_widget.addTab(text_tab, "� 文本聊天")
        
        # 语音标签页
        voice_tab = QWidget()
        voice_layout = QVBoxLayout(voice_tab)
        voice_layout.setContentsMargins(15, 15, 15, 15)
        voice_layout.setSpacing(20)
        
        # 音频控制按钮
        audio_btn_row = QHBoxLayout()
        audio_btn_row.addStretch()
        
        self.record_btn = RoundedButton("� 开始录音")
        self.record_btn.setObjectName("recordBtn")
        self.record_btn.setMinimumSize(150, 50)
        self.record_btn.clicked.connect(self.toggle_recording)
        audio_btn_row.addWidget(self.record_btn)
        
        self.stop_btn = RoundedButton("⏹️ 停止")
        self.stop_btn.setMinimumSize(120, 50)
        self.stop_btn.clicked.connect(self.stop_recording)
        audio_btn_row.addWidget(self.stop_btn)
        
        audio_btn_row.addStretch()
        voice_layout.addLayout(audio_btn_row)
        
        # 音量指示器
        volume_frame = QFrame()
        volume_layout = QVBoxLayout(volume_frame)
        volume_title = QLabel("音量指示器")
        volume_title.setStyleSheet("font-weight: bold; color: #34495e;")
        volume_title.setAlignment(Qt.AlignCenter)
        volume_layout.addWidget(volume_title)
        
        self.volume_meter = QProgressBar()
        self.volume_meter.setRange(0, 100)
        self.volume_meter.setValue(30)
        self.volume_meter.setTextVisible(False)
        volume_layout.addWidget(self.volume_meter)
        voice_layout.addWidget(volume_frame)
        
        # 设备选择
        device_group = QGroupBox("音频设备设置")
        device_layout = QVBoxLayout(device_group)
        
        device_form = QVBoxLayout()
        device_form.setSpacing(12)
        
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("输入设备:"))
        self.input_device_combo = QComboBox()
        input_row.addWidget(self.input_device_combo)
        device_form.addLayout(input_row)
        
        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("输出设备:"))
        self.output_device_combo = QComboBox()
        output_row.addWidget(self.output_device_combo)
        device_form.addLayout(output_row)
        
        device_layout.addLayout(device_form)
        voice_layout.addWidget(device_group)
        
        voice_layout.addStretch()
        self.tab_widget.addTab(voice_tab, "�️ 语音聊天")
        
        chat_layout.addWidget(self.tab_widget)
        splitter.addWidget(chat_card)
        
        # 日志区域
        log_card = CardWidget()
        log_layout = QVBoxLayout(log_card)
        
        # 标题
        log_title = QLabel("日志信息")
        log_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 5px;
                border-bottom: 2px solid #3498db;
            }
        """)
        log_layout.addWidget(log_title)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(150)
        self.log_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monospace', monospace;
                font-size: 11px;
                background: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 6px;
            }
        """)
        log_layout.addWidget(self.log_display)
        splitter.addWidget(log_card)
        
        # 设置分割比例
        splitter.setSizes([200, 400, 150])
        main_layout.addWidget(splitter)
        
        self.setCentralWidget(central_widget)
        
        # 初始化设备列表
        self.init_audio_devices()
        
        # 禁用初始状态下的控件
        self.set_controls_enabled(False)
    
    def init_audio_devices(self):
        """初始化音频设备列表"""
        p = pyaudio.PyAudio()
        
        # 获取输入设备
        input_devices = []
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                input_devices.append((dev_info['index'], dev_info['name']))
        
        # 获取输出设备
        output_devices = []
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxOutputChannels'] > 0:
                output_devices.append((dev_info['index'], dev_info['name']))
        
        # 添加到组合框
        for idx, name in input_devices:
            self.input_device_combo.addItem(name, idx)
        
        for idx, name in output_devices:
            self.output_device_combo.addItem(name, idx)
        
        # 设置默认设备
        default_input = p.get_default_input_device_info()
        if default_input:
            self.input_device_combo.setCurrentText(default_input['name'])
        
        default_output = p.get_default_output_device_info()
        if default_output:
            self.output_device_combo.setCurrentText(default_output['name'])
        
        p.terminate()
    
    def set_controls_enabled(self, enabled):
        """设置控件启用状态"""
        self.record_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.message_edit.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.input_device_combo.setEnabled(enabled)
        self.output_device_combo.setEnabled(enabled)
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.ws_client.isRunning():
            self.disconnect_from_server()
        else:
            self.connect_to_server()
    
    def connect_to_server(self):
        """连接到服务器"""
        # 更新配置
        self.config = {
            "server": self.server_edit.text(),
            "device_id": self.device_id_edit.text(),
            "device_name": self.device_name_edit.text(),
            "device_mac": self.device_mac_edit.text(),
            "client_id": self.client_id_edit.text(),
            "token": self.token_edit.text()
        }
        
        self.ws_client.set_config(self.config)
        self.ws_client.start()
        
        self.connect_btn.setText("断开连接")
        self.log_message("正在连接服务器...")
    
    def disconnect_from_server(self):
        """断开服务器连接"""
        self.ws_client.disconnect()
        self.ws_client.quit()
        self.ws_client.wait(1000)
        
        self.connect_btn.setText("连接")
        self.status_label.setText("状态: 已断开")
        self.status_label.setStyleSheet("background-color: #e74c3c; color: white;")
        self.set_controls_enabled(False)
        self.log_message("已断开服务器连接")
    
    def update_status(self, status, color):
        """更新状态显示"""
        self.status_label.setText(f"状态: {status}")
        
        if color == "green":
            self.status_label.setStyleSheet("background-color: #2ecc71; color: white;")
        elif color == "orange":
            self.status_label.setStyleSheet("background-color: #f39c12; color: white;")
        else:
            self.status_label.setStyleSheet("background-color: #e74c3c; color: white;")
        
        # 连接成功时启用控件
        if "已连接" in status:
            self.set_controls_enabled(True)
    
    def log_message(self, message):
        """记录日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 创建不同日志级别的样式
        if "错误" in message or "失败" in message:
            color = "#e74c3c"
        elif "成功" in message or "已连接" in message:
            color = "#2ecc71"
        elif "警告" in message:
            color = "#f39c12"
        else:
            color = "#3498db"
        
        # 使用HTML格式化日志消息
        formatted_message = f'<span style="color: #95a5a6;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        
        # 移动到文档末尾并插入消息
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(formatted_message + "<br>")
        self.log_display.setTextCursor(cursor)
        self.log_display.ensureCursorVisible()
    
    def toggle_recording(self):
        """切换录音状态"""
        if not self.recorder.isRunning():
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """开始录音"""
        if not self.ws_client.connected:
            self.log_message("错误: 未连接到服务器")
            return
            
        self.recorder.start()
        self.ws_client.start_recording()
        self.record_btn.setText("� 录音中...")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #c0392b, stop: 1 #a23526);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.log_message("开始录音...")
    
    def stop_recording(self):
        """停止录音"""
        if self.recorder.isRunning():
            self.recorder.stop()
            self.ws_client.stop_recording()
            self.record_btn.setText("� 开始录音")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #e74c3c, stop: 1 #c0392b);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            self.log_message("停止录音")
    
    def send_audio_data(self, data):
        """发送音频数据"""
        if self.ws_client.connected:
            # 在这里可以添加音频编码逻辑
            # 编码为Opus格式
            # 创建Opus编码器
            # opus_encoder = Encoder(RATE, CHANNELS, 'audio')
            
            # 编码PCM为Opus
            opus_data = self.opus_encoder.encode(data, CHUNK)
            # 目前直接发送原始PCM数据
            asyncio.run_coroutine_threadsafe(
                self.ws_client.websocket.send(opus_data), 
                self.ws_client.loop
            )
    
    def send_text_message(self):
        """发送文本消息"""
        text = self.message_edit.text().strip()
        if text:
            self.ws_client.send_text(text)
            
            # 使用HTML格式化聊天消息
            formatted_message = f"""
            <div style="
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #6a11cb, stop: 1 #2575fc);
                color: white;
                padding: 10px;
                border-radius: 10px;
                margin: 5px;
                margin-left: 50px;
            ">
                <b>你:</b> {text}
            </div>
            """
            
            self.chat_display.append(formatted_message)
            self.message_edit.clear()
            self.log_message(f"发送文本消息: {text}")
    
    def play_audio(self, data):
        """播放接收到的音频"""
        if not self.player.isRunning():
            self.player.start()
            
        self.player.add_audio(data)
        self.log_message(f"收到音频数据: {len(data)}字节")
    
    def handle_message(self, message):
        """处理接收到的消息"""
        msg_type = message.get("type")
        
        if msg_type == "hello":
            self.session_id = message.get("session_id")
            self.log_message(f"服务器握手成功，会话ID: {self.session_id}")
            
        elif msg_type == "stt":
            text = message.get("text", "")
            
            # 使用HTML格式化聊天消息
            formatted_message = f"""
            <div style="
                background: #e0e0e0;
                color: #333;
                padding: 10px;
                border-radius: 10px;
                margin: 5px;
                margin-right: 50px;
            ">
                <b>语音识别:</b> {text}
            </div>
            """
            
            self.chat_display.append(formatted_message)
            self.log_message(f"语音识别结果: {text}")
            
        elif msg_type == "llm":
            text = message.get("text", "")
            
            # 使用HTML格式化聊天消息
            formatted_message = f"""
            <div style="
                background: #2ecc71;
                color: white;
                padding: 10px;
                border-radius: 10px;
                margin: 5px;
                margin-right: 50px;
            ">
                <b>小智:</b> {text}
            </div>
            """
            
            self.chat_display.append(formatted_message)
            self.log_message(f"AI回复: {text}")
            
        elif msg_type == "tts":
            state = message.get("state")
            if state == "start":
                self.log_message("服务器开始发送语音")
            elif state == "sentence_start":
                text = message.get("text", "")
                self.log_message(f"服务器发送语音段: {text}")
            elif state == "stop":
                self.log_message("服务器语音传输结束")
                
        elif msg_type == "mcp":
            payload = message.get("payload", {})
            method = payload.get("method")
            self.log_message(f"收到MCP消息: {method} {payload}")
            
            # 模拟回复MCP消息
            if method == "tools/list":
                # 实际应用中应发送正确的响应
                # 构造工具列表，包括截图、关机、亮度调节等功能
                tools_list = [
                    {
                        "name": "self.get_device_status",
                        "description": "Provides the real-time information of the device, including the current status of the audio speaker, screen, battery, network, etc.\nUse this tool for: \n1. Answering questions about current condition (e.g. what is the current volume of the audio speaker?)\n2. As the first step to control the device (e.g. turn up / down the volume of the audio speaker, etc.)",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "self.audio_speaker.set_volume",
                        "description": "Set the volume of the audio speaker. If the current volume is unknown, you must call `self.get_device_status` tool first and then call this tool.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "volume": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 100
                                }
                            },
                            "required": ["volume"]
                        }
                    },
                    {
                        "name": "self.screen.set_brightness",
                        "description": "Set the brightness of the screen.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "brightness": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 100
                                }
                            },
                            "required": ["brightness"]
                        }
                    },
                    {
                        "name": "self.screen.set_theme",
                        "description": "Set the theme of the screen. The theme can be 'light' or 'dark'.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "theme": {
                                    "type": "string"
                                }
                            },
                            "required": ["theme"]
                        }
                    },
                    # 新增工具
                    {
                        "name": "self.device.take_screenshot",
                        "description": "Take a screenshot of the current screen.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "self.device.schedule_shutdown",
                        "description": "Schedule the device to shut down after a specified number of minutes.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "minutes": {
                                    "type": "integer",
                                    "minimum": 0
                                }
                            },
                            "required": ["minutes"]
                        }
                    },
                    {
                        "name": "self.device.get_ip_address",
                        "description": "Get the IP address of the client device.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "self.audio_speaker.adjust_volume",
                        "description": "Adjust the volume level by a specified delta.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "delta": {
                                    "type": "integer",
                                    "minimum": -100,
                                    "maximum": 100
                                }
                            },
                            "required": ["delta"]
                        }
                    },
                    {
                        "name": "self.audio_speaker.mute",
                        "description": "Mute the audio speaker.",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "self.audio_speaker.unmute",
                        "description": "Unmute the audio speaker.",
                        "inputSchema": {"type": "object", "properties": {}}
                    }
                ]
                
                # 构造回复消息
                reply_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {"tools": tools_list}
                }
                
                replay_message = json.dumps({
                    "session_id": self.session_id,
                    "type": "mcp",
                    "payload": reply_payload
                })
                
                # 发送回复
                try:
                    self.log_message(f"回复MCP消息: tools/list, 工具数量: {len(tools_list)}")
                    asyncio.run_coroutine_threadsafe(
                        self.ws_client.websocket.send(replay_message), 
                        self.ws_client.loop
                    )
                except Exception as e:
                    self.log_message(f"回复tools/list失败: {str(e)}")
            elif method == "tools/call":
                call_id = payload.get("id")
                function = payload.get("params", {}).get("name")
                arguments = payload.get("params", {}).get("arguments")
                
                result = None
                success = True
                
                # 根据调用的功能名称执行相应操作
                try:
                    # 新增功能处理
                    # 屏幕亮度调节功能
                    if function == "self.screen.set_brightness":
                        brightness = arguments.get("brightness", 50)
                        success = self.set_brightness(brightness)
                        result = {"brightness": brightness}
                        
                    # 屏幕主题切换
                    elif function == "self.screen.set_theme":
                        theme = arguments.get("theme", "light")
                        success = self.set_theme(theme)
                        result = {"theme": theme}
                    if function == "self.device.take_screenshot":
                        result = self.take_screenshot()
                    elif function == "self.device.schedule_shutdown":
                        minutes = arguments.get("minutes", 0)
                        result = self.schedule_shutdown(minutes)
                    elif function == "self.device.get_ip_address":
                        result = self.get_ip_address()
                    elif function == "self.audio_speaker.adjust_volume":
                        delta = arguments.get("delta", 0)
                        result = self.adjust_volume(delta)
                    elif function == "self.audio_speaker.mute":
                        result = self.mute_audio()
                    elif function == "self.audio_speaker.unmute":
                        result = self.unmute_audio()
                    else:
                        # 其他预定义功能的处理
                        self.log_message(f"暂未实现功能调用: {function}")
                        result = {"status": "not_implemented"}
                except Exception as e:
                    success = False
                    result = {"error": str(e)}
                    self.log_message(f"功能调用失败: {function} - {str(e)}")
                
                # 构造回复消息
                reply_payload = {
                    "jsonrpc": "2.0",
                    "id": call_id,
                    "result": {"status": "success" if success else "error", "data": result}
                }
                
                replay_message = json.dumps({
                    "session_id": self.session_id,
                    "type": "mcp",
                    "payload": reply_payload
                })
                
                # 发送回复
                try:
                    self.log_message(f"回复tools/call: {function}, 结果: {result}")
                    asyncio.run_coroutine_threadsafe(
                        self.ws_client.websocket.send(replay_message), 
                        self.ws_client.loop
                    )
                except Exception as e:
                    self.log_message(f"回复tools/call失败: {str(e)}")
                
        else:
            self.log_message(f"未知消息类型: {msg_type} - {json.dumps(message)}")
    
    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        if self.recorder.isRunning():
            self.recorder.stop()
        
        if self.player.isRunning():
            self.player.stop()
        
        if self.ws_client.isRunning():
            self.ws_client.disconnect()
            self.ws_client.quit()
            self.ws_client.wait(1000)
        
        event.accept()

    # 新增功能实现方法
    def take_screenshot(self):
        """截取屏幕截图"""
        # 实际实现需要根据平台使用相应库
        # 这里返回模拟结果
        self.log_message("屏幕截图已保存")
        return {"file_path": "/screenshots/screenshot.jpg", "timestamp": "2023-01-01T12:00:00Z"}
    
    def schedule_shutdown(self, minutes):
        """设置定时关机"""
        # 实际实现需要根据平台使用相应库
        self.log_message(f"设备将在 {minutes} 分钟后关机")
        return {"shutdown_time": f"{minutes}分钟后"}
    
    def get_ip_address(self):
        """获取客户端IP地址"""
        # 返回模拟结果
        return {"ip_address": "192.168.1.100", "interface": "Ethernet"}
    
    def adjust_volume(self, delta):
        """调整音量"""
        # 实际实现需要平台特定代码
        self.log_message(f"音量调整: {delta}")
        return {"volume_level": 70 + delta}
    
    def mute_audio(self):
        """静音"""
        # 实际实现需要平台特定代码
        self.log_message("音频已静音")
        return {"muted": True}
    
    def unmute_audio(self):
        """取消静音"""
        # 实际实现需要平台特定代码
        self.log_message("取消音频静音")
        return {"muted": False}

    def set_brightness(self, brightness):
        """设置屏幕亮度 (0-100)"""
        self.log_message(f"设置屏幕亮度: {brightness}%")
        
        # 根据操作系统调用不同的实现
        os_name = platform.system()
        
        if os_name == "Windows":
            return self.set_brightness_windows(brightness)
        elif os_name == "Darwin":  # macOS
            return self.set_brightness_macos(brightness)
        elif os_name == "Linux":
            return self.set_brightness_linux(brightness)
        else:
            self.log_message(f"不支持的操作系统: {os_name}")
            return False
    
    def set_brightness_windows(self, brightness):
        """Windows系统设置亮度"""
        try:
            import wmi
            import win32api
            import win32con
            import win32security
            
            # 获取物理显示器
            c = wmi.WMI(namespace='wmi')
            monitors = c.WmiMonitorBrightness()
            
            if len(monitors) == 0:
                self.log_message("未找到显示器")
                return False
            
            # 设置亮度
            for monitor in monitors:
                # 亮度范围转换 (0-100 -> 0-100)
                adjusted_brightness = max(0, min(100, brightness))
                monitor.WmiSetBrightness(adjusted_brightness, 0)
            
            self.log_message(f"成功设置亮度: {brightness}%")
            return True
            
        except ImportError:
            # 如果没有安装所需库，尝试使用PowerShell命令
            try:
                import subprocess
                
                # 转换为10-100的范围 (许多显示器最低亮度为10%)
                adjusted_brightness = max(10, brightness)
                
                script = (
                    "$brightness = $args[0]; "
                    "$monitor = (Get-WmiObject -Namespace 'root\\wmi' -Class WmiMonitorBrightness).InstanceName; "
                    "$class = Get-WmiObject -Namespace 'root\\wmi' -Class WmiMonitorBrightnessMethods; "
                    "$class.WmiSetBrightness(1, $brightness)"
                )
                
                subprocess.run(
                    ["powershell", "-Command", script, str(adjusted_brightness)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                
                self.log_message(f"使用PowerShell设置亮度: {brightness}%")
                return True
                
            except Exception as e:
                self.log_message(f"设置亮度失败: {str(e)}")
                return False
    
    def set_brightness_macos(self, brightness):
        """macOS系统设置亮度"""
        try:
            import subprocess
            
            # 亮度范围转换 (0-100 -> 0-1)
            adjusted_brightness = max(0, min(100, brightness)) / 100.0
            
            # 使用AppleScript设置亮度
            script = f'''
            tell application "System Events"
                set brightness to {adjusted_brightness}
                repeat with i from 1 to (count of brightness of displays)
                    set the brightness of display i to brightness
                end repeat
            end tell
            '''
            
            subprocess.run(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            self.log_message(f"成功设置亮度: {brightness}%")
            return True
            
        except Exception as e:
            self.log_message(f"设置亮度失败: {str(e)}")
            return False
    
    def set_brightness_linux(self, brightness):
        """Linux系统设置亮度"""
        try:
            import subprocess
            import os
            
            # 尝试使用xrandr设置亮度
            try:
                # 获取当前连接的显示器
                result = subprocess.run(
                    ["xrandr", "--verbose"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                
                # 解析输出以获取显示器名称
                displays = []
                for line in result.stdout.splitlines():
                    if " connected" in line:
                        display = line.split()[0]
                        displays.append(display)
                
                if not displays:
                    self.log_message("未找到连接的显示器")
                    return False
                
                # 转换为亮度值 (0.1-1.0)
                adjusted_brightness = max(0.1, brightness / 100.0)
                
                # 为每个显示器设置亮度
                for display in displays:
                    subprocess.run(
                        ["xrandr", "--output", display, "--brightness", str(adjusted_brightness)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                
                self.log_message(f"使用xrandr设置亮度: {brightness}%")
                return True
                
            except Exception:
                # 如果xrandr不可用，尝试直接写入/sys/class/backlight
                try:
                    backlight_dirs = os.listdir("/sys/class/backlight")
                    if not backlight_dirs:
                        self.log_message("未找到背光设备")
                        return False
                    
                    # 使用第一个找到的背光设备
                    backlight_dir = os.path.join("/sys/class/backlight", backlight_dirs[0])
                    
                    # 获取最大亮度值
                    with open(os.path.join(backlight_dir, "max_brightness"), "r") as f:
                        max_brightness = int(f.read().strip())
                    
                    # 计算目标亮度 (0-max_brightness)
                    target_brightness = int(max(1, brightness * max_brightness / 100))
                    
                    # 写入亮度值 (需要root权限)
                    with open(os.path.join(backlight_dir, "brightness"), "w") as f:
                        f.write(str(target_brightness))
                    
                    self.log_message(f"通过/sys/class/backlight设置亮度: {brightness}%")
                    return True
                    
                except Exception as e:
                    self.log_message(f"直接设置背光失败: {str(e)}")
                    return False
                    
        except Exception as e:
            self.log_message(f"设置亮度失败: {str(e)}")
            return False
    
    def set_theme(self, theme):
        """设置屏幕主题 (light/dark)"""
        self.log_message(f"设置屏幕主题: {theme}")
        
        # 转换主题值为小写
        theme = theme.lower()
        if theme not in ["light", "dark"]:
            self.log_message(f"无效的主题: {theme}")
            return False
        
        # 根据操作系统调用不同的实现
        os_name = platform.system()
        
        if os_name == "Windows":
            return self.set_theme_windows(theme)
        elif os_name == "Darwin":  # macOS
            return self.set_theme_macos(theme)
        elif os_name == "Linux":
            return self.set_theme_linux(theme)
        else:
            self.log_message(f"不支持的操作系统: {os_name}")
            return False
    
    def set_theme_windows(self, theme):
        """Windows系统设置主题"""
        try:
            # 使用注册表设置主题
            import winreg
            
            # 打开注册表项
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            
            # 设置AppsUseLightTheme
            apps_value = 0 if theme == "dark" else 1
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, apps_value)
            
            # 设置SystemUusesLightTheme
            system_value = 0 if theme == "dark" else 1
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, system_value)
            
            winreg.CloseKey(key)
            
            # 发送消息通知系统主题改变
            import win32gui
            import win32con
            
            win32gui.SendMessage(
                win32con.HWND_BROADCAST,
                win32con.WM_SETTINGCHANGE,
                0,
                "ImmersiveColorScheme"
            )
            
            self.log_message(f"成功设置主题: {theme}")
            return True
            
        except Exception as e:
            self.log_message(f"设置主题失败: {str(e)}")
            return False
    
    def set_theme_macos(self, theme):
        """macOS系统设置主题"""
        try:
            import subprocess
            
            # 设置外观 (light, dark, auto)
            script = f'''
            tell application "System Events"
                tell appearance preferences
                    set dark mode to {("true" if theme == "dark" else "false")}
                end tell
            end tell
            '''
            
            subprocess.run(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            self.log_message(f"成功设置主题: {theme}")
            return True
            
        except Exception as e:
            self.log_message(f"设置主题失败: {str(e)}")
            return False
    
    def set_theme_linux(self, theme):
        """Linux系统设置主题"""
        try:
            # 尝试使用GNOME设置
            import subprocess
            
            # 设置GTK主题
            gtk_theme = "Adwaita" if theme == "light" else "Adwaita-dark"
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", gtk_theme],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            # 设置图标主题 (可选)
            icon_theme = "Adwaita" if theme == "light" else "gnome"
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", icon_theme],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            self.log_message(f"成功设置主题: {theme}")
            return True
            
        except Exception as e:
            self.log_message(f"设置主题失败: {str(e)}")
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用字体
    font = QFont("微软雅黑", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())