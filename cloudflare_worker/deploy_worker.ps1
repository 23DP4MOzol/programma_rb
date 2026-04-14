[CmdletBinding()]
param(
    [string]$NodeVersion = "20.20.2",
    [string]$WorkerApiKey = "",
    [switch]$SkipLogin
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$appConfigPath = Join-Path $repoRoot "app_config.json"
$wranglerToml = Join-Path $scriptDir "wrangler.toml"

if (-not (Test-Path $wranglerToml)) {
    throw "wrangler.toml not found at $wranglerToml"
}

function Resolve-ToolPath {
    param([string]$Name)

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    return ""
}

function Resolve-WranglerCliPath {
    param([string]$BaseDir)

    $candidates = @(
        (Join-Path $BaseDir "node_modules\wrangler\bin\wrangler.js"),
        (Join-Path $BaseDir "node_modules\wrangler\wrangler-dist\cli.js"),
        (Join-Path $BaseDir "node_modules\wrangler\dist\cli.js")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return ""
}

function Ensure-NodeTooling {
    param(
        [string]$Version,
        [string]$ToolsRoot
    )

    $nodePath = Resolve-ToolPath -Name "node"
    $npmPath = Resolve-ToolPath -Name "npm"
    $npxPath = Resolve-ToolPath -Name "npx"

    if ($nodePath -and $npmPath -and $npxPath) {
        Write-Host "Node tooling already available:" -ForegroundColor Green
        Write-Host "  node: $nodePath"
        Write-Host "  npm:  $npmPath"
        Write-Host "  npx:  $npxPath"
        $nodeDir = Split-Path -Parent $nodePath
        $npmCli = Join-Path $nodeDir "node_modules\npm\bin\npm-cli.js"
        if (-not (Test-Path $npmCli)) {
            throw "npm-cli.js not found next to node executable: $npmCli"
        }

        return @{
            Node = $nodePath
            NpmCli = $npmCli
        }
    }

    $portableDir = Join-Path $ToolsRoot "node-v$Version-win-x64"
    $portableNodeExe = Join-Path $portableDir "node.exe"

    if (-not (Test-Path $portableNodeExe)) {
        New-Item -ItemType Directory -Path $ToolsRoot -Force | Out-Null

        $zipName = "node-v$Version-win-x64.zip"
        $zipPath = Join-Path $ToolsRoot $zipName
        $downloadUrl = "https://nodejs.org/dist/v$Version/$zipName"

        Write-Host "Downloading portable Node.js $Version..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath

        Write-Host "Extracting Node.js archive..." -ForegroundColor Yellow
        Expand-Archive -Path $zipPath -DestinationPath $ToolsRoot -Force
    }

    $portableNpmCli = Join-Path $portableDir "node_modules\npm\bin\npm-cli.js"

    if (-not (Test-Path $portableNodeExe)) {
        throw "Failed to provision portable Node.js node.exe"
    }
    if (-not (Test-Path $portableNpmCli)) {
        throw "Failed to provision portable Node.js npm-cli.js"
    }

    Write-Host "Using portable Node tooling:" -ForegroundColor Green
    Write-Host "  node: $portableNodeExe"
    Write-Host "  npm-cli: $portableNpmCli"

    return @{
        Node = $portableNodeExe
        NpmCli = $portableNpmCli
    }
}

function Read-ApiKeyFromAppConfig {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return ""
    }

    try {
        $cfg = Get-Content $Path -Raw | ConvertFrom-Json
        $value = [string]($cfg.warranty_remote_api_key)
        return $value.Trim()
    }
    catch {
        return ""
    }
}

function Read-WorkerUrlFromAppConfig {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return ""
    }

    try {
        $cfg = Get-Content $Path -Raw | ConvertFrom-Json
        $value = [string]($cfg.warranty_remote_api_url)
        return $value.Trim()
    }
    catch {
        return ""
    }
}

$toolsRoot = Join-Path $repoRoot ".tools"
$tooling = Ensure-NodeTooling -Version $NodeVersion -ToolsRoot $toolsRoot
$nodeExe = [string]$tooling.Node
$npmCli = [string]$tooling.NpmCli
$nodeDir = Split-Path -Parent $nodeExe

# Ensure child processes launched by npm (esbuild install.js, etc.) can find node.
$env:Path = "$nodeDir;$env:Path"

if (-not (Test-Path $nodeExe)) {
    throw "node executable not found: $nodeExe"
}
if (-not (Test-Path $npmCli)) {
    throw "npm cli not found: $npmCli"
}

function Invoke-Npm {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & $nodeExe $npmCli @Args
    if ($LASTEXITCODE -ne 0) {
        throw "npm command failed with exit code $LASTEXITCODE"
    }
}

$script:WranglerCli = ""

function Invoke-Wrangler {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)

    if (-not $script:WranglerCli) {
        $script:WranglerCli = Resolve-WranglerCliPath -BaseDir $scriptDir
    }
    if (-not $script:WranglerCli) {
        throw "Wrangler CLI JS not found under node_modules. Run install first."
    }

    & $nodeExe $script:WranglerCli @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Wrangler command failed with exit code $LASTEXITCODE"
    }
}

Push-Location $scriptDir
try {
    Write-Host "Installing worker dependencies..." -ForegroundColor Cyan
    Invoke-Npm install

    if (-not $SkipLogin) {
        Write-Host "Opening Wrangler login (interactive)..." -ForegroundColor Cyan
        Invoke-Wrangler login
    }

    $apiKey = $WorkerApiKey.Trim()
    if (-not $apiKey) {
        $apiKey = Read-ApiKeyFromAppConfig -Path $appConfigPath
    }

    if ($apiKey) {
        Write-Host "Updating Cloudflare secret WARRANTY_REMOTE_API_KEY..." -ForegroundColor Cyan
        $wranglerCli = Resolve-WranglerCliPath -BaseDir $scriptDir
        if (-not $wranglerCli) {
            throw "Wrangler CLI JS not found under node_modules."
        }

        $apiKey | & $nodeExe $wranglerCli secret put WARRANTY_REMOTE_API_KEY
        if ($LASTEXITCODE -ne 0) {
            throw "Wrangler secret put failed with exit code $LASTEXITCODE"
        }
    }
    else {
        Write-Warning "No API key provided and none found in app_config.json. Skipping secret update."
    }

    Write-Host "Deploying worker..." -ForegroundColor Cyan
    Invoke-Wrangler deploy

    $workerLookupUrl = Read-WorkerUrlFromAppConfig -Path $appConfigPath
    if ($workerLookupUrl) {
        try {
            $healthUrl = $workerLookupUrl -replace "/warranty/lookup$", "/health"
            Write-Host "Verifying health endpoint: $healthUrl" -ForegroundColor Cyan
            curl.exe -k -i "$healthUrl"
        }
        catch {
            Write-Warning "Health verification failed: $($_.Exception.Message)"
        }
    }

    Write-Host "Deployment flow finished." -ForegroundColor Green
}
finally {
    Pop-Location
}
