package com.opencode.client

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.opencode.client.ui.screens.ChatScreen
import com.opencode.client.ui.screens.ConnectScreen
import com.opencode.client.ui.theme.OpenCodeTheme
import com.opencode.client.ui.viewmodel.ChatViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            OpenCodeTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    OpenCodeApp()
                }
            }
        }
    }
}

@Composable
fun OpenCodeApp() {
    val viewModel: ChatViewModel = viewModel()
    var isConnected by remember { mutableStateOf(false) }
    val connectionState by viewModel.connectionState.collectAsState()

    // Update connection status based on state
    LaunchedEffect(connectionState) {
        isConnected = connectionState is com.opencode.client.data.repository.OpenCodeRepository.ConnectionState.Connected
    }

    if (isConnected) {
        ChatScreen(
            viewModel = viewModel,
            onDisconnect = {
                viewModel.disconnect()
                isConnected = false
            }
        )
    } else {
        ConnectScreen(
            viewModel = viewModel,
            onConnected = {
                isConnected = true
            }
        )
    }
}
