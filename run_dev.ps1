$env:FLASK_APP = "run.py"
$env:FLASK_DEBUG = "1"
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = "True"
& .\venv\Scripts\Activate.ps1
flask run
