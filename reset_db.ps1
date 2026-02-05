$ErrorActionPreference = "Stop"
& .\venv\Scripts\Activate.ps1
$env:FLASK_APP = "run.py"

Write-Host "Creating instance folder..."
New-Item -ItemType Directory -Force -Path "instance"

Write-Host "Resetting migrations..."
if (Test-Path "migrations") { Remove-Item -Recurse -Force "migrations" }
if (Test-Path "instance/trafficai.db") { Remove-Item -Force "instance/trafficai.db" }

Write-Host "Initializing DB..."
flask db init
flask db migrate -m "Fresh init"
flask db upgrade
Write-Host "DB Init Complete."
