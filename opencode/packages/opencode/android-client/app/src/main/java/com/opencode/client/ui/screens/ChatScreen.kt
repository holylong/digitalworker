package com.opencode.client.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.opencode.client.data.model.ChatMessage
import com.opencode.client.ui.viewmodel.ChatViewModel
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    viewModel: ChatViewModel,
    onDisconnect: () -> Unit
) {
    val messages by viewModel.messages.collectAsState()
    val isTyping by viewModel.isTyping.collectAsState()
    val workspaceInfo by viewModel.workspaceInfo.collectAsState()
    val autoCreateProject by viewModel.autoCreateProject.collectAsState()
    val customProjectName by viewModel.customProjectName.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()

    var messageText by remember { mutableStateOf("") }
    var showSettings by remember { mutableStateOf(false) }
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()

    // Auto-scroll to bottom when new messages arrive
    LaunchedEffect(messages.size, isTyping) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("OpenCode Chat")
                        workspaceInfo?.let { info ->
                            Text(
                                text = info.path,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onDisconnect) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Disconnect")
                    }
                },
                actions = {
                    IconButton(onClick = { showSettings = !showSettings }) {
                        Icon(
                            if (showSettings) Icons.Default.ArrowBack else Icons.Default.Settings,
                            contentDescription = if (showSettings) "Hide Settings" else "Show Settings"
                        )
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            if (showSettings) {
                WorkspaceSettingsPanel(
                    autoCreateProject = autoCreateProject,
                    customProjectName = customProjectName,
                    onAutoCreateProjectChange = { viewModel.setAutoCreateProject(it) },
                    onCustomProjectNameChange = { viewModel.setCustomProjectName(it) },
                    modifier = Modifier.fillMaxWidth()
                )
                Divider()
            }

            // Messages list
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(messages) { message ->
                    MessageBubble(message = message)
                }

                if (isTyping) {
                    item {
                        TypingIndicator()
                    }
                }
            }

            // Connection status
            when (connectionState) {
                is com.opencode.client.data.repository.OpenCodeRepository.ConnectionState.Error -> {
                    Surface(
                        color = MaterialTheme.colorScheme.errorContainer,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = (connectionState as com.opencode.client.data.repository.OpenCodeRepository.ConnectionState.Error).message,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.padding(8.dp)
                        )
                    }
                }
                else -> {}
            }

            // Input field
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = messageText,
                    onValueChange = { messageText = it },
                    placeholder = { Text("Enter your message...") },
                    modifier = Modifier.weight(1f),
                    maxLines = 4,
                    shape = RoundedCornerShape(24.dp)
                )

                IconButton(
                    onClick = {
                        if (messageText.isNotBlank()) {
                            viewModel.sendMessage(messageText)
                            messageText = ""
                        }
                    },
                    enabled = messageText.isNotBlank()
                ) {
                    Icon(Icons.Default.Send, contentDescription = "Send")
                }
            }
        }
    }
}

@Composable
fun MessageBubble(message: ChatMessage) {
    val isUser = message is ChatMessage.User
    val isSystem = message is ChatMessage.System

    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Surface(
            color = when {
                isSystem -> MaterialTheme.colorScheme.surfaceVariant
                isUser -> MaterialTheme.colorScheme.primaryContainer
                else -> MaterialTheme.colorScheme.secondaryContainer
            },
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.widthIn(max = 280.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                when (message) {
                    is ChatMessage.User -> {
                        Text(message.text)
                    }
                    is ChatMessage.Assistant -> {
                        if (message.text.isNotEmpty()) {
                            Text(message.text)
                        }
                        message.toolUses.forEach { tool ->
                            Spacer(modifier = Modifier.height(8.dp))
                            ToolUseCard(tool = tool)
                        }
                    }
                    is ChatMessage.System -> {
                        Text(
                            message.text,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ToolUseCard(tool: com.opencode.client.data.model.ToolUseItem) {
    Surface(
        color = MaterialTheme.colorScheme.tertiaryContainer,
        shape = RoundedCornerShape(8.dp)
    ) {
        Column(modifier = Modifier.padding(8.dp)) {
            Text(
                text = "Tool: ${tool.tool}",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold
            )
            if (tool.title.isNotEmpty()) {
                Text(
                    text = tool.title,
                    style = MaterialTheme.typography.bodySmall
                )
            }
            if (tool.output != null) {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = tool.output,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onTertiaryContainer
                )
            }
        }
    }
}

@Composable
fun WorkspaceSettingsPanel(
    autoCreateProject: Boolean,
    customProjectName: String,
    onAutoCreateProjectChange: (Boolean) -> Unit,
    onCustomProjectNameChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        tonalElevation = 2.dp
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "Workspace Settings",
                style = MaterialTheme.typography.titleMedium
            )

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Switch(
                    checked = autoCreateProject,
                    onCheckedChange = onAutoCreateProjectChange
                )
                Text("Auto-create project")
            }

            OutlinedTextField(
                value = customProjectName,
                onValueChange = onCustomProjectNameChange,
                label = { Text("Custom Project Name") },
                placeholder = { Text("Leave empty to auto-generate") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@Composable
fun TypingIndicator() {
    Row(
        modifier = Modifier.padding(16.dp),
        horizontalArrangement = Arrangement.spacedBy(4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(
            color = MaterialTheme.colorScheme.secondaryContainer,
            shape = RoundedCornerShape(12.dp)
        ) {
            Row(modifier = Modifier.padding(12.dp)) {
                val dots = listOf(0, 1, 2)
                dots.forEach { index ->
                    DotAnimation(delay = index * 100)
                }
            }
        }
    }
}

@Composable
fun DotAnimation(delay: Int) {
    var alpha by remember { mutableStateOf(0.3f) }

    LaunchedEffect(Unit) {
        while (true) {
            kotlinx.coroutines.delay(delay.toLong())
            alpha = if (alpha == 1f) 0.3f else 1f
        }
    }

    Surface(
        color = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = alpha),
        shape = RoundedCornerShape(4.dp),
        modifier = Modifier.size(8.dp)
    ) {}
}
