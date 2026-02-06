# Claude Code 工具参考

## 可用工具列表

### 文件操作
- **Read** - 读取文件内容
- **Write** - 写入文件（会覆盖现有文件）
- **Edit** - 对文件进行精确的字符串替换
- **Glob** - 使用通配符模式查找文件
- **Grep** - 在文件中搜索内容（支持正则表达式）
- **NotebookEdit** - 编辑 Jupyter notebook 单元格

### 命令执行
- **Bash** - 在终端执行 shell 命令

### 任务管理
- **TodoWrite** - 创建和管理任务列表
- **Task** - 启动专门的子代理处理复杂任务
- **TaskOutput** - 获取后台任务输出
- **KillShell** - 终止后台 shell 进程

### 规划与探索
- **EnterPlanMode** - 进入规划模式设计实现方案
- **ExitPlanMode** - 退出规划并请求批准
- **AskUserQuestion** - 向用户提问获取输入

### AI 能力
- **Skill** - 调用特定技能（如 commit、review-pr 等）
- **mcp__4_5v_mcp__analyze_image** - 分析图片
- **mcp__ide__executeCode** - 执行 Python 代码
- **mcp__ide__getDiagnostics** - 获取语言诊断信息
- **mcp__web_reader__webReader** - 获取网页内容
- **WebSearch** - 网络搜索

### Git 操作
- 通过 Bash 工具执行 git 命令（如 `git status`, `git log`, `git diff` 等）

## 工作原则

- 优先使用专用工具（Read, Edit, Write）而非 bash 命令
- 保持文件简洁，避免不必要的注释
- 不创建新文件除非必须
- 遵循项目的编码规范和约定

---

*生成时间: 2026-02-03*
*OpenClaw 项目文档*
