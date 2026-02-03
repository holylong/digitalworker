import json
from plugins_func.register import register_function, ToolType, ActionResponse, Action

face_register_function_desc = {
    "type": "function",
    "function": {
        "name": "face_register",
        "description": (
            "人脸注册功能。当用户说'记住我，我是XXX'、'我是XXX'等包含姓名的语句时，必须调用此函数进行人脸注册。"
            ""
            "【触发场景（必须调用函数）】"
            "- 用户说'记住我，我是张三'：立即调用函数，name='张三'"
            "- 用户说'我是李四'：立即调用函数，name='李四'"
            "- 用户说'记住我，我是王五'：立即调用函数，name='王五'"
            ""
            "【禁止调用场景（必须先询问）】"
            "- 用户说'帮我注册'：禁止调用函数，必须先询问姓名，并强调对准镜头"
            "- 用户说'给我注册'：禁止调用函数，必须先询问姓名，并强调对准镜头"
            "- 用户说'我要注册'：禁止调用函数，必须先询问姓名，并强调对准镜头"
            "- 用户说'注册人脸'：禁止调用函数，必须先询问姓名，并强调对准镜头"
            "- 用户说'记住我的脸'：禁止调用函数，必须先询问姓名，并强调对准镜头"
            ""
            "【询问姓名的规则】"
            "1. 询问时必须简洁，例如：'请告诉我您的姓名'或'您叫什么名字？'"
            "2. 询问时必须强调对准镜头，例如：'请告诉我您的姓名，并正脸对准镜头'或'您叫什么名字？请正脸对准镜头'"
            "3. 禁止回复'您想注册吗'、'需要我帮你注册吗'、'要帮你注册吗'等任何询问性语句"
            "4. 用户回答姓名后，立即调用此函数进行注册"
            ""
            "【注册流程】"
            "1. 用户说'帮我注册'等没有姓名的语句 → 询问姓名，强调对准镜头"
            "2. 用户回答姓名 → 立即调用此函数进行注册"
            "3. 函数调用终端侧拍照注册 → 用户正脸对准镜头拍照"
            "4. 注册成功 → 返回恭喜消息，告知用户注册结果"
            ""
            "【示例】"
            "用户：'帮我注册' → AI：'请告诉我您的姓名，并正脸对准镜头'"
            "用户：'我是张三' → AI：立即调用函数，name='张三'"
            "注册成功 → AI：'恭喜张三，人脸注册成功！识别到您时会自动触发唤醒词问候。'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "identity_id": {
                    "type": "string",
                    "description": "用户身份ID，例如：test1、test2等。如果用户没有提供，可以使用用户姓名的拼音或随机生成一个ID",
                },
                "role_permission": {
                    "type": "string",
                    "description": "角色权限，例如：master（管理员）、user（普通用户）等，默认为master",
                },
                "name": {
                    "type": "string",
                    "description": "用户姓名，例如：张三、李四等。从用户的语句中提取姓名，例如用户说'记住我，我是张三'，姓名就是'张三'",
                },
            },
            "required": ["identity_id", "name"],
        },
    },
}


@register_function("face_register", face_register_function_desc, ToolType.MCP_CLIENT)
async def face_register(identity_id, name, role_permission="master", conn=None):
    """
    用于注册人脸信息，将用户身份ID、角色权限和名字与人脸特征绑定
    """
    if conn is None:
        return ActionResponse(
            Action.RESPONSE,
            "无法获取连接信息，无法执行人脸注册",
            None,
        )

    try:
        mcp_client = conn.mcp_client
        if mcp_client is None:
            return ActionResponse(
                Action.RESPONSE,
                "MCP客户端未初始化，无法执行人脸注册",
                None,
            )

        args = {
            "identity_id": identity_id,
            "name": name,
            "role_permission": role_permission,
        }

        from core.providers.tools.device_mcp.mcp_handler import call_mcp_tool

        result = await call_mcp_tool(
            conn,
            mcp_client,
            "self.face_register",
            json.dumps(args),
            timeout=30,
        )

        # 检查MCP工具调用结果
        if result and isinstance(result, dict):
            success = result.get("success", False)
            if success:
                # 注册成功，直接使用客户端返回的消息
                message = result.get("message", f"恭喜{name}，人脸注册成功！")
                return ActionResponse(Action.RESPONSE, message, None)
            else:
                # 注册失败，返回错误信息
                error_message = result.get("error", "人脸注册失败")
                return ActionResponse(Action.RESPONSE, error_message, None)
        
        # 默认返回结果，让大模型生成回复
        return ActionResponse(Action.REQLLM, result, None)

    except Exception as e:
        return ActionResponse(
            Action.RESPONSE,
            f"人脸注册失败: {str(e)}",
            None,
        )
