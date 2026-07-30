import os
import sqlite3
from utils.logger import logger

# Import psycopg2 for PostgreSQL (Supabase) integration
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except Exception:
    HAS_PSYCOPG2 = False

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "hostel.db")

def is_postgres():
    """Checks if a PostgreSQL database URL (e.g. Supabase) is configured in environment."""
    db_url = os.getenv("DATABASE_URL", "")
    return HAS_PSYCOPG2 and (db_url.startswith("postgres://") or db_url.startswith("postgresql://"))

def get_db_path():
    """Returns the SQLite database file path from environment variable or default location."""
    if os.getenv("VERCEL") and not os.getenv("DATABASE_PATH"):
        return "/tmp/hostel.db"
    return os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)

def get_connection():
    """
    Establishes and returns a database connection (Supabase PostgreSQL or SQLite).
    """
    db_url = os.getenv("DATABASE_URL", "")
    if is_postgres():
        conn = psycopg2.connect(db_url)
        return conn
    else:
        db_path = get_db_path()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def _format_query(query):
    """
    Normalizes query syntax and placeholders between SQLite and PostgreSQL dialects.
    """
    if is_postgres():
        # Replace SQLite ? placeholder with PostgreSQL %s
        formatted = query.replace("?", "%s")
        # Replace SQLite scalar MAX(0, expr) with PostgreSQL GREATEST(0, expr)
        formatted = formatted.replace("MAX(0,", "GREATEST(0,")
        return formatted
    return query

def execute_query(query, params=(), commit=True):
    """
    Executes an INSERT, UPDATE, or DELETE query safely using parameterized inputs.
    
    :param query: SQL statement
    :param params: tuple or dict of parameter values
    :param commit: whether to commit the transaction immediately
    :return: lastrowid or rowcount
    """
    conn = get_connection()
    use_pg = is_postgres()
    formatted_query = _format_query(query)
    try:
        if use_pg:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # If an INSERT statement without RETURNING, append RETURNING * to capture generated PK ID
                if formatted_query.strip().upper().startswith("INSERT") and " RETURNING " not in formatted_query.upper():
                    formatted_query = formatted_query.rstrip("; ") + " RETURNING *"

                cursor.execute(formatted_query, params)
                inserted_id = None
                if cursor.description:
                    row = cursor.fetchone()
                    if row:
                        row_dict = dict(row)
                        # Find primary key column if available
                        for key in ["visitor_id", "complaint_id", "leave_id", "student_id", "room_id", "warden_id", "log_id"]:
                            if key in row_dict:
                                inserted_id = row_dict[key]
                                break
                        if inserted_id is None and row_dict:
                            inserted_id = list(row_dict.values())[0]

                if commit:
                    conn.commit()
                return inserted_id if inserted_id is not None else cursor.rowcount
        else:
            cursor = conn.cursor()
            cursor.execute(formatted_query, params)
            if commit:
                conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    except Exception as e:
        if commit:
            conn.rollback()
        logger.error(f"Database query error: {e} | Query: {formatted_query} | Params: {params}")
        raise e
    finally:
        conn.close()

def query_one(query, params=()):
    """
    Executes a SELECT query and returns a single row as a dictionary (or None).
    """
    conn = get_connection()
    use_pg = is_postgres()
    formatted_query = _format_query(query)
    try:
        if use_pg:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(formatted_query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        else:
            cursor = conn.cursor()
            cursor.execute(formatted_query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Database query_one error: {e} | Query: {formatted_query} | Params: {params}")
        raise e
    finally:
        conn.close()

def query_all(query, params=()):
    """
    Executes a SELECT query and returns all matching rows as a list of dictionaries.
    """
    conn = get_connection()
    use_pg = is_postgres()
    formatted_query = _format_query(query)
    try:
        if use_pg:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(formatted_query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        else:
            cursor = conn.cursor()
            cursor.execute(formatted_query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Database query_all error: {e} | Query: {formatted_query} | Params: {params}")
        raise e
    finally:
        conn.close()

def init_db(reset=False):
    """
    Initializes database schema and populates seed data (Supabase PostgreSQL or SQLite).
    """
    db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
    schema_file = os.path.join(db_dir, "schema.sql")
    seed_file = os.path.join(db_dir, "seed_data.sql")

    if is_postgres():
        db_url = os.getenv("DATABASE_URL")
        logger.info(f"Initializing Supabase PostgreSQL database at: {db_url.split('@')[-1]}")
        conn = psycopg2.connect(db_url)
        try:
            if reset:
                with conn.cursor() as cursor:
                    cursor.execute("DROP TABLE IF EXISTS complaints, visitors, leaves, chat_logs, students, wardens, rooms, hostel_info CASCADE;")
                conn.commit()

            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                schema_sql = schema_sql.replace("PRAGMA foreign_keys = ON;", "")
                schema_sql = schema_sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                conn.commit()
                logger.info("Supabase PostgreSQL schema applied successfully.")

            if os.path.exists(seed_file):
                with open(seed_file, "r", encoding="utf-8") as f:
                    seed_sql = f.read()
                seed_sql = seed_sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
                with conn.cursor() as cursor:
                    for stmt in seed_sql.split(";"):
                        stmt = stmt.strip()
                        if stmt:
                            try:
                                cursor.execute(stmt + " ON CONFLICT DO NOTHING;")
                            except Exception:
                                pass
                conn.commit()

                # Sync PostgreSQL serial sequence generators after explicit ID inserts
                with conn.cursor() as cursor:
                    seq_tables = [("rooms", "room_id"), ("students", "student_id"), ("wardens", "warden_id"), ("visitors", "visitor_id"), ("chat_logs", "log_id")]
                    for tbl, col in seq_tables:
                        try:
                            cursor.execute(f"SELECT setval(pg_get_serial_sequence('{tbl}', '{col}'), COALESCE((SELECT MAX({col}) FROM {tbl}), 1));")
                        except Exception:
                            pass
                conn.commit()
                logger.info("Supabase PostgreSQL seed data applied & sequences synchronized successfully.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error during Supabase PostgreSQL database initialization: {e}")
            raise e
        finally:
            conn.close()
    else:
        db_path = get_db_path()
        logger.info(f"Initializing SQLite database at: {db_path}")
        conn = get_connection()
        try:
            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                logger.info("SQLite schema applied successfully.")
            
            if os.path.exists(seed_file):
                with open(seed_file, "r", encoding="utf-8") as f:
                    seed_sql = f.read()
                conn.executescript(seed_sql)
                logger.info("SQLite seed data applied successfully.")

            # Migration check: Ensure status column exists in students table
            try:
                conn.execute("ALTER TABLE students ADD COLUMN status TEXT NOT NULL DEFAULT 'Active';")
                conn.commit()
            except Exception:
                pass

        except Exception as e:
            conn.rollback()
            logger.error(f"Error during SQLite database initialization: {e}")
            raise e
        finally:
            conn.close()
