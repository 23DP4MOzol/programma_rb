[CmdletBinding()]
param(
    [string]$ApiKey = "",
    [int]$Port = 8787,
    [switch]$AllowInsecureTls,
    [switch]$SkipInstall,
    [switch]$ExitIfPortBusy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$appConfigPath = Join-Path $repoRoot "app_config.json"

function Get-PythonCommand {
    $candidates = @(
        "C:/Users/LV02XVY/AppData/Local/Microsoft/WindowsApps/python3.13.exe",
        "python",
        "py"
    )

    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            if ($candidate -eq "py") {
                return @{
                    Exe = $cmd.Source
                    BaseArgs = @("-3")
                }
            }
            return @{
                Exe = $cmd.Source
                BaseArgs = @()
            }
        }
    }

    throw "Python executable not found."
}

function Read-ApiKeyFromConfig {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return ""
    }

    try {
        $cfg = Get-Content $Path -Raw | ConvertFrom-Json
        return [string]($cfg.warranty_remote_api_key)
    }
    catch {
        return ""
    }
}

function Test-WorkerHealthy {
    param(
        [string]$Address,
        [int]$TcpPort,
        [int]$TimeoutSec = 2
    )

    $url = "http://$Address`:$TcpPort/health"
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $url -Method GET -TimeoutSec $TimeoutSec -ErrorAction Stop
        return [int]$resp.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

$pythonCmd = Get-PythonCommand
$pythonExe = [string]$pythonCmd.Exe
$pythonBaseArgs = @($pythonCmd.BaseArgs)

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & $pythonExe @pythonBaseArgs @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

Push-Location $scriptDir
try {
    if ($ExitIfPortBusy -and (Test-WorkerHealthy -Address "127.0.0.1" -TcpPort $Port)) {
        Write-Host "Local worker already listening on 127.0.0.1:$Port. Exiting." -ForegroundColor Yellow
        return
    }

    if (-not $SkipInstall) {
        Invoke-Python -m pip install -r requirements.txt

        $playwrightRoot = Join-Path $env:LOCALAPPDATA "ms-playwright"
        $firefoxInstalled = $false
        if (Test-Path $playwrightRoot) {
            $entries = @(Get-ChildItem -Path $playwrightRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "firefox-*" })
            $firefoxInstalled = ($entries.Count -gt 0)
        }

        if (-not $firefoxInstalled) {
            Invoke-Python -m playwright install firefox
        }
    }

    $finalApiKey = ($ApiKey -as [string])
    if (-not $finalApiKey) {
        $finalApiKey = (Read-ApiKeyFromConfig -Path $appConfigPath)
    }
    $finalApiKey = ($finalApiKey -as [string]).Trim()

    if ($finalApiKey) {
        $env:WARRANTY_REMOTE_API_KEY = $finalApiKey
    }
    $env:WARRANTY_REMOTE_TIMEOUT_MS = "20000"
    if ($AllowInsecureTls) {
        $env:WARRANTY_REMOTE_ALLOW_INSECURE_TLS = "1"
    }

    $env:WARRANTY_REMOTE_ALLOW_EDGE_CHANNEL = "1"
    $env:WARRANTY_REMOTE_BROWSER = "chromium"
    $env:WARRANTY_REMOTE_BROWSER_CHANNEL = ""
    
    $webView2Paths = @(Get-ChildItem -Path "C:\Program Files (x86)\Microsoft\EdgeWebView\Application\*\msedgewebview2.exe" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
    if ($webView2Paths.Count -gt 0) {
        $env:WARRANTY_REMOTE_BROWSER_EXECUTABLE_PATH = $webView2Paths[0].FullName
    } else {
        $env:WARRANTY_REMOTE_BROWSER_CHANNEL = "msedge"
        $env:WARRANTY_REMOTE_BROWSER_EXECUTABLE_PATH = ""
    }

    Write-Host "Starting local worker on http://0.0.0.0:$Port" -ForegroundColor Green
    & $pythonExe @pythonBaseArgs -m uvicorn hp_warranty_worker:app --host 0.0.0.0 --port $Port
}
finally {
    Pop-Location
}
