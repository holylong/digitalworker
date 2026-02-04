package com.opencode.client.ui.viewmodel

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.opencode.client.data.model.*
import com.opencode.client.data.repository.OpenCodeRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

class ChatViewModel(
    private val repository: OpenCodeRepository = OpenCodeRepository.getInstance()
) : ViewModel() {

    private val TAG = "ChatViewModel"

    // Connection config
    private val _serverUrl = MutableStateFlow("http://10.184.60.127:4096")
    val serverUrl: StateFlow<String> = _serverUrl.asStateFlow()

    private val _username = MutableStateFlow("opencode")
    val username: StateFlow<String> = _username.asStateFlow()

    private val _password = MutableStateFlow("")
    val password: StateFlow<String> = _password.asStateFlow()

    // UI States
    val connectionState: StateFlow<OpenCodeRepository.ConnectionState> =
        repository.connectionState

    val messages: StateFlow<List<ChatMessage>> = repository.messages

    val workspaceInfo: StateFlow<OpenCodeRepository.WorkspaceInfo?> = repository.workspaceInfo

    val isTyping: StateFlow<Boolean> = repository.isTyping

    val autoCreateProject: StateFlow<Boolean> = repository.autoCreateProject

    val customProjectName: StateFlow<String> = repository.customProjectName

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        // Start collecting events from SSE
        viewModelScope.launch {
            repository.getEventFlow()?.collect { event ->
                repository.handleEvent(event)
            }
        }
    }

    fun updateServerUrl(url: String) {
        _serverUrl.value = url
    }

    fun updateUsername(username: String) {
        _username.value = username
    }

    fun updatePassword(password: String) {
        _password.value = password
    }

    fun connect() {
        viewModelScope.launch {
            _isLoading.value = true
            val config = ConnectionConfig(
                serverUrl = _serverUrl.value,
                username = _username.value,
                password = _password.value
            )
            repository.connect(config)
                .onSuccess { health ->
                    Log.d(TAG, "Connected successfully: ${health.workspace}")
                }
                .onFailure { error ->
                    Log.e(TAG, "Connection failed", error)
                }
            _isLoading.value = false
        }
    }

    fun disconnect() {
        repository.disconnect()
    }

    fun sendMessage(message: String) {
        if (message.isBlank()) return

        viewModelScope.launch {
            repository.sendMessage(message)
                .onFailure { error ->
                    Log.e(TAG, "Failed to send message", error)
                }
        }
    }

    fun setAutoCreateProject(value: Boolean) {
        repository.setAutoCreateProject(value)
    }

    fun setCustomProjectName(name: String) {
        repository.setCustomProjectName(name)
    }

    override fun onCleared() {
        super.onCleared()
        repository.disconnect()
    }
}
