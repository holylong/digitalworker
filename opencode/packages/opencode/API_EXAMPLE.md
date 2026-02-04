# REST API 示例

这是一个基于 Hono 框架构建的简单 REST API 示例，展示了基本的 CRUD 操作。

## API 端点

基础 URL: `http://localhost:4096/api/users`

### 1. 获取所有用户

- **GET** `/api/users`
- **响应示例**:

```json
[
  {
    "id": "1",
    "name": "张三",
    "email": "zhangsan@example.com",
    "createdAt": "2024-01-01T00:00:00.000Z"
  }
]
```

### 2. 获取单个用户

- **GET** `/api/users/:id`
- **响应示例**:

```json
{
  "id": "1",
  "name": "张三",
  "email": "zhangsan@example.com",
  "createdAt": "2024-01-01T00:00:00.000Z"
}
```

### 3. 创建用户

- **POST** `/api/users`
- **请求体**:

```json
{
  "name": "王五",
  "email": "wangwu@example.com"
}
```

- **响应**: 201 Created + 新创建的用户对象

### 4. 更新用户

- **PUT** `/api/users/:id`
- **请求体**:

```json
{
  "name": "王五更新",
  "email": "wangwu-updated@example.com"
}
```

- **响应**: 200 OK + 更新后的用户对象

### 5. 删除用户

- **DELETE** `/api/users/:id`
- **响应示例**:

```json
{
  "message": "用户删除成功"
}
```

## 使用方法

### 启动服务器

```bash
bun run dev
```

### 测试 API

#### 使用 curl

```bash
# 获取所有用户
curl http://localhost:4096/api/users

# 创建用户
curl -X POST http://localhost:4096/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","email":"test@example.com"}'

# 获取指定用户
curl http://localhost:4096/api/users/1

# 更新用户
curl -X PUT http://localhost:4096/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"更新的名字"}'

# 删除用户
curl -X DELETE http://localhost:4096/api/users/1
```

#### 使用 HTTP 客户端 (如 Postman, Insomnia)

- 设置基础 URL: `http://localhost:4096`
- 使用相应的 HTTP 方法和端点路径

## 特性

- ✅ 类型安全的请求/响应验证 (使用 Zod)
- ✅ OpenAPI 文档自动生成
- ✅ 错误处理和 HTTP 状态码
- ✅ 单元测试覆盖
- ✅ CORS 支持
- ✅ 基础认证支持 (可配置)

## 错误处理

API 返回标准的 HTTP 状态码：

- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

错误响应格式：

```json
{
  "name": "ErrorName",
  "message": "错误描述"
}
```

## 扩展

要添加更多的 API 端点：

1. 在 `src/server/routes/` 目录下创建新的路由文件
2. 在 `src/server/server.ts` 中注册新路由
3. 为新端点编写测试
4. 更新 OpenAPI 文档

## 测试

运行测试：

```bash
bun test test/server/api-example.test.ts
```

运行所有测试：

```bash
bun test
```

## API 文档

启动服务器后访问以下地址查看完整的 API 文档：

```
http://localhost:4096/doc
```

这将显示由 Hono OpenAPI 自动生成的交互式 API 文档。
