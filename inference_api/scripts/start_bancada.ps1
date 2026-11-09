param([switch]$WithLangSmith)
$ErrorActionPreference = 'Stop'
$apiRoot = Split-Path $PSScriptRoot -Parent
$projectRoot = Split-Path $apiRoot -Parent
$pythonPath = Join-Path $apiRoot '.venv\Scripts\python.exe'
$entryPath = Join-Path $apiRoot 'run.py'
$workPath = Join-Path $apiRoot '.local\bancada-active'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Install the local Python environment first.' }
if (Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Port 8765 is already in use. Inspect the existing Bancada before starting another process.'
}
New-Item -ItemType Directory -Force -Path $workPath | Out-Null
$previousMode = $env:INFERENCE_OBSERVABILITY
$previousBuffering = $env:PYTHONUNBUFFERED
try {
    $env:INFERENCE_OBSERVABILITY = if ($WithLangSmith) { 'langsmith' } else { 'off' }
    $env:PYTHONUNBUFFERED = '1'
    $process = Start-Process -FilePath $pythonPath -ArgumentList @(('"' + $entryPath + '"'), 'serve') `
        -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $workPath 'server.out.log') `
        -RedirectStandardError (Join-Path $workPath 'server.err.log')
    $process.Id | Set-Content -LiteralPath (Join-Path $workPath 'server.pid')
} finally {
    $env:INFERENCE_OBSERVABILITY = $previousMode
    $env:PYTHONUNBUFFERED = $previousBuffering
}
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 1
        if ($health.status -eq 'up') {
            Write-Output "Bancada ready: http://127.0.0.1:8765/ (PID $($process.Id)); LangSmith requested: $WithLangSmith"
            return
        }
    } catch { Start-Sleep -Milliseconds 250 }
}
throw "Bancada did not become healthy. Inspect $workPath\server.err.log."
