[CmdletBinding()]
param(
    [string]$ApiKey = "",
    [int]$Port = 8787,
    [switch]$AllowInsecureTls
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
    Invoke-Python -m pip install -r requirements.txt

    $finalApiKey = ($ApiKey -as [string])
    if (-not $finalApiKey) {
        $finalApiKey = (Read-ApiKeyFromConfig -Path $appConfigPath)
    }
    $finalApiKey = ($finalApiKey -as [string]).Trim()

    if ($finalApiKey) {
        $env:WARRANTY_REMOTE_API_KEY = $finalApiKey
    }
    $env:WARRANTY_REMOTE_TIMEOUT_MS = "45000"
    if ($AllowInsecureTls) {
        $env:WARRANTY_REMOTE_ALLOW_INSECURE_TLS = "1"
    }

    Write-Host "Starting local worker on http://127.0.0.1:$Port" -ForegroundColor Green
    & $pythonExe @pythonBaseArgs -m uvicorn hp_warranty_worker:app --host 127.0.0.1 --port $Port
}
finally {
    Pop-Location
}
