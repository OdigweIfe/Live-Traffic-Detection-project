$ErrorActionPreference = "Stop"

Write-Host "--- Starting TrafficAI Setup ---"

# 1. Check Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed. Please install Python 3.10+ first."
    exit 1
}

# 2. Create Virtual Environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists."
}

# 3. Activate
Write-Host "Activating venv..."
& .\venv\Scripts\Activate.ps1

# 4. Install Dependencies
Write-Host "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 4.1 GPU Support Check (NVIDIA)
Write-Host "Checking for NVIDIA GPU..."
$videoControllers = Get-CimInstance Win32_VideoController
$hasNvidia = $false
foreach ($vc in $videoControllers) {
    if ($vc.Name -like "*NVIDIA*") {
        $hasNvidia = $true
        $gpuName = $vc.Name
        break
    }
}

if ($hasNvidia) {
    Write-Host "NVIDIA GPU detected: $gpuName"
    Write-Host "GPU acceleration can significantly improve ANPR speed."
    $installGpu = Read-Host "Install GPU support for PaddleOCR? (Y/N) [Default: Y]"
    
    if ($installGpu -eq "" -or $installGpu -match "^[Yy]") {
        Write-Host "Installing PaddlePaddle GPU..."
        try {
            pip uninstall -y paddlepaddle
            pip install paddlepaddle-gpu
            Write-Host "PaddlePaddle GPU installed successfully."
        } catch {
            Write-Warning "Failed to install GPU support. Continuing with CPU mode."
        }
    } else {
        Write-Host "Skipping GPU installation."
    }
}

# 5. Frontend Setup
Write-Host "Setting up frontend..."
if (Get-Command "pnpm" -ErrorAction SilentlyContinue) {
    pnpm install
    pnpm run build:css
} elseif (Get-Command "npm" -ErrorAction SilentlyContinue) {
    Write-Host "pnpm not found, using npm..."
    npm install
    npm run build:css
} else {
    Write-Warning "Node.js/pnpm not found. CSS build skipped."
}

# 6. Database Setup
Write-Host "Setting up database..."
$env:FLASK_APP = "run.py"

if (-not (Test-Path "migrations")) {
    Write-Host "Initializing migrations..."
    flask db init
}

try {
    flask db migrate -m "Auto migration"
    flask db upgrade
} catch {
    Write-Host "Database up to date or no changes detected."
}

Write-Host "Setup complete!"
Write-Host "To start: Run '.\venv\Scripts\activate' then 'flask run'"
