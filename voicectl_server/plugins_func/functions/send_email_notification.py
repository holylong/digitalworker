from config.logger import setup_logging
from config.config_loader import load_config
from plugins_func.register import register_function, ToolType
import sys
import os

# 添加项目根目录到Python路径，以便导入demos中的模块
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.send_email_api import send_email, get_contact_by_name

TAG = __name__
logger = setup_logging()

CALL_PERSON_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "call_person",
        "description": "通知某人开会，发送邮件给指定联系人",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "联系人姓名，例如张三",
                },
                "meeting_topic": {
                    "type": "string",
                    "description": "会议主题，默认为'会议通知'",
                },
                "meeting_content": {
                    "type": "string",
                    "description": "会议内容，默认为'请参加会议'",
                },
            },
            "required": ["name"],
        },
    },
}

@register_function("call_person", CALL_PERSON_FUNCTION_DESC, ToolType.NONE)
def call_person(name, meeting_topic="会议通知", meeting_content="请参加会议"):
    """
    通知某人开会，发送邮件给指定联系人
    
    Args:
        name (str): 联系人姓名
        meeting_topic (str): 会议主题
        meeting_content (str): 会议内容
    
    Returns:
        dict: 执行结果
    """
    try:
        # 加载配置
        config = load_config()
        
        # 获取邮件API配置
        email_api_config = config.get("email_api", {})
        contact_api_url = email_api_config.get("contacts_url", "http://localhost:5000/api/contacts")
        email_api_url = email_api_config.get("send_url", "http://localhost:5000/api/email")
        
        # 1. 获取联系人邮箱
        logger.bind(tag=TAG).info(f"获取联系人 {name} 的邮箱信息")
        contact_result = get_contact_by_name(contact_api_url, name)
        
        if contact_result.get("code") != 200 or "data" not in contact_result:
            error_msg = contact_result.get('message', '未知错误')
            logger.bind(tag=TAG).error(f"获取联系人 {name} 失败: {error_msg}")
            
            # 检查是否是连接失败
            if "Connection refused" in error_msg or "ConnectionError" in error_msg or "Failed to establish a new connection" in error_msg:
                return {
                    "code": 500,
                    "message": f"邮件服务连接失败，无法通知 {name}"
                }
            
            return {
                "code": 404,
                "message": f"无法找到联系人 {name} 的邮箱信息"
            }
        
        emails = contact_result["data"]
        if not emails:
            logger.bind(tag=TAG).error(f"未找到联系人 {name} 的邮箱")
            return {
                "code": 404,
                "message": f"未找到联系人 {name} 的邮箱"
            }
        
        # 2. 发送邮件给所有匹配的邮箱
        results = []
        
        for email in emails:
            logger.bind(tag=TAG).info(f"发送邮件给 {email}，主题：{meeting_topic}")
            email_result = send_email(
                email_api_url,
                email,
                meeting_topic,
                meeting_content
            )
            
            if email_result.get("code") == 200:
                results.append(f"成功发送邮件给 {email}")
                logger.bind(tag=TAG).info(f"成功发送邮件给 {email}")
            else:
                results.append(f"发送邮件给 {email} 失败: {email_result.get('message')}")
                logger.bind(tag=TAG).error(f"发送邮件给 {email} 失败: {email_result.get('message')}")
        
        return {
            "code": 200,
            "message": "操作完成",
            "data": {
                "results": results,
                "contact": name,
                "topic": meeting_topic
            }
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.bind(tag=TAG).error(f"发送邮件通知失败: {error_msg}")
        
        # 检查是否是连接失败
        if "Connection refused" in error_msg or "ConnectionError" in error_msg or "Failed to establish a new connection" in error_msg:
            return {
                "code": 500,
                "message": f"邮件服务连接失败，无法发送通知"
            }
        
        return {
            "code": 500,
            "message": f"发送邮件通知失败: {error_msg}"
        }