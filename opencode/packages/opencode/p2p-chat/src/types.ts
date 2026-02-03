import { z } from "zod"

export const MessageSchema = z.object({
  type: z.enum(["discovery", "chat", "user-list"]),
  username: z.string(),
  port: z.number(),
  timestamp: z.number(),
  data: z.optional(z.any()),
})

export type Message = z.infer<typeof MessageSchema>

export const BROADCAST_PORT = 30000
export const CHAT_PORT = 30001
export const BROADCAST_INTERVAL = 5000

export interface Peer {
  username: string
  address: string
  port: number
  lastSeen: number
}
