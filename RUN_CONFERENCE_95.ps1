param(
    [Parameter(Mandatory = $false)]
    [string]$Raw = "input\95.zip",

    [Parameter(Mandatory = $false)]
    [string]$Golden = "input\Conference95.pdf",

    [Parameter(Mandatory = $false)]
    [string]$Output = "build\corpus_cycles",

    [Parameter(Mandatory = $false)]
    [string]$Python = "python",

    [switch]$InstallDependencies,

    [string]$LlmEndpoint,
    [string]$LlmModel
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if (-not (Test-Path -LiteralPath $Raw -PathType Leaf)) {
    throw "RAW archive not found: $Raw"
}
if (-not (Test-Path -LiteralPath $Golden -PathType Leaf)) {
    throw "Official golden PDF not found: $Golden"
}

if ($InstallDependencies) {
    & $Python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed with exit code $LASTEXITCODE"
    }
}

$RawHash = (Get-FileHash -LiteralPath $Raw -Algorithm SHA256).Hash.ToLowerInvariant()
$GoldenHash = (Get-FileHash -LiteralPath $Golden -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "RAW:    $Raw"
Write-Host "SHA256: $RawHash"
Write-Host "GOLDEN: $Golden"
Write-Host "SHA256: $GoldenHash"

$Arguments = @(
    "-m", "journal_factory.cli", "analyze-conference",
    "--conference-id", "95",
    "--raw", $Raw,
    "--golden", $Golden,
    "--expected-articles", "34",
    "--output", $Output
)

if ($LlmEndpoint -or $LlmModel) {
    if (-not $LlmEndpoint -or -not $LlmModel) {
        throw "Specify both -LlmEndpoint and -LlmModel, or neither."
    }
    $Arguments += @("--llm-endpoint", $LlmEndpoint, "--llm-model", $LlmModel)
}

& $Python @Arguments
$ExitCode = $LASTEXITCODE
if ($ExitCode -eq 0) {
    Write-Host "Conference 95 analysis completed with PASS_ANALYSIS."
} else {
    Write-Warning "Conference 95 requires REVIEW. Inspect build\corpus_cycles\Conference95."
}
exit $ExitCode
