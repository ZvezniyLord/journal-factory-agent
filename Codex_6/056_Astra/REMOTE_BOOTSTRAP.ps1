param(
    [string]$Target = "X:\CODEX_5.5_redactor\Codex_6\056_Asttra"
)

$ErrorActionPreference = "Stop"
$branch = "astra/056-clean-room-skeleton"
$repo = "ZvezniyLord/journal-factory-agent"
$syncUrl = "https://raw.githubusercontent.com/$repo/$branch/Codex_6/056_Astra/scripts/sync_from_github.ps1"
$tmpScript = Join-Path $env:TEMP ("astra-sync-" + [guid]::NewGuid().ToString("N") + ".ps1")

Write-Host "Fetching Astra sync script..."
Invoke-WebRequest -Uri $syncUrl -OutFile $tmpScript -UseBasicParsing

& powershell -ExecutionPolicy Bypass -File $tmpScript -Target $Target -Branch $branch
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$bootstrap = Join-Path $Target "scripts\bootstrap_hermes.ps1"
if (-not (Test-Path $bootstrap)) {
    throw "Bootstrap script missing after sync: $bootstrap"
}

& powershell -ExecutionPolicy Bypass -File $bootstrap -ProjectRoot $Target
exit $LASTEXITCODE
