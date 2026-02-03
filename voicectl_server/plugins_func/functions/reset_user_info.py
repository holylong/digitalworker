import json
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

reset_user_info_function_desc = {
    "type": "function",
    "function": {
        "name": "reset_user_info",
        "description": (
            "重置用户信息功能。当用户说'重置'、'重置用户信息'、'重置系统'等语句时，"
            "调用此函数删除本地数据库中的人脸信息，并重启系统。"
            ""
            "【触发场景（必须调用函数）】"
            "- 用户说'重置'：立即调用函数"
            "- 用户说'重置用户信息'：立即调用函数"
            "- 用户说'重置系统'：立即调用函数"
            "- 用户说'清空人脸'：立即调用函数"
            "- 用户说'删除人脸'：立即调用函数"
            ""
            "【禁止调用场景（必须先确认）】"
            "- 用户说'帮我重置'：禁止调用函数，必须先询问确认"
            "- 用户说'给我重置'：禁止调用函数，必须先询问确认"
            "- 用户说'我要重置'：禁止调用函数，必须先询问确认"
            ""
            "【确认规则】"
            "1. 询问时必须简洁，例如：'确定要重置用户信息吗？这将删除所有人脸数据。'"
            "2. 用户确认后，立即调用此函数"
            "3. 用户取消后，告知用户操作已取消"
            ""
            "【示例】"
            "用户：'重置' → AI：立即调用函数"
            "用户：'帮我重置' → AI：'确定要重置用户信息吗？这将删除所有人脸数据。'"
            "用户：'确定' → AI：立即调用函数"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "confirm": {
                    "type": "boolean",
                    "description": "用户是否确认重置操作，true表示确认，false表示取消",
                }
            },
            "required": [],
        },
    },
}


@register_function("reset_user_info", reset_user_info_function_desc, ToolType.MCP_CLIENT)
async def reset_user_info(confirm=False, conn=None):
    """
    用于重置用户信息，删除本地数据库中的人脸信息，并重启系统
    """
    if conn is None:
        return ActionResponse(
            Action.RESPONSE,
            "无法获取连接信息，无法执行重置操作",
            None,
        )

    try:
        mcp_client = conn.mcp_client
        if mcp_client is None:
            return ActionResponse(
                Action.RESPONSE,
                "MCP客户端未初始化，无法执行重置操作",
                None,
            )

        args = {
            "confirm": confirm,
        }

        from core.providers.tools.device_mcp.mcp_handler import call_mcp_tool

        result = await call_mcp_tool(
            conn,
            mcp_client,
            "self.reset_user_info",
            json.dumps(args),
            timeout=30,
        )

        logger.bind(tag=TAG).info(f"重置用户信息结果: {result}")

        if result and isinstance(result, dict):
            success = result.get("success", False)
            if success:
                message = result.get("message", "用户信息重置成功，系统正在重启...")
                return ActionResponse(Action.RESPONSE, message, None)
            else:
                error_message = result.get("error", "用户信息重置失败")
                return ActionResponse(Action.RESPONSE, error_message, None)
        
        return ActionResponse(Action.REQLLM, result, None)

    except Exception as e:
        logger.bind(tag=TAG).error(f"重置用户信息失败: {e}")
        return ActionResponse(
            Action.RESPONSE,
            f"用户信息重置失败: {str(e)}",
            None,
        )
