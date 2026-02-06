# Windows Support Changes

## Summary of Changes

This document describes the changes made to enable native Windows support for OpenClaw.

## Modified Files

### 1. `scripts/bundle-a2ui.mjs` (NEW)
- **Purpose**: Cross-platform replacement for `scripts/bundle-a2ui.sh`
- **Changes**: Converted bash script to Node.js for Windows compatibility
- **Key Features**:
  - Uses `node:fs/promises` and `node:crypto` instead of bash commands
  - Cross-platform path handling with `path.sep`
  - Hash-based cache invalidation works on all platforms

### 2. `package.json`
- **Changed**:
  - `canvas:a2ui:bundle`: `bash scripts/bundle-a2ui.sh` → `node scripts/bundle-a2ui.mjs`

### 3. `.npmrc`
- **Added**: `@napi-rs/canvas` to `allow-build-scripts`
- **Added**: Comment about `authenticate-pam` being Unix-only

### 4. `pnpm-workspace.yaml`
- **Removed**: `authenticate-pam` from `onlyBuiltDependencies` (Unix-only)
- **Added**: Comment explaining the exclusion

### 5. `README.md`
- **Updated**: Platform support text to include Windows
- **Updated**: Installation instructions with Windows-specific notes
- **Added**: Link to Windows Installation Guide

### 6. `docs/install/windows.md` (NEW)
- **Purpose**: Comprehensive Windows installation and troubleshooting guide
- **Contents**:
  - Prerequisites (Node.js, pnpm, Visual Studio Build Tools)
  - Installation options (npm, source, WSL2)
  - Windows-specific features (Scheduled Task daemon, shell differences)
  - Known limitations (PTY, Unix features, Docker paths)
  - Troubleshooting common issues
  - Performance tips

## Existing Windows Support (Already in Codebase)

The following Windows support was already present in the codebase:

### 1. `src/daemon/schtasks.ts`
- Windows Scheduled Task integration for daemon service
- Creates task scripts with `.cmd` extension
- Handles task creation, deletion, start, stop, restart

### 2. `src/daemon/service.ts`
- Platform detection: `process.platform === "win32"`
- Returns Windows-specific service implementation

### 3. `src/agents/bash-tools.exec.ts`
- Platform-aware process spawning
- Windows-specific EOF character: `\x1a` vs `\x04`
- `detached: process.platform !== "win32"` handling
- PTY support with fallback to regular process

### 4. `@lydell/node-pty`
- Includes prebuilt binaries for Windows:
  - `@lydell/node-pty-win32-x64`
  - `@lydell/node-pty-win32-arm64`

## How to Build on Windows

### Prerequisites

1. Install Node.js (>= 22.12.0)
2. Install pnpm: `npm install -g pnpm`
3. Install Visual Studio Build Tools (for native dependencies)

### Build Steps

```cmd
git clone https://github.com/openclaw/openclaw.git
cd openclaw

pnpm install
pnpm build
pnpm openclaw onboard
```

### Troubleshooting Build Issues

**Error: "msbuild not found"**
→ Install Visual Studio Build Tools

**Error: "node-gyp failed"**
→ Ensure Python and Visual Studio Build Tools are installed

**PTY-related errors**
→ These are warnings; the system falls back to non-PTY mode

## Known Limitations

1. **PTY Support**
   - Limited on Windows
   - Some TTY-required CLIs may not work properly
   - Solution: Use `pty=false` flag

2. **Unix-Specific Features**
   - `authenticate-pam` not available (Linux/macOS only)
   - Some shell scripts won't work directly

3. **Docker Sandbox**
   - Requires Docker Desktop with WSL2 backend
   - Path mounting differences (`/c/...` vs `C:\...`)

4. **Platform-Specific Channels**
   - iMessage: macOS only
   - Some notification features may differ

## Testing on Windows

To test the Windows build:

```cmd
# Run the gateway
pnpm openclaw gateway --port 18789 --verbose

# Test agent
pnpm openclaw agent --message "Hello"

# Test doctor
pnpm openclaw doctor
```

## Future Improvements

Potential areas for further Windows enhancement:

1. **Better PTY Support**
   - Investigate conpty/windows-conpty-host
   - Alternative TTY emulation

2. **Native Windows Notifications**
   - Use Windows Toast notifications
   - Integration with Windows Action Center

3. **Windows Service Instead of Scheduled Task**
   - More robust daemon management
   - Better auto-start on boot

4. **PowerShell Support**
   - Add PowerShell as first-class shell option
   - Better cmd.exe compatibility layer

## Contributing

When making changes that affect Windows:

1. Test on Windows 10/11
2. Use cross-platform APIs (`path`, `os`, `child_process`)
3. Avoid hardcoding Unix-specific paths
4. Document Windows-specific behavior
5. Consider using `process.platform` checks for platform-specific code

## Resources

- [Windows Installation Guide](./docs/install/windows.md)
- [Issue Tracker](https://github.com/openclaw/openclaw/issues)
- [Discord](https://discord.gg/clawd)
