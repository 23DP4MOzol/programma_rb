[CmdletBinding()]
param(
    [int]$Port = 8787,
    [switch]$AllowInsecureTls
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$startScript = Join-Path $scriptDir "start_worker.ps1"

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

if (-not (Test-Path $startScript)) {
    throw "Missing worker start script: $startScript"
}

if (Test-WorkerHealthy -Address "127.0.0.1" -TcpPort $Port) {
    return
}

$argList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$startScript`"",
    "-Port", "$Port",
    "-SkipInstall",
    "-ExitIfPortBusy"
)

if ($AllowInsecureTls) {
    $argList += "-AllowInsecureTls"
}

Start-Process -FilePath "powershell.exe" -ArgumentList $argList -WindowStyle Hidden -WorkingDirectory $scriptDir
