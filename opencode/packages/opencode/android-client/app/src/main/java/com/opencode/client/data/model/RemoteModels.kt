package com.opencode.client.data.model

import com.google.gson.annotations.SerializedName

// API Request Models
data class RemoteCommandRequest(
    @SerializedName("type")
    val type: String, // "command", "prompt", "shell", "status"
    @SerializedName("sessionID")
    val sessionId: String? = null,
    @SerializedName("command")
    val command: String? = null,
    @SerializedName("message")
    val message: String? = null,
    @SerializedName("arguments")
    val arguments: String? = null,
    @SerializedName("agent")
    val agent: String? = null,
    @SerializedName("model")
    val model: String? = null,
    @SerializedName("variant")
    val variant: String? = null,
    @SerializedName("directory")
    val directory: String? = null,
    @SerializedName("projectName")
    val projectName: String? = null,
    @SerializedName("autoCreateProject")
    val autoCreateProject: Boolean = false,
    @SerializedName("files")
    val files: List<FileAttachment>? = null
)

data class FileAttachment(
    @SerializedName("path")
    val path: String,
    @SerializedName("content")
    val content: String? = null
)

// API Response Models
data class RemoteCommandResponse(
    @SerializedName("success")
    val success: Boolean,
    @SerializedName("data")
    val data: MessageData? = null,
    @SerializedName("error")
    val error: String? = null,
    @SerializedName("sessionID")
    val sessionId: String? = null,
    @SerializedName("messageID")
    val messageId: String? = null,
    @SerializedName("workspace")
    val workspace: String? = null,
    @SerializedName("projectDir")
    val projectDir: String? = null
)

data class MessageData(
    @SerializedName("parts")
    val parts: List<MessagePart>? = null
)

data class MessagePart(
    @SerializedName("type")
    val type: String, // "text", "tool", "step-start", etc.
    @SerializedName("text")
    val text: String? = null,
    @SerializedName("tool")
    val tool: String? = null,
    @SerializedName("state")
    val state: ToolState? = null,
    @SerializedName("sessionID")
    val sessionId: String? = null,
    @SerializedName("messageID")
    val messageId: String? = null,
    @SerializedName("id")
    val id: String? = null
)

data class ToolState(
    @SerializedName("status")
    val status: String? = null, // "completed", "running", etc.
    @SerializedName("title")
    val title: String? = null,
    @SerializedName("input")
    val input: Map<String, Any>? = null,
    @SerializedName("output")
    val output: String? = null,
    @SerializedName("text")
    val text: String? = null,
    @SerializedName("end")
    val end: Boolean? = null
)

data class HealthResponse(
    @SerializedName("status")
    val status: String,
    @SerializedName("version")
    val version: String,
    @SerializedName("workspace")
    val workspace: String
)

data class WorkspaceResponse(
    @SerializedName("workspaceRoot")
    val workspaceRoot: String,
    @SerializedName("exists")
    val exists: Boolean
)

data class CommandsListResponse(
    @SerializedName("success")
    val success: Boolean,
    @SerializedName("data")
    val data: List<CommandInfo>
)

data class CommandInfo(
    @SerializedName("name")
    val name: String,
    @SerializedName("description")
    val description: String
)

// SSE Event Models
data class ServerEvent(
    val type: String,
    val properties: Map<String, Any>?
) {
    companion object {
        const val SERVER_CONNECTED = "server.connected"
        const val MESSAGE_PART_UPDATED = "message.part.updated"
        const val SESSION_ERROR = "session.error"
        const val SESSION_IDLE = "session.idle"
    }
}

// UI Models
sealed class ChatMessage {
    abstract val timestamp: Long

    data class User(
        val id: String,
        val text: String,
        override val timestamp: Long
    ) : ChatMessage()

    data class Assistant(
        val id: String,
        val text: String,
        val toolUses: List<ToolUseItem> = emptyList(),
        override val timestamp: Long
    ) : ChatMessage()

    data class System(
        val id: String,
        val text: String,
        override val timestamp: Long
    ) : ChatMessage()
}

data class ToolUseItem(
    val tool: String,
    val title: String,
    val output: String? = null
)

data class ConnectionConfig(
    val serverUrl: String,
    val username: String,
    val password: String,
    val autoConnect: Boolean = false
) {
    fun getAuthHeaders(): Map<String, String> {
        val headers = mutableMapOf<String, String>()
        if (username.isNotEmpty() && password.isNotEmpty()) {
            val auth = android.util.Base64.encodeToString(
                "$username:$password".toByteArray(),
                android.util.Base64.NO_WRAP
            )
            headers["Authorization"] = "Basic $auth"
        }
        return headers
    }
}
