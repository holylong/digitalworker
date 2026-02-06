# Windows Installation Guide

OpenClaw supports running on Windows with some considerations.

## Prerequisites

### Required Software

1. **Node.js** (>= 22.12.0)
   - Download from: https://nodejs.org/
   - After installation, verify:
     ```cmd
     node --version
     ```

2. **pnpm** (>= 10.23.0)
   ```cmd
   npm install -g pnpm
   ```

3. **Visual Studio Build Tools** (required for native dependencies)
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++" workload
   - Or install Visual Studio Community with C++ support

   This is required for:
   - `@napi-rs/canvas`
   - `sharp`
   - `@lydell/node-pty`
   - `@matrix-org/matrix-sdk-crypto-nodejs`

4. **Python** (optional, but may be needed for some native modules)
   - Install from: https://www.python.org/
   - Add to PATH

## Installation

### Option 1: Install from npm

```cmd
npm install -g openclaw@latest
openclaw onboard
```

### Option 2: Build from source

```cmd
git clone https://github.com/openclaw/openclaw.git
cd openclaw

pnpm install
pnpm build
pnpm openclaw onboard
```

### Option 3: Use WSL2 (Recommended for Best Compatibility)

If you encounter issues on native Windows, consider using WSL2:

1. Install WSL2:
   ```cmd
   wsl --install
   ```

2. In WSL2 Ubuntu:
   ```bash
   npm install -g openclaw@latest
   openclaw onboard
   ```

## Windows-Specific Features

### Daemon Service

On Windows, OpenClaw uses **Windows Scheduled Task** instead of systemd/launchd.

- The service is installed via `schtasks.exe`
- Task runs at user logon
- Limited privileges (non-admin)

### Shell

- Default shell: `cmd.exe` or `powershell.exe`
- PTY support: Limited (use `pty=false` for commands)
- Some Unix-specific shell features may not work

### Path Handling

- Backslashes (`\`) are automatically converted
- Environment variables: `%NAME%` format
- Home directory: `%USERPROFILE%`

## Known Limitations

1. **PTY (Pseudo-Terminal) Support**
   - Limited PTY support on Windows
   - Some TTY-required CLIs may not work properly
   - Use `pty=false` or `host=gateway` for better compatibility

2. **Unix-Specific Features**
   - `authenticate-pam` is not available (Linux/macOS only)
   - Some shell scripts may not work directly
   - Symlinks may require Developer Mode

3. **Docker Sandbox**
   - Requires Docker Desktop for Windows
   - WSL2 backend recommended
   - Path mounting differences: `/c/...` vs `C:\\...`

4. **iMessage Channel**
   - Not available on Windows (macOS only)

5. **macOS/iOS Apps**
   - Cannot build macOS/iOS apps on Windows
   - Requires macOS with Xcode

## Troubleshooting

### Build Errors

**Error: "msbuild not found"**
- Install Visual Studio Build Tools
- Add MSBuild to PATH

**Error: "Python not found"**
- Install Python 3.x
- Add to PATH
- Set `npm config set python python3`

**Error: "node-gyp failed"**
- Ensure Visual Studio Build Tools are installed
- Update npm: `npm install -g npm@latest`
- Clear cache: `pnpm store prune`

### Runtime Errors

**Error: "Module not found"**
- Run `pnpm install` again
- Clear node_modules: `rmdir /s /q node_modules && pnpm install`

**PTY Errors**
- Use `--no-pty` flag or set `pty=false`
- Run command with `host=gateway`

### Docker Issues

**Error: "docker not recognized"**
- Install Docker Desktop for Windows
- Start Docker Desktop
- Enable WSL2 integration

**Path Mounting Issues**
- Use WSL2 backend for Docker
- Or use full Windows paths: `/c/Users/...`

## Performance Tips

1. **Use SSD**: Node.js and native modules benefit from fast storage
2. **Exclude from Antivirus**: Add project folder to antivirus exclusions
3. **Windows Defender**: Add `node.exe` and `pnpm.exe` to exclusions if needed

## Getting Help

If you encounter issues:

1. Check [FAQ](../help/faq.md)
2. Run `openclaw doctor` for diagnostics
3. Join [Discord](https://discord.gg/clawd) for support
4. File an issue on [GitHub](https://github.com/openclaw/openclaw/issues)

## Alternative: Use Docker

If native Windows installation proves difficult, consider using Docker:

```cmd
docker-compose up -d
```

See [Docker Installation](./docker.md) for details.
