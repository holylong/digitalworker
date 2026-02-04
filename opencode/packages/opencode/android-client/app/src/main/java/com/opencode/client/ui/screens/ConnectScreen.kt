package com.opencode.client.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.opencode.client.ui.viewmodel.ChatViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConnectScreen(
    viewModel: ChatViewModel,
    onConnected: () -> Unit
) {
    var serverUrl by remember { mutableStateOf(viewModel.serverUrl.value) }
    var username by remember { mutableStateOf(viewModel.username.value) }
    var password by remember { mutableStateOf(viewModel.password.value) }
    val isLoading by viewModel.isLoading.collectAsState()

    // Update connection state
    val connectionState by viewModel.connectionState.collectAsState()
    LaunchedEffect(connectionState) {
        if (connectionState is com.opencode.client.data.repository.OpenCodeRepository.ConnectionState.Connected) {
            onConnected()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
        ) {
            Column(
                modifier = Modifier.padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "OpenCode",
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.primary
                )

                Text(
                    text = "Connect to OpenCode Server",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Divider()

                OutlinedTextField(
                    value = serverUrl,
                    onValueChange = {
                        serverUrl = it
                        viewModel.updateServerUrl(it)
                    },
                    label = { Text("Server URL") },
                    placeholder = { Text("http://localhost:4096") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri)
                )

                OutlinedTextField(
                    value = username,
                    onValueChange = {
                        username = it
                        viewModel.updateUsername(it)
                    },
                    label = { Text("Username") },
                    placeholder = { Text("opencode") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = password,
                    onValueChange = {
                        password = it
                        viewModel.updatePassword(it)
                    },
                    label = { Text("Password (Optional)") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth()
                )

                when (val state = connectionState) {
                    is com.opencode.client.data.repository.OpenCodeRepository.ConnectionState.Error -> {
                        Text(
                            text = state.message,
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                    else -> {}
                }

                Button(
                    onClick = { viewModel.connect() },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !isLoading && serverUrl.isNotBlank()
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            color = MaterialTheme.colorScheme.onPrimary,
                            strokeWidth = 2.dp
                        )
                    } else {
                        Text("Connect")
                    }
                }
            }
        }
    }
}
