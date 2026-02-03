"""会议总结数据库管理模块"""

import json
import os
from typing import List, Dict, Optional
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class MeetingSummary:
    """会议总结数据类"""
    
    def __init__(self, meeting_id: str, meeting_theme: str, meeting_time: str, 
                 summary: str, key_points: List[str], attendees: List[str]):
        self.meeting_id = meeting_id
        self.meeting_theme = meeting_theme
        self.meeting_time = meeting_time
        self.summary = summary
        self.key_points = key_points
        self.attendees = attendees
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "meeting_id": self.meeting_id,
            "meeting_theme": self.meeting_theme,
            "meeting_time": self.meeting_time,
            "summary": self.summary,
            "key_points": self.key_points,
            "attendees": self.attendees
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MeetingSummary':
        """从字典创建"""
        return cls(
            meeting_id=data.get("meeting_id", ""),
            meeting_theme=data.get("meeting_theme", ""),
            meeting_time=data.get("meeting_time", ""),
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            attendees=data.get("attendees", [])
        )


class MeetingSummaryDatabase:
    """会议总结数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "data/meeting_summaries.json"
        self.summaries: List[MeetingSummary] = []
        self._load_database()
    
    def _load_database(self):
        """加载数据库"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.summaries = [MeetingSummary.from_dict(item) for item in data]
                logger.bind(tag=TAG).info(f"会议总结数据库加载成功，共 {len(self.summaries)} 条记录")
            else:
                logger.bind(tag=TAG).warning(f"会议总结数据库文件不存在: {self.db_path}")
                self.summaries = []
        except Exception as e:
            logger.bind(tag=TAG).error(f"加载会议总结数据库失败: {e}")
            self.summaries = []
    
    def save_database(self):
        """保存数据库"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                data = [summary.to_dict() for summary in self.summaries]
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.bind(tag=TAG).info(f"会议总结数据库保存成功，共 {len(self.summaries)} 条记录")
        except Exception as e:
            logger.bind(tag=TAG).error(f"保存会议总结数据库失败: {e}")
    
    def add_summary(self, summary: MeetingSummary):
        """添加会议总结"""
        self.summaries.append(summary)
        self.save_database()
        logger.bind(tag=TAG).info(f"添加会议总结成功: {summary.meeting_theme}")
    
    def find_by_theme(self, theme: str) -> Optional[MeetingSummary]:
        """根据会议主题查找会议总结（字符串匹配，已弃用，建议使用find_related_by_llm）"""
        for summary in self.summaries:
            if theme.lower() in summary.meeting_theme.lower() or summary.meeting_theme.lower() in theme.lower():
                logger.bind(tag=TAG).info(f"找到相关会议总结: {summary.meeting_theme}")
                return summary
        logger.bind(tag=TAG).info(f"未找到与主题 '{theme}' 相关的会议总结")
        return None
    
    def find_related_by_llm(self, theme: str, llm_client=None) -> Optional[MeetingSummary]:
        """使用大模型根据会议主题查找相关的会议总结"""
        if not llm_client:
            logger.bind(tag=TAG).warning("未提供LLM客户端，无法使用大模型匹配")
            return None
        
        try:
            # 构建数据库中所有会议主题的列表
            all_themes = []
            for summary in self.summaries:
                all_themes.append(f"会议ID: {summary.meeting_id} - {summary.meeting_theme}（{summary.meeting_time}）")
            
            themes_text = "\n".join(all_themes)
            
            # 构建系统提示词
            system_prompt = """你是一个智能会议助手，需要根据当前会议主题，从历史会议总结中找到最相关的会议。

请分析当前会议主题与历史会议总结的相关性，并返回最相关的会议ID。

重要说明：
1. 会议ID是数字编号，如 001、002、003 等
2. 只返回会议ID，不要返回会议主题、时间或其他信息
3. 如果没有任何历史会议与当前会议主题相关，请返回"无"

示例：
- 正确：001
- 错误：ollo机器人产品需求评审会（2026-01-10 14:00）
- 错误：会议ID: 001
- 错误：无相关会议

只返回会议ID（如001、002）或"无"，不要返回其他内容。"""
            
            # 构建用户提示词
            user_prompt = f"""当前会议主题：{theme}

历史会议总结列表：
{themes_text}"""
            
            # 调用大模型
            logger.bind(tag=TAG).info(f"使用大模型匹配会议主题: {theme}")
            result = llm_client.response_no_stream(system_prompt, user_prompt)
            
            if not result:
                logger.bind(tag=TAG).warning("大模型返回空结果")
                return None
            
            # 清理结果
            result = result.strip()
            logger.bind(tag=TAG).info(f"大模型返回结果: {result}")
            
            # 检查是否返回"无"
            if result == "无" or result.lower() == "none":
                logger.bind(tag=TAG).info(f"大模型判断无相关会议总结")
                return None
            
            # 查找对应的会议总结
            for summary in self.summaries:
                if summary.meeting_id == result:
                    logger.bind(tag=TAG).info(f"大模型找到相关会议总结: {summary.meeting_theme}")
                    return summary
            
            logger.bind(tag=TAG).warning(f"大模型返回的会议ID '{result}' 未在数据库中找到")
            return None
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"使用大模型匹配会议主题失败: {e}")
            return None
    
    def get_all_summaries(self) -> List[MeetingSummary]:
        """获取所有会议总结"""
        return self.summaries.copy()
    
    def get_summary_by_id(self, meeting_id: str) -> Optional[MeetingSummary]:
        """根据会议ID查找会议总结"""
        for summary in self.summaries:
            if summary.meeting_id == meeting_id:
                return summary
        return None
    
    def delete_summary(self, meeting_id: str) -> bool:
        """删除会议总结"""
        for i, summary in enumerate(self.summaries):
            if summary.meeting_id == meeting_id:
                self.summaries.pop(i)
                self.save_database()
                logger.bind(tag=TAG).info(f"删除会议总结成功: {meeting_id}")
                return True
        logger.bind(tag=TAG).warning(f"未找到会议总结: {meeting_id}")
        return False


# 全局数据库实例
_database_instance: Optional[MeetingSummaryDatabase] = None


def get_meeting_summary_database(db_path: str = None) -> MeetingSummaryDatabase:
    """获取会议总结数据库实例（单例模式）"""
    global _database_instance
    if _database_instance is None:
        _database_instance = MeetingSummaryDatabase(db_path)
    return _database_instance


def init_default_summaries():
    """初始化默认的8个会议总结"""
    db = get_meeting_summary_database()
    
    if len(db.summaries) > 0:
        logger.bind(tag=TAG).info("会议总结数据库已有数据，跳过初始化")
        return
    
    default_summaries = [
        MeetingSummary(
            meeting_id="001",
            meeting_theme="ollo机器人产品需求评审会",
            meeting_time="2026-01-10 14:00",
            summary="本次会议主要讨论了ollo机器人Q1季度产品需求，确定了3个核心功能：智能语音交互升级、自主导航优化、多场景适配能力。产品团队对需求优先级达成一致，预计2月底完成原型开发。",
            key_points=["确定ollo机器人Q1季度3个核心功能", "产品团队对需求优先级达成一致", "预计2月底完成原型开发"],
            attendees=["产品经理", "技术负责人", "UI设计师"]
        ),
        MeetingSummary(
            meeting_id="002",
            meeting_theme="CES展筹备会议",
            meeting_time="2026-01-08 10:00",
            summary="会议讨论了2026年CES展会筹备工作，确定了展位设计方案、产品展示流程和现场互动体验。市场部负责展位搭建，技术部负责产品调试，运营部负责现场活动策划。预计1月15日前完成所有准备工作。",
            key_points=["确定CES展位设计方案", "明确产品展示流程", "预计1月15日前完成准备工作"],
            attendees=["市场部", "技术部", "运营部"]
        ),
        MeetingSummary(
            meeting_id="003",
            meeting_theme="电机参数选型评审会",
            meeting_time="2026-01-12 15:30",
            summary="会议评审了ollo机器人电机选型方案，对比了3款电机型号的性能参数。最终确定采用高扭矩无刷电机，额定转速3000rpm，最大扭矩5Nm。供应商已确认交货周期为4周，预计2月中旬到货。",
            key_points=["确定采用高扭矩无刷电机", "电机参数：3000rpm，5Nm", "预计2月中旬到货"],
            attendees=["硬件工程师", "供应链负责人", "项目经理"]
        ),
        MeetingSummary(
            meeting_id="004",
            meeting_theme="周边UI设计方案讨论会",
            meeting_time="2026-01-09 09:00",
            summary="会议讨论了ollo机器人周边产品的UI设计方案，包括手机APP界面、语音助手界面和Web管理平台。设计团队展示了3套设计稿，最终确定了以简洁科技感为主的设计风格。下周开始详细设计。",
            key_points=["确定简洁科技感设计风格", "涵盖APP、语音助手、Web平台", "下周开始详细设计"],
            attendees=["UI设计师", "产品经理", "前端开发"]
        ),
        MeetingSummary(
            meeting_id="005",
            meeting_theme="ollo机器人技术架构评审",
            meeting_time="2026-01-11 16:00",
            summary="会议评审了ollo机器人的技术架构方案，确定了分层架构设计：感知层、决策层、执行层。讨论了各层之间的通信协议和数据流转方式。技术团队对方案表示认可，计划下周开始详细设计。",
            key_points=["确定感知层、决策层、执行层架构", "明确各层通信协议", "下周开始详细设计"],
            attendees=["架构师", "技术负责人", "开发团队"]
        ),
        MeetingSummary(
            meeting_id="006",
            meeting_theme="CES展会物料准备会",
            meeting_time="2026-01-07 11:00",
            summary="会议审核了CES展会所需的物料清单，包括产品样机、宣传册、展示视频和互动设备。确认了物料制作时间节点：宣传册1月10日前完成，展示视频1月12日前完成，样机调试1月14日前完成。",
            key_points=["确认物料清单", "宣传册1月10日前完成", "样机调试1月14日前完成"],
            attendees=["市场部", "设计部", "技术部"]
        ),
        MeetingSummary(
            meeting_id="007",
            meeting_theme="电机性能测试方案讨论",
            meeting_time="2026-01-13 10:30",
            summary="会议讨论了电机性能测试方案，确定了测试项目：扭矩测试、转速测试、温升测试和寿命测试。测试周期预计2周，测试设备已准备就绪。测试完成后将输出详细的性能报告。",
            key_points=["确定4个测试项目", "测试周期2周", "将输出详细性能报告"],
            attendees=["测试工程师", "硬件工程师", "项目经理"]
        ),
        MeetingSummary(
            meeting_id="008",
            meeting_theme="周边产品用户体验优化会",
            meeting_time="2026-01-14 14:30",
            summary="会议分析了ollo机器人周边产品的用户反馈数据，确定了3个优化方向：简化APP操作流程、提升语音识别准确率、增强个性化推荐功能。设计团队将在本周完成优化方案设计，下周开始开发。",
            key_points=["确定3个优化方向", "本周完成优化方案设计", "下周开始开发"],
            attendees=["产品部", "设计部", "开发部"]
        )
    ]
    
    for summary in default_summaries:
        db.add_summary(summary)
    
    logger.bind(tag=TAG).info(f"初始化默认会议总结完成，共 {len(default_summaries)} 条记录")
