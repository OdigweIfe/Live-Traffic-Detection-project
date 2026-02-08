$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting TrafficAI Setup..." -ForegroundColor Cyan

# 1. Check Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed. Please install Python 3.10+ first."
    exit 1
}

# 2. Create Virtual Environment
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "✅ Virtual environment already exists." -ForegroundColor Green
}

# 3. Activate
Write-Host "Activating venv..."
& .\venv\Scripts\Activate.ps1

# 4. Install Dependencies
Write-Host "⬇️ Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# 5. Frontend Setup
Write-Host "🎨 Setting up frontend..." -ForegroundColor Yellow
if (Get-Command "pnpm" -ErrorAction SilentlyContinue) {
    pnpm install
    pnpm run build:css
} elseif (Get-Command "npm" -ErrorAction SilentlyContinue) {
    Write-Host "⚠️ pnpm not found, using npm..." -ForegroundColor Yellow
    npm install
    npm run build:css
} else {
    Write-Warning "❌ Node.js/pnpm not found. CSS build skipped. Install Node.js and run 'pnpm install && pnpm run build:css'"
}

# 6. Database Setup
Write-Host "🗄️ Setting up database..." -ForegroundColor Yellow
$env:FLASK_APP = "run.py"

if (-not (Test-Path "migrations")) {
    Write-Host "   Initializing migrations..."
    flask db init
}

# Run migration (might show 'no changes' which is fine)
try {
    flask db migrate -m "Auto migration"
    flask db upgrade
} catch {
    Write-Host "   Database up to date or no changes detected." -ForegroundColor Gray
}

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "👉 Run '.\venv\Scripts\activate' then 'flask run' to start." -ForegroundColor Cyan
