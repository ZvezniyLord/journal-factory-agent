param(
    [string]$Target = "X:\CODEX_5.5_redactor\Codex_6\056_Asttra",
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

    $bootstrapDir = Join-Path $Target "runs\bootstrap"
    New-Item -ItemType Directory -Force -Path $bootstrapDir | Out-Null
    $syncState = @{
        status = "PASS"
        source_repository = $repo
        source_branch = $Branch
        source_path = "Codex_6/056_Astra"
        local_target = $Target
        runs_preserved = $true
        output_preserved = $true
        timestamp_utc = [DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json -Depth 3
    Set-Content -Path (Join-Path $bootstrapDir "sync_state.json") -Value $syncState -Encoding UTF8

    Write-Host "Synced repository workspace into local folder: $Target"
    Write-Host "Repository source folder is Codex_6\056_Astra; local folder name may remain 056_Asttra."
    Write-Host "Runtime provenance: $bootstrapDir\sync_state.json"
}
finally {
    if (Test-Path $tmp) {
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}
