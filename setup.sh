#!/bin/bash

# TrafficAI Setup Script for Linux/macOS

echo "🚀 Starting TrafficAI Setup..."

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install it first."
    exit 1
fi

# 2. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists."
fi

# 3. Activate venv
source venv/bin/activate
echo "✅ Activated virtual environment."

# 4. Install Dependencies
echo "⬇️ Installing dependencies..."
pip install -r requirements.txt

# 5. Frontend Setup
echo "🎨 Setting up frontend..."
if command -v pnpm &> /dev/null; then
    pnpm install
    pnpm run build:css
elif command -v npm &> /dev/null; then
    echo "⚠️ pnpm not found, using npm..."
    npm install
    npm run build:css
else
    echo "❌ Node.js/pnpm not found. CSS build skipped."
fi

# 6. Database Setup
echo "🗄️ Setting up database..."
export FLASK_APP=run.py
if [ ! -d "migrations" ]; then
    echo "   Initializing migrations..."
    flask db init
fi
flask db migrate -m "Auto migration"
flask db upgrade

# 6. Model Download (Optional check)
if [ ! -f "yolov8n.pt" ] && [ ! -f "models/yolov8n.pt" ]; then
    echo "⚠️ Note: YOLOv8 model will be downloaded automatically on first run."
fi

echo "✅ Setup complete!"
echo "👉 Run 'source venv/bin/activate' then 'flask run' to start."
