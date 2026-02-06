# Windows Build Test Script
# Run this script to verify Windows build compatibility

Write-Host "OpenClaw Windows Build Test" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Node.js version
$nodeVersion = node --version
Write-Host "Node.js version: $nodeVersion" -ForegroundColor Cyan

$requiredVersion = [version]"22.12.0"
$actualVersion = [version]($nodeVersion -replace 'v', '')

if ($actualVersion -lt $requiredVersion) {
    Write-Host "WARNING: Node.js version is below 22.12.0. Please upgrade." -ForegroundColor Red
} else {
    Write-Host "✓ Node.js version OK" -ForegroundColor Green
}

# Check pnpm
try {
    $pnpmVersion = pnpm --version
    Write-Host "pnpm version: $pnpmVersion" -ForegroundColor Cyan
    Write-Host "✓ pnpm installed" -ForegroundColor Green
} catch {
    Write-Host "✗ pnpm not found. Install with: npm install -g pnpm" -ForegroundColor Red
    exit 1
}

# Check Visual Studio Build Tools
Write-Host ""
Write-Host "Checking build tools..." -ForegroundColor Yellow

try {
    $msbuild = Get-Command msbuild -ErrorAction SilentlyContinue
    if ($msbuild) {
        Write-Host "✓ MSBuild found: $($msbuild.Source)" -ForegroundColor Green
    } else {
        Write-Host "WARNING: MSBuild not found. Native modules may fail to build." -ForegroundColor Yellow
        Write-Host "Install Visual Studio Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Cyan
    }
} catch {
    Write-Host "WARNING: Could not check for MSBuild" -ForegroundColor Yellow
}

# Test build scripts
Write-Host ""
Write-Host "Testing build scripts..." -ForegroundColor Yellow

# Test bundle-a2ui.mjs
Write-Host "Testing A2UI bundle script..." -ForegroundColor Cyan
try {
    & node scripts/bundle-a2ui.mjs
    Write-Host "✓ A2UI bundle script works" -ForegroundColor Green
} catch {
    Write-Host "✗ A2UI bundle script failed: $_" -ForegroundColor Red
}

# Check if node_modules exists
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow

if (Test-Path "node_modules") {
    Write-Host "✓ node_modules exists" -ForegroundColor Green
} else {
    Write-Host "✗ node_modules not found. Run: pnpm install" -ForegroundColor Red
}

Write-Host ""
Write-Host "=============================" -ForegroundColor Green
Write-Host "Test complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To build the project, run:" -ForegroundColor Cyan
Write-Host "  pnpm install" -ForegroundColor White
Write-Host "  pnpm build" -ForegroundColor White
Write-Host ""
Write-Host "For detailed Windows installation guide, see: docs/install/windows.md" -ForegroundColor Cyan
