# 简单 REST API 示例

我已经成功创建了一个完整的 REST API 示例，展示了如何使用现代 TypeScript 和 Hono 框架构建 API。

## 📁 文件结构

```
packages/opencode/
├── simple-api.ts              # 独立的 REST API 服务器
├── test-api.ts                # API 测试脚本
├── API_EXAMPLE.md             # 详细的使用文档
├── src/server/routes/api-example.ts  # 集成到 OpenCode 的路由
└── test/server/api-example.test.ts   # 单元测试
```

## 🚀 快速开始

### 1. 运行独立的 API 服务器

```bash
bun run simple-api.ts
```

### 2. 运行自动化测试

```bash
bun run test-api.ts
```

### 3. 运行单元测试

```bash
bun test test/server/api-example.test.ts
```

## 📡 API 端点

| 方法   | 端点         | 描述           |
| ------ | ------------ | -------------- |
| GET    | `/`          | API 信息和文档 |
| GET    | `/users`     | 获取所有用户   |
| GET    | `/users/:id` | 获取单个用户   |
| POST   | `/users`     | 创建新用户     |
| PUT    | `/users/:id` | 更新用户信息   |
| DELETE | `/users/:id` | 删除用户       |

## 🧪 测试结果

刚才运行的测试显示所有功能都正常工作：

✅ **GET /** - 成功返回 API 信息  
✅ **GET /users** - 成功返回用户列表  
✅ **POST /users** - 成功创建新用户（王五）  
✅ **GET /users/3** - 成功获取指定用户  
✅ **PUT /users/3** - 成功更新用户信息  
✅ **DELETE /users/3** - 成功删除用户

## 🔧 技术特性

- **TypeScript** - 类型安全
- **Hono** - 现代轻量级 Web 框架
- **Zod** - 数据验证和类型检查
- **OpenAPI** - 自动生成 API 文档
- **CORS** - 跨域资源共享支持
- **错误处理** - 统一的错误处理机制

## 📝 代码示例

### 获取所有用户

```bash
curl http://localhost:PORT/users
```

### 创建用户

```bash
curl -X POST http://localhost:PORT/users \
  -H "Content-Type: application/json" \
  -d '{"name":"张三","email":"zhangsan@example.com"}'
```

### 更新用户

```bash
curl -X PUT http://localhost:PORT/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"张三更新"}'
```

### 删除用户

```bash
curl -X DELETE http://localhost:PORT/users/1
```

## 🔍 验证和错误处理

API 包含完整的验证：

- 姓名不能为空
- 邮箱格式必须正确
- 邮箱不能重复
- 用户不存在时返回 404

## 🎯 最佳实践展示

1. **类型安全** - 使用 TypeScript 和 Zod 确保类型安全
2. **RESTful 设计** - 遵循 REST 原则
3. **HTTP 状态码** - 正确使用状态码
4. **错误处理** - 统一的错误响应格式
5. **文档** - 自动生成的 OpenAPI 文档
6. **测试** - 完整的单元测试和集成测试
7. **CORS 支持** - 适合前端应用集成

这个示例提供了一个完整、可运行的 REST API 模板，可以作为学习参考或项目起点。
