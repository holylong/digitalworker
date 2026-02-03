"""会议总结数据库测试脚本"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils.meeting_summary_db import MeetingSummary, MeetingSummaryDatabase, init_default_summaries


def test_meeting_summary_db():
    """测试会议总结数据库"""
    print("=" * 60)
    print("会议总结数据库测试")
    print("=" * 60)
    
    # 初始化数据库
    print("\n1. 初始化会议总结数据库...")
    db = MeetingSummaryDatabase("data/test_meeting_summaries.json")
    print(f"   数据库路径: {db.db_path}")
    print(f"   当前记录数: {len(db.summaries)}")
    
    # 初始化默认数据
    print("\n2. 初始化默认会议总结...")
    init_default_summaries()
    print(f"   初始化后记录数: {len(db.summaries)}")
    
    # 查询所有会议总结
    print("\n3. 查询所有会议总结...")
    all_summaries = db.get_all_summaries()
    for i, summary in enumerate(all_summaries, 1):
        print(f"   {i}. {summary.meeting_theme} ({summary.meeting_time})")
    
    # 根据主题查询
    print("\n4. 根据主题查询会议总结...")
    test_themes = ["产品需求", "技术架构", "市场推广", "未知主题"]
    for theme in test_themes:
        summary = db.find_by_theme(theme)
        if summary:
            print(f"   ✓ 找到: {summary.meeting_theme}")
            print(f"     会议时间: {summary.meeting_time}")
            print(f"     会议总结: {summary.summary[:50]}...")
        else:
            print(f"   ✗ 未找到: {theme}")
    
    # 添加新会议总结
    print("\n5. 添加新会议总结...")
    new_summary = MeetingSummary(
        meeting_id="009",
        meeting_theme="测试会议",
        meeting_time="2026-01-15 10:00",
        summary="这是一个测试会议总结",
        key_points=["测试点1", "测试点2"],
        attendees=["测试人员"]
    )
    db.add_summary(new_summary)
    print(f"   添加后记录数: {len(db.summaries)}")
    
    # 根据ID查询
    print("\n6. 根据ID查询会议总结...")
    summary_by_id = db.get_summary_by_id("009")
    if summary_by_id:
        print(f"   ✓ 找到: {summary_by_id.meeting_theme}")
    
    # 删除会议总结
    print("\n7. 删除会议总结...")
    deleted = db.delete_summary("009")
    if deleted:
        print(f"   ✓ 删除成功")
        print(f"   删除后记录数: {len(db.summaries)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_meeting_summary_db()
