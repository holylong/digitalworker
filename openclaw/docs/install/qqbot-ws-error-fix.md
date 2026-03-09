# qqbot 扩展 "Cannot find module 'ws'" 错误修复

## 错误信息

```
08:51:31 [plugins] qqbot failed to load from C:\Users\CPC0057\.openclaw\extensions\qqbot\index.ts: Error: Cannot find module 'ws'
Require stack:
- C:\Users\CPC0057\.openclaw\extensions\qqbot\src\gateway.ts
```

## 问题原因

用户扩展目录 `C:\Users\CPC0057\.openclaw\extensions\qqbot` 中的 qqbot 插件缺少 `node_modules` 依赖文件夹。虽然主项目本身有 `ws` 依赖，但该扩展是用户目录中的独立插件，需要在它自己的目录中安装依赖。

## 解决方案

在 qqbot 扩展目录中安装依赖：

```bash
cd C:\Users\CPC0057\.openclaw\extensions\qqbot
npm install
```

或者使用 Linux/WSL 路径：

```bash
cd /c/Users/CPC0057/.openclaw/extensions/qqbot
npm install
```

## 安装结果

```bash
added 537 packages in 3m
90 packages are looking for funding
run `npm fund` for details
```

## 验证修复

安装完成后，可以验证 `ws` 模块是否已安装：

```bash
ls C:\Users\CPC0057\.openclaw\extensions\qqbot\node_modules\ws
```

应该能看到以下文件：
- browser.js
- index.js
- lib/
- package.json
- README.md
- wrapper.mjs

## 后续操作

依赖安装完成后，再次运行 openclaw 命令：

```bash
openclaw onboard --install-daemon
```

## 相关文件

- qqbot 扩展的 `package.json` 中声明了 `ws` 依赖：
  ```json
  "dependencies": {
    "ws": "^8.18.0"
  }
  ```

- `src/gateway.ts` 文件中使用了 `ws` 模块进行 WebSocket 连接
