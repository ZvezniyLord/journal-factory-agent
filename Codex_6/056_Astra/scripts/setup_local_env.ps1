param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

$venv = Join-Path $ProjectRoot ".venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating clean-room virtual environment: $venv"
    python -m venv $venv
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create local virtual environment."
    }
}

Write-Host "Installing Astra in local editable dev mode..."
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m pip install -e "$ProjectRoot[dev]"
exit $LASTEXITCODE
