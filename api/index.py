import os
import sys

# Add root directory to sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Export wsgi application handler for Vercel serverless
app = app
