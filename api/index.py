import os
import sys

# Add root directory to sys.path for module imports
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Ensure SQLite uses writable /tmp directory in serverless environment if no Postgres DATABASE_URL set
if not os.getenv("DATABASE_PATH") and not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_PATH"] = "/tmp/hostel.db"

from app import app

# Export WSGI application handlers for all Vercel serverless adapters
handler = app
application = app
app = app
