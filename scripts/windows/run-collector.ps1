param([Parameter(Mandatory)][string]$ProjectRoot)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$taskPython = Join-Path $taskRoot '.venv-collector\Scripts\python.exe'
$taskEnv = Join-Path $taskRoot 'collector\.env'
Set-Location -LiteralPath $taskRoot
& $taskPython -m collector --env $taskEnv run-once
exit $LASTEXITCODE
