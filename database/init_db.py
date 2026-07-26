import os
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import init_db
from utils.logger import logger

if __name__ == "__main__":
    logger.info("Running database initialization script...")
    init_db()
    logger.info("Database initialization completed.")
