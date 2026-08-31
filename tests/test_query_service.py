"""Tests for list_tickets and get_ticket_by_id.

The most important tests in this file are the ones that prove user_id
scoping works — there must be no way to read another user's ticket via
either function. Those tests are clearly labeled SECURITY.
"""

from datetime import datetime

from src.models import Category, Priority, QueryFilters, Status
from src.query_service import get_ticket_by_id, list_tickets


# ---------- list_tickets ----------

def test_list_returns_all_user_tickets_when_no_filters(conn, seed_tickets):
    results = list_tickets(conn, user_id=1, filters=QueryFilters())
    assert len(results) == 5  # user 1 has 5 in the fixture


def test_list_excludes_other_users_tickets(conn, seed_tickets):
    """SECURITY: user 1 must never see user 2's tickets, even with no filter."""
    results = list_tickets(conn, user_id=1, filters=QueryFilters())
    for t in results:
        assert t.user_id == 1
    titles = {t.title for t in results}
    assert "Other one" not in titles
    assert "Other two" not in titles


def test_list_orders_newest_first(conn, seed_tickets):
    results = list_tickets(conn, user_id=1, filters=QueryFilters())
    timestamps = [t.created_at for t in results]
    assert timestamps == sorted(timestamps, reverse=True)


def test_list_filters_by_status(conn, seed_tickets):
    results = list_tickets(
        conn, user_id=1, filters=QueryFilters(status=Status.OPEN)
    )
    assert [t.title for t in results] == ["Alpha bug"]


def test_list_filters_by_category(conn, seed_tickets):
    results = list_tickets(
        conn, user_id=1, filters=QueryFilters(category=Category.BILLING)
    )
    assert [t.title for t in results] == ["Gamma billing"]


def test_list_filters_by_priority(conn, seed_tickets):
    results = list_tickets(
        conn, user_id=1, filters=QueryFilters(priority=Priority.URGENT)
    )
    assert [t.title for t in results] == ["Gamma billing"]


def test_list_filters_by_date_range(conn, seed_tickets):
    """User 1's fixture spans 2026-04-01 .. 2026-04-21. Window catches 2 tickets."""
    results = list_tickets(
        conn,
        user_id=1,
        filters=QueryFilters(
            created_after=datetime(2026, 4, 5),
            created_before=datetime(2026, 4, 12),
        ),
    )
    titles = {t.title for t in results}
    assert titles == {"Beta feature", "Gamma billing"}


def test_list_combines_multiple_filters(conn, seed_tickets):
    results = list_tickets(
        conn,
        user_id=1,
        filters=QueryFilters(
            status=Status.RESOLVED,
            category=Category.BILLING,
            priority=Priority.URGENT,
        ),
    )
    assert [t.title for t in results] == ["Gamma billing"]


def test_list_returns_empty_when_no_match(conn, seed_tickets):
    results = list_tickets(
        conn,
        user_id=1,
        filters=QueryFilters(
            category=Category.HOW_TO_QUESTION, priority=Priority.URGENT
        ),
    )
    assert results == []


def test_list_respects_limit(conn, seed_tickets):
    results = list_tickets(conn, user_id=1, filters=QueryFilters(limit=2))
    assert len(results) == 2


def test_list_filter_does_not_break_user_scope(conn, seed_tickets):
    """SECURITY: user 2 has a bug_report ticket. User 1 querying bug_report
    must not see it — scope must compose with filters, never replace them.
    """
    results = list_tickets(
        conn, user_id=1, filters=QueryFilters(category=Category.BUG_REPORT)
    )
    for t in results:
        assert t.user_id == 1
    assert [t.title for t in results] == ["Alpha bug"]


# ---------- get_ticket_by_id ----------

def test_get_returns_owned_ticket(conn, seed_tickets):
    user1_ticket_id = conn.execute(
        "SELECT id FROM tickets WHERE user_id = 1 ORDER BY id LIMIT 1"
    ).fetchone()["id"]
    t = get_ticket_by_id(conn, user_id=1, ticket_id=user1_ticket_id)
    assert t is not None
    assert t.user_id == 1


def test_get_returns_none_for_nonexistent(conn, seed_tickets):
    assert get_ticket_by_id(conn, user_id=1, ticket_id=99999) is None


def test_get_returns_none_for_other_users_ticket(conn, seed_tickets):
    """SECURITY: requesting user 2's ticket as user 1 returns None.

    We deliberately do NOT distinguish 'not found' from 'not yours' — the
    function must look identical in both cases so existence is not leaked.
    """
    user2_ticket_id = conn.execute(
        "SELECT id FROM tickets WHERE user_id = 2 ORDER BY id LIMIT 1"
    ).fetchone()["id"]
    t = get_ticket_by_id(conn, user_id=1, ticket_id=user2_ticket_id)
    assert t is None
