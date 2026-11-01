param([Parameter(Mandatory)][string]$ProjectRoot,[switch]$InstallBrowser)
$ErrorActionPreference = 'Stop'
$root=(Resolve-Path -LiteralPath $ProjectRoot).Path
$python=Join-Path $root '.venv-collector\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.12 -m venv (Join-Path $root '.venv-collector')
    } else {
        python -m venv (Join-Path $root '.venv-collector')
    }
    if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' }
}
& $python -m pip install -r (Join-Path $root 'collector\requirements.txt'); if($LASTEXITCODE -ne 0){throw 'dependency installation failed'}
New-Item -ItemType Directory -Force -Path (Join-Path $root 'data\collector') | Out-Null
$envFile=Join-Path $root '.env'
$exampleFile=Join-Path $root '.env.example'
if(-not(Test-Path -LiteralPath $envFile) -and (Test-Path -LiteralPath $exampleFile)){Copy-Item $exampleFile $envFile}
if($InstallBrowser){& $python -m playwright install chromium; if($LASTEXITCODE -ne 0){throw 'Chromium installation failed'}}
