#!/usr/bin/env python3
"""
邮件发送API调用脚本
用于通过RESTful API发送邮件
"""

import argparse
import json
import requests
import sys

def send_email(api_url, to_email, subject, content):
    """
    发送邮件API请求
    
    Args:
        api_url: API端点URL
        to_email: 收件人邮箱
        subject: 邮件主题
        content: 邮件内容
    
    Returns:
        dict: API响应结果
    """
    try:
        # 构建请求数据
        payload = {
            "to": to_email,
            "subject": subject,
            "content": content
        }
        
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 发送POST请求
        response = requests.post(api_url, json=payload, headers=headers)
        
        # 解析响应
        result = response.json()
        result["status_code"] = response.status_code
        
        return result
    except Exception as e:
        return {
            "status_code": 500,
            "code": 500,
            "message": f"请求失败：{str(e)}"
        }

def get_contacts(api_url):
    """
    获取所有联系人
    
    Args:
        api_url: API端点URL
    
    Returns:
        dict: API响应结果
    """
    try:
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 发送GET请求
        response = requests.get(api_url, headers=headers)
        
        # 解析响应
        result = response.json()
        result["status_code"] = response.status_code
        
        return result
    except Exception as e:
        return {
            "status_code": 500,
            "code": 500,
            "message": f"请求失败：{str(e)}"
        }

def get_contact_by_name(api_url, name):
    """
    通过名字获取联系人，先比对中文再比对英文
    
    Args:
        api_url: API端点URL
        name: 联系人姓名
    
    Returns:
        dict: API响应结果
    """
    try:
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 发送GET请求
        response = requests.get(f"{api_url}/email/{name}", headers=headers)
        
        # 解析响应
        result = response.json()
        result["status_code"] = response.status_code
        
        return result
    except Exception as e:
        return {
            "status_code": 500,
            "code": 500,
            "message": f"请求失败：{str(e)}"
        }

def main():
    """
    主函数，处理命令行参数并执行相应操作
    """
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="通过RESTful API进行邮件发送和联系人管理")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 发送邮件子命令
    email_parser = subparsers.add_parser("send", help="发送邮件")
    email_parser.add_argument("--api-url", default="http://localhost:5000/api/email", 
                              help="邮件发送API端点URL，默认：http://localhost:5000/api/email")
    email_parser.add_argument("--to", required=True, help="收件人邮箱地址")
    email_parser.add_argument("--subject", required=True, help="邮件主题")
    email_parser.add_argument("--content", required=True, help="邮件内容")
    
    # 获取所有联系人和命令
    contacts_parser = subparsers.add_parser("get-contacts", help="获取所有联系人")
    contacts_parser.add_argument("--api-url", default="http://localhost:5000/api/contacts", 
                                help="联系人API端点URL，默认：http://localhost:5000/api/contacts")
    
    # 通过名字获取联系人子命令
    contact_by_name_parser = subparsers.add_parser("get-contact", help="通过名字获取联系人")
    contact_by_name_parser.add_argument("--api-url", default="http://localhost:5000/api/contacts", 
                                      help="联系人API端点URL，默认：http://localhost:5000/api/contacts")
    contact_by_name_parser.add_argument("--name", required=True, help="联系人姓名")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    if args.command == "send":
        # 发送邮件
        print(f"📧 准备发送邮件...")
        print(f"   API地址: {args.api_url}")
        print(f"   收件人: {args.to}")
        print(f"   主题: {args.subject}")
        print(f"   内容: {args.content[:50]}{'...' if len(args.content) > 50 else ''}")
        
        result = send_email(args.api_url, args.to, args.subject, args.content)
        
        # 显示结果
        print(f"\n📋 发送结果:")
        print(f"   HTTP状态码: {result['status_code']}")
        print(f"   API返回码: {result.get('code')}")
        print(f"   消息: {result.get('message')}")
        
        # 根据结果设置退出码
        if result.get('code') == 200:
            print(f"\n✅ 邮件发送成功！")
            sys.exit(0)
        else:
            print(f"\n❌ 邮件发送失败！")
            sys.exit(1)
    elif args.command == "get-contacts":
        # 获取所有联系人
        print(f"📋 准备获取所有联系人...")
        print(f"   API地址: {args.api_url}")
        
        result = get_contacts(args.api_url)
        
        # 显示结果
        print(f"\n📋 获取结果:")
        print(f"   HTTP状态码: {result['status_code']}")
        print(f"   API返回码: {result.get('code')}")
        print(f"   消息: {result.get('message')}")
        
        if result.get('code') == 200 and 'data' in result:
            contacts = result['data']
            print(f"\n📋 联系人列表 ({len(contacts)} 个):")
            for contact in contacts:
                print(f"   ID: {contact['id']}, 姓名: {contact['name']}, 邮箱: {contact['email']}")
                if contact.get('position'):
                    print(f"       职位: {contact['position']}")
                if contact.get('english_name'):
                    print(f"       英文名: {contact['english_name']}")
                if contact.get('phone'):
                    print(f"       电话: {contact['phone']}")
            print(f"\n✅ 获取联系人成功！")
            sys.exit(0)
        else:
            print(f"\n❌ 获取联系人失败！")
            sys.exit(1)
    elif args.command == "get-contact":
        # 通过名字获取联系人
        print(f"🔍 准备通过名字获取联系人...")
        print(f"   API地址: {args.api_url}")
        print(f"   姓名: {args.name}")
        
        result = get_contact_by_name(args.api_url, args.name)
        
        # 显示结果
        print(f"\n📋 获取结果:")
        print(f"   HTTP状态码: {result['status_code']}")
        print(f"   API返回码: {result.get('code')}")
        print(f"   消息: {result.get('message')}")
        
        if result.get('code') == 200 and 'data' in result:
            emails = result['data']
            print(f"\n📋 匹配的邮箱 ({len(emails)} 个):")
            for email in emails:
                print(f"   - {email}")
            print(f"\n✅ 获取联系人邮箱成功！")
            sys.exit(0)
        else:
            print(f"\n❌ 获取联系人邮箱失败！")
            sys.exit(1)
    else:
        # 未指定命令，显示帮助信息
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
