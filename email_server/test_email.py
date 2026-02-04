import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 加载环境变量
load_dotenv()

# 获取邮件配置
SEND_EMAIL = os.getenv("SEND_EMAIL", "mrhlingchen@163.com")
RECV_EMAIL = os.getenv("RECV_EMAIL", "707010543@qq.com")
APP_PASSWORD = os.getenv("APP_PASSWORD", "HFjsFcGurTgbcNKp")

print(f"发送邮箱：{SEND_EMAIL}")
print(f"接收邮箱：{RECV_EMAIL}")

# 邮件发送函数
def send_email(subject, content):
    """发送邮件通知"""
    if not SEND_EMAIL or not RECV_EMAIL or not APP_PASSWORD:
        print("⚠️ 邮件配置不完整，无法发送邮件")
        return
    
    try:
        # 邮件内容
        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = Header(SEND_EMAIL, 'utf-8')
        message['To'] = Header(RECV_EMAIL, 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        
        # 连接SMTP服务器并发送邮件
        server = smtplib.SMTP_SSL('smtp.163.com', 465)
        server.login(SEND_EMAIL, APP_PASSWORD)
        server.sendmail(SEND_EMAIL, [RECV_EMAIL], message.as_string())
        server.quit()
        print(f"📧 邮件已发送：{subject} → {RECV_EMAIL}")
    except Exception as e:
        print(f"❌ 邮件发送失败：{str(e)}")

# 测试发送邮件
if __name__ == "__main__":
    print("测试邮件发送功能...")
    send_email("测试邮件", "这是一封测试邮件，用于验证邮件发送功能是否正常工作。")
    print("测试完成！")
