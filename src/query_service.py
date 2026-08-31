"""Read paths for tickets. Every function here is scoped to user_id.

Two functions:

  * list_tickets — applies optional filters from a QueryFilters and returns
    every matching ticket owned by user_id, newest first.
  * get_ticket_by_id — returns one ticket if it exists AND is owned by
    user_id, otherwise None.

The hard rule: user_id is the FIRST required parameter on every function
in this module. There is no overload that accepts only a ticket_id. This
is intentional — making it impossible to accidentally write a query that
crosses tenant boundaries is more important than any minor convenience.
"""

import sqlite3
from typing import Optional

from src.models import QueryFilters, Ticket


def list_tickets(
    conn: sqlite3.Connection, user_id: int, filters: QueryFilters
) -> list[Ticket]:
    """Return all of user_id's tickets matching `filters`, newest first."""
    sql_parts = [
        "SELECT id, user_id, title, description, category, priority, status, "
        "       created_at, updated_at "
        "FROM tickets WHERE user_id = ?"
    ]
    params: list = [user_id]

    if filters.status is not None:
        sql_parts.append("AND status = ?")
        params.append(filters.status.value)
    if filters.category is not None:
        sql_parts.append("AND category = ?")
        params.append(filters.category.value)
    if filters.priority is not None:
        sql_parts.append("AND priority = ?")
        params.append(filters.priority.value)
    if filters.created_after is not None:
        sql_parts.append("AND created_at >= ?")
        params.append(filters.created_after)
    if filters.created_before is not None:
        sql_parts.append("AND created_at <= ?")
        params.append(filters.created_before)

    sql_parts.append("ORDER BY created_at DESC")
    if filters.limit is not None:
        sql_parts.append("LIMIT ?")
        params.append(filters.limit)

    rows = conn.execute(" ".join(sql_parts), params).fetchall()
    return [Ticket(**dict(row)) for row in rows]


def get_ticket_by_id(
    conn: sqlite3.Connection, user_id: int, ticket_id: int
) -> Optional[Ticket]:
    """Return the ticket if owned by user_id, else None.

    We deliberately do NOT distinguish "ticket does not exist" from "ticket
    exists but belongs to another user" — both return None. Returning
    different errors for the two cases would leak existence information.
    """
    row = conn.execute(
        "SELECT id, user_id, title, description, category, priority, status, "
        "       created_at, updated_at "
        "FROM tickets WHERE id = ? AND user_id = ?",
        (ticket_id, user_id),
    ).fetchone()
    return Ticket(**dict(row)) if row else None
