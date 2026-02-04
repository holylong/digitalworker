import { describe, it, expect } from "bun:test"
import { UserRoutes } from "../../src/server/routes/api-example"

describe("REST API Example", () => {
  const app = UserRoutes()

  describe("GET /api/users", () => {
    it("应该返回所有用户", async () => {
      const res = await app.request("/")
      expect(res.status).toBe(200)

      const data = await res.json()
      expect(Array.isArray(data)).toBe(true)
      expect(data.length).toBeGreaterThan(0)
    })
  })

  describe("GET /api/users/:id", () => {
    it("应该返回指定用户", async () => {
      const res = await app.request("/1")
      expect(res.status).toBe(200)

      const user = await res.json()
      expect(user.id).toBe("1")
      expect(user.name).toBe("张三")
    })

    it("当用户不存在时返回404", async () => {
      const res = await app.request("/999")
      expect(res.status).toBe(404)
    })
  })

  describe("POST /api/users", () => {
    it("应该创建新用户", async () => {
      const newUser = {
        name: "王五",
        email: "wangwu@example.com",
      }

      const res = await app.request("/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newUser),
      })

      expect(res.status).toBe(201)

      const user = await res.json()
      expect(user.name).toBe("王五")
      expect(user.email).toBe("wangwu@example.com")
      expect(user.id).toBeDefined()
      expect(user.createdAt).toBeDefined()
    })

    it("当邮箱格式错误时返回400", async () => {
      const invalidUser = {
        name: "王五",
        email: "invalid-email",
      }

      const res = await app.request("/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(invalidUser),
      })

      expect(res.status).toBe(400)
    })
  })

  describe("PUT /api/users/:id", () => {
    it("应该更新用户信息", async () => {
      const updateData = {
        name: "张三更新",
      }

      const res = await app.request("/1", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updateData),
      })

      expect(res.status).toBe(200)

      const user = await res.json()
      expect(user.name).toBe("张三更新")
      expect(user.email).toBe("zhangsan@example.com") // 保持不变
    })
  })

  describe("DELETE /api/users/:id", () => {
    it("应该删除用户", async () => {
      const res = await app.request("/2", {
        method: "DELETE",
      })

      expect(res.status).toBe(200)

      const result = await res.json()
      expect(result.message).toBe("用户删除成功")
    })

    it("当用户不存在时返回404", async () => {
      const res = await app.request("/999", {
        method: "DELETE",
      })

      expect(res.status).toBe(404)
    })
  })
})
