from app import create_app
import os

app = create_app()
print(f"Root Path: {app.root_path}")
print(f"Static Folder: {app.static_folder}")
