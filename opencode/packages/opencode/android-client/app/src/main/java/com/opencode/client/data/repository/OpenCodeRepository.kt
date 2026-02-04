package com.opencode.client.data.repository

import android.util.Log
import com.opencode.client.data.api.ApiClient
import com.opencode.client.data.api.EventStreamHandler
import com.opencode.client.data.model.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class OpenCodeRepository {

    private val TAG = "OpenCodeRepository"

    private var eventStreamHandler: EventStreamHandler? = null
    private var currentSessionId: String? = null
    private val messageDisplayMap = mutableMapOf<String, String>()

    // Connection state
    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Disconnected)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    // Messages state
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    // Workspace state
    private val _workspaceInfo = MutableStateFlow<WorkspaceInfo?>(null)
    val workspaceInfo: StateFlow<WorkspaceInfo?> = _workspaceInfo.asStateFlow()

    // Typing state
    private val _isTyping = MutableStateFlow(false)
    val isTyping: StateFlow<Boolean> = _isTyping.asStateFlow()

    // Project options
    private val _autoCreateProject = MutableStateFlow(true)
    val autoCreateProject: StateFlow<Boolean> = _autoCreateProject.asStateFlow()

    private val _customProjectName = MutableStateFlow("")
    val customProjectName: StateFlow<String> = _customProjectName.asStateFlow()

    sealed class ConnectionState {
        object Disconnected : ConnectionState()
        object Connecting : ConnectionState()
        data class Connected(val workspace: String) : ConnectionState()
        data class Error(val message: String) : ConnectionState()
    }

    data class WorkspaceInfo(
        val path: String,
        val exists: Boolean
    )

    suspend fun connect(config: ConnectionConfig): Result<HealthResponse> {
        return try {
            _connectionState.value = ConnectionState.Connecting
            ApiClient.setConnectionConfig(config)

            val response = ApiClient.apiService.health()
            if (response.isSuccessful && response.body() != null) {
                val health = response.body()!!
                _connectionState.value = ConnectionState.Connected(health.workspace)
                _workspaceInfo.value = WorkspaceInfo(health.workspace, true)

                // Start SSE stream
                startEventStream(config)

                Result.success(health)
            } else {
                val error = "Connection failed: ${response.code()}"
                _connectionState.value = ConnectionState.Error(error)
                Result.failure(Exception(error))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Connection error", e)
            _connectionState.value = ConnectionState.Error(e.message ?: "Unknown error")
            Result.failure(e)
        }
    }

    private fun startEventStream(config: ConnectionConfig) {
        eventStreamHandler?.disconnect()
        eventStreamHandler = EventStreamHandler(config).apply {
            connect()
        }
    }

    fun disconnect() {
        eventStreamHandler?.disconnect()
        eventStreamHandler = null
        currentSessionId = null
        messageDisplayMap.clear()
        _connectionState.value = ConnectionState.Disconnected
        _messages.value = emptyList()
        _workspaceInfo.value = null
    }

    fun getEventFlow(): Flow<ServerEvent>? {
        return eventStreamHandler?.eventFlow
    }

    suspend fun sendMessage(message: String): Result<RemoteCommandResponse> {
        return try {
            val request = RemoteCommandRequest(
                type = "prompt",
                sessionId = currentSessionId,
                message = message,
                autoCreateProject = _autoCreateProject.value,
                projectName = _customProjectName.value.takeIf { it.isNotEmpty() }
            )

            // Add user message
            addUserMessage(message)

            // Show typing indicator
            _isTyping.value = true

            val response = ApiClient.apiService.execute(
                request = request,
                authorization = ApiClient.apiService.toString().let { null } // Auth handled by interceptor
            )

            if (response.isSuccessful && response.body()?.success == true) {
                val result = response.body()!!
                currentSessionId = result.sessionId

                // Map message ID to display ID
                result.messageId?.let { msgId ->
                    result.sessionId?.let { sessionId ->
                        val displayId = "msg-${System.currentTimeMillis()}"
                        messageDisplayMap["$sessionId:$msgId"] = displayId
                        // Create placeholder for assistant message
                        addAssistantMessage(displayId, "")
                    }
                }

                Result.success(result)
            } else {
                _isTyping.value = false
                Result.failure(Exception(response.body()?.error ?: "Failed to send message"))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Send message error", e)
            _isTyping.value = false
            Result.failure(e)
        }
    }

    fun handleEvent(event: ServerEvent) {
        when (event.type) {
            ServerEvent.MESSAGE_PART_UPDATED -> {
                val part = parseMessagePart(event.properties) ?: return
                handleMessagePartUpdated(part)
            }
            ServerEvent.SESSION_ERROR -> {
                _isTyping.value = false
                addSystemMessage("Error: ${event.properties?.get("error") ?: "Unknown error"}")
            }
            ServerEvent.SESSION_IDLE -> {
                _isTyping.value = false
            }
            ServerEvent.SERVER_CONNECTED -> {
                addSystemMessage("Event stream connected")
            }
        }
    }

    private fun parseMessagePart(properties: Map<String, Any>?): MessagePart? {
        // Simple parsing - in production use proper JSON deserialization
        return null // Placeholder - implement proper parsing based on actual event structure
    }

    private fun handleMessagePartUpdated(part: MessagePart) {
        // Handle text updates
        if (part.type == "text" && part.state?.text != null) {
            part.sessionId?.let { sessionId ->
                updateAssistantMessage(sessionId, part.state.text, part.state.end == true)
            }
        }

        // Handle tool completion
        if (part.type == "tool" && part.state?.status == "completed") {
            part.sessionId?.let { sessionId ->
                addToolUse(sessionId, part.tool ?: "unknown", part.state)
            }
        }

        // Handle step start
        if (part.type == "step-start") {
            _isTyping.value = true
        }
    }

    private fun addUserMessage(text: String) {
        val messages = _messages.value.toMutableList()
        messages.add(ChatMessage.User(
            id = "user-${System.currentTimeMillis()}",
            text = text,
            timestamp = System.currentTimeMillis()
        ))
        _messages.value = messages
    }

    private fun addAssistantMessage(id: String, text: String) {
        val messages = _messages.value.toMutableList()
        val existingIndex = messages.indexOfFirst { it is ChatMessage.Assistant && it.id == id }
        if (existingIndex >= 0) {
            (messages[existingIndex] as ChatMessage.Assistant).let { msg ->
                messages[existingIndex] = msg.copy(text = text)
            }
        } else {
            messages.add(ChatMessage.Assistant(
                id = id,
                text = text,
                timestamp = System.currentTimeMillis()
            ))
        }
        _messages.value = messages
    }

    private fun updateAssistantMessage(id: String, text: String, isComplete: Boolean) {
        addAssistantMessage(id, text)
        if (isComplete) {
            _isTyping.value = false
        }
    }

    private fun addToolUse(sessionId: String, tool: String, state: ToolState) {
        val messages = _messages.value.toMutableList()
        val index = messages.indexOfFirst { it is ChatMessage.Assistant && it.id == sessionId }
        if (index >= 0) {
            val msg = messages[index] as ChatMessage.Assistant
            val toolItem = ToolUseItem(
                tool = tool,
                title = state.title ?: state.input?.toString() ?: tool,
                output = state.output
            )
            messages[index] = msg.copy(toolUses = msg.toolUses + toolItem)
            _messages.value = messages
        }
        _isTyping.value = false
    }

    private fun addSystemMessage(text: String) {
        val messages = _messages.value.toMutableList()
        messages.add(ChatMessage.System(
            id = "system-${System.currentTimeMillis()}",
            text = text,
            timestamp = System.currentTimeMillis()
        ))
        _messages.value = messages
    }

    fun setAutoCreateProject(value: Boolean) {
        _autoCreateProject.value = value
    }

    fun setCustomProjectName(name: String) {
        _customProjectName.value = name
    }

    companion object {
        @Volatile
        private var instance: OpenCodeRepository? = null

        fun getInstance(): OpenCodeRepository {
            return instance ?: synchronized(this) {
                instance ?: OpenCodeRepository().also { instance = it }
            }
        }
    }
}
