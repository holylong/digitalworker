#!/usr/bin/env python3
"""
P2P局域网聊天工具启动脚本
使用方法: python start_chat.py
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from p2p_chat import P2PChatApp
    
    print("正在启动P2P局域网聊天工具...")
    print("确保多个设备在同一个局域网内运行此工具")
    print("=" * 50)
    
    app = P2PChatApp()
    app.run()
    
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保安装了所需依赖:")
    print("pip install tkinter")
    
except Exception as e:
    print(f"启动失败: {e}")
    input("按回车键退出...")