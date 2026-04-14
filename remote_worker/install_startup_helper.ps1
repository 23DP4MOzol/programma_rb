[CmdletBinding()]
param(
    [ValidateSet("install", "remove", "status")]
    [string]$Mode = "install",
    [int]$Port = 8787,
    [switch]$AllowInsecureTls,
    [switch]$StartNow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bootScript = Join-Path $scriptDir "start_worker_boot.ps1"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$startupCmd = Join-Path $startupDir "programma_rb_local_worker_startup.cmd"

if (-not (Test-Path $bootScript)) {
    throw "Missing boot script: $bootScript"
}

function Write-StartupCmd {
    param(
        [string]$Path,
        [string]$BootScriptPath,
        [int]$BootPort,
        [bool]$BootAllowInsecureTls
    )

    $line = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$BootScriptPath`" -Port $BootPort"
    if ($BootAllowInsecureTls) {
        $line += " -AllowInsecureTls"
    }

    $content = @(
        "@echo off",
        $line
    ) -join "`r`n"

    Set-Content -Path $Path -Value $content -Encoding ASCII
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

switch ($Mode) {
    "install" {
        New-Item -ItemType Directory -Path $startupDir -Force | Out-Null
        Write-StartupCmd -Path $startupCmd -BootScriptPath $bootScript -BootPort $Port -BootAllowInsecureTls $AllowInsecureTls.IsPresent
        Write-Host "Installed startup helper: $startupCmd" -ForegroundColor Green

        if ($StartNow) {
            $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$bootScript`"", "-Port", "$Port")
            if ($AllowInsecureTls) {
                $args += "-AllowInsecureTls"
            }
            Start-Process -FilePath "powershell.exe" -ArgumentList $args -WindowStyle Hidden -WorkingDirectory $scriptDir
            Write-Host "Triggered worker boot script." -ForegroundColor Green
        }
    }
    "remove" {
        if (Test-Path $startupCmd) {
            Remove-Item -Path $startupCmd -Force
            Write-Host "Removed startup helper: $startupCmd" -ForegroundColor Green
        }
        else {
            Write-Host "Startup helper was not installed: $startupCmd" -ForegroundColor Yellow
        }
    }
    "status" {
        $installed = Test-Path $startupCmd
        $running = Test-WorkerHealthy -Address "127.0.0.1" -TcpPort $Port

        Write-Host "Startup helper installed: $installed"
        Write-Host "Worker listening on 127.0.0.1:${Port}: $running"
        Write-Host "Startup helper path: $startupCmd"
    }
}
