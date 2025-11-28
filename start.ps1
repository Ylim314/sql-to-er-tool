param(
    [switch]$SkipInstall
)

Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment .venv ..."
    python -m venv .venv
}

$venvActivate = Join-Path ".venv" "Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Error "Virtual environment activation script not found: $venvActivate"
    exit 1
}
. $venvActivate

if (-not $SkipInstall -and (Test-Path "requirements.txt")) {
    Write-Host "Installing dependencies from requirements.txt ..."
    pip install -r requirements.txt
}

Write-Host "Starting Streamlit app..."
streamlit run app.py

Read-Host "Press Enter to exit..."
