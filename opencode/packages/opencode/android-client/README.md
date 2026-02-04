# OpenCode Android Client

Android app to control OpenCode backend for AI-powered coding assistance.

## Features

- **Connect to OpenCode Server**: Connect to any OpenCode remote server
- **Chat Interface**: Send prompts and receive AI responses
- **Real-time Updates**: SSE (Server-Sent Events) for streaming responses
- **Workspace Management**: Auto-create projects and manage workspace
- **Tool Usage Display**: See what tools the AI is using
- **Secure Authentication**: Basic auth support

## Architecture

- **UI**: Jetpack Compose with Material 3
- **Architecture**: MVVM with StateFlow
- **Networking**: Retrofit + OkHttp
- **SSE**: OkHttp EventSource for server-sent events
- **Async**: Kotlin Coroutines

## Project Structure

```
app/src/main/java/com/opencode/client/
├── data/
│   ├── model/          # Data models for API requests/responses
│   ├── api/            # Retrofit API service and SSE handler
│   └── repository/     # Repository pattern for data management
├── ui/
│   ├── screens/        # Compose screens (Connect, Chat)
│   ├── components/     # Reusable UI components
│   ├── viewmodel/      # ViewModels for state management
│   └── theme/          # App theme and colors
└── MainActivity.kt     # Main entry point
```

## Building

### Prerequisites

- Android Studio Hedgehog or later
- JDK 17
- Android SDK 34
- Gradle 8.2

### Build from Android Studio

1. Open the project in Android Studio
2. Wait for Gradle sync to complete
3. Click Run > Run 'app'

### Build from command line

```bash
cd android-client
./gradlew assembleDebug
```

## Usage

1. **Start the OpenCode server**:
   ```bash
   cd packages/opencode
   ./dist/opencode-linux-x64/bin/opencode remote --port 4096
   ```

2. **Launch the Android app**

3. **Enter server details**:
   - Server URL: `http://your-server-ip:4096`
   - Username: `opencode` (or your configured username)
   - Password: (optional, if configured)

4. **Start coding!**

## Configuration

### Workspace Settings

- **Auto-create project**: Automatically creates a new project directory for each session
- **Custom project name**: Specify a project name instead of auto-generation

### Server Configuration

The app connects to OpenCode's remote API endpoints:
- `/remote/health` - Health check
- `/remote/execute` - Execute commands/prompts
- `/event` - SSE event stream

## Troubleshooting

### Connection issues

- Ensure your device/emulator can reach the server
- For emulator, use `http://10.0.2.2:4096` to connect to host machine
- Check firewall settings on the server
- Verify the server is running with `opencode remote`

### Build issues

- Make sure JDK 17 is configured
- Update Android SDK to API 34
- Clear Gradle cache: `./gradlew clean`

## Development

### Adding new features

1. **Data models**: Add to `data/model/`
2. **API endpoints**: Update `OpenCodeApiService`
3. **UI**: Create new screens in `ui/screens/`
4. **State**: Extend `ChatViewModel`

### API Compatibility

This client targets OpenCode Remote API v1.0, compatible with:
- `/remote/health`
- `/remote/execute`
- `/event` SSE stream

## License

Same as OpenCode project.
