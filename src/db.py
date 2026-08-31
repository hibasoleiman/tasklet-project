"""Database connection management for the Tasklet support agent.

We use sqlite3 from the stdlib — no ORM. Every query in this codebase is
hand-written, parameterized SQL. Read the service modules and you'll see
exactly how data flows in and out, and how user_id is enforced on every
query.

Two non-obvious things are set up here:

  1. PARSE_DECLTYPES tells sqlite3 to use registered converters when reading
     columns whose declared type matches a registered name. We register
     TIMESTAMP below so created_at / updated_at columns come back as
     datetime objects instead of strings.

  2. Custom datetime adapter and converter. Python 3.12 deprecated (and
     3.14 removed) the implicit adapters that used to handle this. We
     register explicit ones to make the conversion logic visible and to
     avoid relying on stdlib defaults that no longer exist.

Datetimes throughout the app are naive (no timezone). For a single-tenant
demo this is fine; in production you would store and pass UTC explicitly.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "tasklet.db"
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"
SEED_PATH = PROJECT_ROOT / "data" / "seed.sql"


def _adapt_datetime(value: datetime) -> str:
    return value.isoformat(sep=" ")


def _convert_datetime(value: bytes) -> datetime:
    return datetime.fromisoformat(value.decode())


sqlite3.register_adapter(datetime, _adapt_datetime)
sqlite3.register_converter("TIMESTAMP", _convert_datetime)


def get_connection() -> sqlite3.Connection:
    """Open a connection with foreign keys on, row factory set, and TIMESTAMP parsing.

    Service modules accept a connection as a parameter so tests can swap in
    an in-memory DB. We never reach into a module-level singleton.

    check_same_thread=False is set because Streamlit reruns the script on
    potentially different threads, and we cache the Conversation object
    (which holds a connection) in st.session_state. Without this flag,
    accessing the cached connection on a later rerun raises
    ProgrammingError. SQLite serializes writes internally, so this is
    safe for a teaching app that has one user per process.
    """
    conn = sqlite3.connect(
        DB_PATH,
        detect_types=sqlite3.PARSE_DECLTYPES,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(seed: bool = True) -> None:
    """Create the database from schema.sql, optionally inserting seed.sql.

    DESTRUCTIVE: deletes any existing tasklet.db before re-creating. This is
    the intended behavior for a teaching project — `init` should always
    produce a clean, predictable starting state. Back up data/tasklet.db
    first if you want to keep your data.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = get_connection()
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        if seed:
            conn.executescript(SEED_PATH.read_text())
        conn.commit()
    finally:
        conn.close()
