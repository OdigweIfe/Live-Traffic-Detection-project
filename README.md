# TrafficAI - Intelligent Traffic Violation Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)

TrafficAI is an automated traffic monitoring system that uses Computer Vision (YOLOv8 + OpenCV) to detect traffic violations from CCTV footage. It identifies red-light runners, overspeeding vehicles, and lane violations, providing a dashboard for officers to review evidence.

## Features

- **Vehicle Detection**: Real-time detection of cars, trucks, motorcycles, and buses using specialized YOLOv8 models.
- **Violation Monitoring**:
  - **Red Light Violation**: Detects vehicles crossing stop lines during red signals.
  - **Speeding Violation**: Calculates vehicle speed (km/h) and flags violations > 60 km/h.
  - **Lane Discipline**: Monitors improper lane changes (beta).
- **Advanced ANPR**: Hybrid Optical Character Recognition using PaddleOCR (primary) and EasyOCR (fallback) for high-accuracy license plate detection.
- **Modern Dashboard**: 
  - Real-time statistics and analytics.
  - Detailed violation reports with video evidence playback.
  - Advanced filtering (Date, Violation Type, License Plate).
  - False positive management.
- **Live Stream**: Low-latency video processing feed with modern, responsive UI.

## Tech Stack

- **Backend**: Python 3.10+, Flask 3.0
- **AI/ML**: PyTorch, Ultralytics YOLOv8, OpenCV
- **OCR**: PaddleOCR, EasyOCR
- **Database**: SQLite (SQLAlchemy ORM) with Flask-Migrate for migrations
- **Frontend**: HTML5, Tailwind CSS v4 (via PostCSS)

- **Testing**: pytest

## Prerequisites

- Python 3.10 or higher
- Node.js v18+ (for frontend build)
- pnpm (recommended) or npm
- Git
- (Optional) CUDA-capable GPU for faster processing

## System Requirements

### Windows

1. **Python 3.10+**: Download from [python.org](https://www.python.org/downloads/)
2. **Visual C++ Build Tools** (for PyTorch): Download from [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv git libgl1-mesa-glx
```

### macOS

```bash
brew install python@3.10
```

## 🚀 Quick Start (One-Click Setup)

Get the project running in minutes using our automated setup scripts. These scripts handle everything:
1. Creating a Python virtual environment.
2. Installing backend dependencies.
3. **Installing frontend dependencies (Tailwind CSS v4).**
4. **Building static assets.**


### Windows
```powershell
git clone https://github.com/OdigweIfe/Live-Traffic-Detection-project.git
cd TrafficAI
.\setup.ps1
flask run
```

### Linux / macOS
```bash
git clone https://github.com/OdigweIfe/Live-Traffic-Detection-project.git
cd TrafficAI
chmod +x setup.sh && ./setup.sh
source venv/bin/activate
flask run
```

---

## Manual Installation

If you prefer to set up manually:

### 1. Clone the repository

```bash
git clone https://github.com/OdigweIfe/Live-Traffic-Detection-project.git
cd TrafficAI
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Note**: For GPU support with PyTorch, visit [pytorch.org](https://pytorch.org/get-started/locally/) to install the CUDA version.

### 4. Frontend Setup (New)

The project uses Tailwind CSS v4. You need to install dependencies and build the styles.

```bash
# Install dependencies (pnpm recommended)
pnpm install
# OR
npm install

# Build CSS
pnpm run build:css
# OR
npm run build:css
```


### 5. GPU Support (Optional)

To enable GPU acceleration (recommended for real-time processing), you must install the CUDA-enabled version of PyTorch. **This supports both CPU and GPU modes**.

1.  **Install PyTorch (CUDA 12.1)**:
    ```bash
    # Uninstall default CPU version first
    pip uninstall torch torchvision torchaudio

    # Install GPU version
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    ```

2.  **PaddleOCR GPU (Optional)**:
    For faster license plate recognition, you can install the GPU-optimized version of PaddlePaddle.
    
    **Note**: Our automated setup scripts (`setup.ps1` or `setup.sh`) will automatically detect your NVIDIA GPU and offer to install this for you.
    
    To install manually:
    ```bash
    pip uninstall paddlepaddle
    pip install paddlepaddle-gpu
    ```
    *(Note: Check paddlepaddle.org.cn for specific CUDA version commands if needed)*

3.  **Switching Modes**:
    You can switch between CPU and GPU instantly by editing your `.env` file:
    ```ini
    USE_GPU=true  # Force GPU
    # OR
    USE_GPU=false # Force CPU
    # OR
    USE_GPU=auto  # Auto-detect (Default)
    ```

### 6. Download YOLO models


The application requires the following model files:

- **YOLOv8n.pt** (vehicle detection) - Download from [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
  - Place in: `models/yolov8n.pt`
  - The app will attempt to download automatically on first run

- **license_plate_detector.pt** (license plate detection)
  - **Source**: Hugging Face (Custom trained model)
  - **Status**: Included locally in `models/` directory. No download required if cloning full repo.
  - **Path**: `models/license_plate_detector.pt`

### 7. Configure environment


```bash
cp .env.example .env
```

Edit `.env` and configure:
- `SECRET_KEY`: Change for production
- `PADDLE_OCR_ENABLED`: Enable PaddleOCR (true/false)
- `USE_GPU`: Set to `"true"`, `"false"`, or `"auto"` (default)

### 8. Initialize the database


```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

Or use the setup script:

```bash
# Windows
.\setup.ps1

# Linux/Mac
chmod +x setup.sh && ./setup.sh
```

## Database

TrafficAI uses SQLite for data persistence. The database file is located at:

```
instance/trafficai.db
```

### Database Schema

| Table | Description |
|-------|-------------|
| `violations` | Stores all violation records including metadata, video paths, and timestamps. |

**Key Columns:**
- `id`: Primary Key
- `violation_type`: Red Light, Speeding, etc.
- `license_plate`: Detected text
- `speed_kmh`: Speed in km/h
- `video_path`: Path to evidence video
- `frame_number`: Frame index of violation

### Database Migrations

When making changes to models:

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

### Backup and Restore

```bash
# Backup
copy instance\trafficai.db backups\trafficai_backup.db

# Restore
copy backups\trafficai_backup.db instance\trafficai.db
```

## Usage

### Run the application

```bash
# Using Flask
flask run

# Using run.py
python run.py
```

The application will be available at `http://127.0.0.1:5000`

### Dashboard

Access the dashboard at: `http://127.0.0.1:5000/dashboard`

### Upload Video

1. Navigate to the uploads page
2. Select CCTV footage for processing
3. The system will analyze the video and detect violations

### Running Tests

```bash
pytest
pytest -v  # Verbose output
pytest --cov=app  # With coverage report
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `DATABASE_URI` | Database connection | `sqlite:///instance/trafficai.db` |
| `FLASK_APP` | Flask application entry | `run.py` |
| `FLASK_ENV` | Flask environment | `development` |
| `USE_GPU` | Processing device (true/false/auto) | `auto` |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | `104857600` |
| `UPLOAD_FOLDER` | Upload directory | `app/static/uploads` |
| `SPEED_LIMIT` | Speed limit threshold in km/h | `60.0` |
| `PIXELS_PER_METER` | Camera calibration value (pixels covering 1 meter) | `40.0` |

### ROI Configuration

Region of Interest (ROI) configuration files are located in:
- `config/roi/traffic_video_modified.json`
- `config/roi/highway_cam_01.json`
- `config/roi/intersection_cam_01.json`

## Troubleshooting

### Common Issues

#### 1. PaddleOCR/EasyOCR not loading

```
Error: OCR model not loaded properly
```

**Solution**:
- Ensure paddlepaddle and paddleocr are installed: `pip install paddlepaddle paddleocr`
- For CPU only: `pip install paddlepaddle==3.0.0 paddleocr`
- Check GPU availability with `nvidia-smi`

#### 2. CUDA out of memory

```
RuntimeError: CUDA out of memory
```

**Solution**:
- Set `USE_GPU=false` in `.env`
- Reduce video batch size
- Use a smaller YOLO model

#### 3. Database migration errors

```
 alembic.util.exc.CommandError: Can't locate revision identified by 'xyz'
```

**Solution**:
```bash
flask db stamp head
flask db migrate
flask db upgrade
```

#### 4. Model file not found

```
FileNotFoundError: models/yolov8n.pt not found
```

**Solution**:
- The model will download automatically on first run
- Manual download: `wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt`

#### 5. Port already in use

```
OSError: [Errno 98] Address already in use
```

**Solution**:
```bash
# Find and kill the process
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

#### 6. Import errors with PyTorch

**Solution**:
```bash
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### 7. Frontend / Tailwind Issues

#### Styles not applying or "input.css not found"
- Ensure you have run `pnpm install` and `pnpm run build:css`.
- Check `app/static/css/output.css` exists.
- If getting `Cannot find module`, delete `node_modules` and re-run `pnpm install`.

### Getting Help

- Check the [Issues](https://github.com/OdigweIfe/Live-Traffic-Detection-project/issues) page
- Review the [docs](docs/) directory
- Run with debug mode: `FLASK_ENV=development flask run`

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Write docstrings for all functions
- Add type hints where applicable
- Write tests for new features
- Update documentation as needed

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Your PR will be reviewed by maintainers
4. Once approved, your PR will be merged

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ultralytics](https://ultralytics.com/) for YOLOv8
- [OpenCV](https://opencv.org/) for computer vision
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for text recognition
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for deep learning OCR

## Project Structure

```
TrafficAI/
├── app/
│   ├── __init__.py          # App factory: Initializes Flask, DB, and Blueprints
│   ├── models.py            # Database models: Defines Violation schema
│   ├── routes/              # Flask blueprints
│   │   ├── admin.py         # Admin routes for system management
│   │   ├── dashboard.py     # Main dashboard view logic
│   │   ├── upload.py        # Video upload handling
│   │   ├── violations.py    # Violation details and playback
│   │   └── summary.py       # Statistics aggregation
│   ├── ai/                  # Core AI Detection Modules
│   │   ├── detector.py      # Object Detection: Loads YOLOv8 to find vehicles
│   │   ├── anpr.py          # ANPR: Optical Character Recognition (PaddleOCR)
│   │   ├── red_light.py     # Logic: Checks if vehicle crossed stop line
│   │   ├── speed.py         # Logic: Calculates pixel-to-meter speed
│   │   └── lane.py          # Logic: Monitors lane boundary crossings
│   ├── static/              # Static assets
│   ├── templates/           # Jinja2 HTML templates
│   └── utils/               # Helper functions
├── config/
│   └── roi_config.py        # Defines Stop Lines and Zones for cameras
├── models/                  # AI Model Files
│   ├── yolov8n.pt           # Vehicle detection model (auto-downloaded)
│   └── license_plate_detector.pt # Custom Plate Detection Model (Local/HuggingFace)
├── requirements.txt         # Project dependencies
├── run.py                   # Application entry point
├── setup.ps1                # One-click setup script (Windows)
├── setup.sh                 # One-click setup script (Linux/Mac)
└── README.md                # Project documentation
```
