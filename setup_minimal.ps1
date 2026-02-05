$ErrorActionPreference = "Stop"
Write-Host "Activating venv..."
& .\venv\Scripts\Activate.ps1

Write-Host "Installing minimal dependencies..."
pip install -r requirements-minimal.txt

Write-Host "Initializing database..."
$env:FLASK_APP = "run.py"
if (-not (Test-Path "migrations")) {
    flask db init
}
flask db migrate -m "Initial schema"
flask db upgrade

Write-Host "Setup complete!"
