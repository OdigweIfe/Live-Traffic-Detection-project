from app import create_app
from app.models import Violation

app = create_app()

with app.app_context():
    v = Violation.query.get(99)
    if v:
        print(f"PATH_START|{v.video_path}|PATH_END")
