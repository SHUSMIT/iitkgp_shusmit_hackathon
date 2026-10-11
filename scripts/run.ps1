param(
    [int]$ApiPort = 8000,
    [int]$WebPort = 5173
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
$apiLog = Join-Path $root 'api-startup.log'
$apiErrorLog = Join-Path $root 'api-startup-error.log'
$webLog = Join-Path $root 'web-startup.log'
$webErrorLog = Join-Path $root 'web-startup-error.log'

if (-not (Test-Path $python)) {
    throw "The .venv environment was not found. Run the setup commands in README.md first."
}
if ($null -eq $npm) {
    throw 'npm was not found. Install Node.js 20+ and run this script again.'
}

$api = $null
$web = $null
try {
    $api = Start-Process `
        -FilePath $python `
        -ArgumentList "-m uvicorn src.api.app:app --host 127.0.0.1 --port $ApiPort" `
        -WorkingDirectory $root `
        -RedirectStandardOutput $apiLog `
        -RedirectStandardError $apiErrorLog `
        -PassThru

    $web = Start-Process `
        -FilePath $env:ComSpec `
        -ArgumentList "/c `"$($npm.Source)`" run dev -- --host 127.0.0.1 --port $WebPort" `
        -WorkingDirectory (Join-Path $root 'web') `
        -RedirectStandardOutput $webLog `
        -RedirectStandardError $webErrorLog `
        -PassThru

    $ready = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        Start-Sleep -Milliseconds 500
        try {
            $health = Invoke-WebRequest "http://127.0.0.1:$ApiPort/health" -UseBasicParsing -TimeoutSec 2
            if ($health.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {
            if ($api.HasExited) {
                throw "The API stopped during startup. See $apiLog for details."
            }
        }
    }
    if (-not $ready) {
        throw "The API did not become ready within 15 seconds. See $apiLog for details."
    }

    Write-Host "RiskPulse API is ready: http://127.0.0.1:$ApiPort"
    Write-Host "RiskPulse dashboard: http://127.0.0.1:$WebPort"
    Write-Host 'Press Ctrl+C to stop both services.'
    Start-Process "http://127.0.0.1:$WebPort"

    while (-not $api.HasExited -and -not $web.HasExited) {
        Start-Sleep -Seconds 1
    }
}
finally {
    foreach ($process in @($api, $web)) {
        if ($null -ne $process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
