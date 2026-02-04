import { Hono } from "hono"
import { cors } from "hono/cors"
import { describeRoute, validator, resolver } from "hono-openapi"
import z from "zod"
import { HTTPException } from "hono/http-exception"

interface User {
  id: string
  name: string
  email: string
  createdAt: string
}

// 内存数据存储
const users: User[] = [
  {
    id: "1",
    name: "张三",
    email: "zhangsan@example.com",
    createdAt: new Date().toISOString(),
  },
  {
    id: "2",
    name: "李四",
    email: "lisi@example.com",
    createdAt: new Date().toISOString(),
  },
]

// 创建 Hono 应用
const app = new Hono()

// 添加 CORS 支持
app.use(
  "*",
  cors({
    origin: ["http://localhost:3000", "http://localhost:4096", "*"],
    allowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization"],
  }),
)

// 请求日志中间件
app.use("*", async (c, next) => {
  console.log(`${c.req.method} ${c.req.path}`)
  await next()
})

// 错误处理中间件
app.onError((err, c) => {
  console.error("Error:", err)
  if (err instanceof HTTPException) {
    return c.json({ error: err.message, status: err.status }, err.status)
  }
  return c.json({ error: "Internal Server Error" }, 500)
})

// 用户数据模式
const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string(),
  createdAt: z.string(),
})

const CreateUserSchema = z.object({
  name: z.string().min(1, "姓名不能为空"),
  email: z.string().email("邮箱格式不正确"),
})

const UpdateUserSchema = z.object({
  name: z.string().min(1, "姓名不能为空").optional(),
  email: z.string().email("邮箱格式不正确").optional(),
})

// GET / - 根路径
app.get("/", (c) => {
  return c.json({
    message: "简单 REST API 示例",
    version: "1.0.0",
    endpoints: {
      "GET /": "API 信息",
      "GET /users": "获取所有用户",
      "GET /users/:id": "获取单个用户",
      "POST /users": "创建用户",
      "PUT /users/:id": "更新用户",
      "DELETE /users/:id": "删除用户",
    },
  })
})

// GET /users - 获取所有用户
app.get(
  "/users",
  describeRoute({
    summary: "获取所有用户",
    description: "返回用户列表",
    operationId: "users.list",
    responses: {
      200: {
        description: "用户列表",
        content: {
          "application/json": {
            schema: resolver(z.array(UserSchema)),
          },
        },
      },
    },
  }),
  async (c) => {
    return c.json(users)
  },
)

// GET /users/:id - 获取单个用户
app.get(
  "/users/:id",
  describeRoute({
    summary: "获取单个用户",
    description: "根据ID获取用户信息",
    operationId: "users.get",
    responses: {
      200: {
        description: "用户信息",
        content: {
          "application/json": {
            schema: resolver(UserSchema),
          },
        },
      },
      404: {
        description: "用户不存在",
      },
    },
  }),
  validator(
    "param",
    z.object({
      id: z.string(),
    }),
  ),
  async (c) => {
    const { id } = c.req.valid("param")
    const user = users.find((u) => u.id === id)

    if (!user) {
      throw new HTTPException(404, { message: "用户不存在" })
    }

    return c.json(user)
  },
)

// POST /users - 创建新用户
app.post(
  "/users",
  describeRoute({
    summary: "创建用户",
    description: "创建新用户",
    operationId: "users.create",
    responses: {
      201: {
        description: "创建成功",
        content: {
          "application/json": {
            schema: resolver(UserSchema),
          },
        },
      },
      400: {
        description: "请求参数错误",
      },
    },
  }),
  validator("json", CreateUserSchema),
  async (c) => {
    const { name, email } = c.req.valid("json")

    // 检查邮箱是否已存在
    if (users.some((u) => u.email === email)) {
      throw new HTTPException(400, { message: "邮箱已存在" })
    }

    const newUser: User = {
      id: (users.length + 1).toString(),
      name,
      email,
      createdAt: new Date().toISOString(),
    }

    users.push(newUser)

    return c.json(newUser, 201)
  },
)

// PUT /users/:id - 更新用户
app.put(
  "/users/:id",
  describeRoute({
    summary: "更新用户",
    description: "更新用户信息",
    operationId: "users.update",
    responses: {
      200: {
        description: "更新成功",
        content: {
          "application/json": {
            schema: resolver(UserSchema),
          },
        },
      },
      404: {
        description: "用户不存在",
      },
      400: {
        description: "请求参数错误",
      },
    },
  }),
  validator(
    "param",
    z.object({
      id: z.string(),
    }),
  ),
  validator("json", UpdateUserSchema),
  async (c) => {
    const { id } = c.req.valid("param")
    const updates = c.req.valid("json")

    const userIndex = users.findIndex((u) => u.id === id)
    if (userIndex === -1) {
      throw new HTTPException(404, { message: "用户不存在" })
    }

    // 如果更新邮箱，检查是否已存在
    if (updates.email && users.some((u) => u.email === updates.email && u.id !== id)) {
      throw new HTTPException(400, { message: "邮箱已存在" })
    }

    users[userIndex] = { ...users[userIndex], ...updates }

    return c.json(users[userIndex])
  },
)

// DELETE /users/:id - 删除用户
app.delete(
  "/users/:id",
  describeRoute({
    summary: "删除用户",
    description: "根据ID删除用户",
    operationId: "users.delete",
    responses: {
      200: {
        description: "删除成功",
        content: {
          "application/json": {
            schema: resolver(z.object({ message: z.string() })),
          },
        },
      },
      404: {
        description: "用户不存在",
      },
    },
  }),
  validator(
    "param",
    z.object({
      id: z.string(),
    }),
  ),
  async (c) => {
    const { id } = c.req.valid("param")

    const userIndex = users.findIndex((u) => u.id === id)
    if (userIndex === -1) {
      throw new HTTPException(404, { message: "用户不存在" })
    }

    users.splice(userIndex, 1)

    return c.json({ message: "用户删除成功" })
  },
)

// 启动服务器
const port = 0 // 0 表示使用随机可用端口
console.log(`🚀 服务器启动在 http://localhost:${port}`)
console.log("📚 API 文档: http://localhost:3000/doc")
console.log("")
console.log("可用的 API 端点:")
console.log("  GET  /           - API 信息")
console.log("  GET  /users      - 获取所有用户")
console.log("  GET  /users/:id  - 获取单个用户")
console.log("  POST /users      - 创建用户")
console.log("  PUT  /users/:id  - 更新用户")
console.log("  DELETE /users/:id - 删除用户")
console.log("")

export default {
  fetch: app.fetch,
  port,
}

// 开发模式直接启动
if (import.meta.main) {
  const server = Bun.serve({
    port,
    fetch: app.fetch,
  })

  console.log(`🎯 服务器正在监听 http://localhost:${server.port}`)
}
