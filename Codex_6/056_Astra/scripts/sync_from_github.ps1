param(
    [string]$Target = "X:\CODEX_5.5_redactor\Codex_6\056_Astra",
    [string]$Branch = "astra/056-clean-room-skeleton"
)

$ErrorActionPreference = "Stop"

$repo = "ZvezniyLord/journal-factory-agent"
$archiveUrl = "https://github.com/$repo/archive/refs/heads/$Branch.zip"
$tmp = Join-Path $env:TEMP ("astra-sync-" + [guid]::NewGuid().ToString("N"))
$zip = Join-Path $tmp "repo.zip"
$extract = Join-Path $tmp "extract"

New-Item -ItemType Directory -Force -Path $tmp, $extract | Out-Null

try {
    Write-Host "Downloading Astra branch..."
    Invoke-WebRequest -Uri $archiveUrl -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $extract -Force

    $marker = Get-ChildItem -Path $extract -Recurse -File -Filter "ASTRA_MASTER.md" |
        Where-Object { $_.FullName -match "[\\/]Codex_6[\\/]056_Astra[\\/]ASTRA_MASTER\.md$" } |
        Select-Object -First 1

    if (-not $marker) {
        throw "Could not locate Codex_6\056_Astra in downloaded archive."
    }

    $source = Split-Path $marker.FullName -Parent
    New-Item -ItemType Directory -Force -Path $Target | Out-Null

    # Overlay repository-managed files. Keep local runtime/output state.
    $excludeDirs = @("runs", "output")
    Get-ChildItem -Path $source -Force | ForEach-Object {
        if ($excludeDirs -contains $_.Name) {
            return
        }
        $dest = Join-Path $Target $_.Name
        if ($_.PSIsContainer) {
            Copy-Item $_.FullName -Destination $dest -Recurse -Force
        }
        else {
            Copy-Item $_.FullName -Destination $dest -Force
        }
    }

    Write-Host "Synced to: $Target"
    Write-Host "Next: $Target\scripts\bootstrap_hermes.ps1"
}
finally {
    if (Test-Path $tmp) {
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}
