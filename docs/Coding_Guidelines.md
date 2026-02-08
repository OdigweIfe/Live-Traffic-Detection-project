# TrafficAI - Coding Guidelines

## The Blueprint and Build Protocol (Mandatory)

This protocol governs the entire lifecycle of creating any non-trivial feature.

### Phase 1: The Blueprint (Planning & Documentation)
Before writing code, a plan MUST be created in `docs/features/FeatureName.md`. This plan must detail:
- **High-Level Goal:** What is the feature and why is it needed?
- **Component Breakdown:** List all files/modules to be created or modified. Label each as "Server" (backend/AI) or "Client" (frontend).
- **Logic & Data Breakdown:** Describe key functions, API routes, database schema changes, and AI model integration.
- **Database Schema Changes:** If modifying the database, provide the exact SQL or schema definition.
- **Step-by-Step Implementation Plan:** Break down the work into sequential, testable steps.

**This plan requires human approval before proceeding.**

### Phase 2: The Build (Iterative Implementation)
Execute the plan one step at a time. After each step:
1. Present the code changes made.
2. Update the feature documentation with progress.
3. Wait for "proceed" signal before continuing.

### Phase 3: Finalization
Once all steps are complete:
1. Announce completion.
2. Present final documentation (updated `docs/features/FeatureName.md`).
3. Provide integration instructions and testing steps.

---

## Tech Stack Guidelines

### Python (Backend & AI)

**1. Code Style**
- Follow **PEP 8** strictly.
- Use **type hints** for all function signatures.
- Maximum line length: 100 characters.
- Use `black` for auto-formatting.

**Example:**
```python
def detect_violation(frame: np.ndarray, roi: Dict[str, int]) -> Optional[Violation]:
    """Detects traffic violations in a given frame.
    
    Args:
        frame: The video frame as a NumPy array.
        roi: Region of interest coordinates.
    
    Returns:
        Violation object if detected, None otherwise.
    """
    pass
```

**2. Project Structure**
```
/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models
│   ├── routes/              # API routes
│   │   ├── upload.py
│   │   ├── violations.py
│   ├── ai/                  # AI processing modules
│   │   ├── detector.py      # YOLO vehicle detection
│   │   ├── anpr.py          # License plate recognition
│   │   ├── violations.py    # Violation detection logic
│   ├── utils/               # Helper functions
│   │   ├── video.py
│   │   ├── config.py
│   ├── static/              # Frontend assets (CSS, JS, images)
│   ├── templates/           # HTML templates
├── config.py                # Configuration
├── requirements.txt         # Dependencies
├── run.py                   # Entry point
```

**3. Flask Best Practices**
- Use **Blueprints** for route organization.
- Use **Flask-SQLAlchemy** for ORM.
- Use **Flask-Migrate** for database migrations.
- Store secrets in `.env` (never commit to Git).

**4. AI/ML Guidelines**
- **Model Loading:** Load YOLO and OCR models once at app startup (not per request).
- **Preprocessing:** Standardize input (resize, normalize) before passing to models.
- **Error Handling:** Wrap AI inference in try-except blocks. Log failures, don't crash.
- **Performance:** Use `torch.no_grad()` for inference to save memory.

**Example:**
```python
import torch
from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        # Select device based on configuration
        use_gpu_env = os.environ.get('USE_GPU', 'auto').lower()
        cuda_available = torch.cuda.is_available()
        if use_gpu_env == 'true':
            self.device = 'cuda'
        elif use_gpu_env == 'auto':
            self.device = 'cuda' if cuda_available else 'cpu'
        else:
            self.device = 'cpu'
        self.model.to(self.device)
    
    @torch.no_grad()
    def detect(self, frame: np.ndarray) -> List[Detection]:
        results = self.model(frame, device=self.device)
        return self._parse_results(results)
```

**5. Database Guidelines**
- Use **SQLite** for local development (file-based, no server setup needed).
- Use **migrations** for all schema changes (`flask db migrate`, `flask db upgrade`).
- Index frequently queried columns (`timestamp`, `license_plate`).
- Use `DateTime(timezone=True)` for timestamps.
- Database file stored as `instance/trafficai.db`.

**Example Model:**
```python
from app import db
from datetime import datetime

class Violation(db.Model):
    __tablename__ = 'violations'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, index=True)
    violation_type = db.Column(db.String(50), nullable=False, index=True)
    vehicle_type = db.Column(db.String(50))
    license_plate = db.Column(db.String(20), index=True)
    speed_kmh = db.Column(db.Float)
    image_path = db.Column(db.String(255))
    location = db.Column(db.String(100))
```

---

### Frontend (HTML/CSS/JavaScript/Bootstrap)

**1. Structure**
- **Option A (Traditional):** Use **Bootstrap 5** for responsive design.
- **Option B (Modern):** Use **Next.js + Tailwind CSS** for a polished, modern admin dashboard.
- Separate concerns: HTML (structure), CSS (styling), JS (behavior).
- Place custom CSS in `static/css/style.css` (or Tailwind config if using Next.js).
- Place custom JS in `static/js/app.js`.

**2. HTML Guidelines**
- Use semantic HTML5 tags (`<header>`, `<main>`, `<section>`).
- Use Bootstrap classes for layout (e.g., `container`, `row`, `col`).
- Use **ARIA labels** for accessibility.

**3. JavaScript Guidelines**
- Use **vanilla JS** or **jQuery** (if already included with Bootstrap).
- For dynamic updates, use **Fetch API** to call Flask routes.
- Use `async/await` for asynchronous operations.

**Example (Fetch violations):**
```javascript
async function loadViolations() {
    try {
        const response = await fetch('/api/violations');
        const data = await response.json();
        renderViolationsTable(data.violations);
    } catch (error) {
        console.error('Error loading violations:', error);
    }
}
```

---

## Git Workflow

1. **Branching:**
   - `main` branch is production-ready.
   - Create feature branches: `feature/video-upload`, `feature/yolo-detection`.
   - Create bugfix branches: `bugfix/anpr-crash`.

2. **Commit Messages:**
   - Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`.
   - Example: `feat: add red-light violation detection logic`.

3. **Pull Requests:**
   - All features must be reviewed before merging to `main`.
   - Include tests and documentation updates in the PR.

---

## Testing Guidelines

**1. Unit Tests**
- Place tests in `tests/` directory.
- Use **pytest** for testing.
- Test all AI detection functions with sample images/videos.

**Example:**
```python
def test_vehicle_detection():
    detector = VehicleDetector('models/yolov8n.pt')
    frame = cv2.imread('test_data/sample_frame.jpg')
    detections = detector.detect(frame)
    assert len(detections) > 0
```

**2. Integration Tests**
- Test Flask routes with test client.

**Example:**
```python
def test_violation_api(client):
    response = client.get('/api/violations')
    assert response.status_code == 200
    assert 'violations' in response.json
```

---

## Security & Privacy

1. **Data Protection:** Do not store personal information beyond license plates (which are already pseudo-anonymous).
2. **Access Control:** Dashboard requires login (implement in Future scope).
3. **Input Validation:** Validate all uploaded files (file type, size).
4. **SQL Injection:** Use SQLAlchemy ORM (avoid raw SQL).

---

## Performance Optimization

1. **Video Processing:** Process video in chunks (e.g., every 5th frame for speed estimation).
2. **Database Queries:** Use pagination for violation lists.
3. **Caching:** Cache ROI configurations to avoid reloading.
4. **GPU Acceleration:** Use Google Colab for training. For inference, detect GPU availability:
   ```python
   # Select device based on configuration
   use_gpu_env = os.environ.get('USE_GPU', 'auto').lower()
   cuda_available = torch.cuda.is_available()
   if use_gpu_env == 'true':
       device = 'cuda'
   elif use_gpu_env == 'auto':
       device = 'cuda' if cuda_available else 'cpu'
   else:
       device = 'cpu'
   ```

---

## Documentation Standards

- **Code Comments:** Explain WHY, not WHAT. Code should be self-explanatory.
- **Docstrings:** Required for all public functions/classes (Google style).
- **README:** Update README.md with setup instructions, dependencies, and usage.
- **Feature Docs:** Maintain `docs/features/` for each major feature.

---

## Environment Setup

**1. Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Database Setup (SQLite)**
```bash
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```
Note: SQLite database file will be created automatically at `instance/trafficai.db`.

**3. Configuration (.env)**
```
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URI=sqlite:///instance/trafficai.db
SECRET_KEY=your-secret-key-here
MODEL_PATH=models/yolov8n.pt
```

---

## AI Model Management

**1. Model Storage**
- Store models in `models/` directory.
- **YOLOv8:** Download from Ultralytics (`yolov8n.pt`, `yolov8s.pt`).
- **OCR:** Use Tesseract or EasyOCR (install separately).

**2. Model Training (Google Colab)**
- Train/fine-tune models in Colab notebooks.
- Save trained weights and download to `models/`.
- Document training process in `docs/model_training.md`.

---

## Common Pitfalls to Avoid

1. ❌ **Hardcoding paths:** Use `config.py` for all paths.
2. ❌ **Loading models per request:** Load once at app startup.
3. ❌ **No error handling:** Wrap AI inference and file operations in try-except.
4. ❌ **Ignoring video format compatibility:** Test with multiple formats (MP4, AVI).
5. ❌ **Skipping database migrations:** Always use Flask-Migrate.

---

## Final Checklist Before Deployment

- [ ] All tests pass (`pytest`).
- [ ] Models are included in `models/` or downloadable via script.
- [ ] `.env` template provided (`.env.example`).
- [ ] README updated with setup and usage instructions.
- [ ] Database migrations applied.
- [ ] Sample test videos included in `test_data/`.
