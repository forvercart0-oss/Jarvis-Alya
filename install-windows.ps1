# JARVIS 2.0 - Windows Installer
# Requires: PowerShell 5.1+, Administrator privileges
# Installs: Python, Node.js, Rust, Tauri dependencies, JARVIS

param(
    [switch]$SkipTauri = $false,
    [switch]$Dev = $false
)

$ErrorActionPreference = "Stop"

function Write-Info { Write-Host "[JARVIS] $args" -ForegroundColor Cyan }
function Write-Ok { Write-Host "[JARVIS] $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[JARVIS] $args" -ForegroundColor Yellow }
function Write-Fail { Write-Host "[JARVIS] $args" -ForegroundColor Red }

function Test-Admin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Fail "Please run this script as Administrator."
    exit 1
}

Write-Info "Installing JARVIS 2.0 for Windows..."

# ---------------------------------------------------------------- Package managers
$hasWinget = $false
$hasChoco = $false
$hasScoop = $false

if (Get-Command winget -ErrorAction SilentlyContinue) { $hasWinget = $true }
if (Get-Command choco -ErrorAction SilentlyContinue) { $hasChoco = $true }
if (Get-Command scoop -ErrorAction SilentlyContinue) { $hasScoop = $true }

if (-not $hasWinget -and -not $hasChoco -and -not $hasScoop) {
    Write-Warn "No package manager found. Installing winget..."
    # winget is included in Windows 11 / modern Windows 10
    # Try to install via Microsoft Store
    Start-Process "ms-windows-store://search/?query=winget" -ErrorAction SilentlyContinue
    Write-Fail "Please install winget manually and re-run this script."
    exit 1
}

$pkgMgr = "winget"
if ($hasChoco) { $pkgMgr = "choco" }
elseif ($hasScoop) { $pkgMgr = "scoop" }

Write-Ok "Package manager: $pkgMgr"

# ---------------------------------------------------------------- System dependencies
function Install-Pkg {
    param($Name, $PackageId)
    if ($pkgMgr -eq "winget") {
        winget install --id $PackageId -e --accept-source-agreements --accept-package-agreements
    } elseif ($pkgMgr -eq "choco") {
        choco install $Name -y
    } else {
        scoop install $Name
    }
}

$required = @(
    @{ Name = "Python 3"; Id = "Python.Python.3.12" },
    @{ Name = "Node.js"; Id = "OpenJS.NodeJS.LTS" },
    @{ Name = "Git"; Id = "Git.Git" }
)

foreach ($pkg in $required) {
    $cmd = $pkg.Name.ToLower().Replace(" ", "")
    if ($cmd -eq "python3") { $cmd = "python" }
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Warn "Missing: $($pkg.Name)"
        $response = Read-Host "Install $($pkg.Name) now? (y/N)"
        if ($response -match "^[Yy]$") {
            Install-Pkg $pkg.Name $pkg.Id
            Write-Ok "$($pkg.Name) installed"
        } else {
            Write-Fail "Cannot continue without $($pkg.Name)"
            exit 1
        }
    } else {
        Write-Ok "$($pkg.Name): OK"
    }
}

# ---------------------------------------------------------------- Rust
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Warn "Rust not found. Installing..."
    Invoke-RestMethod -Uri "https://sh.rustup.rs" -OutFile "$env:TEMP\rustup-init.exe"
    & "$env:TEMP\rustup-init.exe" -y --default-toolchain stable --profile minimal
    $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
    Write-Ok "Rust installed"
} else {
    Write-Ok "Rust: OK"
}

# ---------------------------------------------------------------- Python venv
Write-Info "Setting up Python environment..."
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Ok "Virtual environment created"
}

.\.venv\Scripts\Activate.ps1

$env:PIP_OPTS = "--timeout 60 --retries 5"
if ($env:JARVIS_PIP_MIRROR) {
    $env:PIP_OPTS = "$env:PIP_OPTS -i $env:JARVIS_PIP_MIRROR"
}

pip install $env:PIP_OPTS -r requirements.txt
Write-Ok "Python dependencies installed"

# ---------------------------------------------------------------- Node deps
Write-Info "Installing Node dependencies..."
Set-Location frontend
npm install --no-audit --no-fund
Set-Location ..
Write-Ok "Node dependencies installed"

# ---------------------------------------------------------------- Build frontend
Write-Info "Building frontend..."
Set-Location frontend
npm run build
Set-Location ..
Write-Ok "Frontend built"

# ---------------------------------------------------------------- Environment
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Ok ".env created from .env.example"
        Write-Warn "Edit .env to add your API keys"
    }
}

# ---------------------------------------------------------------- Data dirs
New-Item -ItemType Directory -Force -Path data/generated/images, data/generated/videos, logs | Out-Null
Write-Ok "Data directories prepared"

# ---------------------------------------------------------------- Tauri
if (-not $SkipTauri) {
    Write-Info "Building Tauri desktop application..."
    Set-Location frontend
    npm install @tauri-apps/cli 2>$null | Out-Null
    if ($Dev) {
        npm run tauri:dev
    } else {
        npm run tauri:build
    }
    Set-Location ..
    Write-Ok "Tauri build complete"
}

# ---------------------------------------------------------------- Desktop shortcuts
Write-Info "Creating shortcuts..."
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"

$Shortcut = $WshShell.CreateShortcut("$DesktopPath\JARVIS 2.0.lnk")
$Shortcut.TargetPath = "$PWD\run.bat"
$Shortcut.WorkingDirectory = $PWD
$Shortcut.IconLocation = "$PWD\assets\app-icon.ico"
$Shortcut.Save()

$Shortcut = $WshShell.CreateShortcut("$StartMenuPath\JARVIS 2.0.lnk")
$Shortcut.TargetPath = "$PWD\run.bat"
$Shortcut.WorkingDirectory = $PWD
$Shortcut.IconLocation = "$PWD\assets\app-icon.ico"
$Shortcut.Save()

Write-Ok "Shortcuts created"

Write-Host ""
Write-Host -Object "================================================" -ForegroundColor Green
Write-Host -Object "   JARVIS INSTALLATION COMPLETE" -ForegroundColor Green
Write-Host -Object "================================================" -ForegroundColor Green
Write-Host ""
Write-Info "Run: .\run.bat"
Write-Info "Or from Desktop / Start Menu: JARVIS 2.0"
