param([Parameter(Mandatory)][string]$ProjectRoot)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$taskPython = Join-Path $taskRoot '.venv-collector\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython -PathType Leaf)) {
    $taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $taskPython -PathType Leaf)) {
    throw 'No se encontró Python en .venv-collector ni .venv. Ejecuta scripts\windows\install-collector.ps1.'
}
$taskEnv = Join-Path $taskRoot 'collector\.env'
Set-Location -LiteralPath $taskRoot
& $taskPython -m collector --env $taskEnv run-once
exit $LASTEXITCODE
