import os
import sqlite3
from utils.logger import logger

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "hostel.db")

def get_db_path():
    """Returns the database file path from environment variable or default location."""
    return os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)

def get_connection():
    """
    Establishes and returns a SQLite database connection with row factory enabled.
    
    :return: sqlite3.Connection
    """
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def execute_query(query, params=(), commit=True):
    """
    Executes an INSERT, UPDATE, or DELETE query safely using parameterized inputs.
    
    :param query: SQL statement
    :param params: tuple or dict of parameter values
    :param commit: whether to commit the transaction immediately
    :return: lastrowid or rowcount
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    except Exception as e:
        conn.rollback()
        logger.error(f"Database query error: {e} | Query: {query} | Params: {params}")
        raise e
    finally:
        conn.close()

def query_one(query, params=()):
    """
    Executes a SELECT query and returns a single row as a dictionary (or None).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Database query_one error: {e} | Query: {query} | Params: {params}")
        raise e
    finally:
        conn.close()

def query_all(query, params=()):
    """
    Executes a SELECT query and returns all matching rows as a list of dictionaries.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Database query_all error: {e} | Query: {query} | Params: {params}")
        raise e
    finally:
        conn.close()

def init_db():
    """
    Initializes database schema and populates seed data if tables do not exist.
    """
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    schema_file = os.path.join(db_dir, "schema.sql")
    seed_file = os.path.join(db_dir, "seed_data.sql")

    conn = get_connection()
    try:
        logger.info(f"Initializing database at: {db_path}")
        if os.path.exists(schema_file):
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
            logger.info("Schema applied successfully.")
        
        if os.path.exists(seed_file):
            with open(seed_file, "r", encoding="utf-8") as f:
                seed_sql = f.read()
            conn.executescript(seed_sql)
            logger.info("Seed data applied successfully.")
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error during database initialization: {e}")
        raise e
    finally:
        conn.close()
