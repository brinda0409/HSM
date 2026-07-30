import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name="shms"):
    """
    Configures and returns a logger instance with dual output: console and rotating log file.
    Falls back gracefully to console-only output on read-only serverless filesystems (e.g. Vercel).
    
    :param name: Logger name
    :return: logging.Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # Format for logs
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler (Captured automatically by Vercel / Terminal)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Safe fallback for read-only serverless environments)
    try:
        if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
            log_dir = "/tmp/logs"
        else:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")

        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        # Read-only filesystem on serverless cloud environments - Console Handler is active
        pass

    return logger

logger = setup_logger()
