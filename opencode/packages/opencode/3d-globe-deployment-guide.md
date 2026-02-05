# 3D 地球仪部署说明

## 🌍 项目简介

这是一个使用Three.js实现的3D旋转地球仪，具有以下特性：

- 🎨 精美的3D视觉效果
- 🖱️ 鼠标拖拽旋转和滚轮缩放
- 🌟 星空背景和大气层效果
- 📱 响应式设计，支持移动端触摸操作
- ⚡ 高性能渲染，流畅动画

## 🚀 快速部署方法

### 方法一：GitHub Pages（推荐）

1. **创建GitHub仓库**
   - 访问 https://github.com/new
   - 仓库名称填写：`3d-globe`
   - 设置为Public（公开）
   - 点击"Create repository"

2. **上传文件**
   - 点击"Add file" → "Upload files"
   - 将`index.html`文件拖拽上传
   - 在页面底部填写提交信息："Add 3D globe"
   - 点击"Commit changes"

3. **启用GitHub Pages**
   - 进入仓库的"Settings"选项卡
   - 在左侧菜单找到"Pages"
   - 在"Build and deployment"部分，选择"Deploy from a branch"
   - Branch选择"main"，文件夹选择"/(root)"
   - 点击"Save"

4. **访问网站**
   - 等待1-2分钟部署完成
   - 访问：`https://[你的GitHub用户名].github.io/3d-globe/`

### 方法二：Netlify Drop（最简单）

1. **访问Netlify Drop**
   - 打开 https://app.netlify.com/drop

2. **上传文件**
   - 将整个项目文件夹拖拽到页面中
   - 等待上传完成

3. **获取链接**
   - 自动生成一个公开链接
   - 可以自定义域名

### 方法三：Vercel部署

1. **访问Vercel**
   - 打开 https://vercel.com
   - 使用GitHub登录

2. **导入项目**
   - 点击"New Project"
   - 选择刚才创建的GitHub仓库
   - 点击"Deploy"

## 🎮 功能说明

- **鼠标左键拖拽**：旋转地球
- **滚轮**：缩放视角
- **暂停旋转按钮**：停止/开始自动旋转
- **重置视角按钮**：回到初始位置和角度
- **切换线框按钮**：在线框模式和实体模式间切换
- **移动端支持**：触摸滑动旋转

## 🛠️ 技术栈

- **Three.js**：3D图形库
- **HTML5 Canvas**：渲染引擎
- **CSS3**：现代UI设计
- **JavaScript ES6+**：现代JavaScript特性

## 📱 兼容性

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+
- ✅ 移动端浏览器

## 🎨 自定义

你可以修改以下参数来自定义地球仪：

1. **颜色主题**：修改CSS中的`background`渐变色
2. **旋转速度**：修改JavaScript中的`0.005`值
3. **地球大小**：修改`SphereGeometry(1, 64, 64)`中的参数
4. **星空密度**：修改循环中的`10000`值

## 📄 文件结构

```
3d-globe/
├── index.html          # 主页面文件
└── README.md          # 说明文档
```

只有一个文件！这就是所谓的"单页应用"，部署极其简单。

## 🌟 部署完成后

部署完成后，你将获得一个公开的链接，可以分享给任何人查看。这个3D地球仪展示了现代Web技术的强大能力，完全可以作为个人作品集的一部分或技术演示项目。
