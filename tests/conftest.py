"""Shared pytest fixtures.

Every test gets a fresh in-memory SQLite database — fast, isolated, and
never contaminates the on-disk demo DB at data/tasklet.db.

Importing src.db is intentional even though we don't reference it: the
import registers the TIMESTAMP adapter/converter on the sqlite3 module,
so the in-memory connections in `conn` benefit from datetime parsing too.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import src.db  # noqa: F401  (registers TIMESTAMP adapter/converter)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schema.sql"


@pytest.fixture
def conn():
    """A fresh in-memory DB with the production schema applied."""
    c = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(SCHEMA_PATH.read_text())
    yield c
    c.close()


@pytest.fixture
def seed_users(conn):
    """Two test users — kept tiny and deterministic, unlike data/seed.sql."""
    conn.executemany(
        "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
        [
            (1, "test1@example.com", "Test One"),
            (2, "test2@example.com", "Test Two"),
        ],
    )
    conn.commit()


@pytest.fixture
def seed_tickets(conn, seed_users):
    """A controlled set of tickets across both users.

    User 1 has 5 tickets covering all 5 statuses and 5 categories.
    User 2 has 2 — included so security tests can prove cross-user isolation
    even when the other user has values that would otherwise match the filter.

    Dates are explicit (not datetime('now') like data/seed.sql) so date-range
    tests can assert exact behavior.
    """
    base = datetime(2026, 4, 1, 12, 0, 0)
    rows = [
        # user_id, title,             category,            priority, status,                 day_offset
        (1, "Alpha bug",          "bug_report",        "high",   "open",                  0),
        (1, "Beta feature",       "feature_request",   "medium", "in_progress",           5),
        (1, "Gamma billing",      "billing",           "urgent", "resolved",             10),
        (1, "Delta integration",  "integration_issue", "low",    "closed",               15),
        (1, "Echo how-to",        "how_to_question",   "low",    "waiting_on_customer",  20),
        (2, "Other one",          "bug_report",        "low",    "open",                  3),
        (2, "Other two",          "billing",           "high",   "open",                  7),
    ]
    for uid, title, cat, pri, st, offset in rows:
        ts = base + timedelta(days=offset)
        conn.execute(
            "INSERT INTO tickets (user_id, title, description, category, priority, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, title, f"description for {title}", cat, pri, st, ts, ts),
        )
    conn.commit()
