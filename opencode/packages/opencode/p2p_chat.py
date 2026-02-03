import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
import socket
import threading
import json
import time
import uuid
import hashlib
import random
from datetime import datetime
import platform
from typing import Dict, Any, Callable


class PeerDiscovery:
    def __init__(self, port=5000):
        self.port = port
        self.broadcast_port = port + 1
        self.peers = {}
        self.running = False
        self.username = f"User_{random.randint(1000, 9999)}"
        self.peer_id = str(uuid.uuid4())
        
    def start_discovery(self):
        self.running = True
        threading.Thread(target=self._listen_for_broadcasts, daemon=True).start()
        threading.Thread(target=self._broadcast_presence, daemon=True).start()
        
    def stop_discovery(self):
        self.running = False
        
    def _listen_for_broadcasts(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        try:
            sock.bind(('', self.broadcast_port))
        except OSError:
            sock.bind(('', self.broadcast_port + 1))
            
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode())
                
                if message.get('type') == 'discovery' and message.get('peer_id') != self.peer_id:
                    self.peers[message['peer_id']] = {
                        'username': message['username'],
                        'address': addr[0],
                        'port': message.get('port', self.port),
                        'last_seen': time.time()
                    }
                    
                    # Send response
                    response = {
                        'type': 'discovery_response',
                        'peer_id': self.peer_id,
                        'username': self.username,
                        'port': self.port
                    }
                    sock.sendto(json.dumps(response).encode(), addr)
                    
            except Exception as e:
                pass
                
    def _broadcast_presence(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            try:
                message = {
                    'type': 'discovery',
                    'peer_id': self.peer_id,
                    'username': self.username,
                    'port': self.port
                }
                sock.sendto(json.dumps(message).encode(), ('<broadcast>', self.broadcast_port))
                time.sleep(5)
                
            except Exception as e:
                time.sleep(5)
                
    def get_active_peers(self):
        current_time = time.time()
        active_peers = {}
        for peer_id, peer_info in self.peers.items():
            if current_time - peer_info['last_seen'] < 15:
                active_peers[peer_id] = peer_info
        return active_peers


class ChatServer:
    def __init__(self, port=5000):
        self.port = port
        self.server_socket: socket.socket | None = None
        self.clients = {}
        self.running = False
        self.message_callback: Callable[[Dict[str, Any]], None] | None = None
        
    def start_server(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(5)
            threading.Thread(target=self._accept_connections, daemon=True).start()
        except OSError:
            self.port += 1
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(5)
            threading.Thread(target=self._accept_connections, daemon=True).start()
            
    def stop_server(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            
    def _accept_connections(self):
        while self.running and self.server_socket:
            try:
                client_socket, addr = self.server_socket.accept()
                client_id = str(uuid.uuid4())
                self.clients[client_id] = {
                    'socket': client_socket,
                    'address': addr[0],
                    'connected': True
                }
                threading.Thread(target=self._handle_client, args=(client_id,), daemon=True).start()
                
            except Exception as e:
                break
                
    def _handle_client(self, client_id):
        client = self.clients[client_id]
        socket_client = client['socket']
        
        while self.running and client['connected']:
            try:
                data = socket_client.recv(4096)
                if data:
                    message = json.loads(data.decode())
                    message['timestamp'] = datetime.now().strftime('%H:%M:%S')
                    
                    if self.message_callback:
                        self.message_callback(message)
                        
                    # Broadcast to other clients
                    self._broadcast_message(message, exclude_client=client_id)
                else:
                    break
                    
            except Exception as e:
                break
                
        client['connected'] = False
        socket_client.close()
        
    def _broadcast_message(self, message, exclude_client=None):
        message_str = json.dumps(message)
        for client_id, client in self.clients.items():
            if client_id != exclude_client and client['connected']:
                try:
                    client['socket'].send(message_str.encode())
                except:
                    client['connected'] = False
                    
    def send_message(self, message):
        self._broadcast_message(message)


class ChatClient:
    def __init__(self):
        self.socket: socket.socket | None = None
        self.connected = False
        self.message_callback: Callable[[Dict[str, Any]], None] | None = None
        
    def connect(self, host, port=5000):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            
            threading.Thread(target=self._listen_for_messages, daemon=True).start()
            return True
        except Exception as e:
            return False
            
    def disconnect(self):
        self.connected = False
        if self.socket:
            self.socket.close()
            
    def _listen_for_messages(self):
        while self.connected and self.socket:
            try:
                data = self.socket.recv(4096)
                if data:
                    message = json.loads(data.decode())
                    message['timestamp'] = datetime.now().strftime('%H:%M:%S')
                    
                    if self.message_callback:
                        self.message_callback(message)
                else:
                    break
            except Exception as e:
                break
                
        self.connected = False
        if self.socket:
            self.socket.close()
        
    def send_message(self, message):
        if self.connected and self.socket:
            try:
                self.socket.send(json.dumps(message).encode())
                return True
            except Exception as e:
                self.connected = False
                return False
        return False


class P2PChatApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("P2P局域网聊天工具")
        self.root.geometry("900x700")
        self.root.configure(bg='#1e1e1e')
        
        # 设置窗口图标和样式
        self.root.tk_setPalette(background='#1e1e1e', foreground='#ffffff',
                               activeBackground='#3a3a3a', activeForeground='#ffffff')
        
        # 初始化组件
        self.discovery = PeerDiscovery()
        self.server = ChatServer()
        self.client = ChatClient()
        
        self.server.message_callback = self.on_message_received
        self.client.message_callback = self.on_message_received
        
        self.connected_peers = {}
        self.chat_history = []
        
        self.setup_ui()
        self.start_services()
        
    def setup_ui(self):
        # 主容器
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部信息栏
        self.setup_header(main_frame)
        
        # 中间内容区域
        content_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 左侧用户列表
        self.setup_user_list(content_frame)
        
        # 右侧聊天区域
        self.setup_chat_area(content_frame)
        
        # 底部输入区域
        self.setup_input_area(main_frame)
        
    def setup_header(self, parent):
        header_frame = ttk.Frame(parent, style='Dark.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 用户名显示
        username_label = tk.Label(header_frame, 
                                text=f"用户名: {self.discovery.username}",
                                font=('Arial', 12, 'bold'),
                                bg='#1e1e1e', fg='#4fc3f7')
        username_label.pack(side=tk.LEFT)
        
        # 在线状态指示器
        self.status_indicator = tk.Label(header_frame, text="● 在线", 
                                       font=('Arial', 10),
                                       bg='#1e1e1e', fg='#4caf50')
        self.status_indicator.pack(side=tk.LEFT, padx=(20, 0))
        
        # 端口显示
        self.port_label = tk.Label(header_frame, 
                                 text=f"端口: {self.server.port}",
                                 font=('Arial', 10),
                                 bg='#1e1e1e', fg='#888888')
        self.port_label.pack(side=tk.RIGHT)
        
    def setup_user_list(self, parent):
        # 用户列表容器
        user_frame = ttk.Frame(parent, style='Dark.TFrame')
        user_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 用户列表标题
        user_title = tk.Label(user_frame, text="在线用户", 
                            font=('Arial', 14, 'bold'),
                            bg='#1e1e1e', fg='#ffffff')
        user_title.pack(pady=(0, 10))
        
        # 用户列表
        self.user_listbox = tk.Listbox(user_frame, width=20, height=15,
                                      bg='#2a2a2a', fg='#ffffff',
                                      selectbackground='#4a4a4a',
                                      font=('Arial', 10))
        self.user_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 刷新按钮
        refresh_btn = tk.Button(user_frame, text="刷新用户",
                              bg='#4fc3f7', fg='#1e1e1e',
                              font=('Arial', 10, 'bold'),
                              command=self.refresh_user_list)
        refresh_btn.pack(pady=(10, 0), fill=tk.X)
        
    def setup_chat_area(self, parent):
        # 聊天区域容器
        chat_frame = ttk.Frame(parent, style='Dark.TFrame')
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 聊天标题
        chat_title = tk.Label(chat_frame, text="聊天消息", 
                            font=('Arial', 14, 'bold'),
                            bg='#1e1e1e', fg='#ffffff')
        chat_title.pack(pady=(0, 10))
        
        # 聊天消息显示区域
        self.chat_display = scrolledtext.ScrolledText(chat_frame, 
                                                     wrap=tk.WORD,
                                                     width=60, height=20,
                                                     bg='#2a2a2a', fg='#ffffff',
                                                     font=('Arial', 10),
                                                     state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
    def setup_input_area(self, parent):
        # 输入区域容器
        input_frame = ttk.Frame(parent, style='Dark.TFrame')
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 消息输入框
        self.message_entry = tk.Entry(input_frame, 
                                     font=('Arial', 11),
                                     bg='#2a2a2a', fg='#ffffff',
                                     insertbackground='#ffffff')
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        # 发送按钮
        send_btn = tk.Button(input_frame, text="发送", 
                           bg='#4caf50', fg='#1e1e1e',
                           font=('Arial', 10, 'bold'),
                           command=self.send_message)
        send_btn.pack(side=tk.RIGHT)
        
    def start_services(self):
        # 启动服务器和发现服务
        self.server.start_server()
        self.discovery.start_discovery()
        
        # 定期刷新用户列表
        self.refresh_user_list()
        self.root.after(5000, self.periodic_refresh)
        
    def refresh_user_list(self):
        peers = self.discovery.get_active_peers()
        
        # 清空列表
        self.user_listbox.delete(0, tk.END)
        
        # 添加自己
        self.user_listbox.insert(tk.END, f"{self.discovery.username} (我)")
        
        # 添加其他用户
        for peer_id, peer_info in peers.items():
            display_name = f"{peer_info['username']} ({peer_info['address']})"
            self.user_listbox.insert(tk.END, display_name)
            
        # 更新在线状态
        online_count = len(peers)
        self.status_indicator.config(text=f"● 在线 ({online_count + 1}人)")
        
    def periodic_refresh(self):
        self.refresh_user_list()
        self.root.after(5000, self.periodic_refresh)
        
    def send_message(self):
        message_text = self.message_entry.get().strip()
        if not message_text:
            return
            
        # 创建消息对象
        message = {
            'type': 'chat',
            'username': self.discovery.username,
            'message': message_text,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        
        # 显示在自己的聊天窗口
        self.display_message(message, is_self=True)
        
        # 发送给连接的客户端
        self.server.send_message(message)
        
        # 清空输入框
        self.message_entry.delete(0, tk.END)
        
    def on_message_received(self, message):
        self.display_message(message, is_self=False)
        
    def display_message(self, message, is_self=False):
        # 启用文本框
        self.chat_display.config(state=tk.NORMAL)
        
        # 格式化消息
        timestamp = message.get('timestamp', datetime.now().strftime('%H:%M:%S'))
        username = message.get('username', 'Unknown')
        content = message.get('message', '')
        
        if is_self:
            formatted_msg = f"[{timestamp}] {username} (我): {content}\n"
            tag = 'self_message'
        else:
            formatted_msg = f"[{timestamp}] {username}: {content}\n"
            tag = 'other_message'
            
        # 插入消息
        self.chat_display.insert(tk.END, formatted_msg, tag)
        
        # 配置标签颜色
        if tag == 'self_message':
            self.chat_display.tag_config(tag, foreground='#4fc3f7')
        else:
            self.chat_display.tag_config(tag, foreground='#ffffff')
            
        # 自动滚动到底部
        self.chat_display.see(tk.END)
        
        # 禁用文本框
        self.chat_display.config(state=tk.DISABLED)
        
    def run(self):
        # 设置样式
        style = ttk.Style()
        style.theme_use('default')
        
        # 自定义深色主题
        style.configure('Dark.TFrame', background='#1e1e1e')
        
        # 运行主循环
        self.root.mainloop()
        
        # 清理资源
        self.stop_services()
        
    def stop_services(self):
        self.discovery.stop_discovery()
        self.server.stop_server()
        self.client.disconnect()


if __name__ == "__main__":
    app = P2PChatApp()
    app.run()