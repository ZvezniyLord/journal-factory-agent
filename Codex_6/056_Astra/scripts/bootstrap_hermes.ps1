param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"
$src = Join-Path $ProjectRoot "src"
$localPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $localPython) { $localPython } else { "python" }

if (-not (Test-Path (Join-Path $ProjectRoot "config\hermes_runtime.json"))) {
    throw "Missing config\hermes_runtime.json in $ProjectRoot"
}

$env:PYTHONPATH = $src
Write-Host "Astra workspace: $ProjectRoot"
Write-Host "Python: $python"
Write-Host "Bootstrapping local Hermes..."

& $python -m astra_journal.bootstrap --root $ProjectRoot
exit $LASTEXITCODE
