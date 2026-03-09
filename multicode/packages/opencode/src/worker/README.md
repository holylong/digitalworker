# Distributed Worker System

This module enables cross-platform compilation and testing by distributing work to remote worker nodes.

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Linux (Master)                              │
│                                                                 │
│  AI: 写代码 ──▶ 本地保存 ──▶ Sync Engine ──▶ 推送到 Worker      │
│                                    │                            │
│                                    ▼                            │
│                           收集编译/测试结果                      │
└────────────────────────────────────────────────────────────────┘
                                     │
                                     │ HTTP/WS
                                     ▼
┌────────────────────────────────────────────────────────────────┐
│                    Windows/macOS (Worker)                       │
│                                                                 │
│  Worker Server (:4097)                                         │
│  - 接收文件变更                                                  │
│  - 执行编译命令                                                  │
│  - 返回结果                                                      │
└────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Worker on Remote Machine (e.g., Windows)

```bash
# On Windows machine
opencode worker --port 4097 --directory C:\workspace
```

### 2. Add Worker Node on Master (Linux)

```bash
# On Linux machine
opencode node add \
  --name windows-build \
  --url http://192.168.1.100:4097 \
  --directory C:\workspace
```

### 3. List Available Workers

```bash
opencode node list
```

### 4. Sync Files and Execute Commands

```bash
# Sync local directory to worker
opencode node sync --id wrk_xxx --local-dir ./myproject

# Execute command on worker
opencode node exec --id wrk_xxx --command "go build -o app.exe main.go"

# Test connection
opencode node test --id wrk_xxx
```

## AI Tool Usage

The AI agent can use the `worker` tool for cross-platform development:

```
# List workers
action: "list"

# Sync and compile
action: "compile-run"
workerId: "wrk_xxx"
compileCommand: "go build -o chat.exe"
runCommand: "./chat.exe --client"

# Execute arbitrary command
action: "exec"
workerId: "wrk_xxx"
command: "cargo build --release"
```

## Example: Developing a P2P Chat Application

1. AI writes code on Linux
2. AI uses `worker` tool to sync code to Windows worker
3. AI runs compile command on Windows worker
4. If compilation fails, AI sees the error and fixes the code
5. AI re-syncs and re-compiles
6. Once compiled, AI can run the application on both machines for testing

## API Endpoints

Worker nodes expose the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/worker/status` | GET | Get worker status and capabilities |
| `/worker/sync` | POST | Sync files to worker |
| `/worker/exec` | POST | Execute command on worker |
| `/worker/exec/stream` | POST | Execute with streaming output |

## Files Created

| File | Description |
|------|-------------|
| `src/worker/types.ts` | Type definitions for worker system |
| `src/worker/worker.sql.ts` | Database schema for worker nodes |
| `src/worker/registry.ts` | Worker node management (add/remove/list) |
| `src/worker/sync.ts` | File sync and remote execution |
| `src/worker/server.ts` | Worker HTTP server routes |
| `src/worker/index.ts` | Module exports |
| `src/cli/cmd/worker.ts` | CLI command: `opencode worker` |
| `src/cli/cmd/node.ts` | CLI command: `opencode node` |
| `src/tool/worker.ts` | AI tool for using workers |
| `migration/.../migration.sql` | Database migration for worker tables |