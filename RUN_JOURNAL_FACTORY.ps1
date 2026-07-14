Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
$uv = Get-Command uv -ErrorAction Stop
& $uv.Source run --no-project --with-requirements requirements.txt python -m journal_factory.launcher_gui
