import { Hono } from "hono"
import { describeRoute, validator, resolver } from "hono-openapi"
import z from "zod"
import { HTTPException } from "hono/http-exception"

interface User {
  id: string
  name: string
  email: string
  createdAt: string
}

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

export function UserRoutes() {
  const app = new Hono()

  // GET /api/users - 获取所有用户
  app.get(
    "/",
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

  // GET /api/users/:id - 获取单个用户
  app.get(
    "/:id",
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

  // POST /api/users - 创建新用户
  app.post(
    "/",
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
    validator(
      "json",
      z.object({
        name: z.string().min(1, "姓名不能为空"),
        email: z.string().email("邮箱格式不正确"),
      }),
    ),
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

  // PUT /api/users/:id - 更新用户
  app.put(
    "/:id",
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
    validator(
      "json",
      z.object({
        name: z.string().min(1, "姓名不能为空").optional(),
        email: z.string().email("邮箱格式不正确").optional(),
      }),
    ),
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

  // DELETE /api/users/:id - 删除用户
  app.delete(
    "/:id",
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

  return app
}

// 用户数据模式
const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string(),
  createdAt: z.string(),
})
