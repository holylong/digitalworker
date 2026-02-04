import os
import sqlite3
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from flask import Flask, request, jsonify, render_template_string

# 加载环境变量
load_dotenv()

# 获取邮件配置
SEND_EMAIL = os.getenv("SEND_EMAIL", "mrhlingchen@163.com")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

# 初始化Flask应用
app = Flask(__name__)

# 数据库初始化
conn = sqlite3.connect('contacts.db', check_same_thread=False)
cursor = conn.cursor()

# 创建联系人表
cursor.execute('''
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    position TEXT,
    english_name TEXT,
    email TEXT NOT NULL UNIQUE,
    phone TEXT
)
''')
conn.commit()

# 邮件发送函数
def send_email(to_email, subject, content):
    """发送邮件通知"""
    if not SEND_EMAIL or not to_email or not APP_PASSWORD:
        return False, "邮件配置不完整或收件人地址为空"
    
    try:
        # 邮件内容
        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = Header(SEND_EMAIL, 'utf-8')
        message['To'] = Header(to_email, 'utf-8')
        message['Subject'] = Header(subject, 'utf-8')
        
        # 连接SMTP服务器并发送邮件
        server = smtplib.SMTP_SSL('smtp.163.com', 465)
        server.login(SEND_EMAIL, APP_PASSWORD)
        server.sendmail(SEND_EMAIL, [to_email], message.as_string())
        server.quit()
        return True, f"邮件已成功发送到 {to_email}"
    except Exception as e:
        return False, f"邮件发送失败：{str(e)}"

# RESTful API端点
@app.route('/api/email', methods=['POST'])
def api_send_email():
    """通过REST API发送邮件"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必填字段
        if not data:
            return jsonify({"code": 400, "message": "请求体不能为空"}), 400
        
        to_email = data.get('to')
        subject = data.get('subject')
        content = data.get('content')
        
        if not to_email:
            return jsonify({"code": 400, "message": "缺少必填字段：to"}), 400
        
        if not subject:
            return jsonify({"code": 400, "message": "缺少必填字段：subject"}), 400
        
        if not content:
            return jsonify({"code": 400, "message": "缺少必填字段：content"}), 400
        
        # 发送邮件
        success, message = send_email(to_email, subject, content)
        
        if success:
            return jsonify({"code": 200, "message": message}), 200
        else:
            return jsonify({"code": 500, "message": message}), 500
            
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器内部错误：{str(e)}"}), 500

# 联系人管理API

@app.route('/api/contacts', methods=['POST'])
def add_contact():
    """添加联系人"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求体不能为空"}), 400
        
        name = data.get('name')
        email = data.get('email')
        position = data.get('position', '')
        english_name = data.get('english_name', '')
        phone = data.get('phone', '')
        
        if not name:
            return jsonify({"code": 400, "message": "缺少必填字段：name"}), 400
        if not email:
            return jsonify({"code": 400, "message": "缺少必填字段：email"}), 400
        
        cursor.execute('''
        INSERT INTO contacts (name, position, english_name, email, phone)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, position, english_name, email, phone))
        conn.commit()
        
        return jsonify({"code": 200, "message": "联系人添加成功"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"code": 400, "message": "邮箱已存在"}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器内部错误：{str(e)}"}), 500

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """获取所有联系人列表"""
    try:
        name = request.args.get('name')
        if name:
            cursor.execute('SELECT * FROM contacts WHERE name LIKE ?', (f'%{name}%',))
        else:
            cursor.execute('SELECT * FROM contacts')
        
        contacts = cursor.fetchall()
        result = []
        for contact in contacts:
            result.append({
                "id": contact[0],
                "name": contact[1],
                "position": contact[2],
                "english_name": contact[3],
                "email": contact[4],
                "phone": contact[5]
            })
        
        return jsonify({"code": 200, "data": result}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器内部错误：{str(e)}"}), 500

@app.route('/api/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """根据ID获取联系人"""
    try:
        cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
        contact = cursor.fetchone()
        if not contact:
            return jsonify({"code": 404, "message": "联系人不存在"}), 404
        
        result = {
            "id": contact[0],
            "name": contact[1],
            "position": contact[2],
            "english_name": contact[3],
            "email": contact[4],
            "phone": contact[5]
        }
        
        return jsonify({"code": 200, "data": result}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器内部错误：{str(e)}"}), 500

@app.route('/api/contacts/email/<name>', methods=['GET'])
def get_email_by_name(name):
    """根据姓名获取邮箱，先比对中文再比对英文"""
    try:
        # 先根据中文姓名查询
        cursor.execute('SELECT email FROM contacts WHERE name LIKE ?', (f'%{name}%',))
        contacts = cursor.fetchall()
        
        # 如果没有找到，再根据英文名查询
        if not contacts:
            cursor.execute('SELECT email FROM contacts WHERE english_name LIKE ?', (f'%{name}%',))
            contacts = cursor.fetchall()
        
        if not contacts:
            return jsonify({"code": 404, "message": "未找到匹配的联系人"}), 404
        
        emails = [contact[0] for contact in contacts]
        return jsonify({"code": 200, "data": emails}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器内部错误：{str(e)}"}), 500

@app.route('/api/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """更新联系人信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求体不能为空"}), 400
        
        # 检查联系人是否存在
        cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
        contact = cursor.fetchone()
        if not contact:
            return jsonify({"code": 404, "message": "联系人不存在"}), 404
        
        # 更新联系人信息
        name = data.get('name', contact[1])
        position = data.get('position', contact[2])
        english_name = data.get('english_name', contact[3])
        email = data.get('email', contact[4])
        phone = data.get('phone', contact[5])
        
        # 验证必填字段
        if not name:
            return jsonify({"code": 400, "message": "姓名不能为空"}), 400
        if not email:
            return jsonify({"code": 400, "message": "邮箱不能为空"}), 400
        
        cursor.execute('''
        UPDATE contacts 
        SET name = ?, position = ?, english_name = ?, email = ?, phone = ?
        WHERE id = ?
        ''', (name, position, english_name, email, phone, contact_id))
        conn.commit()
        
        return jsonify({"code": 200, "message": "联系人信息更新成功"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"code": 400, "message": "邮箱已存在"}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器内部错误：{str(e)}"}), 500

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """删除联系人"""
    try:
        # 检查联系人是否存在
        cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
        contact = cursor.fetchone()
        if not contact:
            return jsonify({"code": 404, "message": "联系人不存在"}), 404
        
        # 删除联系人
        cursor.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
        conn.commit()
        
        return jsonify({"code": 200, "message": "联系人删除成功"}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器内部错误：{str(e)}"}), 500

# 批量发送邮件接口
@app.route('/api/email/batch', methods=['POST'])
def batch_send_email():
    """批量发送邮件"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求体不能为空"}), 400
        
        to_emails = data.get('to')
        subject = data.get('subject')
        content = data.get('content')
        
        if not to_emails or not isinstance(to_emails, list):
            return jsonify({"code": 400, "message": "缺少必填字段：to（必须是邮箱列表）"}), 400
        if not subject:
            return jsonify({"code": 400, "message": "缺少必填字段：subject"}), 400
        if not content:
            return jsonify({"code": 400, "message": "缺少必填字段：content"}), 400
        
        results = []
        for email in to_emails:
            success, message = send_email(email, subject, content)
            results.append({"email": email, "success": success, "message": message})
        
        return jsonify({"code": 200, "data": results}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器内部错误：{str(e)}"}), 500

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    """服务器健康检查"""
    return jsonify({"code": 200, "message": "服务器运行正常"}), 200

# Web UI页面
@app.route('/')
def index():
    """联系人管理Web UI"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>联系人管理系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        h1 {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            font-size: 2.5em;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            padding: 30px;
            margin-bottom: 25px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
        }
        h2 {
            color: #2d3748;
            margin-bottom: 25px;
            font-size: 1.8em;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        h2::before {
            content: '';
            width: 4px;
            height: 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-row {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .form-row .form-group {
            flex: 1;
            min-width: 250px;
            margin-bottom: 0;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4a5568;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        input {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 15px;
            transition: all 0.3s ease;
            background-color: #f7fafc;
            color: #2d3748;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
            background-color: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button {
            width: 100%;
            padding: 14px 24px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        button:not(.secondary) {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        button:not(.secondary):hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        }
        button.secondary {
            background-color: #edf2f7;
            color: #4a5568;
            border: 2px solid #e2e8f0;
        }
        button.secondary:hover {
            background-color: #e2e8f0;
            border-color: #cbd5e0;
            transform: translateY(-2px);
        }
        .table-container {
            overflow-x: auto;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }
        th, td {
            padding: 16px 20px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 13px;
        }
        tr {
            transition: all 0.3s ease;
        }
        tr:hover {
            background-color: #f7fafc;
            transform: scale(1.01);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        tr:last-child td {
            border-bottom: none;
        }
        .message {
            padding: 16px 20px;
            border-radius: 8px;
            margin-top: 20px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        .message.success {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
        }
        .message.error {
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            color: white;
        }
        .search-container {
            margin-bottom: 25px;
            display: flex;
            gap: 12px;
            align-items: stretch;
            flex-wrap: wrap;
        }
        .search-container input {
            flex: 1;
            min-width: 200px;
        }
        .search-container button {
            min-width: 100px;
            flex: 0 0 auto;
        }
        /* 响应式设计 */
        @media (max-width: 768px) {
            .form-row {
                flex-direction: column;
            }
            .form-row .form-group {
                min-width: 100%;
            }
            .search-container {
                flex-direction: column;
                align-items: stretch;
            }
            .search-container input {
                min-width: 100%;
            }
            .search-container button {
                min-width: 100%;
                flex: 1;
            }
            h1 {
                font-size: 2em;
            }
            .card {
                padding: 20px;
            }
        }
        /* 动画效果 */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .card {
            animation: fadeIn 0.6s ease-out;
        }
        .card:nth-child(2) {
            animation-delay: 0.1s;
        }
        .card:nth-child(3) {
            animation-delay: 0.2s;
        }
        .card:nth-child(4) {
            animation-delay: 0.3s;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>联系人管理系统</h1>
        
        <!-- 添加联系人卡片 -->
        <div class="card">
            <h2>添加联系人</h2>
            <form id="addContactForm">
                <div class="form-row">
                    <div class="form-group">
                        <label for="name">姓名 *</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="englishName">英文名</label>
                        <input type="text" id="englishName" name="englishName">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="position">职位</label>
                        <input type="text" id="position" name="position">
                    </div>
                    <div class="form-group">
                        <label for="email">邮箱 *</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="phone">电话</label>
                    <input type="tel" id="phone" name="phone">
                </div>
                <button type="submit">添加联系人</button>
            </form>
            <div id="addMessage"></div>
        </div>
        
        <!-- 搜索联系人卡片 -->
        <div class="card">
            <h2>搜索联系人</h2>
            <div class="search-container">
                <input type="text" id="searchName" placeholder="输入姓名搜索">
                <button id="searchBtn" class="secondary">搜索</button>
                <button id="clearSearchBtn" class="secondary">清除</button>
            </div>
        </div>
        
        <!-- 联系人列表卡片 -->
        <div class="card">
            <h2>联系人列表</h2>
            <div class="table-container">
                <table id="contactsTable">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>姓名</th>
                            <th>职位</th>
                            <th>英文名</th>
                            <th>邮箱</th>
                            <th>电话</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- 联系人数据将通过JavaScript动态添加 -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        // 页面加载时获取所有联系人
        document.addEventListener('DOMContentLoaded', function() {
            fetchContacts();
        });
        
        // 获取联系人列表
        function fetchContacts(name = '') {
            let url = '/api/contacts';
            if (name) {
                url += `?name=${encodeURIComponent(name)}`;
            }
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.code === 200) {
                        renderContacts(data.data);
                    }
                })
                .catch(error => console.error('Error fetching contacts:', error));
        }
        
        // 渲染联系人列表
        function renderContacts(contacts) {
            const tbody = document.querySelector('#contactsTable tbody');
            tbody.innerHTML = '';
            
            contacts.forEach(contact => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${contact.id}</td>
                    <td>${contact.name}</td>
                    <td>${contact.position || '-'}</td>
                    <td>${contact.english_name || '-'}</td>
                    <td>${contact.email}</td>
                    <td>${contact.phone || '-'}</td>
                    <td>
                        <button class="edit-btn" data-id="${contact.id}" style="width: auto; min-width: 80px; margin-right: 8px; background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);">编辑</button>
                        <button class="delete-btn" data-id="${contact.id}" style="width: auto; min-width: 80px; background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);">删除</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
            
            // 添加编辑按钮事件监听器
            document.querySelectorAll('.edit-btn').forEach(btn => {
                btn.addEventListener('click', editContact);
            });
            
            // 添加删除按钮事件监听器
            document.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', deleteContact);
            });
        }
        
        // 编辑联系人
        function editContact(e) {
            const contactId = e.target.dataset.id;
            fetch(`/api/contacts/${contactId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.code === 200) {
                        const contact = data.data;
                        const form = document.querySelector('#addContactForm');
                        
                        // 填充表单数据
                        form.querySelector('#name').value = contact.name;
                        form.querySelector('#position').value = contact.position || '';
                        form.querySelector('#englishName').value = contact.english_name || '';
                        form.querySelector('#email').value = contact.email;
                        form.querySelector('#phone').value = contact.phone || '';
                        
                        // 保存联系人ID到表单
                        form.dataset.contactId = contactId;
                        
                        // 更改表单标题
                        form.parentElement.querySelector('h2').textContent = '编辑联系人';
                        
                        // 滚动到表单顶部
                        form.scrollIntoView({ behavior: 'smooth' });
                    }
                })
                .catch(error => console.error('Error fetching contact:', error));
        }
        
        // 删除联系人
        function deleteContact(e) {
            const contactId = e.target.dataset.id;
            if (confirm('确定要删除这个联系人吗？')) {
                fetch(`/api/contacts/${contactId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    const messageDiv = document.querySelector('#addMessage');
                    if (data.code === 200) {
                        messageDiv.className = 'message success';
                        messageDiv.textContent = '联系人删除成功';
                        fetchContacts();
                    } else {
                        messageDiv.className = 'message error';
                        messageDiv.textContent = data.message;
                    }
                    
                    // 3秒后清除消息
                    setTimeout(() => {
                        messageDiv.textContent = '';
                        messageDiv.className = 'message';
                    }, 3000);
                })
                .catch(error => {
                    const messageDiv = document.querySelector('#addMessage');
                    messageDiv.className = 'message error';
                    messageDiv.textContent = '删除失败：' + error.message;
                });
            }
        }
        
        // 添加联系人表单提交
        document.querySelector('#addContactForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const contactData = {
                name: formData.get('name'),
                position: formData.get('position'),
                english_name: formData.get('englishName'),
                email: formData.get('email'),
                phone: formData.get('phone')
            };
            
            const contactId = this.dataset.contactId;
            const url = contactId ? `/api/contacts/${contactId}` : '/api/contacts';
            const method = contactId ? 'PUT' : 'POST';
            
            fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(contactData)
            })
            .then(response => response.json())
            .then(data => {
                const messageDiv = document.querySelector('#addMessage');
                messageDiv.className = `message ${data.code === 200 ? 'success' : 'error'}`;
                messageDiv.textContent = data.message;
                
                if (data.code === 200) {
                    this.reset();
                    // 重置表单状态
                    delete this.dataset.contactId;
                    this.parentElement.querySelector('h2').textContent = '添加联系人';
                    fetchContacts();
                }
                
                // 3秒后清除消息
                setTimeout(() => {
                    messageDiv.textContent = '';
                    messageDiv.className = 'message';
                }, 3000);
            })
            .catch(error => {
                const messageDiv = document.querySelector('#addMessage');
                messageDiv.className = 'message error';
                messageDiv.textContent = (this.dataset.contactId ? '编辑' : '添加') + '失败：' + error.message;
            });
        });
        
        // 搜索按钮点击事件
        document.querySelector('#searchBtn').addEventListener('click', function() {
            const name = document.querySelector('#searchName').value;
            fetchContacts(name);
        });
        
        // 清除搜索按钮点击事件
        document.querySelector('#clearSearchBtn').addEventListener('click', function() {
            document.querySelector('#searchName').value = '';
            fetchContacts();
        });
        
        // 搜索框回车键事件
        document.querySelector('#searchName').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const name = this.value;
                fetchContacts(name);
            }
        });
    </script>
</body>
</html>
    ''')

if __name__ == "__main__":
    # 获取端口配置，默认使用5000
    port = int(os.getenv("PORT", 5000))
    print(f"📧 邮件发送RESTful服务器启动中...")
    print(f"📍 监听地址：http://0.0.0.0:{port}")
    print(f"📖 API文档：")
    print(f"   POST /api/email - 发送邮件")
    print(f"   POST /api/email/batch - 批量发送邮件")
    print(f"   GET /api/contacts - 获取联系人列表")
    print(f"   POST /api/contacts - 添加联系人")
    print(f"   GET /api/contacts/<id> - 获取单个联系人")
    print(f"   GET /api/contacts/email/<name> - 根据姓名获取邮箱")
    print(f"   GET /health - 健康检查")
    print(f"   GET / - Web UI界面")
    print(f"\n🔧 配置信息：")
    print(f"   发送邮箱：{SEND_EMAIL}")
    print(f"\n🚀 服务器已启动，等待请求...")
    app.run(host='0.0.0.0', port=port, debug=True)
